/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";

/**
 * BOHIO CRM - FORM EXPANDIBLE CON SIDEBAR
 * - Maneja expansión/compresión de métricas
 * - Maneja sidebar comprimible con oportunidades relacionadas
 * - Integra mapa con toggle de ubicación
 */

export class BohioCrmFormExpandable extends FormController {
    setup() {
        super.setup();

        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            metricsExpanded: false,
            sidebarExpanded: true,
            mapLocationVisible: true,
            relatedOpportunities: [],
            currentPage: 1,
            pageSize: 4,
            totalCount: 0,
            filterType: 'same_partner',
            loading: false,
            autoRefresh: true,            // Auto-refresh activado por defecto
            refreshInterval: 30000,        // 30 segundos
            lastRefresh: Date.now(),
        });

        // Referencia al polling interval
        this.pollingInterval = null;

        onMounted(() => {
            this.setupEventListeners();
            this.loadRelatedOpportunities();
            this.startPolling();  // Iniciar polling automático
        });

        onWillUnmount(() => {
            this.removeEventListeners();
            this.stopPolling();   // Detener polling al desmontar
        });
    }

    /**
     * Configura event listeners para los botones
     */
    setupEventListeners() {
        // Toggle Métricas
        const metricsToggleBtn = this.el?.querySelector('.o_bohio_toggle_metrics');
        if (metricsToggleBtn) {
            this.metricsToggleHandler = () => this.toggleMetrics();
            metricsToggleBtn.addEventListener('click', this.metricsToggleHandler);
        }

        // Toggle Sidebar
        const sidebarToggleBtn = this.el?.querySelector('.o_bohio_toggle_sidebar');
        if (sidebarToggleBtn) {
            this.sidebarToggleHandler = () => this.toggleSidebar();
            sidebarToggleBtn.addEventListener('click', this.sidebarToggleHandler);
        }

        // Toggle Mapa
        const mapToggle = this.el?.querySelector('#toggle_map_location');
        if (mapToggle) {
            this.mapToggleHandler = (e) => this.toggleMapLocation(e.target.checked);
            mapToggle.addEventListener('change', this.mapToggleHandler);
        }

        // Filtro de Oportunidades
        const filterSelect = this.el?.querySelector('.o_bohio_filter_type');
        if (filterSelect) {
            this.filterChangeHandler = (e) => this.onFilterChange(e.target.value);
            filterSelect.addEventListener('change', this.filterChangeHandler);
        }

        // Escuchar colapso de métricas con Bootstrap
        const metricsContent = this.el?.querySelector('#bohio_metrics_content');
        if (metricsContent) {
            metricsContent.addEventListener('shown.bs.collapse', () => {
                this.updateMetricsToggleText(true);
            });
            metricsContent.addEventListener('hidden.bs.collapse', () => {
                this.updateMetricsToggleText(false);
            });
        }
    }

    /**
     * Remueve event listeners al desmontar
     */
    removeEventListeners() {
        const metricsToggleBtn = this.el?.querySelector('.o_bohio_toggle_metrics');
        const sidebarToggleBtn = this.el?.querySelector('.o_bohio_toggle_sidebar');
        const mapToggle = this.el?.querySelector('#toggle_map_location');
        const filterSelect = this.el?.querySelector('.o_bohio_filter_type');

        if (metricsToggleBtn && this.metricsToggleHandler) {
            metricsToggleBtn.removeEventListener('click', this.metricsToggleHandler);
        }
        if (sidebarToggleBtn && this.sidebarToggleHandler) {
            sidebarToggleBtn.removeEventListener('click', this.sidebarToggleHandler);
        }
        if (mapToggle && this.mapToggleHandler) {
            mapToggle.removeEventListener('change', this.mapToggleHandler);
        }
        if (filterSelect && this.filterChangeHandler) {
            filterSelect.removeEventListener('change', this.filterChangeHandler);
        }
    }

    /**
     * Alterna expansión de métricas
     */
    toggleMetrics() {
        this.state.metricsExpanded = !this.state.metricsExpanded;
    }

    /**
     * Actualiza texto del botón de toggle de métricas
     */
    updateMetricsToggleText(isExpanded) {
        const btn = this.el?.querySelector('.o_bohio_toggle_metrics');
        if (btn) {
            const expandText = btn.querySelector('.o_toggle_text_expand');
            const collapseText = btn.querySelector('.o_toggle_text_collapse');

            if (isExpanded) {
                expandText?.classList.add('d-none');
                collapseText?.classList.remove('d-none');
            } else {
                expandText?.classList.remove('d-none');
                collapseText?.classList.add('d-none');
            }
        }
    }

    /**
     * Alterna expansión del sidebar
     */
    toggleSidebar() {
        this.state.sidebarExpanded = !this.state.sidebarExpanded;

        const sidebar = this.el?.querySelector('.o_bohio_sidebar_right');
        const mainContent = this.el?.querySelector('.o_bohio_main_content');

        if (sidebar && mainContent) {
            if (this.state.sidebarExpanded) {
                sidebar.classList.remove('collapsed');
                mainContent.classList.remove('full-width');
            } else {
                sidebar.classList.add('collapsed');
                mainContent.classList.add('full-width');
            }
        }
    }

    /**
     * Alterna visualización de ubicación en mapa
     */
    async toggleMapLocation(visible) {
        this.state.mapLocationVisible = visible;

        // Actualizar el campo en el registro actual
        if (this.model.root.resId) {
            await this.orm.write('crm.lead', [this.model.root.resId], {
                show_map_location: visible
            });
        }

        // Actualizar visualización del mapa
        this.updateMapDisplay();
    }

    /**
     * Actualiza visualización del mapa
     */
    updateMapDisplay() {
        const mapPlaceholder = this.el?.querySelector('.o_bohio_map_placeholder');
        if (mapPlaceholder) {
            if (this.state.mapLocationVisible) {
                mapPlaceholder.style.opacity = '1';
            } else {
                mapPlaceholder.style.opacity = '0.5';
            }
        }
    }

    /**
     * Carga oportunidades relacionadas según filtro
     */
    async loadRelatedOpportunities() {
        if (!this.model.root.resId) {
            return; // No cargar si es registro nuevo
        }

        this.state.loading = true;

        try {
            // Obtener datos del registro actual
            const currentRecord = await this.orm.read('crm.lead', [this.model.root.resId], [
                'partner_id',
                'service_interested',
                'user_id'
            ]);

            if (!currentRecord || currentRecord.length === 0) {
                return;
            }

            const record = currentRecord[0];

            // Construir dominio según filtro
            let domain = [
                ['id', '!=', this.model.root.resId],
                ['type', '=', 'opportunity']
            ];

            switch (this.state.filterType) {
                case 'same_partner':
                    if (record.partner_id) {
                        domain.push(['partner_id', '=', record.partner_id[0]]);
                    }
                    break;
                case 'same_service':
                    if (record.service_interested) {
                        domain.push(['service_interested', '=', record.service_interested]);
                    }
                    break;
                case 'same_user':
                    if (record.user_id) {
                        domain.push(['user_id', '=', record.user_id[0]]);
                    }
                    break;
                case 'all':
                default:
                    // Sin filtro adicional
                    break;
            }

            // Calcular offset para paginación
            const offset = (this.state.currentPage - 1) * this.state.pageSize;

            // Buscar oportunidades
            const opportunities = await this.orm.searchRead(
                'crm.lead',
                domain,
                [
                    'id',
                    'name',
                    'partner_id',
                    'stage_id',
                    'service_interested',
                    'expected_revenue',
                    'probability',
                    'company_currency'
                ],
                {
                    limit: this.state.pageSize,
                    offset: offset,
                    order: 'write_date desc'
                }
            );

            // Contar total
            const totalCount = await this.orm.searchCount('crm.lead', domain);

            this.state.relatedOpportunities = opportunities;
            this.state.totalCount = totalCount;

            // Renderizar las oportunidades
            this.renderOpportunitiesList();

        } catch (error) {
            console.error('Error loading related opportunities:', error);
        } finally {
            this.state.loading = false;
        }
    }

    /**
     * Renderiza la lista de oportunidades en el sidebar
     */
    renderOpportunitiesList() {
        const listContainer = this.el?.querySelector('.o_bohio_opportunities_list');
        if (!listContainer) return;

        // Limpiar contenido
        listContainer.innerHTML = '';

        if (this.state.loading) {
            listContainer.innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="fa fa-spinner fa-spin fa-2x mb-2"></i>
                    <p class="small">Cargando oportunidades...</p>
                </div>
            `;
            return;
        }

        if (this.state.relatedOpportunities.length === 0) {
            listContainer.innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="fa fa-inbox fa-2x mb-2"></i>
                    <p class="small">No hay oportunidades relacionadas</p>
                </div>
            `;
            return;
        }

        // Renderizar cada oportunidad
        this.state.relatedOpportunities.forEach(opp => {
            const card = this.createOpportunityCard(opp);
            listContainer.appendChild(card);
        });

        // Actualizar paginación
        this.updatePaginationDisplay();
    }

    /**
     * Crea un card HTML para una oportunidad
     */
    createOpportunityCard(opp) {
        const card = document.createElement('div');
        card.className = 'o_bohio_opportunity_card mb-2 p-2 border rounded bg-white';
        card.style.cursor = 'pointer';

        const serviceBadgeClass = this.getServiceBadgeClass(opp.service_interested);
        const serviceIcon = this.getServiceIcon(opp.service_interested);

        card.innerHTML = `
            <div class="d-flex justify-content-between align-items-start mb-1">
                <strong class="text-truncate flex-grow-1 me-2">${opp.name}</strong>
                <span class="badge ${serviceBadgeClass}">
                    <i class="fa ${serviceIcon} me-1"></i>
                    ${opp.service_interested || '-'}
                </span>
            </div>
            <div class="small text-muted mb-1">
                <i class="fa fa-user me-1"></i>
                ${opp.partner_id ? opp.partner_id[1] : 'Sin cliente'}
            </div>
            <div class="small text-muted mb-1">
                <i class="fa fa-flag me-1"></i>
                ${opp.stage_id ? opp.stage_id[1] : 'Sin etapa'}
            </div>
            <div class="d-flex justify-content-between align-items-center mt-2 pt-2 border-top">
                <span class="small fw-bold text-success">
                    <i class="fa fa-dollar-sign me-1"></i>
                    ${this.formatCurrency(opp.expected_revenue)}
                </span>
                <span class="small text-muted">
                    ${opp.probability}% prob.
                </span>
            </div>
        `;

        // Click para abrir oportunidad
        card.addEventListener('click', () => {
            this.openOpportunity(opp.id);
        });

        return card;
    }

    /**
     * Abre una oportunidad
     */
    async openOpportunity(oppId) {
        await this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'crm.lead',
            res_id: oppId,
            views: [[false, 'form']],
            target: 'current',
        });
    }

    /**
     * Cambia el filtro de oportunidades
     */
    async onFilterChange(filterType) {
        this.state.filterType = filterType;
        this.state.currentPage = 1;
        await this.loadRelatedOpportunities();
    }

    /**
     * Actualiza la visualización de la paginación
     */
    updatePaginationDisplay() {
        const paginationContainer = this.el?.querySelector('.o_bohio_sidebar_pagination');
        if (!paginationContainer) return;

        const start = (this.state.currentPage - 1) * this.state.pageSize + 1;
        const end = Math.min(this.state.currentPage * this.state.pageSize, this.state.totalCount);
        const paginationText = `${start}-${end} de ${this.state.totalCount}`;

        const textSpan = paginationContainer.querySelector('.small.text-muted');
        if (textSpan) {
            textSpan.textContent = paginationText;
        }
    }

    /**
     * Obtiene clase de badge según tipo de servicio
     */
    getServiceBadgeClass(serviceType) {
        const classes = {
            'sale': 'text-bg-primary',
            'rent': 'text-bg-info',
            'projects': 'text-bg-success',
            'consign': 'text-bg-warning',
            'marketing': 'text-bg-danger',
            'legal': 'text-bg-secondary',
            'corporate': 'text-bg-dark',
        };
        return classes[serviceType] || 'text-bg-secondary';
    }

    /**
     * Obtiene icono según tipo de servicio
     */
    getServiceIcon(serviceType) {
        const icons = {
            'sale': 'fa-home',
            'rent': 'fa-key',
            'projects': 'fa-building',
            'consign': 'fa-handshake',
            'marketing': 'fa-bullhorn',
            'legal': 'fa-gavel',
            'corporate': 'fa-briefcase',
        };
        return icons[serviceType] || 'fa-circle';
    }

    /**
     * Formatea valor monetario
     */
    formatCurrency(value) {
        if (!value) return '-';
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0
        }).format(value);
    }

    /**
     * Inicia el polling automático para actualizar sidebar
     */
    startPolling() {
        if (!this.state.autoRefresh || this.pollingInterval) {
            return;
        }

        console.log(`[Polling] Starting auto-refresh every ${this.state.refreshInterval / 1000} seconds`);

        this.pollingInterval = setInterval(async () => {
            // Solo actualizar si el sidebar está expandido y no está en proceso de carga
            if (this.state.sidebarExpanded && !this.state.loading) {
                console.log('[Polling] Auto-refreshing opportunities...');
                await this.loadRelatedOpportunities();
                this.state.lastRefresh = Date.now();
                this.updateLastRefreshDisplay();
            }
        }, this.state.refreshInterval);
    }

    /**
     * Detiene el polling automático
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
            console.log('[Polling] Auto-refresh stopped');
        }
    }

    /**
     * Alterna el estado de auto-refresh
     */
    toggleAutoRefresh() {
        this.state.autoRefresh = !this.state.autoRefresh;

        if (this.state.autoRefresh) {
            this.startPolling();
        } else {
            this.stopPolling();
        }
    }

    /**
     * Actualiza el display de última actualización
     */
    updateLastRefreshDisplay() {
        const lastRefreshEl = this.el?.querySelector('.o_bohio_last_refresh');
        if (!lastRefreshEl) return;

        const timeAgo = this.getTimeAgo(this.state.lastRefresh);
        lastRefreshEl.textContent = `Actualizado: ${timeAgo}`;
    }

    /**
     * Obtiene el tiempo transcurrido desde la última actualización
     */
    getTimeAgo(timestamp) {
        const seconds = Math.floor((Date.now() - timestamp) / 1000);

        if (seconds < 60) {
            return 'hace unos segundos';
        }

        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) {
            return `hace ${minutes} ${minutes === 1 ? 'minuto' : 'minutos'}`;
        }

        const hours = Math.floor(minutes / 60);
        return `hace ${hours} ${hours === 1 ? 'hora' : 'horas'}`;
    }
}

BohioCrmFormExpandable.template = "web.FormView";

/**
 * Registrar el controller personalizado
 */
registry.category("views").add("bohio_crm_form_expandable", {
    ...registry.category("views").get("form"),
    Controller: BohioCrmFormExpandable,
});

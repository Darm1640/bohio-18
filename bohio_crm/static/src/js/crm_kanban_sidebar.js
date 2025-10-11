/** @odoo-module **/

import { KanbanController } from "@web/views/kanban/kanban_controller";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";

/**
 * BOHIO CRM - SIDEBAR KANBAN COMPRIMIBLE
 * Muestra oportunidades agrupadas por tipo con paginación 4 en 4
 */

export class BohioCrmKanbanSidebar extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            isCollapsed: false,
            currentPage: 1,
            pageSize: 4,
            selectedType: 'all',
            opportunities: [],
            totalCount: 0,
            loading: false,
        });

        onWillStart(async () => {
            await this.loadOpportunities();
        });

        onMounted(() => {
            this.setupToggleButton();
        });
    }

    /**
     * Carga oportunidades según filtros actuales
     */
    async loadOpportunities() {
        this.state.loading = true;

        try {
            // Construir dominio de búsqueda
            const domain = [['type', '=', 'opportunity']];

            if (this.state.selectedType !== 'all') {
                domain.push(['service_interested', '=', this.state.selectedType]);
            }

            // Calcular offset para paginación
            const offset = (this.state.currentPage - 1) * this.state.pageSize;

            // Buscar oportunidades
            const opportunities = await this.orm.searchRead(
                "crm.lead",
                domain,
                [
                    "id",
                    "name",
                    "partner_id",
                    "email_from",
                    "phone",
                    "mobile",
                    "service_interested",
                    "client_type",
                    "stage_id",
                    "user_id",
                    "expected_revenue",
                    "probability",
                    "company_currency"
                ],
                {
                    limit: this.state.pageSize,
                    offset: offset,
                    order: "write_date desc"
                }
            );

            // Contar total de oportunidades
            const totalCount = await this.orm.searchCount("crm.lead", domain);

            this.state.opportunities = opportunities;
            this.state.totalCount = totalCount;

        } catch (error) {
            console.error("Error loading opportunities:", error);
        } finally {
            this.state.loading = false;
        }
    }

    /**
     * Cambia el filtro de tipo de servicio
     */
    async onTypeFilterChange(ev) {
        this.state.selectedType = ev.target.value;
        this.state.currentPage = 1; // Reset a página 1
        await this.loadOpportunities();
    }

    /**
     * Navega a la página anterior
     */
    async onPrevPage() {
        if (this.state.currentPage > 1) {
            this.state.currentPage--;
            await this.loadOpportunities();
        }
    }

    /**
     * Navega a la página siguiente
     */
    async onNextPage() {
        const totalPages = Math.ceil(this.state.totalCount / this.state.pageSize);
        if (this.state.currentPage < totalPages) {
            this.state.currentPage++;
            await this.loadOpportunities();
        }
    }

    /**
     * Alterna el estado colapsado del sidebar
     */
    toggleSidebar() {
        this.state.isCollapsed = !this.state.isCollapsed;

        // Actualizar clase del kanban principal
        const kanbanMain = document.querySelector('.o_bohio_kanban_main');
        if (kanbanMain) {
            if (this.state.isCollapsed) {
                kanbanMain.classList.remove('with-sidebar');
                kanbanMain.classList.add('with-sidebar-collapsed');
            } else {
                kanbanMain.classList.remove('with-sidebar-collapsed');
                kanbanMain.classList.add('with-sidebar');
            }
        }
    }

    /**
     * Configura el botón de toggle después del montaje
     */
    setupToggleButton() {
        const toggleBtn = this.el.querySelector('.o_bohio_sidebar_toggle');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggleSidebar());
        }
    }

    /**
     * Abre una oportunidad al hacer clic en su card
     */
    async openOpportunity(opportunityId) {
        await this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'crm.lead',
            res_id: opportunityId,
            views: [[false, 'form']],
            target: 'current',
        });
    }

    /**
     * Obtiene el icono según el tipo de servicio
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
            'valuation': 'fa-chart-line'
        };
        return icons[serviceType] || 'fa-circle';
    }

    /**
     * Obtiene la clase de badge según el tipo de servicio
     */
    getServiceBadgeClass(serviceType) {
        return `o_bohio_badge_${serviceType}`;
    }

    /**
     * Formatea el valor monetario
     */
    formatCurrency(value, currencyId) {
        if (!value) return '-';
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0
        }).format(value);
    }

    /**
     * Obtiene el nombre del contacto (teléfono o email si no hay partner)
     */
    getContactDisplay(opportunity) {
        if (opportunity.partner_id) {
            return opportunity.partner_id[1];
        }
        if (opportunity.mobile) {
            return opportunity.mobile;
        }
        if (opportunity.phone) {
            return opportunity.phone;
        }
        if (opportunity.email_from) {
            return opportunity.email_from;
        }
        return 'Sin contacto';
    }

    /**
     * Calcula si hay página anterior
     */
    get hasPrevPage() {
        return this.state.currentPage > 1;
    }

    /**
     * Calcula si hay página siguiente
     */
    get hasNextPage() {
        const totalPages = Math.ceil(this.state.totalCount / this.state.pageSize);
        return this.state.currentPage < totalPages;
    }

    /**
     * Calcula el texto de paginación (ej: "1-4 de 23")
     */
    get paginationText() {
        const start = (this.state.currentPage - 1) * this.state.pageSize + 1;
        const end = Math.min(this.state.currentPage * this.state.pageSize, this.state.totalCount);
        return `${start}-${end} de ${this.state.totalCount}`;
    }

    /**
     * Traducciones para tipos de servicio
     */
    get serviceTypeOptions() {
        return [
            { value: 'all', label: 'Todos los tipos' },
            { value: 'sale', label: 'Venta' },
            { value: 'rent', label: 'Arriendo' },
            { value: 'projects', label: 'Proyectos' },
            { value: 'consign', label: 'Consignación' },
            { value: 'marketing', label: 'Marketing' },
            { value: 'legal', label: 'Legal' },
            { value: 'corporate', label: 'Corporativo' },
            { value: 'valuation', label: 'Avalúo' }
        ];
    }
}

BohioCrmKanbanSidebar.template = "bohio_crm.KanbanSidebarTemplate";


/**
 * Extensión del KanbanController para integrar el sidebar
 */
export class BohioCrmKanbanController extends KanbanController {
    setup() {
        super.setup();
        this.sidebarComponent = BohioCrmKanbanSidebar;
    }
}

BohioCrmKanbanController.template = "bohio_crm.KanbanControllerWithSidebar";
BohioCrmKanbanController.components = {
    ...KanbanController.components,
    BohioCrmKanbanSidebar,
};


/**
 * Registrar la vista Kanban personalizada
 */
registry.category("views").add("bohio_crm_kanban_sidebar", {
    ...registry.category("views").get("kanban"),
    Controller: BohioCrmKanbanController,
});

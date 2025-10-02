/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class CrmSalespersonDashboard extends Component {
    static template = "bohio_crm.CrmSalespersonDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            dashboardData: {},
            loading: true,
            filters: {
                period: 'month',
                status: '',
                property_type: '',
                price_range: '',
                contract_status: '',
                region: ''
            }
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    async loadDashboardData(filters = null) {
        this.state.loading = true;
        try {
            const data = await this.orm.call(
                "crm.salesperson.dashboard",
                "get_dashboard_data",
                [],
                { filters: filters || this.state.filters }
            );
            this.state.dashboardData = data || {};
            this.state.loading = false;
        } catch (error) {
            this.notification.add(_t("Error al cargar datos del dashboard"), {
                type: "danger"
            });
            console.error("Dashboard loading error:", error);
            this.state.loading = false;
        }
    }

    async onFilterChange(filterName, value) {
        // Actualizar el filtro en el estado
        this.state.filters[filterName] = value;

        // Recargar datos con los nuevos filtros
        await this.loadDashboardData();

        // Notificar al usuario
        this.notification.add(_t("Filtros aplicados correctamente"), {
            type: "success"
        });
    }

    async resetFilters() {
        // Resetear todos los filtros
        this.state.filters = {
            period: 'month',
            status: '',
            property_type: '',
            price_range: '',
            contract_status: '',
            region: ''
        };

        // Resetear los selects en el DOM
        const selects = document.querySelectorAll('.o_crm_salesperson_dashboard select');
        selects.forEach((select, index) => {
            if (index === 0) {
                select.value = 'month'; // Period filter
            } else {
                select.value = '';
            }
        });

        // Recargar datos
        await this.loadDashboardData();

        this.notification.add(_t("Filtros limpiados"), {
            type: "info"
        });
    }

    // =================== MÉTODOS DE NAVEGACIÓN ===================

    onViewOpportunities() {
        this.action.doAction({
            name: _t("Oportunidades"),
            type: 'ir.actions.act_window',
            res_model: 'crm.lead',
            views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
            domain: [['type', '=', 'opportunity']],
            context: { default_type: 'opportunity' }
        });
    }

    onViewWonOpportunities() {
        this.action.doAction({
            name: _t("Oportunidades Ganadas"),
            type: 'ir.actions.act_window',
            res_model: 'crm.lead',
            views: [[false, 'list'], [false, 'form']],
            domain: [['type', '=', 'opportunity'], ['stage_id.is_won', '=', true]],
        });
    }

    onViewPipeline() {
        this.action.doAction({
            name: _t("Pipeline"),
            type: 'ir.actions.act_window',
            res_model: 'crm.lead',
            views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
            domain: [['type', '=', 'opportunity'], ['active', '=', true]],
        });
    }

    onViewContracts() {
        this.action.doAction({
            name: _t("Contratos"),
            type: 'ir.actions.act_window',
            res_model: 'property.contract',
            views: [[false, 'list'], [false, 'form']],
            domain: [],
        });
    }

    onViewProperties() {
        this.action.doAction({
            name: _t("Propiedades"),
            type: 'ir.actions.act_window',
            res_model: 'product.template',
            views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
            domain: [['is_property', '=', true]],
        });
    }

    onViewProperty(propertyId) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'product.template',
            res_id: propertyId,
            views: [[false, 'form']],
            target: 'current',
        });
    }

    onViewMessages() {
        this.action.doAction({
            name: _t("Mensajes"),
            type: 'ir.actions.act_window',
            res_model: 'mail.message',
            views: [[false, 'list'], [false, 'form']],
            domain: [['model', '=', 'crm.lead']],
        });
    }

    onViewForecast() {
        // Mostrar proyección financiera en detalle
        this.notification.add(_t("Proyección financiera mostrada en el dashboard"), {
            type: "info"
        });
    }
}

// Registrar el componente en el registry de acciones
registry.category("actions").add("crm_salesperson_dashboard", CrmSalespersonDashboard);

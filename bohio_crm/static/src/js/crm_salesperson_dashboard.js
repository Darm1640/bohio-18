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
}

// Registrar el componente en el registry de acciones
registry.category("actions").add("crm_salesperson_dashboard", CrmSalespersonDashboard);

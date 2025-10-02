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
            loading: true
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    async loadDashboardData() {
        try {
            const data = await this.orm.call(
                "crm.salesperson.dashboard",
                "get_dashboard_data",
                []
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
}

// Registrar el componente en el registry de acciones
registry.category("actions").add("crm_salesperson_dashboard", CrmSalespersonDashboard);

/** @odoo-module **/

import { KanbanController } from "@web/views/kanban/kanban_controller";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class BohioCRMKanbanController extends KanbanController {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
    }

    /**
     * Navega a las oportunidades filtradas por el estado del dashboard
     */
    async onDashboardCardClick(filterType) {
        const domain = this.getDomainForFilter(filterType);
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: this.getDashboardTitle(filterType),
            res_model: "crm.lead",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            context: { ...this.props.context },
        });
    }

    /**
     * Obtiene el dominio según el filtro
     */
    getDomainForFilter(filterType) {
        const baseDomain = [["type", "=", "opportunity"]];

        switch (filterType) {
            case "new":
                return [...baseDomain, ["stage_id.sequence", "=", 1]];
            case "qualified":
                return [...baseDomain, ["stage_id.name", "=", "Calificado"]];
            case "proposal":
                return [...baseDomain, ["stage_id.name", "=", "Propuesta"]];
            case "won":
                return [...baseDomain, ["probability", "=", 100], ["active", "=", true]];
            case "lost":
                return [...baseDomain, ["probability", "=", 0], ["active", "=", false]];
            case "rent":
                return [...baseDomain, ["service_interested", "=", "rent"]];
            case "sale":
                return [...baseDomain, ["service_interested", "=", "sale"]];
            default:
                return baseDomain;
        }
    }

    /**
     * Obtiene el título según el filtro
     */
    getDashboardTitle(filterType) {
        const titles = {
            new: "Oportunidades Nuevas",
            qualified: "Oportunidades Calificadas",
            proposal: "Propuestas",
            won: "Oportunidades Ganadas",
            lost: "Oportunidades Perdidas",
            rent: "Arriendo",
            sale: "Venta",
        };
        return titles[filterType] || "Oportunidades";
    }
}

export class BohioCRMKanbanRenderer extends KanbanRenderer {
    /**
     * Renderiza el dashboard en la parte superior del kanban
     */
    async computeDashboardData() {
        const result = await this.orm.call(
            "crm.lead",
            "read_group",
            [],
            ["stage_id", "expected_revenue:sum", "recurring_revenue:sum", "estimated_commission:sum"],
            ["stage_id"],
            { lazy: false }
        );

        const dashboardData = {
            new: 0,
            qualified: 0,
            proposal: 0,
            won: 0,
            lost: 0,
            rent: 0,
            sale: 0,
            total_revenue: 0,
            recurring_revenue: 0,
            commission: 0,
        };

        // Procesar resultados del read_group
        for (const group of result) {
            dashboardData.total_revenue += group.expected_revenue || 0;
            dashboardData.recurring_revenue += group.recurring_revenue || 0;
            dashboardData.commission += group.estimated_commission || 0;
        }

        // Contar por estados específicos
        const counts = await this.orm.call(
            "crm.lead",
            "search_count_by_state",
            []
        );

        Object.assign(dashboardData, counts);

        return dashboardData;
    }
}

export const bohioCRMKanbanView = {
    ...kanbanView,
    Controller: BohioCRMKanbanController,
    Renderer: BohioCRMKanbanRenderer,
};

registry.category("views").add("bohio_crm_kanban_dashboard", bohioCRMKanbanView);

/** @odoo-module */

import { registry } from "@web/core/registry";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { BohioCRMDashBoard } from "./bohio_crm_dashboard";

export class BohioCRMDashBoardKanbanRenderer extends KanbanRenderer {
    static template = "bohio_crm.BohioCRMKanbanView";
    static components = {
        ...KanbanRenderer.components,
        BohioCRMDashBoard,
    };
}

export const bohioCRMDashBoardKanbanView = {
    ...kanbanView,
    Renderer: BohioCRMDashBoardKanbanRenderer,
};

registry.category("views").add("bohio_crm_dashboard_kanban", bohioCRMDashBoardKanbanView);

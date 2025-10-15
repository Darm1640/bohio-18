/** @odoo-module */

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { ListController } from "@web/views/list/list_controller";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { useService } from "@web/core/utils/hooks";

/**
 * BOHIO CRM - LIST VIEW MODERNA
 * Controller personalizado para la vista list de CRM
 */
export class BohioCrmListModernController extends ListController {
    setup() {
        super.setup();
        this.notification = useService("notification");
    }

    /**
     * Acción personalizada al seleccionar múltiples registros
     */
    async onSelectRecords(records) {
        if (records.length > 0) {
            console.log(`Selected ${records.length} records`);
        }
    }
}

/**
 * BOHIO CRM - KANBAN VIEW MODERNA
 * Controller personalizado para la vista kanban de CRM
 */
export class BohioCrmKanbanModernController extends KanbanController {
    setup() {
        super.setup();
        this.notification = useService("notification");
        this.action = useService("action");
    }

    /**
     * Hook personalizado después de crear un registro rápido
     */
    async onRecordCreate(record) {
        await super.onRecordCreate?.(record);
        console.log("Record created:", record);
    }

    /**
     * Hook personalizado al mover una tarjeta entre columnas
     */
    async onRecordMove(record, group) {
        console.log("Record moved to:", group);
    }
}

/**
 * Vista List Moderna de Bohio CRM
 */
export const bohioCrmListModern = {
    ...listView,
    Controller: BohioCrmListModernController,
};

/**
 * Vista Kanban Moderna de Bohio CRM
 */
export const bohioCrmKanbanModern = {
    ...kanbanView,
    Controller: BohioCrmKanbanModernController,
};

// Registrar las vistas en el registry
registry.category("views").add("bohio_crm_list_modern", bohioCrmListModern);
registry.category("views").add("bohio_crm_kanban_modern", bohioCrmKanbanModern);

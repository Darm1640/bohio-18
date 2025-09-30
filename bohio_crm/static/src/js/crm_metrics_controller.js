/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
import { onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { kanbanView } from "@web/views/kanban/kanban_view";

/**
 * CRM Metrics List Controller
 * Based on hr_expense pattern but tailored for CRM metrics
 */
export class CrmMetricsListController extends ListController {
    setup() {
        super.setup();
        this.notification = useService("notification");
        this.actionService = useService("action");
        this.orm = useService("orm");

        onWillStart(async () => {
            this.userIsSalesManager = await user.hasGroup("sales_team.group_sale_manager");
            this.userIsSalesman = await user.hasGroup("sales_team.group_sale_salesman");
        });
    }

    /**
     * Display selection metrics
     */
    displaySelectionMetrics() {
        const records = this.model.root.selection;
        if (records.length > 0) {
            const totalRevenue = records.reduce((sum, record) =>
                sum + (record.data.expected_revenue || 0), 0
            );
            const avgProbability = records.reduce((sum, record) =>
                sum + (record.data.probability || 0), 0
            ) / records.length;

            return {
                count: records.length,
                totalRevenue: totalRevenue,
                avgProbability: avgProbability.toFixed(1)
            };
        }
        return null;
    }

    /**
     * Override selection change to show metrics
     */
    onSelectionChanged() {
        super.onSelectionChanged();
        const metrics = this.displaySelectionMetrics();
        if (metrics) {
            this.notification.add(
                `Selected: ${metrics.count} opportunities, Total Revenue: ${metrics.totalRevenue.toLocaleString()}, Avg Probability: ${metrics.avgProbability}%`,
                { type: "info", sticky: false }
            );
        }
    }
}

/**
 * CRM Metrics Dashboard List Controller
 * Read-only version for dashboard views
 */
export class CrmMetricsDashboardListController extends CrmMetricsListController {
    setup() {
        super.setup();
    }

    /**
     * Override to prevent editing in dashboard mode
     */
    get canCreate() {
        return false;
    }

    get canEdit() {
        return false;
    }

    get canDelete() {
        return false;
    }
}

/**
 * CRM Metrics Kanban Controller
 */
export class CrmMetricsKanbanController extends KanbanController {
    setup() {
        super.setup();
        this.notification = useService("notification");
        this.orm = useService("orm");

        onWillStart(async () => {
            this.userIsSalesManager = await user.hasGroup("sales_team.group_sale_manager");
            this.userIsSalesman = await user.hasGroup("sales_team.group_sale_salesman");
        });
    }

    /**
     * Override record click to show enhanced info
     */
    async onRecordClick(record, ev) {
        // Show quick metrics preview for managers
        if (this.userIsSalesManager) {
            this.showMetricsPreview(record);
        }
        return super.onRecordClick(record, ev);
    }

    /**
     * Show metrics preview for a record
     */
    showMetricsPreview(record) {
        const data = record.data;
        const metrics = [
            `Expected Revenue: ${(data.expected_revenue || 0).toLocaleString()}`,
            `Probability: ${data.probability || 0}%`,
            `Stage: ${data.stage_id?.[1] || 'Unknown'}`,
            `Salesperson: ${data.user_id?.[1] || 'Unassigned'}`
        ].join('\n');

        this.notification.add(
            `${data.name}\n${metrics}`,
            { type: "info", sticky: false }
        );
    }

    /**
     * Enhanced drag and drop for stage changes
     */
    async moveRecord(dataRecordId, dataGroupId, options = {}) {
        const result = await super.moveRecord(dataRecordId, dataGroupId, options);

        // Log stage change for analytics - simplified logging
        if (dataRecordId && dataGroupId) {
            this.orm.call(
                this.props.resModel,
                "log_stage_change",
                [[dataRecordId], dataGroupId]
            ).catch(() => {
                // Silent fail for logging
            });
        }

        return result;
    }
}

/**
 * CRM Metrics Dashboard Kanban Controller
 */
export class CrmMetricsDashboardKanbanController extends CrmMetricsKanbanController {
    setup() {
        super.setup();
    }

    get canCreate() {
        return false;
    }

    get canEdit() {
        return this.userIsSalesManager;
    }

    get canDelete() {
        return false;
    }
}

// Register the controllers
registry.category("views").add("crm_metrics_tree", {
    ...listView,
    Controller: CrmMetricsListController,
});

registry.category("views").add("crm_metrics_dashboard_tree", {
    ...listView,
    Controller: CrmMetricsDashboardListController,
});

registry.category("views").add("crm_metrics_kanban", {
    ...kanbanView,
    Controller: CrmMetricsKanbanController,
});

registry.category("views").add("crm_metrics_dashboard_kanban", {
    ...kanbanView,
    Controller: CrmMetricsDashboardKanbanController,
});
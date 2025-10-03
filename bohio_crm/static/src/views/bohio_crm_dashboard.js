/** @odoo-module */

import { Component, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class BohioCRMDashBoard extends Component {
    static template = "bohio_crm.BohioCRMDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        onWillStart(async () => {
            this.crmData = await this.orm.call("crm.lead", "retrieve_dashboard", []);
        });
    }

    setSearchContext(ev) {
        const filter_name = ev.currentTarget.getAttribute("filter_name");
        const filter_value = ev.currentTarget.getAttribute("filter_value");

        let domain = [];
        let context = {};

        switch(filter_name) {
            case "new":
                domain = [["stage_id.is_won", "=", false], ["probability", "<", 20]];
                break;
            case "qualified":
                domain = [["stage_id.is_won", "=", false], ["probability", ">=", 20], ["probability", "<", 70]];
                break;
            case "proposal":
                domain = [["stage_id.is_won", "=", false], ["probability", ">=", 70]];
                break;
            case "my_new":
                domain = [["user_id", "=", this.crmData.user_id], ["stage_id.is_won", "=", false], ["probability", "<", 20]];
                break;
            case "my_qualified":
                domain = [["user_id", "=", this.crmData.user_id], ["stage_id.is_won", "=", false], ["probability", ">=", 20], ["probability", "<", 70]];
                break;
            case "my_proposal":
                domain = [["user_id", "=", this.crmData.user_id], ["stage_id.is_won", "=", false], ["probability", ">=", 70]];
                break;
        }

        if (filter_value) {
            context['search_default_' + filter_value] = true;
        }

        // Odoo 18: Usar action.doAction en lugar de searchModel.setDomainParts
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "CRM Leads",
            res_model: "crm.lead",
            views: [[false, "list"], [false, "kanban"], [false, "form"]],
            domain: domain,
            context: context,
        });
    }
}

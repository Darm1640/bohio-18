/** @odoo-module **/

import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

class BohioTimelineView extends Component {
    static template = "bohio_crm.TimelineView";
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService('orm');
        this.action = useService('action');
        this.notification = useService('notification');

        this.state = useState({
            opportunityData: {},
            recommendedProperties: [],
            comparisonProperties: [],
            clientFieldsExpanded: false,
        });

        onWillStart(async () => {
            await this.loadOpportunityData();
        });
    }

    async loadOpportunityData() {
        const opportunityId = this.props.action.context.active_id;
        if (!opportunityId) {
            this.notification.add('No se encontró la oportunidad', { type: 'danger' });
            return;
        }

        const data = await this.orm.call('crm.lead', 'get_timeline_view_data', [opportunityId]);
        this.state.opportunityData = data;
        this.state.recommendedProperties = data.recommended_properties || [];
        this.state.comparisonProperties = data.comparison_properties || [];
    }

    // === ACTION BUTTONS ===
    async createActivity() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'mail.activity',
            views: [[false, 'form']],
            target: 'new',
            context: {
                default_res_id: this.state.opportunityData.id,
                default_res_model: 'crm.lead',
            }
        });
    }

    async scheduleCall() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'mail.activity',
            views: [[false, 'form']],
            target: 'new',
            context: {
                default_res_id: this.state.opportunityData.id,
                default_res_model: 'crm.lead',
                default_activity_type_id: 2, // Phone Call
            }
        });
    }

    async scheduleMeeting() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'calendar.event',
            views: [[false, 'form']],
            target: 'new',
            context: {
                default_res_id: this.state.opportunityData.id,
                default_res_model: 'crm.lead',
                default_partner_ids: [this.state.opportunityData.partner_id[0]],
            }
        });
    }

    async sendEmail() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'mail.compose.message',
            views: [[false, 'form']],
            target: 'new',
            context: {
                default_model: 'crm.lead',
                default_res_ids: [this.state.opportunityData.id],
                default_partner_ids: [this.state.opportunityData.partner_id[0]],
            }
        });
    }

    async sendWhatsApp() {
        const phone = this.state.opportunityData.phone || this.state.opportunityData.partner_phone;
        if (!phone) {
            this.notification.add('No hay teléfono registrado', { type: 'warning' });
            return;
        }
        const cleanPhone = phone.replace(/[^0-9]/g, '');
        const message = `Hola ${this.state.opportunityData.partner_name}, te contacto desde BOHIO...`;
        window.open(`https://wa.me/${cleanPhone}?text=${encodeURIComponent(message)}`, '_blank');
    }

    async generateContract() {
        await this.orm.call('crm.lead', 'action_generate_contract', [this.state.opportunityData.id]);
        this.notification.add('Contrato generado exitosamente', { type: 'success' });
        await this.loadOpportunityData();
    }

    async compareProperties() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'property.property',
            name: 'Comparar Propiedades',
            views: [[false, 'list']],
            domain: [['id', 'in', this.state.comparisonProperties.map(p => p.id)]],
        });
    }

    async printView() {
        window.print();
    }

    // === PROPERTY ACTIONS ===
    async refreshRecommendations() {
        const properties = await this.orm.call('crm.lead', 'get_ai_recommendations', [this.state.opportunityData.id]);
        this.state.recommendedProperties = properties;
        this.notification.add('Recomendaciones actualizadas', { type: 'success' });
    }

    async addToComparison(propertyId) {
        await this.orm.call('crm.lead', 'add_property_to_comparison', [this.state.opportunityData.id, propertyId]);
        await this.loadOpportunityData();
        this.notification.add('Propiedad agregada a comparación', { type: 'success' });
    }

    async removeFromComparison(propertyId) {
        await this.orm.call('crm.lead', 'remove_property_from_comparison', [this.state.opportunityData.id, propertyId]);
        await this.loadOpportunityData();
        this.notification.add('Propiedad removida', { type: 'info' });
    }

    async viewProperty(propertyId) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'property.property',
            res_id: propertyId,
            views: [[false, 'form']],
            target: 'current',
        });
    }

    // === UI ACTIONS ===
    toggleClientFields() {
        this.state.clientFieldsExpanded = !this.state.clientFieldsExpanded;
    }

    async updateMetric(field, value) {
        await this.orm.write('crm.lead', [this.state.opportunityData.id], { [field]: value });
        await this.loadOpportunityData();
    }

    // === CALCULATIONS ===
    get totalRevenue() {
        const expected = this.state.opportunityData.expected_revenue || 0;
        const recurring = (this.state.opportunityData.recurring_revenue || 0) * 12;
        return expected + recurring;
    }

    get commissionAmount() {
        const total = this.totalRevenue;
        const percent = this.state.opportunityData.commission_percent || 0;
        return (total * percent) / 100;
    }
}

registry.category('actions').add('bohio_timeline_view', BohioTimelineView);

export default BohioTimelineView;

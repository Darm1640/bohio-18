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
            additionalInfoExpanded: false,
            amenitiesExpanded: false,
            contractInfoExpanded: false,
            // Lista de oportunidades
            allOpportunities: [],
            filteredOpportunities: [],
            selectedOpportunityId: null,
            searchQuery: '',
            filterService: '',
            // Edición inline
            editing: {},
        });

        onWillStart(async () => {
            await this.loadAllOpportunities();
            await this.loadOpportunityData();
        });
    }

    async loadAllOpportunities() {
        const opportunities = await this.orm.searchRead(
            'crm.lead',
            [['type', '=', 'opportunity']],
            ['id', 'name', 'partner_id', 'partner_name', 'stage_id', 'probability', 'service_interested'],
            { limit: 100, order: 'write_date desc' }
        );

        this.state.allOpportunities = opportunities.map(opp => ({
            id: opp.id,
            name: opp.name,
            partner_name: opp.partner_name || (opp.partner_id ? opp.partner_id[1] : 'Sin cliente'),
            stage_name: opp.stage_id ? opp.stage_id[1] : 'Nueva',
            probability: opp.probability || 0,
            service_interested: opp.service_interested,
            initials: this.getInitials(opp.partner_name || (opp.partner_id ? opp.partner_id[1] : 'SC')),
        }));

        this.state.filteredOpportunities = [...this.state.allOpportunities];
    }

    getInitials(name) {
        if (!name) return 'SC';
        const parts = name.trim().split(' ');
        if (parts.length >= 2) {
            return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    }

    filterOpportunities() {
        let filtered = [...this.state.allOpportunities];

        // Filtro por búsqueda
        if (this.state.searchQuery) {
            const query = this.state.searchQuery.toLowerCase();
            filtered = filtered.filter(opp =>
                opp.name.toLowerCase().includes(query) ||
                opp.partner_name.toLowerCase().includes(query)
            );
        }

        // Filtro por servicio
        if (this.state.filterService) {
            filtered = filtered.filter(opp => opp.service_interested === this.state.filterService);
        }

        this.state.filteredOpportunities = filtered;
    }

    async selectOpportunity(opportunityId) {
        this.state.selectedOpportunityId = opportunityId;
        this.props.action.context.active_id = opportunityId;
        await this.loadOpportunityData();
    }

    async loadOpportunityData() {
        const opportunityId = this.props.action.context.active_id || this.state.selectedOpportunityId;
        if (!opportunityId) {
            // Si no hay oportunidad seleccionada, seleccionar la primera
            if (this.state.allOpportunities.length > 0) {
                this.state.selectedOpportunityId = this.state.allOpportunities[0].id;
                await this.selectOpportunity(this.state.selectedOpportunityId);
            }
            return;
        }

        this.state.selectedOpportunityId = opportunityId;
        const data = await this.orm.call('crm.lead', 'get_timeline_view_data', [opportunityId]);
        this.state.opportunityData = data;
        this.state.recommendedProperties = data.recommended_properties || [];
        this.state.comparisonProperties = data.comparison_properties || [];
    }

    // === ACTION BUTTONS ===
    async editOpportunity() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'crm.lead',
            res_id: this.state.opportunityData.id,
            views: [[false, 'form']],
            target: 'current',
        });
    }

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

    async generateQuote() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'sale.order',
            views: [[false, 'form']],
            target: 'current',
            context: {
                default_partner_id: this.state.opportunityData.partner_id[0],
                default_opportunity_id: this.state.opportunityData.id,
            }
        });
    }

    async printView() {
        window.print();
    }

    // === INLINE EDITING ===
    toggleEdit(fieldName) {
        this.state.editing[fieldName] = !this.state.editing[fieldName];
    }

    async saveField(fieldName) {
        const value = this.state.opportunityData[fieldName];
        const fieldMapping = {
            'partner_name': 'partner_name',
            'phone': 'phone',
            'email': 'email_from',
            'budget_min': 'budget_min',
            'budget_max': 'budget_max',
            // Información adicional
            'number_of_occupants': 'number_of_occupants',
            'has_pets': 'has_pets',
            'pet_type': 'pet_type',
            'requires_parking': 'requires_parking',
            'parking_spots': 'parking_spots',
            'occupation': 'occupation',
            'monthly_income': 'monthly_income',
            // Amenidades
            'requires_common_areas': 'requires_common_areas',
            'requires_gym': 'requires_gym',
            'requires_pool': 'requires_pool',
            'requires_security': 'requires_security',
            'requires_elevator': 'requires_elevator',
            'property_purpose': 'property_purpose',
            // Contractual
            'contract_start_date': 'contract_start_date',
            'contract_duration_months': 'contract_duration_months',
            'commission_percentage': 'commission_percentage',
        };

        const actualFieldName = fieldMapping[fieldName] || fieldName;

        try {
            await this.orm.write('crm.lead', [this.state.opportunityData.id], {
                [actualFieldName]: value
            });
            this.notification.add('Campo actualizado', { type: 'success' });
            this.state.editing[fieldName] = false;
            await this.loadOpportunityData();
        } catch (error) {
            this.notification.add('Error al guardar: ' + error.message, { type: 'danger' });
        }
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

    toggleAdditionalInfo() {
        this.state.additionalInfoExpanded = !this.state.additionalInfoExpanded;
    }

    toggleAmenities() {
        this.state.amenitiesExpanded = !this.state.amenitiesExpanded;
    }

    toggleContractInfo() {
        this.state.contractInfoExpanded = !this.state.contractInfoExpanded;
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

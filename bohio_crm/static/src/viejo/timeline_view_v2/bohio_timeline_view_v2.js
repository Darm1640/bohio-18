/** @odoo-module **/

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * BOHIO TIMELINE VIEW V2
 *
 * Vista timeline mejorada con:
 * - Modelo reactivo usando useState
 * - Chatter nativo integrado
 * - Actualización en tiempo real
 * - Campos completos de cliente
 * - Precios dinámicos según operación
 */
export class BohioTimelineViewV2 extends Component {
    static template = "bohio_crm.TimelineViewV2";
    static components = {};
    static props = {
        resModel: { type: String, optional: true },
        resId: { type: Number, optional: true },
        context: { type: Object, optional: true },
    };

    setup() {
        // Servicios de Odoo
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.dialog = useService("dialog");

        // Estado reactivo
        this.state = useState({
            // Datos del record actual
            record: null,
            resId: this.props.resId || this.props.context?.active_id,

            // Lista de oportunidades (sidebar)
            opportunities: [],
            filteredOpportunities: [],
            searchQuery: "",
            filterService: "",

            // Secciones expandibles
            sections: {
                client: false,
                preferences: false,
                additionalInfo: false,
                amenities: false,
                contract: false,
            },

            // Modo edición
            isEditMode: false,
            originalData: {},

            // Propiedades
            recommendedProperties: [],
            comparedProperties: [],

            // Configuración de vista
            compactFields: this._loadCompactFieldsConfig(),
            showConfigModal: false,

            // Loading states
            isLoading: false,
            isSaving: false,
        });

        onWillStart(async () => {
            await this._loadInitialData();
        });

        onMounted(() => {
            this._setupAutoRefresh();
        });
    }

    // ===================================
    // CARGA DE DATOS
    // ===================================

    async _loadInitialData() {
        this.state.isLoading = true;
        try {
            // Cargar lista de oportunidades
            await this._loadOpportunitiesList();

            // Cargar datos del record actual
            if (this.state.resId) {
                await this._loadRecordData(this.state.resId);
            } else if (this.state.opportunities.length > 0) {
                // Si no hay ID, cargar la primera oportunidad
                this.state.resId = this.state.opportunities[0].id;
                await this._loadRecordData(this.state.resId);
            }
        } catch (error) {
            console.error("Error al cargar datos iniciales:", error);
            this.notification.add(
                `Error al cargar la vista: ${error.message || 'Error desconocido'}`,
                { type: "danger" }
            );
        } finally {
            this.state.isLoading = false;
        }
    }

    async _loadOpportunitiesList() {
        const opportunities = await this.orm.searchRead(
            "crm.lead",
            [["type", "=", "opportunity"]],
            [
                "id", "name", "partner_id", "partner_name",
                "stage_id", "probability", "service_interested",
                "expected_revenue"
            ],
            { limit: 100, order: "write_date desc" }
        );

        this.state.opportunities = opportunities.map(opp => ({
            ...opp,
            initials: this._getInitials(opp.partner_name || opp.partner_id?.[1] || "NN"),
            stage_name: opp.stage_id?.[1] || "Nueva",
        }));

        this.state.filteredOpportunities = [...this.state.opportunities];
    }

    async _loadRecordData(resId) {
        this.state.isLoading = true;
        try {
            // Llamar al método del backend que retorna todos los datos
            const result = await this.orm.call(
                "crm.lead",
                "get_timeline_view_data",
                [[resId]]  // Pasar como recordset
            );

            // El método retorna un diccionario para un solo record
            this.state.record = result;

            // Cargar propiedades
            this.state.recommendedProperties = result.recommended_properties || [];
            this.state.comparedProperties = result.comparison_properties || [];

        } catch (error) {
            this.notification.add(
                `Error al cargar datos: ${error.message}`,
                { type: "danger" }
            );
        } finally {
            this.state.isLoading = false;
        }
    }

    _setupAutoRefresh() {
        // Actualizar cada 30 segundos si no está en modo edición
        this.refreshInterval = setInterval(() => {
            if (!this.state.isEditMode && this.state.resId) {
                this._loadRecordData(this.state.resId);
            }
        }, 30000);
    }

    willUnmount() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }

    // ===================================
    // NAVEGACIÓN DE OPORTUNIDADES
    // ===================================

    async selectOpportunity(oppId) {
        if (this.state.isEditMode) {
            this.notification.add(
                "Guarda o cancela los cambios antes de cambiar de oportunidad",
                { type: "warning" }
            );
            return;
        }

        this.state.resId = oppId;
        await this._loadRecordData(oppId);
    }

    filterOpportunities() {
        let filtered = [...this.state.opportunities];

        // Filtro por búsqueda
        if (this.state.searchQuery) {
            const query = this.state.searchQuery.toLowerCase();
            filtered = filtered.filter(
                opp =>
                    opp.name.toLowerCase().includes(query) ||
                    opp.partner_name?.toLowerCase().includes(query)
            );
        }

        // Filtro por servicio
        if (this.state.filterService) {
            filtered = filtered.filter(
                opp => opp.service_interested === this.state.filterService
            );
        }

        this.state.filteredOpportunities = filtered;
    }

    // ===================================
    // MODO EDICIÓN
    // ===================================

    enableEditMode() {
        // Guardar copia de datos originales
        this.state.originalData = JSON.parse(JSON.stringify(this.state.record));
        this.state.isEditMode = true;

        // Expandir todas las secciones
        Object.keys(this.state.sections).forEach(key => {
            this.state.sections[key] = true;
        });
    }

    async saveAllChanges() {
        this.state.isSaving = true;
        try {
            // Preparar datos para guardar
            const fieldsToSave = {
                // Básicos
                partner_name: this.state.record.partner_name,
                phone: this.state.record.phone,
                email_from: this.state.record.email,
                client_type: this.state.record.client_type,
                service_interested: this.state.record.service_interested,

                // Presupuesto
                budget_min: this.state.record.min_budget,
                budget_max: this.state.record.max_budget,

                // Métricas
                expected_revenue: this.state.record.expected_revenue,
                probability: this.state.record.probability,
                commission_percentage: this.state.record.commission_percent,

                // Preferencias de propiedad
                desired_city: this.state.record.desired_city,
                desired_neighborhood: this.state.record.desired_neighborhood,
                min_bedrooms: this.state.record.min_bedrooms,
                ideal_bedrooms: this.state.record.ideal_bedrooms,
                min_bathrooms: this.state.record.min_bathrooms,
                min_area: this.state.record.min_area,
                max_area: this.state.record.max_area,

                // Información adicional
                number_of_occupants: this.state.record.number_of_occupants,
                has_pets: this.state.record.has_pets,
                pet_type: this.state.record.pet_type,
                requires_parking: this.state.record.requires_parking,
                parking_spots: this.state.record.parking_spots,
                occupation: this.state.record.occupation,
                monthly_income: this.state.record.monthly_income,

                // Amenidades
                requires_common_areas: this.state.record.requires_common_areas,
                requires_gym: this.state.record.requires_gym,
                requires_pool: this.state.record.requires_pool,
                requires_security: this.state.record.requires_security,
                requires_elevator: this.state.record.requires_elevator,
                property_purpose: this.state.record.property_purpose,

                // Contractual
                contract_start_date: this.state.record.contract_start_date,
                contract_duration_months: this.state.record.contract_duration_months,
            };

            // Guardar en backend
            await this.orm.write("crm.lead", [this.state.resId], fieldsToSave);

            this.notification.add("Cambios guardados exitosamente", {
                type: "success",
            });

            this.state.isEditMode = false;
            this.state.originalData = {};

            // Recargar datos
            await this._loadRecordData(this.state.resId);

        } catch (error) {
            this.notification.add(`Error al guardar: ${error.message}`, {
                type: "danger",
            });
        } finally {
            this.state.isSaving = false;
        }
    }

    cancelEditMode() {
        // Restaurar datos originales
        this.state.record = JSON.parse(JSON.stringify(this.state.originalData));
        this.state.isEditMode = false;
        this.state.originalData = {};

        this.notification.add("Cambios cancelados", { type: "info" });
    }

    enableFieldEdit(fieldName, sectionName = null) {
        if (!this.state.isEditMode) {
            this.enableEditMode();
        }

        if (sectionName && this.state.sections[sectionName] !== undefined) {
            this.state.sections[sectionName] = true;
        }
    }

    // ===================================
    // CAMBIO DE ETAPA
    // ===================================

    async changeStage(stageId) {
        try {
            await this.orm.write("crm.lead", [this.state.resId], {
                stage_id: stageId,
            });

            this.notification.add("Etapa actualizada", { type: "success" });
            await this._loadRecordData(this.state.resId);

        } catch (error) {
            this.notification.add(`Error al cambiar etapa: ${error.message}`, {
                type: "danger",
            });
        }
    }

    // ===================================
    // ACCIONES
    // ===================================

    async createNewOpportunity() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "crm.lead",
            views: [[false, "form"]],
            target: "current",
            context: {
                default_type: "opportunity",
            },
        });
    }

    openFullForm() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "crm.lead",
            res_id: this.state.resId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    async createActivity() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "mail.activity",
            views: [[false, "form"]],
            target: "new",
            context: {
                default_res_id: this.state.resId,
                default_res_model: "crm.lead",
            },
        });
    }

    async generateQuote() {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "sale.order",
            views: [[false, "form"]],
            target: "current",
            context: {
                default_partner_id: this.state.record.partner_id?.[0],
                default_opportunity_id: this.state.resId,
            },
        });
    }

    async generateContract() {
        try {
            const result = await this.orm.call(
                "crm.lead",
                "action_close_lead_with_contract",
                [this.state.resId]
            );

            if (result) {
                this.action.doAction(result);
            }
        } catch (error) {
            this.notification.add(`Error: ${error.message}`, { type: "danger" });
        }
    }

    // ===================================
    // CONFIGURACIÓN DE VISTA
    // ===================================

    _loadCompactFieldsConfig() {
        const defaultFields = [
            "partner_name",
            "phone",
            "email",
            "service_interested",
            "budget_min",
            "budget_max",
        ];

        try {
            const saved = localStorage.getItem("bohio_timeline_compact_fields");
            return saved ? JSON.parse(saved) : defaultFields;
        } catch {
            return defaultFields;
        }
    }

    saveViewConfig() {
        localStorage.setItem(
            "bohio_timeline_compact_fields",
            JSON.stringify(this.state.compactFields)
        );

        this.state.showConfigModal = false;
        this.notification.add("Configuración guardada", { type: "success" });
    }

    // ===================================
    // PROPIEDADES
    // ===================================

    async addToComparison(propertyId) {
        try {
            await this.orm.call(
                "crm.lead",
                "add_property_to_comparison",
                [this.state.resId, propertyId]
            );

            await this._loadRecordData(this.state.resId);

        } catch (error) {
            this.notification.add(`Error: ${error.message}`, { type: "danger" });
        }
    }

    async refreshRecommendations() {
        try {
            const recommendations = await this.orm.call(
                "crm.lead",
                "get_ai_recommendations",
                [[this.state.resId]]
            );

            this.state.recommendedProperties = recommendations;
            this.notification.add("Recomendaciones actualizadas", { type: "success" });

        } catch (error) {
            this.notification.add(`Error: ${error.message}`, { type: "danger" });
        }
    }

    async removeFromComparison(propertyId) {
        try {
            // Remover de la lista de comparación
            await this.orm.write(
                "crm.lead",
                [this.state.resId],
                {
                    compared_properties_ids: [[3, propertyId]]  // Comando 3 = unlink
                }
            );

            // Recargar datos
            await this._loadRecordData(this.state.resId);
            this.notification.add("Propiedad removida de la comparación", { type: "success" });

        } catch (error) {
            this.notification.add(`Error: ${error.message}`, { type: "danger" });
        }
    }

    async viewPropertyDetails(propertyId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "product.template",
            res_id: propertyId,
            views: [[false, "form"]],
            target: "new",
        });
    }

    // ===================================
    // UTILIDADES
    // ===================================

    _getInitials(name) {
        if (!name) return "NN";
        const parts = name.trim().split(" ");
        if (parts.length >= 2) {
            return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    }

    toggleSection(sectionName) {
        this.state.sections[sectionName] = !this.state.sections[sectionName];
    }

    // ===================================
    // GETTERS COMPUTADOS
    // ===================================

    get completionPercentage() {
        if (!this.state.record) return 0;

        const data = this.state.record;
        let completed = 0;
        const total = 10;

        if (data.partner_id?.[0]) completed++;
        if (data.service_interested) completed++;
        if (data.min_budget) completed++;
        if (data.phone) completed++;
        if (data.email) completed++;
        if (data.client_type) completed++;
        if (this.state.comparedProperties.length > 0) completed++;
        if (data.number_of_occupants) completed++;
        if (data.desired_neighborhood) completed++;
        if (data.expected_revenue) completed++;

        return Math.round((completed / total) * 100);
    }

    get totalRevenue() {
        if (!this.state.record) return "$0";

        const expected = this.state.record.expected_revenue || 0;
        const recurring = (this.state.record.recurring_revenue || 0) * 12;
        const total = expected + recurring;

        return this._formatCurrency(total);
    }

    get commissionAmount() {
        if (!this.state.record) return "$0";

        const total = (this.state.record.expected_revenue || 0) +
                     ((this.state.record.recurring_revenue || 0) * 12);
        const percent = this.state.record.commission_percent || 0;
        const commission = (total * percent) / 100;

        return this._formatCurrency(commission);
    }

    _formatCurrency(amount) {
        if (!amount) return "$0";
        return `$${amount.toLocaleString("es-CO", { maximumFractionDigits: 0 })}`;
    }
}

// Registrar el componente como acción cliente
registry.category("actions").add("bohio_timeline_view_v2", BohioTimelineViewV2);

export default BohioTimelineViewV2;

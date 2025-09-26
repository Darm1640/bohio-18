/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class CrmDashboard extends Component {
    static template = "bohio_real_estate.CrmDashboard";

    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            metrics: {
                total_leads: 0,
                expected_revenue: 0,
                active_properties: 0,
                conversion_rate: 0,
            },
            pipeline: [],
            activities: [],
            topSellers: [],
            properties: [],
            isLoading: true,
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    async loadDashboardData() {
        try {
            // Cargar métricas principales
            const leads = await this.rpc("/web/dataset/search_read", {
                model: "crm.lead",
                domain: [["active", "=", true], ["type", "=", "opportunity"]],
                fields: ["expected_revenue", "stage_id", "probability", "user_id"],
            });

            // Calcular métricas
            const totalLeads = leads.length;
            const totalRevenue = leads.reduce((sum, lead) => sum + (lead.expected_revenue || 0), 0);
            const wonLeads = leads.filter(lead => lead.probability === 100);
            const conversionRate = totalLeads > 0 ? (wonLeads.length / totalLeads * 100).toFixed(1) : 0;

            // Cargar propiedades activas
            const properties = await this.rpc("/web/dataset/search_read", {
                model: "product.template",
                domain: [["state", "=", "free"]],
                fields: ["name", "list_price", "default_code"],
                limit: 10,
            });

            // Pipeline por etapas
            const stages = await this.rpc("/web/dataset/search_read", {
                model: "crm.stage",
                domain: [],
                fields: ["name", "sequence"],
                order: "sequence",
            });

            const pipeline = stages.map(stage => {
                const stageLeads = leads.filter(lead => lead.stage_id && lead.stage_id[0] === stage.id);
                return {
                    id: stage.id,
                    name: stage.name,
                    count: stageLeads.length,
                    amount: stageLeads.reduce((sum, lead) => sum + (lead.expected_revenue || 0), 0),
                };
            });

            // Actividades próximas
            const activities = await this.rpc("/web/dataset/search_read", {
                model: "mail.activity",
                domain: [
                    ["res_model", "=", "crm.lead"],
                    ["date_deadline", ">=", new Date().toISOString().split('T')[0]],
                ],
                fields: ["res_name", "date_deadline", "user_id", "activity_type_id"],
                limit: 5,
                order: "date_deadline",
            });

            // Top vendedores
            const userStats = {};
            leads.forEach(lead => {
                if (lead.user_id) {
                    const userId = lead.user_id[0];
                    const userName = lead.user_id[1];
                    if (!userStats[userId]) {
                        userStats[userId] = {
                            id: userId,
                            name: userName,
                            count: 0,
                            revenue: 0,
                        };
                    }
                    userStats[userId].count++;
                    userStats[userId].revenue += lead.expected_revenue || 0;
                }
            });

            const topSellers = Object.values(userStats)
                .sort((a, b) => b.revenue - a.revenue)
                .slice(0, 5);

            // Actualizar estado
            this.state.metrics = {
                total_leads: totalLeads,
                expected_revenue: totalRevenue,
                active_properties: properties.length,
                conversion_rate: conversionRate,
            };
            this.state.pipeline = pipeline;
            this.state.activities = activities;
            this.state.topSellers = topSellers;
            this.state.properties = properties;
            this.state.isLoading = false;

        } catch (error) {
            console.error("Error loading dashboard data:", error);
            this.state.isLoading = false;
        }
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
        }).format(amount);
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const options = { day: 'numeric', month: 'short', year: 'numeric' };
        return date.toLocaleDateString('es-CO', options);
    }

    getActivityIcon(activityType) {
        const icons = {
            'Call': 'fa-phone',
            'Meeting': 'fa-calendar',
            'Email': 'fa-envelope',
            'Todo': 'fa-check-square',
        };
        return icons[activityType] || 'fa-tasks';
    }
}

// Registrar el componente
registry.category("actions").add("bohio_real_estate.crm_dashboard", CrmDashboard);

// Widget de Kanban mejorado para CRM
export class CrmKanbanController extends Component {
    static template = "bohio_real_estate.CrmKanbanController";

    setup() {
        super.setup();
        this.rpc = useService("rpc");

        // Agregar funcionalidades adicionales al kanban
        onWillStart(async () => {
            await this.loadPropertyData();
        });
    }

    async loadPropertyData() {
        // Cargar datos de propiedades relacionadas si existen
        try {
            const records = this.model.root.records;
            for (const record of records) {
                if (record.data.partner_id) {
                    const properties = await this.rpc("/web/dataset/search_read", {
                        model: "product.template",
                        domain: [["partner_id", "=", record.data.partner_id[0]]],
                        fields: ["name", "default_code", "list_price"],
                        limit: 1,
                    });

                    if (properties.length > 0) {
                        record.data.x_property_id = {
                            id: properties[0].id,
                            value: properties[0].default_code || properties[0].name,
                        };
                    }
                }
            }
        } catch (error) {
            console.error("Error loading property data:", error);
        }
    }
}
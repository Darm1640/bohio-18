/** @odoo-module **/

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class CrmMetricsWidget extends Component {
    static template = "bohio_real_estate.CrmMetricsWidget";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.router = useService("router");

        this.state = useState({
            metrics: {
                availableProperties: 0,
                monthlyRevenue: 0,
                totalOpportunities: 0,
                accountsReceivable: 0,
                pendingActivities: 0,
                urgentActivities: 0,
                visits: 0,
                won: 0,
                lost: 0,
                inProgress: 0,
                conversionRate: 0,
                averageTime: 0,
                averageValue: 0,
            },
            loading: true,
            selectedPeriod: 'month',
        });

        onWillStart(async () => {
            await this.loadMetrics();
        });

        onMounted(() => {
            this.initializeCharts();
            this.attachEventListeners();
        });
    }

    async loadMetrics() {
        try {
            // Cargar todas las métricas en paralelo
            const [properties, revenue, opportunities, receivables, activities] = await Promise.all([
                this.getAvailableProperties(),
                this.getMonthlyRevenue(),
                this.getOpportunities(),
                this.getAccountsReceivable(),
                this.getPendingActivities(),
            ]);

            this.state.metrics = {
                availableProperties: properties.count,
                monthlyRevenue: revenue.total,
                totalOpportunities: opportunities.total,
                accountsReceivable: receivables.total,
                pendingActivities: activities.pending,
                urgentActivities: activities.urgent,
                visits: opportunities.visits,
                won: opportunities.won,
                lost: opportunities.lost,
                inProgress: opportunities.in_progress,
                conversionRate: opportunities.conversion_rate,
                averageTime: opportunities.average_time,
                averageValue: opportunities.average_value,
            };

            this.state.loading = false;
        } catch (error) {
            console.error("Error loading metrics:", error);
            this.notification.add(_t("Error al cargar las métricas"), {
                type: "danger"
            });
            this.state.loading = false;
        }
    }

    async getAvailableProperties() {
        const domain = [
            ['is_property', '=', true],
            ['property_status', '=', 'available']
        ];
        const count = await this.orm.searchCount("product.template", domain);
        return { count };
    }

    async getMonthlyRevenue() {
        const date = new Date();
        const firstDay = new Date(date.getFullYear(), date.getMonth(), 1);
        const lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);

        const domain = [
            ['state', 'in', ['sale', 'done']],
            ['date_order', '>=', firstDay.toISOString().split('T')[0]],
            ['date_order', '<=', lastDay.toISOString().split('T')[0]]
        ];

        const orders = await this.orm.searchRead(
            "sale.order",
            domain,
            ["amount_total"]
        );

        const total = orders.reduce((sum, order) => sum + order.amount_total, 0);
        return { total };
    }

    async getOpportunities() {
        const domain = [['type', '=', 'opportunity']];

        // Obtener oportunidades por estado
        const opportunities = await this.orm.searchRead(
            "crm.lead",
            domain,
            ["stage_id", "expected_revenue", "probability", "create_date"]
        );

        // Calcular métricas
        const total = opportunities.length;
        const won = opportunities.filter(o => o.probability === 100).length;
        const lost = opportunities.filter(o => o.probability === 0).length;
        const in_progress = total - won - lost;
        const visits = await this.orm.searchCount("crm.lead", [
            ...domain,
            ['tag_ids', 'ilike', 'visita']
        ]);

        const conversion_rate = total > 0 ? Math.round((won / total) * 100) : 0;
        const average_value = total > 0
            ? opportunities.reduce((sum, o) => sum + o.expected_revenue, 0) / total
            : 0;

        // Calcular tiempo promedio (simplificado)
        const average_time = 12; // días promedio

        return {
            total,
            won,
            lost,
            in_progress,
            visits,
            conversion_rate,
            average_time,
            average_value
        };
    }

    async getAccountsReceivable() {
        const domain = [
            ['move_type', '=', 'out_invoice'],
            ['state', '=', 'posted'],
            ['payment_state', 'in', ['not_paid', 'partial']]
        ];

        const invoices = await this.orm.searchRead(
            "account.move",
            domain,
            ["amount_residual"]
        );

        const total = invoices.reduce((sum, inv) => sum + inv.amount_residual, 0);
        return { total };
    }

    async getPendingActivities() {
        const today = new Date().toISOString().split('T')[0];

        const domain = [
            ['date_deadline', '=', today],
            ['user_id', '=', this.env.user.id]
        ];

        const pending = await this.orm.searchCount("mail.activity", domain);

        const urgentDomain = [
            ['date_deadline', '<', today],
            ['user_id', '=', this.env.user.id]
        ];

        const urgent = await this.orm.searchCount("mail.activity", urgentDomain);

        return { pending, urgent };
    }

    // Navegación a diferentes vistas
    navigateToProperties() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: _t('Propiedades Disponibles'),
            res_model: 'product.template',
            view_mode: 'kanban,list,form',
            views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
            domain: [['is_property', '=', true], ['property_status', '=', 'available']],
            context: {
                default_is_property: true,
            },
            target: 'current',
        });
    }

    navigateToRevenue() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: _t('Ventas del Mes'),
            res_model: 'sale.order',
            view_mode: 'list,form,kanban,pivot,graph',
            views: [[false, 'list'], [false, 'form'], [false, 'kanban'], [false, 'pivot'], [false, 'graph']],
            domain: this.getMonthDomain(),
            context: {},
            target: 'current',
        });
    }

    navigateToOpportunities() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: _t('Oportunidades CRM'),
            res_model: 'crm.lead',
            view_mode: 'kanban,list,form,calendar,pivot,graph',
            views: [[false, 'kanban'], [false, 'list'], [false, 'form'], [false, 'calendar'], [false, 'pivot'], [false, 'graph']],
            domain: [['type', '=', 'opportunity']],
            context: {
                default_type: 'opportunity',
                search_default_my_opportunities: 1,
            },
            target: 'current',
        });
    }

    navigateToReceivables() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: _t('Cuentas por Cobrar'),
            res_model: 'account.move',
            view_mode: 'list,form,kanban',
            views: [[false, 'list'], [false, 'form'], [false, 'kanban']],
            domain: [
                ['move_type', '=', 'out_invoice'],
                ['state', '=', 'posted'],
                ['payment_state', 'in', ['not_paid', 'partial']]
            ],
            context: {},
            target: 'current',
        });
    }

    navigateToActivities() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: _t('Actividades Pendientes'),
            res_model: 'mail.activity',
            view_mode: 'list,form,calendar',
            views: [[false, 'list'], [false, 'form'], [false, 'calendar']],
            domain: [['user_id', '=', this.env.user.id]],
            context: {},
            target: 'current',
        });
    }

    // Abrir wizard para registrar gasto
    openExpenseWizard() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: _t('Registrar Gasto'),
            res_model: 'hr.expense',
            view_mode: 'form',
            views: [[false, 'form']],
            context: {
                default_employee_id: this.env.user.employee_id,
                default_date: new Date().toISOString().split('T')[0],
                form_view_initial_mode: 'edit',
            },
            target: 'new',
        });
    }

    // Abrir reporte de gastos
    openExpenseReport() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: _t('Reporte de Gastos'),
            res_model: 'hr.expense',
            view_mode: 'pivot,graph,list,form',
            views: [[false, 'pivot'], [false, 'graph'], [false, 'list'], [false, 'form']],
            domain: [],
            context: {
                search_default_group_by_date: 1,
                search_default_group_by_employee: 1,
            },
            target: 'current',
        });
    }

    // Cambiar período de visualización
    changePeriod(period) {
        this.state.selectedPeriod = period;
        this.loadMetrics();
    }

    getMonthDomain() {
        const date = new Date();
        const firstDay = new Date(date.getFullYear(), date.getMonth(), 1);
        const lastDay = new Date(date.getFullYear(), date.getMonth() + 1, 0);

        return [
            ['date_order', '>=', firstDay.toISOString().split('T')[0]],
            ['date_order', '<=', lastDay.toISOString().split('T')[0]]
        ];
    }

    initializeCharts() {
        // Inicializar mini gráficos si Chart.js está disponible
        if (typeof Chart !== 'undefined') {
            this.renderSparkline();
            this.renderTrendChart();
        }
    }

    renderSparkline() {
        const canvas = this.el.querySelector('#opportunities_sparkline');
        if (canvas) {
            const ctx = canvas.getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['', '', '', '', '', '', ''],
                    datasets: [{
                        data: [12, 19, 3, 5, 2, 15, 20],
                        borderColor: '#FFD700',
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4,
                        pointRadius: 0,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: { enabled: false }
                    },
                    scales: {
                        x: { display: false },
                        y: { display: false }
                    }
                }
            });
        }
    }

    renderTrendChart() {
        const canvas = this.el.querySelector('#crm_trends_chart');
        if (canvas) {
            const ctx = canvas.getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Oportunidades',
                        data: [65, 59, 80, 81, 95, 112],
                        borderColor: '#8B4513',
                        backgroundColor: 'rgba(139, 69, 19, 0.1)',
                        tension: 0.4,
                    }, {
                        label: 'Ganadas',
                        data: [45, 39, 60, 71, 85, 92],
                        borderColor: '#27ae60',
                        backgroundColor: 'rgba(39, 174, 96, 0.1)',
                        tension: 0.4,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 15,
                                boxWidth: 12,
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                borderDash: [5, 5]
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        }
    }

    attachEventListeners() {
        // Hacer las métricas clickeables
        const metricsContainer = this.el.querySelector('.metrics-row');
        if (metricsContainer) {
            metricsContainer.addEventListener('click', (e) => {
                const metricCard = e.target.closest('.metric-card');
                if (metricCard) {
                    if (metricCard.classList.contains('available-properties')) {
                        this.navigateToProperties();
                    } else if (metricCard.classList.contains('monthly-revenue')) {
                        this.navigateToRevenue();
                    } else if (metricCard.classList.contains('opportunities')) {
                        this.navigateToOpportunities();
                    } else if (metricCard.classList.contains('accounts-receivable')) {
                        this.navigateToReceivables();
                    } else if (metricCard.classList.contains('pending-activities')) {
                        this.navigateToActivities();
                    }
                }
            });
        }

        // Filtros de período
        const filterBtns = this.el.querySelectorAll('.filter-btn');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                filterBtns.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.changePeriod(e.target.dataset.period);
            });
        });
    }

    formatCurrency(value) {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0
        }).format(value);
    }
}

// Registrar el widget
registry.category("fields").add("crm_metrics_widget", CrmMetricsWidget);
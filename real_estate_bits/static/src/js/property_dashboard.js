/** @odoo-module **/

import { Component, onWillStart, onMounted, useState, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { loadJS } from "@web/core/assets";

export class PropertyDashboard extends Component {
    static template = "real_estate_bits.PropertyDashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            dashboardData: {
                properties_by_status: [],
                properties_by_region: [],
                expected_income: [],
                properties_by_salesperson: [],
                properties_by_type: [],
                recent_activities: [],
                map_data: [],
                contracts_data: {},
                contracts_by_status: [],
                monthly_billing: [],
                payment_collection: [],
                new_contracts_month: [],
                user_info: {}
            },
            selectedSalesperson: null,
            salespersonProperties: [],
            loading: true,
            mapLoaded: false,
            contractFilters: {
                period: 'month',
                contract_type: '',
                property_type: '',
                state: ''
            },
            showContractsSection: true
        });

        this.mapRef = useRef("mapContainer");
        this.chartRefs = {
            statusChart: useRef("statusChart"),
            typeChart: useRef("typeChart"),
            incomeChart: useRef("incomeChart"),
            contractStatusChart: useRef("contractStatusChart"),
            billingChart: useRef("billingChart"),
            collectionChart: useRef("collectionChart"),
            opportunityChart: useRef("opportunityChart")
        };

        onWillStart(async () => {
            await this.loadDashboardData();
        });

        onMounted(() => {
            this.initializeCharts();
            this.initializeMap();
        });
    }

    async loadDashboardData() {
        try {
            const data = await this.orm.call(
                "property.dashboard",
                "get_dashboard_data",
                []
            );
            // Ensure all arrays are defined with default values
            this.state.dashboardData = {
                properties_by_status: data.properties_by_status || [],
                properties_by_region: data.properties_by_region || [],
                expected_income: data.expected_income || [],
                properties_by_salesperson: data.properties_by_salesperson || [],
                properties_by_type: data.properties_by_type || [],
                recent_activities: data.recent_activities || [],
                map_data: data.map_data || [],
                contracts_data: data.contracts_data || {},
                contracts_by_status: data.contracts_by_status || [],
                monthly_billing: data.monthly_billing || [],
                payment_collection: data.payment_collection || [],
                new_contracts_month: data.new_contracts_month || [],
                user_info: data.user_info || {}
            };
            this.state.loading = false;
        } catch (error) {
            this.notification.add(_t("Error al cargar datos del dashboard"), {
                type: "danger"
            });
            console.error("Dashboard loading error:", error);
            this.state.loading = false;
        }
    }

    initializeCharts() {
        // Wait for Chart.js to be available
        if (typeof Chart === 'undefined') {
            // Chart.js should be loaded via assets, wait for it
            setTimeout(() => {
                this.initializeCharts();
            }, 100);
            return;
        }
        this.renderCharts();
    }

    renderCharts() {
        this.renderStatusChart();
        this.renderTypeChart();
        this.renderIncomeChart();
        this.renderContractCharts();
    }

    renderContractCharts() {
        if (!this.state.dashboardData.contracts_data) return;

        this.renderContractStatusChart();
        this.renderBillingChart();
        this.renderCollectionChart();
        this.renderOpportunityChart();
    }

    renderStatusChart() {
        const ctx = this.chartRefs.statusChart.el;
        if (!ctx) return;

        const data = this.state.dashboardData.properties_by_status;

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(d => d.label),
                datasets: [{
                    data: data.map(d => d.count),
                    backgroundColor: [
                        '#28a745',
                        '#17a2b8',
                        '#ffc107',
                        '#dc3545',
                        '#6c757d'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
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
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                return label + ': ' + value + ' propiedades';
                            }
                        }
                    }
                }
            }
        });
    }

    renderTypeChart() {
        const ctx = this.chartRefs.typeChart.el;
        if (!ctx) return;

        const data = this.state.dashboardData.properties_by_type;

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.type_name),
                datasets: [{
                    label: 'Cantidad de Propiedades',
                    data: data.map(d => d.count),
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: function(context) {
                                const item = data[context.dataIndex];
                                return [
                                    'Precio promedio: $' + (item.avg_price || 0).toFixed(0),
                                    'Precio mín: $' + (item.min_price || 0).toFixed(0),
                                    'Precio máx: $' + (item.max_price || 0).toFixed(0)
                                ];
                            }
                        }
                    }
                }
            }
        });
    }

    renderIncomeChart() {
        const ctx = this.chartRefs.incomeChart.el;
        if (!ctx) return;

        const data = this.state.dashboardData.expected_income;

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.property_type || 'Sin tipo'),
                datasets: [{
                    label: 'Ingreso Mensual Esperado',
                    data: data.map(d => d.monthly_income || 0),
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(0);
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Ingreso: $' + (context.parsed.x || 0).toFixed(0);
                            }
                        }
                    }
                }
            }
        });
    }

    async initializeMap() {
        // Cargar Leaflet para el mapa
        if (!window.L) {
            await loadJS("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js");
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
            document.head.appendChild(link);

            setTimeout(() => {
                this.renderMap();
            }, 500);
        } else {
            this.renderMap();
        }
    }

    renderMap() {
        if (!this.mapRef.el || this.state.mapLoaded) return;

        const mapData = this.state.dashboardData.map_data;
        const regionData = this.state.dashboardData.properties_by_region;

        // Crear mapa centrado en Colombia por defecto
        const map = L.map(this.mapRef.el).setView([4.570868, -74.297333], 6);

        // Agregar capa de mapa
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(map);

        // Agregar marcadores de barrios con cantidad de propiedades
        regionData.forEach(region => {
            if (region.latitude && region.longitude) {
                const marker = L.circleMarker([region.latitude, region.longitude], {
                    radius: Math.min(20, 5 + region.property_count),
                    fillColor: this.getColorByCount(region.property_count),
                    color: '#000',
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.7
                }).addTo(map);

                marker.bindPopup(`
                    <div class="map-popup">
                        <h6>${region.region_name}</h6>
                        <p>Propiedades: <strong>${region.property_count}</strong></p>
                        <p>Valor total: <strong>$${(region.total_value || 0).toFixed(0)}</strong></p>
                        <p>Precio promedio: <strong>$${(region.avg_price || 0).toFixed(0)}</strong></p>
                    </div>
                `);
            }
        });

        // Si hay datos de ubicación, ajustar el zoom
        if (regionData.length > 0) {
            const bounds = [];
            regionData.forEach(region => {
                if (region.latitude && region.longitude) {
                    bounds.push([region.latitude, region.longitude]);
                }
            });
            if (bounds.length > 0) {
                map.fitBounds(bounds);
            }
        }

        this.state.mapLoaded = true;
    }

    getColorByCount(count) {
        if (count > 50) return '#ff0000';
        if (count > 30) return '#ff6600';
        if (count > 15) return '#ffcc00';
        if (count > 5) return '#99ff00';
        return '#00ff00';
    }

    async onSalespersonClick(ev, salesperson) {
        const userId = salesperson.user_id;
        if (!userId) return;

        this.state.selectedSalesperson = salesperson;

        try {
            const properties = await this.orm.call(
                "property.dashboard",
                "get_salesperson_properties",
                [userId]
            );
            this.state.salespersonProperties = properties;
        } catch (error) {
            this.notification.add(_t("Error al cargar propiedades del vendedor"), {
                type: "danger"
            });
        }
    }

    onPropertyClick(propertyId) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'product.template',
            res_id: propertyId,
            views: [[false, 'form']],
            target: 'current',
        });
    }

    onViewAllProperties() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'product.template',
            name: _t('Propiedades'),
            view_mode: 'kanban,list,form',
            views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
            domain: [['is_property', '=', true]],
            context: {
                default_is_property: true,
            },
            target: 'current',
        });
    }

    formatCurrency(value) {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value || 0);
    }

    getStatusClass(status) {
        const classes = {
            'new': 'badge-primary',
            'available': 'badge-success',
            'booked': 'badge-warning',
            'rented': 'badge-info',
            'sold': 'badge-danger'
        };
        return classes[status] || 'badge-secondary';
    }

    getStatusLabel(status) {
        const labels = {
            'new': 'Nuevo',
            'available': 'Disponible',
            'booked': 'Reservado',
            'rented': 'Alquilado',
            'sold': 'Vendido'
        };
        return labels[status] || status;
    }

    renderContractStatusChart() {
        const ctx = this.chartRefs.contractStatusChart.el;
        if (!ctx) return;

        const data = this.state.dashboardData.contracts_by_status || [];

        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: data.map(d => d.label),
                datasets: [{
                    data: data.map(d => d.count),
                    backgroundColor: [
                        '#6c757d',
                        '#28a745',
                        '#17a2b8',
                        '#dc3545'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            padding: 10,
                            font: {
                                size: 11
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const dataset = data[context.dataIndex];
                                return [
                                    label + ': ' + value + ' contratos',
                                    'Valor total: $' + (dataset.total_value || 0).toFixed(0)
                                ];
                            }
                        }
                    }
                }
            }
        });
    }

    renderBillingChart() {
        const ctx = this.chartRefs.billingChart.el;
        if (!ctx) return;

        const data = this.state.dashboardData.monthly_billing || [];

        // Agrupar por fecha y calcular totales
        const dates = [...new Set(data.map(d => d.date))];
        const billingData = dates.map(date => {
            const dayData = data.filter(d => d.date === date);
            return {
                date: date,
                total: dayData.reduce((sum, d) => sum + (d.total_amount || 0), 0),
                paid: dayData.reduce((sum, d) => sum + (d.paid_amount || 0), 0)
            };
        });

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: billingData.map(d => new Date(d.date).toLocaleDateString('es-CO', { day: '2-digit', month: 'short' })),
                datasets: [{
                    label: 'Facturado',
                    data: billingData.map(d => d.total),
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    tension: 0.3,
                    fill: true
                }, {
                    label: 'Recaudado',
                    data: billingData.map(d => d.paid),
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Facturación vs Recaudo del Mes'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': $' + context.parsed.y.toFixed(0);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(0);
                            }
                        }
                    }
                }
            }
        });
    }

    renderCollectionChart() {
        const ctx = this.chartRefs.collectionChart.el;
        if (!ctx) return;

        const data = this.state.dashboardData.payment_collection || [];

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.contract_type === 'is_rental' ? 'Arrendamiento' : 'Propiedad'),
                datasets: [{
                    label: 'Recaudado',
                    data: data.map(d => d.total_paid || 0),
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }, {
                    label: 'Pendiente',
                    data: data.map(d => d.total_balance || 0),
                    backgroundColor: 'rgba(255, 99, 132, 0.6)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Estado de Recaudo por Tipo'
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: function(context) {
                                const item = data[context.dataIndex];
                                return 'Porcentaje recaudado: ' + (item.collection_percentage || 0).toFixed(1) + '%';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        stacked: true
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(0);
                            }
                        }
                    }
                }
            }
        });
    }

    renderOpportunityChart() {
        const ctx = this.chartRefs.opportunityChart.el;
        if (!ctx) return;

        // Calcular oportunidades basadas en propiedades disponibles vs ocupadas
        const statusData = this.state.dashboardData.properties_by_status || [];
        const contractData = this.state.dashboardData.contracts_data || {};

        const available = statusData.find(s => s.label === 'Disponible')?.count || 0;
        const rented = statusData.find(s => s.label === 'Alquilado')?.count || 0;
        const sold = statusData.find(s => s.label === 'Vendido')?.count || 0;
        const booked = statusData.find(s => s.label === 'Reservado')?.count || 0;

        const opportunityRate = available > 0 ? ((booked + available) / (available + rented + sold) * 100) : 0;

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Oportunidad', 'Ocupado', 'En Proceso'],
                datasets: [{
                    data: [available, rented + sold, booked],
                    backgroundColor: [
                        'rgba(46, 204, 113, 0.7)',
                        'rgba(52, 152, 219, 0.7)',
                        'rgba(241, 196, 15, 0.7)'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
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
                            font: {
                                size: 12
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: `Tasa de Oportunidad: ${opportunityRate.toFixed(1)}%`,
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return label + ': ' + value + ' (' + percentage + '%)';
                            }
                        }
                    }
                },
                cutout: '60%'
            }
        });
    }

    async onFilterChange(filterType, value) {
        this.state.contractFilters[filterType] = value;

        // Llamar al backend con los filtros
        try {
            const filteredData = await this.orm.call(
                "property.dashboard",
                "get_filtered_contracts_data",
                [this.state.contractFilters]
            );

            // Actualizar datos del dashboard con los resultados filtrados
            Object.assign(this.state.dashboardData, filteredData);

            // Re-renderizar gráficos de contratos
            this.renderContractCharts();
        } catch (error) {
            this.notification.add(_t("Error al aplicar filtros"), {
                type: "danger"
            });
        }
    }

    getContractTypeLabel(type) {
        return type === 'is_rental' ? 'Arrendamiento' : 'Propiedad';
    }

    getContractStateLabel(state) {
        const labels = {
            'draft': 'Borrador',
            'confirmed': 'Confirmado',
            'renew': 'Renovado',
            'cancel': 'Cancelado'
        };
        return labels[state] || state;
    }

    onToggleContractsSection() {
        this.state.showContractsSection = !this.state.showContractsSection;
    }
}

registry.category("actions").add("property_dashboard", PropertyDashboard);
/** @odoo-module */

import { Component, onWillStart, onMounted, useState, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

export class BohioCRMDashBoard extends Component {
    static template = "bohio_crm.BohioCRMDashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.mapRef = useRef("mapContainer");

        this.state = useState({
            mapLoaded: false,
        });

        onWillStart(async () => {
            this.crmData = await this.orm.call("crm.lead", "retrieve_dashboard", []);
        });

        onMounted(() => {
            this.initializeMap();
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

    async renderMap() {
        if (!this.mapRef.el || this.state.mapLoaded) return;

        // Obtener oportunidades con ubicación
        const opportunities = await this.orm.searchRead(
            "crm.lead",
            [
                ["type", "=", "opportunity"],
                ["stage_id.is_won", "=", false],
                ["active", "=", true]
            ],
            ["id", "name", "partner_id", "expected_revenue", "probability", "street", "city", "partner_latitude", "partner_longitude"]
        );

        console.log('Oportunidades para mapa:', opportunities.length);

        // Crear mapa centrado en Montería, Córdoba
        const map = L.map(this.mapRef.el).setView([8.7574, -75.8814], 13);

        // Agregar capa de mapa
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(map);

        // Agregar marcador de base
        L.marker([8.7574, -75.8814], {
            icon: L.divIcon({
                className: 'monteria-marker',
                html: '<div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);color:white;padding:8px 15px;border-radius:10px;font-weight:bold;box-shadow:0 2px 10px rgba(0,0,0,0.3);white-space:nowrap;">📍 Montería, Córdoba</div>',
                iconSize: [180, 40],
                iconAnchor: [90, 40]
            })
        }).addTo(map).bindPopup(`
            <div class="map-popup">
                <h6>Montería, Córdoba</h6>
                <p><strong>Ciudad base</strong></p>
                <p>Centro de operaciones CRM</p>
            </div>
        `);

        // Agregar marcadores de oportunidades
        let markersAdded = 0;
        opportunities.forEach(opp => {
            if (opp.partner_latitude && opp.partner_longitude) {
                markersAdded++;
                const marker = L.circleMarker([opp.partner_latitude, opp.partner_longitude], {
                    radius: 10,
                    fillColor: this.getOpportunityColor(opp.probability),
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                }).addTo(map);

                const popupContent = document.createElement('div');
                popupContent.className = 'map-popup';
                popupContent.innerHTML = `
                    <h6>${opp.name}</h6>
                    <p><strong>Cliente:</strong> ${opp.partner_id ? opp.partner_id[1] : 'Sin cliente'}</p>
                    <p><strong>Valor Esperado:</strong> ${this.formatCurrency(opp.expected_revenue || 0)}</p>
                    <p><strong>Probabilidad:</strong> <span class="badge bg-primary">${opp.probability || 0}%</span></p>
                    <p><strong>Ubicación:</strong> ${opp.city || 'Sin ciudad'}</p>
                    <button class="btn btn-sm btn-primary mt-2 view-opportunity-btn">Ver Detalles</button>
                `;

                const viewBtn = popupContent.querySelector('.view-opportunity-btn');
                viewBtn.addEventListener('click', () => {
                    this.onOpportunityClick(opp.id);
                });

                marker.bindPopup(popupContent);
            }
        });

        console.log('Marcadores de oportunidades agregados:', markersAdded);
        this.state.mapLoaded = true;
    }

    getOpportunityColor(probability) {
        if (probability >= 70) return '#28a745'; // Verde - Alta probabilidad
        if (probability >= 40) return '#ffc107'; // Amarillo - Media probabilidad
        return '#dc3545'; // Rojo - Baja probabilidad
    }

    formatCurrency(value) {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value || 0);
    }

    onOpportunityClick(opportunityId) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'crm.lead',
            res_id: opportunityId,
            views: [[false, 'form']],
            target: 'current',
        });
    }
}

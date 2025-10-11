/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJS, loadCSS } from "@web/core/assets";

/**
 * BOHIO CRM - WIDGET DE MAPA CON LEAFLET
 * Muestra propiedades en mapa interactivo con markers
 */

export class CrmMapWidget extends Component {
    setup() {
        this.orm = useService("orm");
        this.mapContainer = useRef("mapContainer");

        this.state = useState({
            map: null,
            markers: [],
            showLocation: true,
            properties: [],
            center: [8.7479, -75.8814], // Montería, Córdoba (centro por defecto)
            zoom: 13,
        });

        onMounted(async () => {
            await this.loadLeaflet();
            await this.initializeMap();
            await this.loadProperties();
        });

        onWillUnmount(() => {
            this.destroyMap();
        });
    }

    /**
     * Carga la librería Leaflet.js dinámicamente
     */
    async loadLeaflet() {
        try {
            // Cargar CSS de Leaflet
            await loadCSS("https://unpkg.com/leaflet@1.9.4/dist/leaflet.css");

            // Cargar JS de Leaflet
            await loadJS("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js");

            console.log("Leaflet loaded successfully");
        } catch (error) {
            console.error("Error loading Leaflet:", error);
        }
    }

    /**
     * Inicializa el mapa de Leaflet
     */
    async initializeMap() {
        if (!window.L || !this.mapContainer.el) {
            console.error("Leaflet or map container not available");
            return;
        }

        try {
            // Crear mapa
            this.state.map = window.L.map(this.mapContainer.el, {
                center: this.state.center,
                zoom: this.state.zoom,
                zoomControl: true,
                attributionControl: true,
            });

            // Agregar capa de tiles (OpenStreetMap)
            window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                maxZoom: 19,
            }).addTo(this.state.map);

            // Agregar controles personalizados
            this.addCustomControls();

            console.log("Map initialized successfully");
        } catch (error) {
            console.error("Error initializing map:", error);
        }
    }

    /**
     * Agrega controles personalizados al mapa
     */
    addCustomControls() {
        // Control para centrar en oficina de BOHIO
        const centerControl = window.L.control({ position: 'topright' });

        centerControl.onAdd = () => {
            const div = window.L.DomUtil.create('div', 'leaflet-bar leaflet-control');
            div.innerHTML = `
                <a href="#" class="leaflet-control-center" title="Centrar en oficina BOHIO">
                    <i class="fa fa-home"></i>
                </a>
            `;

            div.onclick = (e) => {
                e.preventDefault();
                this.centerOnOffice();
            };

            return div;
        };

        centerControl.addTo(this.state.map);
    }

    /**
     * Centra el mapa en la oficina de BOHIO
     */
    centerOnOffice() {
        const officeLocation = [8.7479, -75.8814]; // Montería (ajustar coordenadas reales)
        this.state.map.setView(officeLocation, 15);

        // Agregar marker temporal de oficina
        const officeMarker = window.L.marker(officeLocation, {
            icon: this.createCustomIcon('office')
        }).addTo(this.state.map);

        officeMarker.bindPopup(`
            <div class="map-popup-office">
                <strong>BOHIO Inmobiliaria</strong><br/>
                <small>Oficina Principal</small>
            </div>
        `);
    }

    /**
     * Carga propiedades asociadas a la oportunidad
     */
    async loadProperties() {
        if (!this.props.record || !this.props.record.data) {
            return;
        }

        const propertyIds = this.props.record.data.property_ids?.records?.map(r => r.resId) || [];

        if (propertyIds.length === 0) {
            console.log("No properties to display");
            return;
        }

        try {
            // Buscar propiedades con sus coordenadas
            const properties = await this.orm.searchRead(
                'product.template',
                [['id', 'in', propertyIds]],
                [
                    'id',
                    'name',
                    'type_service',
                    'price',
                    'street',
                    'city_id',
                    'region_id',
                    'latitude',
                    'longitude',
                    'property_type_id',
                    'state',
                ]
            );

            this.state.properties = properties;

            // Agregar markers al mapa
            this.addPropertyMarkers(properties);

            // Ajustar vista para mostrar todas las propiedades
            this.fitBoundsToProperties(properties);

        } catch (error) {
            console.error("Error loading properties:", error);
        }
    }

    /**
     * Agrega markers de propiedades al mapa
     */
    addPropertyMarkers(properties) {
        // Limpiar markers existentes
        this.clearMarkers();

        properties.forEach(property => {
            // Solo agregar si tiene coordenadas
            if (!property.latitude || !property.longitude) {
                console.log(`Property ${property.name} has no coordinates`);
                return;
            }

            const marker = window.L.marker(
                [property.latitude, property.longitude],
                {
                    icon: this.createCustomIcon(property.type_service),
                    title: property.name
                }
            ).addTo(this.state.map);

            // Popup con información de la propiedad
            marker.bindPopup(this.createPropertyPopup(property));

            // Guardar referencia del marker
            this.state.markers.push(marker);

            // Click event para abrir propiedad
            marker.on('click', () => {
                this.openProperty(property.id);
            });
        });
    }

    /**
     * Crea un icono personalizado según el tipo de servicio
     */
    createCustomIcon(typeService) {
        const iconColors = {
            'sale': '#0d6efd',      // Azul
            'rent': '#0dcaf0',      // Cyan
            'projects': '#198754',  // Verde
            'office': '#dc3545',    // Rojo (oficina)
        };

        const color = iconColors[typeService] || '#6c757d';

        return window.L.divIcon({
            className: 'custom-marker-icon',
            html: `
                <div style="
                    background: ${color};
                    width: 30px;
                    height: 30px;
                    border-radius: 50% 50% 50% 0;
                    border: 3px solid white;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                    transform: rotate(-45deg);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">
                    <i class="fa fa-home" style="
                        color: white;
                        font-size: 14px;
                        transform: rotate(45deg);
                    "></i>
                </div>
            `,
            iconSize: [30, 30],
            iconAnchor: [15, 30],
            popupAnchor: [0, -30],
        });
    }

    /**
     * Crea el HTML del popup de una propiedad
     */
    createPropertyPopup(property) {
        const priceFormatted = new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0
        }).format(property.price);

        return `
            <div class="map-popup-property" style="min-width: 200px;">
                <div class="popup-header" style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 8px;
                    margin: -10px -10px 8px -10px;
                    border-radius: 4px 4px 0 0;
                ">
                    <strong>${property.name}</strong>
                </div>

                <div class="popup-body">
                    <div style="margin-bottom: 4px;">
                        <i class="fa fa-tag" style="color: #6c757d; margin-right: 6px;"></i>
                        <strong>${priceFormatted}</strong>
                    </div>

                    ${property.city_id ? `
                        <div style="margin-bottom: 4px;">
                            <i class="fa fa-map-marker-alt" style="color: #6c757d; margin-right: 6px;"></i>
                            ${property.city_id[1]}
                        </div>
                    ` : ''}

                    ${property.region_id ? `
                        <div style="margin-bottom: 4px;">
                            <i class="fa fa-building" style="color: #6c757d; margin-right: 6px;"></i>
                            ${property.region_id[1]}
                        </div>
                    ` : ''}

                    ${property.property_type_id ? `
                        <div style="margin-bottom: 4px;">
                            <i class="fa fa-home" style="color: #6c757d; margin-right: 6px;"></i>
                            ${property.property_type_id[1]}
                        </div>
                    ` : ''}
                </div>

                <div class="popup-footer" style="
                    margin-top: 8px;
                    padding-top: 8px;
                    border-top: 1px solid #dee2e6;
                ">
                    <span class="badge text-bg-${this.getStateBadgeClass(property.state)}">
                        ${property.state}
                    </span>
                    <span class="badge text-bg-${this.getServiceBadgeClass(property.type_service)} ms-2">
                        ${property.type_service}
                    </span>
                </div>
            </div>
        `;
    }

    /**
     * Obtiene clase de badge según estado
     */
    getStateBadgeClass(state) {
        const classes = {
            'free': 'success',
            'reserved': 'warning',
            'sold': 'danger',
            'rented': 'info',
        };
        return classes[state] || 'secondary';
    }

    /**
     * Obtiene clase de badge según tipo de servicio
     */
    getServiceBadgeClass(typeService) {
        const classes = {
            'sale': 'primary',
            'rent': 'info',
            'projects': 'success',
        };
        return classes[typeService] || 'secondary';
    }

    /**
     * Ajusta el mapa para mostrar todas las propiedades
     */
    fitBoundsToProperties(properties) {
        const validCoords = properties.filter(p => p.latitude && p.longitude);

        if (validCoords.length === 0) {
            return;
        }

        if (validCoords.length === 1) {
            // Solo una propiedad, centrar en ella
            this.state.map.setView([validCoords[0].latitude, validCoords[0].longitude], 15);
        } else {
            // Múltiples propiedades, ajustar bounds
            const bounds = validCoords.map(p => [p.latitude, p.longitude]);
            this.state.map.fitBounds(bounds, { padding: [50, 50] });
        }
    }

    /**
     * Limpia todos los markers del mapa
     */
    clearMarkers() {
        this.state.markers.forEach(marker => {
            this.state.map.removeLayer(marker);
        });
        this.state.markers = [];
    }

    /**
     * Abre una propiedad en vista form
     */
    async openProperty(propertyId) {
        const actionService = this.env.services.action;
        await actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'product.template',
            res_id: propertyId,
            views: [[false, 'form']],
            target: 'current',
        });
    }

    /**
     * Destruye el mapa al desmontar
     */
    destroyMap() {
        if (this.state.map) {
            this.state.map.remove();
            this.state.map = null;
        }
    }

    /**
     * Actualiza el mapa cuando cambia show_map_location
     */
    updateMapVisibility(visible) {
        this.state.showLocation = visible;

        if (this.state.map) {
            if (visible) {
                this.mapContainer.el.style.opacity = '1';
                this.mapContainer.el.style.pointerEvents = 'auto';
            } else {
                this.mapContainer.el.style.opacity = '0.5';
                this.mapContainer.el.style.pointerEvents = 'none';
            }
        }
    }
}

CrmMapWidget.template = "bohio_crm.MapWidgetTemplate";
CrmMapWidget.props = {
    record: Object,
};

// Registrar el widget
registry.category("fields").add("crm_map_widget", {
    component: CrmMapWidget,
});

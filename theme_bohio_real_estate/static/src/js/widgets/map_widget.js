/** @odoo-module **/

// =============================================================================
// BOHIO REAL ESTATE - MAP WIDGET
// =============================================================================
// PublicWidget para mapa de propiedades con Leaflet
// Basado en el patrón oficial de addons/web/static/src/legacy/js/public/public_widget.js

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

import {
    tryGeolocation,
    ZOOM_WITH_USER,
    DEFAULT_CENTER,
    DEFAULT_ZOOM
} from '../utils/geolocation';

import {
    createPropertyMarker,
    createUserMarker,
    updateMarkersDistance
} from '../dom/markers';

// =============================================================================
// MAP WIDGET
// =============================================================================

const BohioMapWidget = publicWidget.Widget.extend({
    selector: '.bohio-map-container',
    xmlDependencies: [],

    /**
     * Widget lifecycle: start
     */
    start: function () {
        this._super.apply(this, arguments);

        // Validación DOM: Verificar que Leaflet esté cargado
        if (typeof L === 'undefined') {
            console.error('[MapWidget] Leaflet not loaded');
            this._showError('Leaflet no está cargado');
            return Promise.resolve();
        }

        // Validación DOM: Verificar que el contenedor del mapa exista
        this.mapContainer = this.el.querySelector('#bohio-map');
        if (!this.mapContainer) {
            console.warn('[MapWidget] Map container #bohio-map not found');
            return Promise.resolve();
        }

        // Inicializar propiedades
        this.map = null;
        this.userLocation = null;
        this.allMarkers = [];
        this.userMarker = null;
        this.markersLayer = null;

        // Configurar Leaflet
        this._configureLeaflet();

        // Inicializar mapa
        return this._initMap();
    },

    /**
     * Widget lifecycle: destroy
     */
    destroy: function () {
        // Limpiar mapa si existe
        if (this.map) {
            this.map.remove();
            this.map = null;
        }

        // Limpiar referencias
        this.allMarkers = [];
        this.userMarker = null;
        this.markersLayer = null;

        this._super.apply(this, arguments);
    },

    // -------------------------------------------------------------------------
    // CONFIGURACIÓN
    // -------------------------------------------------------------------------

    /**
     * Configura los paths de iconos de Leaflet
     * @private
     */
    _configureLeaflet: function () {
        L.Icon.Default.mergeOptions({
            iconRetinaUrl: '/real_estate_bits/static/src/lib/leaflet/images/marker-icon-2x.png',
            iconUrl: '/real_estate_bits/static/src/lib/leaflet/images/marker-icon.png',
            shadowUrl: '/real_estate_bits/static/src/lib/leaflet/images/marker-shadow.png'
        });
    },

    // -------------------------------------------------------------------------
    // INICIALIZACIÓN DEL MAPA
    // -------------------------------------------------------------------------

    /**
     * Inicializa el mapa con propiedades
     * @private
     * @returns {Promise}
     */
    _initMap: async function () {
        console.log('[MapWidget] Initializing map...');

        // Intentar geolocalización
        this.userLocation = await tryGeolocation();

        // Cargar propiedades
        const data = await this._loadProperties();
        if (!data) {
            return;
        }

        // Crear mapa de Leaflet
        this._createMap(data);

        // Crear marcadores si hay propiedades
        if (data.properties && data.properties.length > 0) {
            this._createMarkers(data.properties);

            // Mostrar ubicación de usuario si existe
            if (this.userLocation) {
                this._showUserLocation();
            }

            // Actualizar marcadores según distancia
            this._updateMarkersDistance();

            // Event listeners
            this.map.on('zoomend', this._updateMarkersDistance.bind(this));
            this.map.on('moveend', this._updateMarkersDistance.bind(this));
        } else {
            this._showNoPropertiesMessage(data);
        }

        this._hideLoading();
    },

    /**
     * Carga las propiedades desde el servidor
     * @private
     * @returns {Promise<Object|null>}
     */
    _loadProperties: async function () {
        try {
            const data = await rpc('/api/properties/mapa', {
                user_lat: this.userLocation?.lat,
                user_lng: this.userLocation?.lng
            });

            console.log('[MapWidget] Properties loaded:', data.property_count);

            // Actualizar contador si existe
            this._updatePropertyCount(data.property_count);

            return data;
        } catch (error) {
            console.error('[MapWidget] Error loading properties:', error);
            this._hideLoading();
            this._showError('Error al cargar propiedades');
            return null;
        }
    },

    /**
     * Actualiza el contador de propiedades
     * @private
     * @param {number} count
     */
    _updatePropertyCount: function (count) {
        const countEl = document.getElementById('property-count');
        if (countEl) {
            countEl.textContent = count;
        }
    },

    // -------------------------------------------------------------------------
    // CREACIÓN DEL MAPA
    // -------------------------------------------------------------------------

    /**
     * Crea el mapa de Leaflet
     * @private
     * @param {Object} data - Datos del servidor
     */
    _createMap: function (data) {
        this.map = L.map(this.mapContainer, {
            center: [data.center.lat, data.center.lng],
            zoom: data.zoom,
            zoomControl: true,
            scrollWheelZoom: true
        });

        // Añadir capa de OpenStreetMap
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        }).addTo(this.map);

        console.log('[MapWidget] Map created');
    },

    // -------------------------------------------------------------------------
    // MARCADORES
    // -------------------------------------------------------------------------

    /**
     * Crea los marcadores de propiedades
     * @private
     * @param {Array} properties
     */
    _createMarkers: function (properties) {
        // Crear capa para los marcadores
        this.markersLayer = L.layerGroup().addTo(this.map);

        properties.forEach(property => {
            const marker = createPropertyMarker(property, L);
            marker.addTo(this.markersLayer);
            this.allMarkers.push(marker);
        });

        console.log('[MapWidget] Created', this.allMarkers.length, 'markers');
    },

    /**
     * Muestra la ubicación del usuario en el mapa
     * @private
     */
    _showUserLocation: function () {
        if (!this.userLocation || !this.map) return;

        // Remover marcador anterior si existe
        if (this.userMarker) {
            this.map.removeLayer(this.userMarker);
        }

        // Crear marcador de usuario
        this.userMarker = createUserMarker(this.userLocation, L);
        this.userMarker.addTo(this.map);
        this.userMarker.openPopup();

        // Centrar mapa en usuario
        this.map.setView([this.userLocation.lat, this.userLocation.lng], ZOOM_WITH_USER);

        console.log('[MapWidget] User location shown on map');
    },

    /**
     * Actualiza los marcadores según distancia del usuario
     * @private
     */
    _updateMarkersDistance: function () {
        updateMarkersDistance(this.allMarkers, this.userLocation);
    },

    // -------------------------------------------------------------------------
    // GEOLOCALIZACIÓN MANUAL
    // -------------------------------------------------------------------------

    /**
     * Reintenta la geolocalización (llamado desde el botón)
     */
    manualGeolocate: async function () {
        console.log('[MapWidget] Manual geolocation requested');

        // Remover mensaje de error si existe
        const overlay = this.el.querySelector('#no-data-overlay');
        if (overlay) {
            overlay.remove();
        }

        this._showLoading();

        // Intentar geolocalización
        this.userLocation = await tryGeolocation();

        if (this.userLocation) {
            // Mostrar ubicación en mapa
            this._showUserLocation();

            // Recargar propiedades con nueva ubicación
            const data = await this._loadProperties();
            if (!data) return;

            // Limpiar marcadores anteriores
            if (this.markersLayer) {
                this.markersLayer.clearLayers();
            }
            this.allMarkers = [];

            // Crear nuevos marcadores
            if (data.properties && data.properties.length > 0) {
                this._createMarkers(data.properties);
                this._updateMarkersDistance();
            } else {
                this._showNoPropertiesMessage(data);
            }
        } else {
            this._showNoLocationMessage();
        }

        this._hideLoading();
    },

    // -------------------------------------------------------------------------
    // MENSAJES Y OVERLAYS
    // -------------------------------------------------------------------------

    /**
     * Muestra overlay de loading
     * @private
     */
    _showLoading: function () {
        const loading = this.el.querySelector('#map-loading');
        if (loading) {
            loading.style.display = 'flex';
        }
    },

    /**
     * Oculta overlay de loading
     * @private
     */
    _hideLoading: function () {
        const loading = this.el.querySelector('#map-loading');
        if (loading) {
            loading.style.display = 'none';
        }
    },

    /**
     * Muestra mensaje de error
     * @private
     * @param {string} message
     */
    _showError: function (message) {
        this._showOverlay(message, 'error', [
            {
                text: 'Ver Todas las Propiedades',
                icon: 'bi-list-ul',
                href: '/shop',
                class: 'btn-danger'
            }
        ]);
    },

    /**
     * Muestra mensaje cuando no hay propiedades
     * @private
     * @param {Object} data
     */
    _showNoPropertiesMessage: function (data) {
        const message = data.has_user_location
            ? 'No se encontraron propiedades cerca de tu ubicación'
            : 'No se encontraron propiedades disponibles';

        this._showOverlay(message, 'no-properties', [
            {
                text: 'Ver Todas las Propiedades',
                icon: 'bi-list-ul',
                href: '/shop',
                class: 'btn-danger'
            }
        ]);
    },

    /**
     * Muestra mensaje cuando no se puede obtener ubicación
     * @private
     */
    _showNoLocationMessage: function () {
        this._showOverlay(
            'No se pudo obtener tu ubicación. Por favor, verifica los permisos del navegador.',
            'no-location',
            [
                {
                    text: 'Intentar de Nuevo',
                    icon: 'bi-geo-alt-fill',
                    onclick: 'manualGeolocate',
                    class: 'btn-danger'
                }
            ]
        );
    },

    /**
     * Muestra overlay con mensaje y acciones (usando createElement)
     * @private
     * @param {string} message
     * @param {string} type
     * @param {Array} actions
     */
    _showOverlay: function (message, type, actions) {
        // Remover overlay anterior si existe
        const existingOverlay = this.el.querySelector('#no-data-overlay');
        if (existingOverlay) {
            existingOverlay.remove();
        }

        // Crear overlay
        const overlay = document.createElement('div');
        overlay.id = 'no-data-overlay';
        overlay.className = 'map-overlay';

        // Card
        const card = document.createElement('div');
        card.className = 'no-data-card';

        // Icono
        const iconDiv = document.createElement('div');
        iconDiv.className = 'no-data-icon';
        iconDiv.textContent = type === 'no-properties' ? '🏠' : '📍';
        card.appendChild(iconDiv);

        // Mensaje
        const h3 = document.createElement('h3');
        h3.textContent = message;
        card.appendChild(h3);

        // Acciones
        if (actions && actions.length > 0) {
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'no-data-actions';

            actions.forEach(action => {
                if (action.href) {
                    // Link
                    const a = document.createElement('a');
                    a.href = action.href;
                    a.className = `btn ${action.class}`;

                    const icon = document.createElement('i');
                    icon.className = `bi ${action.icon} me-1`;

                    a.appendChild(icon);
                    a.appendChild(document.createTextNode(action.text));

                    actionsDiv.appendChild(a);
                } else if (action.onclick) {
                    // Button con evento
                    const button = document.createElement('button');
                    button.className = `btn ${action.class}`;
                    button.addEventListener('click', this[action.onclick].bind(this));

                    const icon = document.createElement('i');
                    icon.className = `bi ${action.icon} me-1`;

                    button.appendChild(icon);
                    button.appendChild(document.createTextNode(action.text));

                    actionsDiv.appendChild(button);
                }
            });

            card.appendChild(actionsDiv);
        }

        overlay.appendChild(card);

        // Agregar al contenedor
        const mapContainer = this.el.querySelector('.map-container');
        if (mapContainer) {
            mapContainer.appendChild(overlay);
        }
    },
});

// =============================================================================
// REGISTRO DEL WIDGET
// =============================================================================

publicWidget.registry.BohioMapWidget = BohioMapWidget;

export default BohioMapWidget;

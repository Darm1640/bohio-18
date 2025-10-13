/** @odoo-module **/

// =============================================================================
// BOHIO REAL ESTATE - UNIVERSAL MAP WIDGET
// =============================================================================
// PublicWidget versátil para mapas de propiedades/proyectos con Leaflet
// Soporta múltiples modos: homepage, detalle, proyecto, búsqueda

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

import {
    tryGeolocation,
    ZOOM_WITH_USER,
    DEFAULT_CENTER,
    DEFAULT_ZOOM
} from '../utils/geolocation';

import {
    OSM_TILE_URL,
    OSM_ATTRIBUTION,
    MAX_ZOOM
} from '../utils/constants';

import {
    createPropertyMarker,
    createUserMarker,
    updateMarkersDistance
} from '../dom/markers';

// =============================================================================
// MAP WIDGET - Configuración por Modo
// =============================================================================

/**
 * Configuración del widget según el modo de uso
 *
 * Modos disponibles:
 * - 'search': Mapa de búsqueda con múltiples propiedades y filtros
 * - 'detail': Mapa de detalle de una propiedad específica
 * - 'project': Mapa de proyecto con múltiples propiedades del proyecto
 * - 'homepage': Mapa del homepage con propiedades destacadas
 */
const MAP_MODES = {
    search: {
        endpoint: '/api/properties/mapa',
        useFilters: true,
        useGeolocation: true,
        allowZoom: true,
        allowScroll: true,
        clusterMarkers: true
    },
    detail: {
        endpoint: null, // No necesita endpoint, recibe datos directamente
        useFilters: false,
        useGeolocation: false,
        allowZoom: true,
        allowScroll: true,
        clusterMarkers: false,
        defaultZoom: 16
    },
    project: {
        endpoint: '/api/project/properties',
        useFilters: false,
        useGeolocation: false,
        allowZoom: true,
        allowScroll: true,
        clusterMarkers: false,
        defaultZoom: 15
    },
    homepage: {
        endpoint: '/api/properties/homepage',
        useFilters: false,
        useGeolocation: false,
        allowZoom: true,
        allowScroll: false,
        clusterMarkers: false
    }
};

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

        // Validar que Leaflet esté cargado
        if (typeof L === 'undefined') {
            console.error('[MapWidget] Leaflet not loaded');
            this._showError('Leaflet no está cargado');
            return Promise.resolve();
        }

        // Obtener configuración desde data attributes
        this._parseConfiguration();

        // Validar contenedor del mapa
        this.mapContainer = this.el.querySelector(this.config.mapSelector || '#bohio-map');
        if (!this.mapContainer) {
            console.warn('[MapWidget] Map container not found:', this.config.mapSelector);
            return Promise.resolve();
        }

        // Inicializar propiedades
        this._initProperties();

        // Configurar Leaflet
        this._configureLeaflet();

        // Inicializar mapa
        return this._initMap();
    },

    /**
     * Widget lifecycle: destroy
     */
    destroy: function () {
        // Limpiar mapa
        if (this.map) {
            this.map.remove();
            this.map = null;
        }

        // Limpiar referencias
        this.allMarkers = [];
        this.userMarker = null;
        this.markersLayer = null;
        this.clusterGroup = null;

        this._super.apply(this, arguments);
    },

    // -------------------------------------------------------------------------
    // CONFIGURACIÓN
    // -------------------------------------------------------------------------

    /**
     * Lee configuración desde data attributes del HTML
     * @private
     */
    _parseConfiguration: function () {
        const el = this.el;

        // Modo del mapa (default: search)
        const mode = el.dataset.mapMode || 'search';
        const modeConfig = MAP_MODES[mode] || MAP_MODES.search;

        this.config = {
            // Modo
            mode: mode,
            ...modeConfig,

            // Selector del contenedor
            mapSelector: el.dataset.mapSelector || '#bohio-map',

            // Datos inline (para modo detail)
            lat: parseFloat(el.dataset.lat),
            lng: parseFloat(el.dataset.lng),
            propertyId: parseInt(el.dataset.propertyId),
            projectId: parseInt(el.dataset.projectId),
            propertyName: el.dataset.propertyName || '',

            // Endpoint personalizado (sobrescribe el del modo)
            endpoint: el.dataset.endpoint || modeConfig.endpoint,

            // Parámetros adicionales
            filters: el.dataset.filters ? JSON.parse(el.dataset.filters) : {},

            // Centro y zoom personalizados
            centerLat: parseFloat(el.dataset.centerLat),
            centerLng: parseFloat(el.dataset.centerLng),
            zoom: parseInt(el.dataset.zoom) || modeConfig.defaultZoom || DEFAULT_ZOOM,

            // Comportamiento
            showUserLocation: el.dataset.showUserLocation !== 'false',
            autoFit: el.dataset.autoFit !== 'false',
        };

        console.log('[MapWidget] Configuration:', this.config);
    },

    /**
     * Inicializa propiedades del widget
     * @private
     */
    _initProperties: function () {
        this.map = null;
        this.userLocation = null;
        this.allMarkers = [];
        this.userMarker = null;
        this.markersLayer = null;
        this.clusterGroup = null;
    },

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
     * Inicializa el mapa según el modo
     * @private
     * @returns {Promise}
     */
    _initMap: async function () {
        console.log('[MapWidget] Initializing map in mode:', this.config.mode);

        // Geolocalización solo si está habilitada
        if (this.config.useGeolocation && this.config.showUserLocation) {
            this.userLocation = await tryGeolocation();
        }

        // Cargar datos según el modo
        let data;
        if (this.config.mode === 'detail') {
            // Modo detalle: usar datos inline
            data = this._getDetailData();
        } else {
            // Otros modos: cargar desde endpoint
            data = await this._loadProperties();
        }

        if (!data) {
            return;
        }

        // Crear mapa de Leaflet
        this._createMap(data);

        // Crear marcadores
        if (data.properties && data.properties.length > 0) {
            this._createMarkers(data.properties);

            // Ajustar vista según configuración
            if (this.config.autoFit && this.allMarkers.length > 1) {
                this._fitBounds();
            }

            // Mostrar ubicación de usuario
            if (this.userLocation && this.config.showUserLocation) {
                this._showUserLocation();
            }

            // Actualizar distancias
            if (this.config.useGeolocation) {
                this._updateMarkersDistance();
            }

            // Event listeners
            if (this.config.useGeolocation) {
                this.map.on('zoomend', this._updateMarkersDistance.bind(this));
                this.map.on('moveend', this._updateMarkersDistance.bind(this));
            }
        } else if (this.config.mode !== 'detail') {
            this._showNoPropertiesMessage(data);
        }

        this._hideLoading();
    },

    /**
     * Obtiene datos inline para modo detalle
     * @private
     * @returns {Object}
     */
    _getDetailData: function () {
        if (!this.config.lat || !this.config.lng) {
            console.error('[MapWidget] Missing lat/lng for detail mode');
            return null;
        }

        return {
            center: {
                lat: this.config.lat,
                lng: this.config.lng
            },
            zoom: this.config.zoom,
            properties: [{
                id: this.config.propertyId,
                name: this.config.propertyName,
                lat: this.config.lat,
                lng: this.config.lng,
                // Más datos pueden venir del dataset
                type_service: this.el.dataset.typeService,
                price: parseFloat(this.el.dataset.price),
                city: this.el.dataset.city,
                neighborhood: this.el.dataset.neighborhood
            }]
        };
    },

    /**
     * Carga propiedades desde el servidor
     * @private
     * @returns {Promise<Object|null>}
     */
    _loadProperties: async function () {
        if (!this.config.endpoint) {
            console.error('[MapWidget] No endpoint configured');
            return null;
        }

        try {
            // Construir parámetros
            const params = {
                ...this.config.filters
            };

            // Agregar ubicación de usuario si está disponible
            if (this.userLocation && this.config.useGeolocation) {
                params.user_lat = this.userLocation.lat;
                params.user_lng = this.userLocation.lng;
            }

            // Agregar project_id si es modo proyecto
            if (this.config.mode === 'project' && this.config.projectId) {
                params.project_id = this.config.projectId;
            }

            const data = await rpc(this.config.endpoint, params);

            console.log('[MapWidget] Properties loaded:', data.property_count || data.properties?.length);

            // Actualizar contador si existe
            if (data.property_count !== undefined) {
                this._updatePropertyCount(data.property_count);
            }

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
        // Determinar centro
        let center;
        if (this.config.centerLat && this.config.centerLng) {
            center = [this.config.centerLat, this.config.centerLng];
        } else if (data.center) {
            center = [data.center.lat, data.center.lng];
        } else {
            center = DEFAULT_CENTER;
        }

        // Crear mapa
        this.map = L.map(this.mapContainer, {
            center: center,
            zoom: data.zoom || this.config.zoom,
            zoomControl: true,
            scrollWheelZoom: this.config.allowScroll,
            dragging: true,
            doubleClickZoom: this.config.allowZoom,
            touchZoom: this.config.allowZoom
        });

        // Añadir capa de OpenStreetMap
        L.tileLayer(OSM_TILE_URL, {
            attribution: OSM_ATTRIBUTION,
            maxZoom: MAX_ZOOM
        }).addTo(this.map);

        console.log('[MapWidget] Map created at', center, 'zoom', data.zoom || this.config.zoom);
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
        if (this.config.clusterMarkers && typeof L.markerClusterGroup === 'function') {
            // Usar clustering si está disponible
            this.clusterGroup = L.markerClusterGroup();
            this.markersLayer = this.clusterGroup;
        } else {
            // Capa simple
            this.markersLayer = L.layerGroup();
        }

        this.markersLayer.addTo(this.map);

        // Crear marcadores
        properties.forEach(property => {
            const marker = createPropertyMarker(property, L);
            marker.addTo(this.markersLayer);
            this.allMarkers.push(marker);
        });

        console.log('[MapWidget] Created', this.allMarkers.length, 'markers');
    },

    /**
     * Ajusta el mapa para mostrar todos los marcadores
     * @private
     */
    _fitBounds: function () {
        if (this.allMarkers.length === 0) return;

        const bounds = L.latLngBounds(
            this.allMarkers.map(m => m.getLatLng())
        );

        this.map.fitBounds(bounds, {
            padding: [50, 50],
            maxZoom: 15
        });

        console.log('[MapWidget] Bounds fitted to markers');
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

        // Centrar solo si no hay propiedades o es modo search
        if (this.allMarkers.length === 0 || this.config.mode === 'search') {
            this.map.setView([this.userLocation.lat, this.userLocation.lng], ZOOM_WITH_USER);
        }

        console.log('[MapWidget] User location shown on map');
    },

    /**
     * Actualiza los marcadores según distancia del usuario
     * @private
     */
    _updateMarkersDistance: function () {
        if (this.config.useGeolocation) {
            updateMarkersDistance(this.allMarkers, this.userLocation);
        }
    },

    // -------------------------------------------------------------------------
    // MÉTODOS PÚBLICOS
    // -------------------------------------------------------------------------

    /**
     * Actualiza los marcadores con nuevas propiedades
     * @public
     * @param {Array} properties - Nuevas propiedades
     */
    updateProperties: function (properties) {
        console.log('[MapWidget] Updating properties:', properties.length);

        // Limpiar marcadores anteriores
        if (this.markersLayer) {
            this.markersLayer.clearLayers();
        }
        this.allMarkers = [];

        // Crear nuevos marcadores
        if (properties && properties.length > 0) {
            this._createMarkers(properties);

            // Ajustar vista
            if (this.config.autoFit) {
                this._fitBounds();
            }

            // Actualizar distancias
            if (this.config.useGeolocation) {
                this._updateMarkersDistance();
            }
        }
    },

    /**
     * Centra el mapa en una ubicación específica
     * @public
     * @param {number} lat - Latitud
     * @param {number} lng - Longitud
     * @param {number} zoom - Nivel de zoom (opcional)
     */
    centerMap: function (lat, lng, zoom) {
        if (!this.map) return;

        this.map.setView([lat, lng], zoom || this.config.zoom);
        console.log('[MapWidget] Map centered at', lat, lng);
    },

    /**
     * Aplica filtros y recarga propiedades
     * @public
     * @param {Object} filters - Filtros a aplicar
     */
    applyFilters: async function (filters) {
        if (!this.config.useFilters) {
            console.warn('[MapWidget] Filters not enabled in this mode');
            return;
        }

        console.log('[MapWidget] Applying filters:', filters);

        this.config.filters = filters;
        this._showLoading();

        const data = await this._loadProperties();
        if (!data) return;

        // Actualizar propiedades
        if (data.properties && data.properties.length > 0) {
            this.updateProperties(data.properties);
        } else {
            this._showNoPropertiesMessage(data);
        }

        this._hideLoading();
    },

    // -------------------------------------------------------------------------
    // GEOLOCALIZACIÓN MANUAL
    // -------------------------------------------------------------------------

    /**
     * Reintenta la geolocalización (llamado desde el botón)
     * @public
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

            // Actualizar propiedades
            if (data.properties && data.properties.length > 0) {
                this.updateProperties(data.properties);
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
                href: '/properties',
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
                href: '/properties',
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

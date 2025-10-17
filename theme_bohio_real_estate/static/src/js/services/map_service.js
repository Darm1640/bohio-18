/** @odoo-module **/

/**
 * ============================================================================
 * BOHIO Map Service - Servicio Centralizado de Mapas Leaflet
 * ============================================================================
 * Unifica TODAS las implementaciones de mapas (5 archivos diferentes)
 * Proporciona API consistente para crear y gestionar mapas
 */

export class MapService {
    /**
     * Configuración por defecto
     */
    static DEFAULT_CENTER = [4.7110, -74.0721]; // Bogotá, Colombia
    static DEFAULT_ZOOM = 11;
    static TILE_LAYER = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
    static TILE_ATTRIBUTION = '© OpenStreetMap contributors';

    /**
     * Crear una instancia de mapa
     * @param {Object} config - Configuración del mapa
     * @returns {Promise<Object>} - Objeto con mapa y métodos
     */
    static async create(config) {
        const {
            container,
            properties = [],
            center = this.DEFAULT_CENTER,
            zoom = this.DEFAULT_ZOOM,
            mode = 'search', // 'search', 'detail', 'homepage'
            onMarkerClick,
            enableClustering = false,
            markerTemplate
        } = config;

        // Validaciones
        if (!container) {
            throw new Error('[MapService] Container element is required');
        }

        if (typeof L === 'undefined') {
            throw new Error('[MapService] Leaflet library is not loaded');
        }

        // Obtener elemento del contenedor
        const mapElement = typeof container === 'string' ?
            document.getElementById(container) || document.querySelector(container) :
            container;

        if (!mapElement) {
            throw new Error('[MapService] Container element not found');
        }

        // Crear mapa
        const map = L.map(mapElement, {
            center,
            zoom,
            zoomControl: true,
            scrollWheelZoom: mode !== 'detail', // Solo scroll zoom en search/homepage
            dragging: true,
            touchZoom: true,
            doubleClickZoom: true
        });

        // Añadir capa de tiles
        L.tileLayer(this.TILE_LAYER, {
            attribution: this.TILE_ATTRIBUTION,
            maxZoom: 19,
            minZoom: 3
        }).addTo(map);

        // Capa de marcadores (o cluster)
        let markersLayer;
        if (enableClustering && typeof L.markerClusterGroup === 'function') {
            markersLayer = L.markerClusterGroup({
                maxClusterRadius: 50,
                spiderfyOnMaxZoom: true,
                showCoverageOnHover: false,
                zoomToBoundsOnClick: true
            });
        } else {
            markersLayer = L.layerGroup();
        }
        markersLayer.addTo(map);

        console.log(`[MapService] Map created in ${mode} mode with ${properties.length} properties`);

        // Agregar marcadores iniciales
        if (properties.length > 0) {
            this._addMarkers(map, markersLayer, properties, onMarkerClick, markerTemplate);
            this._fitBounds(map, properties);
        }

        // Retornar objeto con mapa y métodos útiles
        return {
            map,
            markersLayer,

            /**
             * Invalidar tamaño del mapa (útil cuando se muestra en tabs)
             */
            invalidateSize: () => {
                setTimeout(() => map.invalidateSize(), 100);
            },

            /**
             * Actualizar propiedades en el mapa
             */
            updateProperties: (newProperties, clearFirst = true) => {
                if (clearFirst) {
                    markersLayer.clearLayers();
                }

                if (newProperties.length > 0) {
                    this._addMarkers(map, markersLayer, newProperties, onMarkerClick, markerTemplate);
                    this._fitBounds(map, newProperties);
                }
            },

            /**
             * Agregar una sola propiedad
             */
            addProperty: (property) => {
                if (property.latitude && property.longitude) {
                    const marker = this._createMarker(property, onMarkerClick, markerTemplate);
                    marker.addTo(markersLayer);
                }
            },

            /**
             * Centrar en una propiedad específica
             */
            centerOnProperty: (property, zoomLevel = 15) => {
                if (property.latitude && property.longitude) {
                    map.setView([property.latitude, property.longitude], zoomLevel);
                }
            },

            /**
             * Limpiar todos los marcadores
             */
            clearMarkers: () => {
                markersLayer.clearLayers();
            },

            /**
             * Destruir mapa
             */
            destroy: () => {
                map.remove();
            }
        };
    }

    /**
     * Agregar marcadores al mapa
     * @private
     */
    static _addMarkers(map, markersLayer, properties, onMarkerClick, markerTemplate) {
        properties.forEach(property => {
            if (property.latitude && property.longitude) {
                const marker = this._createMarker(property, onMarkerClick, markerTemplate);
                marker.addTo(markersLayer);
            }
        });
    }

    /**
     * Crear marcador de propiedad
     * @private
     */
    static _createMarker(property, onMarkerClick, markerTemplate) {
        const marker = L.marker([property.latitude, property.longitude]);

        // Crear popup
        const popupContent = markerTemplate ?
            markerTemplate(property) :
            this._createDefaultPopup(property);

        marker.bindPopup(popupContent, {
            maxWidth: 300,
            className: 'bohio-map-popup',
            closeButton: true,
            autoPan: true
        });

        // Event listener para click
        if (onMarkerClick) {
            marker.on('click', () => onMarkerClick(property));
        }

        return marker;
    }

    /**
     * Crear popup por defecto
     * @private
     */
    static _createDefaultPopup(property) {
        const imageUrl = property.image_url || '/theme_bohio_real_estate/static/src/img/placeholder.jpg';

        // Formatear precio
        const price = property.price ?
            new Intl.NumberFormat('es-CO', {
                style: 'currency',
                currency: 'COP',
                minimumFractionDigits: 0
            }).format(property.price) : 'Consultar';

        const priceLabel = property.type_service === 'rent' || property.type_service === 'Arriendo' ?
            'Arriendo/mes' : 'Venta';

        // Ubicación
        const neighborhood = property.neighborhood ? `${property.neighborhood}, ` : '';
        const location = `${neighborhood}${property.city || property.state || ''}`;

        // Características
        const area = property.area || property.total_area || property.built_area || 0;
        const bedrooms = property.bedrooms || 0;
        const bathrooms = property.bathrooms || 0;

        const features = [];
        if (area > 0) features.push(`<span><i class="bi bi-rulers me-1"></i>${Math.round(area)} m²</span>`);
        if (bedrooms > 0) features.push(`<span><i class="bi bi-bed me-1"></i>${bedrooms}</span>`);
        if (bathrooms > 0) features.push(`<span><i class="bi bi-droplet me-1"></i>${bathrooms}</span>`);

        // Construir HTML
        return `
            <div style="min-width: 280px; max-width: 300px;">
                <img src="${imageUrl}"
                     alt="${property.name}"
                     style="width: 100%; height: 160px; object-fit: cover; border-radius: 8px; margin-bottom: 12px;"
                     onerror="this.src='/theme_bohio_real_estate/static/src/img/placeholder.jpg'"/>

                <h6 class="fw-bold mb-2" style="font-size: 14px;">${property.name}</h6>

                <p class="small mb-2 text-muted">
                    <i class="bi bi-geo-alt-fill text-danger me-1"></i>${location}
                </p>

                <div class="mb-2">
                    <small class="text-muted d-block">${priceLabel}</small>
                    <p class="mb-2 text-danger fw-bold" style="font-size: 16px;">${price}</p>
                </div>

                ${features.length > 0 ? `
                    <div class="d-flex gap-3 mb-3" style="font-size: 13px; color: #666;">
                        ${features.join('')}
                    </div>
                ` : ''}

                <a href="/property/${property.id}"
                   class="btn btn-sm btn-danger w-100"
                   style="background: #FF1D25; border: none;">
                   <i class="bi bi-eye me-1"></i>Ver detalles
                </a>
            </div>
        `;
    }

    /**
     * Ajustar vista del mapa a las propiedades
     * @private
     */
    static _fitBounds(map, properties) {
        const bounds = properties
            .filter(p => p.latitude && p.longitude)
            .map(p => [p.latitude, p.longitude]);

        if (bounds.length === 0) return;

        if (bounds.length === 1) {
            // Una sola propiedad, centrar con zoom específico
            map.setView(bounds[0], 15);
        } else {
            // Múltiples propiedades, ajustar bounds
            map.fitBounds(bounds, {
                padding: [50, 50],
                maxZoom: 15
            });
        }
    }

    /**
     * Crear mapa simple para detalle de propiedad
     * @param {Object} config - { container, property }
     * @returns {Promise<Object>}
     */
    static async createDetailMap(config) {
        const { container, property } = config;

        if (!property.latitude || !property.longitude) {
            throw new Error('[MapService] Property must have coordinates');
        }

        return this.create({
            container,
            properties: [property],
            center: [property.latitude, property.longitude],
            zoom: 15,
            mode: 'detail'
        });
    }

    /**
     * Crear mapa para búsqueda/shop
     * @param {Object} config - { container, properties, onMarkerClick }
     * @returns {Promise<Object>}
     */
    static async createSearchMap(config) {
        return this.create({
            ...config,
            mode: 'search',
            enableClustering: true // Habilitar clustering para búsqueda
        });
    }

    /**
     * Crear mapa para homepage
     * @param {Object} config - { container, properties }
     * @returns {Promise<Object>}
     */
    static async createHomepageMap(config) {
        return this.create({
            ...config,
            mode: 'homepage',
            enableClustering: false
        });
    }

    /**
     * Verificar si Leaflet está cargado
     * @returns {boolean}
     */
    static isLeafletLoaded() {
        return typeof L !== 'undefined';
    }

    /**
     * Obtener distancia entre dos puntos (en km)
     * @param {Array} point1 - [lat, lng]
     * @param {Array} point2 - [lat, lng]
     * @returns {number}
     */
    static getDistance(point1, point2) {
        if (!this.isLeafletLoaded()) {
            throw new Error('[MapService] Leaflet is not loaded');
        }

        const latlng1 = L.latLng(point1[0], point1[1]);
        const latlng2 = L.latLng(point2[0], point2[1]);

        return latlng1.distanceTo(latlng2) / 1000; // Convertir a km
    }

    /**
     * Obtener propiedades cercanas
     * @param {Object} property - Propiedad base
     * @param {Array} properties - Lista de propiedades
     * @param {number} maxDistance - Distancia máxima en km
     * @returns {Array}
     */
    static getNearbyProperties(property, properties, maxDistance = 5) {
        if (!property.latitude || !property.longitude) return [];

        const point1 = [property.latitude, property.longitude];

        return properties
            .filter(p => p.id !== property.id && p.latitude && p.longitude)
            .map(p => ({
                ...p,
                distance: this.getDistance(point1, [p.latitude, p.longitude])
            }))
            .filter(p => p.distance <= maxDistance)
            .sort((a, b) => a.distance - b.distance);
    }
}

// Exportar por defecto
export default MapService;

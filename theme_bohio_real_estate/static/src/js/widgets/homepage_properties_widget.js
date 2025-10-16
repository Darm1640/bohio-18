/** @odoo-module **/

// =============================================================================
// BOHIO REAL ESTATE - HOMEPAGE PROPERTIES WIDGET
// =============================================================================
// PublicWidget para carga de propiedades en homepage con mapas
// Basado en el patrón oficial de Odoo 18

import publicWidget from "@web/legacy/js/public/public_widget";

import { getElement, clearElement } from '../utils/dom_helpers';
import { createPropertyCard, createEmptyState, createMapPopup } from '../components/property_card';
import PropertyService from '../services/property_service';
import MapService from '../services/map_service';

// =============================================================================
// HOMEPAGE PROPERTIES WIDGET
// =============================================================================

const HomepagePropertiesWidget = publicWidget.Widget.extend({
    selector: '.bohio-homepage-properties',
    xmlDependencies: [],

    events: {
        'click .service-type-btn': '_onServiceTypeClick',
        'keypress #quickCodeSearch': '_onQuickCodeKeypress',
        'keypress #modalPropertyCode': '_onModalCodeKeypress',
    },

    /**
     * Widget lifecycle: start
     */
    start: function () {
        this._super.apply(this, arguments);

        // Inicializar estado
        this.maps = {
            arriendo: null,
            usedSale: null,
            projects: null
        };

        this.propertiesData = {
            arriendo: [],
            usedSale: [],
            projects: []
        };

        // Cargar propiedades
        this._loadAllProperties();

        // Configurar tabs de mapas
        this._setupMapTabs();

        return Promise.resolve();
    },

    /**
     * Widget lifecycle: destroy
     */
    destroy: function () {
        // Limpiar mapas
        Object.keys(this.maps).forEach(key => {
            if (this.maps[key]) {
                this.maps[key].remove();
                this.maps[key] = null;
            }
        });

        this._super.apply(this, arguments);
    },

    // -------------------------------------------------------------------------
    // CARGA DE PROPIEDADES
    // -------------------------------------------------------------------------

    /**
     * Carga todas las propiedades del homepage
     * @private
     */
    _loadAllProperties: async function () {
        console.log('[Homepage] Cargando propiedades...');

        // Cargar en paralelo
        await Promise.all([
            this._loadArriendoProperties(),
            this._loadUsedSaleProperties(),
            this._loadProjectsProperties()
        ]);

        console.log('[Homepage] Todas las propiedades cargadas');
    },

    /**
     * Carga propiedades de arriendo
     * @private
     */
    _loadArriendoProperties: async function () {
        try {
            const container = getElement('#arriendo-properties-grid', this.el);
            if (!container) {
                console.warn('[Homepage] Contenedor arriendo-properties-grid no encontrado');
                return;
            }

            const data = await PropertyService.loadByType('rent', { limit: 4 });

            if (data.success && data.properties && data.properties.length > 0) {
                this._renderProperties(container, data.properties);
                this.propertiesData.arriendo = data.properties.filter(p => p.latitude && p.longitude);
                console.log(`[Homepage] ${data.properties.length} propiedades de arriendo cargadas`);
            } else {
                this._renderEmptyState(container, {
                    icon: 'bi-house-fill',
                    message: 'No hay propiedades de arriendo disponibles en este momento'
                });
            }
        } catch (error) {
            console.error('[Homepage] Error cargando arriendos:', error);
        }
    },

    /**
     * Carga propiedades de venta usada
     * @private
     */
    _loadUsedSaleProperties: async function () {
        try {
            const container = getElement('#used-sale-properties-grid', this.el);
            if (!container) {
                console.warn('[Homepage] Contenedor used-sale-properties-grid no encontrado');
                return;
            }

            const data = await PropertyService.loadByType('sale', { limit: 4 });

            if (data.success && data.properties && data.properties.length > 0) {
                this._renderProperties(container, data.properties);
                this.propertiesData.usedSale = data.properties.filter(p => p.latitude && p.longitude);
                console.log(`[Homepage] ${data.properties.length} propiedades usadas cargadas`);
            } else {
                this._renderEmptyState(container, {
                    icon: 'bi-building',
                    message: 'No hay propiedades usadas en venta disponibles en este momento'
                });
            }
        } catch (error) {
            console.error('[Homepage] Error cargando ventas usadas:', error);
        }
    },

    /**
     * Carga proyectos
     * @private
     */
    _loadProjectsProperties: async function () {
        try {
            const container = getElement('#projects-properties-grid', this.el);
            if (!container) {
                console.warn('[Homepage] Contenedor projects-properties-grid no encontrado');
                return;
            }

            const data = await PropertyService.loadByType('projects', { limit: 4 });

            if (data.success && data.properties && data.properties.length > 0) {
                this._renderProperties(container, data.properties);
                this.propertiesData.projects = data.properties.filter(p => p.latitude && p.longitude);
                console.log(`[Homepage] ${data.properties.length} proyectos cargados`);
            } else {
                this._renderEmptyState(container, {
                    icon: 'bi-geo-alt-fill',
                    message: 'No hay proyectos en venta disponibles en este momento'
                });
            }
        } catch (error) {
            console.error('[Homepage] Error cargando proyectos:', error);
        }
    },

    // -------------------------------------------------------------------------
    // RENDERIZADO
    // -------------------------------------------------------------------------

    /**
     * Renderiza propiedades en un contenedor
     * @private
     * @param {HTMLElement} container
     * @param {Array} properties
     */
    _renderProperties: function (container, properties) {
        clearElement(container);

        properties.forEach(property => {
            const card = createPropertyCard(property);
            container.appendChild(card);
        });
    },

    /**
     * Renderiza estado vacío
     * @private
     * @param {HTMLElement} container
     * @param {Object} options
     */
    _renderEmptyState: function (container, options) {
        clearElement(container);
        const emptyState = createEmptyState(options);
        container.appendChild(emptyState);
    },

    // -------------------------------------------------------------------------
    // MAPAS
    // -------------------------------------------------------------------------

    /**
     * Configura los tabs de mapas
     * @private
     */
    _setupMapTabs: function () {
        // Tab de arriendo
        const arriendoTab = getElement('#arriendo-map-tab', this.el);
        if (arriendoTab) {
            arriendoTab.addEventListener('shown.bs.tab', this._onArriendoMapTabShow.bind(this));
        }

        // Tab de ventas usadas
        const usedSaleTab = getElement('[data-bs-target="#used-sale-map"]', this.el);
        if (usedSaleTab) {
            usedSaleTab.addEventListener('shown.bs.tab', this._onUsedSaleMapTabShow.bind(this));
        }

        // Tab de proyectos
        const projectsTab = getElement('[data-bs-target="#projects-map"]', this.el);
        if (projectsTab) {
            projectsTab.addEventListener('shown.bs.tab', this._onProjectsMapTabShow.bind(this));
        }
    },

    /**
     * Handler: Tab de mapa de arriendos mostrado
     * @private
     */
    _onArriendoMapTabShow: function () {
        const mapContainer = getElement('#arriendo-properties-map', this.el);
        if (!mapContainer) return;

        if (this.propertiesData.arriendo.length === 0) {
            this._renderMapEmptyState(mapContainer);
        } else {
            this._initMap('arriendo', 'arriendo-properties-map');
            this._updateMapMarkers(this.maps.arriendo, this.propertiesData.arriendo);
        }
    },

    /**
     * Handler: Tab de mapa de ventas usadas mostrado
     * @private
     */
    _onUsedSaleMapTabShow: function () {
        const mapContainer = getElement('#used-sale-properties-map', this.el);
        if (!mapContainer) return;

        if (this.propertiesData.usedSale.length === 0) {
            this._renderMapEmptyState(mapContainer);
        } else {
            this._initMap('usedSale', 'used-sale-properties-map');
            this._updateMapMarkers(this.maps.usedSale, this.propertiesData.usedSale);
        }
    },

    /**
     * Handler: Tab de mapa de proyectos mostrado
     * @private
     */
    _onProjectsMapTabShow: function () {
        const mapContainer = getElement('#projects-properties-map', this.el);
        if (!mapContainer) return;

        if (this.propertiesData.projects.length === 0) {
            this._renderMapEmptyState(mapContainer);
        } else {
            this._initMap('projects', 'projects-properties-map');
            this._updateMapMarkers(this.maps.projects, this.propertiesData.projects);
        }
    },

    /**
     * Inicializa un mapa
     * @private
     * @param {string} key - Clave del mapa (arriendo, usedSale, projects)
     * @param {string} mapId - ID del elemento del mapa
     */
    _initMap: function (key, mapId) {
        // Verificar Leaflet
        if (typeof L === 'undefined') {
            console.warn('[Homepage] Leaflet no está cargado');
            return;
        }

        const mapEl = document.getElementById(mapId);
        if (!mapEl) {
            console.warn('[Homepage] Elemento del mapa no encontrado:', mapId);
            return;
        }

        // Si ya existe, invalidar tamaño
        if (this.maps[key]) {
            setTimeout(() => this.maps[key].invalidateSize(), 100);
            return;
        }

        // Crear nuevo mapa (centrado en Bogotá por defecto)
        this.maps[key] = L.map(mapId).setView([4.7110, -74.0721], 11);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(this.maps[key]);

        console.log('[Homepage] Mapa inicializado:', mapId);
    },

    /**
     * Actualiza marcadores en el mapa
     * @private
     * @param {Object} map - Instancia del mapa
     * @param {Array} properties - Propiedades a mostrar
     */
    _updateMapMarkers: function (map, properties) {
        if (!map || typeof L === 'undefined') return;

        // Limpiar marcadores existentes
        map.eachLayer(layer => {
            if (layer instanceof L.Marker) {
                map.removeLayer(layer);
            }
        });

        // Agregar nuevos marcadores
        const bounds = [];

        properties.forEach(property => {
            if (property.latitude && property.longitude) {
                const marker = L.marker([property.latitude, property.longitude]).addTo(map);

                // Crear popup
                const popupContent = createMapPopup(property);

                marker.bindPopup(popupContent, {
                    maxWidth: 300,
                    className: 'bohio-map-popup'
                });

                bounds.push([property.latitude, property.longitude]);
            }
        });

        // Ajustar vista
        if (bounds.length > 0) {
            setTimeout(() => {
                map.fitBounds(bounds, {
                    padding: [50, 50],
                    maxZoom: 13
                });
            }, 200);
        }
    },

    /**
     * Renderiza estado vacío en el mapa
     * @private
     * @param {HTMLElement} container
     */
    _renderMapEmptyState: function (container) {
        container.innerHTML = '';

        const wrapper = document.createElement('div');
        wrapper.className = 'd-flex align-items-center justify-content-center h-100 bg-light';

        const content = document.createElement('div');
        content.className = 'text-center p-4';

        const icon = document.createElement('i');
        icon.className = 'fa fa-map-marked-alt fa-3x text-muted mb-3';
        content.appendChild(icon);

        const text = document.createElement('p');
        text.className = 'text-muted';
        text.textContent = 'No hay propiedades con ubicación disponible para mostrar en el mapa';
        content.appendChild(text);

        wrapper.appendChild(content);
        container.appendChild(wrapper);
    },

    // -------------------------------------------------------------------------
    // EVENT HANDLERS
    // -------------------------------------------------------------------------

    /**
     * Handler: Click en botón de tipo de servicio
     * @private
     * @param {Event} ev
     */
    _onServiceTypeClick: function (ev) {
        const button = ev.currentTarget;
        const serviceType = button.dataset.service;

        // Actualizar estados
        this.el.querySelectorAll('.service-type-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        button.classList.add('active');

        // Actualizar input oculto
        const serviceInput = getElement('#selectedServiceType', this.el);
        if (serviceInput) {
            serviceInput.value = serviceType;
        }
    },

    /**
     * Handler: Keypress en búsqueda rápida por código
     * @private
     * @param {Event} ev
     */
    _onQuickCodeKeypress: function (ev) {
        if (ev.key === 'Enter') {
            ev.preventDefault();
            this._quickSearchCode();
        }
    },

    /**
     * Handler: Keypress en modal de código
     * @private
     * @param {Event} ev
     */
    _onModalCodeKeypress: function (ev) {
        if (ev.key === 'Enter') {
            ev.preventDefault();
            this._searchPropertyByCode();
        }
    },

    /**
     * Búsqueda rápida por código
     * @private
     */
    _quickSearchCode: function () {
        const input = getElement('#quickCodeSearch', this.el);
        const code = input ? input.value.trim() : '';

        if (code) {
            window.location.href = '/properties?search=' + encodeURIComponent(code);
        }
    },

    /**
     * Búsqueda por código desde modal
     * @private
     */
    _searchPropertyByCode: function () {
        const input = getElement('#modalPropertyCode', this.el);
        const code = input ? input.value.trim() : '';

        if (code) {
            // Cerrar modal
            const modalEl = getElement('#codeSearchModal', this.el);
            if (modalEl && typeof bootstrap !== 'undefined') {
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            }

            // Redirigir
            window.location.href = '/properties?search=' + encodeURIComponent(code);
        } else {
            alert('Por favor ingresa un código de propiedad');
        }
    },
});

// =============================================================================
// REGISTRO DEL WIDGET
// =============================================================================

publicWidget.registry.HomepagePropertiesWidget = HomepagePropertiesWidget;

export default HomepagePropertiesWidget;

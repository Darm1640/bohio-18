/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import { AdvancedPropertyFilters } from './property_filters_advanced';
import { URLSync } from './utils/url_sync';

/**
 * BOHIO Property Shop Enhanced - Integración con Filtros Avanzados
 *
 * Características:
 * - Búsqueda por código unificada (funciona en home y shop)
 * - Integración con filtros avanzados
 * - Filtros dinámicos según tipo de propiedad
 * - Actualización en tiempo real de resultados
 * - Paginación y ordenamiento
 * - Vista grid y mapa
 * - Sincronización con URL para búsquedas compartibles
 */

class PropertyShopEnhanced {
    constructor() {
        this.filters = null;
        this.urlSync = new URLSync();
        this.currentPage = 1;
        this.itemsPerPage = 12;
        this.totalItems = 0;
        this.currentSort = 'relevance';
        this.currentView = 'grid';
        this.properties = [];
        this.searchTerm = '';
        this.isInitialLoad = true;
    }

    /**
     * Inicializar shop con filtros avanzados
     */
    async init() {
        // Verificar que estamos en la página del shop
        if (!document.getElementById('advancedFiltersShop')) {
            console.log('No estamos en el property shop, saltando inicialización');
            return;
        }

        console.log('Inicializando Property Shop Enhanced...');

        try {
            // Cargar estado inicial desde URL
            const urlState = this.urlSync.getStateFromURL();
            if (urlState.page) this.currentPage = urlState.page;
            if (urlState.sort) this.currentSort = urlState.sort;
            if (urlState.view) this.currentView = urlState.view;

            // Inicializar filtros avanzados
            await this.initAdvancedFilters();

            // Aplicar filtros desde URL si existen
            if (Object.keys(urlState.filters).length > 0) {
                await this.applyFiltersFromURL(urlState.filters);
            }

            // Inicializar búsqueda por código
            this.initCodeSearch();

            // Inicializar ordenamiento
            this.initSorting();

            // Inicializar tabs (grid/mapa)
            this.initTabs();

            // Inicializar navegación hacia atrás/adelante
            this.initURLNavigation();

            // Inicializar botón de compartir
            this.initShareButton();

            // Cargar propiedades iniciales
            await this.loadProperties();

            this.isInitialLoad = false;
            console.log('Property Shop Enhanced inicializado correctamente');
        } catch (error) {
            console.error('Error inicializando Property Shop Enhanced:', error);
        }
    }

    /**
     * Inicializar filtros avanzados
     */
    async initAdvancedFilters() {
        const container = document.getElementById('advancedFiltersShop');
        if (!container) return;

        this.filters = new AdvancedPropertyFilters(container);

        // Registrar callbacks
        this.filters.on('propertiesLoaded', (result) => {
            this.properties = result.properties;
            this.totalItems = result.total;
            this.renderProperties();
            this.renderPagination();
        });

        this.filters.on('filterChange', (currentFilters) => {
            console.log('Filtros cambiados:', currentFilters);
            // Los filtros se aplicarán cuando el usuario haga clic en "Buscar"
        });

        // Inicializar filtros
        await this.filters.init();
    }

    /**
     * Inicializar búsqueda por código (funciona en home y shop)
     */
    initCodeSearch() {
        const searchInput = document.getElementById('propertyCodeSearch');
        if (!searchInput) return;

        // Autocompletado mientras escribe
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            if (query.length >= 2) {
                this.searchByCodeAutocomplete(query);
            } else {
                this.hideAutocomplete();
            }
        });

        // Buscar al presionar Enter
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.searchByCodeExecute();
            }
        });

        // Buscar al hacer clic en el botón
        const searchBtn = searchInput.closest('.search-bar-container').querySelector('button');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                this.searchByCodeExecute();
            });
        }
    }

    /**
     * Autocompletado de búsqueda por código
     */
    async searchByCodeAutocomplete(query) {
        try {
            const result = await rpc('/shop/properties/search/code', {
                query: query,
                limit: 5
            });

            if (result.success && result.properties.length > 0) {
                this.showAutocomplete(result.properties);
            } else {
                this.hideAutocomplete();
            }
        } catch (error) {
            console.error('Error en autocompletado:', error);
        }
    }

    /**
     * Mostrar sugerencias de autocompletado
     */
    showAutocomplete(properties) {
        const container = document.querySelector('.autocomplete-container');
        if (!container) return;

        const html = properties.map(prop => `
            <div class="autocomplete-item p-3 border-bottom"
                 data-property-id="${prop.id}"
                 style="cursor: pointer;">
                <div class="d-flex align-items-center">
                    <img src="${prop.image_url}"
                         alt="${prop.name}"
                         class="rounded me-3"
                         style="width: 60px; height: 60px; object-fit: cover;">
                    <div class="flex-grow-1">
                        <div class="fw-bold">${prop.default_code}</div>
                        <div class="text-muted small">${prop.name}</div>
                        <div class="text-danger small">${prop.currency} ${this.formatPrice(prop.net_price)}</div>
                    </div>
                    <i class="bi bi-arrow-right text-danger"></i>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
        container.style.display = 'block';

        // Event listeners para los items
        container.querySelectorAll('.autocomplete-item').forEach(item => {
            item.addEventListener('click', () => {
                const propertyId = item.dataset.propertyId;
                window.location.href = `/property/${propertyId}`;
            });
        });
    }

    /**
     * Ocultar autocompletado
     */
    hideAutocomplete() {
        const container = document.querySelector('.autocomplete-container');
        if (container) {
            container.style.display = 'none';
        }
    }

    /**
     * Ejecutar búsqueda por código
     */
    async searchByCodeExecute() {
        const searchInput = document.getElementById('propertyCodeSearch');
        if (!searchInput) return;

        const query = searchInput.value.trim();
        if (!query) return;

        this.searchTerm = query;
        this.currentPage = 1;

        // Si los filtros están disponibles, usarlos
        if (this.filters) {
            this.filters.filters.search_code = query;
            await this.filters.searchProperties(this.itemsPerPage, 0);
        } else {
            // Búsqueda simple
            await this.loadProperties();
        }

        this.hideAutocomplete();
        this.updateURL(); // Actualizar URL con búsqueda
    }

    /**
     * Inicializar ordenamiento
     */
    initSorting() {
        const sortSelect = document.querySelector('.property-sort');
        if (!sortSelect) return;

        // Establecer valor inicial desde URL
        if (this.currentSort && this.currentSort !== 'relevance') {
            sortSelect.value = this.currentSort;
        }

        sortSelect.addEventListener('change', (e) => {
            this.currentSort = e.target.value;
            this.currentPage = 1;
            this.loadProperties();
            this.updateURL(); // Actualizar URL con ordenamiento
        });
    }

    /**
     * Inicializar tabs (grid/mapa)
     */
    initTabs() {
        const gridTab = document.querySelector('[data-bs-target="#grid-view"]');
        const mapTab = document.querySelector('[data-bs-target="#map-view"]');

        // Activar tab inicial según URL
        if (this.currentView === 'map' && mapTab) {
            const tab = new bootstrap.Tab(mapTab);
            tab.show();
        }

        if (mapTab) {
            mapTab.addEventListener('shown.bs.tab', () => {
                this.currentView = 'map';
                this.renderMap();
                this.updateURL(); // Actualizar URL con vista
            });
        }

        if (gridTab) {
            gridTab.addEventListener('shown.bs.tab', () => {
                this.currentView = 'grid';
                this.updateURL(); // Actualizar URL con vista
            });
        }
    }

    /**
     * Cargar propiedades
     */
    async loadProperties() {
        try {
            const offset = (this.currentPage - 1) * this.itemsPerPage;

            // Construir orden
            let order = 'id desc';
            switch (this.currentSort) {
                case 'price_asc':
                    order = 'net_price asc';
                    break;
                case 'price_desc':
                    order = 'net_price desc';
                    break;
                case 'newest':
                    order = 'create_date desc';
                    break;
                case 'area_desc':
                    order = 'area_in_m2 desc';
                    break;
            }

            // Si tenemos filtros avanzados, usarlos
            if (this.filters) {
                const result = await this.filters.searchProperties(this.itemsPerPage, offset);
                if (result) {
                    this.properties = result.properties;
                    this.totalItems = result.total;
                }
            } else {
                // Búsqueda simple
                const result = await rpc('/api/property/search/advanced', {
                    filters: { search_code: this.searchTerm },
                    limit: this.itemsPerPage,
                    offset: offset,
                    order: order
                });

                if (result.success) {
                    this.properties = result.properties;
                    this.totalItems = result.total;
                }
            }

            this.renderProperties();
            this.renderPagination();

        } catch (error) {
            console.error('Error cargando propiedades:', error);
            this.showError('Error cargando propiedades. Por favor, intenta nuevamente.');
        }
    }

    /**
     * Renderizar propiedades en grid
     */
    renderProperties() {
        const grid = document.getElementById('properties-grid');
        if (!grid) return;

        if (this.properties.length === 0) {
            grid.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="bi bi-search display-1 text-muted"></i>
                    <h3 class="mt-3">No se encontraron propiedades</h3>
                    <p class="text-muted">Intenta ajustar los filtros de búsqueda</p>
                </div>
            `;
            return;
        }

        const html = this.properties.map(prop => this.renderPropertyCard(prop)).join('');
        grid.innerHTML = html;

        // Inicializar lazy loading de imágenes
        if (window.lazyImageLoader) {
            window.lazyImageLoader.init();
        }
    }

    /**
     * Renderizar tarjeta de propiedad
     */
    renderPropertyCard(property) {
        return `
            <div class="col-lg-4 col-md-6">
                <div class="property-card shadow-sm h-100">
                    <div class="property-image position-relative">
                        <img src="${property.image_url}"
                             alt="${property.name}"
                             class="w-100"
                             loading="lazy"
                             style="height: 250px; object-fit: cover;">
                        <div class="property-badge position-absolute top-0 start-0 m-3">
                            <span class="badge bg-danger">${property.property_type}</span>
                        </div>
                        <div class="property-code position-absolute top-0 end-0 m-3">
                            <span class="badge bg-dark">${property.default_code}</span>
                        </div>
                    </div>
                    <div class="property-body p-3">
                        <h5 class="property-title mb-2">${property.name}</h5>
                        <p class="property-location text-muted mb-2">
                            <i class="bi bi-geo-alt me-1"></i>
                            ${property.city}${property.region ? ', ' + property.region : ''}
                        </p>
                        <p class="property-price text-danger fw-bold fs-5 mb-3">
                            ${property.currency} ${this.formatPrice(property.net_price)}
                        </p>
                        <div class="property-specs d-flex justify-content-between text-muted small mb-3">
                            ${property.num_bedrooms ? `
                                <span>
                                    <i class="bi bi-house-door me-1"></i>
                                    ${property.num_bedrooms} hab
                                </span>
                            ` : ''}
                            ${property.num_bathrooms ? `
                                <span>
                                    <i class="bi bi-droplet me-1"></i>
                                    ${property.num_bathrooms} baños
                                </span>
                            ` : ''}
                            ${property.property_area ? `
                                <span>
                                    <i class="bi bi-arrows-fullscreen me-1"></i>
                                    ${property.property_area} m²
                                </span>
                            ` : ''}
                        </div>
                        <a href="${property.url}" class="btn btn-danger w-100">
                            Ver Detalle <i class="bi bi-arrow-right ms-2"></i>
                        </a>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Renderizar paginación
     */
    renderPagination() {
        const container = document.getElementById('paginationContainer');
        if (!container) return;

        const totalPages = Math.ceil(this.totalItems / this.itemsPerPage);

        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let html = `
            <nav aria-label="Navegación de propiedades">
                <ul class="pagination justify-content-center">
                    <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                        <a class="page-link" href="#" data-page="${this.currentPage - 1}">
                            <i class="bi bi-chevron-left"></i>
                        </a>
                    </li>
        `;

        // Páginas
        for (let i = 1; i <= totalPages; i++) {
            if (
                i === 1 ||
                i === totalPages ||
                (i >= this.currentPage - 2 && i <= this.currentPage + 2)
            ) {
                html += `
                    <li class="page-item ${i === this.currentPage ? 'active' : ''}">
                        <a class="page-link" href="#" data-page="${i}">${i}</a>
                    </li>
                `;
            } else if (i === this.currentPage - 3 || i === this.currentPage + 3) {
                html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }

        html += `
                    <li class="page-item ${this.currentPage === totalPages ? 'disabled' : ''}">
                        <a class="page-link" href="#" data-page="${this.currentPage + 1}">
                            <i class="bi bi-chevron-right"></i>
                        </a>
                    </li>
                </ul>
            </nav>
        `;

        container.innerHTML = html;

        // Event listeners para paginación
        container.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(e.currentTarget.dataset.page);
                if (page && page !== this.currentPage) {
                    this.currentPage = page;
                    this.loadProperties();
                    this.updateURL(); // Actualizar URL con página
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }
            });
        });
    }

    /**
     * Renderizar mapa con Leaflet
     */
    renderMap() {
        const mapContainer = document.getElementById('properties-map');
        if (!mapContainer) return;

        // Verificar que Leaflet esté disponible
        if (typeof L === 'undefined') {
            console.error('Leaflet no está cargado');
            mapContainer.innerHTML = `
                <div class="alert alert-warning m-4">
                    <i class="bi bi-exclamation-triangle me-2"></i>
                    Mapa no disponible. Leaflet no está cargado.
                </div>
            `;
            return;
        }

        // Destruir mapa anterior si existe
        if (this.map) {
            this.map.remove();
        }

        // Configuración del mapa centrado en Colombia
        const defaultCenter = [4.570868, -74.297333]; // Bogotá
        const defaultZoom = 6;

        // Crear mapa
        this.map = L.map('properties-map').setView(defaultCenter, defaultZoom);

        // Añadir capa de OpenStreetMap
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(this.map);

        // Añadir marcadores de propiedades
        const bounds = [];
        const markers = [];

        this.properties.forEach(prop => {
            // Solo añadir si tiene coordenadas
            if (prop.latitude && prop.longitude) {
                const lat = parseFloat(prop.latitude);
                const lng = parseFloat(prop.longitude);

                // Crear icono personalizado
                const markerIcon = L.divIcon({
                    html: `
                        <div class="custom-marker">
                            <div class="marker-price bg-danger text-white px-2 py-1 rounded shadow-sm">
                                ${prop.currency} ${this.formatPrice(prop.net_price)}
                            </div>
                            <div class="marker-pin"></div>
                        </div>
                    `,
                    className: 'custom-marker-container',
                    iconSize: [120, 50],
                    iconAnchor: [60, 50]
                });

                // Crear marcador
                const marker = L.marker([lat, lng], { icon: markerIcon }).addTo(this.map);

                // Popup con info de la propiedad
                const popupContent = `
                    <div class="property-popup" style="min-width: 250px;">
                        <img src="${prop.image_url}"
                             alt="${prop.name}"
                             style="width: 100%; height: 150px; object-fit: cover; border-radius: 4px; margin-bottom: 10px;">
                        <h6 class="mb-1">${prop.name}</h6>
                        <p class="text-muted small mb-1">
                            <i class="bi bi-geo-alt me-1"></i>
                            ${prop.city}
                        </p>
                        <p class="text-danger fw-bold mb-2">
                            ${prop.currency} ${this.formatPrice(prop.net_price)}
                        </p>
                        <div class="d-flex justify-content-between text-muted small mb-2">
                            ${prop.num_bedrooms ? `<span><i class="bi bi-house-door me-1"></i>${prop.num_bedrooms} hab</span>` : ''}
                            ${prop.num_bathrooms ? `<span><i class="bi bi-droplet me-1"></i>${prop.num_bathrooms} baños</span>` : ''}
                            ${prop.property_area ? `<span><i class="bi bi-arrows-fullscreen me-1"></i>${prop.property_area} m²</span>` : ''}
                        </div>
                        <a href="${prop.url}" class="btn btn-danger btn-sm w-100">
                            Ver Detalle <i class="bi bi-arrow-right ms-1"></i>
                        </a>
                    </div>
                `;

                marker.bindPopup(popupContent, {
                    maxWidth: 300,
                    className: 'property-popup-container'
                });

                markers.push(marker);
                bounds.push([lat, lng]);
            }
        });

        // Ajustar vista del mapa a los marcadores
        if (bounds.length > 0) {
            this.map.fitBounds(bounds, {
                padding: [50, 50],
                maxZoom: 15
            });
        }

        // Añadir control de capas
        const baseMaps = {
            "OpenStreetMap": L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }),
            "Satélite": L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                attribution: 'Tiles © Esri'
            })
        };

        L.control.layers(baseMaps).addTo(this.map);

        // Cluster de marcadores si hay muchas propiedades
        if (markers.length > 10 && typeof L.markerClusterGroup !== 'undefined') {
            const clusterGroup = L.markerClusterGroup();
            markers.forEach(marker => clusterGroup.addLayer(marker));
            this.map.addLayer(clusterGroup);
        }

        console.log(`Mapa renderizado con ${markers.length} propiedades`);
    }

    /**
     * Aplicar filtros desde URL
     */
    async applyFiltersFromURL(urlFilters) {
        if (!this.filters) return;

        // Aplicar cada filtro al sistema de filtros
        if (urlFilters.price_min || urlFilters.price_max) {
            // Actualizar sliders de precio si existen
            const minInput = document.querySelector('input[name="price_min"]');
            const maxInput = document.querySelector('input[name="price_max"]');
            if (minInput && urlFilters.price_min) minInput.value = urlFilters.price_min;
            if (maxInput && urlFilters.price_max) maxInput.value = urlFilters.price_max;
        }

        // Marcar checkboxes según filtros URL
        ['bedrooms', 'bathrooms', 'parking', 'stratum', 'area_range', 'characteristics'].forEach(filterType => {
            if (urlFilters[filterType]) {
                const values = Array.isArray(urlFilters[filterType]) ? urlFilters[filterType] : [urlFilters[filterType]];
                values.forEach(value => {
                    const checkbox = document.querySelector(`input[name="${filterType}"][value="${value}"]`);
                    if (checkbox) checkbox.checked = true;
                });
            }
        });

        // Actualizar filtros internos
        this.filters.currentFilters = { ...this.filters.currentFilters, ...urlFilters };
    }

    /**
     * Inicializar navegación con botones atrás/adelante
     */
    initURLNavigation() {
        this.urlSync.onPopState(async (state) => {
            if (this.isInitialLoad) return;

            // Restaurar estado desde navegación
            this.currentPage = state.page || 1;
            this.currentSort = state.sort || 'relevance';
            this.currentView = state.view || 'grid';

            // Aplicar filtros
            if (state.filters && Object.keys(state.filters).length > 0) {
                await this.applyFiltersFromURL(state.filters);
            } else {
                // Limpiar filtros si no hay en URL
                if (this.filters) {
                    this.filters.clearFilters();
                }
            }

            // Recargar propiedades
            await this.loadProperties();
        });
    }

    /**
     * Inicializar botón de compartir búsqueda
     */
    initShareButton() {
        // Crear botón de compartir si no existe
        const headerActions = document.querySelector('.col-md-4.text-end');
        if (!headerActions) return;

        const shareBtn = document.createElement('button');
        shareBtn.className = 'btn btn-outline-danger ms-2';
        shareBtn.innerHTML = '<i class="bi bi-share"></i> Compartir';
        shareBtn.title = 'Compartir esta búsqueda';

        shareBtn.addEventListener('click', async () => {
            const state = this.getCurrentState();
            const result = await this.urlSync.copyShareableURL(state);

            if (result.success) {
                // Mostrar notificación de éxito
                this.showNotification('URL copiada al portapapeles', 'success');
            } else {
                // Mostrar modal con URL si falló copiar
                this.showShareModal(result.url);
            }
        });

        headerActions.appendChild(shareBtn);
    }

    /**
     * Obtener estado actual de filtros y búsqueda
     */
    getCurrentState() {
        return {
            filters: this.filters ? this.filters.currentFilters : {},
            page: this.currentPage,
            sort: this.currentSort,
            view: this.currentView
        };
    }

    /**
     * Actualizar URL con estado actual
     */
    updateURL() {
        if (this.isInitialLoad) return;

        const state = this.getCurrentState();
        this.urlSync.updateURL(state);
    }

    /**
     * Mostrar notificación
     */
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
        notification.style.zIndex = '9999';
        notification.innerHTML = `
            <i class="bi bi-check-circle me-2"></i>
            ${message}
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    /**
     * Mostrar modal con URL para compartir
     */
    showShareModal(url) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-share me-2"></i>
                            Compartir búsqueda
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Comparte esta URL para que otros vean los mismos resultados:</p>
                        <div class="input-group">
                            <input type="text" class="form-control" value="${url}" readonly>
                            <button class="btn btn-danger" type="button" onclick="navigator.clipboard.writeText('${url}')">
                                <i class="bi bi-clipboard"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();

        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }

    /**
     * Formatear precio
     */
    formatPrice(price) {
        if (!price) return '0';
        return new Intl.NumberFormat('es-CO').format(price);
    }

    /**
     * Mostrar error
     */
    showError(message) {
        const grid = document.getElementById('properties-grid');
        if (grid) {
            grid.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger" role="alert">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        ${message}
                    </div>
                </div>
            `;
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', async () => {
    const shop = new PropertyShopEnhanced();
    await shop.init();

    // Exportar globalmente para uso en otros scripts
    window.propertyShopEnhanced = shop;
});

// Función global para búsqueda por código (compatible con home)
window.searchByCode = function() {
    if (window.propertyShopEnhanced) {
        window.propertyShopEnhanced.searchByCodeExecute();
    }
};

export { PropertyShopEnhanced };

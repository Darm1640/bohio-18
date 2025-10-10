/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

console.log('BOHIO Property Shop JS cargado');

class PropertyShop {
    constructor() {
        this.context = 'public';
        this.filters = {};
        this.comparisonList = [];
        this.map = null;
        this.markers = null;
        this.autocompleteTimeout = null;
        this.currentProperties = [];

        // Paginación
        this.currentPage = 1;
        this.itemsPerPage = 40;
        this.totalItems = 0;
        this.totalPages = 0;

        this.init();
    }

    init() {
        console.log('Inicializando Property Shop...');

        // Obtener contexto
        const container = document.querySelector('.property_search_container');
        if (container) {
            this.context = container.dataset.context || 'public';
        }

        // Leer filtros de la URL
        this.readFiltersFromURL();

        // Inicializar componentes
        this.initSearch();
        this.initFilters();
        this.initComparison();
        this.initMap();

        // Cargar propiedades iniciales
        this.loadProperties();
    }

    // =================== GESTIÓN DE URL ===================

    readFiltersFromURL() {
        const params = new URLSearchParams(window.location.search);
        this.filters = {};

        // Leer todos los parámetros de filtro
        const filterKeys = ['type_service', 'property_type', 'bedrooms', 'bathrooms', 'min_price', 'max_price', 'garage', 'pool', 'garden', 'elevator', 'order'];
        filterKeys.forEach(key => {
            const value = params.get(key);
            if (value) {
                this.filters[key] = value;
            }
        });

        // Leer página
        const page = params.get('page');
        if (page) {
            this.currentPage = parseInt(page);
        }

        console.log('Filtros leídos de URL:', this.filters);
    }

    updateURL() {
        const params = new URLSearchParams();

        // Agregar filtros a la URL
        Object.keys(this.filters).forEach(key => {
            if (this.filters[key]) {
                params.set(key, this.filters[key]);
            }
        });

        // Agregar página si no es la primera
        if (this.currentPage > 1) {
            params.set('page', this.currentPage);
        }

        // Actualizar URL sin recargar la página
        const newURL = `${window.location.pathname}?${params.toString()}`;
        window.history.pushState({}, '', newURL);
    }

    // =================== BÚSQUEDA Y AUTOCOMPLETADO ===================

    initSearch() {
        const searchInput = document.querySelector('.property-search-input');
        if (!searchInput) return;

        searchInput.addEventListener('input', (e) => {
            clearTimeout(this.autocompleteTimeout);
            const term = e.target.value.trim();

            if (term.length < 2) {
                this.hideAutocomplete();
                return;
            }

            this.autocompleteTimeout = setTimeout(() => {
                this.performAutocomplete(term);
            }, 300);
        });
    }

    async performAutocomplete(term) {
        const subdivision = document.querySelector('.subdivision-filter')?.value || 'all';

        try {
            const result = await rpc('/property/search/autocomplete/' + this.context, {
                term: term,
                subdivision: subdivision,
                limit: 10
            });

            this.renderAutocompleteResults(result.results || []);
        } catch (error) {
            console.error('Error en autocompletado:', error);
        }
    }

    renderAutocompleteResults(results) {
        const container = document.querySelector('.autocomplete-container');
        if (!container) return;

        if (results.length === 0) {
            container.innerHTML = '<div class="p-3 text-muted">No se encontraron resultados</div>';
            container.style.display = 'block';
            return;
        }

        let html = '<ul class="list-unstyled mb-0">';
        results.forEach(result => {
            html += `
                <li class="autocomplete-item p-3 border-bottom" style="cursor: pointer;" data-type="${result.type}" data-id="${result.id}">
                    <div>${result.label}</div>
                    <small class="text-muted">${result.property_count} ${result.property_count === 1 ? 'propiedad' : 'propiedades'}</small>
                </li>
            `;
        });
        html += '</ul>';

        container.innerHTML = html;
        container.style.display = 'block';

        // Event listeners para items
        container.querySelectorAll('.autocomplete-item').forEach(item => {
            item.addEventListener('click', () => {
                this.selectAutocompleteItem(item.dataset);
            });
        });
    }

    selectAutocompleteItem(data) {
        // Agregar filtro según el tipo seleccionado
        if (data.type === 'city') {
            this.filters.city_id = data.id;
        } else if (data.type === 'region') {
            this.filters.region_id = data.id;
        } else if (data.type === 'property') {
            window.location.href = `/property/${data.id}`;
            return;
        }

        this.hideAutocomplete();
        this.loadProperties();
    }

    hideAutocomplete() {
        const container = document.querySelector('.autocomplete-container');
        if (container) {
            container.style.display = 'none';
        }
    }

    // =================== FILTROS ===================

    initFilters() {
        // Sincronizar valores del formulario con filtros de la URL
        this.syncFormWithFilters();

        // Filtros checkboxes y selects
        document.querySelectorAll('.property-filter').forEach(filter => {
            filter.addEventListener('change', () => {
                this.updateFilters();
                this.loadProperties();
            });
        });

        // Ordenamiento
        const sortSelect = document.querySelector('.property-sort');
        if (sortSelect) {
            sortSelect.addEventListener('change', (e) => {
                this.filters.order = e.target.value;
                this.updateURL();
                this.loadProperties();
            });
        }

        // Limpiar filtros
        const clearButton = document.querySelector('.clear-filters');
        if (clearButton) {
            clearButton.addEventListener('click', () => {
                this.clearFilters();
            });
        }
    }

    syncFormWithFilters() {
        // Sincronizar valores de los inputs con los filtros leídos de la URL
        document.querySelectorAll('.property-filter').forEach(filter => {
            const filterName = filter.dataset.filter;
            if (!filterName || !this.filters[filterName]) return;

            const filterValue = this.filters[filterName];

            if (filter.type === 'checkbox') {
                filter.checked = Array.isArray(filterValue) && filterValue.includes(filter.dataset.value || filter.value);
            } else if (filter.tagName === 'SELECT' || filter.type === 'number' || filter.type === 'text') {
                filter.value = filterValue;
            }
        });

        // Sincronizar orden
        const sortSelect = document.querySelector('.property-sort');
        if (sortSelect && this.filters.order) {
            sortSelect.value = this.filters.order;
        }
    }

    updateFilters() {
        this.filters = {};

        document.querySelectorAll('.property-filter').forEach(filter => {
            const filterName = filter.dataset.filter;
            const filterValue = filter.dataset.value || filter.value;

            if (!filterName) return;

            if (filter.type === 'checkbox' && filter.checked) {
                if (!this.filters[filterName]) {
                    this.filters[filterName] = [];
                }
                this.filters[filterName].push(filterValue);
            } else if (filter.type === 'number' && filterValue) {
                this.filters[filterName] = filterValue;
            } else if (filter.tagName === 'SELECT' && filterValue) {
                this.filters[filterName] = filterValue;
            }
        });

        console.log('Filtros actualizados:', this.filters);

        // Actualizar URL con los nuevos filtros
        this.updateURL();
    }

    clearFilters() {
        this.filters = {};

        document.querySelectorAll('.property-filter').forEach(filter => {
            if (filter.type === 'checkbox') {
                filter.checked = false;
            } else {
                filter.value = '';
            }
        });

        // Actualizar URL (limpia)
        this.updateURL();
        this.loadProperties();
    }

    // =================== CARGAR PROPIEDADES ===================

    async loadProperties() {
        console.log('Cargando propiedades con filtros:', this.filters);

        const gridContainer = document.getElementById('properties-grid');
        if (!gridContainer) return;

        // Mostrar loading
        gridContainer.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="spinner-border text-danger" role="status"></div>
                <p class="text-muted mt-3">Cargando propiedades...</p>
            </div>
        `;

        try {
            console.log('Enviando request a /bohio/api/properties con filtros:', this.filters);
            const result = await rpc('/bohio/api/properties', {
                ...this.filters,
                context: this.context,
                limit: this.itemsPerPage,
                offset: (this.currentPage - 1) * this.itemsPerPage
            });

            console.log('Datos recibidos:', result);

            this.currentProperties = result.items || result.properties || [];
            this.totalItems = result.total || this.currentProperties.length;
            this.totalPages = Math.ceil(this.totalItems / this.itemsPerPage);

            console.log(`Propiedades: ${this.currentProperties.length} de ${this.totalItems} total (Página ${this.currentPage}/${this.totalPages})`);

            this.renderProperties(this.currentProperties);
            this.updateMap(this.currentProperties);
            this.updateCounter(this.totalItems);
            this.renderPagination();
        } catch (error) {
            console.error('Error cargando propiedades:', error);

            let errorMessage = error.message;
            let errorDetails = '';

            if (error.message.includes('503')) {
                errorMessage = 'El servidor no está disponible (Error 503)';
                errorDetails = `
                    <div class="alert alert-warning mt-3">
                        <h6><i class="fa fa-info-circle"></i> Posibles causas:</h6>
                        <ul class="text-start mb-0">
                            <li>El servidor Odoo no está ejecutándose</li>
                            <li>Error en el código del servidor</li>
                            <li>Base de datos no disponible</li>
                        </ul>
                        <p class="mt-2 mb-0"><strong>Acción:</strong> Verifica que Odoo esté corriendo y revisa los logs del servidor.</p>
                    </div>
                `;
            } else if (error.message.includes('404')) {
                errorMessage = 'La ruta /bohio/api/properties no existe (Error 404)';
                errorDetails = '<p class="text-muted mt-2">Verifica que el módulo theme_bohio_real_estate esté instalado correctamente.</p>';
            }

            gridContainer.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fa fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                    <h5 class="text-danger mb-3">Error al cargar propiedades</h5>
                    <p class="text-muted">${errorMessage}</p>
                    ${errorDetails}
                    <button class="btn btn-danger mt-3" onclick="location.reload()">
                        <i class="fa fa-refresh"></i> Reintentar
                    </button>
                </div>
            `;
        }
    }

    renderProperties(properties) {
        const gridContainer = document.getElementById('properties-grid');
        if (!gridContainer) return;

        if (properties.length === 0) {
            gridContainer.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fa fa-home fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No se encontraron propiedades</p>
                    <button class="btn btn-outline-danger clear-filters">Limpiar Filtros</button>
                </div>
            `;
            return;
        }

        gridContainer.innerHTML = properties.map(prop => this.renderPropertyCard(prop)).join('');

        // Re-attach event listeners para comparación y CRM
        this.attachComparisonListeners();
        this.attachCRMListeners();
    }

    renderPropertyCard(property) {
        const imageUrl = property.image_url || '/theme_bohio_real_estate/static/src/img/banner1.jpg';
        const price = this.formatPrice(property.list_price);
        const priceLabel = property.type_service === 'rent' ? `$${price}/mes` : `$${price}`;
        const isInComparison = this.comparisonList.includes(property.id);

        // Ubicación completa
        const location = [property.address, property.region, property.city, property.state]
            .filter(x => x).join(', ');

        return `
            <div class="col-lg-4 col-md-6 mb-4 d-flex justify-content-center">
                <div class="card property-card shadow-sm border-0" style="width: 100%; max-width: 380px;">
                    <div class="position-relative" style="width: 100%; padding-top: 100%; overflow: hidden;">
                        <img src="${imageUrl}" class="position-absolute top-0 start-0 w-100 h-100" alt="${property.name}" style="object-fit: cover; object-position: center;"/>
                        <div class="position-absolute top-0 end-0 m-3">
                            <span class="badge px-3 py-2 fs-6 fw-bold" style="background: #E31E24;">${priceLabel}</span>
                        </div>
                        <div class="position-absolute top-0 start-0 m-3 d-flex flex-column gap-1">
                            ${property.type_service === 'rent' ? '<span class="badge me-1" style="background: #E31E24;">Arriendo</span>' : ''}
                            ${property.type_service === 'sale' ? '<span class="badge me-1" style="background: #10B981;">Venta</span>' : ''}
                            ${property.is_new ? '<span class="badge bg-warning text-dark">NUEVO</span>' : ''}
                            ${property.property_type_name ? `<span class="badge bg-info text-white">${property.property_type_name}</span>` : ''}
                        </div>
                        <div class="position-absolute bottom-0 end-0 m-3 d-flex gap-2">
                            <button class="btn btn-sm ${isInComparison ? 'btn-warning' : 'btn-outline-light'} add-to-comparison"
                                    data-property-id="${property.id}"
                                    title="Comparar">
                                <i class="fa fa-balance-scale"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-light add-to-crm"
                                    data-property-id="${property.id}"
                                    title="Agregar al CRM">
                                <i class="fa fa-heart"></i>
                            </button>
                        </div>
                    </div>
                    <div class="card-body d-flex flex-column">
                        <h5 class="card-title mb-2">
                            <a href="/property/${property.id}" class="text-decoration-none" style="color: #E31E24; font-weight: 600;">
                                ${property.name.substring(0, 50)}${property.name.length > 50 ? '...' : ''}
                            </a>
                        </h5>

                        <!-- Código -->
                        <div class="mb-2">
                            <small class="text-muted">Código: <strong style="color: #E31E24;">${property.default_code || 'N/A'}</strong></small>
                        </div>

                        <!-- Ubicación Precisa -->
                        <p class="text-muted small mb-2">
                            <i class="fa fa-map-marker text-danger me-1"></i>
                            ${location || 'Ubicación no disponible'}
                        </p>

                        <!-- Tipo de Propiedad -->
                        ${property.property_type_name ? `
                            <p class="text-muted small mb-2">
                                <i class="fa fa-building text-danger me-1"></i>
                                ${property.property_type_name}
                            </p>
                        ` : ''}

                        <!-- OBSERVACIONES PRIMERO -->
                        ${property.description ? `
                            <div class="alert alert-light mb-3 p-2" style="border-left: 3px solid #E31E24;">
                                <small class="fw-bold text-danger d-block mb-1">
                                    <i class="fa fa-comment"></i> Observaciones:
                                </small>
                                <small class="text-muted">
                                    ${property.description.substring(0, 100)}${property.description.length > 100 ? '...' : ''}
                                </small>
                            </div>
                        ` : ''}

                        <!-- Características Básicas -->
                        ${this.renderFeatures(property)}

                        <!-- Características Adicionales Agrupadas -->
                        ${this.renderAdditionalFeatures(property)}

                        <a href="/property/${property.id}" class="btn w-100 mt-auto" style="background: #E31E24; color: white; border: none;">
                            Ver Detalles
                        </a>
                    </div>
                </div>
            </div>
        `;
    }

    renderFeatures(property) {
        let html = '<div class="mb-3 pb-2 border-bottom">';

        if (['apartment', 'house'].includes(property.property_type)) {
            html += `
                <div class="d-flex justify-content-between">
                    <span class="text-muted small">
                        <img src="/theme_bohio_real_estate/static/src/img/habitacion-8.png" style="width: 18px; height: 18px;" alt="Hab"/>
                        <strong>${property.bedrooms || 0}</strong>
                    </span>
                    <span class="text-muted small">
                        <img src="/theme_bohio_real_estate/static/src/img/baño_1-8.png" style="width: 18px; height: 18px;" alt="Baños"/>
                        <strong>${property.bathrooms || 0}</strong>
                    </span>
                    <span class="text-muted small">
                        <img src="/theme_bohio_real_estate/static/src/img/areas_1-8.png" style="width: 18px; height: 18px;" alt="Área"/>
                        <strong>${property.area_constructed || 0}</strong> m²
                    </span>
                </div>
            `;
        } else {
            html += `
                <div class="d-flex justify-content-start">
                    <span class="text-muted small">
                        <img src="/theme_bohio_real_estate/static/src/img/areas_1-8.png" style="width: 18px; height: 18px;" alt="Área"/>
                        <strong>${property.area_total || 0}</strong> m²
                    </span>
                </div>
            `;
        }

        // Estrato y parqueadero
        if (property.stratum > 0 || property.parking > 0) {
            html += `<div class="d-flex justify-content-between mt-2">`;
            if (property.stratum > 0) {
                html += `<span class="text-muted small"><i class="fa fa-star text-warning"></i> Estrato ${property.stratum}</span>`;
            }
            if (property.parking > 0) {
                html += `<span class="text-muted small"><i class="fa fa-car text-primary"></i> ${property.parking} Parqueo(s)</span>`;
            }
            html += `</div>`;
        }

        html += '</div>';
        return html;
    }

    renderAdditionalFeatures(property) {
        const features = [];

        // Amenidades del inmueble
        if (property.furnished) features.push({ icon: 'fa-cube', text: 'Amoblado', color: 'info' });
        if (property.balcony) features.push({ icon: 'fa-building', text: 'Balcón', color: 'primary' });
        if (property.terrace) features.push({ icon: 'fa-sun-o', text: 'Terraza', color: 'warning' });
        if (property.patio) features.push({ icon: 'fa-tree', text: 'Patio', color: 'success' });
        if (property.garden) features.push({ icon: 'fa-leaf', text: 'Jardín', color: 'success' });
        if (property.laundry_area) features.push({ icon: 'fa-tint', text: 'Zona Lavandería', color: 'info' });
        if (property.warehouse) features.push({ icon: 'fa-archive', text: 'Depósito', color: 'secondary' });
        if (property.fireplace) features.push({ icon: 'fa-fire', text: 'Chimenea', color: 'danger' });
        if (property.mezzanine) features.push({ icon: 'fa-level-up', text: 'Mezzanine', color: 'info' });

        // Servicios del edificio
        if (property.elevator) features.push({ icon: 'fa-arrows-v', text: 'Ascensor', color: 'primary' });
        if (property.gym) features.push({ icon: 'fa-heartbeat', text: 'Gimnasio', color: 'danger' });
        if (property.pools) features.push({ icon: 'fa-tint', text: 'Piscina', color: 'info' });
        if (property.social_room) features.push({ icon: 'fa-users', text: 'Salón Social', color: 'warning' });
        if (property.green_areas) features.push({ icon: 'fa-tree', text: 'Zonas Verdes', color: 'success' });
        if (property.has_playground) features.push({ icon: 'fa-child', text: 'Zona Juegos', color: 'warning' });
        if (property.sports_area) features.push({ icon: 'fa-futbol-o', text: 'Cancha', color: 'success' });

        // Servicios y comodidades
        if (property.air_conditioning) features.push({ icon: 'fa-snowflake-o', text: 'Aire Acond.', color: 'info' });
        if (property.hot_water) features.push({ icon: 'fa-fire', text: 'Agua Caliente', color: 'danger' });

        // Seguridad
        if (property.has_security) features.push({ icon: 'fa-shield', text: 'Seguridad', color: 'primary' });
        if (property.security_cameras) features.push({ icon: 'fa-video-camera', text: 'Cámaras', color: 'secondary' });
        if (property.alarm) features.push({ icon: 'fa-bell', text: 'Alarma', color: 'danger' });
        if (property.intercom) features.push({ icon: 'fa-phone', text: 'Citófono', color: 'info' });
        if (property.doorman) {
            const doormanText = {
                '24_hours': '24h Portería',
                'daytime': 'Portería Diurna',
                'virtual': 'Video Portería',
            };
            features.push({ icon: 'fa-user-circle', text: doormanText[property.doorman] || 'Portería', color: 'primary' });
        }

        if (features.length === 0) {
            return '';
        }

        // Agrupar en filas de máximo 3 características
        let html = '<div class="mb-3"><small class="fw-bold text-danger d-block mb-2"><i class="fa fa-check-circle"></i> Características:</small>';
        html += '<div class="row g-1">';

        features.slice(0, 6).forEach(feature => {
            html += `
                <div class="col-6">
                    <small class="d-flex align-items-center">
                        <i class="fa ${feature.icon} text-${feature.color} me-1" style="width: 14px;"></i>
                        <span class="text-muted">${feature.text}</span>
                    </small>
                </div>
            `;
        });

        if (features.length > 6) {
            html += `
                <div class="col-12">
                    <small class="text-muted fst-italic">+ ${features.length - 6} más características</small>
                </div>
            `;
        }

        html += '</div></div>';
        return html;
    }

    updateCounter(count) {
        const counter = document.getElementById('property-count');
        if (counter) {
            counter.textContent = count;
        }

        const showing = document.getElementById('showing-count');
        if (showing) {
            showing.textContent = count;
        }
    }

    formatPrice(price) {
        return new Intl.NumberFormat('es-CO').format(price);
    }

    // =================== MAPA ===================

    initMap() {
        const mapContainer = document.getElementById('properties-map');
        if (!mapContainer) return;

        // Esperar a que Leaflet esté disponible
        const checkLeaflet = setInterval(() => {
            if (typeof L !== 'undefined') {
                clearInterval(checkLeaflet);
                this.createMap();
            }
        }, 100);
    }

    createMap() {
        const mapContainer = document.getElementById('properties-map');
        if (!mapContainer || this.map) return;

        try {
            // Crear mapa centrado en Barranquilla
            this.map = L.map('properties-map').setView([10.9685, -74.7813], 12);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(this.map);

            this.markers = L.layerGroup().addTo(this.map);

            // Cuando se muestra el tab del mapa, actualizar tamaño
            const mapTab = document.querySelector('[data-bs-target="#map-view"]');
            if (mapTab) {
                mapTab.addEventListener('shown.bs.tab', () => {
                    setTimeout(() => {
                        this.map.invalidateSize();
                        this.updateMap(this.currentProperties);
                    }, 100);
                });
            }

            console.log('Mapa creado correctamente');
        } catch (error) {
            console.error('Error creando mapa:', error);
        }
    }

    updateMap(properties) {
        if (!this.map || !this.markers) return;

        this.markers.clearLayers();

        const bounds = [];

        properties.forEach(prop => {
            if (prop.latitude && prop.longitude) {
                // Pin personalizado con precio
                const customIcon = L.divIcon({
                    className: 'custom-property-pin',
                    html: `
                        <div class="map-pin">
                            <div class="pin-price">$${this.formatPrice(prop.list_price)}</div>
                            <div class="pin-arrow"></div>
                        </div>
                    `,
                    iconSize: [120, 50],
                    iconAnchor: [60, 50]
                });

                const marker = L.marker([prop.latitude, prop.longitude], { icon: customIcon });

                marker.bindPopup(`
                    <div class="property-popup">
                        <h6><a href="/property/${prop.id}">${prop.name}</a></h6>
                        <p class="mb-1"><strong>$${this.formatPrice(prop.list_price)}</strong></p>
                        <p class="small text-muted mb-2">${prop.city || ''}, ${prop.region || ''}</p>
                        <a href="/property/${prop.id}" class="btn btn-sm btn-danger w-100">Ver Detalles</a>
                    </div>
                `);

                this.markers.addLayer(marker);
                bounds.push([prop.latitude, prop.longitude]);
            }
        });

        if (bounds.length > 0) {
            this.map.fitBounds(bounds, { padding: [50, 50] });
        }
    }

    // =================== COMPARACIÓN ===================

    initComparison() {
        // Cargar del localStorage
        const saved = localStorage.getItem('bohio_comparison');
        if (saved) {
            this.comparisonList = JSON.parse(saved);
            this.updateComparisonBadge();
        }

        // Botón ver comparación
        const viewButton = document.querySelector('.view-comparison');
        if (viewButton) {
            viewButton.addEventListener('click', () => {
                this.showComparisonModal();
            });
        }

        // Limpiar comparación
        document.addEventListener('click', (e) => {
            if (e.target.closest('.clear-comparison')) {
                this.clearComparison();
            }
        });

        // Agregar listeners para cerrar modal manualmente
        this.initModalCloseListeners();
    }

    initModalCloseListeners() {
        const modal = document.getElementById('comparisonModal');
        if (!modal) return;

        // Botones con data-bs-dismiss
        modal.querySelectorAll('[data-bs-dismiss="modal"]').forEach(btn => {
            btn.addEventListener('click', () => {
                this.closeModal(modal);
            });
        });

        // Click en backdrop
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeModal(modal);
            }
        });
    }

    closeModal(modalElement) {
        modalElement.style.display = 'none';
        modalElement.classList.remove('show');
        document.body.classList.remove('modal-open');

        // Remover backdrop
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
    }

    attachComparisonListeners() {
        document.querySelectorAll('.add-to-comparison').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const propertyId = parseInt(btn.dataset.propertyId);
                this.toggleComparison(propertyId);
            });
        });
    }

    attachCRMListeners() {
        document.querySelectorAll('.add-to-crm').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                e.stopPropagation();
                const propertyId = parseInt(btn.dataset.propertyId);
                await this.addPropertyToCRM(propertyId);
            });
        });
    }

    async addPropertyToCRM(propertyId) {
        try {
            // Obtener información de la propiedad
            const property = this.currentProperties.find(p => p.id === propertyId);
            if (!property) {
                console.error('Propiedad no encontrada');
                return;
            }

            // Crear oportunidad en CRM
            const response = await fetch('/bohio/api/crm/add_property', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    property_id: propertyId,
                    property_name: property.name
                })
            });

            const result = await response.json();

            if (result.success || result.result?.success) {
                this.showNotification('Propiedad agregada al CRM exitosamente', 'success');
            } else {
                this.showNotification(result.message || 'Error al agregar propiedad al CRM', 'error');
            }
        } catch (error) {
            console.error('Error agregando propiedad al CRM:', error);
            this.showNotification('Error al agregar propiedad al CRM', 'error');
        }
    }

    showNotification(message, type = 'info') {
        // Crear notificación con estilo BOHIO
        const notification = document.createElement('div');
        notification.className = 'bohio-notification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'success' ? '#E31E24' : '#dc3545'};
            color: white;
            border-radius: 5px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
        `;
        notification.innerHTML = `
            <i class="fa ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}" style="margin-right: 10px;"></i>
            ${message}
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    toggleComparison(propertyId) {
        const index = this.comparisonList.indexOf(propertyId);

        if (index > -1) {
            this.comparisonList.splice(index, 1);
        } else {
            if (this.comparisonList.length >= 4) {
                alert('Máximo 4 propiedades para comparar');
                return;
            }
            this.comparisonList.push(propertyId);
        }

        localStorage.setItem('bohio_comparison', JSON.stringify(this.comparisonList));
        this.updateComparisonBadge();
        this.renderProperties(this.currentProperties);
    }

    updateComparisonBadge() {
        const badge = document.querySelector('.comparison-badge');
        const button = document.querySelector('.view-comparison');

        if (badge && button) {
            if (this.comparisonList.length > 0) {
                badge.textContent = this.comparisonList.length;
                badge.style.display = 'inline-block';
                button.disabled = false;
            } else {
                badge.style.display = 'none';
                button.disabled = true;
            }
        }
    }

    async showComparisonModal() {
        if (this.comparisonList.length === 0) return;

        try {
            console.log('Solicitando comparación con IDs:', this.comparisonList);
            const response = await fetch('/property/comparison/get', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    property_ids: this.comparisonList,
                    context: this.context
                })
            });
            const data = await response.json();
            console.log('Datos de comparación recibidos:', data);

            this.renderComparisonModal(data);
        } catch (error) {
            console.error('Error obteniendo comparación:', error);
        }
    }

    renderComparisonModal(data) {
        const content = document.getElementById('comparison-content');
        if (!content) return;

        // Validar datos
        const properties = data?.properties || data?.result?.properties || [];

        if (!Array.isArray(properties) || properties.length === 0) {
            content.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fa fa-exclamation-triangle"></i> No hay propiedades para comparar o error al cargar los datos.
                </div>
            `;
            // Mostrar modal con fallback
            const modalEl = document.getElementById('comparisonModal');
            if (modalEl) {
                if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                    new bootstrap.Modal(modalEl).show();
                } else if (typeof $ !== 'undefined' && $.fn.modal) {
                    $(modalEl).modal('show');
                } else {
                    modalEl.style.display = 'block';
                    modalEl.classList.add('show');
                    document.body.classList.add('modal-open');
                    const backdrop = document.createElement('div');
                    backdrop.className = 'modal-backdrop fade show';
                    document.body.appendChild(backdrop);
                }
            }
            return;
        }

        // Renderizar tabla de comparación
        let html = '<div class="table-responsive"><table class="table table-bordered">';

        // Headers con imágenes
        html += '<thead><tr><th>Característica</th>';
        properties.forEach(prop => {
            const imageUrl = prop.image_url || '/theme_bohio_real_estate/static/src/img/banner1.jpg';
            html += `<th class="text-center">
                <img src="${imageUrl}" style="width: 100px; height: 100px; object-fit: cover;" class="rounded mb-2"/>
                <div class="small">${prop.name || 'Sin nombre'}</div>
            </th>`;
        });
        html += '</tr></thead><tbody>';

        // Comparar campos
        const fields = ['list_price', 'property_type_name', 'bedrooms', 'bathrooms', 'area_constructed', 'city', 'stratum'];
        fields.forEach(field => {
            html += '<tr><td><strong>' + this.getFieldLabel(field) + '</strong></td>';
            properties.forEach(prop => {
                html += `<td class="text-center">${this.getFieldValue(prop, field)}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table></div>';
        content.innerHTML = html;

        // Mostrar modal - usar jQuery si Bootstrap 5 no está disponible
        const modalElement = document.getElementById('comparisonModal');
        if (modalElement) {
            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
            } else if (typeof $ !== 'undefined' && $.fn.modal) {
                $(modalElement).modal('show');
            } else {
                // Fallback: mostrar con display
                modalElement.style.display = 'block';
                modalElement.classList.add('show');
                document.body.classList.add('modal-open');

                // Crear backdrop
                const backdrop = document.createElement('div');
                backdrop.className = 'modal-backdrop fade show';
                document.body.appendChild(backdrop);

                // Cerrar al hacer click en backdrop
                backdrop.addEventListener('click', () => {
                    modalElement.style.display = 'none';
                    modalElement.classList.remove('show');
                    document.body.classList.remove('modal-open');
                    backdrop.remove();
                });
            }
        }
    }

    getFieldLabel(field) {
        const labels = {
            list_price: 'Precio',
            property_type: 'Tipo',
            property_type_name: 'Tipo de Propiedad',
            bedrooms: 'Habitaciones',
            bathrooms: 'Baños',
            area_constructed: 'Área Construida',
            city: 'Ciudad',
            stratum: 'Estrato'
        };
        return labels[field] || field;
    }

    getFieldValue(property, field) {
        if (field === 'list_price') {
            return '$' + this.formatPrice(property[field]);
        }
        return property[field] || 'N/A';
    }

    clearComparison() {
        this.comparisonList = [];
        localStorage.removeItem('bohio_comparison');
        this.updateComparisonBadge();
        this.renderProperties(this.currentProperties);
    }
    // =================== PAGINACIÓN ===================

    renderPagination() {
        const container = document.getElementById('paginationContainer');
        if (!container || this.totalPages <= 1) {
            if (container) container.innerHTML = '';
            return;
        }

        const maxButtons = 5;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxButtons / 2));
        let endPage = Math.min(this.totalPages, startPage + maxButtons - 1);

        if (endPage - startPage < maxButtons - 1) {
            startPage = Math.max(1, endPage - maxButtons + 1);
        }

        let html = '<nav aria-label="Paginación de propiedades"><ul class="pagination justify-content-center mb-0">';

        // Botón Anterior
        html += `
            <li class="page-item ${this.currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${this.currentPage - 1}" aria-label="Anterior">
                    <span aria-hidden="true">&laquo;</span>
                </a>
            </li>
        `;

        // Primera página si no está visible
        if (startPage > 1) {
            html += `<li class="page-item"><a class="page-link" href="#" data-page="1">1</a></li>`;
            if (startPage > 2) {
                html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }

        // Páginas numeradas
        for (let i = startPage; i <= endPage; i++) {
            html += `
                <li class="page-item ${i === this.currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `;
        }

        // Última página si no está visible
        if (endPage < this.totalPages) {
            if (endPage < this.totalPages - 1) {
                html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
            html += `<li class="page-item"><a class="page-link" href="#" data-page="${this.totalPages}">${this.totalPages}</a></li>`;
        }

        // Botón Siguiente
        html += `
            <li class="page-item ${this.currentPage === this.totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${this.currentPage + 1}" aria-label="Siguiente">
                    <span aria-hidden="true">&raquo;</span>
                </a>
            </li>
        `;

        html += '</ul></nav>';

        // Info de resultados
        const start = ((this.currentPage - 1) * this.itemsPerPage) + 1;
        const end = Math.min(this.currentPage * this.itemsPerPage, this.totalItems);
        html += `
            <div class="text-center mt-3 text-muted small">
                Mostrando ${start} a ${end} de ${this.totalItems} propiedades
            </div>
        `;

        container.innerHTML = html;

        // Event listeners
        container.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(e.currentTarget.dataset.page);
                if (page && page !== this.currentPage && page >= 1 && page <= this.totalPages) {
                    this.goToPage(page);
                }
            });
        });
    }

    goToPage(page) {
        this.currentPage = page;
        this.loadProperties();

        // Scroll suave a la parte superior de los resultados
        const resultsContainer = document.querySelector('.property-results-grid');
        if (resultsContainer) {
            resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (document.querySelector('.property_search_container')) {
            window.bohioShop = new PropertyShop();
        }
    });
} else {
    if (document.querySelector('.property_search_container')) {
        window.bohioShop = new PropertyShop();
    }
}

export default PropertyShop;

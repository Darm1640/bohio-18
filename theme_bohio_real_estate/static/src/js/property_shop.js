/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

console.log('BOHIO Property Shop JS cargado');

// Ubicación de la oficina principal de BOHIO
const BOHIO_OFFICE = {
    name: 'Bohío Consultores Soluciones Inmobiliarias SAS',
    address: 'Cl. 29 #2, Esquina, Centro, Montería, Córdoba',
    latitude: 8.7479,  // Coordenadas de Montería, Córdoba
    longitude: -75.8814,
    phone: '+57 321 740 3356',
    email: 'info@bohio.com.co',
    website: 'bohioconsultores.com',
    hours: 'Lun - Vie: 7:30 AM - 6:00 PM'
};

// Lugares de interés cerca de la oficina en Montería
const NEARBY_PLACES = [
    {
        name: 'Plaza de la Concepción',
        type: 'landmark',
        latitude: 8.7496,
        longitude: -75.8840,
        icon: 'fa-landmark',
        color: '#FF9800'
    },
    {
        name: 'Ronda del Sinú',
        type: 'park',
        latitude: 8.7586,
        longitude: -75.8899,
        icon: 'fa-tree',
        color: '#4CAF50'
    },
    {
        name: 'Centro Comercial Nuestro',
        type: 'shopping',
        latitude: 8.7450,
        longitude: -75.8743,
        icon: 'fa-shopping-cart',
        color: '#2196F3'
    },
    {
        name: 'Universidad de Córdoba',
        type: 'education',
        latitude: 8.7851,
        longitude: -75.8646,
        icon: 'fa-graduation-cap',
        color: '#9C27B0'
    }
];

class PropertyShop {
    constructor() {
        this.context = 'public';
        this.filters = {};
        this.comparisonList = [];
        this.map = null;
        this.markers = null;
        this.officeMarker = null;  // Marker especial para la oficina
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
        if (!searchInput) {
            console.warn('[AUTOCOMPLETE] Property search input NOT FOUND');
            return;
        }

        console.log('[AUTOCOMPLETE] Property search input encontrado, agregando listeners...');

        searchInput.addEventListener('input', (e) => {
            clearTimeout(this.autocompleteTimeout);
            const term = e.target.value.trim();

            console.log('[AUTOCOMPLETE] Busqueda input:', term);

            if (term.length < 2) {
                this.hideAutocomplete();
                return;
            }

            this.autocompleteTimeout = setTimeout(() => {
                console.log('[AUTOCOMPLETE] Ejecutando autocomplete para:', term);
                this.performAutocomplete(term);
            }, 300);
        });
    }

    async performAutocomplete(term) {
        const subdivision = document.querySelector('.subdivision-filter')?.value || 'all';

        console.log('[AUTOCOMPLETE] Llamando autocompletado:', {
            url: '/property/search/autocomplete/' + this.context,
            term: term,
            subdivision: subdivision
        });

        try {
            const result = await rpc('/property/search/autocomplete/' + this.context, {
                term: term,
                subdivision: subdivision,
                limit: 10
            });

            console.log('[AUTOCOMPLETE] Resultado autocompletado:', result);

            if (result.success) {
                this.renderAutocompleteResults(result.results || []);
            } else {
                console.error('[AUTOCOMPLETE] Autocomplete fallo:', result);
            }
        } catch (error) {
            console.error('[AUTOCOMPLETE] Error en autocompletado:', error);
        }
    }

    renderAutocompleteResults(results) {
        const container = document.querySelector('.autocomplete-container');
        if (!container) {
            console.warn('[AUTOCOMPLETE] Autocomplete container NOT FOUND');
            return;
        }

        console.log('[AUTOCOMPLETE] Renderizando resultados:', results.length, 'items');

        if (results.length === 0) {
            container.innerHTML = '<div class="p-3 text-muted">No se encontraron resultados</div>';
            container.style.display = 'block';
            return;
        }

        let html = '<ul class="list-unstyled mb-0">';
        results.forEach(result => {
            // Extraer ID numérico basado en el tipo
            let numericId = '';
            if (result.city_id) numericId = result.city_id;
            else if (result.region_id) numericId = result.region_id;
            else if (result.project_id) numericId = result.project_id;
            else if (result.property_id) numericId = result.property_id;

            // Determinar ícono según tipo
            let iconClass = 'fa-map-marker-alt';
            let iconType = 'city';
            if (result.type === 'city') {
                iconClass = 'fa-map-marker-alt';
                iconType = 'city';
            } else if (result.type === 'region') {
                iconClass = 'fa-home';
                iconType = 'region';
            } else if (result.type === 'project') {
                iconClass = 'fa-building';
                iconType = 'project';
            } else if (result.type === 'property') {
                iconClass = 'fa-key';
                iconType = 'property';
            }

            html += `
                <li class="autocomplete-item"
                    data-type="${result.type}"
                    data-id="${numericId}"
                    data-city-id="${result.city_id || ''}"
                    data-region-id="${result.region_id || ''}"
                    data-project-id="${result.project_id || ''}"
                    data-property-id="${result.property_id || ''}">
                    <div class="autocomplete-item-icon ${iconType}">
                        <i class="fa ${iconClass}"></i>
                    </div>
                    <div class="autocomplete-item-content">
                        <span class="autocomplete-item-title">${result.name}</span>
                        <span class="autocomplete-item-subtitle">${result.full_name || ''}</span>
                    </div>
                    <span class="autocomplete-item-badge">${result.property_count}</span>
                </li>
            `;
        });
        html += '</ul>';

        container.innerHTML = html;
        container.style.display = 'block';

        console.log('[AUTOCOMPLETE] Autocomplete renderizado y visible');

        // Event listeners para items
        container.querySelectorAll('.autocomplete-item').forEach(item => {
            item.addEventListener('click', () => {
                this.selectAutocompleteItem(item.dataset);
            });
        });
    }

    selectAutocompleteItem(data) {
        console.log('[AUTOCOMPLETE] Item seleccionado:', data);

        // Agregar filtro según el tipo seleccionado usando los IDs específicos
        if (data.type === 'city' && data.cityId) {
            this.filters.city_id = data.cityId;
            console.log('[FILTER] Filtro ciudad agregado:', data.cityId);
        } else if (data.type === 'region' && data.regionId) {
            this.filters.region_id = data.regionId;
            console.log('[FILTER] Filtro region agregado:', data.regionId);
        } else if (data.type === 'project' && data.projectId) {
            this.filters.project_id = data.projectId;
            console.log('[FILTER] Filtro proyecto agregado:', data.projectId);
        } else if (data.type === 'property' && data.propertyId) {
            window.location.href = `/property/${data.propertyId}`;
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
            <div class="col-lg-3 col-md-6 mb-4 d-flex justify-content-center">
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

                // Popup mejorado con imagen y detalles
                const imageUrl = prop.image_url || '/theme_bohio_real_estate/static/src/img/placeholder.jpg';
                const bedrooms = prop.bedrooms || 0;
                const bathrooms = prop.bathrooms || 0;
                const area = prop.total_area || prop.built_area || 0;
                const neighborhood = prop.neighborhood || prop.region || '';

                marker.bindPopup(`
                    <div class="property-popup-card" style="min-width: 280px;">
                        <div class="popup-image" style="height: 160px; overflow: hidden; border-radius: 8px 8px 0 0; margin: -12px -12px 12px -12px;">
                            <img src="${imageUrl}"
                                 alt="${prop.name}"
                                 style="width: 100%; height: 100%; object-fit: cover;"
                                 onerror="this.src='/theme_bohio_real_estate/static/src/img/placeholder.jpg'"/>
                        </div>
                        <div class="popup-content">
                            <h6 class="mb-2" style="font-size: 14px; font-weight: 600;">
                                <a href="/property/${prop.id}" class="text-dark text-decoration-none">
                                    ${prop.name}
                                </a>
                            </h6>
                            ${neighborhood ? `<p class="small text-muted mb-2"><i class="fa fa-map-marker-alt me-1"></i>${neighborhood}</p>` : ''}
                            <p class="mb-2" style="font-size: 16px; color: #e31e24; font-weight: 700;">
                                $${this.formatPrice(prop.list_price)}
                            </p>
                            <div class="d-flex gap-3 mb-3" style="font-size: 13px; color: #666;">
                                ${area > 0 ? `<span><i class="fa fa-ruler-combined me-1"></i>${area} m²</span>` : ''}
                                ${bedrooms > 0 ? `<span><i class="fa fa-bed me-1"></i>${bedrooms}</span>` : ''}
                                ${bathrooms > 0 ? `<span><i class="fa fa-bath me-1"></i>${bathrooms}</span>` : ''}
                            </div>
                            <a href="/property/${prop.id}" class="btn btn-sm btn-danger w-100">Ver Detalles</a>
                        </div>
                    </div>
                `, {
                    maxWidth: 300,
                    className: 'custom-popup'
                });

                this.markers.addLayer(marker);
                bounds.push([prop.latitude, prop.longitude]);
            }
        });

        // Agregar pin especial de la oficina de BOHIO
        this.addOfficeMarker();

        if (bounds.length > 0) {
            this.map.fitBounds(bounds, { padding: [50, 50] });
        }
    }

    addOfficeMarker() {
        if (!this.map) return;

        // Remover marker anterior si existe
        if (this.officeMarker) {
            this.map.removeLayer(this.officeMarker);
        }

        // Icono especial para la oficina (rojo con icono de edificio)
        const officeIcon = L.divIcon({
            className: 'bohio-office-marker',
            html: `
                <div style="position: relative;">
                    <div style="
                        background: linear-gradient(135deg, #e31e24 0%, #c01d20 100%);
                        color: white;
                        padding: 12px 16px;
                        border-radius: 25px;
                        box-shadow: 0 4px 15px rgba(227, 30, 36, 0.4);
                        font-weight: bold;
                        font-size: 13px;
                        white-space: nowrap;
                        border: 3px solid white;
                        animation: pulse-office 2s infinite;
                    ">
                        <i class="fa fa-building me-2"></i>OFICINA BOHIO
                    </div>
                    <div style="
                        position: absolute;
                        bottom: -10px;
                        left: 50%;
                        transform: translateX(-50%);
                        width: 0;
                        height: 0;
                        border-left: 10px solid transparent;
                        border-right: 10px solid transparent;
                        border-top: 10px solid white;
                    "></div>
                </div>
            `,
            iconSize: [180, 50],
            iconAnchor: [90, 50]
        });

        // Crear marker de la oficina
        this.officeMarker = L.marker([BOHIO_OFFICE.latitude, BOHIO_OFFICE.longitude], {
            icon: officeIcon,
            zIndexOffset: 1000  // Siempre al frente
        }).addTo(this.map);

        // Popup especial para la oficina con botón de Google Maps
        const googleMapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${BOHIO_OFFICE.latitude},${BOHIO_OFFICE.longitude}`;

        const officePopup = `
            <div class="bohio-office-popup" style="min-width: 300px;">
                <div style="background: linear-gradient(135deg, #e31e24 0%, #c01d20 100%); color: white; padding: 15px; margin: -12px -12px 15px -12px; border-radius: 8px 8px 0 0;">
                    <h5 class="mb-1" style="font-size: 16px; font-weight: bold;">
                        <i class="fa fa-building me-2"></i>${BOHIO_OFFICE.name}
                    </h5>
                </div>
                <div style="padding: 0 5px;">
                    <p class="mb-2" style="font-size: 14px;">
                        <i class="fa fa-map-marker-alt me-2" style="color: #e31e24;"></i>
                        <strong>${BOHIO_OFFICE.address}</strong>
                    </p>
                    <p class="mb-2" style="font-size: 13px;">
                        <i class="fa fa-phone me-2" style="color: #e31e24;"></i>
                        <a href="tel:${BOHIO_OFFICE.phone}" class="text-dark">${BOHIO_OFFICE.phone}</a>
                    </p>
                    <p class="mb-2" style="font-size: 13px;">
                        <i class="fa fa-envelope me-2" style="color: #e31e24;"></i>
                        <a href="mailto:${BOHIO_OFFICE.email}" class="text-dark">${BOHIO_OFFICE.email}</a>
                    </p>
                    <p class="mb-2" style="font-size: 12px; color: #666;">
                        <i class="fa fa-clock me-2" style="color: #e31e24;"></i>
                        ${BOHIO_OFFICE.hours}
                    </p>
                    <p class="mb-3" style="font-size: 13px;">
                        <i class="fa fa-globe me-2" style="color: #e31e24;"></i>
                        <a href="https://${BOHIO_OFFICE.website}" target="_blank" class="text-dark">
                            ${BOHIO_OFFICE.website}
                        </a>
                    </p>
                    <a href="${googleMapsUrl}"
                       target="_blank"
                       class="btn btn-danger w-100 mb-2"
                       style="background: #e31e24; border: none;">
                        <i class="fa fa-map-marked-alt me-2"></i>Cómo llegar (Google Maps)
                    </a>
                    <a href="tel:${BOHIO_OFFICE.phone}"
                       class="btn btn-outline-danger w-100"
                       style="border-color: #e31e24; color: #e31e24;">
                        <i class="fa fa-phone me-2"></i>Llamar ahora
                    </a>
                </div>
            </div>
        `;

        this.officeMarker.bindPopup(officePopup, {
            maxWidth: 350,
            className: 'bohio-office-popup-container'
        });

        // Agregar lugares de interés cercanos
        this.addNearbyPlaces();

        // Auto-abrir el popup de la oficina brevemente al cargar el mapa
        setTimeout(() => {
            this.officeMarker.openPopup();
            setTimeout(() => {
                this.officeMarker.closePopup();
            }, 3000);  // Cerrar después de 3 segundos
        }, 1000);
    }

    addNearbyPlaces() {
        if (!this.map) return;

        NEARBY_PLACES.forEach(place => {
            // Icono pequeño para lugares de interés
            const placeIcon = L.divIcon({
                className: 'nearby-place-marker',
                html: `
                    <div style="
                        background: ${place.color};
                        color: white;
                        width: 32px;
                        height: 32px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                        border: 2px solid white;
                        font-size: 14px;
                    ">
                        <i class="fa ${place.icon}"></i>
                    </div>
                `,
                iconSize: [32, 32],
                iconAnchor: [16, 16]
            });

            const marker = L.marker([place.latitude, place.longitude], {
                icon: placeIcon,
                zIndexOffset: 500
            }).addTo(this.map);

            // Popup para el lugar de interés
            const placePopup = `
                <div style="min-width: 200px; text-align: center;">
                    <div style="color: ${place.color}; font-size: 24px; margin-bottom: 8px;">
                        <i class="fa ${place.icon}"></i>
                    </div>
                    <h6 class="mb-2" style="font-weight: 600;">${place.name}</h6>
                    <a href="https://www.google.com/maps/dir/?api=1&origin=${BOHIO_OFFICE.latitude},${BOHIO_OFFICE.longitude}&destination=${place.latitude},${place.longitude}"
                       target="_blank"
                       class="btn btn-sm btn-outline-secondary"
                       style="border-color: ${place.color}; color: ${place.color};">
                        <i class="fa fa-directions me-1"></i>Cómo llegar
                    </a>
                </div>
            `;

            marker.bindPopup(placePopup, {
                maxWidth: 250,
                className: 'nearby-place-popup'
            });
        });
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

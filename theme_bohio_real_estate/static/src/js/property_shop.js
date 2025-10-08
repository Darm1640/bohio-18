/** @odoo-module **/

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

        this.init();
    }

    init() {
        console.log('Inicializando Property Shop...');

        // Obtener contexto
        const container = document.querySelector('.property_search_container');
        if (container) {
            this.context = container.dataset.context || 'public';
        }

        // Inicializar componentes
        this.initSearch();
        this.initFilters();
        this.initComparison();
        this.initMap();

        // Cargar propiedades iniciales
        this.loadProperties();
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
            const response = await fetch('/property/search/autocomplete/' + this.context, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    term: term,
                    subdivision: subdivision,
                    limit: 10
                })
            });
            const result = await response.json();

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
            const response = await fetch('/bohio/api/properties', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ...this.filters,
                    context: this.context,
                    limit: 50
                })
            });
            const data = await response.json();

            this.currentProperties = data.items || [];
            this.renderProperties(this.currentProperties);
            this.updateMap(this.currentProperties);
            this.updateCounter(this.currentProperties.length);
        } catch (error) {
            console.error('Error cargando propiedades:', error);
            gridContainer.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fa fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                    <p class="text-muted">Error al cargar propiedades</p>
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

        // Re-attach event listeners para comparación
        this.attachComparisonListeners();
    }

    renderPropertyCard(property) {
        const imageUrl = property.image_url || '/theme_bohio_real_estate/static/src/img/home-banner.jpg';
        const price = this.formatPrice(property.list_price);
        const isInComparison = this.comparisonList.includes(property.id);

        return `
            <div class="col-lg-4 col-md-6">
                <div class="card property-card shadow-sm h-100">
                    <div class="position-relative">
                        <img src="${imageUrl}" class="card-img-top" alt="${property.name}" style="height: 250px; object-fit: cover;"/>
                        <div class="position-absolute top-0 end-0 m-3">
                            <span class="badge bg-danger px-3 py-2">$${price}</span>
                        </div>
                        <div class="position-absolute top-0 start-0 m-3">
                            ${property.type_service === 'rent' ? '<span class="badge bg-primary me-1">Arriendo</span>' : ''}
                            ${property.type_service === 'sale' ? '<span class="badge bg-success me-1">Venta</span>' : ''}
                            ${property.is_new ? '<span class="badge bg-warning">NUEVO</span>' : ''}
                        </div>
                        <button class="btn btn-sm ${isInComparison ? 'btn-warning' : 'btn-outline-light'} position-absolute bottom-0 end-0 m-3 add-to-comparison"
                                data-property-id="${property.id}">
                            <i class="fa fa-balance-scale"></i>
                        </button>
                    </div>
                    <div class="card-body">
                        <h5 class="card-title mb-2">
                            <a href="/property/${property.id}" class="text-decoration-none text-dark">
                                ${property.name.substring(0, 50)}
                            </a>
                        </h5>
                        <p class="text-muted small mb-3">
                            <i class="fa fa-map-marker-alt me-1"></i>
                            ${property.city || ''}, ${property.region || ''}
                        </p>
                        ${this.renderFeatures(property)}
                        <div class="mb-3">
                            <small class="text-muted">Código: <strong>${property.default_code || 'N/A'}</strong></small>
                        </div>
                        <a href="/property/${property.id}" class="btn btn-outline-danger w-100">Ver Detalles</a>
                    </div>
                </div>
            </div>
        `;
    }

    renderFeatures(property) {
        if (!['apartment', 'house'].includes(property.property_type)) {
            return `
                <div class="d-flex justify-content-between mb-3 pb-3 border-bottom">
                    <span class="text-muted small">
                        <img src="/theme_bohio_real_estate/static/src/img/areas_1-8.png" style="width: 20px; height: 20px;" alt="Área"/>
                        <strong>${property.area_total || 0}</strong> m²
                    </span>
                </div>
            `;
        }

        return `
            <div class="d-flex justify-content-between mb-3 pb-3 border-bottom">
                <span class="text-muted small">
                    <img src="/theme_bohio_real_estate/static/src/img/habitacion-8.png" style="width: 20px; height: 20px;" alt="Hab"/>
                    <strong>${property.bedrooms || 0}</strong>
                </span>
                <span class="text-muted small">
                    <img src="/theme_bohio_real_estate/static/src/img/baño_1-8.png" style="width: 20px; height: 20px;" alt="Baños"/>
                    <strong>${property.bathrooms || 0}</strong>
                </span>
                <span class="text-muted small">
                    <img src="/theme_bohio_real_estate/static/src/img/areas_1-8.png" style="width: 20px; height: 20px;" alt="Área"/>
                    <strong>${property.area_constructed || 0}</strong> m²
                </span>
            </div>
        `;
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

            this.renderComparisonModal(data);
        } catch (error) {
            console.error('Error obteniendo comparación:', error);
        }
    }

    renderComparisonModal(data) {
        const content = document.getElementById('comparison-content');
        if (!content) return;

        // Renderizar tabla de comparación
        let html = '<div class="table-responsive"><table class="table table-bordered">';

        // Headers con imágenes
        html += '<thead><tr><th>Característica</th>';
        data.properties.forEach(prop => {
            html += `<th class="text-center">
                <img src="${prop.image_url}" style="width: 100px; height: 100px; object-fit: cover;" class="rounded mb-2"/>
                <div>${prop.name}</div>
            </th>`;
        });
        html += '</tr></thead><tbody>';

        // Comparar campos
        const fields = ['list_price', 'property_type', 'bedrooms', 'bathrooms', 'area_constructed'];
        fields.forEach(field => {
            html += '<tr><td><strong>' + this.getFieldLabel(field) + '</strong></td>';
            data.properties.forEach(prop => {
                html += `<td class="text-center">${this.getFieldValue(prop, field)}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table></div>';
        content.innerHTML = html;

        // Mostrar modal
        const modal = new bootstrap.Modal(document.getElementById('comparisonModal'));
        modal.show();
    }

    getFieldLabel(field) {
        const labels = {
            list_price: 'Precio',
            property_type: 'Tipo',
            bedrooms: 'Habitaciones',
            bathrooms: 'Baños',
            area_constructed: 'Área'
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

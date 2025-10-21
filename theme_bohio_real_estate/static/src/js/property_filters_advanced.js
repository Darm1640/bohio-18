/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

/**
 * BOHIO Advanced Property Filters - Sistema de Filtros Agrupados
 *
 * Características:
 * - Filtros por rangos (precio, área, habitaciones, baños, parqueaderos)
 * - Filtros por características agrupadas (áreas exteriores, amenidades, seguridad)
 * - Contadores en tiempo real por cada filtro
 * - Conversión automática de unidades de medida
 * - Multi-moneda
 *
 * Uso:
 * const filters = new AdvancedPropertyFilters(containerElement);
 * filters.init();
 */

export class AdvancedPropertyFilters {
    constructor(container) {
        this.container = container;
        this.filters = {
            price_range: null,
            rental_price_range: null,
            bedrooms_range: null,
            bathrooms_range: null,
            parking_range: null,
            area_range: null,
            property_type: null,
            type_service: null,
            has_outdoor_areas: false,
            has_building_amenities: false,
            has_luxury_amenities: false,
            has_full_security: false,
        };
        this.ranges = {};
        this.properties = [];
        this.total = 0;
        this.callbacks = {
            onFilterChange: null,
            onPropertiesLoaded: null,
        };
    }

    /**
     * Inicializar sistema de filtros
     */
    async init() {
        try {
            await this.loadRanges();
            this.renderFilters();
            this.attachEventListeners();
        } catch (error) {
            console.error('Error initializing advanced filters:', error);
        }
    }

    /**
     * Cargar rangos disponibles con contadores
     */
    async loadRanges() {
        try {
            const result = await rpc('/api/property/filters/ranges', {});

            if (result.success) {
                this.ranges = {
                    price_ranges: result.price_ranges,
                    rental_ranges: result.rental_ranges,
                    bedroom_ranges: result.bedroom_ranges,
                    bathroom_ranges: result.bathroom_ranges,
                    parking_ranges: result.parking_ranges,
                    area_ranges: result.area_ranges,
                    grouped_characteristics: result.grouped_characteristics,
                };
            } else {
                console.error('Error loading ranges:', result.error);
            }
        } catch (error) {
            console.error('Error in loadRanges:', error);
        }
    }

    /**
     * Renderizar filtros en el DOM
     */
    renderFilters() {
        if (!this.container) return;

        const html = `
            <div class="advanced-filters-container">

                <!-- FILTROS DE PRECIO -->
                <div class="filter-section">
                    <h5 class="filter-section-title" data-bs-toggle="collapse" data-bs-target="#priceFilters">
                        <i class="bi bi-currency-dollar me-2"></i>
                        Rango de Precio
                        <i class="bi bi-chevron-down float-end"></i>
                    </h5>
                    <div class="collapse show" id="priceFilters">
                        <div class="filter-options">
                            ${this.renderPriceRangeOptions()}
                        </div>
                    </div>
                </div>

                <!-- FILTROS DE HABITACIONES -->
                <div class="filter-section">
                    <h5 class="filter-section-title" data-bs-toggle="collapse" data-bs-target="#bedroomFilters">
                        <i class="bi bi-house-door me-2"></i>
                        Habitaciones
                        <i class="bi bi-chevron-down float-end"></i>
                    </h5>
                    <div class="collapse show" id="bedroomFilters">
                        <div class="filter-options">
                            ${this.renderBedroomOptions()}
                        </div>
                    </div>
                </div>

                <!-- FILTROS DE BAÑOS -->
                <div class="filter-section">
                    <h5 class="filter-section-title" data-bs-toggle="collapse" data-bs-target="#bathroomFilters">
                        <i class="bi bi-droplet me-2"></i>
                        Baños
                        <i class="bi bi-chevron-down float-end"></i>
                    </h5>
                    <div class="collapse show" id="bathroomFilters">
                        <div class="filter-options">
                            ${this.renderBathroomOptions()}
                        </div>
                    </div>
                </div>

                <!-- FILTROS DE PARQUEADEROS -->
                <div class="filter-section">
                    <h5 class="filter-section-title" data-bs-toggle="collapse" data-bs-target="#parkingFilters">
                        <i class="bi bi-car-front me-2"></i>
                        Parqueaderos
                        <i class="bi bi-chevron-down float-end"></i>
                    </h5>
                    <div class="collapse" id="parkingFilters">
                        <div class="filter-options">
                            ${this.renderParkingOptions()}
                        </div>
                    </div>
                </div>

                <!-- FILTROS DE ÁREA -->
                <div class="filter-section">
                    <h5 class="filter-section-title" data-bs-toggle="collapse" data-bs-target="#areaFilters">
                        <i class="bi bi-arrows-fullscreen me-2"></i>
                        Área
                        <i class="bi bi-chevron-down float-end"></i>
                    </h5>
                    <div class="collapse" id="areaFilters">
                        <div class="filter-options">
                            ${this.renderAreaOptions()}
                        </div>
                    </div>
                </div>

                <!-- CARACTERÍSTICAS AGRUPADAS -->
                <div class="filter-section">
                    <h5 class="filter-section-title" data-bs-toggle="collapse" data-bs-target="#featuresFilters">
                        <i class="bi bi-star me-2"></i>
                        Características
                        <i class="bi bi-chevron-down float-end"></i>
                    </h5>
                    <div class="collapse" id="featuresFilters">
                        <div class="filter-options">
                            ${this.renderGroupedCharacteristics()}
                        </div>
                    </div>
                </div>

                <!-- BOTONES DE ACCIÓN -->
                <div class="filter-actions mt-3">
                    <button class="btn btn-primary w-100 mb-2" id="applyFilters">
                        <i class="bi bi-search me-2"></i>
                        Buscar (<span id="totalProperties">${this.total}</span>)
                    </button>
                    <button class="btn btn-outline-secondary w-100" id="clearFilters">
                        <i class="bi bi-x-lg me-2"></i>
                        Limpiar Filtros
                    </button>
                </div>

            </div>
        `;

        this.container.innerHTML = html;
    }

    /**
     * Renderizar opciones de rango de precio
     */
    renderPriceRangeOptions() {
        const priceLabels = {
            '0-50m': 'Menos de $50M',
            '50-100m': '$50M - $100M',
            '100-200m': '$100M - $200M',
            '200-300m': '$200M - $300M',
            '300-500m': '$300M - $500M',
            '500-1000m': '$500M - $1.000M',
            '1000m+': 'Más de $1.000M',
        };

        let html = '';
        for (const [value, label] of Object.entries(priceLabels)) {
            const count = this.ranges.price_ranges?.[value] || 0;
            const disabled = count === 0 ? 'disabled' : '';
            html += `
                <div class="form-check">
                    <input class="form-check-input filter-radio"
                           type="radio"
                           name="price_range"
                           value="${value}"
                           id="price_${value}"
                           ${disabled}>
                    <label class="form-check-label" for="price_${value}">
                        ${label}
                        <span class="badge bg-secondary ms-2">${count}</span>
                    </label>
                </div>
            `;
        }
        return html;
    }

    /**
     * Renderizar opciones de habitaciones
     */
    renderBedroomOptions() {
        const bedroomLabels = {
            'studio': 'Apartaestudio',
            '1': '1 Habitación',
            '2': '2 Habitaciones',
            '3': '3 Habitaciones',
            '4': '4 Habitaciones',
            '5+': '5+ Habitaciones',
        };

        let html = '';
        for (const [value, label] of Object.entries(bedroomLabels)) {
            const count = this.ranges.bedroom_ranges?.[value] || 0;
            const disabled = count === 0 ? 'disabled' : '';
            html += `
                <div class="form-check">
                    <input class="form-check-input filter-radio"
                           type="radio"
                           name="bedrooms_range"
                           value="${value}"
                           id="bedrooms_${value}"
                           ${disabled}>
                    <label class="form-check-label" for="bedrooms_${value}">
                        ${label}
                        <span class="badge bg-secondary ms-2">${count}</span>
                    </label>
                </div>
            `;
        }
        return html;
    }

    /**
     * Renderizar opciones de baños
     */
    renderBathroomOptions() {
        const bathroomLabels = {
            '1': '1 Baño',
            '2': '2 Baños',
            '3': '3 Baños',
            '4+': '4+ Baños',
        };

        let html = '';
        for (const [value, label] of Object.entries(bathroomLabels)) {
            const count = this.ranges.bathroom_ranges?.[value] || 0;
            const disabled = count === 0 ? 'disabled' : '';
            html += `
                <div class="form-check">
                    <input class="form-check-input filter-radio"
                           type="radio"
                           name="bathrooms_range"
                           value="${value}"
                           id="bathrooms_${value}"
                           ${disabled}>
                    <label class="form-check-label" for="bathrooms_${value}">
                        ${label}
                        <span class="badge bg-secondary ms-2">${count}</span>
                    </label>
                </div>
            `;
        }
        return html;
    }

    /**
     * Renderizar opciones de parqueaderos
     */
    renderParkingOptions() {
        const parkingLabels = {
            '0': 'Sin Parqueadero',
            '1': '1 Parqueadero',
            '2': '2 Parqueaderos',
            '3+': '3+ Parqueaderos',
        };

        let html = '';
        for (const [value, label] of Object.entries(parkingLabels)) {
            const count = this.ranges.parking_ranges?.[value] || 0;
            const disabled = count === 0 ? 'disabled' : '';
            html += `
                <div class="form-check">
                    <input class="form-check-input filter-radio"
                           type="radio"
                           name="parking_range"
                           value="${value}"
                           id="parking_${value}"
                           ${disabled}>
                    <label class="form-check-label" for="parking_${value}">
                        ${label}
                        <span class="badge bg-secondary ms-2">${count}</span>
                    </label>
                </div>
            `;
        }
        return html;
    }

    /**
     * Renderizar opciones de área
     */
    renderAreaOptions() {
        const areaLabels = {
            '0-50': 'Menos de 50 m²',
            '50-80': '50-80 m²',
            '80-120': '80-120 m²',
            '120-200': '120-200 m²',
            '200-500': '200-500 m²',
            '500+': 'Más de 500 m²',
        };

        let html = '';
        for (const [value, label] of Object.entries(areaLabels)) {
            const count = this.ranges.area_ranges?.[value] || 0;
            const disabled = count === 0 ? 'disabled' : '';
            html += `
                <div class="form-check">
                    <input class="form-check-input filter-radio"
                           type="radio"
                           name="area_range"
                           value="${value}"
                           id="area_${value}"
                           ${disabled}>
                    <label class="form-check-label" for="area_${value}">
                        ${label}
                        <span class="badge bg-secondary ms-2">${count}</span>
                    </label>
                </div>
            `;
        }
        return html;
    }

    /**
     * Renderizar características agrupadas
     */
    renderGroupedCharacteristics() {
        const characteristics = [
            {
                id: 'has_outdoor_areas',
                label: 'Áreas Exteriores',
                icon: 'fa-tree',
                description: 'Balcón, terraza, jardín o patio'
            },
            {
                id: 'has_building_amenities',
                label: 'Amenidades del Conjunto',
                icon: 'fa-building',
                description: 'Piscina, gimnasio, salón social, zonas verdes'
            },
            {
                id: 'has_luxury_amenities',
                label: 'Amenidades de Lujo',
                icon: 'fa-gem',
                description: 'Jacuzzi, sauna, turco'
            },
            {
                id: 'has_full_security',
                label: 'Seguridad Completa',
                icon: 'fa-shield-alt',
                description: 'Portería 24h, cámaras, alarma'
            },
        ];

        let html = '';
        for (const char of characteristics) {
            const count = this.ranges.grouped_characteristics?.[char.id] || 0;
            const disabled = count === 0 ? 'disabled' : '';
            html += `
                <div class="form-check">
                    <input class="form-check-input filter-checkbox"
                           type="checkbox"
                           name="${char.id}"
                           id="${char.id}"
                           ${disabled}>
                    <label class="form-check-label" for="${char.id}">
                        <i class="fa ${char.icon} me-2"></i>
                        ${char.label}
                        <span class="badge bg-secondary ms-2">${count}</span>
                        <small class="d-block text-muted">${char.description}</small>
                    </label>
                </div>
            `;
        }
        return html;
    }

    /**
     * Adjuntar event listeners
     */
    attachEventListeners() {
        // Listener para cambios en filtros de radio
        this.container.querySelectorAll('.filter-radio').forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.filters[e.target.name] = e.target.value;
                this.onFilterChange();
            });
        });

        // Listener para cambios en filtros de checkbox
        this.container.querySelectorAll('.filter-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                this.filters[e.target.name] = e.target.checked;
                this.onFilterChange();
            });
        });

        // Botón aplicar filtros
        const applyBtn = this.container.querySelector('#applyFilters');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => {
                this.searchProperties();
            });
        }

        // Botón limpiar filtros
        const clearBtn = this.container.querySelector('#clearFilters');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearFilters();
            });
        }
    }

    /**
     * Callback cuando cambia un filtro
     */
    onFilterChange() {
        // Actualizar contadores en tiempo real
        this.loadRanges().then(() => {
            this.updateCounters();
        });

        // Callback personalizado
        if (this.callbacks.onFilterChange) {
            this.callbacks.onFilterChange(this.filters);
        }
    }

    /**
     * Actualizar contadores de filtros
     */
    updateCounters() {
        // Actualizar badges con nuevos contadores
        for (const [key, value] of Object.entries(this.ranges.price_ranges || {})) {
            const badge = this.container.querySelector(`#price_${key} + label .badge`);
            if (badge) badge.textContent = value;
        }

        // Similar para otros rangos...
    }

    /**
     * Buscar propiedades con filtros aplicados
     */
    async searchProperties(limit = 20, offset = 0) {
        try {
            const result = await rpc('/api/property/search/advanced', {
                filters: this.filters,
                limit: limit,
                offset: offset,
            });

            if (result.success) {
                this.properties = result.properties;
                this.total = result.total;

                // Actualizar contador
                const totalSpan = this.container.querySelector('#totalProperties');
                if (totalSpan) totalSpan.textContent = this.total;

                // Callback personalizado
                if (this.callbacks.onPropertiesLoaded) {
                    this.callbacks.onPropertiesLoaded(result);
                }

                return result;
            } else {
                console.error('Error searching properties:', result.error);
                return null;
            }
        } catch (error) {
            console.error('Error in searchProperties:', error);
            return null;
        }
    }

    /**
     * Limpiar todos los filtros
     */
    clearFilters() {
        // Reset filters object
        for (const key in this.filters) {
            this.filters[key] = typeof this.filters[key] === 'boolean' ? false : null;
        }

        // Uncheck all checkboxes
        this.container.querySelectorAll('.filter-checkbox').forEach(cb => {
            cb.checked = false;
        });

        // Uncheck all radios
        this.container.querySelectorAll('.filter-radio').forEach(radio => {
            radio.checked = false;
        });

        // Reload ranges and search
        this.loadRanges().then(() => {
            this.searchProperties();
        });
    }

    /**
     * Registrar callback
     */
    on(event, callback) {
        if (this.callbacks.hasOwnProperty(`on${event.charAt(0).toUpperCase()}${event.slice(1)}`)) {
            this.callbacks[`on${event.charAt(0).toUpperCase()}${event.slice(1)}`] = callback;
        }
    }

    /**
     * Cargar filtros específicos por tipo de propiedad
     */
    async loadPropertyTypeFilters(propertyType) {
        try {
            const result = await rpc('/api/property/filters/grouped', {
                property_type: propertyType
            });

            if (result.success) {
                this.propertyTypeFilters = result.filter_groups;
                console.log(`Filtros cargados para tipo: ${propertyType}`, this.propertyTypeFilters);
            }
        } catch (error) {
            console.error('Error loading property type filters:', error);
        }
    }

    /**
     * Actualizar filtros cuando cambia el tipo de propiedad
     */
    async onPropertyTypeChange(newType) {
        this.filters.property_type = newType;
        await this.loadPropertyTypeFilters(newType);
        await this.loadRanges();
        this.renderFilters();
        this.attachEventListeners();
    }
}

// Exportar para uso global
window.AdvancedPropertyFilters = AdvancedPropertyFilters;

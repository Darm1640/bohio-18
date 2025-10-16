/** @odoo-module **/

import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";

/**
 * BOHIO Property Filters - Componente OWL para Filtros Dinámicos
 * Implementación tipo search_panel con actualización en tiempo real
 *
 * Características:
 * - Filtros dinámicos con contadores
 * - Actualización AJAX sin recarga
 * - Unidades de medida según tipo de propiedad
 * - Sincronización con URL (SEO friendly)
 * - Historial del navegador (back/forward)
 */

export class PropertyFilters extends Component {
    setup() {
        this.state = useState({
            // Filtros activos
            filters: {
                type_service: '',
                property_type: '',
                city_id: '',
                state_id: '',
                region_id: '',
                project_id: '',
                min_price: '',
                max_price: '',
                min_area: '',
                max_area: '',
                bedrooms: '',
                bathrooms: '',
                garage: false,
                garden: false,
                pool: false,
                elevator: false,
            },

            // Opciones de filtros con contadores
            filterOptions: {
                property_types: [],
                cities: [],
                states: [],
                regions: [],
                projects: [],
                price_ranges: [],
                area_ranges: [],
                bedroom_options: [1, 2, 3, 4, 5, 6],
                bathroom_options: [1, 2, 3, 4, 5],
                service_types: [
                    { value: 'sale', label: 'Venta' },
                    { value: 'rent', label: 'Arriendo' },
                    { value: 'vacation_rent', label: 'Arriendo Vacacional' },
                ],
            },

            // Estado de la UI
            isLoading: false,
            expandedSections: {
                type: true,
                location: true,
                price: false,
                features: false,
                amenities: false,
            },

            // Resultados
            properties: [],
            total: 0,
            page: 1,
            ppg: 20,

            // Unidades de medida dinámicas
            measurementUnit: 'm²',  // Cambiará según property_type
        });

        onWillStart(async () => {
            await this.loadInitialFilters();
            await this.loadProperties();
        });

        onMounted(() => {
            this.setupURLSync();
        });
    }

    /**
     * Cargar opciones iniciales de filtros
     */
    async loadInitialFilters() {
        try {
            const result = await rpc('/property/filters/options', {
                context: 'public',
                filters: this.state.filters
            });

            if (result.success) {
                this.state.filterOptions = { ...this.state.filterOptions, ...result };
            }
        } catch (error) {
            console.error('Error cargando filtros iniciales:', error);
        }
    }

    /**
     * Cargar propiedades según filtros actuales
     */
    async loadProperties() {
        this.state.isLoading = true;

        try {
            const result = await rpc('/property/search/ajax', {
                context: 'public',
                filters: this.state.filters,
                page: this.state.page,
                ppg: this.state.ppg,
                order: 'relevance'
            });

            if (result.success) {
                this.state.properties = result.properties;
                this.state.total = result.total;
            }
        } catch (error) {
            console.error('Error cargando propiedades:', error);
        } finally {
            this.state.isLoading = false;
        }
    }

    /**
     * Actualizar filtros y recargar opciones con contadores
     */
    async updateFilterOptions() {
        try {
            const result = await rpc('/property/filters/options', {
                context: 'public',
                filters: this.state.filters
            });

            if (result.success) {
                // Actualizar solo las opciones que dependen de otros filtros
                this.state.filterOptions.regions = result.regions;
                this.state.filterOptions.projects = result.projects;
                this.state.filterOptions.price_ranges = result.price_ranges;

                // Actualizar unidad de medida según tipo de propiedad
                this.updateMeasurementUnit();
            }
        } catch (error) {
            console.error('Error actualizando opciones de filtros:', error);
        }
    }

    /**
     * Actualizar unidad de medida según tipo de propiedad
     */
    updateMeasurementUnit() {
        const propertyType = this.state.filters.property_type;

        // Mapeo de tipos a unidades
        const unitMap = {
            'apartment': 'm²',
            'house': 'm²',
            'penthouse': 'm²',
            'office': 'm²',
            'commercial': 'm²',
            'warehouse': 'm²',
            'lot': 'm²',  // o 'hectáreas' para lotes grandes
            'farm': 'hectáreas',
            'land': 'hectáreas',
        };

        this.state.measurementUnit = unitMap[propertyType] || 'm²';
    }

    /**
     * Manejar cambio en un filtro
     */
    async onFilterChange(filterName, value) {
        // Actualizar filtro
        this.state.filters[filterName] = value;

        // Si cambió ciudad/estado/región, limpiar filtros dependientes
        if (filterName === 'city_id') {
            this.state.filters.region_id = '';
            this.state.filters.project_id = '';
        } else if (filterName === 'state_id') {
            this.state.filters.city_id = '';
            this.state.filters.region_id = '';
            this.state.filters.project_id = '';
        }

        // Si cambió tipo de propiedad o servicio, actualizar rangos de precio
        if (filterName === 'property_type' || filterName === 'type_service') {
            await this.updateFilterOptions();
        }

        // Resetear paginación
        this.state.page = 1;

        // Recargar propiedades
        await this.loadProperties();

        // Actualizar URL
        this.updateURL();

        // Actualizar opciones de filtros con nuevos contadores
        await this.updateFilterOptions();
    }

    /**
     * Limpiar todos los filtros
     */
    async clearFilters() {
        // Resetear filtros
        Object.keys(this.state.filters).forEach(key => {
            if (typeof this.state.filters[key] === 'boolean') {
                this.state.filters[key] = false;
            } else {
                this.state.filters[key] = '';
            }
        });

        // Recargar
        this.state.page = 1;
        await this.loadProperties();
        await this.updateFilterOptions();

        // Limpiar URL
        window.history.pushState({}, '', window.location.pathname);
    }

    /**
     * Toggle sección expandida/colapsada
     */
    toggleSection(section) {
        this.state.expandedSections[section] = !this.state.expandedSections[section];
    }

    /**
     * Cambiar página
     */
    async changePage(newPage) {
        this.state.page = newPage;
        await this.loadProperties();
        this.updateURL();

        // Scroll al top de resultados
        document.querySelector('.property-results')?.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }

    /**
     * Sincronizar filtros con URL (SEO)
     */
    setupURLSync() {
        // Leer filtros de la URL al cargar
        const urlParams = new URLSearchParams(window.location.search);

        Object.keys(this.state.filters).forEach(key => {
            const value = urlParams.get(key);
            if (value) {
                if (typeof this.state.filters[key] === 'boolean') {
                    this.state.filters[key] = value === 'true';
                } else {
                    this.state.filters[key] = value;
                }
            }
        });

        // Manejar botón atrás/adelante del navegador
        window.addEventListener('popstate', () => {
            this.setupURLSync();
            this.loadProperties();
        });
    }

    /**
     * Actualizar URL con filtros actuales
     */
    updateURL() {
        const params = new URLSearchParams();

        Object.entries(this.state.filters).forEach(([key, value]) => {
            if (value && value !== '' && value !== false) {
                params.set(key, value);
            }
        });

        if (this.state.page > 1) {
            params.set('page', this.state.page);
        }

        const newURL = `${window.location.pathname}?${params.toString()}`;
        window.history.pushState({ filters: this.state.filters }, '', newURL);
    }

    /**
     * Formatear precio en COP
     */
    formatPrice(price) {
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0
        }).format(price);
    }

    /**
     * Obtener conteo activo de filtros
     */
    get activeFiltersCount() {
        return Object.values(this.state.filters).filter(v => v && v !== '' && v !== false).length;
    }
}


PropertyFilters.template = "theme_bohio_real_estate.PropertyFiltersTemplate";

registry.category("public_components").add("PropertyFilters", PropertyFilters);

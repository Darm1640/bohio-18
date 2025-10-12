/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";

console.log('[HOMEPAGE-AUTOCOMPLETE] Módulo cargado');

/**
 * Widget de Autocompletado para Homepage
 * Se inicializa automáticamente en la homepage
 */
const HomepageAutocomplete = publicWidget.Widget.extend({
    selector: '.search-bar-container',

    events: {
        'input .property-search-input': '_onSearchInput',
        'click .autocomplete-item': '_onItemClick',
    },

    /**
     * Inicialización del widget
     */
    start: function () {
        console.log('[HOMEPAGE-AUTOCOMPLETE] Widget inicializado');
        this.autocompleteTimeout = null;
        this.searchInput = this.$('.property-search-input')[0];
        this.autocompleteContainer = this.$('.autocomplete-container')[0];

        if (!this.searchInput) {
            console.warn('[HOMEPAGE-AUTOCOMPLETE] Input de búsqueda NO encontrado');
            return this._super.apply(this, arguments);
        }

        if (!this.autocompleteContainer) {
            console.warn('[HOMEPAGE-AUTOCOMPLETE] Contenedor NO encontrado, creando...');
            this.autocompleteContainer = document.createElement('div');
            this.autocompleteContainer.className = 'autocomplete-container shadow-lg';
            this.autocompleteContainer.style.cssText = 'display: none; position: absolute; top: 100%; left: 0; right: 0; z-index: 2000; margin-top: 5px; background: white; border-radius: 8px; max-height: 400px; overflow-y: auto; border: 2px solid #E31E24;';
            this.el.appendChild(this.autocompleteContainer);
        }

        console.log('[HOMEPAGE-AUTOCOMPLETE] ✅ Widget listo');

        // Cerrar al hacer click fuera
        $(document).on('click', (e) => {
            if (!$(e.target).closest('.search-bar-container').length) {
                this._hideAutocomplete();
            }
        });

        return this._super.apply(this, arguments);
    },

    /**
     * Handler del input de búsqueda
     */
    _onSearchInput: function (ev) {
        clearTimeout(this.autocompleteTimeout);
        const term = $(ev.currentTarget).val().trim();

        console.log('[HOMEPAGE-AUTOCOMPLETE] Input detectado:', term);

        if (term.length < 2) {
            this._hideAutocomplete();
            return;
        }

        // Mostrar indicador de carga
        this._showLoading();

        // Debounce de 300ms
        this.autocompleteTimeout = setTimeout(() => {
            console.log('[HOMEPAGE-AUTOCOMPLETE] Ejecutando búsqueda para:', term);
            this._performAutocomplete(term);
        }, 300);
    },

    /**
     * Mostrar indicador de carga
     */
    _showLoading: function () {
        if (!this.autocompleteContainer) return;

        this.autocompleteContainer.innerHTML = `
            <div class="p-3 text-center">
                <div class="spinner-border spinner-border-sm text-danger me-2" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <span class="text-muted">Buscando...</span>
            </div>
        `;
        this.autocompleteContainer.style.display = 'block';
    },

    /**
     * Realizar búsqueda de autocompletado
     */
    _performAutocomplete: async function (term) {
        console.log('[HOMEPAGE-AUTOCOMPLETE] Llamando a /property/search/autocomplete');

        try {
            const result = await rpc('/property/search/autocomplete', {
                term: term,
                subdivision: 'all',
                context: 'public',
                limit: 10
            });

            console.log('[HOMEPAGE-AUTOCOMPLETE] Resultado:', result);

            if (result.success) {
                this._renderResults(result.results || [], term);
            } else {
                console.error('[HOMEPAGE-AUTOCOMPLETE] Error en resultado:', result);
                this._showError('Error al buscar');
            }
        } catch (error) {
            console.error('[HOMEPAGE-AUTOCOMPLETE] Error en RPC:', error);
            this._showError('Error de conexión');
        }
    },

    /**
     * Renderizar resultados
     */
    _renderResults: function (results, term) {
        if (!this.autocompleteContainer) return;

        console.log('[HOMEPAGE-AUTOCOMPLETE] Renderizando', results.length, 'resultados');

        if (results.length === 0) {
            this.autocompleteContainer.innerHTML = `
                <div class="p-3 text-center text-muted">
                    <i class="fa fa-search-minus me-2"></i>
                    No se encontraron resultados
                </div>
            `;
            this.autocompleteContainer.style.display = 'block';
            return;
        }

        let html = '<ul class="list-unstyled mb-0">';

        results.forEach(result => {
            // Extraer IDs numéricos
            let numericId = result.city_id || result.region_id || result.project_id || result.property_id || '';

            // Determinar ícono y color
            let iconClass = 'fa-map-marker-alt';
            let badgeColor = 'primary';

            if (result.type === 'city') {
                iconClass = 'fa-map-marker-alt';
                badgeColor = 'primary';
            } else if (result.type === 'region') {
                iconClass = 'fa-home';
                badgeColor = 'success';
            } else if (result.type === 'project') {
                iconClass = 'fa-building';
                badgeColor = 'warning';
            } else if (result.type === 'property') {
                iconClass = 'fa-key';
                badgeColor = 'info';
            }

            html += `
                <li class="autocomplete-item"
                    data-type="${result.type}"
                    data-id="${numericId}"
                    data-city-id="${result.city_id || ''}"
                    data-region-id="${result.region_id || ''}"
                    data-project-id="${result.project_id || ''}"
                    data-property-id="${result.property_id || ''}"
                    style="cursor: pointer; padding: 12px 16px; border-bottom: 1px solid #eee; display: flex; align-items: center; transition: background 0.2s;"
                    onmouseover="this.style.background='#f8f9fa'"
                    onmouseout="this.style.background='white'">

                    <div style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background: rgba(227, 30, 36, 0.1); border-radius: 50%; margin-right: 12px;">
                        <i class="fa ${iconClass}" style="color: #E31E24; font-size: 16px;"></i>
                    </div>

                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: #333; margin-bottom: 2px;">
                            ${this._highlightTerm(result.name, term)}
                        </div>
                        ${result.full_name && result.full_name !== result.name ? `
                            <div style="font-size: 12px; color: #666;">
                                ${result.full_name}
                            </div>
                        ` : ''}
                    </div>

                    ${result.property_count > 0 ? `
                        <span class="badge bg-${badgeColor}" style="margin-left: 8px;">
                            ${result.property_count}
                        </span>
                    ` : ''}
                </li>
            `;
        });

        html += '</ul>';

        this.autocompleteContainer.innerHTML = html;
        this.autocompleteContainer.style.display = 'block';

        console.log('[HOMEPAGE-AUTOCOMPLETE] Resultados renderizados');
    },

    /**
     * Highlight del término de búsqueda
     */
    _highlightTerm: function (text, term) {
        if (!term) return text;
        const regex = new RegExp(`(${this._escapeRegex(term)})`, 'gi');
        return text.replace(regex, '<strong style="color: #E31E24;">$1</strong>');
    },

    /**
     * Escapar caracteres especiales para regex
     */
    _escapeRegex: function (string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    },

    /**
     * Handler del click en un item
     */
    _onItemClick: function (ev) {
        const $item = $(ev.currentTarget);
        const data = $item.data();

        console.log('[HOMEPAGE-AUTOCOMPLETE] Item seleccionado:', data);

        // Construir URL de redirección
        let params = new URLSearchParams();

        // Agregar tipo de servicio si existe
        const serviceTypeInput = document.getElementById('selectedServiceType');
        if (serviceTypeInput && serviceTypeInput.value) {
            params.set('type_service', serviceTypeInput.value);
        }

        // Agregar el término de búsqueda actual
        const searchTerm = $(this.searchInput).val().trim();
        if (searchTerm) {
            params.set('search', searchTerm);
        }

        // Agregar filtro de ubicación según el tipo
        if (data.type === 'city' && data.cityId) {
            params.set('city_id', data.cityId);
        } else if (data.type === 'region' && data.regionId) {
            params.set('region_id', data.regionId);
        } else if (data.type === 'project' && data.projectId) {
            params.set('project_id', data.projectId);
        } else if (data.type === 'property' && data.propertyId) {
            // Si es una propiedad específica, ir directamente al detalle
            window.location.href = `/property/${data.propertyId}`;
            return;
        }

        // Redirigir a la página de propiedades con filtros
        window.location.href = `/properties?${params.toString()}`;
    },

    /**
     * Mostrar mensaje de error
     */
    _showError: function (message) {
        if (!this.autocompleteContainer) return;

        this.autocompleteContainer.innerHTML = `
            <div class="p-3 text-center text-danger">
                <i class="fa fa-exclamation-triangle me-2"></i>${message}
            </div>
        `;
        this.autocompleteContainer.style.display = 'block';
    },

    /**
     * Ocultar autocompletado
     */
    _hideAutocomplete: function () {
        if (this.autocompleteContainer) {
            this.autocompleteContainer.style.display = 'none';
        }
    },
});

// Registrar el widget para que se active automáticamente
publicWidget.registry.HomepageAutocomplete = HomepageAutocomplete;

export default HomepageAutocomplete;

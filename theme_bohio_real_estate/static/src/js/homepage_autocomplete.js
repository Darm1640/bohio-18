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
        'click .autocomplete-container .autocomplete-item': '_onItemClick',
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
     * Mostrar indicador de carga (usando createElement)
     */
    _showLoading: function () {
        if (!this.autocompleteContainer) return;

        // Limpiar contenido anterior
        this.autocompleteContainer.innerHTML = '';

        // Crear estructura con createElement
        const wrapper = document.createElement('div');
        wrapper.className = 'p-3 text-center';

        const spinner = document.createElement('div');
        spinner.className = 'spinner-border spinner-border-sm text-danger me-2';
        spinner.setAttribute('role', 'status');

        const spinnerText = document.createElement('span');
        spinnerText.className = 'visually-hidden';
        spinnerText.textContent = 'Cargando...';
        spinner.appendChild(spinnerText);

        const text = document.createElement('span');
        text.className = 'text-muted';
        text.textContent = 'Buscando...';

        wrapper.appendChild(spinner);
        wrapper.appendChild(text);

        this.autocompleteContainer.appendChild(wrapper);
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
     * Renderizar resultados (usando createElement)
     */
    _renderResults: function (results, term) {
        if (!this.autocompleteContainer) return;

        console.log('[HOMEPAGE-AUTOCOMPLETE] Renderizando', results.length, 'resultados');

        // Limpiar contenido anterior
        this.autocompleteContainer.innerHTML = '';

        if (results.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'p-3 text-center text-muted';

            const icon = document.createElement('i');
            icon.className = 'fa fa-search-minus me-2';

            noResults.appendChild(icon);
            noResults.appendChild(document.createTextNode('No se encontraron resultados'));

            this.autocompleteContainer.appendChild(noResults);
            this.autocompleteContainer.style.display = 'block';
            return;
        }

        // Crear lista
        const ul = document.createElement('ul');
        ul.className = 'list-unstyled mb-0';

        results.forEach(result => {
            const item = this._createAutocompleteItem(result, term);
            ul.appendChild(item);
        });

        this.autocompleteContainer.appendChild(ul);
        this.autocompleteContainer.style.display = 'block';

        console.log('[HOMEPAGE-AUTOCOMPLETE] Resultados renderizados');
    },

    /**
     * Crear item de autocomplete (usando createElement)
     * @private
     */
    _createAutocompleteItem: function (result, term) {
        // Extraer IDs numéricos
        const numericId = result.city_id || result.region_id || result.project_id || result.property_id || '';

        // Determinar ícono y color
        const iconMap = {
            city: { class: 'fa-map-marker-alt', badge: 'primary' },
            region: { class: 'fa-home', badge: 'success' },
            project: { class: 'fa-building', badge: 'warning' },
            property: { class: 'fa-key', badge: 'info' }
        };
        const iconInfo = iconMap[result.type] || iconMap.city;

        // Crear item <li>
        const li = document.createElement('li');
        li.className = 'autocomplete-item';
        li.style.cssText = 'cursor: pointer; padding: 12px 16px; border-bottom: 1px solid #eee; display: flex; align-items: center; transition: background 0.2s;';

        // Data attributes
        li.dataset.type = result.type;
        li.dataset.id = numericId;
        li.dataset.cityId = result.city_id || '';
        li.dataset.regionId = result.region_id || '';
        li.dataset.projectId = result.project_id || '';
        li.dataset.propertyId = result.property_id || '';

        // Hover effects
        li.addEventListener('mouseenter', () => li.style.background = '#f8f9fa');
        li.addEventListener('mouseleave', () => li.style.background = 'white');

        // Icono
        const iconWrapper = document.createElement('div');
        iconWrapper.style.cssText = 'width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; background: rgba(227, 30, 36, 0.1); border-radius: 50%; margin-right: 12px;';

        const icon = document.createElement('i');
        icon.className = `fa ${iconInfo.class}`;
        icon.style.cssText = 'color: #E31E24; font-size: 16px;';

        iconWrapper.appendChild(icon);
        li.appendChild(iconWrapper);

        // Contenido
        const content = document.createElement('div');
        content.style.flex = '1';

        // Nombre (con highlight)
        const title = document.createElement('div');
        title.style.cssText = 'font-weight: 600; color: #333; margin-bottom: 2px;';
        title.innerHTML = this._highlightTerm(result.name, term);
        content.appendChild(title);

        // Nombre completo (si existe)
        if (result.full_name && result.full_name !== result.name) {
            const subtitle = document.createElement('div');
            subtitle.style.cssText = 'font-size: 12px; color: #666;';
            subtitle.textContent = result.full_name;
            content.appendChild(subtitle);
        }

        li.appendChild(content);

        // Badge (si hay propiedades)
        if (result.property_count > 0) {
            const badge = document.createElement('span');
            badge.className = `badge bg-${iconInfo.badge}`;
            badge.style.marginLeft = '8px';
            badge.textContent = result.property_count;
            li.appendChild(badge);
        }

        return li;
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
     * Mostrar mensaje de error (usando createElement)
     */
    _showError: function (message) {
        if (!this.autocompleteContainer) return;

        // Limpiar contenido anterior
        this.autocompleteContainer.innerHTML = '';

        const errorDiv = document.createElement('div');
        errorDiv.className = 'p-3 text-center text-danger';

        const icon = document.createElement('i');
        icon.className = 'bi bi-exclamation-triangle me-2';

        errorDiv.appendChild(icon);
        errorDiv.appendChild(document.createTextNode(message));

        this.autocompleteContainer.appendChild(errorDiv);
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

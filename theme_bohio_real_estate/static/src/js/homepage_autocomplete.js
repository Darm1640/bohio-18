/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

console.log('[HOMEPAGE-AUTOCOMPLETE] Módulo cargado');

/**
 * Sistema de Autocompletado para Homepage
 * Funciona igual que en la página de propiedades
 */
class HomepageAutocomplete {
    constructor() {
        this.autocompleteTimeout = null;
        this.searchInput = null;
        this.autocompleteContainer = null;

        this.init();
    }

    init() {
        console.log('[HOMEPAGE-AUTOCOMPLETE] Inicializando...');

        // Buscar el input de búsqueda (puede tener diferentes clases/IDs)
        this.searchInput = document.querySelector('.property-search-input') ||
                          document.getElementById('homepage-search-input') ||
                          document.querySelector('input[name="search_query"]');

        if (!this.searchInput) {
            console.warn('[HOMEPAGE-AUTOCOMPLETE] Input de búsqueda NO encontrado');
            return;
        }

        console.log('[HOMEPAGE-AUTOCOMPLETE] Input encontrado:', this.searchInput);

        // Buscar o crear contenedor de resultados
        this.autocompleteContainer = this.searchInput.closest('.search-bar-container')?.querySelector('.autocomplete-container');

        if (!this.autocompleteContainer) {
            console.warn('[HOMEPAGE-AUTOCOMPLETE] Contenedor de autocompletado NO encontrado');
            // Crear contenedor si no existe
            this.autocompleteContainer = document.createElement('div');
            this.autocompleteContainer.className = 'autocomplete-container shadow-lg';
            this.autocompleteContainer.style.display = 'none';

            const parent = this.searchInput.closest('.search-bar-container');
            if (parent) {
                parent.appendChild(this.autocompleteContainer);
                console.log('[HOMEPAGE-AUTOCOMPLETE] Contenedor creado');
            }
        }

        // Agregar event listener al input
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(this.autocompleteTimeout);
            const term = e.target.value.trim();

            console.log('[HOMEPAGE-AUTOCOMPLETE] Input detectado:', term);

            if (term.length < 2) {
                this.hideAutocomplete();
                return;
            }

            // Mostrar indicador de carga
            this.showLoading();

            // Debounce de 300ms
            this.autocompleteTimeout = setTimeout(() => {
                console.log('[HOMEPAGE-AUTOCOMPLETE] Ejecutando búsqueda para:', term);
                this.performAutocomplete(term);
            }, 300);
        });

        // Cerrar al hacer click fuera
        document.addEventListener('click', (e) => {
            if (!this.searchInput.contains(e.target) &&
                !this.autocompleteContainer.contains(e.target)) {
                this.hideAutocomplete();
            }
        });

        console.log('[HOMEPAGE-AUTOCOMPLETE] ✅ Inicialización completa');
    }

    showLoading() {
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
    }

    async performAutocomplete(term) {
        const subdivision = 'all'; // En homepage siempre buscar todo

        console.log('[HOMEPAGE-AUTOCOMPLETE] Llamando a /property/search/autocomplete');

        try {
            const result = await rpc('/property/search/autocomplete', {
                term: term,
                subdivision: subdivision,
                context: 'public',
                limit: 10
            });

            console.log('[HOMEPAGE-AUTOCOMPLETE] Resultado:', result);

            if (result.success) {
                this.renderAutocompleteResults(result.results || []);
            } else {
                console.error('[HOMEPAGE-AUTOCOMPLETE] Error en resultado:', result);
                this.showError('Error al buscar');
            }
        } catch (error) {
            console.error('[HOMEPAGE-AUTOCOMPLETE] Error en RPC:', error);
            this.showError('Error de conexión');
        }
    }

    renderAutocompleteResults(results) {
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
            let numericId = '';
            if (result.city_id) numericId = result.city_id;
            else if (result.region_id) numericId = result.region_id;
            else if (result.project_id) numericId = result.project_id;
            else if (result.property_id) numericId = result.property_id;

            // Determinar ícono
            let iconClass = 'fa-map-marker-alt';
            let iconType = 'city';
            let badgeColor = 'primary';

            if (result.type === 'city') {
                iconClass = 'fa-map-marker-alt';
                iconType = 'city';
                badgeColor = 'primary';
            } else if (result.type === 'region') {
                iconClass = 'fa-home';
                iconType = 'region';
                badgeColor = 'success';
            } else if (result.type === 'project') {
                iconClass = 'fa-building';
                iconType = 'project';
                badgeColor = 'warning';
            } else if (result.type === 'property') {
                iconClass = 'fa-key';
                iconType = 'property';
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

                    <div class="autocomplete-item-icon ${iconType}" style="width: 40px; height: 40px; display: flex; align-items: center; justify-content-center; background: rgba(227, 30, 36, 0.1); border-radius: 50%; margin-right: 12px;">
                        <i class="fa ${iconClass}" style="color: #E31E24; font-size: 16px;"></i>
                    </div>

                    <div class="autocomplete-item-content" style="flex: 1;">
                        <div class="autocomplete-item-title" style="font-weight: 600; color: #333; margin-bottom: 2px;">
                            ${this.highlightTerm(result.name, term)}
                        </div>
                        ${result.full_name && result.full_name !== result.name ? `
                            <div class="autocomplete-item-subtitle" style="font-size: 12px; color: #666;">
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
        this.autocompleteContainer.style.position = 'absolute';
        this.autocompleteContainer.style.top = '100%';
        this.autocompleteContainer.style.left = '0';
        this.autocompleteContainer.style.right = '0';
        this.autocompleteContainer.style.background = 'white';
        this.autocompleteContainer.style.borderRadius = '8px';
        this.autocompleteContainer.style.maxHeight = '400px';
        this.autocompleteContainer.style.overflowY = 'auto';
        this.autocompleteContainer.style.zIndex = '1050';
        this.autocompleteContainer.style.marginTop = '5px';

        console.log('[HOMEPAGE-AUTOCOMPLETE] Resultados renderizados');

        // Agregar event listeners a los items
        this.autocompleteContainer.querySelectorAll('.autocomplete-item').forEach(item => {
            item.addEventListener('click', () => {
                this.selectAutocompleteItem(item.dataset);
            });
        });
    }

    highlightTerm(text, term) {
        if (!term) return text;
        const regex = new RegExp(`(${this.escapeRegex(term)})`, 'gi');
        return text.replace(regex, '<strong style="color: #E31E24;">$1</strong>');
    }

    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    selectAutocompleteItem(data) {
        console.log('[HOMEPAGE-AUTOCOMPLETE] Item seleccionado:', data);

        // Construir URL de redirección
        let params = new URLSearchParams();

        // Agregar tipo de servicio si existe
        const serviceTypeSelect = document.getElementById('selectedServiceType');
        if (serviceTypeSelect && serviceTypeSelect.value) {
            params.set('type_service', serviceTypeSelect.value);
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
    }

    showError(message) {
        if (!this.autocompleteContainer) return;

        this.autocompleteContainer.innerHTML = `
            <div class="p-3 text-center text-danger">
                <i class="fa fa-exclamation-triangle me-2"></i>${message}
            </div>
        `;
        this.autocompleteContainer.style.display = 'block';
    }

    hideAutocomplete() {
        if (this.autocompleteContainer) {
            this.autocompleteContainer.style.display = 'none';
        }
    }
}

// Inicializar cuando el DOM esté listo
function initHomepageAutocomplete() {
    console.log('[HOMEPAGE-AUTOCOMPLETE] Ejecutando inicialización...');

    // Verificar que estemos en la página correcta
    const searchInput = document.querySelector('.property-search-input') ||
                       document.getElementById('homepage-search-input') ||
                       document.querySelector('input[name="search_query"]');

    if (searchInput) {
        console.log('[HOMEPAGE-AUTOCOMPLETE] Creando instancia...');
        window.homepageAutocomplete = new HomepageAutocomplete();
    } else {
        console.log('[HOMEPAGE-AUTOCOMPLETE] No se encontró input de búsqueda, saltando inicialización');
    }
}

// Ejecutar al cargar el DOM
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initHomepageAutocomplete);
} else {
    initHomepageAutocomplete();
}

// También escuchar el evento de Odoo para páginas cargadas dinámicamente
window.addEventListener('website:page_loaded', initHomepageAutocomplete);

// Exportar para uso global
export { HomepageAutocomplete, initHomepageAutocomplete };

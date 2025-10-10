/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

/**
 * BOHIO Homepage Autocomplete - Sistema de Autocompletado Inteligente
 * Implementación con RPC nativo de Odoo 18 (disponible en web.assets_frontend)
 *
 * Características:
 * - Búsqueda en tiempo real con debounce
 * - Normalización sin acentos (buscar "bogota" encuentra "Bogotá")
 * - Resultados agrupados: Ciudades, Barrios, Proyectos, Propiedades
 * - Iconos por tipo de resultado
 * - Contadores de propiedades disponibles
 * - Navegación por teclado (↑ ↓ Enter Escape)
 */

class BohioAutocomplete {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.options = {
            minChars: 2,
            debounceMs: 300,
            maxResults: 10,
            context: 'public',
            subdivision: 'all', // 'all', 'cities', 'regions', 'projects', 'properties'
            onSelect: null,
            ...options
        };

        this.resultsContainer = null;
        this.currentResults = [];
        this.selectedIndex = -1;
        this.debounceTimer = null;
        this.isLoading = false;

        this.init();
    }

    init() {
        // Crear contenedor de resultados
        this.createResultsContainer();

        // Eventos del input
        this.input.addEventListener('input', (e) => this.handleInput(e));
        this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
        this.input.addEventListener('focus', () => this.showResults());

        // Cerrar al hacer click fuera
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.resultsContainer.contains(e.target)) {
                this.hideResults();
            }
        });

        console.log('BOHIO Autocomplete inicializado en:', this.input.id || this.input.placeholder);
    }

    createResultsContainer() {
        this.resultsContainer = document.createElement('div');
        this.resultsContainer.className = 'bohio-autocomplete-results';
        this.resultsContainer.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            max-height: 400px;
            overflow-y: auto;
            z-index: 1050;
            display: none;
            margin-top: 5px;
        `;

        // Insertar después del input
        const parent = this.input.parentElement;
        if (parent.style.position !== 'relative' && parent.style.position !== 'absolute') {
            parent.style.position = 'relative';
        }
        parent.appendChild(this.resultsContainer);
    }

    handleInput(e) {
        const value = e.target.value.trim();

        // Limpiar timer anterior
        clearTimeout(this.debounceTimer);

        if (value.length < this.options.minChars) {
            this.hideResults();
            return;
        }

        // Mostrar loading inmediatamente
        this.showLoading();

        // Debounce la búsqueda
        this.debounceTimer = setTimeout(async () => {
            await this.search(value);
        }, this.options.debounceMs);
    }

    handleKeydown(e) {
        if (!this.resultsContainer.style.display || this.resultsContainer.style.display === 'none') {
            return;
        }

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectNext();
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.selectPrevious();
                break;
            case 'Enter':
                e.preventDefault();
                if (this.selectedIndex >= 0 && this.currentResults[this.selectedIndex]) {
                    this.selectResult(this.currentResults[this.selectedIndex]);
                }
                break;
            case 'Escape':
                this.hideResults();
                break;
        }
    }

    async search(term) {
        if (this.isLoading) return;

        this.isLoading = true;

        try {
            const result = await rpc('/property/search/autocomplete', {
                term: term,
                context: this.options.context,
                subdivision: this.options.subdivision,
                limit: this.options.maxResults
            });

            if (result.success) {
                this.currentResults = result.results || [];
                this.renderResults(result.results || [], term);
            } else {
                this.showError('Error al buscar');
            }
        } catch (error) {
            console.error('Error en autocompletado:', error);
            this.showError('Error de conexión');
        } finally {
            this.isLoading = false;
        }
    }

    renderResults(results, searchTerm) {
        if (results.length === 0) {
            this.resultsContainer.innerHTML = `
                <div class="p-3 text-center text-muted">
                    <i class="fa fa-search-minus me-2"></i>
                    No se encontraron resultados para "${searchTerm}"
                </div>
            `;
            this.showResults();
            return;
        }

        // Agrupar resultados por tipo
        const grouped = this.groupResultsByType(results);

        let html = '';

        // Ciudades
        if (grouped.cities && grouped.cities.length > 0) {
            html += this.renderGroup('Ciudades', grouped.cities, 'fa-map-marker-alt', 'text-primary');
        }

        // Regiones/Barrios
        if (grouped.regions && grouped.regions.length > 0) {
            html += this.renderGroup('Barrios', grouped.regions, 'fa-home', 'text-success');
        }

        // Proyectos
        if (grouped.projects && grouped.projects.length > 0) {
            html += this.renderGroup('Proyectos', grouped.projects, 'fa-building', 'text-warning');
        }

        // Propiedades
        if (grouped.properties && grouped.properties.length > 0) {
            html += this.renderGroup('Propiedades', grouped.properties, 'fa-key', 'text-info');
        }

        this.resultsContainer.innerHTML = html;
        this.selectedIndex = -1;
        this.showResults();

        // Agregar eventos click
        this.attachClickEvents();
    }

    groupResultsByType(results) {
        return {
            cities: results.filter(r => r.type === 'city'),
            regions: results.filter(r => r.type === 'region'),
            projects: results.filter(r => r.type === 'project'),
            properties: results.filter(r => r.type === 'property')
        };
    }

    renderGroup(title, items, icon, colorClass) {
        let html = `<div class="autocomplete-group">`;

        items.forEach((item, index) => {
            const globalIndex = this.currentResults.indexOf(item);

            // Determinar tipo de icono
            let iconType = 'city';
            if (item.type === 'city') iconType = 'city';
            else if (item.type === 'region') iconType = 'region';
            else if (item.type === 'project') iconType = 'project';
            else if (item.type === 'property') iconType = 'property';

            html += `
                <div class="autocomplete-item" data-index="${globalIndex}">
                    <div class="autocomplete-item-icon ${iconType}">
                        <i class="fa ${icon}"></i>
                    </div>
                    <div class="autocomplete-item-content">
                        <span class="autocomplete-item-title">${this.highlightTerm(item.name, this.input.value)}</span>
                        ${item.full_name && item.full_name !== item.name ?
                            `<span class="autocomplete-item-subtitle">${item.full_name}</span>` : ''}
                    </div>
                    ${item.property_count ?
                        `<span class="autocomplete-item-badge">${item.property_count}</span>` : ''}
                </div>
            `;
        });

        html += `</div>`;
        return html;
    }

    highlightTerm(text, term) {
        if (!term) return text;
        const regex = new RegExp(`(${this.escapeRegex(term)})`, 'gi');
        return text.replace(regex, '<strong class="text-danger">$1</strong>');
    }

    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    attachClickEvents() {
        const items = this.resultsContainer.querySelectorAll('.autocomplete-item');
        items.forEach(item => {
            item.addEventListener('click', () => {
                const index = parseInt(item.dataset.index);
                this.selectResult(this.currentResults[index]);
            });

            item.addEventListener('mouseenter', () => {
                this.selectedIndex = parseInt(item.dataset.index);
                this.updateSelection();
            });
        });
    }

    selectNext() {
        if (this.selectedIndex < this.currentResults.length - 1) {
            this.selectedIndex++;
            this.updateSelection();
            this.scrollToSelected();
        }
    }

    selectPrevious() {
        if (this.selectedIndex > 0) {
            this.selectedIndex--;
            this.updateSelection();
            this.scrollToSelected();
        }
    }

    updateSelection() {
        const items = this.resultsContainer.querySelectorAll('.autocomplete-item');
        items.forEach((item, index) => {
            const itemIndex = parseInt(item.dataset.index);
            if (itemIndex === this.selectedIndex) {
                item.style.backgroundColor = '#f8f9fa';
                item.style.cursor = 'pointer';
            } else {
                item.style.backgroundColor = '';
            }
        });
    }

    scrollToSelected() {
        const selected = this.resultsContainer.querySelector(`[data-index="${this.selectedIndex}"]`);
        if (selected) {
            selected.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
    }

    selectResult(result) {
        if (!result) return;

        // Callback personalizado
        if (this.options.onSelect) {
            this.options.onSelect(result);
            this.hideResults();
            return;
        }

        // Comportamiento por defecto: redirigir a búsqueda
        this.redirectToSearch(result);
    }

    redirectToSearch(result) {
        let params = new URLSearchParams();

        switch (result.type) {
            case 'city':
                params.set('city_id', result.city_id);
                break;
            case 'region':
                params.set('region_id', result.region_id);
                break;
            case 'project':
                params.set('project_id', result.project_id);
                break;
            case 'property':
                window.location.href = `/property/${result.property_id}`;
                return;
        }

        window.location.href = `/properties?${params.toString()}`;
    }

    showLoading() {
        this.resultsContainer.innerHTML = `
            <div class="p-3 text-center">
                <div class="spinner-border spinner-border-sm text-danger me-2" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <span class="text-muted">Buscando...</span>
            </div>
        `;
        this.showResults();
    }

    showError(message) {
        this.resultsContainer.innerHTML = `
            <div class="p-3 text-center text-danger">
                <i class="fa fa-exclamation-triangle me-2"></i>${message}
            </div>
        `;
        this.showResults();
    }

    showResults() {
        this.resultsContainer.style.display = 'block';
    }

    hideResults() {
        this.resultsContainer.style.display = 'none';
        this.selectedIndex = -1;
    }

    destroy() {
        if (this.resultsContainer && this.resultsContainer.parentElement) {
            this.resultsContainer.parentElement.removeChild(this.resultsContainer);
        }
    }
}

/**
 * Inicializar autocompletado en todos los campos de búsqueda
 */
function initAutocomplete() {
    // Campo de búsqueda en el hero (¿Dónde quieres vivir?)
    const heroSearchInput = document.getElementById('homepage-search-input');

    // Inicializar autocompletado en el input de la homepage
    if (heroSearchInput) {
        new BohioAutocomplete(heroSearchInput, {
            context: 'public',
            subdivision: 'all',
            minChars: 2,
            onSelect: (result) => {
                // Al seleccionar, actualizar el formulario y enviarlo
                let params = new URLSearchParams();

                switch (result.type) {
                    case 'city':
                        params.set('city_id', result.city_id);
                        break;
                    case 'region':
                        params.set('region_id', result.region_id);
                        break;
                    case 'project':
                        params.set('project_id', result.project_id);
                        break;
                    case 'property':
                        window.location.href = `/property/${result.property_id}`;
                        return;
                }

                // Agregar tipo de servicio actual
                const serviceType = document.getElementById('selectedServiceType');
                if (serviceType) {
                    params.set('type_service', serviceType.value);
                }

                // Redirigir
                window.location.href = `/properties?${params.toString()}`;
            }
        });

        console.log('Autocompletado inicializado en hero search');
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', initAutocomplete);

// Exportar clase y función de inicialización
export { BohioAutocomplete, initAutocomplete };

// También exportar globalmente para uso desde plantillas
window.BohioAutocomplete = BohioAutocomplete;
window.initBohioAutocomplete = initAutocomplete;

/**
 * BOHIO Real Estate - Search Bar Component
 * Barra de búsqueda con autocomplete de ubicaciones
 */

import { locationAutocomplete } from '../utils/api.js';
import { debounce } from '../utils/debounce.js';
import { $, createElement, show, hide } from '../utils/dom.js';
import { setUrlParams } from '../utils/url.js';

export class SearchBar {
    constructor(containerSelector) {
        this.container = $(containerSelector);
        this.searchInput = null;
        this.resultsDropdown = null;
        this.selectedLocations = [];
        this.init();
    }

    init() {
        this.render();
        this.attachEvents();
    }

    render() {
        this.searchInput = $('#location_search', this.container);
        this.resultsDropdown = $('#autocomplete_results', this.container);
        this.selectedContainer = $('#selected_locations', this.container);
    }

    attachEvents() {
        if (!this.searchInput) return;

        const debouncedSearch = debounce(async (term) => {
            await this.performSearch(term);
        }, 300);

        this.searchInput.addEventListener('input', (e) => {
            const term = e.target.value.trim();

            if (term.length < 2) {
                hide(this.resultsDropdown);
                return;
            }

            debouncedSearch(term);
        });

        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                hide(this.resultsDropdown);
            }
        });
    }

    async performSearch(term) {
        try {
            const result = await locationAutocomplete(term);

            if (result.results && result.results.length > 0) {
                this.renderResults(result.results, term);
                show(this.resultsDropdown);
            } else {
                this.resultsDropdown.innerHTML = '<div class="dropdown-item text-muted">No se encontraron resultados</div>';
                show(this.resultsDropdown);
            }
        } catch (error) {
            console.error('Error en búsqueda:', error);
            hide(this.resultsDropdown);
        }
    }

    renderResults(results, term) {
        this.resultsDropdown.innerHTML = '';
        let currentLevel = 0;

        results.forEach(item => {
            if (item.level !== currentLevel) {
                currentLevel = item.level;
                const levelName = item.level === 1 ? 'Departamentos' :
                                 item.level === 2 ? 'Ciudades' : 'Barrios';

                const header = createElement('div', {
                    className: 'dropdown-header'
                }, [levelName]);

                this.resultsDropdown.appendChild(header);
            }

            const highlightedDisplay = this.highlightMatch(item.display, term);
            const icon = item.type === 'state' ? 'map' :
                        item.type === 'city' ? 'building' : 'map-marker';

            const resultItem = createElement('a', {
                className: 'dropdown-item location-item',
                href: '#',
                onClick: (e) => {
                    e.preventDefault();
                    this.selectLocation(item);
                }
            });

            resultItem.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <div>${highlightedDisplay}</div>
                        <small class="text-muted">${item.subtitle}</small>
                    </div>
                    <i class="fa fa-${icon}"></i>
                </div>
            `;

            this.resultsDropdown.appendChild(resultItem);
        });
    }

    highlightMatch(text, term) {
        const regex = new RegExp(`(${term})`, 'gi');
        return text.replace(regex, '<strong>$1</strong>');
    }

    selectLocation(location) {
        const exists = this.selectedLocations.find(loc => loc.id === location.id);

        if (!exists) {
            this.selectedLocations.push(location);
            this.renderSelectedLocations();
            this.updateURL();
        }

        this.searchInput.value = '';
        hide(this.resultsDropdown);
    }

    removeLocation(locationId) {
        this.selectedLocations = this.selectedLocations.filter(loc => loc.id !== locationId);
        this.renderSelectedLocations();
        this.updateURL();
    }

    renderSelectedLocations() {
        if (!this.selectedContainer) return;

        this.selectedContainer.innerHTML = '';

        this.selectedLocations.forEach(loc => {
            const badge = createElement('span', {
                className: 'badge bg-primary me-2 mb-2 p-2'
            });

            badge.innerHTML = `
                ${loc.display}
                <button type="button" class="btn-close btn-close-white ms-2" aria-label="Remove"></button>
            `;

            const closeBtn = badge.querySelector('.btn-close');
            closeBtn.addEventListener('click', () => this.removeLocation(loc.id));

            this.selectedContainer.appendChild(badge);
        });
    }

    updateURL() {
        const params = {};

        this.selectedLocations.forEach(loc => {
            if (loc.type === 'state') {
                params.state_id = loc.id;
            } else if (loc.type === 'city') {
                params.city_id = loc.id;
                if (loc.state_id) params.state_id = loc.state_id;
            } else if (loc.type === 'region') {
                params.region_id = loc.id;
                if (loc.city_id) params.city_id = loc.city_id;
                if (loc.state_id) params.state_id = loc.state_id;
            }
        });

        const queryString = new URLSearchParams(params).toString();
        const newUrl = queryString ? `/properties?${queryString}` : '/properties';

        window.location.href = newUrl;
    }
}
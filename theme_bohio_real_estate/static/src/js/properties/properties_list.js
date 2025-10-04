/**
 * BOHIO Real Estate - Properties List Page
 * Página de listado de propiedades con filtros
 */

import { searchProperties } from '../utils/api.js';
import { PropertyCard } from './property_card.js';
import { SearchBar } from '../search/search_bar.js';
import { $, $$ } from '../utils/dom.js';
import { getUrlParams, setUrlParams } from '../utils/url.js';

class PropertiesListPage {
    constructor() {
        this.propertiesContainer = $('#properties-list');
        this.filters = getUrlParams();
        this.currentPage = parseInt(this.filters.page || 1);
        this.searchBar = null;
        this.init();
    }

    async init() {
        this.initSearchBar();
        this.initFilters();
        await this.loadProperties();
    }

    initSearchBar() {
        const searchContainer = $('#search-bar-container');
        if (searchContainer) {
            this.searchBar = new SearchBar('#search-bar-container');
        }
    }

    initFilters() {
        const filterInputs = $$('[data-filter]');

        filterInputs.forEach(input => {
            input.addEventListener('change', () => {
                this.applyFilters();
            });
        });

        const priceRange = $('#price-range');
        if (priceRange) {
            priceRange.addEventListener('change', () => {
                this.applyFilters();
            });
        }
    }

    applyFilters() {
        const filterInputs = $$('[data-filter]');
        const newFilters = {};

        filterInputs.forEach(input => {
            const filterName = input.dataset.filter;
            const value = input.value;

            if (value) {
                newFilters[filterName] = value;
            }
        });

        setUrlParams(newFilters);
        this.filters = newFilters;
        this.loadProperties();
    }

    async loadProperties() {
        if (!this.propertiesContainer) return;

        this.showLoading();

        try {
            const result = await searchProperties(this.filters, this.currentPage, 12);

            if (result.properties && result.properties.length > 0) {
                this.renderProperties(result.properties);
                this.renderPagination(result);
            } else {
                this.showNoResults();
            }
        } catch (error) {
            console.error('Error cargando propiedades:', error);
            this.showError();
        }
    }

    renderProperties(properties) {
        this.propertiesContainer.innerHTML = '';

        properties.forEach(property => {
            const card = new PropertyCard(property);
            this.propertiesContainer.appendChild(card.render());
        });
    }

    renderPagination(result) {
        const paginationContainer = $('#pagination');
        if (!paginationContainer) return;

        paginationContainer.innerHTML = '';

        for (let i = 1; i <= result.pages; i++) {
            const pageBtn = document.createElement('button');
            pageBtn.className = `btn ${i === this.currentPage ? 'btn-primary' : 'btn-outline-primary'} mx-1`;
            pageBtn.textContent = i;

            pageBtn.addEventListener('click', () => {
                this.currentPage = i;
                setUrlParams({ ...this.filters, page: i });
                this.loadProperties();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });

            paginationContainer.appendChild(pageBtn);
        }
    }

    showLoading() {
        this.propertiesContainer.innerHTML = '<div class="text-center py-5"><div class="spinner-border"></div></div>';
    }

    showNoResults() {
        this.propertiesContainer.innerHTML = '<div class="alert alert-info">No se encontraron propiedades con los filtros seleccionados.</div>';
    }

    showError() {
        this.propertiesContainer.innerHTML = '<div class="alert alert-danger">Error al cargar las propiedades. Intente nuevamente.</div>';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new PropertiesListPage();
});
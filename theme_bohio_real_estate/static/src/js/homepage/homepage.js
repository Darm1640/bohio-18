/**
 * BOHIO Real Estate - Homepage
 * Lógica específica de la página de inicio
 */

import { searchProperties } from '../utils/api.js';
import { PropertyCard } from '../properties/property_card.js';
import { $ } from '../utils/dom.js';

class Homepage {
    constructor() {
        this.featuredContainer = $('#featured-properties');
        this.init();
    }

    async init() {
        await this.loadFeaturedProperties();
        this.initSearchButton();
    }

    async loadFeaturedProperties() {
        if (!this.featuredContainer) return;

        try {
            const result = await searchProperties({}, 1, 6);

            if (result.properties && result.properties.length > 0) {
                this.renderProperties(result.properties);
            }
        } catch (error) {
            console.error('Error cargando propiedades destacadas:', error);
        }
    }

    renderProperties(properties) {
        this.featuredContainer.innerHTML = '';

        properties.forEach(property => {
            const card = new PropertyCard(property);
            this.featuredContainer.appendChild(card.render());
        });
    }

    initSearchButton() {
        const searchBtn = $('#search-properties-btn');

        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                window.location.href = '/properties';
            });
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new Homepage();
});
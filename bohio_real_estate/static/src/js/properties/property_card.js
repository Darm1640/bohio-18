/**
 * BOHIO Real Estate - Property Card Component
 * Componente para tarjetas de propiedades
 */

import { formatCurrency, formatArea } from '../utils/formatters.js';
import { createElement } from '../utils/dom.js';

export class PropertyCard {
    constructor(property) {
        this.property = property;
    }

    render() {
        const card = createElement('div', {
            className: 'property-card col-md-4 mb-4'
        });

        const price = this.property.sale_price || this.property.rental_price || 0;
        const priceLabel = this.property.sale_price ? 'Venta' : 'Arriendo';

        card.innerHTML = `
            <div class="card h-100 shadow-sm">
                <img src="${this.property.image_url}" class="card-img-top" alt="${this.property.name}">
                <div class="card-body">
                    <span class="badge bg-primary mb-2">${this.property.property_type_name || ''}</span>
                    <h5 class="card-title">${this.property.name}</h5>
                    <p class="text-muted small">
                        <i class="fa fa-map-marker"></i>
                        ${this.property.region || ''}, ${this.property.city || ''}
                    </p>
                    <div class="property-features mb-3">
                        ${this.renderFeatures()}
                    </div>
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <small class="text-muted">${priceLabel}</small>
                            <h4 class="mb-0">${formatCurrency(price, this.property.currency)}</h4>
                        </div>
                        <a href="${this.property.url}" class="btn btn-outline-primary">Ver más</a>
                    </div>
                </div>
            </div>
        `;

        return card;
    }

    renderFeatures() {
        const features = [];

        if (this.property.bedrooms) {
            features.push(`<span><i class="fa fa-bed"></i> ${this.property.bedrooms}</span>`);
        }

        if (this.property.bathrooms) {
            features.push(`<span><i class="fa fa-bath"></i> ${this.property.bathrooms}</span>`);
        }

        if (this.property.area) {
            features.push(`<span><i class="fa fa-ruler-combined"></i> ${formatArea(this.property.area, this.property.area_unit)}</span>`);
        }

        if (this.property.parking) {
            features.push(`<span><i class="fa fa-car"></i> ${this.property.parking}</span>`);
        }

        return features.join(' • ');
    }
}
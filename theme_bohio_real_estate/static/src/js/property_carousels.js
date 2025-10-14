/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import { rpc } from "@web/core/network/rpc";

// Importar utilidades centralizadas
import { formatPrice, getPriceLabel, formatLocation, formatArea } from './utils/formatters';
import { PLACEHOLDER_IMAGE, CAROUSEL_INTERVAL } from './utils/constants';
import { createElement, createLink } from './utils/dom_helpers';

/**
 * BOHIO Property Carousels Widget
 * Widget de Odoo 18 para carruseles dinámicos de propiedades
 * Sigue el patrón PublicWidget con mejores prácticas
 * REFACTORIZADO: PublicWidget pattern + createElement helper + utilidades centralizadas
 */
publicWidget.registry.PropertyCarouselWidget = publicWidget.Widget.extend({
    selector: '.property-carousel-container',
    events: {},

    /**
     * @override
     */
    start() {
        this._super(...arguments);

        // Obtener configuración del data attribute
        this.carouselType = this.$el.data('carousel-type');
        this.carouselId = this.$el.attr('id');

        if (!this.carouselType) {
            console.warn('[CAROUSEL WIDGET] No carousel-type specified');
            return Promise.resolve();
        }

        console.log(`[CAROUSEL WIDGET] Inicializando carrusel ${this.carouselId} tipo: ${this.carouselType}`);

        // Inicializar carrusel
        return this._loadAndRenderCarousel();
    },

    /**
     * @override
     */
    destroy() {
        // Cleanup del carrusel Bootstrap
        if (this.carouselInstance) {
            this.carouselInstance.dispose();
            this.carouselInstance = null;
        }

        this._super(...arguments);
    },

    /**
     * Cargar y renderizar el carrusel
     * @private
     */
    async _loadAndRenderCarousel() {
        try {
            // Cargar propiedades
            await this._loadProperties();

            // Renderizar carrusel
            this._renderCarousel();

            // Inicializar Bootstrap Carousel
            this._initBootstrapCarousel();
        } catch (error) {
            console.error('[CAROUSEL WIDGET] Error:', error);
            this._renderError();
        }
    },

    /**
     * Cargar propiedades desde el servidor usando endpoints optimizados
     * @private
     */
    async _loadProperties() {
        console.log(`[CAROUSEL WIDGET] Cargando propiedades tipo: ${this.carouselType}`);

        // Mapear tipo de carrusel a endpoint específico optimizado
        const endpointMap = {
            'rent': '/api/properties/arriendo',
            'sale': '/api/properties/venta-usada',
            'projects': '/api/properties/proyectos'
        };

        const endpoint = endpointMap[this.carouselType];
        if (!endpoint) {
            throw new Error(`Tipo de carrusel no válido: ${this.carouselType}`);
        }

        const result = await rpc(endpoint, {
            limit: 12
        });

        if (result.success && result.properties) {
            this.properties = result.properties;
            console.log(`[CAROUSEL WIDGET] ${this.properties.length} propiedades cargadas para ${this.carouselType} (de ${result.total} total)`);
        } else {
            throw new Error(result.error || 'No properties returned');
        }
    }

    /**
     * Renderizar el carrusel en el DOM usando createElement helper
     * @private
     */
    _renderCarousel() {
        // Limpiar contenedor
        this.el.innerHTML = '';

        if (!this.properties || this.properties.length === 0) {
            this._renderEmptyState();
            return;
        }

        // Agrupar propiedades en grupos de 4 para el carrusel
        const itemsPerSlide = 4;
        const slides = [];
        for (let i = 0; i < this.properties.length; i += itemsPerSlide) {
            slides.push(this.properties.slice(i, i + itemsPerSlide));
        }

        // Crear estructura del carrusel
        const carouselId = `${this.carouselId}-carousel`;
        const carouselDiv = this._createCarouselStructure(carouselId, slides);

        this.el.appendChild(carouselDiv);
    }

    /**
     * Crear estructura del carrusel completa usando createElement helper
     * @private
     */
    _createCarouselStructure(carouselId, slides) {
        const carousel = createElement('div', {
            id: carouselId,
            className: 'carousel slide',
            attributes: { 'data-bs-ride': 'carousel' }
        });

        // Inner carousel
        const carouselInner = createElement('div', 'carousel-inner');

        slides.forEach((slideProperties, index) => {
            const carouselItem = createElement('div',
                `carousel-item ${index === 0 ? 'active' : ''}`
            );

            const row = createElement('div', 'row g-4');

            slideProperties.forEach(property => {
                const propertyCard = this._createPropertyCardElement(property);
                row.appendChild(propertyCard);
            });

            carouselItem.appendChild(row);
            carouselInner.appendChild(carouselItem);
        });

        carousel.appendChild(carouselInner);

        // Controles
        carousel.appendChild(this._createCarouselControl('prev', carouselId));
        carousel.appendChild(this._createCarouselControl('next', carouselId));

        // Indicadores
        carousel.appendChild(this._createCarouselIndicators(carouselId, slides.length));

        return carousel;
    }

    /**
     * Crear control de carrusel (prev/next)
     * @private
     */
    _createCarouselControl(direction, carouselId) {
        const button = createElement('button', {
            className: `carousel-control-${direction}`,
            attributes: {
                type: 'button',
                'data-bs-target': `#${carouselId}`,
                'data-bs-slide': direction
            }
        });

        const icon = createElement('span', {
            className: `carousel-control-${direction}-icon`,
            attributes: { 'aria-hidden': 'true' }
        });

        const visuallyHidden = createElement('span', {
            className: 'visually-hidden',
            text: direction === 'prev' ? 'Anterior' : 'Siguiente'
        });

        button.appendChild(icon);
        button.appendChild(visuallyHidden);

        return button;
    }

    /**
     * Crear indicadores del carrusel
     * @private
     */
    _createCarouselIndicators(carouselId, slideCount) {
        const indicators = createElement('div', 'carousel-indicators');

        for (let i = 0; i < slideCount; i++) {
            const button = createElement('button', {
                className: i === 0 ? 'active' : '',
                attributes: {
                    type: 'button',
                    'data-bs-target': `#${carouselId}`,
                    'data-bs-slide-to': i.toString(),
                    'aria-label': `Slide ${i + 1}`,
                    ...(i === 0 && { 'aria-current': 'true' })
                }
            });

            indicators.appendChild(button);
        }

        return indicators;
    }

    /**
     * Crear elemento de tarjeta de propiedad usando createElement helper
     * @private
     */
    _createPropertyCardElement(property) {
        // Preparar datos usando formatters centralizados
        const imageUrl = property.image_url || PLACEHOLDER_IMAGE;
        const location = formatLocation(property);
        const priceFormatted = formatPrice(property.price);
        const priceLabel = getPriceLabel(property);

        // Crear estructura con createElement helper
        const colDiv = createElement('div', 'col-md-3');

        const card = createElement('div',
            'card h-100 shadow-sm border-0 bohio-property-card position-relative'
        );

        // Badge de proyecto
        if (property.project_id) {
            card.appendChild(this._createProjectBadge(property));
        }

        // Imagen
        card.appendChild(this._createPropertyImage(imageUrl, property.name));

        // Card body
        const cardBody = createElement('div', 'card-body d-flex flex-column');

        // Título
        cardBody.appendChild(this._createPropertyTitle(property.name));

        // Ubicación
        cardBody.appendChild(this._createPropertyLocation(location));

        // Características
        cardBody.appendChild(this._createPropertyFeatures(property));

        // Precio
        cardBody.appendChild(this._createPropertyPrice(priceLabel, priceFormatted));

        // Botón
        cardBody.appendChild(this._createDetailsButton(property.url));

        card.appendChild(cardBody);
        colDiv.appendChild(card);

        return colDiv;
    }

    /**
     * Crear badge de proyecto
     * @private
     */
    _createProjectBadge(property) {
        const div = createElement('div', 'position-absolute top-0 end-0 m-2');

        const link = createLink({
            href: `/proyecto/${property.project_id}`,
            className: 'badge bg-danger text-white text-decoration-none property-project-badge',
            children: [
                createElement('i', 'bi bi-building me-1'),
                document.createTextNode(property.project_name)
            ]
        });

        div.appendChild(link);
        return div;
    }

    /**
     * Crear imagen de propiedad
     * @private
     */
    _createPropertyImage(imageUrl, name) {
        const img = createElement('img', {
            className: 'card-img-top property-card-image',
            attributes: {
                src: imageUrl,
                alt: name,
                loading: 'lazy',
                onerror: `this.src='${PLACEHOLDER_IMAGE}'`
            }
        });

        return img;
    }

    /**
     * Crear título de propiedad
     * @private
     */
    _createPropertyTitle(name) {
        return createElement('h5', {
            className: 'card-title text-truncate',
            text: name,
            attributes: { title: name }
        });
    }

    /**
     * Crear ubicación de propiedad
     * @private
     */
    _createPropertyLocation(location) {
        const p = createElement('p', {
            className: 'text-muted small mb-2',
            children: [
                createElement('i', 'bi bi-geo-alt-fill me-1'),
                document.createTextNode(location)
            ]
        });

        return p;
    }

    /**
     * Crear características de propiedad (área, habitaciones, baños)
     * @private
     */
    _createPropertyFeatures(property) {
        const div = createElement('div',
            'd-flex justify-content-between mb-2 text-muted small property-features'
        );

        if (property.area > 0) {
            const areaFormatted = formatArea(property.area);
            div.appendChild(this._createFeature('bi-rulers', areaFormatted));
        }
        if (property.bedrooms > 0) {
            div.appendChild(this._createFeature('bi-bed', property.bedrooms.toString()));
        }
        if (property.bathrooms > 0) {
            div.appendChild(this._createFeature('bi-droplet', property.bathrooms.toString()));
        }

        return div;
    }

    /**
     * Crear característica individual
     * @private
     */
    _createFeature(iconClass, text) {
        return createElement('span', {
            children: [
                createElement('i', `bi ${iconClass} me-1`),
                document.createTextNode(text)
            ]
        });
    }

    /**
     * Crear sección de precio
     * @private
     */
    _createPropertyPrice(label, formatted) {
        const div = createElement('div', {
            className: 'mb-2',
            children: [
                createElement('small', {
                    className: 'text-muted',
                    text: label
                }),
                createElement('h4', {
                    className: 'text-danger mb-0',
                    text: formatted
                })
            ]
        });

        return div;
    }

    /**
     * Crear botón de detalles
     * @private
     */
    _createDetailsButton(url) {
        return createLink({
            href: url,
            className: 'btn btn-outline-danger w-100 mt-auto',
            children: [
                createElement('i', 'bi bi-eye me-1'),
                document.createTextNode('Ver detalles')
            ]
        });
    }

    /**
     * Renderizar estado vacío
     * @private
     */
    _renderEmptyState() {
        const div = createElement('div', {
            className: 'text-center py-5',
            children: [
                createElement('i', 'bi bi-house-fill fa-3x text-muted mb-3'),
                createElement('p', {
                    className: 'text-muted',
                    text: 'No hay propiedades disponibles en este momento'
                })
            ]
        });

        this.el.appendChild(div);
    }

    /**
     * Renderizar error
     * @private
     */
    _renderError() {
        const div = createElement('div', {
            className: 'alert alert-danger',
            children: [
                createElement('i', 'bi bi-exclamation-triangle me-2'),
                document.createTextNode('Error al cargar las propiedades. Por favor, intente más tarde.')
            ]
        });

        this.el.appendChild(div);
    }

    /**
     * Inicializar Bootstrap Carousel con opciones
     * @private
     */
    _initBootstrapCarousel() {
        const carouselId = `${this.carouselId}-carousel`;
        const carouselEl = document.getElementById(carouselId);

        if (carouselEl && typeof bootstrap !== 'undefined') {
            this.carouselInstance = new bootstrap.Carousel(carouselEl, {
                interval: CAROUSEL_INTERVAL,  // Desde constants.js
                wrap: true,
                keyboard: true,
                pause: 'hover'
            });

            console.log(`[CAROUSEL WIDGET] Bootstrap carousel inicializado para ${carouselId}`);
        }
    }
});

/**
 * Exportar el widget para que pueda ser usado desde otros módulos si es necesario
 */
export default publicWidget.registry.PropertyCarouselWidget;

/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import { rpc } from "@web/core/network/rpc";

// Importar utilidades centralizadas
import { CAROUSEL_INTERVAL } from './utils/constants';
import { createElement } from './utils/dom_helpers';
import PropertyCardEnhanced from './components/property_card_enhanced';

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
    },

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
    },

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
    },

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
    },

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
    },

    /**
     * Crear elemento de tarjeta de propiedad usando la clase mejorada
     * @private
     */
    _createPropertyCardElement(property) {
        // Usar la nueva clase PropertyCardEnhanced para crear tarjetas mejoradas
        const enhancedCard = new PropertyCardEnhanced(property, {
            showActions: true,
            showFloatingButtons: true,
            enableCompare: true,
            enableWishlist: true,
            enableShare: true
        });

        // Crear el contenedor de columna para el carrusel
        const colDiv = createElement('div', 'col-md-3');

        // Crear la tarjeta mejorada y agregarla al contenedor
        const card = enhancedCard.create();
        colDiv.appendChild(card);

        return colDiv;
    },

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
    },

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
    },

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

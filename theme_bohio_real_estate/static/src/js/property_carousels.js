/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

// Importar utilidades centralizadas
import { formatPrice, getPriceLabel, formatLocation, formatArea } from './utils/formatters';
import { PLACEHOLDER_IMAGE, CAROUSEL_INTERVAL } from './utils/constants';

/**
 * BOHIO Property Carousels - Sistema de Carruseles Dinámicos
 * Carga propiedades desde la base de datos para Venta, Renta y Proyectos
 * REFACTORIZADO: Sin HTML strings, usa createElement + utilidades centralizadas
 */

class PropertyCarousel {
    constructor(containerId, carouselType) {
        this.containerId = containerId;
        this.carouselType = carouselType;
        this.container = document.getElementById(containerId);
        this.carouselInstance = null;
        this.properties = [];
    }

    /**
     * Inicializar el carrusel
     */
    async init() {
        if (!this.container) {
            console.warn(`[CAROUSEL] Contenedor ${this.containerId} no encontrado`);
            return;
        }

        console.log(`[CAROUSEL] Inicializando carrusel ${this.containerId}`);

        // Cargar propiedades
        await this.loadProperties();

        // Renderizar carrusel
        this.render();

        // Inicializar Bootstrap Carousel
        this.initBootstrapCarousel();
    }

    /**
     * Cargar propiedades desde el servidor usando endpoints optimizados
     */
    async loadProperties() {
        try {
            console.log(`[CAROUSEL] Cargando propiedades tipo: ${this.carouselType}`);

            // Mapear tipo de carrusel a endpoint específico optimizado
            const endpointMap = {
                'rent': '/api/properties/arriendo',
                'sale': '/api/properties/venta-usada',
                'projects': '/api/properties/proyectos'
            };

            const endpoint = endpointMap[this.carouselType];
            if (!endpoint) {
                console.error(`[CAROUSEL] Tipo de carrusel no válido: ${this.carouselType}`);
                return;
            }

            const result = await rpc(endpoint, {
                limit: 12
            });

            if (result.success && result.properties) {
                this.properties = result.properties;
                console.log(`[CAROUSEL] ${this.properties.length} propiedades cargadas para ${this.carouselType} (de ${result.total} total)`);
            } else {
                console.error('[CAROUSEL] Error:', result.error || 'No properties returned');
            }
        } catch (error) {
            console.error('[CAROUSEL] Error cargando propiedades:', error);
        }
    }

    /**
     * Renderizar el carrusel en el DOM usando createElement (sin HTML strings)
     */
    render() {
        // Limpiar contenedor
        this.container.innerHTML = '';

        if (this.properties.length === 0) {
            this.renderEmptyState();
            return;
        }

        // Agrupar propiedades en grupos de 4 para el carrusel
        const itemsPerSlide = 4;
        const slides = [];
        for (let i = 0; i < this.properties.length; i += itemsPerSlide) {
            slides.push(this.properties.slice(i, i + itemsPerSlide));
        }

        // Crear estructura del carrusel
        const carouselId = `${this.containerId}-carousel`;
        const carouselDiv = this.createCarouselStructure(carouselId, slides);

        this.container.appendChild(carouselDiv);
    }

    /**
     * Crear estructura del carrusel completa usando createElement
     */
    createCarouselStructure(carouselId, slides) {
        const carousel = document.createElement('div');
        carousel.id = carouselId;
        carousel.className = 'carousel slide';
        carousel.setAttribute('data-bs-ride', 'carousel');

        // Inner carousel
        const carouselInner = document.createElement('div');
        carouselInner.className = 'carousel-inner';

        slides.forEach((slideProperties, index) => {
            const carouselItem = document.createElement('div');
            carouselItem.className = `carousel-item ${index === 0 ? 'active' : ''}`;

            const row = document.createElement('div');
            row.className = 'row g-4';

            slideProperties.forEach(property => {
                const propertyCard = this.createPropertyCardElement(property);
                row.appendChild(propertyCard);
            });

            carouselItem.appendChild(row);
            carouselInner.appendChild(carouselItem);
        });

        carousel.appendChild(carouselInner);

        // Controles
        carousel.appendChild(this.createCarouselControl('prev', carouselId));
        carousel.appendChild(this.createCarouselControl('next', carouselId));

        // Indicadores
        carousel.appendChild(this.createCarouselIndicators(carouselId, slides.length));

        return carousel;
    }

    /**
     * Crear control de carrusel (prev/next)
     */
    createCarouselControl(direction, carouselId) {
        const button = document.createElement('button');
        button.className = `carousel-control-${direction}`;
        button.type = 'button';
        button.setAttribute('data-bs-target', `#${carouselId}`);
        button.setAttribute('data-bs-slide', direction);

        const icon = document.createElement('span');
        icon.className = `carousel-control-${direction}-icon`;
        icon.setAttribute('aria-hidden', 'true');

        const visuallyHidden = document.createElement('span');
        visuallyHidden.className = 'visually-hidden';
        visuallyHidden.textContent = direction === 'prev' ? 'Anterior' : 'Siguiente';

        button.appendChild(icon);
        button.appendChild(visuallyHidden);

        return button;
    }

    /**
     * Crear indicadores del carrusel
     */
    createCarouselIndicators(carouselId, slideCount) {
        const indicators = document.createElement('div');
        indicators.className = 'carousel-indicators';

        for (let i = 0; i < slideCount; i++) {
            const button = document.createElement('button');
            button.type = 'button';
            button.setAttribute('data-bs-target', `#${carouselId}`);
            button.setAttribute('data-bs-slide-to', i.toString());
            button.setAttribute('aria-label', `Slide ${i + 1}`);

            if (i === 0) {
                button.className = 'active';
                button.setAttribute('aria-current', 'true');
            }

            indicators.appendChild(button);
        }

        return indicators;
    }

    /**
     * Crear elemento de tarjeta de propiedad usando createElement (sin HTML strings)
     */
    createPropertyCardElement(property) {
        // Preparar datos usando formatters centralizados
        const imageUrl = property.image_url || PLACEHOLDER_IMAGE;
        const location = formatLocation(property);
        const priceFormatted = formatPrice(property.price);
        const priceLabel = getPriceLabel(property);

        // Crear estructura
        const colDiv = document.createElement('div');
        colDiv.className = 'col-md-3';

        const card = document.createElement('div');
        card.className = 'card h-100 shadow-sm border-0 bohio-property-card position-relative';

        // Badge de proyecto
        if (property.project_id) {
            card.appendChild(this.createProjectBadge(property));
        }

        // Imagen
        card.appendChild(this.createPropertyImage(imageUrl, property.name));

        // Card body
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body d-flex flex-column';

        // Título
        cardBody.appendChild(this.createPropertyTitle(property.name));

        // Ubicación
        cardBody.appendChild(this.createPropertyLocation(location));

        // Características
        cardBody.appendChild(this.createPropertyFeatures(property));

        // Precio
        cardBody.appendChild(this.createPropertyPrice(priceLabel, priceFormatted));

        // Botón
        cardBody.appendChild(this.createDetailsButton(property.url));

        card.appendChild(cardBody);
        colDiv.appendChild(card);

        return colDiv;
    }

    /**
     * Crear badge de proyecto
     */
    createProjectBadge(property) {
        const div = document.createElement('div');
        div.className = 'position-absolute top-0 end-0 m-2';

        const a = document.createElement('a');
        a.href = `/proyecto/${property.project_id}`;
        a.className = 'badge bg-danger text-white text-decoration-none property-project-badge';

        const icon = document.createElement('i');
        icon.className = 'bi bi-building me-1';

        a.appendChild(icon);
        a.appendChild(document.createTextNode(property.project_name));
        div.appendChild(a);

        return div;
    }

    /**
     * Crear imagen de propiedad
     */
    createPropertyImage(imageUrl, name) {
        const img = document.createElement('img');
        img.src = imageUrl;
        img.className = 'card-img-top property-card-image';
        img.alt = name;
        img.loading = 'lazy';
        img.onerror = function() {
            this.src = PLACEHOLDER_IMAGE;
        };

        return img;
    }

    /**
     * Crear título de propiedad
     */
    createPropertyTitle(name) {
        const h5 = document.createElement('h5');
        h5.className = 'card-title text-truncate';
        h5.title = name;
        h5.textContent = name;

        return h5;
    }

    /**
     * Crear ubicación de propiedad
     */
    createPropertyLocation(location) {
        const p = document.createElement('p');
        p.className = 'text-muted small mb-2';

        const icon = document.createElement('i');
        icon.className = 'bi bi-geo-alt-fill me-1';

        p.appendChild(icon);
        p.appendChild(document.createTextNode(location));

        return p;
    }

    /**
     * Crear características de propiedad (área, habitaciones, baños)
     */
    createPropertyFeatures(property) {
        const div = document.createElement('div');
        div.className = 'd-flex justify-content-between mb-2 text-muted small property-features';

        if (property.area > 0) {
            const areaFormatted = formatArea(property.area);
            div.appendChild(this.createFeature('bi-rulers', areaFormatted));
        }
        if (property.bedrooms > 0) {
            div.appendChild(this.createFeature('bi-bed', property.bedrooms.toString()));
        }
        if (property.bathrooms > 0) {
            div.appendChild(this.createFeature('bi-droplet', property.bathrooms.toString()));
        }

        return div;
    }

    /**
     * Crear característica individual
     */
    createFeature(iconClass, text) {
        const span = document.createElement('span');

        const icon = document.createElement('i');
        icon.className = `bi ${iconClass} me-1`;

        span.appendChild(icon);
        span.appendChild(document.createTextNode(text));

        return span;
    }

    /**
     * Crear sección de precio
     */
    createPropertyPrice(label, formatted) {
        const div = document.createElement('div');
        div.className = 'mb-2';

        const small = document.createElement('small');
        small.className = 'text-muted';
        small.textContent = label;

        const h4 = document.createElement('h4');
        h4.className = 'text-danger mb-0';
        h4.textContent = formatted;

        div.appendChild(small);
        div.appendChild(h4);

        return div;
    }

    /**
     * Crear botón de detalles
     */
    createDetailsButton(url) {
        const a = document.createElement('a');
        a.href = url;
        a.className = 'btn btn-outline-danger w-100 mt-auto';

        const icon = document.createElement('i');
        icon.className = 'bi bi-eye me-1';

        a.appendChild(icon);
        a.appendChild(document.createTextNode('Ver detalles'));

        return a;
    }

    /**
     * Renderizar estado vacío
     */
    renderEmptyState() {
        const div = document.createElement('div');
        div.className = 'text-center py-5';

        const icon = document.createElement('i');
        icon.className = 'bi bi-house-fill fa-3x text-muted mb-3';

        const p = document.createElement('p');
        p.className = 'text-muted';
        p.textContent = 'No hay propiedades disponibles en este momento';

        div.appendChild(icon);
        div.appendChild(p);

        this.container.appendChild(div);
    }

    /**
     * Inicializar Bootstrap Carousel con opciones
     */
    initBootstrapCarousel() {
        const carouselId = `${this.containerId}-carousel`;
        const carouselEl = document.getElementById(carouselId);

        if (carouselEl && typeof bootstrap !== 'undefined') {
            this.carouselInstance = new bootstrap.Carousel(carouselEl, {
                interval: CAROUSEL_INTERVAL,  // Desde constants.js
                wrap: true,
                keyboard: true,
                pause: 'hover'
            });

            console.log(`[CAROUSEL] Bootstrap carousel inicializado para ${carouselId}`);
        }
    }
}

/**
 * Inicializar todos los carruseles al cargar la página
 */
function initPropertyCarousels() {
    console.log('=== Inicializando carruseles de propiedades ===');

    // Carrusel de propiedades en arriendo
    const rentCarousel = new PropertyCarousel('carousel-rent', 'rent');
    rentCarousel.init();

    // Carrusel de propiedades usadas en venta
    const saleCarousel = new PropertyCarousel('carousel-sale', 'sale');
    saleCarousel.init();

    // Carrusel de proyectos/propiedades nuevas
    const projectsCarousel = new PropertyCarousel('carousel-projects', 'projects');
    projectsCarousel.init();
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', initPropertyCarousels);

// Exportar clase y función de inicialización
export { PropertyCarousel, initPropertyCarousels };

// También exportar globalmente para uso desde plantillas
window.PropertyCarousel = PropertyCarousel;
window.initPropertyCarousels = initPropertyCarousels;

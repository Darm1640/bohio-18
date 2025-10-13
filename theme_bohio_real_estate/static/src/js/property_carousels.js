/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

/**
 * BOHIO Property Carousels - Sistema de Carruseles Dinámicos
 * Carga propiedades desde la base de datos para Venta, Renta y Proyectos
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
     * Renderizar el carrusel en el DOM
     */
    render() {
        if (this.properties.length === 0) {
            this.container.innerHTML = `
                <div class="text-center py-5">
                    <i class="bi bi-house-fill fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No hay propiedades disponibles en este momento</p>
                </div>
            `;
            return;
        }

        // Agrupar propiedades en grupos de 4 para el carrusel
        const itemsPerSlide = 4;
        const slides = [];
        for (let i = 0; i < this.properties.length; i += itemsPerSlide) {
            slides.push(this.properties.slice(i, i + itemsPerSlide));
        }

        // Generar HTML del carrusel
        const carouselId = `${this.containerId}-carousel`;
        let carouselHTML = `
            <div id="${carouselId}" class="carousel slide" data-bs-ride="carousel">
                <div class="carousel-inner">
        `;

        slides.forEach((slideProperties, index) => {
            const activeClass = index === 0 ? 'active' : '';
            carouselHTML += `
                <div class="carousel-item ${activeClass}">
                    <div class="row g-4">
                        ${slideProperties.map(prop => this.createPropertyCard(prop)).join('')}
                    </div>
                </div>
            `;
        });

        carouselHTML += `
                </div>

                <!-- Controles del carrusel -->
                <button class="carousel-control-prev" type="button" data-bs-target="#${carouselId}" data-bs-slide="prev">
                    <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                    <span class="visually-hidden">Anterior</span>
                </button>
                <button class="carousel-control-next" type="button" data-bs-target="#${carouselId}" data-bs-slide="next">
                    <span class="carousel-control-next-icon" aria-hidden="true"></span>
                    <span class="visually-hidden">Siguiente</span>
                </button>

                <!-- Indicadores -->
                <div class="carousel-indicators">
                    ${slides.map((_, i) => `
                        <button type="button"
                                data-bs-target="#${carouselId}"
                                data-bs-slide-to="${i}"
                                ${i === 0 ? 'class="active" aria-current="true"' : ''}
                                aria-label="Slide ${i + 1}"></button>
                    `).join('')}
                </div>
            </div>
        `;

        this.container.innerHTML = carouselHTML;
    }

    /**
     * Crear tarjeta HTML de propiedad
     */
    createPropertyCard(property) {
        const imageUrl = property.image_url || '/theme_bohio_real_estate/static/src/img/placeholder.jpg';

        // Construir ubicación
        const location = property.neighborhood ?
            `${property.neighborhood}, ${property.city}` :
            `${property.city}${property.state ? ', ' + property.state : ''}`;

        // Formatear precio
        const priceFormatted = property.price ?
            new Intl.NumberFormat('es-CO', {
                style: 'currency',
                currency: 'COP',
                minimumFractionDigits: 0
            }).format(property.price) : 'Consultar';

        // Label de precio según tipo (type_service viene como label traducido desde API)
        // Valores posibles: "Venta", "Arriendo", "Venta y Arriendo", "Arriendo Vacacional"
        const isRental = property.type_service && property.type_service.includes('Arriendo');
        const priceLabel = isRental ? 'Arriendo/mes' : 'Venta';

        // Badge de proyecto si existe
        const projectBadge = property.project_id ? `
            <div class="position-absolute top-0 end-0 m-2">
                <a href="/proyecto/${property.project_id}"
                   class="badge bg-danger text-white text-decoration-none"
                   style="font-size: 0.7rem; padding: 0.4rem 0.6rem;">
                    <i class="bi bi-building me-1"></i>${property.project_name}
                </a>
            </div>
        ` : '';

        return `
            <div class="col-md-3">
                <div class="card h-100 shadow-sm border-0 bohio-property-card position-relative">
                    ${projectBadge}
                    <img src="${imageUrl}"
                         class="card-img-top"
                         alt="${property.name}"
                         style="height: 200px; object-fit: cover;"
                         loading="lazy"
                         onerror="this.src='/theme_bohio_real_estate/static/src/img/placeholder.jpg'"/>
                    <div class="card-body d-flex flex-column">
                        <h5 class="card-title text-truncate" title="${property.name}">
                            ${property.name}
                        </h5>
                        <p class="text-muted small mb-2">
                            <i class="bi bi-geo-alt-fill me-1"></i>${location}
                        </p>
                        <div class="d-flex justify-content-between mb-2 text-muted small">
                            ${property.area > 0 ? `<span><i class="bi bi-rulers me-1"></i>${property.area} m²</span>` : ''}
                            ${property.bedrooms > 0 ? `<span><i class="bi bi-bed me-1"></i>${property.bedrooms}</span>` : ''}
                            ${property.bathrooms > 0 ? `<span><i class="bi bi-droplet me-1"></i>${property.bathrooms}</span>` : ''}
                        </div>
                        <div class="mb-2">
                            <small class="text-muted">${priceLabel}</small>
                            <h4 class="text-danger mb-0">${priceFormatted}</h4>
                        </div>
                        <a href="${property.url}"
                           class="btn btn-outline-danger w-100 mt-auto">
                            <i class="bi bi-eye me-1"></i>Ver detalles
                        </a>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Inicializar Bootstrap Carousel con opciones
     */
    initBootstrapCarousel() {
        const carouselId = `${this.containerId}-carousel`;
        const carouselEl = document.getElementById(carouselId);

        if (carouselEl && typeof bootstrap !== 'undefined') {
            this.carouselInstance = new bootstrap.Carousel(carouselEl, {
                interval: 5000,  // 5 segundos entre slides
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

/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

/**
 * Property Carousel - Vanilla JS con RPC de Odoo 18
 */
class PropertyCarousel {
    constructor(containerId, type, limit = 12) {
        this.containerId = containerId;
        this.type = type;
        this.limit = limit;
        this.container = document.getElementById(containerId);
        this.properties = [];

        // Endpoints por tipo
        this.endpoints = {
            rent: "/api/properties/arriendo",
            sale: "/api/properties/venta-usada",
            projects: "/api/properties/proyectos",
        };
    }

    async init() {
        if (!this.container) {
            console.warn(`[PropertyCarousel] Contenedor #${this.containerId} no encontrado`);
            return;
        }

        console.log(`[PropertyCarousel] Inicializando carrusel ${this.type}...`);
        await this.loadProperties();
        this.render();
        this.initBootstrapCarousel();
        console.log(`[PropertyCarousel] ✅ Carrusel ${this.type} listo`);
    }

    async loadProperties() {
        try {
            const endpoint = this.endpoints[this.type];
            const result = await rpc(endpoint, { limit: this.limit });

            if (result?.success && Array.isArray(result.properties)) {
                this.properties = result.properties;
            } else {
                console.error(`[PropertyCarousel] Respuesta inválida:`, result);
                this.properties = [];
            }
        } catch (error) {
            console.error(`[PropertyCarousel] Error cargando propiedades:`, error);
            this.properties = [];
            this.showError(error.message);
        }
    }

    render() {
        if (!this.properties.length) {
            this.showEmpty();
            return;
        }

        const slides = this.createSlides();
        const carouselId = `carousel-${this.type}-inner`;

        this.container.innerHTML = `
            <div id="${carouselId}" class="carousel slide" data-bs-ride="carousel">
                <div class="carousel-inner">
                    ${slides.map((slide, index) => `
                        <div class="carousel-item ${index === 0 ? 'active' : ''}">
                            <div class="row g-4">
                                ${slide.map(prop => this.renderPropertyCard(prop)).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
                ${slides.length > 1 ? `
                    <button class="carousel-control-prev" type="button" data-bs-target="#${carouselId}" data-bs-slide="prev">
                        <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                        <span class="visually-hidden">Anterior</span>
                    </button>
                    <button class="carousel-control-next" type="button" data-bs-target="#${carouselId}" data-bs-slide="next">
                        <span class="carousel-control-next-icon" aria-hidden="true"></span>
                        <span class="visually-hidden">Siguiente</span>
                    </button>
                ` : ''}
            </div>
        `;
    }

    createSlides() {
        const itemsPerSlide = this.getItemsPerSlide();
        const slides = [];

        for (let i = 0; i < this.properties.length; i += itemsPerSlide) {
            slides.push(this.properties.slice(i, i + itemsPerSlide));
        }

        return slides;
    }

    getItemsPerSlide() {
        const width = window.innerWidth;
        // Cards horizontales: 2 por fila en desktop, 1 en móvil
        if (width >= 992) return 2;  // lg y xl: 2 cards
        return 1;  // móvil y tablet: 1 card
    }

    renderPropertyCard(prop) {
        const price = this.formatPrice(prop);
        const priceLabel = this.getPriceLabel(prop);
        const imageUrl = prop.image_url || '/theme_bohio_real_estate/static/src/img/placeholder.jpg';

        return `
            <div class="col-lg-6">
                <div class="card border-0 shadow-sm hover-lift h-100">
                    <div class="row g-0">
                        <div class="col-md-5">
                            <div class="position-relative" style="height: 100%; min-height: 250px;">
                                <img src="${imageUrl}"
                                     alt="${prop.name}"
                                     class="w-100 h-100"
                                     style="object-fit: cover;"
                                     loading="lazy"/>
                                ${prop.project_id ? `
                                    <span class="badge bg-danger position-absolute top-0 start-0 m-3">
                                        <i class="fa fa-building me-1"></i>${prop.project_name}
                                    </span>
                                ` : ''}
                            </div>
                        </div>
                        <div class="col-md-7">
                            <div class="card-body p-4 d-flex flex-column h-100">
                                <h3 class="h5 fw-bold text-danger mb-2">${prop.name}</h3>

                                ${prop.neighborhood ? `
                                    <p class="text-muted small mb-1">
                                        <i class="fa fa-home text-danger me-1"></i>
                                        <strong>${prop.neighborhood}</strong>
                                    </p>
                                ` : ''}

                                <p class="text-muted small mb-3">
                                    <i class="fa fa-map-marker-alt text-danger me-1"></i>
                                    ${prop.city}${prop.state ? ', ' + prop.state : ''}
                                </p>

                                <div class="mb-3">
                                    <div class="row g-2 small">
                                        ${prop.available_units !== undefined ? `
                                            <div class="col-6">
                                                <i class="fa fa-building text-danger me-1"></i>
                                                <span class="text-muted">${prop.available_units} Disponibles</span>
                                            </div>
                                            <div class="col-6">
                                                <i class="fa fa-home text-danger me-1"></i>
                                                <span class="text-muted">${prop.total_units || 0} Total</span>
                                            </div>
                                        ` : `
                                            ${prop.area > 0 ? `
                                                <div class="col-6">
                                                    <i class="fa fa-ruler-combined text-danger me-1"></i>
                                                    <span class="text-muted">${prop.area} m²</span>
                                                </div>
                                            ` : ''}
                                            ${prop.bedrooms > 0 ? `
                                                <div class="col-6">
                                                    <i class="fa fa-bed text-danger me-1"></i>
                                                    <span class="text-muted">${prop.bedrooms} Hab</span>
                                                </div>
                                            ` : ''}
                                            ${prop.bathrooms > 0 ? `
                                                <div class="col-6">
                                                    <i class="fa fa-bath text-danger me-1"></i>
                                                    <span class="text-muted">${prop.bathrooms} Baños</span>
                                                </div>
                                            ` : ''}
                                            ${prop.code ? `
                                                <div class="col-6">
                                                    <i class="fa fa-hashtag text-danger me-1"></i>
                                                    <span class="text-muted">${prop.code}</span>
                                                </div>
                                            ` : ''}
                                        `}
                                    </div>
                                </div>

                                ${prop.available_units === undefined ? `
                                    <div class="mb-3">
                                        <small class="text-muted d-block">${priceLabel}</small>
                                        <h4 class="text-danger fw-bold mb-0">${price}</h4>
                                    </div>
                                ` : ''}

                                <div class="mt-auto">
                                    <a href="${prop.url}" class="btn btn-danger btn-sm w-100">
                                        <i class="fa fa-eye me-1"></i>Ver Detalles
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    getLocation(prop) {
        if (prop.neighborhood) {
            return `${prop.neighborhood}, ${prop.city}`;
        }
        return prop.state ? `${prop.city}, ${prop.state}` : prop.city;
    }

    formatPrice(prop) {
        if (!prop.price) return "Consultar";
        return new Intl.NumberFormat("es-CO", {
            style: "currency",
            currency: "COP",
            minimumFractionDigits: 0,
        }).format(prop.price);
    }

    getPriceLabel(prop) {
        const isRental = prop.type_service && prop.type_service.includes("Arriendo");
        return isRental ? "Arriendo/mes" : "Venta";
    }

    showEmpty() {
        this.container.innerHTML = `
            <div class="text-center py-5">
                <i class="fa fa-home fa-3x text-muted mb-3"></i>
                <p class="text-muted">No hay propiedades disponibles</p>
            </div>
        `;
    }

    showError(message) {
        this.container.innerHTML = `
            <div class="alert alert-warning" role="alert">
                <i class="fa fa-exclamation-triangle me-2"></i>
                Error cargando propiedades: ${message}
            </div>
        `;
    }

    initBootstrapCarousel() {
        // Bootstrap 5 ya inicializa automáticamente con data-bs-ride="carousel"
        // No se necesita código adicional
    }
}

/**
 * Inicializar todos los carruseles
 */
async function initCarousels() {
    console.log('[PropertyCarousels] Inicializando carruseles...');

    const carousels = [
        new PropertyCarousel('carousel-rent', 'rent', 12),
        new PropertyCarousel('carousel-sale', 'sale', 12),
        new PropertyCarousel('carousel-projects', 'projects', 12),
    ];

    // Inicializar en paralelo
    await Promise.all(carousels.map(c => c.init()));

    console.log('[PropertyCarousels] ✅ Todos los carruseles listos');
}

// Ejecutar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCarousels);
} else {
    initCarousels();
}

// También ejecutar en evento de Odoo website
window.addEventListener('website:page_loaded', initCarousels);

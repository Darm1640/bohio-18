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
        if (width >= 1200) return 4;
        if (width >= 992) return 3;
        if (width >= 768) return 2;
        return 1;
    }

    renderPropertyCard(prop) {
        const location = this.getLocation(prop);
        const price = this.formatPrice(prop);
        const priceLabel = this.getPriceLabel(prop);
        const imageUrl = prop.image_url || '/theme_bohio_real_estate/static/src/img/placeholder.jpg';

        return `
            <div class="col-12 col-md-6 col-lg-3">
                <div class="card h-100 shadow-sm border-0 position-relative">
                    ${prop.project_id ? `
                        <div class="position-absolute top-0 end-0 m-2">
                            <a href="/proyecto/${prop.project_id}" class="badge bg-danger text-white text-decoration-none">
                                <i class="fa fa-building me-1"></i>
                                ${prop.project_name}
                            </a>
                        </div>
                    ` : ''}

                    <img src="${imageUrl}"
                         alt="${prop.name}"
                         class="card-img-top"
                         style="height: 200px; object-fit: cover;"
                         loading="lazy">

                    <div class="card-body d-flex flex-column">
                        <h5 class="card-title text-truncate" title="${prop.name}">${prop.name}</h5>

                        <p class="text-muted small mb-2">
                            <i class="fa fa-map-marker-alt me-1"></i>
                            ${location}
                        </p>

                        <div class="d-flex justify-content-between mb-2 text-muted small">
                            ${prop.area > 0 ? `<span><i class="fa fa-ruler-combined me-1"></i>${prop.area} m²</span>` : ''}
                            ${prop.bedrooms > 0 ? `<span><i class="fa fa-bed me-1"></i>${prop.bedrooms}</span>` : ''}
                            ${prop.bathrooms > 0 ? `<span><i class="fa fa-bath me-1"></i>${prop.bathrooms}</span>` : ''}
                        </div>

                        <div class="mb-2">
                            <small class="text-muted">${priceLabel}</small>
                            <h4 class="text-danger mb-0">${price}</h4>
                        </div>

                        <a href="${prop.url}" class="btn btn-outline-danger w-100 mt-auto">
                            <i class="fa fa-eye me-1"></i> Ver detalles
                        </a>
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

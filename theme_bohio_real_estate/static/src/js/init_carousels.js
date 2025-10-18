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
            // Silenciosamente salir si el contenedor no existe en esta página
            // Esto es normal ya que no todas las páginas tienen todos los carruseles
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

        // Si es un proyecto, usar diseño especial
        if (prop.available_units !== undefined) {
            return this.renderProjectCard(prop, imageUrl);
        }

        // Diseño normal para propiedades
        return `
            <div class="col-lg-6">
                <div class="card border-0 shadow-sm hover-lift h-100 bg-white">
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
                                        <i class="bi bi-building me-1"></i>${prop.project_name}
                                    </span>
                                ` : ''}
                            </div>
                        </div>
                        <div class="col-md-7">
                            <div class="card-body p-4 d-flex flex-column h-100">
                                <h3 class="h5 fw-bold text-danger mb-2">${prop.name}</h3>

                                ${prop.neighborhood ? `
                                    <p class="text-muted small mb-1">
                                        <i class="bi bi-house-fill text-danger me-1"></i>
                                        <strong>${prop.neighborhood}</strong>
                                    </p>
                                ` : ''}

                                <p class="text-muted small mb-3">
                                    <i class="bi bi-geo-alt-fill text-danger me-1"></i>
                                    ${prop.city}${prop.state ? ', ' + prop.state : ''}
                                </p>

                                <div class="mb-3">
                                    <div class="row g-2 small">
                                        ${prop.area > 0 ? `
                                            <div class="col-6">
                                                <i class="bi bi-rulers text-danger me-1"></i>
                                                <span class="text-muted">${prop.area} m²</span>
                                            </div>
                                        ` : ''}
                                        ${prop.bedrooms > 0 ? `
                                            <div class="col-6">
                                                <i class="bi bi-bed text-danger me-1"></i>
                                                <span class="text-muted">${prop.bedrooms} Hab</span>
                                            </div>
                                        ` : ''}
                                        ${prop.bathrooms > 0 ? `
                                            <div class="col-6">
                                                <i class="bi bi-droplet text-danger me-1"></i>
                                                <span class="text-muted">${prop.bathrooms} Baños</span>
                                            </div>
                                        ` : ''}
                                        ${prop.code ? `
                                            <div class="col-6">
                                                <i class="bi bi-hash text-danger me-1"></i>
                                                <span class="text-muted">${prop.code}</span>
                                            </div>
                                        ` : ''}
                                    </div>
                                </div>

                                <div class="mb-3">
                                    <small class="text-muted d-block">${priceLabel}</small>
                                    <h4 class="text-danger fw-bold mb-0">${price}</h4>
                                </div>

                                <div class="mt-auto">
                                    <a href="${prop.url}" class="btn btn-danger btn-sm w-100">
                                        <i class="bi bi-eye me-1"></i>Ver Detalles
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    renderProjectCard(project, imageUrl) {
        return `
            <div class="col-lg-6">
                <div class="card border-0 shadow-sm hover-lift h-100 bg-white">
                    <div class="position-relative" style="height: 300px;">
                        <span class="badge bg-warning text-dark position-absolute top-0 start-0 m-3" style="z-index: 10;">
                            En Construcción
                        </span>
                        <img src="${imageUrl}"
                             alt="${project.name}"
                             class="w-100 h-100"
                             style="object-fit: cover;"
                             loading="lazy"/>
                    </div>
                    <div class="card-body p-4">
                        <h3 class="h4 fw-bold text-danger mb-2">${project.name}</h3>

                        <p class="text-muted small mb-3">
                            ${project.description || 'Sin ubicación'}
                        </p>

                        <div class="d-flex justify-content-between align-items-center mb-4">
                            <div class="text-center">
                                <div class="d-flex align-items-center">
                                    <i class="bi bi-building text-muted me-2" style="font-size: 1.2rem;"></i>
                                    <span class="h5 mb-0">${project.total_units || 0}</span>
                                </div>
                                <small class="text-muted">Unidades</small>
                            </div>
                            <div class="text-center">
                                <div class="d-flex align-items-center">
                                    <i class="bi bi-house-fill text-danger me-2" style="font-size: 1.2rem;"></i>
                                    <span class="h5 mb-0 text-danger">${project.available_units}</span>
                                </div>
                                <small class="text-muted">Disponibles</small>
                            </div>
                        </div>

                        <div class="d-flex flex-column gap-2">
                            <a href="${project.url}" class="btn btn-danger w-100">
                                <i class="bi bi-building me-1"></i>Ver Proyecto Completo
                            </a>
                            <div class="row g-2">
                                <div class="col-6">
                                    <a href="/properties?project_id=${project.id}" class="btn btn-outline-danger btn-sm w-100">
                                        <i class="bi bi-grid me-1"></i>Ver Unidades
                                    </a>
                                </div>
                                <div class="col-6">
                                    <a href="/contacto?proyecto=${project.id}" class="btn btn-outline-danger btn-sm w-100">
                                        <i class="bi bi-envelope me-1"></i>Contactar
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
                <i class="bi bi-house-fill fa-3x text-muted mb-3"></i>
                <p class="text-muted">No hay propiedades disponibles</p>
            </div>
        `;
    }

    showError(message) {
        this.container.innerHTML = `
            <div class="alert alert-warning" role="alert">
                <i class="bi bi-exclamation-triangle me-2"></i>
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

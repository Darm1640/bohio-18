/** @odoo-module **/

import { Component, useState, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * Componente OWL para Carrusel de Propiedades
 *
 * Props:
 * - type: "rent" | "sale" | "projects"
 * - limit: número de propiedades a cargar (default: 12)
 */
export class PropertyCarousel extends Component {
    static template = "theme_bohio_real_estate.PropertyCarousel";
    static props = {
        type: String,
        limit: { type: Number, optional: true },
    };

    setup() {
        this.propertyData = useService("propertyData");

        this.state = useState({
            properties: [],
            loading: true,
            error: null,
            itemsPerSlide: this.computeItemsPerSlide(),
        });

        this.resizeHandler = this.onResize.bind(this);

        onWillStart(async () => {
            await this.loadProperties();
        });

        onMounted(() => {
            window.addEventListener("resize", this.resizeHandler);
            this.initCarousel();
        });

        onWillUnmount(() => {
            window.removeEventListener("resize", this.resizeHandler);
        });
    }

    /**
     * Cargar propiedades desde el servicio
     */
    async loadProperties() {
        console.log(`[PropertyCarousel] Cargando propiedades tipo: ${this.props.type}`);

        try {
            this.state.loading = true;
            this.state.error = null;

            const result = await this.propertyData.fetchProperties(this.props.type, {
                limit: this.props.limit || 12,
            });

            if (result && result.success) {
                this.state.properties = result.properties;
                console.log(
                    `[PropertyCarousel] ${result.properties.length} propiedades cargadas ` +
                    `para ${this.props.type} (de ${result.total} total)`
                );
            } else if (result === null) {
                // Request cancelado, no hacer nada
                console.log(`[PropertyCarousel] Request cancelado para ${this.props.type}`);
            } else {
                throw new Error("No se recibieron propiedades válidas");
            }
        } catch (error) {
            console.error(`[PropertyCarousel] Error:`, error);
            this.state.error = error.message || "Error cargando propiedades";
        } finally {
            this.state.loading = false;
        }
    }

    /**
     * Calcular items por slide según ancho de pantalla
     */
    computeItemsPerSlide() {
        const width = window.innerWidth;
        if (width >= 1200) return 4; // XL
        if (width >= 992) return 3;  // LG
        if (width >= 768) return 2;  // MD
        return 1;                     // SM, XS
    }

    /**
     * Manejar resize
     */
    onResize() {
        const newItems = this.computeItemsPerSlide();
        if (newItems !== this.state.itemsPerSlide) {
            this.state.itemsPerSlide = newItems;
        }
    }

    /**
     * Agrupar propiedades en slides
     */
    get slides() {
        const slides = [];
        const items = this.state.itemsPerSlide;

        for (let i = 0; i < this.state.properties.length; i += items) {
            slides.push(this.state.properties.slice(i, i + items));
        }

        return slides;
    }

    /**
     * Formatear precio
     */
    formatPrice(property) {
        if (!property.price) return "Consultar";

        return new Intl.NumberFormat("es-CO", {
            style: "currency",
            currency: "COP",
            minimumFractionDigits: 0,
        }).format(property.price);
    }

    /**
     * Label de precio según tipo
     */
    priceLabel(property) {
        const isRental = property.type_service && property.type_service.includes("Arriendo");
        return isRental ? "Arriendo/mes" : "Venta";
    }

    /**
     * Construir ubicación
     */
    getLocation(property) {
        if (property.neighborhood) {
            return `${property.neighborhood}, ${property.city}`;
        }
        return property.state ? `${property.city}, ${property.state}` : property.city;
    }

    /**
     * Inicializar Bootstrap Carousel
     */
    initCarousel() {
        if (typeof bootstrap === "undefined") {
            console.warn("[PropertyCarousel] Bootstrap no disponible");
            return;
        }

        const carouselEl = this.el.querySelector(".carousel");
        if (!carouselEl) {
            console.warn("[PropertyCarousel] Elemento .carousel no encontrado");
            return;
        }

        try {
            new bootstrap.Carousel(carouselEl, {
                interval: 5000,
                wrap: true,
                keyboard: true,
                pause: "hover",
            });
            console.log(`[PropertyCarousel] Bootstrap carousel inicializado para ${this.props.type}`);
        } catch (error) {
            console.error("[PropertyCarousel] Error inicializando carousel:", error);
        }
    }
}

// Registrar componente
registry.category("public_components").add("PropertyCarousel", PropertyCarousel);

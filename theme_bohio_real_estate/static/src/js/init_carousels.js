/** @odoo-module **/

import { Component, mount } from "@odoo/owl";
import { PropertyCarousel } from "@theme_bohio_real_estate/components/property_carousel/property_carousel";

/**
 * Inicializar carruseles OWL en la homepage
 * Monta componentes en los divs existentes
 */
async function initCarousels() {
    console.log('[InitCarousels] Inicializando carruseles OWL...');

    const carousels = [
        { id: 'carousel-rent', type: 'rent', limit: 12 },
        { id: 'carousel-sale', type: 'sale', limit: 12 },
        { id: 'carousel-projects', type: 'projects', limit: 12 },
    ];

    for (const carousel of carousels) {
        const container = document.getElementById(carousel.id);

        if (!container) {
            console.warn(`[InitCarousels] Contenedor ${carousel.id} no encontrado`);
            continue;
        }

        try {
            console.log(`[InitCarousels] Montando carrusel ${carousel.type} en #${carousel.id}`);

            // Limpiar contenido previo (spinner)
            container.innerHTML = '';

            // Montar componente OWL
            await mount(PropertyCarousel, container, {
                props: {
                    type: carousel.type,
                    limit: carousel.limit,
                },
            });

            console.log(`[InitCarousels] ✅ Carrusel ${carousel.type} montado exitosamente`);
        } catch (error) {
            console.error(`[InitCarousels] ❌ Error montando carrusel ${carousel.type}:`, error);

            // Mostrar mensaje de error
            container.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="fa fa-exclamation-triangle me-2"></i>
                    Error cargando propiedades. Por favor, recarga la página.
                </div>
            `;
        }
    }

    console.log('[InitCarousels] Inicialización completa');
}

// Ejecutar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCarousels);
} else {
    // DOM ya está listo
    initCarousels();
}

// También ejecutar en evento de Odoo website
window.addEventListener('website:page_loaded', initCarousels);

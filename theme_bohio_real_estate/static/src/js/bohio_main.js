/** @odoo-module **/
/**
 * Bohío Real Estate - Main JavaScript
 * Inicialización global y funcionalidades comunes del tema
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Bohío Real Estate Theme - Initialized');

    // Inicializar navegación sticky
    initStickyHeader();

    // Inicializar lazy loading de imágenes
    initLazyLoading();

    // Inicializar smooth scroll
    initSmoothScroll();
});

/**
 * Header sticky al hacer scroll
 */
function initStickyHeader() {
    const header = document.querySelector('header.o_header_standard');
    if (!header) return;

    let lastScroll = 0;

    window.addEventListener('scroll', function() {
        const currentScroll = window.pageYOffset;

        if (currentScroll > 100) {
            header.classList.add('header-scrolled');
        } else {
            header.classList.remove('header-scrolled');
        }

        lastScroll = currentScroll;
    });
}

/**
 * Lazy loading de imágenes
 */
function initLazyLoading() {
    const images = document.querySelectorAll('img[loading="lazy"]');

    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src || img.src;
                    img.classList.add('loaded');
                    observer.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));
    }
}

/**
 * Smooth scroll para enlaces internos
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#') return;

            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Formatear precio
 */
window.formatPrice = function(price) {
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(price);
};

/**
 * Formatear área
 */
window.formatArea = function(area) {
    return new Intl.NumberFormat('es-CO', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(area) + ' m²';
};

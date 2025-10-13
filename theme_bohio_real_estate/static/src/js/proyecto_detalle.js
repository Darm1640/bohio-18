/** @odoo-module **/

console.log('BOHIO Proyecto Detalle JS cargado');

let proyectoDetalleMap = null;

/**
 * Inicializar mapa de Leaflet para proyecto
 */
function inicializarMapaProyecto() {
    if (typeof L === 'undefined') {
        console.warn('[PROYECTO] Leaflet no esta cargado todavia');
        return;
    }

    // Buscar el elemento del mapa
    const mapElement = document.querySelector('[id^="map-proyecto-"]');
    if (!mapElement) {
        console.log('[PROYECTO] No se encontro elemento del mapa - no hay coordenadas disponibles');
        return;
    }

    // Obtener coordenadas y nombre del proyecto desde data attributes
    const lat = parseFloat(mapElement.dataset.lat);
    const lng = parseFloat(mapElement.dataset.lng);
    const projectName = mapElement.dataset.name;

    console.log('[PROYECTO] Inicializando mapa:', {
        elemento: mapElement.id,
        lat: lat,
        lng: lng,
        nombre: projectName
    });

    if (!lat || !lng || isNaN(lat) || isNaN(lng)) {
        console.warn('[PROYECTO] Coordenadas invalidas:', { lat, lng });
        // Mostrar mensaje en el contenedor
        mapElement.innerHTML = `
            <div class="d-flex align-items-center justify-content-center h-100 bg-light">
                <div class="text-center p-4">
                    <i class="fa fa-map-marked-alt fa-3x text-muted mb-3"></i>
                    <p class="text-muted mb-0">Mapa no disponible</p>
                    <small class="text-muted">No hay coordenadas GPS para este proyecto</small>
                </div>
            </div>
        `;
        return;
    }

    try {
        // Crear mapa centrado en las coordenadas del proyecto
        proyectoDetalleMap = L.map(mapElement.id).setView([lat, lng], 15);

        // Agregar capa de tiles de OpenStreetMap
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(proyectoDetalleMap);

        // Crear icono personalizado rojo
        const redIcon = L.divIcon({
            className: 'custom-marker-proyecto',
            html: `
                <div style="
                    background: #E31E24;
                    width: 40px;
                    height: 40px;
                    border-radius: 50% 50% 50% 0;
                    transform: rotate(-45deg);
                    border: 3px solid white;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.3);
                    position: relative;
                ">
                    <div style="
                        transform: rotate(45deg);
                        margin-top: 8px;
                        margin-left: 12px;
                        color: white;
                        font-weight: bold;
                        font-size: 18px;
                    ">P</div>
                </div>
            `,
            iconSize: [40, 40],
            iconAnchor: [20, 40],
            popupAnchor: [0, -40]
        });

        // Agregar marcador con popup
        const marker = L.marker([lat, lng], { icon: redIcon }).addTo(proyectoDetalleMap);

        // Crear contenido del popup
        const popupContent = `
            <div style="min-width: 200px; max-width: 250px;">
                <h6 class="fw-bold mb-2" style="color: #E31E24;">${projectName}</h6>
                <p class="small text-muted mb-2">
                    <i class="bi bi-geo-alt-fill me-1"></i>
                    Ubicación del proyecto
                </p>
                <a href="#propiedades" class="btn btn-sm w-100" style="background: #E31E24; color: white; border: none;">
                    <i class="bi bi-building me-1"></i>Ver Propiedades
                </a>
            </div>
        `;

        marker.bindPopup(popupContent, {
            maxWidth: 250,
            className: 'bohio-proyecto-popup'
        });

        console.log('[PROYECTO] Mapa inicializado exitosamente en:', mapElement.id);

    } catch (error) {
        console.error('[PROYECTO] Error inicializando mapa:', error);
        // Mostrar error en el contenedor
        mapElement.innerHTML = `
            <div class="d-flex align-items-center justify-content-center h-100 bg-light">
                <div class="text-center p-4">
                    <i class="bi bi-exclamation-triangle fa-3x text-warning mb-3"></i>
                    <p class="text-muted mb-0">Error al cargar el mapa</p>
                    <small class="text-muted">${error.message}</small>
                </div>
            </div>
        `;
    }
}

/**
 * Smooth scroll para enlaces internos
 */
function inicializarSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const target = document.querySelector(targetId);

            if (target) {
                // Offset para el header fijo
                const headerOffset = 80;
                const elementPosition = target.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

/**
 * Hover effects para cards de propiedades
 */
function inicializarHoverEffects() {
    const propertyCards = document.querySelectorAll('.property-type-card');

    propertyCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

/**
 * Lazy loading de imagenes
 */
function inicializarLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');

    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}

/**
 * Contador animado para stats
 */
function animarContadores() {
    const counters = document.querySelectorAll('.display-4');

    counters.forEach(counter => {
        const target = parseInt(counter.textContent);
        if (isNaN(target)) return;

        let current = 0;
        const increment = target / 50; // 50 frames
        const duration = 1500; // 1.5 segundos
        const interval = duration / 50;

        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                counter.textContent = target;
                clearInterval(timer);
            } else {
                counter.textContent = Math.floor(current);
            }
        }, interval);
    });
}

/**
 * Parallax effect para hero section
 */
function inicializarParallax() {
    const heroSection = document.querySelector('.hero-proyecto');
    if (!heroSection) return;

    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const parallaxSpeed = 0.5;

        if (scrolled < window.innerHeight) {
            heroSection.style.transform = `translateY(${scrolled * parallaxSpeed}px)`;
        }
    });
}

/**
 * Inicializar cuando Leaflet este listo
 */
function esperarLeaflet() {
    console.log('[PROYECTO] Verificando Leaflet...', typeof L !== 'undefined' ? 'DISPONIBLE' : 'NO DISPONIBLE');

    if (typeof L !== 'undefined') {
        console.log('[PROYECTO] Leaflet disponible, inicializando mapa...');
        inicializarMapaProyecto();
    } else {
        console.log('[PROYECTO] Esperando a que Leaflet se cargue... reintentando en 100ms');
        setTimeout(esperarLeaflet, 100);
    }
}

/**
 * Inicializar todo cuando el DOM este listo
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('[PROYECTO] DOM listo, inicializando proyecto detalle...');

    // Verificar si estamos en una pagina de proyecto
    const proyectoPage = document.querySelector('.hero-proyecto');
    console.log('[PROYECTO] Elemento .hero-proyecto encontrado:', !!proyectoPage);

    if (!proyectoPage) {
        console.log('[PROYECTO] No es una pagina de proyecto - saliendo');
        return;
    }

    console.log('[PROYECTO] Inicializando funcionalidades...');

    // Inicializar funcionalidades
    inicializarSmoothScroll();
    inicializarHoverEffects();
    inicializarLazyLoading();

    // Animar contadores cuando sean visibles
    const statsSection = document.querySelector('.hero-proyecto');
    if (statsSection) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animarContadores();
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });

        observer.observe(statsSection);
    }

    // Inicializar parallax
    inicializarParallax();

    console.log('[PROYECTO] Llamando a esperarLeaflet()...');
    // Esperar a que Leaflet este disponible para inicializar mapa
    esperarLeaflet();
});

/**
 * Reinicializar mapa cuando cambie el tamaño de la ventana
 */
window.addEventListener('resize', () => {
    if (proyectoDetalleMap) {
        setTimeout(() => {
            proyectoDetalleMap.invalidateSize();
        }, 100);
    }
});

/** @odoo-module **/

console.log('BOHIO Homepage JS cargado');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM listo - Iniciando BOHIO Homepage');

    // Navbar transparente con scroll
    initTransparentNavbar();

    // Iniciar banner (GIF → Carrusel)
    initHeroBanner();

    // Cargar propiedades
    loadHomeProperties();
});

function initTransparentNavbar() {
    const header = document.querySelector('.bohio-header');
    if (!header) return;

    window.addEventListener('scroll', () => {
        if (window.scrollY > 100) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });
}

function initHeroBanner() {
    const carouselContainer = document.getElementById('heroCarousel');

    if (!carouselContainer) return;

    // Iniciar el carrusel automático con Bootstrap
    if (typeof bootstrap !== 'undefined') {
        new bootstrap.Carousel(carouselContainer, {
            interval: 5000,
            ride: 'carousel'
        });
    }
}

async function loadHomeProperties() {
    console.log('Cargando propiedades...');

    try {
        const arriendoData = await fetchProperties({ type_service: 'rent', limit: 6 });
        renderProperties(arriendoData.properties, 'arriendo-properties-grid');

        const usedSaleData = await fetchProperties({ type_service: 'sale', state: 'used', limit: 6 });
        renderProperties(usedSaleData.properties, 'used-sale-properties-grid');

        const projectsData = await fetchProperties({ type_service: 'sale', is_project: true, limit: 6 });
        renderProperties(projectsData.properties, 'projects-properties-grid');

        console.log('Propiedades cargadas');
    } catch (error) {
        console.error('Error cargando propiedades:', error);
    }
}

async function fetchProperties(filters) {
    try {
        const response = await fetch('/bohio/api/properties', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(filters)
        });
        const data = await response.json();
        console.log('Propiedades recibidas:', data);
        return data;
    } catch (error) {
        console.error('Error en fetch:', error);
        return { properties: [], count: 0 };
    }
}

function renderProperties(properties, containerId) {
    const container = document.getElementById(containerId);
    if (!container) {
        console.warn('Contenedor no encontrado:', containerId);
        return;
    }

    if (!properties || properties.length === 0) {
        container.innerHTML = '<div class="col-12 text-center py-5"><i class="fa fa-home fa-3x text-muted mb-3"></i><p class="text-muted">No hay propiedades disponibles</p></div>';
        return;
    }

    container.innerHTML = properties.map(property => renderPropertyCard(property)).join('');
}

function renderPropertyCard(property) {
    const imageUrl = property.image_url || '/theme_bohio_real_estate/static/src/img/home-banner.jpg';
    const price = formatPrice(property.list_price);
    const typeServiceBadge = property.type_service === 'rent' ? '<span class="badge bg-primary">Arriendo</span>' : '<span class="badge bg-success">Venta</span>';
    const newBadge = property.is_new ? '<span class="badge bg-warning ms-1">NUEVO</span>' : '';

    return `
        <div class="col-lg-4 col-md-6">
            <div class="card property-card-homepage shadow-sm rounded-3 h-100">
                <div class="position-relative">
                    <img src="${imageUrl}" class="card-img-top property-image" alt="${property.name}" style="height: 250px; object-fit: cover;"/>
                    <div class="position-absolute top-0 end-0 m-3">
                        <span class="badge bg-danger px-3 py-2">$${price}</span>
                    </div>
                    <div class="position-absolute top-0 start-0 m-3">
                        ${typeServiceBadge}
                        ${newBadge}
                    </div>
                </div>
                <div class="card-body">
                    <h5 class="card-title mb-2">
                        <a href="/property/${property.id}" class="text-decoration-none text-dark">
                            ${property.name.substring(0, 50)}${property.name.length > 50 ? '...' : ''}
                        </a>
                    </h5>
                    <p class="text-muted small mb-3">
                        <i class="fa fa-map-marker-alt me-1"></i>
                        ${property.city || ''}, ${property.region || ''}
                    </p>
                    ${renderPropertyFeatures(property)}
                    <div class="mb-3">
                        <small class="text-muted">Código: <strong>${property.default_code || 'N/A'}</strong></small>
                    </div>
                    <a href="/property/${property.id}" class="btn btn-outline-danger w-100">Ver Detalles</a>
                </div>
            </div>
        </div>
    `;
}

function renderPropertyFeatures(property) {
    if (!['apartment', 'house'].includes(property.property_type)) {
        return `<div class="property-features d-flex justify-content-between mb-3 pb-3 border-bottom"><span class="feature-item text-muted small"><i class="fa fa-ruler-combined"></i> <strong>${property.area_total || 0}</strong> m²</span></div>`;
    }

    return `
        <div class="property-features d-flex justify-content-between mb-3 pb-3 border-bottom">
            <span class="feature-item text-muted small">
                <img src="/theme_bohio_real_estate/static/src/img/habitacion-8.png" style="width: 20px; height: 20px;" alt="Habitaciones"/>
                <strong>${property.bedrooms || 0}</strong>
            </span>
            <span class="feature-item text-muted small">
                <img src="/theme_bohio_real_estate/static/src/img/baño_1-8.png" style="width: 20px; height: 20px;" alt="Baños"/>
                <strong>${property.bathrooms || 0}</strong>
            </span>
            <span class="feature-item text-muted small">
                <img src="/theme_bohio_real_estate/static/src/img/areas_1-8.png" style="width: 20px; height: 20px;" alt="Área"/>
                <strong>${property.area_constructed || 0}</strong> m²
            </span>
        </div>
    `;
}

function formatPrice(price) {
    return new Intl.NumberFormat('es-CO').format(price);
}

/**
 * Toggle Advanced Filters
 * Muestra/oculta los filtros avanzados en el formulario de búsqueda
 */
window.toggleAdvancedFilters = function() {
    const filtersContainer = document.getElementById('advancedFilters');
    const toggleBtn = document.getElementById('toggleFiltersBtn');
    const toggleText = document.getElementById('toggleFiltersText');
    const toggleIcon = toggleBtn?.querySelector('i');

    if (!filtersContainer || !toggleBtn || !toggleText || !toggleIcon) return;

    if (filtersContainer.style.display === 'none' || filtersContainer.style.display === '') {
        // Mostrar filtros
        filtersContainer.style.display = 'block';
        toggleText.textContent = 'Ocultar filtros';
        toggleIcon.classList.remove('fa-plus-circle');
        toggleIcon.classList.add('fa-minus-circle');
        toggleBtn.classList.add('active');
    } else {
        // Ocultar filtros
        filtersContainer.style.display = 'none';
        toggleText.textContent = 'Mostrar más filtros';
        toggleIcon.classList.remove('fa-minus-circle');
        toggleIcon.classList.add('fa-plus-circle');
        toggleBtn.classList.remove('active');
    }
};

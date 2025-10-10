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

// Variables globales para mapas y datos de propiedades
let arriendoMap = null;
let usedSaleMap = null;
let projectsMap = null;
let rentPropertiesData = [];
let usedSalePropertiesData = [];
let projectsPropertiesData = [];

async function loadHomeProperties() {
    console.log('Cargando propiedades...');

    try {
        // Cargar propiedades en arriendo
        const arriendoData = await fetchProperties({ type_service: 'rent', limit: 4 });
        if (arriendoData.properties && arriendoData.properties.length > 0) {
            rentPropertiesData = arriendoData.properties;
            renderProperties(arriendoData.properties, 'arriendo-properties-grid');
        }

        // Cargar propiedades usadas en venta (NO proyectos)
        const usedSaleData = await fetchProperties({ type_service: 'sale', is_project: 'false', limit: 4 });
        if (usedSaleData.properties && usedSaleData.properties.length > 0) {
            usedSalePropertiesData = usedSaleData.properties;
            renderProperties(usedSaleData.properties, 'used-sale-properties-grid');
        }

        // Cargar proyectos en venta
        const projectsData = await fetchProperties({ type_service: 'sale', is_project: 'true', limit: 4 });
        if (projectsData.properties && projectsData.properties.length > 0) {
            projectsPropertiesData = projectsData.properties;
            renderProperties(projectsData.properties, 'projects-properties-grid');
        }

        console.log('Propiedades cargadas:', {
            arriendos: rentPropertiesData.length,
            usadas: usedSalePropertiesData.length,
            proyectos: projectsPropertiesData.length
        });

        // Configurar eventos de las pestañas de mapas
        setupMapTabs();
    } catch (error) {
        console.error('Error cargando propiedades:', error);
    }
}

async function fetchProperties(filters) {
    try {
        // Usar jsonRpc para llamar al endpoint correcto
        const response = await fetch('/properties/api/list', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: filters,
                id: Math.floor(Math.random() * 1000000)
            })
        });
        const data = await response.json();
        console.log('Respuesta API:', data);
        return data.result || { properties: [] };
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
    const price = formatPrice(property.price || property.list_price || 0);
    const typeServiceBadge = property.type_service === 'rent' ? '<span class="badge bg-primary">Arriendo</span>' : '<span class="badge bg-success">Venta</span>';
    const newBadge = property.is_new ? '<span class="badge bg-warning ms-1">NUEVO</span>' : '';

    // Adaptar nombres de campos del API a los que usa el frontend
    const bedrooms = property.bedrooms || property.num_bedrooms || 0;
    const bathrooms = property.bathrooms || property.num_bathrooms || 0;
    const area = property.area || property.area_constructed || property.property_area || 0;
    const city = property.city || '';
    const region = property.region || property.neighborhood || '';

    return `
        <div class="col-md-3">
            <div class="card h-100 shadow-sm border-0">
                <img src="${imageUrl}" class="card-img-top" alt="${property.name}" style="height: 200px; object-fit: cover;" loading="lazy"/>
                <div class="card-body d-flex flex-column">
                    <h5 class="card-title text-truncate">${property.name}</h5>
                    <p class="text-muted small mb-2">
                        <i class="fa fa-map-marker-alt me-1"></i>${city}${region ? ', ' + region : ''}
                    </p>
                    <div class="d-flex justify-content-between mb-2">
                        <span class="small"><i class="fa fa-bed me-1"></i>${bedrooms}</span>
                        <span class="small"><i class="fa fa-bath me-1"></i>${bathrooms}</span>
                        <span class="small"><i class="fa fa-ruler-combined me-1"></i>${area} m²</span>
                    </div>
                    <div class="mb-2">
                        <small class="text-muted">${property.type_service === 'rent' ? 'Arriendo/mes' : 'Venta'}</small>
                        <h4 class="text-danger mb-0">$${price}</h4>
                    </div>
                    <a href="/property/${property.id}" class="btn btn-outline-danger w-100 mt-auto">Ver detalles</a>
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
 * Inicializar un mapa específico con Leaflet
 */
function initMap(mapId) {
    if (typeof L === 'undefined') {
        console.warn('Leaflet no está cargado');
        return null;
    }

    try {
        const mapEl = document.getElementById(mapId);
        if (!mapEl) {
            console.warn('Elemento del mapa no encontrado:', mapId);
            return null;
        }

        // Crear nuevo mapa centrado en Colombia
        const newMap = L.map(mapId).setView([4.7110, -74.0721], 11);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(newMap);

        console.log('Mapa inicializado:', mapId);
        return newMap;
    } catch (error) {
        console.error('Error inicializando mapa:', mapId, error);
        return null;
    }
}

/**
 * Actualizar marcadores en el mapa
 */
function updateMapMarkers(map, properties) {
    if (!map || typeof L === 'undefined') return;

    // Limpiar marcadores existentes
    map.eachLayer(function(layer) {
        if (layer instanceof L.Marker) {
            map.removeLayer(layer);
        }
    });

    // Agregar nuevos marcadores
    const bounds = [];
    properties.forEach(prop => {
        if (prop.latitude && prop.longitude) {
            const marker = L.marker([prop.latitude, prop.longitude]).addTo(map);

            const price = formatPrice(prop.price || 0);
            const priceLabel = prop.type_service === 'rent' ? 'Arriendo/mes' : 'Venta';
            const imageUrl = prop.image_url || '/theme_bohio_real_estate/static/src/img/placeholder.jpg';
            const location = `${prop.neighborhood || ''} ${prop.city || ''}`.trim();

            const popupContent = `
                <div style="min-width: 250px; max-width: 300px;">
                    <img src="${imageUrl}" alt="${prop.name}" style="width: 100%; height: 150px; object-fit: cover; border-radius: 8px; margin-bottom: 10px;"/>
                    <h6 class="fw-bold mb-2" style="font-size: 14px;">${prop.name}</h6>
                    <p class="small mb-1 text-muted">
                        <i class="fa fa-map-marker-alt text-danger"></i> ${location}
                    </p>
                    <div class="mb-2">
                        <small class="text-muted d-block">${priceLabel}</small>
                        <p class="mb-1 text-danger fw-bold" style="font-size: 16px;">$${price}</p>
                    </div>
                    <a href="/property/${prop.id}" class="btn btn-sm btn-danger w-100">
                       <i class="fa fa-eye me-1"></i>Ver detalles
                    </a>
                </div>
            `;

            marker.bindPopup(popupContent, {
                maxWidth: 300,
                className: 'custom-popup'
            });

            bounds.push([prop.latitude, prop.longitude]);
        }
    });

    // Ajustar vista del mapa
    if (bounds.length > 0) {
        map.fitBounds(bounds, {
            padding: [50, 50],
            maxZoom: 13
        });
    }
}

/**
 * Configurar eventos de las pestañas de mapas
 */
function setupMapTabs() {
    // Pestaña de arriendo
    const arriendoMapTab = document.getElementById('arriendo-map-tab');
    if (arriendoMapTab) {
        arriendoMapTab.addEventListener('shown.bs.tab', function() {
            console.log('Mostrando mapa de arriendos');
            if (!arriendoMap) {
                arriendoMap = initMap('arriendo-properties-map');
            } else {
                arriendoMap.invalidateSize();
            }
            if (arriendoMap && rentPropertiesData.length > 0) {
                setTimeout(() => {
                    updateMapMarkers(arriendoMap, rentPropertiesData);
                }, 200);
            }
        });
    }

    // Pestaña de ventas usadas
    const usedSaleMapTab = document.querySelector('[data-bs-target="#used-sale-map"]');
    if (usedSaleMapTab) {
        usedSaleMapTab.addEventListener('shown.bs.tab', function() {
            console.log('Mostrando mapa de ventas usadas');
            if (!usedSaleMap) {
                usedSaleMap = initMap('used-sale-properties-map');
            } else {
                usedSaleMap.invalidateSize();
            }
            if (usedSaleMap && usedSalePropertiesData.length > 0) {
                setTimeout(() => {
                    updateMapMarkers(usedSaleMap, usedSalePropertiesData);
                }, 200);
            }
        });
    }

    // Pestaña de proyectos
    const projectsMapTab = document.querySelector('[data-bs-target="#projects-map"]');
    if (projectsMapTab) {
        projectsMapTab.addEventListener('shown.bs.tab', function() {
            console.log('Mostrando mapa de proyectos');
            if (!projectsMap) {
                projectsMap = initMap('projects-properties-map');
            } else {
                projectsMap.invalidateSize();
            }
            if (projectsMap && projectsPropertiesData.length > 0) {
                setTimeout(() => {
                    updateMapMarkers(projectsMap, projectsPropertiesData);
                }, 200);
            }
        });
    }
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

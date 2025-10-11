/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

/**
 * BOHIO Homepage Properties - Sistema de Carga y Mapas
 * Implementación con RPC nativo de Odoo 18 (disponible en web.assets_frontend)
 */

// Variables globales para mapas y datos
let arriendoMap = null;
let usedSaleMap = null;
let projectsMap = null;
let rentPropertiesData = [];
let usedSalePropertiesData = [];
let projectsPropertiesData = [];

/**
 * Inicializar un mapa específico de Leaflet
 * @param {string} mapId - ID del elemento del mapa
 * @param {object} mapVariable - Variable del mapa existente
 * @returns {object} - Instancia del mapa de Leaflet
 */
function initMap(mapId, mapVariable) {
    // Verificar que Leaflet esté cargado
    if (typeof L === 'undefined') {
        console.warn('Leaflet no está cargado todavía');
        return null;
    }

    try {
        const mapEl = document.getElementById(mapId);
        if (!mapEl) {
            console.warn('Elemento del mapa no encontrado:', mapId);
            return null;
        }

        // Si el mapa ya existe, solo invalidar el tamaño
        if (mapVariable) {
            setTimeout(() => mapVariable.invalidateSize(), 100);
            return mapVariable;
        }

        // Crear nuevo mapa centrado en Bogotá
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
 * @param {object} map - Instancia del mapa de Leaflet
 * @param {array} properties - Array de propiedades
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

            // Formatear precio y ubicación
            const price = prop.price ?
                new Intl.NumberFormat('es-CO', {
                    style: 'currency',
                    currency: 'COP',
                    minimumFractionDigits: 0
                }).format(prop.price) : 'Consultar';

            const priceLabel = prop.type_service === 'rent' ? 'Arriendo/mes' : 'Venta';
            const imageUrl = prop.image_url || '/theme_bohio_real_estate/static/src/img/placeholder.jpg';
            const neighborhood = prop.neighborhood ? `${prop.neighborhood}, ` : '';
            const location = `${neighborhood}${prop.city || prop.state || ''}`;
            const bedrooms = prop.bedrooms || 0;
            const bathrooms = prop.bathrooms || 0;
            const area = prop.total_area || prop.built_area || 0;

            // Crear popup con imagen, barrio, precio y detalles
            const popupContent = `
                <div style="min-width: 280px; max-width: 300px;">
                    <img src="${imageUrl}"
                         alt="${prop.name}"
                         style="width: 100%; height: 160px; object-fit: cover; border-radius: 8px; margin-bottom: 12px;"
                         onerror="this.src='/theme_bohio_real_estate/static/src/img/placeholder.jpg'"/>
                    <h6 class="fw-bold mb-2" style="font-size: 14px;">${prop.name}</h6>
                    <p class="small mb-2 text-muted">
                        <i class="fa fa-map-marker-alt text-danger me-1"></i>${location}
                    </p>
                    <div class="mb-2">
                        <small class="text-muted d-block">${priceLabel}</small>
                        <p class="mb-2 text-danger fw-bold" style="font-size: 16px;">${price}</p>
                    </div>
                    <div class="d-flex gap-3 mb-3" style="font-size: 13px; color: #666;">
                        ${area > 0 ? `<span><i class="fa fa-ruler-combined me-1"></i>${area} m²</span>` : ''}
                        ${bedrooms > 0 ? `<span><i class="fa fa-bed me-1"></i>${bedrooms} hab</span>` : ''}
                        ${bathrooms > 0 ? `<span><i class="fa fa-bath me-1"></i>${bathrooms} baños</span>` : ''}
                    </div>
                    <a href="/property/${prop.id}"
                       class="btn btn-sm btn-danger w-100"
                       style="background: #E31E24; border: none;">
                       <i class="fa fa-eye me-1"></i>Ver detalles
                    </a>
                </div>
            `;

            marker.bindPopup(popupContent, {
                maxWidth: 300,
                className: 'bohio-map-popup'
            });

            bounds.push([prop.latitude, prop.longitude]);
        }
    });

    // Ajustar vista del mapa con zoom apropiado
    if (bounds.length > 0) {
        map.fitBounds(bounds, {
            padding: [50, 50],
            maxZoom: 13
        });
    }
}

/**
 * Crear tarjeta de propiedad HTML
 * @param {object} property - Objeto de propiedad
 * @returns {string} - HTML de la tarjeta
 */
function createPropertyCard(property) {
    const imageUrl = property.image_url || '/theme_bohio_real_estate/static/src/img/placeholder.jpg';
    const price = property.price ?
        new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            minimumFractionDigits: 0
        }).format(property.price) : 'Consultar';

    const bedrooms = property.bedrooms || 0;
    const bathrooms = property.bathrooms || 0;
    const area = property.area || 0;
    const location = (property.city && property.state) ?
        `${property.city}, ${property.state}` :
        (property.city || property.state || 'No especificado');
    const description = property.description ? property.description.substring(0, 100) + '...' : '';
    const priceLabel = property.type_service === 'rent' ? 'Arriendo/mes' : 'Venta';

    // Badge de proyecto si la propiedad pertenece a uno
    const projectBadge = property.project_id && property.project_name ? `
        <div class="position-absolute top-0 end-0 m-2">
            <a href="/proyecto/${property.project_id}"
               class="badge bg-danger text-white text-decoration-none"
               style="font-size: 0.7rem; padding: 0.4rem 0.6rem;">
                <i class="fa fa-building me-1"></i>${property.project_name}
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
                     loading="lazy"/>
                <div class="card-body d-flex flex-column">
                    <h5 class="card-title text-truncate">${property.name}</h5>
                    <p class="text-muted small mb-2">
                        <i class="fa fa-map-marker-alt me-1"></i>${location}
                    </p>
                    ${description ? `<p class="text-muted small mb-2">${description}</p>` : ''}
                    <div class="d-flex justify-content-between mb-2">
                        <span class="small"><i class="fa fa-bed me-1"></i>${bedrooms}</span>
                        <span class="small"><i class="fa fa-bath me-1"></i>${bathrooms}</span>
                        <span class="small"><i class="fa fa-ruler-combined me-1"></i>${area} m²</span>
                    </div>
                    <div class="mb-2">
                        <small class="text-muted">${priceLabel}</small>
                        <h4 class="text-danger mb-0">${price}</h4>
                    </div>
                    <a href="/property/${property.id}"
                       class="btn btn-outline-danger w-100 mt-auto">Ver detalles</a>
                </div>
            </div>
        </div>
    `;
}

/**
 * Cargar propiedades desde el API usando RPC nativo de Odoo
 * @param {object} params - Parámetros de búsqueda
 * @returns {Promise} - Promesa con los datos
 */
async function loadProperties(params) {
    try {
        console.log('Llamando /property/search/ajax con params:', params);

        const result = await rpc('/property/search/ajax', {
            context: 'public',
            filters: params,
            page: 1,
            ppg: params.limit || 20,
            order: params.order || 'newest'
        });

        console.log('Resultado recibido:', result);
        return result;
    } catch (error) {
        console.error('Error cargando propiedades:', error);
        return { properties: [] };
    }
}

/**
 * Cargar todas las propiedades del homepage
 */
async function loadHomePropertiesWithMaps() {
    console.log('=== Iniciando carga de propiedades del homepage ===');

    // Cargar propiedades en arriendo (10 más recientes para grid + 20 con ubicación para mapa)
    try {
        // Primero: cargar propiedades para el GRID (sin requerir ubicación)
        const rentDataGrid = await loadProperties({
            type_service: 'rent',
            limit: 10,
            order: 'newest'
        });

        if (rentDataGrid.properties && rentDataGrid.properties.length > 0) {
            const arriendoContainer = document.getElementById('arriendo-properties-grid');
            if (arriendoContainer) {
                // Mostrar solo las primeras 4 en el grid
                arriendoContainer.innerHTML = rentDataGrid.properties.slice(0, 4).map(prop => createPropertyCard(prop)).join('');
            }
            console.log('Propiedades de arriendo cargadas (grid):', rentDataGrid.properties.length);
        } else {
            console.warn('No se encontraron propiedades de arriendo');
            const arriendoContainer = document.getElementById('arriendo-properties-grid');
            if (arriendoContainer) {
                arriendoContainer.innerHTML = `
                    <div class="col-12 text-center py-5">
                        <i class="fa fa-home fa-3x text-muted mb-3"></i>
                        <p class="text-muted">No hay propiedades de arriendo disponibles en este momento</p>
                    </div>
                `;
            }
        }

        // Segundo: cargar propiedades CON ubicación para el MAPA
        const rentDataMap = await loadProperties({
            type_service: 'rent',
            has_location: true,  // Solo con coordenadas para mapa
            limit: 20,
            order: 'newest'
        });

        if (rentDataMap.properties && rentDataMap.properties.length > 0) {
            rentPropertiesData = rentDataMap.properties;
            console.log('Propiedades de arriendo con ubicación (mapa):', rentPropertiesData.length);
        } else {
            console.warn('No hay propiedades de arriendo con ubicación para el mapa');
            rentPropertiesData = [];
        }
    } catch (err) {
        console.error('Error cargando arriendos:', err);
    }

    // Cargar propiedades usadas en venta (10 para grid + 20 con ubicación para mapa, SIN PROYECTO)
    try {
        // Primero: cargar propiedades para el GRID (sin requerir ubicación)
        const usedSaleDataGrid = await loadProperties({
            type_service: 'sale',
            has_project: false,      // Sin proyecto = propiedades usadas
            limit: 10,
            order: 'newest'
        });

        if (usedSaleDataGrid.properties && usedSaleDataGrid.properties.length > 0) {
            const usedSaleContainer = document.getElementById('used-sale-properties-grid');
            if (usedSaleContainer) {
                // Mostrar solo las primeras 4 en el grid
                usedSaleContainer.innerHTML = usedSaleDataGrid.properties.slice(0, 4).map(prop => createPropertyCard(prop)).join('');
            }
            console.log('Propiedades usadas cargadas (grid):', usedSaleDataGrid.properties.length);
        } else {
            console.warn('No se encontraron propiedades de venta usadas');
            const usedSaleContainer = document.getElementById('used-sale-properties-grid');
            if (usedSaleContainer) {
                usedSaleContainer.innerHTML = `
                    <div class="col-12 text-center py-5">
                        <i class="fa fa-building fa-3x text-muted mb-3"></i>
                        <p class="text-muted">No hay propiedades usadas en venta disponibles en este momento</p>
                    </div>
                `;
            }
        }

        // Segundo: cargar propiedades CON ubicación para el MAPA
        const usedSaleDataMap = await loadProperties({
            type_service: 'sale',
            has_location: true,      // Solo con coordenadas para mapa
            has_project: false,      // Sin proyecto = propiedades usadas
            limit: 20,
            order: 'newest'
        });

        if (usedSaleDataMap.properties && usedSaleDataMap.properties.length > 0) {
            usedSalePropertiesData = usedSaleDataMap.properties;
            console.log('Propiedades usadas con ubicación (mapa):', usedSalePropertiesData.length);
        } else {
            console.warn('No hay propiedades usadas con ubicación para el mapa');
            usedSalePropertiesData = [];
        }
    } catch (err) {
        console.error('Error cargando ventas usadas:', err);
    }

    // Cargar proyectos en venta (10 para grid + 20 con ubicación para mapa, CON PROYECTO)
    try {
        // Primero: cargar proyectos para el GRID (sin requerir ubicación)
        const projectsDataGrid = await loadProperties({
            type_service: 'sale',
            has_project: true,    // Con proyecto = propiedades nuevas/proyectos
            limit: 10,
            order: 'newest'
        });

        if (projectsDataGrid.properties && projectsDataGrid.properties.length > 0) {
            const projectsContainer = document.getElementById('projects-properties-grid');
            if (projectsContainer) {
                // Mostrar solo los primeros 4 en el grid
                projectsContainer.innerHTML = projectsDataGrid.properties.slice(0, 4).map(prop => createPropertyCard(prop)).join('');
            }
            console.log('Proyectos cargados (grid):', projectsDataGrid.properties.length);
        } else {
            console.warn('No se encontraron proyectos');
            const projectsContainer = document.getElementById('projects-properties-grid');
            if (projectsContainer) {
                projectsContainer.innerHTML = `
                    <div class="col-12 text-center py-5">
                        <i class="fa fa-map-marker-alt fa-3x text-muted mb-3"></i>
                        <p class="text-muted">No hay proyectos en venta disponibles en este momento</p>
                    </div>
                `;
            }
        }

        // Segundo: cargar proyectos CON ubicación para el MAPA
        const projectsDataMap = await loadProperties({
            type_service: 'sale',
            has_location: true,   // Solo con coordenadas para mapa
            has_project: true,    // Con proyecto = propiedades nuevas/proyectos
            limit: 20,
            order: 'newest'
        });

        if (projectsDataMap.properties && projectsDataMap.properties.length > 0) {
            projectsPropertiesData = projectsDataMap.properties;
            console.log('Proyectos con ubicación (mapa):', projectsPropertiesData.length);
        } else {
            console.warn('No hay proyectos con ubicación para el mapa');
            projectsPropertiesData = [];
        }
    } catch (err) {
        console.error('Error cargando proyectos:', err);
    }

    // Configurar eventos de las pestañas de mapas
    setupMapTabs();
}

/**
 * Configurar eventos de pestañas de mapas
 */
function setupMapTabs() {
    // Pestaña de arriendo
    const arriendoMapTab = document.getElementById('arriendo-map-tab');
    if (arriendoMapTab) {
        arriendoMapTab.addEventListener('shown.bs.tab', function(e) {
            console.log('Mostrando mapa de arriendos');
            const mapContainer = document.getElementById('arriendo-properties-map');

            if (rentPropertiesData.length === 0) {
                // Sin propiedades con ubicación, mostrar mensaje
                if (mapContainer) {
                    mapContainer.innerHTML = `
                        <div class="d-flex align-items-center justify-content-center h-100 bg-light">
                            <div class="text-center p-4">
                                <i class="fa fa-map-marked-alt fa-3x text-muted mb-3"></i>
                                <p class="text-muted">No hay propiedades con ubicación disponible para mostrar en el mapa</p>
                            </div>
                        </div>
                    `;
                }
            } else {
                // Hay propiedades, mostrar mapa
                if (!arriendoMap) {
                    arriendoMap = initMap('arriendo-properties-map', arriendoMap);
                } else {
                    arriendoMap.invalidateSize();
                }
                if (arriendoMap) {
                    setTimeout(() => {
                        updateMapMarkers(arriendoMap, rentPropertiesData);
                    }, 200);
                }
            }
        });
    }

    // Pestaña de ventas usadas
    const usedSaleMapTab = document.querySelector('[data-bs-target="#used-sale-map"]');
    if (usedSaleMapTab) {
        usedSaleMapTab.addEventListener('shown.bs.tab', function(e) {
            console.log('Mostrando mapa de ventas usadas');
            const mapContainer = document.getElementById('used-sale-properties-map');

            if (usedSalePropertiesData.length === 0) {
                // Sin propiedades con ubicación, mostrar mensaje
                if (mapContainer) {
                    mapContainer.innerHTML = `
                        <div class="d-flex align-items-center justify-content-center h-100 bg-light">
                            <div class="text-center p-4">
                                <i class="fa fa-map-marked-alt fa-3x text-muted mb-3"></i>
                                <p class="text-muted">No hay propiedades con ubicación disponible para mostrar en el mapa</p>
                            </div>
                        </div>
                    `;
                }
            } else {
                // Hay propiedades, mostrar mapa
                if (!usedSaleMap) {
                    usedSaleMap = initMap('used-sale-properties-map', usedSaleMap);
                } else {
                    usedSaleMap.invalidateSize();
                }
                if (usedSaleMap) {
                    setTimeout(() => {
                        updateMapMarkers(usedSaleMap, usedSalePropertiesData);
                    }, 200);
                }
            }
        });
    }

    // Pestaña de proyectos
    const projectsMapTab = document.querySelector('[data-bs-target="#projects-map"]');
    if (projectsMapTab) {
        projectsMapTab.addEventListener('shown.bs.tab', function(e) {
            console.log('Mostrando mapa de proyectos');
            const mapContainer = document.getElementById('projects-properties-map');

            if (projectsPropertiesData.length === 0) {
                // Sin propiedades con ubicación, mostrar mensaje
                if (mapContainer) {
                    mapContainer.innerHTML = `
                        <div class="d-flex align-items-center justify-content-center h-100 bg-light">
                            <div class="text-center p-4">
                                <i class="fa fa-map-marked-alt fa-3x text-muted mb-3"></i>
                                <p class="text-muted">No hay proyectos con ubicación disponible para mostrar en el mapa</p>
                            </div>
                        </div>
                    `;
                }
            } else {
                // Hay propiedades, mostrar mapa
                if (!projectsMap) {
                    projectsMap = initMap('projects-properties-map', projectsMap);
                } else {
                    projectsMap.invalidateSize();
                }
                if (projectsMap) {
                    setTimeout(() => {
                        updateMapMarkers(projectsMap, projectsPropertiesData);
                    }, 200);
                }
            }
        });
    }
}

/**
 * Búsqueda rápida por código
 */
function quickSearchCode() {
    const code = document.getElementById('quickCodeSearch')?.value.trim();
    if (code) {
        window.location.href = '/properties?search=' + encodeURIComponent(code);
    }
}

/**
 * Búsqueda por código desde modal
 */
function searchPropertyByCode() {
    const code = document.getElementById('modalPropertyCode')?.value.trim();
    if (code) {
        // Cerrar modal
        const modalEl = document.getElementById('codeSearchModal');
        if (modalEl) {
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
        }

        // Redirigir a búsqueda
        window.location.href = '/properties?search=' + encodeURIComponent(code);
    } else {
        alert('Por favor ingresa un código de propiedad');
    }
}

/**
 * Inicialización cuando el DOM esté listo
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando BOHIO Homepage Properties...');

    // Botones Arrendar/Comprar
    const serviceBtns = document.querySelectorAll('.service-type-btn');
    const serviceInput = document.getElementById('selectedServiceType');

    if (serviceBtns && serviceInput) {
        serviceBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                serviceBtns.forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                serviceInput.value = this.dataset.service;
            });
        });
    }

    // Enter en campo de código rápido
    const codeInput = document.getElementById('quickCodeSearch');
    if (codeInput) {
        codeInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                quickSearchCode();
            }
        });
    }

    // Enter en modal de código
    const modalInput = document.getElementById('modalPropertyCode');
    if (modalInput) {
        modalInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                searchPropertyByCode();
            }
        });
    }

    // Cargar propiedades del homepage con mapas
    loadHomePropertiesWithMaps();
});

// Exportar funciones globales para uso en plantillas
window.bohioHomepage = {
    quickSearchCode,
    searchPropertyByCode,
    loadProperties,
    initMap,
    updateMapMarkers
};

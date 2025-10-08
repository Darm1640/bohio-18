/** @odoo-module **/

console.log('BOHIO Proyectos JS cargado');

let proyectosMap = null;
let proyectosMarkers = null;

// Hacer funciones globales para que funcionen con onclick
window.toggleMapaProyectos = function() {
    const mapContainer = document.getElementById('proyectosMapContainer');
    const toggleText = document.getElementById('mapaToggleText');

    if (mapContainer.style.display === 'none') {
        mapContainer.style.display = 'block';
        toggleText.textContent = 'Ocultar Mapa';

        // Refresh map size
        setTimeout(() => {
            if (proyectosMap) {
                proyectosMap.invalidateSize();
            }
        }, 100);
    } else {
        mapContainer.style.display = 'none';
        toggleText.textContent = 'Ver Mapa';
    }
};

function inicializarMapaProyectos() {
    if (typeof L === 'undefined') {
        console.warn('Leaflet no está cargado');
        return;
    }

    const mapElement = document.getElementById('proyectosMap');
    if (!mapElement) return;

    proyectosMap = L.map('proyectosMap').setView([4.7110, -74.0721], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(proyectosMap);

    proyectosMarkers = L.layerGroup().addTo(proyectosMap);
}

function actualizarMapaProyectos(proyectos) {
    if (!proyectosMap || !proyectosMarkers) return;

    proyectosMarkers.clearLayers();
    const bounds = [];

    proyectos.forEach(proyecto => {
        if (proyecto.latitude && proyecto.longitude) {
            const marker = L.marker([proyecto.latitude, proyecto.longitude]);

            const popupContent = `
                <div style="min-width: 200px;">
                    <h6 class="fw-bold text-danger mb-2">${proyecto.name}</h6>
                    <p class="small text-muted mb-2">${proyecto.ubicacion || ''}</p>
                    <p class="small mb-2">
                        <strong>${proyecto.disponibles || 0}</strong> unidades disponibles
                    </p>
                    <a href="/properties?project_id=${proyecto.id}" class="btn btn-danger btn-sm w-100">
                        Ver Unidades
                    </a>
                </div>
            `;

            marker.bindPopup(popupContent);
            proyectosMarkers.addLayer(marker);
            bounds.push([proyecto.latitude, proyecto.longitude]);
        }
    });

    if (bounds.length > 0) {
        proyectosMap.fitBounds(bounds, { padding: [50, 50] });
    }
}

function renderizarProyectos(proyectos) {
    const container = document.getElementById('proyectosContainer');
    if (!container) return;

    if (proyectos.length === 0) {
        container.innerHTML = `
            <div class="col-12 text-center py-5">
                <i class="fa fa-building fa-3x text-muted mb-3"></i>
                <p class="text-muted">No se encontraron proyectos</p>
            </div>
        `;
        return;
    }

    container.innerHTML = '';

    proyectos.forEach(proyecto => {
        const card = document.createElement('div');
        card.className = 'col-md-6 col-lg-4';
        card.innerHTML = `
            <div class="card h-100 border-0 shadow-sm hover-lift">
                ${proyecto.image_url ? `
                    <img src="${proyecto.image_url}"
                         class="card-img-top"
                         alt="${proyecto.name}"
                         style="height: 200px; object-fit: cover;">
                ` : `
                    <div class="bg-light d-flex align-items-center justify-content-center"
                         style="height: 200px;">
                        <i class="fa fa-building fa-3x text-muted"></i>
                    </div>
                `}
                <div class="card-body p-4 d-flex flex-column h-100">
                    <h3 class="h5 fw-bold text-danger mb-2">${proyecto.name}</h3>
                    <p class="text-muted small mb-3">
                        <i class="fa fa-map-marker text-danger me-1"></i>
                        ${proyecto.ubicacion || 'Sin ubicación'}
                    </p>
                    <p class="text-muted small mb-3">${proyecto.descripcion || 'Proyecto inmobiliario de alta calidad'}</p>

                    <div class="proyecto-stats mb-3">
                        <div class="row g-2 small">
                            <div class="col-6">
                                <i class="fa fa-building text-muted me-1"></i>
                                <span class="text-muted">${proyecto.unidades || 0} Unidades</span>
                            </div>
                            <div class="col-6">
                                <i class="fa fa-home text-muted me-1"></i>
                                <span class="text-muted">${proyecto.disponibles || 0} Disponibles</span>
                            </div>
                        </div>
                    </div>

                    <div class="mt-auto">
                        <div class="d-flex gap-2">
                            <a href="/properties?project_id=${proyecto.id}" class="btn btn-outline-danger btn-sm flex-fill">
                                <i class="fa fa-th me-1"></i>Ver Unidades
                            </a>
                            <a href="/contacto?proyecto=${proyecto.id}" class="btn btn-danger btn-sm flex-fill">
                                <i class="fa fa-envelope me-1"></i>Contactar
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

async function cargarProyectos() {
    try {
        const response = await fetch('/bohio/api/proyectos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({})
        });

        const data = await response.json();
        const result = data.result || data;
        const proyectos = result.proyectos || [];

        console.log('Proyectos cargados:', proyectos.length);

        renderizarProyectos(proyectos);
        actualizarMapaProyectos(proyectos);

    } catch (error) {
        console.error('Error cargando proyectos:', error);
        const container = document.getElementById('proyectosContainer');
        if (container) {
            container.innerHTML = `
                <div class="col-12 text-center py-5">
                    <i class="fa fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                    <p class="text-muted">Error al cargar proyectos</p>
                </div>
            `;
        }
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    const proyectosPage = document.querySelector('.bohio-proyectos-page');
    if (proyectosPage) {
        console.log('Inicializando página de proyectos...');
        inicializarMapaProyectos();
        cargarProyectos();
    }
});

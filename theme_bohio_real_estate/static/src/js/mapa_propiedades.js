/** @odoo-module **/

import { jsonrpc } from "@web/core/network/rpc_service";

// ==========================================
// CONFIGURACIÓN DE LEAFLET
// ==========================================
// IMPORTANTE: Rutas apuntan a real_estate_bits (módulo base)
document.addEventListener('DOMContentLoaded', function() {
    if (typeof L !== 'undefined') {
        L.Icon.Default.mergeOptions({
            iconRetinaUrl: '/real_estate_bits/static/src/lib/leaflet/images/marker-icon-2x.png',
            iconUrl: '/real_estate_bits/static/src/lib/leaflet/images/marker-icon.png',
            shadowUrl: '/real_estate_bits/static/src/lib/leaflet/images/marker-shadow.png'
        });
    }
});

// ==========================================
// CONSTANTES
// ==========================================
const DISTANCE_THRESHOLD_KM = 5; // 5 km para mostrar nombres
const ZOOM_WITH_USER = 13;
const DEFAULT_CENTER = [8.7479, -75.8814]; // Montería [lat, lng]
const DEFAULT_ZOOM = 12;

// ==========================================
// VARIABLES GLOBALES
// ==========================================
let map = null;
let userLocation = null;
let allMarkers = [];
let userMarker = null;
let markersLayer = null;

// ==========================================
// FUNCIONES DE GEOLOCALIZACIÓN
// ==========================================
function calculateDistance(lat1, lng1, lat2, lng2) {
    const R = 6371; // Radio de la Tierra en km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

async function tryGeolocation() {
    return new Promise((resolve) => {
        if (!navigator.geolocation) {
            console.log('Geolocation not supported');
            resolve(null);
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                userLocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                console.log('User location obtained:', userLocation);
                resolve(userLocation);
            },
            (error) => {
                console.log('Geolocation error:', error.message);
                resolve(null);
            },
            {
                timeout: 5000,
                enableHighAccuracy: false,
                maximumAge: 300000 // 5 minutos
            }
        );
    });
}

function showUserLocationOnMap() {
    if (!userLocation || !map) return;

    // Remover marcador anterior si existe
    if (userMarker) {
        map.removeLayer(userMarker);
    }

    // Crear icono de usuario personalizado
    const userIcon = L.divIcon({
        className: 'user-location-marker',
        html: '<div class="user-location-pulse"></div>',
        iconSize: [20, 20],
        iconAnchor: [10, 10]
    });

    // Crear marcador de usuario
    userMarker = L.marker([userLocation.lat, userLocation.lng], {
        icon: userIcon,
        zIndexOffset: 1000
    }).addTo(map);

    userMarker.bindPopup('<strong>Tu ubicación</strong>').openPopup();

    // Centrar mapa en usuario
    map.setView([userLocation.lat, userLocation.lng], ZOOM_WITH_USER);
}

function updateMarkersDistance() {
    if (!userLocation) {
        // Si no hay ubicación, mostrar todos los precios
        allMarkers.forEach(marker => {
            const el = marker.getElement();
            if (el) {
                const priceEl = el.querySelector('.bohio-marker-price');
                const nameEl = el.querySelector('.bohio-marker-name');
                if (priceEl && nameEl) {
                    priceEl.style.display = 'block';
                    nameEl.style.display = 'none';
                }
            }
        });
        return;
    }

    // Actualizar cada marcador según distancia
    allMarkers.forEach(marker => {
        const property = marker.property;
        const distance = calculateDistance(
            userLocation.lat,
            userLocation.lng,
            property.lat,
            property.lng
        );

        const el = marker.getElement();
        if (el) {
            const priceEl = el.querySelector('.bohio-marker-price');
            const nameEl = el.querySelector('.bohio-marker-name');

            if (priceEl && nameEl) {
                if (distance <= DISTANCE_THRESHOLD_KM) {
                    // Mostrar nombre con distancia
                    priceEl.style.display = 'none';
                    nameEl.style.display = 'block';

                    const distText = distance < 1
                        ? `${Math.round(distance * 1000)}m`
                        : `${distance.toFixed(1)}km`;
                    nameEl.textContent = `${property.name} (${distText})`;
                } else {
                    // Mostrar precio
                    priceEl.style.display = 'block';
                    nameEl.style.display = 'none';
                }
            }
        }
    });
}

// ==========================================
// MANEJO DE CASOS SIN DATOS
// ==========================================
function showNoDataMessage(message, type = 'no-properties') {
    const overlay = document.createElement('div');
    overlay.id = 'no-data-overlay';
    overlay.className = 'map-overlay';
    overlay.innerHTML = `
        <div class="no-data-card">
            <div class="no-data-icon">
                ${type === 'no-properties' ? '🏠' : '📍'}
            </div>
            <h3>${message}</h3>
            <div class="no-data-actions">
                ${type === 'no-properties' ? `
                    <a href="/shop" class="btn btn-danger">
                        <i class="bi bi-list-ul"></i> Ver Todas las Propiedades
                    </a>
                ` : `
                    <button onclick="window.manualGeolocate()" class="btn btn-danger">
                        <i class="bi bi-geo-alt-fill"></i> Intentar de Nuevo
                    </button>
                `}
            </div>
        </div>
    `;
    document.querySelector('.map-container').appendChild(overlay);
}

function hideLoadingOverlay() {
    const loading = document.getElementById('map-loading');
    if (loading) {
        loading.style.display = 'none';
    }
}

// ==========================================
// CREACIÓN DE MARCADORES
// ==========================================
function createPropertyMarker(property) {
    // Usar Bootstrap Icons según el tipo de propiedad
    let iconClass = 'bi-house-fill';
    if (property.type === 'rent') {
        iconClass = 'bi-key-fill';
    } else if (property.type === 'sale_rent') {
        iconClass = 'bi-building-fill';
    }

    const markerHtml = `
        <div class="bohio-marker-card">
            <div class="bohio-marker-icon">
                <i class="bi ${iconClass}"></i>
            </div>
            <div class="bohio-marker-price">${property.price}</div>
            <div class="bohio-marker-name" style="display: none;">
                ${property.name}
            </div>
        </div>
    `;

    const icon = L.divIcon({
        className: 'bohio-marker',
        html: markerHtml,
        iconSize: [null, null],
        iconAnchor: [45, 55]
    });

    const marker = L.marker([property.lat, property.lng], {
        icon: icon
    });

    // Popup con información de la propiedad
    const popupContent = `
        <div class="property-popup">
            <h5 class="mb-2">${property.name}</h5>
            <p class="mb-1"><strong>${property.price}</strong></p>
            ${property.bedrooms ? `<p class="mb-1 small"><i class="bi bi-bed"></i> ${property.bedrooms} hab</p>` : ''}
            ${property.bathrooms ? `<p class="mb-1 small"><i class="bi bi-droplet"></i> ${property.bathrooms} baños</p>` : ''}
            ${property.area ? `<p class="mb-1 small"><i class="bi bi-rulers"></i> ${property.area} m²</p>` : ''}
            ${property.address ? `<p class="mb-2 small text-muted">${property.address}</p>` : ''}
            <a href="${property.url}" class="btn btn-danger btn-sm w-100">
                <i class="bi bi-eye"></i> Ver Detalles
            </a>
        </div>
    `;

    marker.bindPopup(popupContent);

    // Guardar referencia a la propiedad en el marcador
    marker.property = property;

    return marker;
}

// ==========================================
// INICIALIZACIÓN DEL MAPA
// ==========================================
async function initMap() {
    console.log('Initializing Bohio Map with OpenStreetMap...');

    // Intentar geolocalización automática
    await tryGeolocation();

    // Obtener propiedades del servidor
    let data;
    try {
        data = await jsonrpc('/api/properties/mapa', {
            user_lat: userLocation?.lat,
            user_lng: userLocation?.lng
        });
        console.log('Properties loaded:', data.property_count);

        // Actualizar contador
        const countEl = document.getElementById('property-count');
        if (countEl) {
            countEl.textContent = data.property_count;
        }
    } catch (error) {
        console.error('Error loading properties:', error);
        hideLoadingOverlay();
        showNoDataMessage('Error al cargar propiedades', 'no-properties');
        return;
    }

    // Crear mapa de Leaflet
    map = L.map('bohio-map', {
        center: [data.center.lat, data.center.lng],
        zoom: data.zoom,
        zoomControl: true,
        scrollWheelZoom: true
    });

    // Añadir capa de OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    // Si hay propiedades, crear marcadores
    if (data.properties && data.properties.length > 0) {
        // Crear capa para los marcadores
        markersLayer = L.layerGroup().addTo(map);

        data.properties.forEach(property => {
            const marker = createPropertyMarker(property);
            marker.addTo(markersLayer);
            allMarkers.push(marker);
        });

        // Si hay ubicación de usuario, mostrarla
        if (userLocation) {
            showUserLocationOnMap();
        }

        // Actualizar marcadores según distancia
        updateMarkersDistance();

        // Event listeners para actualizar al mover/zoom
        map.on('zoomend', updateMarkersDistance);
        map.on('moveend', updateMarkersDistance);

    } else {
        // No hay propiedades
        const message = data.has_user_location
            ? 'No se encontraron propiedades cerca de tu ubicación'
            : 'No se encontraron propiedades disponibles';
        showNoDataMessage(message, 'no-properties');
    }

    hideLoadingOverlay();
}

// ==========================================
// GEOLOCALIZACIÓN MANUAL
// ==========================================
window.manualGeolocate = async function() {
    const overlay = document.getElementById('no-data-overlay');
    if (overlay) overlay.remove();

    const loadingEl = document.getElementById('map-loading');
    if (loadingEl) {
        loadingEl.style.display = 'flex';
    }

    await tryGeolocation();
    if (userLocation) {
        showUserLocationOnMap();

        // Recargar propiedades con nueva ubicación
        const data = await jsonrpc('/api/properties/mapa', {
            user_lat: userLocation.lat,
            user_lng: userLocation.lng
        });

        // Actualizar contador
        const countEl = document.getElementById('property-count');
        if (countEl) {
            countEl.textContent = data.property_count;
        }

        // Limpiar marcadores anteriores
        if (markersLayer) {
            markersLayer.clearLayers();
        }
        allMarkers = [];

        // Crear nuevos marcadores
        data.properties.forEach(property => {
            const marker = createPropertyMarker(property);
            marker.addTo(markersLayer);
            allMarkers.push(marker);
        });

        updateMarkersDistance();

        if (data.properties.length === 0) {
            showNoDataMessage('No se encontraron propiedades cerca de tu ubicación', 'no-properties');
        }
    } else {
        showNoDataMessage('No se pudo obtener tu ubicación. Por favor, verifica los permisos del navegador.', 'no-location');
    }

    hideLoadingOverlay();
};

// ==========================================
// INICIO
// ==========================================
document.addEventListener('DOMContentLoaded', function() {
    // Botón de geolocalización manual
    const btnGeolocate = document.getElementById('btn-geolocate');
    if (btnGeolocate) {
        btnGeolocate.addEventListener('click', window.manualGeolocate);
    }

    // Inicializar mapa cuando Leaflet esté listo
    if (typeof L !== 'undefined') {
        initMap();
    } else {
        console.error('Leaflet not loaded');
    }
});

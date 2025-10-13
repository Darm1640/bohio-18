/** @odoo-module **/

// =============================================================================
// BOHIO REAL ESTATE - MAP MARKERS (DOM)
// =============================================================================
// Creación de marcadores usando createElement (sin HTML strings)
// Basado en mejores prácticas de Odoo 18

import { calculateDistance, formatDistance, DISTANCE_THRESHOLD_KM } from '../utils/geolocation';

// -----------------------------------------------------------------------------
// CREACIÓN DE MARCADORES
// -----------------------------------------------------------------------------

/**
 * Crea un icono de Bootstrap según el tipo de propiedad
 * @param {string} type - Tipo de propiedad ('rent', 'sale', 'sale_rent')
 * @returns {HTMLElement}
 */
function createMarkerIcon(type) {
    const icon = document.createElement('i');

    // Determinar clase de icono según tipo
    let iconClass = 'bi-house-fill';
    if (type === 'rent') {
        iconClass = 'bi-key-fill';
    } else if (type === 'sale_rent') {
        iconClass = 'bi-building-fill';
    }

    icon.className = `bi ${iconClass}`;
    return icon;
}

/**
 * Crea el contenedor del icono del marcador
 * @param {string} type - Tipo de propiedad
 * @returns {HTMLElement}
 */
function createMarkerIconContainer(type) {
    const container = document.createElement('div');
    container.className = 'bohio-marker-icon';
    container.appendChild(createMarkerIcon(type));
    return container;
}

/**
 * Crea el elemento del precio del marcador
 * @param {string} price - Precio formateado
 * @returns {HTMLElement}
 */
function createMarkerPrice(price) {
    const priceEl = document.createElement('div');
    priceEl.className = 'bohio-marker-price';
    priceEl.textContent = price;
    return priceEl;
}

/**
 * Crea el elemento del nombre del marcador (oculto por defecto)
 * @param {string} name - Nombre de la propiedad
 * @returns {HTMLElement}
 */
function createMarkerName(name) {
    const nameEl = document.createElement('div');
    nameEl.className = 'bohio-marker-name';
    nameEl.style.display = 'none';
    nameEl.textContent = name;
    return nameEl;
}

/**
 * Crea el HTML del marcador usando createElement (sin template strings)
 * @param {Object} property - Datos de la propiedad
 * @returns {HTMLElement}
 */
function createMarkerElement(property) {
    const card = document.createElement('div');
    card.className = 'bohio-marker-card';

    // Agregar componentes
    card.appendChild(createMarkerIconContainer(property.type));
    card.appendChild(createMarkerPrice(property.price));
    card.appendChild(createMarkerName(property.name));

    return card;
}

// -----------------------------------------------------------------------------
// POPUP DE PROPIEDAD
// -----------------------------------------------------------------------------

/**
 * Crea el título del popup
 * @param {string} name - Nombre de la propiedad
 * @returns {HTMLElement}
 */
function createPopupTitle(name) {
    const h5 = document.createElement('h5');
    h5.className = 'mb-2';
    h5.textContent = name;
    return h5;
}

/**
 * Crea elemento de precio en el popup
 * @param {string} price - Precio formateado
 * @returns {HTMLElement}
 */
function createPopupPrice(price) {
    const p = document.createElement('p');
    p.className = 'mb-1';

    const strong = document.createElement('strong');
    strong.textContent = price;

    p.appendChild(strong);
    return p;
}

/**
 * Crea una característica del popup (habitaciones, baños, área)
 * @param {string} iconClass - Clase del icono Bootstrap
 * @param {string} text - Texto de la característica
 * @returns {HTMLElement|null}
 */
function createPopupFeature(iconClass, text) {
    if (!text) return null;

    const p = document.createElement('p');
    p.className = 'mb-1 small';

    const icon = document.createElement('i');
    icon.className = `bi ${iconClass}`;

    p.appendChild(icon);
    p.appendChild(document.createTextNode(` ${text}`));

    return p;
}

/**
 * Crea el botón de detalles del popup
 * @param {string} url - URL de la propiedad
 * @returns {HTMLElement}
 */
function createPopupButton(url) {
    const a = document.createElement('a');
    a.href = url;
    a.className = 'btn btn-danger btn-sm w-100';

    const icon = document.createElement('i');
    icon.className = 'bi bi-eye';

    a.appendChild(icon);
    a.appendChild(document.createTextNode(' Ver Detalles'));

    return a;
}

/**
 * Crea el contenido del popup usando createElement (sin HTML strings)
 * @param {Object} property - Datos de la propiedad
 * @returns {HTMLElement}
 */
function createPopupElement(property) {
    const container = document.createElement('div');
    container.className = 'property-popup';

    // Título
    container.appendChild(createPopupTitle(property.name));

    // Precio
    container.appendChild(createPopupPrice(property.price));

    // Características (solo si existen)
    const features = [
        { icon: 'bi-bed', text: property.bedrooms ? `${property.bedrooms} hab` : null },
        { icon: 'bi-droplet', text: property.bathrooms ? `${property.bathrooms} baños` : null },
        { icon: 'bi-rulers', text: property.area ? `${property.area} m²` : null }
    ];

    features.forEach(feature => {
        const featureEl = createPopupFeature(feature.icon, feature.text);
        if (featureEl) {
            container.appendChild(featureEl);
        }
    });

    // Dirección (si existe)
    if (property.address) {
        const address = document.createElement('p');
        address.className = 'mb-2 small text-muted';
        address.textContent = property.address;
        container.appendChild(address);
    }

    // Botón
    container.appendChild(createPopupButton(property.url));

    return container;
}

// -----------------------------------------------------------------------------
// CREACIÓN DEL MARCADOR DE LEAFLET
// -----------------------------------------------------------------------------

/**
 * Crea un marcador de Leaflet para una propiedad
 * @param {Object} property - Datos de la propiedad
 * @param {Object} L - Objeto Leaflet
 * @returns {Object} Marcador de Leaflet
 */
export function createPropertyMarker(property, L) {
    // Crear elemento del marcador
    const markerElement = createMarkerElement(property);

    // Crear icono de Leaflet
    const icon = L.divIcon({
        className: 'bohio-marker',
        html: markerElement.outerHTML,
        iconSize: [null, null],
        iconAnchor: [45, 55]
    });

    // Crear marcador
    const marker = L.marker([property.lat, property.lng], {
        icon: icon
    });

    // Crear y vincular popup
    const popupElement = createPopupElement(property);
    marker.bindPopup(popupElement);

    // Guardar referencia a la propiedad
    marker.property = property;

    return marker;
}

// -----------------------------------------------------------------------------
// ACTUALIZACIÓN DE MARCADORES SEGÚN DISTANCIA
// -----------------------------------------------------------------------------

/**
 * Actualiza la visualización de los marcadores según la distancia del usuario
 * @param {Array} markers - Array de marcadores de Leaflet
 * @param {Object|null} userLocation - Ubicación del usuario {lat, lng}
 */
export function updateMarkersDistance(markers, userLocation) {
    if (!userLocation) {
        // Si no hay ubicación, mostrar todos los precios
        markers.forEach(marker => {
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
    markers.forEach(marker => {
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

                    const distText = formatDistance(distance);
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

// -----------------------------------------------------------------------------
// MARCADOR DE USUARIO
// -----------------------------------------------------------------------------

/**
 * Crea el icono del marcador de usuario
 * @param {Object} L - Objeto Leaflet
 * @returns {Object} Icono de Leaflet
 */
export function createUserLocationIcon(L) {
    return L.divIcon({
        className: 'user-location-marker',
        html: '<div class="user-location-pulse"></div>',
        iconSize: [20, 20],
        iconAnchor: [10, 10]
    });
}

/**
 * Crea un marcador para la ubicación del usuario
 * @param {Object} userLocation - {lat, lng}
 * @param {Object} L - Objeto Leaflet
 * @returns {Object} Marcador de Leaflet
 */
export function createUserMarker(userLocation, L) {
    const icon = createUserLocationIcon(L);

    const marker = L.marker([userLocation.lat, userLocation.lng], {
        icon: icon,
        zIndexOffset: 1000
    });

    marker.bindPopup('<strong>Tu ubicación</strong>');

    return marker;
}

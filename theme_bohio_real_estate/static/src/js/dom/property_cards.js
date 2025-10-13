/** @odoo-module **/

// =============================================================================
// BOHIO REAL ESTATE - PROPERTY CARDS (DOM)
// =============================================================================
// Creación de tarjetas de propiedades usando createElement (sin HTML strings)
// Reutilizable en homepage, shop, búsquedas, etc.

import { createElement, createLink } from '../utils/dom_helpers';

// -----------------------------------------------------------------------------
// HELPERS DE FORMATO
// -----------------------------------------------------------------------------

/**
 * Formatea precio en COP
 * @param {number} price - Precio
 * @returns {string}
 */
function formatPrice(price) {
    if (!price) return 'Consultar';

    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: 0
    }).format(price);
}

/**
 * Obtiene el label del precio según tipo de servicio
 * @param {string} typeService - Tipo de servicio
 * @returns {string}
 */
function getPriceLabel(typeService) {
    if (typeService === 'rent') return 'Arriendo/mes';
    if (typeService === 'sale_rent') return 'Venta o Arriendo';
    return 'Venta';
}

// -----------------------------------------------------------------------------
// COMPONENTES DE TARJETA
// -----------------------------------------------------------------------------

/**
 * Crea imagen de la propiedad
 * @param {Object} property
 * @returns {HTMLElement}
 */
function createPropertyImage(property) {
    const img = document.createElement('img');
    img.src = property.image_url || '/theme_bohio_real_estate/static/src/img/placeholder.jpg';
    img.className = 'card-img-top';
    img.alt = property.name;
    img.style.height = '200px';
    img.style.objectFit = 'cover';
    img.loading = 'lazy';
    img.onerror = function() {
        this.src = '/theme_bohio_real_estate/static/src/img/placeholder.jpg';
    };

    return img;
}

/**
 * Crea badge de proyecto
 * @param {Object} property
 * @returns {HTMLElement|null}
 */
function createProjectBadge(property) {
    if (!property.project_id || !property.project_name) return null;

    const container = createElement('div', 'position-absolute top-0 end-0 m-2');

    const link = document.createElement('a');
    link.href = `/proyecto/${property.project_id}`;
    link.className = 'badge bg-danger text-white text-decoration-none';
    link.style.fontSize = '0.7rem';
    link.style.padding = '0.4rem 0.6rem';

    const icon = createElement('i', 'bi bi-building me-1');
    link.appendChild(icon);
    link.appendChild(document.createTextNode(property.project_name));

    container.appendChild(link);
    return container;
}

/**
 * Crea título de la propiedad
 * @param {string} name
 * @returns {HTMLElement}
 */
function createPropertyTitle(name) {
    const h5 = createElement('h5', 'card-title text-truncate', name);
    h5.title = name;
    return h5;
}

/**
 * Crea ubicación de la propiedad
 * @param {Object} property
 * @returns {HTMLElement}
 */
function createPropertyLocation(property) {
    const p = createElement('p', 'text-muted small mb-2');

    const icon = createElement('i', 'bi bi-geo-alt-fill me-1');
    p.appendChild(icon);

    const location = (property.city && property.state) ?
        `${property.city}, ${property.state}` :
        (property.city || property.state || 'No especificado');

    p.appendChild(document.createTextNode(location));

    return p;
}

/**
 * Crea descripción corta
 * @param {string} description
 * @returns {HTMLElement|null}
 */
function createPropertyDescription(description) {
    if (!description) return null;

    const shortDesc = description.substring(0, 100) + '...';
    return createElement('p', 'text-muted small mb-2', shortDesc);
}

/**
 * Crea características (habitaciones, baños, área)
 * @param {Object} property
 * @returns {HTMLElement}
 */
function createPropertyFeatures(property) {
    const container = createElement('div', 'd-flex justify-content-between mb-2');

    const features = [
        { icon: 'bi-bed', value: property.bedrooms || 0 },
        { icon: 'bi-droplet', value: property.bathrooms || 0 },
        { icon: 'bi-rulers', value: property.area || 0, unit: 'm²' }
    ];

    features.forEach(feature => {
        const span = createElement('span', 'small');

        const icon = createElement('i', `bi ${feature.icon} me-1`);
        span.appendChild(icon);

        const text = feature.unit ?
            `${feature.value} ${feature.unit}` :
            feature.value.toString();

        span.appendChild(document.createTextNode(text));
        container.appendChild(span);
    });

    return container;
}

/**
 * Crea sección de precio
 * @param {Object} property
 * @returns {HTMLElement}
 */
function createPropertyPrice(property) {
    const container = createElement('div', 'mb-2');

    const label = createElement('small', 'text-muted', getPriceLabel(property.type_service));
    container.appendChild(label);

    const price = createElement('h4', 'text-danger mb-0', formatPrice(property.price));
    container.appendChild(price);

    return container;
}

/**
 * Crea botón de detalles
 * @param {number} propertyId
 * @returns {HTMLElement}
 */
function createDetailsButton(propertyId) {
    return createLink({
        href: `/property/${propertyId}`,
        text: 'Ver detalles',
        className: 'btn btn-outline-danger w-100 mt-auto'
    });
}

// -----------------------------------------------------------------------------
// TARJETA COMPLETA
// -----------------------------------------------------------------------------

/**
 * Crea tarjeta completa de propiedad
 * @param {Object} property - Datos de la propiedad
 * @returns {HTMLElement}
 */
export function createPropertyCard(property) {
    // Container principal
    const col = createElement('div', 'col-md-3');

    const card = createElement('div', 'card h-100 shadow-sm border-0 bohio-property-card position-relative');

    // Badge de proyecto (si existe)
    const projectBadge = createProjectBadge(property);
    if (projectBadge) {
        card.appendChild(projectBadge);
    }

    // Imagen
    card.appendChild(createPropertyImage(property));

    // Card body
    const cardBody = createElement('div', 'card-body d-flex flex-column');

    // Título
    cardBody.appendChild(createPropertyTitle(property.name));

    // Ubicación
    cardBody.appendChild(createPropertyLocation(property));

    // Descripción (opcional)
    const description = createPropertyDescription(property.description);
    if (description) {
        cardBody.appendChild(description);
    }

    // Características
    cardBody.appendChild(createPropertyFeatures(property));

    // Precio
    cardBody.appendChild(createPropertyPrice(property));

    // Botón
    cardBody.appendChild(createDetailsButton(property.id));

    card.appendChild(cardBody);
    col.appendChild(card);

    return col;
}

// -----------------------------------------------------------------------------
// MENSAJE DE ESTADO VACÍO
// -----------------------------------------------------------------------------

/**
 * Crea mensaje cuando no hay propiedades
 * @param {Object} options
 * @param {string} options.icon - Clase del icono Bootstrap
 * @param {string} options.message - Mensaje a mostrar
 * @returns {HTMLElement}
 */
export function createEmptyState(options) {
    const col = createElement('div', 'col-12 text-center py-5');

    const icon = createElement('i', `bi ${options.icon} fa-3x text-muted mb-3`);
    col.appendChild(icon);

    const message = createElement('p', 'text-muted', options.message);
    col.appendChild(message);

    return col;
}

// -----------------------------------------------------------------------------
// POPUP DE MAPA
// -----------------------------------------------------------------------------

/**
 * Crea contenido del popup para el mapa
 * @param {Object} property - Datos de la propiedad
 * @returns {HTMLElement}
 */
export function createMapPopup(property) {
    const container = createElement('div');
    container.style.minWidth = '280px';
    container.style.maxWidth = '300px';

    // Imagen
    const img = document.createElement('img');
    img.src = property.image_url || '/theme_bohio_real_estate/static/src/img/placeholder.jpg';
    img.alt = property.name;
    img.style.width = '100%';
    img.style.height = '160px';
    img.style.objectFit = 'cover';
    img.style.borderRadius = '8px';
    img.style.marginBottom = '12px';
    img.onerror = function() {
        this.src = '/theme_bohio_real_estate/static/src/img/placeholder.jpg';
    };
    container.appendChild(img);

    // Título
    const h6 = createElement('h6', 'fw-bold mb-2', property.name);
    h6.style.fontSize = '14px';
    container.appendChild(h6);

    // Ubicación
    const locationP = createElement('p', 'small mb-2 text-muted');
    const locationIcon = createElement('i', 'bi bi-geo-alt-fill text-danger me-1');
    locationP.appendChild(locationIcon);

    const neighborhood = property.neighborhood ? `${property.neighborhood}, ` : '';
    const location = `${neighborhood}${property.city || property.state || ''}`;
    locationP.appendChild(document.createTextNode(location));
    container.appendChild(locationP);

    // Precio
    const priceContainer = createElement('div', 'mb-2');
    const priceLabel = createElement('small', 'text-muted d-block', getPriceLabel(property.type_service));
    priceContainer.appendChild(priceLabel);

    const price = createElement('p', 'mb-2 text-danger fw-bold', formatPrice(property.price));
    price.style.fontSize = '16px';
    priceContainer.appendChild(price);
    container.appendChild(priceContainer);

    // Características
    const featuresDiv = createElement('div', 'd-flex gap-3 mb-3');
    featuresDiv.style.fontSize = '13px';
    featuresDiv.style.color = '#666';

    const area = property.total_area || property.built_area || 0;
    const bedrooms = property.bedrooms || 0;
    const bathrooms = property.bathrooms || 0;

    if (area > 0) {
        const areaSpan = createElement('span');
        const areaIcon = createElement('i', 'bi bi-rulers me-1');
        areaSpan.appendChild(areaIcon);
        areaSpan.appendChild(document.createTextNode(`${area} m²`));
        featuresDiv.appendChild(areaSpan);
    }

    if (bedrooms > 0) {
        const bedroomsSpan = createElement('span');
        const bedroomsIcon = createElement('i', 'bi bi-bed me-1');
        bedroomsSpan.appendChild(bedroomsIcon);
        bedroomsSpan.appendChild(document.createTextNode(`${bedrooms} hab`));
        featuresDiv.appendChild(bedroomsSpan);
    }

    if (bathrooms > 0) {
        const bathroomsSpan = createElement('span');
        const bathroomsIcon = createElement('i', 'bi bi-droplet me-1');
        bathroomsSpan.appendChild(bathroomsIcon);
        bathroomsSpan.appendChild(document.createTextNode(`${bathrooms} baños`));
        featuresDiv.appendChild(bathroomsSpan);
    }

    container.appendChild(featuresDiv);

    // Botón
    const link = document.createElement('a');
    link.href = `/property/${property.id}`;
    link.className = 'btn btn-sm btn-danger w-100';
    link.style.background = '#E31E24';
    link.style.border = 'none';

    const linkIcon = createElement('i', 'bi bi-eye me-1');
    link.appendChild(linkIcon);
    link.appendChild(document.createTextNode('Ver detalles'));

    container.appendChild(link);

    return container;
}

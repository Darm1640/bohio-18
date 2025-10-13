/** @odoo-module **/

/**
 * Template Renderer Utility
 *
 * Utilidad para renderizar templates QWeb desde JavaScript
 * Evita el uso de HTML strings (anti-pattern)
 *
 * USO:
 * import { renderTemplate } from './utils/template_renderer';
 *
 * const html = renderTemplate('property_card_shop_template', {
 *     property: propertyData
 * });
 */

import { loadJS, loadCSS } from "@web/core/assets";
import { renderToString } from "@web/core/utils/render";

/**
 * Renderiza un template QWeb a HTML string
 * @param {string} templateId - ID del template (ej: 'theme_bohio_real_estate.property_card_shop_template')
 * @param {Object} context - Contexto de datos para el template
 * @returns {string} HTML string renderizado
 */
export function renderTemplate(templateId, context = {}) {
    try {
        // Si el templateId no tiene el prefijo del módulo, agregarlo
        const fullTemplateId = templateId.includes('.')
            ? templateId
            : `theme_bohio_real_estate.${templateId}`;

        // Renderizar usando el sistema de Odoo
        return renderToString(fullTemplateId, context);
    } catch (error) {
        console.error(`[TemplateRenderer] Error rendering template ${templateId}:`, error);
        return '';
    }
}

/**
 * Crea elementos DOM desde un template QWeb
 * @param {string} templateId - ID del template
 * @param {Object} context - Contexto de datos
 * @returns {HTMLElement} Elemento DOM
 */
export function createElementFromTemplate(templateId, context = {}) {
    const htmlString = renderTemplate(templateId, context);
    const temp = document.createElement('div');
    temp.innerHTML = htmlString.trim();
    return temp.firstElementChild;
}

/**
 * Renderiza una lista de items usando un template
 * @param {string} templateId - ID del template
 * @param {Array} items - Array de items a renderizar
 * @param {string} itemKey - Nombre de la clave en el contexto (default: 'item')
 * @returns {string} HTML string con todos los items renderizados
 */
export function renderList(templateId, items, itemKey = 'item') {
    if (!Array.isArray(items) || items.length === 0) {
        return '';
    }

    return items.map(item => {
        const context = { [itemKey]: item };
        return renderTemplate(templateId, context);
    }).join('');
}

/**
 * Prepara datos de propiedad para templates
 * Agrega campos computados necesarios para la renderización
 */
export function preparePropertyData(property) {
    // Imports de formatters
    const { formatPrice, formatLocation, formatArea, getPriceLabel } =
        require('./formatters');
    const { PLACEHOLDER_IMAGE, PROPERTY_TYPES } =
        require('./constants');

    // Determinar iconos y badges según tipo
    const propertyTypeInfo = PROPERTY_TYPES[property.property_type] || PROPERTY_TYPES.apartment;

    // Agregar campos computados
    return {
        ...property,

        // Formateo de precios
        price_formatted: formatPrice(property.net_price || property.list_price),
        rental_price_formatted: formatPrice(property.net_rental_price),

        // Ubicación
        location: formatLocation(property),

        // Área formateada
        area_formatted: formatArea(property.area_constructed || property.area_total),

        // Imagen con fallback
        image_url: property.image_url || PLACEHOLDER_IMAGE,

        // Tipo de propiedad
        type_name: propertyTypeInfo.label,
        type_icon: propertyTypeInfo.icon,

        // Badge de servicio (color)
        service_badge_class: property.type_service === 'rent'
            ? 'bg-bohio-red'
            : property.type_service === 'sale'
                ? 'bg-success'
                : 'bg-warning',

        // Label de precio
        price_label: getPriceLabel(property),
    };
}

/**
 * Prepara datos de resultado de autocomplete
 */
export function prepareAutocompleteResult(result) {
    // Determinar ícono según tipo
    const iconMap = {
        city: { class: 'fa-map-marker-alt', type: 'city' },
        region: { class: 'fa-home', type: 'region' },
        project: { class: 'fa-building', type: 'project' },
        property: { class: 'fa-key', type: 'property' }
    };

    const iconInfo = iconMap[result.type] || iconMap.city;

    return {
        ...result,
        iconClass: iconInfo.class,
        iconType: iconInfo.type,
        // IDs numéricos
        id: result.city_id || result.region_id || result.project_id || result.property_id || ''
    };
}

/**
 * Renderiza un template y lo inserta en un contenedor
 * @param {HTMLElement} container - Elemento contenedor
 * @param {string} templateId - ID del template
 * @param {Object} context - Contexto de datos
 * @param {boolean} append - Si true, agrega al final. Si false, reemplaza contenido
 */
export function renderIntoContainer(container, templateId, context = {}, append = false) {
    if (!container) {
        console.error('[TemplateRenderer] Container element not found');
        return;
    }

    const html = renderTemplate(templateId, context);

    if (append) {
        container.insertAdjacentHTML('beforeend', html);
    } else {
        container.innerHTML = html;
    }
}

/**
 * Alternativa simple: crear elementos sin QWeb
 * Para casos donde QWeb no está disponible o es muy complejo
 */
export function createSimpleElement(tag, attributes = {}, content = '') {
    const element = document.createElement(tag);

    Object.entries(attributes).forEach(([key, value]) => {
        if (key === 'className' || key === 'class') {
            element.className = value;
        } else if (key === 'style' && typeof value === 'object') {
            Object.assign(element.style, value);
        } else if (key.startsWith('data-')) {
            element.setAttribute(key, value);
        } else {
            element[key] = value;
        }
    });

    if (content) {
        if (typeof content === 'string') {
            element.textContent = content;
        } else if (content instanceof HTMLElement) {
            element.appendChild(content);
        }
    }

    return element;
}

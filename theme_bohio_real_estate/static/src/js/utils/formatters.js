/** @odoo-module **/

/**
 * BOHIO Real Estate - Formatters Utilities
 * Funciones centralizadas para formateo de datos
 * Evita duplicación de código en múltiples archivos
 */

/**
 * Formatear precio en pesos colombianos
 * @param {Number} price - Precio a formatear
 * @returns {String} - Precio formateado o "Consultar"
 */
export function formatPrice(price) {
    if (!price || price === 0) return 'Consultar';

    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(price);
}

/**
 * Formatear distancia (metros o kilómetros)
 * @param {Number} distanceKm - Distancia en kilómetros
 * @returns {String} - Distancia formateada
 */
export function formatDistance(distanceKm) {
    if (!distanceKm || distanceKm === 0) return '';

    if (distanceKm < 1) {
        const meters = Math.round(distanceKm * 1000);
        return `${meters}m`;
    }

    return `${distanceKm.toFixed(1)}km`;
}

/**
 * Formatear área (metros cuadrados, hectáreas, etc.)
 * @param {Number} area - Área a formatear
 * @param {String} unit - Unidad (default: 'm²')
 * @returns {String} - Área formateada
 */
export function formatArea(area, unit = 'm²') {
    if (!area || area === 0) return '';

    const rounded = Math.round(area);
    return `${rounded.toLocaleString('es-CO')} ${unit}`;
}

/**
 * Formatear número de habitaciones/baños
 * @param {Number} count - Cantidad
 * @param {String} singular - Texto singular (default: 'habitación')
 * @param {String} plural - Texto plural (default: 'habitaciones')
 * @returns {String} - Texto formateado
 */
export function formatRooms(count, singular = 'habitación', plural = 'habitaciones') {
    if (!count || count === 0) return '';

    return count === 1 ? `${count} ${singular}` : `${count} ${plural}`;
}

/**
 * Obtener label de precio según tipo de servicio
 * @param {Object} property - Propiedad con type_service
 * @returns {String} - Label de precio
 */
export function getPriceLabel(property) {
    if (!property || !property.type_service) return 'Precio';

    const isRental = property.type_service.toLowerCase().includes('arriendo');
    return isRental ? 'Arriendo/mes' : 'Venta';
}

/**
 * Construir texto de ubicación completa
 * @param {Object} property - Propiedad con city, neighborhood, state
 * @returns {String} - Ubicación formateada
 */
export function formatLocation(property) {
    if (!property) return '';

    const parts = [];

    if (property.neighborhood) {
        parts.push(property.neighborhood);
    }

    if (property.city) {
        parts.push(property.city);
    }

    if (property.state && !property.neighborhood) {
        parts.push(property.state);
    }

    return parts.join(', ');
}

/**
 * Formatear fecha relativa (hace X días/horas)
 * @param {String|Date} date - Fecha a formatear
 * @returns {String} - Texto relativo
 */
export function formatRelativeDate(date) {
    if (!date) return '';

    const dateObj = typeof date === 'string' ? new Date(date) : date;
    const now = new Date();
    const diffMs = now - dateObj;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Hoy';
    if (diffDays === 1) return 'Ayer';
    if (diffDays < 7) return `Hace ${diffDays} días`;
    if (diffDays < 30) return `Hace ${Math.floor(diffDays / 7)} semanas`;
    if (diffDays < 365) return `Hace ${Math.floor(diffDays / 30)} meses`;

    return `Hace ${Math.floor(diffDays / 365)} años`;
}

/**
 * Formatear número con separadores de miles
 * @param {Number} number - Número a formatear
 * @returns {String} - Número formateado
 */
export function formatNumber(number) {
    if (!number && number !== 0) return '';

    return number.toLocaleString('es-CO');
}

/**
 * Truncar texto con ellipsis
 * @param {String} text - Texto a truncar
 * @param {Number} maxLength - Longitud máxima
 * @returns {String} - Texto truncado
 */
export function truncateText(text, maxLength = 100) {
    if (!text) return '';
    if (text.length <= maxLength) return text;

    return text.substring(0, maxLength).trim() + '...';
}

/**
 * Exportar todas las funciones como objeto
 */
export default {
    formatPrice,
    formatDistance,
    formatArea,
    formatRooms,
    getPriceLabel,
    formatLocation,
    formatRelativeDate,
    formatNumber,
    truncateText
};

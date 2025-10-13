/** @odoo-module **/

// =============================================================================
// BOHIO REAL ESTATE - URL PARAMETERS UTILITIES
// =============================================================================
// Utilidades genéricas para manejar parámetros de URL y estado de filtros
// Reutilizable en toda la aplicación

// -----------------------------------------------------------------------------
// LECTURA DE PARÁMETROS
// -----------------------------------------------------------------------------

/**
 * Obtiene todos los parámetros de la URL actual
 * @returns {URLSearchParams}
 */
export function getUrlParams() {
    return new URLSearchParams(window.location.search);
}

/**
 * Obtiene un parámetro específico de la URL
 * @param {string} key - Nombre del parámetro
 * @param {*} defaultValue - Valor por defecto si no existe
 * @returns {string|null}
 */
export function getUrlParam(key, defaultValue = null) {
    const params = getUrlParams();
    return params.get(key) || defaultValue;
}

/**
 * Obtiene múltiples parámetros de la URL
 * @param {Array<string>} keys - Array de nombres de parámetros
 * @returns {Object} Objeto con los valores de los parámetros
 */
export function getUrlParams(keys) {
    const params = getUrlParams();
    const result = {};
    keys.forEach(key => {
        result[key] = params.get(key) || null;
    });
    return result;
}

// -----------------------------------------------------------------------------
// ESCRITURA DE PARÁMETROS
// -----------------------------------------------------------------------------

/**
 * Actualiza la URL con nuevos parámetros sin recargar la página
 * @param {Object} params - Objeto con parámetros a actualizar
 * @param {boolean} replace - Si true, reemplaza la URL en lugar de agregar al historial
 */
export function updateUrlParams(params, replace = false) {
    const url = new URL(window.location.href);

    Object.keys(params).forEach(key => {
        const value = params[key];
        if (value === null || value === undefined || value === '') {
            url.searchParams.delete(key);
        } else {
            url.searchParams.set(key, value);
        }
    });

    if (replace) {
        window.history.replaceState({}, '', url.toString());
    } else {
        window.history.pushState({}, '', url.toString());
    }
}

/**
 * Elimina parámetros de la URL
 * @param {Array<string>} keys - Array de nombres de parámetros a eliminar
 */
export function removeUrlParams(keys) {
    const url = new URL(window.location.href);
    keys.forEach(key => url.searchParams.delete(key));
    window.history.replaceState({}, '', url.toString());
}

/**
 * Limpia todos los parámetros de la URL
 */
export function clearUrlParams() {
    const url = new URL(window.location.href);
    url.search = '';
    window.history.replaceState({}, '', url.toString());
}

// -----------------------------------------------------------------------------
// FILTROS DE PROPIEDADES
// -----------------------------------------------------------------------------

/**
 * Extrae los filtros de propiedades desde la URL
 * @returns {Object} Objeto con filtros activos
 */
export function getPropertyFiltersFromUrl() {
    const params = getUrlParams();

    return {
        // Búsqueda
        search: params.get('search') || null,

        // Tipo de servicio
        service: params.get('service') || null, // 'rent', 'sale', 'sale_rent'

        // Tipo de propiedad
        property_type: params.get('property_type') || null, // 'apartment', 'house', etc.

        // Ubicación
        city: params.get('city') || null,
        neighborhood: params.get('neighborhood') || null,
        state: params.get('state') || null,

        // Rango de precios
        price_min: params.get('price_min') ? parseFloat(params.get('price_min')) : null,
        price_max: params.get('price_max') ? parseFloat(params.get('price_max')) : null,

        // Características
        bedrooms: params.get('bedrooms') ? parseInt(params.get('bedrooms')) : null,
        bathrooms: params.get('bathrooms') ? parseInt(params.get('bathrooms')) : null,
        area_min: params.get('area_min') ? parseFloat(params.get('area_min')) : null,
        area_max: params.get('area_max') ? parseFloat(params.get('area_max')) : null,

        // Proyecto
        project_id: params.get('project_id') ? parseInt(params.get('project_id')) : null,

        // Paginación
        page: params.get('page') ? parseInt(params.get('page')) : 1,
        limit: params.get('limit') ? parseInt(params.get('limit')) : 20,
    };
}

/**
 * Convierte filtros a parámetros de URL
 * @param {Object} filters - Objeto con filtros
 * @returns {Object} Objeto con parámetros para URL
 */
export function filtersToUrlParams(filters) {
    const params = {};

    Object.keys(filters).forEach(key => {
        const value = filters[key];
        if (value !== null && value !== undefined && value !== '') {
            params[key] = value.toString();
        }
    });

    return params;
}

/**
 * Verifica si hay filtros activos
 * @returns {boolean}
 */
export function hasActiveFilters() {
    const filters = getPropertyFiltersFromUrl();

    // Excluir page y limit de la verificación
    const filterKeys = Object.keys(filters).filter(key =>
        key !== 'page' && key !== 'limit'
    );

    return filterKeys.some(key => filters[key] !== null);
}

/**
 * Construye un objeto de filtros limpio (solo valores no nulos)
 * @param {Object} filters - Filtros raw
 * @returns {Object} Filtros limpios
 */
export function cleanFilters(filters) {
    const clean = {};

    Object.keys(filters).forEach(key => {
        const value = filters[key];
        if (value !== null && value !== undefined && value !== '') {
            clean[key] = value;
        }
    });

    return clean;
}

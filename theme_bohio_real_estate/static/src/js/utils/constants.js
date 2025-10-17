/** @odoo-module **/

/**
 * BOHIO Real Estate - Constants
 * Constantes centralizadas para todo el módulo
 * Evita valores mágicos duplicados en el código
 */

// =============================================================================
// GEOLOCALIZACIÓN
// =============================================================================

/**
 * Umbral de distancia en kilómetros para considerar una propiedad "cercana"
 * Propiedades dentro de este radio mostrarán badge "Cerca de ti"
 */
export const DISTANCE_THRESHOLD_KM = 5;

/**
 * Nivel de zoom del mapa cuando se muestra ubicación del usuario
 */
export const ZOOM_WITH_USER = 13;

/**
 * Centro por defecto del mapa [lat, lng] - Montería, Colombia
 */
export const DEFAULT_CENTER = [8.7479, -75.8814];

/**
 * Zoom por defecto del mapa (vista de ciudad)
 */
export const DEFAULT_ZOOM = 12;

/**
 * Zoom máximo permitido en el mapa
 */
export const MAX_ZOOM = 19;

/**
 * Timeout para request de geolocalización (milisegundos)
 */
export const GEOLOCATION_TIMEOUT = 5000;

/**
 * Edad máxima de cache de geolocalización (milisegundos)
 * 5 minutos = 300000ms
 */
export const GEOLOCATION_MAX_AGE = 300000;

// =============================================================================
// LEAFLET CONFIGURATION
// =============================================================================

/**
 * Path a los iconos de Leaflet
 */
export const LEAFLET_ICON_PATH = '/real_estate_bits/static/src/lib/leaflet/images/';

/**
 * URL del tile server de OpenStreetMap
 */
export const OSM_TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';

/**
 * Atribución de OpenStreetMap
 */
export const OSM_ATTRIBUTION = '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

// =============================================================================
// CARRUSELES Y PAGINACIÓN
// =============================================================================

/**
 * Número de propiedades por página en carruseles
 */
export const CAROUSEL_ITEMS_PER_PAGE = 4;

/**
 * Número de propiedades por página en listados
 */
export const LIST_ITEMS_PER_PAGE = 12;

/**
 * Número de propiedades por página en shop
 */
export const SHOP_ITEMS_PER_PAGE = 15;

/**
 * Intervalo de auto-play del carrusel (milisegundos)
 */
export const CAROUSEL_INTERVAL = 5000;

// =============================================================================
// FILTROS Y BÚSQUEDA
// =============================================================================

/**
 * Delay para debounce en búsqueda (milisegundos)
 */
export const SEARCH_DEBOUNCE_DELAY = 300;

/**
 * Número mínimo de caracteres para activar autocompletado
 */
export const AUTOCOMPLETE_MIN_CHARS = 2;

/**
 * Número máximo de resultados en autocompletado
 */
export const AUTOCOMPLETE_MAX_RESULTS = 10;

// =============================================================================
// RANGOS DE PRECIOS (COP)
// =============================================================================

/**
 * Rangos de precios predefinidos para filtros
 */
export const PRICE_RANGES = {
    // Arriendo
    rent: [
        { min: 0, max: 500000, label: 'Hasta $500.000' },
        { min: 500000, max: 1000000, label: '$500.000 - $1.000.000' },
        { min: 1000000, max: 2000000, label: '$1.000.000 - $2.000.000' },
        { min: 2000000, max: 3000000, label: '$2.000.000 - $3.000.000' },
        { min: 3000000, max: null, label: 'Más de $3.000.000' }
    ],
    // Venta
    sale: [
        { min: 0, max: 100000000, label: 'Hasta $100 millones' },
        { min: 100000000, max: 200000000, label: '$100M - $200M' },
        { min: 200000000, max: 300000000, label: '$200M - $300M' },
        { min: 300000000, max: 500000000, label: '$300M - $500M' },
        { min: 500000000, max: null, label: 'Más de $500M' }
    ]
};

// =============================================================================
// TIPOS DE PROPIEDADES
// =============================================================================

/**
 * Tipos de inmuebles con iconos Bootstrap
 */
export const PROPERTY_TYPES = {
    apartment: {
        label: 'Apartamento',
        icon: 'bi-building',
        plural: 'Apartamentos'
    },
    house: {
        label: 'Casa',
        icon: 'bi-house-door',
        plural: 'Casas'
    },
    office: {
        label: 'Oficina',
        icon: 'bi-briefcase',
        plural: 'Oficinas'
    },
    commercial: {
        label: 'Local Comercial',
        icon: 'bi-shop',
        plural: 'Locales Comerciales'
    },
    lot: {
        label: 'Lote',
        icon: 'bi-square',
        plural: 'Lotes'
    },
    warehouse: {
        label: 'Bodega',
        icon: 'bi-box',
        plural: 'Bodegas'
    },
    farm: {
        label: 'Finca',
        icon: 'bi-tree',
        plural: 'Fincas'
    },
    penthouse: {
        label: 'Penthouse',
        icon: 'bi-stars',
        plural: 'Penthouses'
    }
};

// =============================================================================
// TIPOS DE SERVICIO
// =============================================================================

/**
 * Tipos de servicio con iconos
 */
export const SERVICE_TYPES = {
    rent: {
        label: 'Arriendo',
        icon: 'bi-key',
        color: '#FF1D25'
    },
    sale: {
        label: 'Venta',
        icon: 'bi-house',
        color: '#FF1D25'
    },
    sale_rent: {
        label: 'Venta y Arriendo',
        icon: 'bi-grid',
        color: '#FF1D25'
    }
};

// =============================================================================
// ESTADOS DE PROPIEDADES
// =============================================================================

/**
 * Estados de propiedades con colores
 */
export const PROPERTY_STATES = {
    available: {
        label: 'Disponible',
        color: 'success',
        badge: 'bg-success'
    },
    reserved: {
        label: 'Reservada',
        color: 'warning',
        badge: 'bg-warning'
    },
    rented: {
        label: 'Arrendada',
        color: 'info',
        badge: 'bg-info'
    },
    sold: {
        label: 'Vendida',
        color: 'secondary',
        badge: 'bg-secondary'
    }
};

// =============================================================================
// IMAGEN PLACEHOLDER
// =============================================================================

/**
 * Path a imagen placeholder cuando no hay imagen disponible
 */
export const PLACEHOLDER_IMAGE = '/theme_bohio_real_estate/static/src/img/placeholder.jpg';

// =============================================================================
// REDES SOCIALES
// =============================================================================

/**
 * URLs de redes sociales de BOHIO
 */
export const SOCIAL_MEDIA = {
    facebook: 'https://www.facebook.com/bohioinmobiliaria',
    instagram: 'https://www.instagram.com/bohioinmobiliaria',
    youtube: 'https://www.youtube.com/channel/bohio',
    whatsapp: 'https://wa.me/573001234567',
    linkedin: 'https://www.linkedin.com/company/bohio-inmobiliaria'
};

// =============================================================================
// TIMEOUTS Y DELAYS
// =============================================================================

/**
 * Timeout para peticiones RPC (milisegundos)
 */
export const RPC_TIMEOUT = 30000;

/**
 * Delay para mostrar loader (milisegundos)
 */
export const LOADER_DELAY = 200;

/**
 * Duración de animaciones (milisegundos)
 */
export const ANIMATION_DURATION = 300;

// =============================================================================
// Z-INDEX LAYERS
// =============================================================================

/**
 * Z-index para diferentes capas de la UI
 */
export const Z_INDEX = {
    base: 1,
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    modal_backdrop: 1040,
    modal: 1050,
    popover: 1060,
    tooltip: 1070
};

// =============================================================================
// BREAKPOINTS (Sincronizados con Bootstrap 5)
// =============================================================================

/**
 * Breakpoints responsivos en pixeles
 */
export const BREAKPOINTS = {
    xs: 0,
    sm: 576,
    md: 768,
    lg: 992,
    xl: 1200,
    xxl: 1400
};

// =============================================================================
// EXPORTAR TODO COMO OBJETO DEFAULT
// =============================================================================

export default {
    // Geolocalización
    DISTANCE_THRESHOLD_KM,
    ZOOM_WITH_USER,
    DEFAULT_CENTER,
    DEFAULT_ZOOM,
    MAX_ZOOM,
    GEOLOCATION_TIMEOUT,
    GEOLOCATION_MAX_AGE,

    // Leaflet
    LEAFLET_ICON_PATH,
    OSM_TILE_URL,
    OSM_ATTRIBUTION,

    // Carruseles
    CAROUSEL_ITEMS_PER_PAGE,
    LIST_ITEMS_PER_PAGE,
    SHOP_ITEMS_PER_PAGE,
    CAROUSEL_INTERVAL,

    // Búsqueda
    SEARCH_DEBOUNCE_DELAY,
    AUTOCOMPLETE_MIN_CHARS,
    AUTOCOMPLETE_MAX_RESULTS,

    // Precios
    PRICE_RANGES,

    // Tipos
    PROPERTY_TYPES,
    SERVICE_TYPES,
    PROPERTY_STATES,

    // Imágenes
    PLACEHOLDER_IMAGE,

    // Social
    SOCIAL_MEDIA,

    // Timing
    RPC_TIMEOUT,
    LOADER_DELAY,
    ANIMATION_DURATION,

    // UI
    Z_INDEX,
    BREAKPOINTS
};

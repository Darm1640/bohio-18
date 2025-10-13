/** @odoo-module **/

// =============================================================================
// BOHIO REAL ESTATE - GEOLOCATION UTILITIES
// =============================================================================
// Utilidades para geolocalización y cálculo de distancias
// Basado en mejores prácticas de Odoo 18

// -----------------------------------------------------------------------------
// CONSTANTES
// -----------------------------------------------------------------------------

export const DISTANCE_THRESHOLD_KM = 5; // 5 km para mostrar nombres
export const ZOOM_WITH_USER = 13;
export const DEFAULT_CENTER = [8.7479, -75.8814]; // Montería [lat, lng]
export const DEFAULT_ZOOM = 12;

// -----------------------------------------------------------------------------
// CÁLCULO DE DISTANCIAS
// -----------------------------------------------------------------------------

/**
 * Calcula la distancia entre dos puntos usando la fórmula de Haversine
 * @param {number} lat1 - Latitud del punto 1
 * @param {number} lng1 - Longitud del punto 1
 * @param {number} lat2 - Latitud del punto 2
 * @param {number} lng2 - Longitud del punto 2
 * @returns {number} Distancia en kilómetros
 */
export function calculateDistance(lat1, lng1, lat2, lng2) {
    const R = 6371; // Radio de la Tierra en km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

/**
 * Formatea la distancia para mostrar (metros si < 1km, kilómetros si >= 1km)
 * @param {number} distanceKm - Distancia en kilómetros
 * @returns {string} Distancia formateada
 */
export function formatDistance(distanceKm) {
    if (distanceKm < 1) {
        return `${Math.round(distanceKm * 1000)}m`;
    }
    return `${distanceKm.toFixed(1)}km`;
}

// -----------------------------------------------------------------------------
// GEOLOCALIZACIÓN
// -----------------------------------------------------------------------------

/**
 * Intenta obtener la geolocalización del usuario
 * @returns {Promise<{lat: number, lng: number}|null>} Ubicación o null si falla
 */
export async function tryGeolocation() {
    return new Promise((resolve) => {
        if (!navigator.geolocation) {
            console.log('[Geolocation] Not supported by browser');
            resolve(null);
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                const location = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                console.log('[Geolocation] User location obtained:', location);
                resolve(location);
            },
            (error) => {
                console.log('[Geolocation] Error:', error.message);
                resolve(null);
            },
            {
                timeout: 5000,
                enableHighAccuracy: false,
                maximumAge: 300000 // 5 minutos de cache
            }
        );
    });
}

/**
 * Verifica si el navegador soporta geolocalización
 * @returns {boolean}
 */
export function isGeolocationSupported() {
    return 'geolocation' in navigator;
}

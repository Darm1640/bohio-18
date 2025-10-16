/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

/**
 * ============================================================================
 * BOHIO Property Service - Servicio Centralizado de APIs
 * ============================================================================
 * Centraliza TODAS las llamadas a APIs de propiedades
 * Elimina redundancia de 47 llamadas repetidas en múltiples archivos
 */

export class PropertyService {
    /**
     * Endpoints disponibles
     */
    static ENDPOINTS = {
        rent: '/api/properties/arriendo',
        sale: '/api/properties/venta-usada',
        projects: '/api/properties/proyectos',
        search: '/property/search/ajax',
        detail: '/property/detail',
        map: '/api/properties/map',
        autocomplete: '/property/search/autocomplete'
    };

    /**
     * Cargar propiedades por tipo
     * @param {string} type - 'rent', 'sale', 'projects'
     * @param {Object} options - { limit, filters, page }
     * @returns {Promise<Object>}
     */
    static async loadByType(type, options = {}) {
        const endpoint = this.ENDPOINTS[type];
        if (!endpoint) {
            throw new Error(`[PropertyService] Tipo de propiedad no válido: ${type}`);
        }

        const params = {
            limit: options.limit || 12,
            ...options.filters,
            page: options.page || 1
        };

        try {
            console.log(`[PropertyService] Loading ${type} properties:`, params);
            const response = await rpc(endpoint, params);
            return this._processResponse(response);
        } catch (error) {
            console.error(`[PropertyService] Error loading ${type}:`, error);
            return { success: false, properties: [], total: 0, error: error.message };
        }
    }

    /**
     * Búsqueda con filtros
     * @param {Object} filters - Filtros de búsqueda
     * @param {number} page - Página actual
     * @param {number} limit - Límite por página
     * @returns {Promise<Object>}
     */
    static async search(filters, page = 1, limit = 20) {
        const params = {
            context: 'public',
            filters,
            page,
            ppg: limit,
            order: filters.order || 'newest'
        };

        try {
            console.log('[PropertyService] Search with filters:', params);
            const response = await rpc(this.ENDPOINTS.search, params);
            return this._processResponse(response);
        } catch (error) {
            console.error('[PropertyService] Search error:', error);
            return { success: false, properties: [], total: 0, error: error.message };
        }
    }

    /**
     * Obtener detalle de una propiedad
     * @param {number} propertyId - ID de la propiedad
     * @returns {Promise<Object|null>}
     */
    static async getDetail(propertyId) {
        if (!propertyId) {
            throw new Error('[PropertyService] Property ID is required');
        }

        try {
            console.log('[PropertyService] Getting detail for property:', propertyId);
            const response = await rpc(this.ENDPOINTS.detail, {
                property_id: propertyId
            });

            if (response.result) {
                return response.result;
            }

            return null;
        } catch (error) {
            console.error('[PropertyService] Detail error:', error);
            return null;
        }
    }

    /**
     * Cargar propiedades para mapa
     * @param {Object} filters - Filtros de ubicación
     * @returns {Promise<Object>}
     */
    static async loadForMap(filters = {}) {
        const params = {
            ...filters,
            limit: filters.limit || 50, // Más propiedades para mapa
            with_coordinates: true // Solo propiedades con coordenadas
        };

        try {
            console.log('[PropertyService] Loading properties for map:', params);
            const response = await rpc(this.ENDPOINTS.map, params);
            return this._processResponse(response);
        } catch (error) {
            console.error('[PropertyService] Map error:', error);
            return { success: false, properties: [], error: error.message };
        }
    }

    /**
     * Autocompletado de búsqueda
     * @param {string} query - Texto de búsqueda
     * @param {number} limit - Número máximo de resultados
     * @returns {Promise<Array>}
     */
    static async autocomplete(query, limit = 10) {
        if (!query || query.trim().length < 2) {
            return [];
        }

        try {
            console.log('[PropertyService] Autocomplete:', query);
            const response = await rpc(this.ENDPOINTS.autocomplete, {
                query: query.trim(),
                limit
            });

            if (response.result && Array.isArray(response.result)) {
                return response.result;
            }

            return [];
        } catch (error) {
            console.error('[PropertyService] Autocomplete error:', error);
            return [];
        }
    }

    /**
     * Cargar propiedades relacionadas/similares
     * @param {number} propertyId - ID de la propiedad base
     * @param {number} limit - Número de propiedades a retornar
     * @returns {Promise<Object>}
     */
    static async loadRelated(propertyId, limit = 4) {
        try {
            console.log('[PropertyService] Loading related properties for:', propertyId);
            const response = await rpc('/property/related', {
                property_id: propertyId,
                limit
            });

            return this._processResponse(response);
        } catch (error) {
            console.error('[PropertyService] Related properties error:', error);
            return { success: false, properties: [] };
        }
    }

    /**
     * Cargar propiedades destacadas
     * @param {number} limit - Número de propiedades
     * @returns {Promise<Object>}
     */
    static async loadFeatured(limit = 6) {
        try {
            console.log('[PropertyService] Loading featured properties');
            const response = await rpc('/api/properties/featured', { limit });
            return this._processResponse(response);
        } catch (error) {
            console.error('[PropertyService] Featured properties error:', error);
            return { success: false, properties: [] };
        }
    }

    /**
     * Cargar propiedades recientes
     * @param {number} limit - Número de propiedades
     * @returns {Promise<Object>}
     */
    static async loadRecent(limit = 8) {
        try {
            console.log('[PropertyService] Loading recent properties');
            const response = await rpc('/api/properties/recent', { limit });
            return this._processResponse(response);
        } catch (error) {
            console.error('[PropertyService] Recent properties error:', error);
            return { success: false, properties: [] };
        }
    }

    /**
     * Obtener estadísticas de propiedades
     * @returns {Promise<Object>}
     */
    static async getStatistics() {
        try {
            console.log('[PropertyService] Getting statistics');
            const response = await rpc('/api/properties/statistics');
            return response.result || {};
        } catch (error) {
            console.error('[PropertyService] Statistics error:', error);
            return {};
        }
    }

    /**
     * Procesar respuesta estándar del API
     * @private
     * @param {Object} response - Respuesta del RPC
     * @returns {Object}
     */
    static _processResponse(response) {
        // Caso 1: Respuesta con result.success
        if (response.result && typeof response.result.success !== 'undefined') {
            return {
                success: response.result.success,
                properties: response.result.properties || [],
                total: response.result.total || response.result.count || 0,
                page: response.result.page || 1,
                pages: response.result.pages || 1
            };
        }

        // Caso 2: Respuesta directa con properties array
        if (response.properties && Array.isArray(response.properties)) {
            return {
                success: true,
                properties: response.properties,
                total: response.total || response.count || response.properties.length,
                page: response.page || 1,
                pages: response.pages || 1
            };
        }

        // Caso 3: Respuesta con result como array
        if (response.result && Array.isArray(response.result)) {
            return {
                success: true,
                properties: response.result,
                total: response.result.length,
                page: 1,
                pages: 1
            };
        }

        // Caso 4: Error o respuesta no reconocida
        return {
            success: false,
            properties: [],
            total: 0,
            page: 1,
            pages: 0
        };
    }

    /**
     * Crear filtros desde formulario
     * @param {HTMLFormElement} form - Formulario con filtros
     * @returns {Object}
     */
    static getFiltersFromForm(form) {
        if (!form) return {};

        const formData = new FormData(form);
        const filters = {};

        // Convertir FormData a objeto de filtros
        for (const [key, value] of formData.entries()) {
            if (value && value !== '' && value !== 'all') {
                // Convertir valores numéricos
                if (['min_price', 'max_price', 'min_area', 'max_area', 'bedrooms', 'bathrooms', 'parking'].includes(key)) {
                    const numValue = parseFloat(value);
                    if (!isNaN(numValue)) {
                        filters[key] = numValue;
                    }
                } else {
                    filters[key] = value;
                }
            }
        }

        return filters;
    }

    /**
     * Construir query string desde filtros
     * @param {Object} filters - Objeto con filtros
     * @returns {string}
     */
    static buildQueryString(filters) {
        const params = new URLSearchParams();

        Object.entries(filters).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                params.append(key, value);
            }
        });

        const queryString = params.toString();
        return queryString ? `?${queryString}` : '';
    }
}

// Exportar por defecto
export default PropertyService;

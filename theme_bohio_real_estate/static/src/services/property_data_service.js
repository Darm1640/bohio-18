/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

/**
 * Servicio para cargar datos de propiedades
 * Maneja cache, abort controllers y reintentos
 */
export const propertyDataService = {
    dependencies: [],

    start(env) {
        const cache = new Map();
        const abortControllers = new Map();

        const ENDPOINTS = {
            rent: "/api/properties/arriendo",
            sale: "/api/properties/venta-usada",
            projects: "/api/properties/proyectos",
        };

        /**
         * Cargar propiedades por tipo
         */
        async function fetchProperties(type, options = {}) {
            const limit = options.limit || 12;
            const cacheKey = `${type}:${limit}`;

            console.log(`[PropertyDataService] Cargando ${type} con límite ${limit}`);

            // Verificar cache
            if (cache.has(cacheKey) && !options.forceRefresh) {
                console.log(`[PropertyDataService] Retornando desde cache: ${cacheKey}`);
                return cache.get(cacheKey);
            }

            // Cancelar request anterior del mismo tipo
            if (abortControllers.has(type)) {
                console.log(`[PropertyDataService] Cancelando request anterior de ${type}`);
                abortControllers.get(type).abort();
            }

            const abortCtrl = new AbortController();
            abortControllers.set(type, abortCtrl);

            const endpoint = ENDPOINTS[type];
            if (!endpoint) {
                throw new Error(`Tipo de propiedad no válido: ${type}`);
            }

            try {
                const result = await rpc(endpoint, { limit }, {
                    signal: abortCtrl.signal,
                });

                console.log(`[PropertyDataService] Respuesta de ${type}:`, result);

                if (result?.success && Array.isArray(result.properties)) {
                    const data = {
                        success: true,
                        properties: result.properties,
                        total: result.total || result.properties.length,
                    };

                    // Guardar en cache
                    cache.set(cacheKey, data);

                    return data;
                }

                throw new Error(result?.error || "No se recibieron propiedades");
            } catch (error) {
                if (error.name === "AbortError") {
                    console.log(`[PropertyDataService] Request cancelado: ${type}`);
                    return null;
                }

                console.error(`[PropertyDataService] Error cargando ${type}:`, error);
                throw error;
            } finally {
                abortControllers.delete(type);
            }
        }

        /**
         * Limpiar cache
         */
        function clearCache() {
            console.log("[PropertyDataService] Limpiando cache");
            cache.clear();
        }

        /**
         * Cancelar todas las peticiones
         */
        function abortAll() {
            console.log("[PropertyDataService] Cancelando todas las peticiones");
            abortControllers.forEach((ctrl) => ctrl.abort());
            abortControllers.clear();
        }

        return {
            fetchProperties,
            clearCache,
            abortAll,
        };
    },
};

registry.category("services").add("propertyData", propertyDataService);

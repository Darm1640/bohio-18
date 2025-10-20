/** @odoo-module **/

/**
 * BOHIO URL Synchronization - Sincronización de Estado con URL
 *
 * Características:
 * - Sincronizar filtros con URL para búsquedas compartibles
 * - Mantener estado de paginación y ordenamiento
 * - History API para navegación hacia atrás/adelante
 * - SEO friendly URLs
 *
 * Uso:
 *   const urlSync = new URLSync();
 *   urlSync.updateURL({ filters: {...}, page: 1, sort: 'price_asc' });
 *   const state = urlSync.getStateFromURL();
 */

export class URLSync {
    constructor() {
        this.baseURL = window.location.pathname;
        this.listeners = [];
    }

    /**
     * Actualizar URL con el estado actual de filtros
     * @param {Object} state - Estado a guardar en URL
     * @param {Object} state.filters - Filtros aplicados
     * @param {Number} state.page - Página actual
     * @param {String} state.sort - Orden aplicado
     * @param {String} state.view - Vista activa (grid/map)
     */
    updateURL(state) {
        const params = new URLSearchParams();

        // Agregar filtros a URL
        if (state.filters) {
            // Rango de precio
            if (state.filters.price_min) {
                params.set('price_min', state.filters.price_min);
            }
            if (state.filters.price_max) {
                params.set('price_max', state.filters.price_max);
            }

            // Tipo de propiedad
            if (state.filters.property_type) {
                params.set('type', state.filters.property_type);
            }

            // Tipo de servicio
            if (state.filters.service_type) {
                params.set('service', state.filters.service_type);
            }

            // Características múltiples (como arrays)
            const arrayFilters = [
                'bedrooms', 'bathrooms', 'parking', 'area_range',
                'stratum', 'characteristics'
            ];

            arrayFilters.forEach(key => {
                if (state.filters[key] && state.filters[key].length > 0) {
                    params.set(key, state.filters[key].join(','));
                }
            });

            // Ciudad y barrio
            if (state.filters.city) {
                params.set('city', state.filters.city);
            }
            if (state.filters.neighborhood) {
                params.set('neighborhood', state.filters.neighborhood);
            }

            // Búsqueda por código
            if (state.filters.search_code) {
                params.set('code', state.filters.search_code);
            }
        }

        // Paginación
        if (state.page && state.page > 1) {
            params.set('page', state.page);
        }

        // Ordenamiento
        if (state.sort && state.sort !== 'relevance') {
            params.set('sort', state.sort);
        }

        // Vista activa
        if (state.view && state.view !== 'grid') {
            params.set('view', state.view);
        }

        // Construir URL
        const queryString = params.toString();
        const newURL = queryString ? `${this.baseURL}?${queryString}` : this.baseURL;

        // Actualizar URL sin recargar página
        if (window.location.href !== newURL) {
            window.history.pushState(state, '', newURL);
        }
    }

    /**
     * Obtener estado desde los parámetros de URL
     * @returns {Object} Estado recuperado de URL
     */
    getStateFromURL() {
        const params = new URLSearchParams(window.location.search);
        const state = {
            filters: {},
            page: 1,
            sort: 'relevance',
            view: 'grid'
        };

        // Recuperar filtros de precio
        if (params.has('price_min')) {
            state.filters.price_min = parseFloat(params.get('price_min'));
        }
        if (params.has('price_max')) {
            state.filters.price_max = parseFloat(params.get('price_max'));
        }

        // Recuperar tipo de propiedad
        if (params.has('type')) {
            state.filters.property_type = params.get('type');
        }

        // Recuperar tipo de servicio
        if (params.has('service')) {
            state.filters.service_type = params.get('service');
        }

        // Recuperar filtros de array
        const arrayFilters = ['bedrooms', 'bathrooms', 'parking', 'area_range', 'stratum'];
        arrayFilters.forEach(key => {
            if (params.has(key)) {
                state.filters[key] = params.get(key).split(',').map(v => v.trim());
            }
        });

        // Características (IDs separados por coma)
        if (params.has('characteristics')) {
            state.filters.characteristics = params.get('characteristics')
                .split(',')
                .map(id => parseInt(id))
                .filter(id => !isNaN(id));
        }

        // Ciudad y barrio
        if (params.has('city')) {
            state.filters.city = params.get('city');
        }
        if (params.has('neighborhood')) {
            state.filters.neighborhood = params.get('neighborhood');
        }

        // Código de búsqueda
        if (params.has('code')) {
            state.filters.search_code = params.get('code');
        }

        // Paginación
        if (params.has('page')) {
            state.page = parseInt(params.get('page')) || 1;
        }

        // Ordenamiento
        if (params.has('sort')) {
            state.sort = params.get('sort');
        }

        // Vista
        if (params.has('view')) {
            state.view = params.get('view');
        }

        return state;
    }

    /**
     * Limpiar todos los parámetros de URL
     */
    clearURL() {
        window.history.pushState({}, '', this.baseURL);
    }

    /**
     * Registrar listener para cambios en URL (botón atrás/adelante)
     * @param {Function} callback - Función a ejecutar cuando cambie URL
     */
    onPopState(callback) {
        const handler = (event) => {
            const state = event.state || this.getStateFromURL();
            callback(state);
        };

        window.addEventListener('popstate', handler);
        this.listeners.push(handler);

        return () => {
            window.removeEventListener('popstate', handler);
            this.listeners = this.listeners.filter(l => l !== handler);
        };
    }

    /**
     * Generar URL compartible con filtros aplicados
     * @param {Object} state - Estado a compartir
     * @returns {String} URL completa con filtros
     */
    getShareableURL(state) {
        const params = new URLSearchParams();

        if (state.filters) {
            Object.keys(state.filters).forEach(key => {
                const value = state.filters[key];
                if (value !== null && value !== undefined && value !== '') {
                    if (Array.isArray(value)) {
                        if (value.length > 0) {
                            params.set(key, value.join(','));
                        }
                    } else {
                        params.set(key, value);
                    }
                }
            });
        }

        if (state.page && state.page > 1) {
            params.set('page', state.page);
        }
        if (state.sort && state.sort !== 'relevance') {
            params.set('sort', state.sort);
        }
        if (state.view && state.view !== 'grid') {
            params.set('view', state.view);
        }

        const queryString = params.toString();
        return queryString ?
            `${window.location.origin}${this.baseURL}?${queryString}` :
            `${window.location.origin}${this.baseURL}`;
    }

    /**
     * Copiar URL compartible al portapapeles
     * @param {Object} state - Estado actual
     * @returns {Promise} Promise que resuelve cuando se copia
     */
    async copyShareableURL(state) {
        const url = this.getShareableURL(state);

        try {
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(url);
                return { success: true, url };
            } else {
                // Fallback para navegadores antiguos
                const textArea = document.createElement('textarea');
                textArea.value = url;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                document.body.appendChild(textArea);
                textArea.select();
                const successful = document.execCommand('copy');
                document.body.removeChild(textArea);

                return { success: successful, url };
            }
        } catch (error) {
            console.error('Error copiando URL:', error);
            return { success: false, url, error };
        }
    }

    /**
     * Destruir instancia y limpiar listeners
     */
    destroy() {
        this.listeners.forEach(handler => {
            window.removeEventListener('popstate', handler);
        });
        this.listeners = [];
    }
}

/**
 * Helper para crear URLs de búsqueda sin instanciar clase
 * @param {Object} filters - Filtros a aplicar
 * @returns {String} URL con filtros
 */
export function createSearchURL(filters) {
    const sync = new URLSync();
    return sync.getShareableURL({ filters });
}

/**
 * Helper para obtener filtros desde URL actual
 * @returns {Object} Filtros desde URL
 */
export function getFiltersFromURL() {
    const sync = new URLSync();
    const state = sync.getStateFromURL();
    return state.filters;
}

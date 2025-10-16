/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

/**
 * ============================================================================
 * BOHIO Wishlist Service - Servicio de Favoritos
 * ============================================================================
 * Gestiona la lista de deseos/favoritos del usuario
 * Centraliza funcionalidad dispersa en múltiples archivos
 */

export class WishlistService {
    /**
     * Cache local de wishlist
     */
    static _wishlist = new Set();
    static _loaded = false;

    /**
     * Inicializar servicio (cargar wishlist del usuario)
     * @returns {Promise<void>}
     */
    static async initialize() {
        if (this._loaded) return;

        try {
            console.log('[WishlistService] Initializing...');
            const response = await rpc('/property/wishlist/get');

            if (response.success && Array.isArray(response.property_ids)) {
                this._wishlist = new Set(response.property_ids);
                console.log(`[WishlistService] Loaded ${this._wishlist.size} favorites`);
            }

            this._loaded = true;
        } catch (error) {
            console.error('[WishlistService] Initialize error:', error);
            this._loaded = true; // Marcar como loaded aunque haya error
        }
    }

    /**
     * Agregar propiedad a favoritos
     * @param {number} propertyId - ID de la propiedad
     * @returns {Promise<Object>}
     */
    static async add(propertyId) {
        try {
            console.log('[WishlistService] Adding property:', propertyId);
            const response = await rpc('/property/wishlist/add', {
                property_id: propertyId
            });

            if (response.success) {
                this._wishlist.add(propertyId);
                this._dispatchEvent('added', propertyId);
                return { success: true, message: 'Agregado a favoritos' };
            }

            return { success: false, message: response.message || 'Error al agregar' };
        } catch (error) {
            console.error('[WishlistService] Add error:', error);
            return { success: false, message: 'Error al agregar a favoritos' };
        }
    }

    /**
     * Eliminar propiedad de favoritos
     * @param {number} propertyId - ID de la propiedad
     * @returns {Promise<Object>}
     */
    static async remove(propertyId) {
        try {
            console.log('[WishlistService] Removing property:', propertyId);
            const response = await rpc('/property/wishlist/remove', {
                property_id: propertyId
            });

            if (response.success) {
                this._wishlist.delete(propertyId);
                this._dispatchEvent('removed', propertyId);
                return { success: true, message: 'Eliminado de favoritos' };
            }

            return { success: false, message: response.message || 'Error al eliminar' };
        } catch (error) {
            console.error('[WishlistService] Remove error:', error);
            return { success: false, message: 'Error al eliminar de favoritos' };
        }
    }

    /**
     * Toggle propiedad en favoritos
     * @param {number} propertyId - ID de la propiedad
     * @returns {Promise<Object>}
     */
    static async toggle(propertyId) {
        try {
            console.log('[WishlistService] Toggling property:', propertyId);
            const response = await rpc('/property/wishlist/toggle', {
                property_id: propertyId
            });

            if (response.success) {
                if (response.in_wishlist) {
                    this._wishlist.add(propertyId);
                    this._dispatchEvent('added', propertyId);
                } else {
                    this._wishlist.delete(propertyId);
                    this._dispatchEvent('removed', propertyId);
                }

                return {
                    success: true,
                    in_wishlist: response.in_wishlist,
                    message: response.in_wishlist ? 'Agregado a favoritos' : 'Eliminado de favoritos'
                };
            }

            return { success: false, message: response.message || 'Error al actualizar' };
        } catch (error) {
            console.error('[WishlistService] Toggle error:', error);
            return { success: false, message: 'Error al actualizar favoritos' };
        }
    }

    /**
     * Verificar si una propiedad está en favoritos
     * @param {number} propertyId - ID de la propiedad
     * @returns {boolean}
     */
    static isInWishlist(propertyId) {
        return this._wishlist.has(propertyId);
    }

    /**
     * Obtener todas las propiedades favoritas con detalles
     * @returns {Promise<Array>}
     */
    static async getAll() {
        try {
            console.log('[WishlistService] Getting all favorites');
            const response = await rpc('/property/wishlist/list');

            if (response.success && Array.isArray(response.properties)) {
                // Actualizar cache local
                this._wishlist = new Set(response.properties.map(p => p.id));
                return response.properties;
            }

            return [];
        } catch (error) {
            console.error('[WishlistService] GetAll error:', error);
            return [];
        }
    }

    /**
     * Obtener contador de favoritos
     * @returns {number}
     */
    static getCount() {
        return this._wishlist.size;
    }

    /**
     * Limpiar todos los favoritos
     * @returns {Promise<Object>}
     */
    static async clear() {
        try {
            console.log('[WishlistService] Clearing wishlist');
            const response = await rpc('/property/wishlist/clear');

            if (response.success) {
                this._wishlist.clear();
                this._dispatchEvent('cleared');
                return { success: true, message: 'Favoritos eliminados' };
            }

            return { success: false, message: response.message || 'Error al limpiar' };
        } catch (error) {
            console.error('[WishlistService] Clear error:', error);
            return { success: false, message: 'Error al limpiar favoritos' };
        }
    }

    /**
     * Compartir wishlist (generar enlace)
     * @returns {Promise<string|null>}
     */
    static async share() {
        try {
            console.log('[WishlistService] Sharing wishlist');
            const response = await rpc('/property/wishlist/share');

            if (response.success && response.share_url) {
                return response.share_url;
            }

            return null;
        } catch (error) {
            console.error('[WishlistService] Share error:', error);
            return null;
        }
    }

    /**
     * Exportar wishlist (PDF, Excel, etc.)
     * @param {string} format - 'pdf' o 'excel'
     * @returns {Promise<string|null>}
     */
    static async export(format = 'pdf') {
        try {
            console.log('[WishlistService] Exporting wishlist as:', format);
            const response = await rpc('/property/wishlist/export', { format });

            if (response.success && response.download_url) {
                return response.download_url;
            }

            return null;
        } catch (error) {
            console.error('[WishlistService] Export error:', error);
            return null;
        }
    }

    /**
     * Obtener estadísticas del wishlist
     * @returns {Promise<Object>}
     */
    static async getStatistics() {
        try {
            const properties = await this.getAll();

            if (properties.length === 0) {
                return {
                    total: 0,
                    byType: {},
                    byService: {},
                    avgPrice: 0,
                    totalValue: 0
                };
            }

            const stats = {
                total: properties.length,
                byType: {},
                byService: {},
                prices: properties.map(p => p.price || 0).filter(p => p > 0),
            };

            // Agrupar por tipo
            properties.forEach(prop => {
                const type = prop.property_type || 'other';
                stats.byType[type] = (stats.byType[type] || 0) + 1;

                const service = prop.type_service || 'sale';
                stats.byService[service] = (stats.byService[service] || 0) + 1;
            });

            // Calcular precios
            if (stats.prices.length > 0) {
                stats.avgPrice = stats.prices.reduce((a, b) => a + b, 0) / stats.prices.length;
                stats.totalValue = stats.prices.reduce((a, b) => a + b, 0);
                stats.minPrice = Math.min(...stats.prices);
                stats.maxPrice = Math.max(...stats.prices);
            } else {
                stats.avgPrice = 0;
                stats.totalValue = 0;
                stats.minPrice = 0;
                stats.maxPrice = 0;
            }

            return stats;
        } catch (error) {
            console.error('[WishlistService] Statistics error:', error);
            return null;
        }
    }

    /**
     * Disparar evento personalizado
     * @private
     */
    static _dispatchEvent(action, propertyId = null) {
        const event = new CustomEvent('wishlist:changed', {
            detail: {
                action, // 'added', 'removed', 'cleared'
                propertyId,
                count: this._wishlist.size
            }
        });

        window.dispatchEvent(event);
    }

    /**
     * Registrar listener para cambios en wishlist
     * @param {Function} callback - Función a ejecutar
     * @returns {Function} - Función para remover listener
     */
    static onChange(callback) {
        const handler = (event) => callback(event.detail);
        window.addEventListener('wishlist:changed', handler);

        // Retornar función para remover listener
        return () => window.removeEventListener('wishlist:changed', handler);
    }

    /**
     * Actualizar UI de botones de wishlist
     * @param {number} propertyId - ID de la propiedad
     * @param {boolean} isInWishlist - Estado
     */
    static updateUI(propertyId, isInWishlist) {
        // Buscar todos los botones de wishlist para esta propiedad
        const buttons = document.querySelectorAll(
            `[data-property-id="${propertyId}"] .btn-wishlist, ` +
            `.btn-wishlist[data-property-id="${propertyId}"]`
        );

        buttons.forEach(button => {
            if (isInWishlist) {
                button.classList.add('active');
                const icon = button.querySelector('i');
                if (icon) {
                    icon.className = 'bi bi-heart-fill text-danger';
                }
                button.setAttribute('title', 'Quitar de favoritos');
            } else {
                button.classList.remove('active');
                const icon = button.querySelector('i');
                if (icon) {
                    icon.className = 'bi bi-heart';
                }
                button.setAttribute('title', 'Agregar a favoritos');
            }
        });

        // Actualizar contador en header si existe
        this._updateHeaderCount();
    }

    /**
     * Actualizar contador en header
     * @private
     */
    static _updateHeaderCount() {
        const counter = document.querySelector('.wishlist-count, #wishlistCount');
        if (counter) {
            const count = this.getCount();
            counter.textContent = count;

            if (count > 0) {
                counter.style.display = 'inline-block';
            } else {
                counter.style.display = 'none';
            }
        }
    }

    /**
     * Sincronizar con servidor (útil después de login)
     * @returns {Promise<void>}
     */
    static async sync() {
        this._loaded = false;
        await this.initialize();
        this._updateHeaderCount();
    }
}

// Auto-inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        WishlistService.initialize();
    });
} else {
    WishlistService.initialize();
}

// Exportar por defecto
export default WishlistService;

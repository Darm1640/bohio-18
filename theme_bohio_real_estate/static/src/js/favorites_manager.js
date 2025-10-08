/** @odoo-module **/

/**
 * BOHIO Real Estate - Favorites Manager
 * Sistema de gestión de propiedades favoritas con persistencia en localStorage
 */

export class FavoritesManager {
    constructor() {
        this.storageKey = 'bohio-favorites';
        this.favorites = this.loadFavorites();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateFavoriteButtons();
        this.showFavoritesCount();
    }

    /**
     * Carga favoritos desde localStorage
     */
    loadFavorites() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            return stored ? JSON.parse(stored) : [];
        } catch (e) {
            console.error('Error al cargar favoritos:', e);
            return [];
        }
    }

    /**
     * Guarda favoritos en localStorage
     */
    saveFavorites() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.favorites));
            this.dispatchEvent('favoritesChanged');
        } catch (e) {
            console.error('Error al guardar favoritos:', e);
        }
    }

    /**
     * Agrega o quita una propiedad de favoritos
     */
    toggleFavorite(propertyId) {
        const index = this.favorites.indexOf(propertyId);

        if (index > -1) {
            this.favorites.splice(index, 1);
            this.showNotification('Eliminado de favoritos', 'info');
        } else {
            this.favorites.push(propertyId);
            this.showNotification('Agregado a favoritos', 'success');
        }

        this.saveFavorites();
        this.updateFavoriteButtons();
        this.showFavoritesCount();

        return index === -1; // Retorna true si se agregó
    }

    /**
     * Verifica si una propiedad está en favoritos
     */
    isFavorite(propertyId) {
        return this.favorites.includes(propertyId);
    }

    /**
     * Obtiene todas las propiedades favoritas
     */
    getFavorites() {
        return [...this.favorites];
    }

    /**
     * Limpia todos los favoritos
     */
    clearFavorites() {
        if (confirm('¿Estás seguro de eliminar todos los favoritos?')) {
            this.favorites = [];
            this.saveFavorites();
            this.updateFavoriteButtons();
            this.showFavoritesCount();
            this.showNotification('Favoritos eliminados', 'info');
        }
    }

    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Delegación de eventos para botones de favoritos
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.btn-favorite');
            if (btn) {
                e.preventDefault();
                const propertyId = parseInt(btn.dataset.propertyId);
                if (propertyId) {
                    this.toggleFavorite(propertyId);
                }
            }
        });

        // Botón de limpiar favoritos
        const clearBtn = document.getElementById('clearFavoritesBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearFavorites());
        }
    }

    /**
     * Actualiza el estado visual de los botones de favoritos
     */
    updateFavoriteButtons() {
        const buttons = document.querySelectorAll('.btn-favorite');
        buttons.forEach(btn => {
            const propertyId = parseInt(btn.dataset.propertyId);
            const isFav = this.isFavorite(propertyId);

            const icon = btn.querySelector('i');
            if (icon) {
                icon.className = isFav ? 'fa fa-heart' : 'fa fa-heart-o';
            }

            btn.classList.toggle('active', isFav);
            btn.setAttribute('aria-pressed', isFav);
            btn.setAttribute('title', isFav ? 'Quitar de favoritos' : 'Agregar a favoritos');
        });
    }

    /**
     * Muestra el contador de favoritos
     */
    showFavoritesCount() {
        const counter = document.getElementById('favoritesCount');
        if (counter) {
            const count = this.favorites.length;
            counter.textContent = count;
            counter.style.display = count > 0 ? 'inline-block' : 'none';
        }

        // Actualizar badge en el header
        const badge = document.querySelector('.favorites-badge');
        if (badge) {
            const count = this.favorites.length;
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        }
    }

    /**
     * Muestra notificación
     */
    showNotification(message, type = 'info') {
        // Crear contenedor si no existe
        let container = document.getElementById('bohio-notifications');
        if (!container) {
            container = document.createElement('div');
            container.id = 'bohio-notifications';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 300px;
            `;
            document.body.appendChild(container);
        }

        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.setAttribute('role', 'alert');
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
        `;

        container.appendChild(notification);

        // Auto-eliminar después de 3 segundos
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    /**
     * Dispara evento personalizado
     */
    dispatchEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, {
            detail: { ...detail, favorites: this.favorites },
            bubbles: true
        });
        document.dispatchEvent(event);
    }

    /**
     * Exporta favoritos como JSON
     */
    exportFavorites() {
        const data = {
            favorites: this.favorites,
            exportDate: new Date().toISOString()
        };

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bohio-favorites-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }

    /**
     * Importa favoritos desde JSON
     */
    importFavorites(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = JSON.parse(e.target.result);
                if (data.favorites && Array.isArray(data.favorites)) {
                    this.favorites = data.favorites;
                    this.saveFavorites();
                    this.updateFavoriteButtons();
                    this.showFavoritesCount();
                    this.showNotification('Favoritos importados correctamente', 'success');
                }
            } catch (err) {
                this.showNotification('Error al importar favoritos', 'danger');
            }
        };
        reader.readAsText(file);
    }

    /**
     * Limpia recursos
     */
    destroy() {
        // Remover event listeners si es necesario
    }
}

// Auto-inicialización
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.bohioFavorites = new FavoritesManager();
    });
} else {
    window.bohioFavorites = new FavoritesManager();
}

export default FavoritesManager;

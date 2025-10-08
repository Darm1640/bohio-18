/** @odoo-module **/

/**
 * BOHIO Real Estate - Property Comparator
 * Sistema de comparación de hasta 3 propiedades
 */

export class PropertyComparator {
    constructor() {
        this.storageKey = 'bohio-comparison';
        this.maxProperties = 3;
        this.comparison = this.loadComparison();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateCompareButtons();
        this.showComparisonCount();
    }

    /**
     * Carga comparación desde localStorage
     */
    loadComparison() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            return stored ? JSON.parse(stored) : [];
        } catch (e) {
            console.error('Error al cargar comparación:', e);
            return [];
        }
    }

    /**
     * Guarda comparación en localStorage
     */
    saveComparison() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.comparison));
            this.dispatchEvent('comparisonChanged');
        } catch (e) {
            console.error('Error al guardar comparación:', e);
        }
    }

    /**
     * Agrega o quita una propiedad de la comparación
     */
    toggleCompare(propertyId, propertyData = null) {
        const index = this.comparison.findIndex(p => p.id === propertyId);

        if (index > -1) {
            this.comparison.splice(index, 1);
            this.showNotification('Eliminada de comparación', 'info');
        } else {
            if (this.comparison.length >= this.maxProperties) {
                this.showNotification(`Solo puedes comparar hasta ${this.maxProperties} propiedades`, 'warning');
                return false;
            }

            const property = propertyData || { id: propertyId };
            this.comparison.push(property);
            this.showNotification('Agregada a comparación', 'success');
        }

        this.saveComparison();
        this.updateCompareButtons();
        this.showComparisonCount();

        return index === -1;
    }

    /**
     * Verifica si una propiedad está en comparación
     */
    isInComparison(propertyId) {
        return this.comparison.some(p => p.id === propertyId);
    }

    /**
     * Obtiene propiedades en comparación
     */
    getComparison() {
        return [...this.comparison];
    }

    /**
     * Limpia la comparación
     */
    clearComparison() {
        if (confirm('¿Deseas limpiar la comparación?')) {
            this.comparison = [];
            this.saveComparison();
            this.updateCompareButtons();
            this.showComparisonCount();
            this.showNotification('Comparación limpiada', 'info');
        }
    }

    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Botones de comparar
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.btn-compare');
            if (btn) {
                e.preventDefault();
                const propertyId = parseInt(btn.dataset.propertyId);

                // Obtener datos de la propiedad del DOM
                const propertyData = this.extractPropertyData(btn);

                if (propertyId) {
                    this.toggleCompare(propertyId, propertyData);
                }
            }
        });

        // Botón de ver comparación
        const viewBtn = document.getElementById('viewComparisonBtn');
        if (viewBtn) {
            viewBtn.addEventListener('click', () => this.showComparisonModal());
        }

        // Botón de limpiar comparación
        const clearBtn = document.getElementById('clearComparisonBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearComparison());
        }
    }

    /**
     * Extrae datos de la propiedad del DOM
     */
    extractPropertyData(btn) {
        const card = btn.closest('.property-card');
        if (!card) return { id: parseInt(btn.dataset.propertyId) };

        return {
            id: parseInt(btn.dataset.propertyId),
            name: card.querySelector('.property-title')?.textContent?.trim(),
            price: card.querySelector('.property-price')?.textContent?.trim(),
            location: card.querySelector('.property-location')?.textContent?.trim(),
            area: card.querySelector('[data-area]')?.dataset?.area,
            bedrooms: card.querySelector('[data-bedrooms]')?.dataset?.bedrooms,
            bathrooms: card.querySelector('[data-bathrooms]')?.dataset?.bathrooms,
            image: card.querySelector('img')?.src
        };
    }

    /**
     * Actualiza botones de comparar
     */
    updateCompareButtons() {
        const buttons = document.querySelectorAll('.btn-compare');
        buttons.forEach(btn => {
            const propertyId = parseInt(btn.dataset.propertyId);
            const isComparing = this.isInComparison(propertyId);
            const isFull = this.comparison.length >= this.maxProperties;

            const icon = btn.querySelector('i');
            if (icon) {
                icon.className = isComparing ? 'fa fa-check-square-o' : 'fa fa-square-o';
            }

            btn.classList.toggle('active', isComparing);
            btn.disabled = !isComparing && isFull;
            btn.setAttribute('aria-pressed', isComparing);
            btn.setAttribute('title', isComparing ? 'Quitar de comparación' : 'Agregar a comparación');
        });
    }

    /**
     * Muestra contador de comparación
     */
    showComparisonCount() {
        const counter = document.getElementById('comparisonCount');
        if (counter) {
            const count = this.comparison.length;
            counter.textContent = count;
            counter.style.display = count > 0 ? 'inline-block' : 'none';
        }

        // Badge en el header
        const badge = document.querySelector('.comparison-badge');
        if (badge) {
            const count = this.comparison.length;
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
        }

        // Habilitar/deshabilitar botón de ver comparación
        const viewBtn = document.getElementById('viewComparisonBtn');
        if (viewBtn) {
            viewBtn.disabled = this.comparison.length < 2;
        }
    }

    /**
     * Muestra modal de comparación
     */
    showComparisonModal() {
        if (this.comparison.length < 2) {
            this.showNotification('Selecciona al menos 2 propiedades para comparar', 'warning');
            return;
        }

        // Verificar si existe el modal
        let modal = document.getElementById('comparisonModal');
        if (!modal) {
            modal = this.createComparisonModal();
            document.body.appendChild(modal);
        }

        // Actualizar contenido
        this.updateComparisonModalContent();

        // Mostrar modal usando Bootstrap
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    /**
     * Crea el modal de comparación
     */
    createComparisonModal() {
        const modal = document.createElement('div');
        modal.id = 'comparisonModal';
        modal.className = 'modal fade';
        modal.setAttribute('tabindex', '-1');
        modal.innerHTML = `
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Comparar Propiedades</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
                    </div>
                    <div class="modal-body" id="comparisonModalBody">
                        <!-- Contenido dinámico -->
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                        <button type="button" class="btn btn-danger" id="modalClearComparison">Limpiar Comparación</button>
                    </div>
                </div>
            </div>
        `;

        // Event listener para limpiar desde el modal
        modal.querySelector('#modalClearComparison').addEventListener('click', () => {
            this.clearComparison();
            bootstrap.Modal.getInstance(modal).hide();
        });

        return modal;
    }

    /**
     * Actualiza contenido del modal de comparación
     */
    updateComparisonModalContent() {
        const body = document.getElementById('comparisonModalBody');
        if (!body) return;

        if (this.comparison.length === 0) {
            body.innerHTML = '<p class="text-center">No hay propiedades para comparar</p>';
            return;
        }

        const features = ['name', 'price', 'location', 'area', 'bedrooms', 'bathrooms'];
        const labels = {
            name: 'Nombre',
            price: 'Precio',
            location: 'Ubicación',
            area: 'Área (m²)',
            bedrooms: 'Habitaciones',
            bathrooms: 'Baños'
        };

        let html = '<div class="table-responsive"><table class="table table-bordered">';
        html += '<thead><tr><th>Característica</th>';

        this.comparison.forEach((prop, index) => {
            html += `<th>Propiedad ${index + 1}</th>`;
        });

        html += '</tr></thead><tbody>';

        features.forEach(feature => {
            html += `<tr><td class="fw-bold">${labels[feature]}</td>`;
            this.comparison.forEach(prop => {
                const value = prop[feature] || 'N/A';
                html += `<td>${value}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table></div>';
        body.innerHTML = html;
    }

    /**
     * Muestra notificación
     */
    showNotification(message, type = 'info') {
        let container = document.getElementById('bohio-notifications');
        if (!container) {
            container = document.createElement('div');
            container.id = 'bohio-notifications';
            container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
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
            detail: { ...detail, comparison: this.comparison },
            bubbles: true
        });
        document.dispatchEvent(event);
    }

    /**
     * Limpia recursos
     */
    destroy() {
        const modal = document.getElementById('comparisonModal');
        if (modal) modal.remove();
    }
}

// Auto-inicialización
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.bohioComparator = new PropertyComparator();
    });
} else {
    window.bohioComparator = new PropertyComparator();
}

export default PropertyComparator;

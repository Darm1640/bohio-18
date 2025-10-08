/** @odoo-module **/
/*
 * Sistema de Comparación de Propiedades con Contextos
 * Integrado con localStorage y sistema de sesión del servidor
 */

import { jsonrpc } from "@web/core/network/rpc_service";

export class PropertyComparisonWidget {
    constructor() {
        this.comparisonList = [];
        this.context = 'public';
        this.maxProperties = 4;
        this.init();
    }

    // =================== INICIALIZACIÓN ===================

    init() {
        this._loadFromStorage();
        this._attachEventListeners();
        this._updateBadge();
        this._createFloatingButton();
    }

    _loadFromStorage() {
        const stored = localStorage.getItem('property_comparison');
        if (stored) {
            try {
                this.comparisonList = JSON.parse(stored);
            } catch (e) {
                this.comparisonList = [];
            }
        }
    }

    _saveToStorage() {
        localStorage.setItem('property_comparison', JSON.stringify(this.comparisonList));
    }

    // =================== EVENTOS ===================

    _attachEventListeners() {
        // Delegar eventos para botones dinámicos
        document.addEventListener('click', (e) => {
            const addBtn = e.target.closest('.btn-add-comparison, .add-to-comparison');
            if (addBtn) {
                e.preventDefault();
                const propertyId = parseInt(addBtn.dataset.propertyId);
                this.addProperty(propertyId);
            }

            const removeBtn = e.target.closest('.btn-remove-comparison, .remove-from-comparison');
            if (removeBtn) {
                e.preventDefault();
                const propertyId = parseInt(removeBtn.dataset.propertyId);
                this.removeProperty(propertyId);
            }

            const viewBtn = e.target.closest('.btn-view-comparison, .view-comparison');
            if (viewBtn) {
                e.preventDefault();
                this.showComparisonModal();
            }

            const clearBtn = e.target.closest('.btn-clear-comparison, .clear-comparison');
            if (clearBtn) {
                e.preventDefault();
                this.clearComparison();
            }
        });
    }

    // =================== BOTÓN FLOTANTE ===================

    _createFloatingButton() {
        const existingBtn = document.getElementById('floating-comparison-btn');
        if (existingBtn) return;

        const floatingBtn = document.createElement('div');
        floatingBtn.id = 'floating-comparison-btn';
        floatingBtn.className = 'floating-comparison-button';
        floatingBtn.innerHTML = `
            <button class="btn btn-primary btn-lg rounded-circle shadow-lg btn-view-comparison"
                    title="Ver comparación"
                    style="width: 60px; height: 60px; position: fixed; bottom: 20px; right: 20px; z-index: 1000; display: none;">
                <i class="fa fa-balance-scale fa-lg"></i>
                <span class="badge bg-danger comparison-count-badge"
                      style="position: absolute; top: -5px; right: -5px; min-width: 24px; height: 24px; border-radius: 12px; display: none;">0</span>
            </button>
        `;

        document.body.appendChild(floatingBtn);
    }

    _updateBadge() {
        const count = this.comparisonList.length;
        const badge = document.querySelector('.comparison-count-badge');
        const button = document.querySelector('.floating-comparison-button .btn');

        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'flex' : 'none';
            badge.style.alignItems = 'center';
            badge.style.justifyContent = 'center';
        }

        if (button) {
            button.style.display = count > 0 ? 'block' : 'none';
        }

        // Actualizar estado de todos los botones de comparar en la página
        this._updateAllButtons();
    }

    _updateAllButtons() {
        const allButtons = document.querySelectorAll('[data-property-id]');

        allButtons.forEach(btn => {
            const propertyId = parseInt(btn.dataset.propertyId);
            const isInComparison = this.comparisonList.includes(propertyId);

            if (btn.classList.contains('btn-add-comparison') || btn.classList.contains('add-to-comparison')) {
                if (isInComparison) {
                    btn.classList.add('active', 'btn-success');
                    btn.classList.remove('btn-outline-primary');
                    const icon = btn.querySelector('i');
                    if (icon) {
                        icon.className = 'fa fa-check';
                    }
                } else {
                    btn.classList.remove('active', 'btn-success');
                    btn.classList.add('btn-outline-primary');
                    const icon = btn.querySelector('i');
                    if (icon) {
                        icon.className = 'fa fa-balance-scale';
                    }
                }
            }
        });
    }

    // =================== AGREGAR/ELIMINAR PROPIEDADES ===================

    async addProperty(propertyId) {
        if (this.comparisonList.includes(propertyId)) {
            this.showNotification('Esta propiedad ya está en la comparación', 'warning');
            return;
        }

        if (this.comparisonList.length >= this.maxProperties) {
            this.showNotification(`Máximo ${this.maxProperties} propiedades para comparar`, 'warning');
            return;
        }

        try {
            const result = await jsonrpc('/property/comparison/add', {
                property_id: propertyId,
                context: this.context
            });

            if (result.success) {
                this.comparisonList = result.property_ids;
                this._saveToStorage();
                this._updateBadge();
                this.showNotification('Propiedad agregada a la comparación', 'success');
            } else {
                this.showNotification(result.message || 'Error al agregar', 'error');
            }
        } catch (error) {
            console.error('Error adding to comparison:', error);
            this.showNotification('Error al agregar a la comparación', 'error');
        }
    }

    async removeProperty(propertyId) {
        try {
            const result = await jsonrpc('/property/comparison/remove', {
                property_id: propertyId
            });

            if (result.success) {
                this.comparisonList = result.property_ids;
                this._saveToStorage();
                this._updateBadge();
                this.showNotification('Propiedad eliminada de la comparación', 'info');

                // Si estamos en el modal, actualizar
                const modal = document.querySelector('#comparisonModal');
                if (modal && modal.classList.contains('show')) {
                    if (this.comparisonList.length === 0) {
                        const modalInstance = bootstrap.Modal.getInstance(modal);
                        if (modalInstance) modalInstance.hide();
                    } else {
                        this.showComparisonModal();
                    }
                }
            }
        } catch (error) {
            console.error('Error removing from comparison:', error);
            this.showNotification('Error al eliminar de la comparación', 'error');
        }
    }

    async clearComparison() {
        if (this.comparisonList.length === 0) return;

        if (!confirm('¿Deseas limpiar toda la lista de comparación?')) return;

        try {
            const result = await jsonrpc('/property/comparison/clear', {});

            if (result.success) {
                this.comparisonList = [];
                this._saveToStorage();
                this._updateBadge();
                this.showNotification('Lista de comparación limpiada', 'info');

                // Cerrar modal si está abierto
                const modal = document.querySelector('#comparisonModal');
                if (modal && modal.classList.contains('show')) {
                    const modalInstance = bootstrap.Modal.getInstance(modal);
                    if (modalInstance) modalInstance.hide();
                }
            }
        } catch (error) {
            console.error('Error clearing comparison:', error);
            this.showNotification('Error al limpiar comparación', 'error');
        }
    }

    // =================== MODAL DE COMPARACIÓN ===================

    async showComparisonModal() {
        if (this.comparisonList.length < 2) {
            this.showNotification('Agrega al menos 2 propiedades para comparar', 'warning');
            return;
        }

        try {
            const data = await jsonrpc('/property/comparison/get', {
                context: this.context
            });

            if (!data.properties || data.properties.length === 0) {
                this.showNotification('No hay propiedades para comparar', 'warning');
                return;
            }

            this._renderComparisonModal(data);
        } catch (error) {
            console.error('Error getting comparison data:', error);
            this.showNotification('Error al cargar datos de comparación', 'error');
        }
    }

    _renderComparisonModal(data) {
        const { properties, fields, differences } = data;

        // Crear o actualizar modal
        let modal = document.querySelector('#comparisonModal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'comparisonModal';
            modal.className = 'modal fade';
            modal.setAttribute('tabindex', '-1');
            document.body.appendChild(modal);
        }

        modal.innerHTML = `
            <div class="modal-dialog modal-xl modal-dialog-scrollable">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="fa fa-balance-scale me-2"></i>
                            Comparación de Propiedades (${properties.length})
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover table-bordered mb-0 comparison-table">
                                <thead class="table-light sticky-top">
                                    <tr>
                                        <th class="text-center" style="min-width: 150px;">Característica</th>
                                        ${properties.map(prop => `
                                            <th class="text-center" style="min-width: 200px;">
                                                <div class="property-header p-2">
                                                    <img src="${prop.image_url}"
                                                         alt="${prop.name}"
                                                         class="img-fluid rounded mb-2"
                                                         style="max-height: 120px; object-fit: cover;">
                                                    <h6 class="mb-1">${prop.name}</h6>
                                                    <small class="text-muted d-block mb-2">${prop.property_type}</small>
                                                    <button class="btn btn-sm btn-danger btn-remove-comparison"
                                                            data-property-id="${prop.id}">
                                                        <i class="fa fa-times"></i> Quitar
                                                    </button>
                                                </div>
                                            </th>
                                        `).join('')}
                                    </tr>
                                </thead>
                                <tbody>
                                    ${fields.map(field => {
                                        const isDifferent = differences.some(d => d.field === field.name);
                                        return `
                                            <tr class="${isDifferent ? 'table-warning' : ''}">
                                                <td class="fw-bold">
                                                    ${field.label}
                                                    ${isDifferent ? '<i class="fa fa-exclamation-triangle text-warning ms-2"></i>' : ''}
                                                </td>
                                                ${properties.map(prop => `
                                                    <td class="text-center">${prop[field.name] || '-'}</td>
                                                `).join('')}
                                            </tr>
                                        `;
                                    }).join('')}
                                </tbody>
                            </table>
                        </div>

                        ${differences.length > 0 ? `
                            <div class="alert alert-info m-3">
                                <h6 class="alert-heading">
                                    <i class="fa fa-info-circle me-2"></i>
                                    Diferencias Detectadas (${differences.length})
                                </h6>
                                <ul class="mb-0">
                                    ${differences.map(d => `<li>${d.label}</li>`).join('')}
                                </ul>
                            </div>
                        ` : `
                            <div class="alert alert-success m-3">
                                <i class="fa fa-check-circle me-2"></i>
                                Las propiedades son muy similares
                            </div>
                        `}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-danger btn-clear-comparison">
                            <i class="fa fa-trash me-2"></i>Limpiar Todo
                        </button>
                        <button type="button" class="btn btn-primary" onclick="window.print()">
                            <i class="fa fa-print me-2"></i>Imprimir
                        </button>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                    </div>
                </div>
            </div>
        `;

        // Mostrar modal usando Bootstrap 5
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();
    }

    // =================== NOTIFICACIONES ===================

    showNotification(message, type = 'info') {
        // Crear contenedor si no existe
        let container = document.querySelector('.notification-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notification-container';
            container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
            document.body.appendChild(container);
        }

        // Crear notificación
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
        notification.style.cssText = 'min-width: 300px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        container.appendChild(notification);

        // Auto-remover después de 4 segundos
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 150);
        }, 4000);
    }
}

// Auto-inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.propertyComparison = new PropertyComparisonWidget();
    });
} else {
    window.propertyComparison = new PropertyComparisonWidget();
}

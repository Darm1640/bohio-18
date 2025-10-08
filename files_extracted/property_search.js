/** @odoo-module **/
/* 
 * Sistema de Búsqueda de Propiedades con Comparación
 * Soporta contextos múltiples, autocompletado inteligente y comparación de propiedades
 */

import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PropertySearchWidget = publicWidget.Widget.extend({
    selector: '.property_search_container',
    events: {
        'keyup .property-search-input': '_onSearchInput',
        'click .autocomplete-result': '_onAutocompleteSelect',
        'click .add-to-comparison': '_onAddToComparison',
        'click .remove-from-comparison': '_onRemoveFromComparison',
        'click .view-comparison': '_onViewComparison',
        'click .clear-comparison': '_onClearComparison',
        'change .subdivision-filter': '_onSubdivisionChange',
        'click .property-filter': '_onFilterClick',
    },

    /**
     * Inicialización del widget
     */
    start: function() {
        this._super.apply(this, arguments);
        this.context = this.$el.data('context') || 'public';
        this.comparisonList = [];
        this.autocompleteTimeout = null;
        
        // Cargar lista de comparación del localStorage
        this._loadComparisonFromStorage();
        this._updateComparisonBadge();
        
        return this._super.apply(this, arguments);
    },

    // =================== AUTOCOMPLETADO INTELIGENTE ===================

    /**
     * Maneja el input de búsqueda con debounce
     */
    _onSearchInput: function(ev) {
        clearTimeout(this.autocompleteTimeout);
        const $input = $(ev.currentTarget);
        const term = $input.val().trim();
        
        if (term.length < 2) {
            this._hideAutocomplete();
            return;
        }
        
        this.autocompleteTimeout = setTimeout(() => {
            this._performAutocomplete(term);
        }, 300); // Debounce de 300ms
    },

    /**
     * Realiza la búsqueda de autocompletado
     */
    _performAutocomplete: function(term) {
        const subdivision = this.$('.subdivision-filter').val() || 'all';
        
        jsonrpc('/property/search/autocomplete/' + this.context, {
            term: term,
            subdivision: subdivision,
            limit: 10
        }).then((result) => {
            this._renderAutocompleteResults(result.results);
        });
    },

    /**
     * Renderiza los resultados del autocompletado
     */
    _renderAutocompleteResults: function(results) {
        const $container = this.$('.autocomplete-container');
        
        if (!results || results.length === 0) {
            $container.html('<div class="autocomplete-empty">No se encontraron resultados</div>');
            $container.show();
            return;
        }
        
        let html = '<ul class="autocomplete-results list-unstyled">';
        
        results.forEach((result) => {
            html += `
                <li class="autocomplete-result" 
                    data-type="${result.type}" 
                    data-id="${result.id}"
                    data-city-id="${result.city_id || ''}"
                    data-state-id="${result.state_id || ''}"
                    data-region-id="${result.region_id || ''}"
                    data-project-id="${result.project_id || ''}"
                    data-property-id="${result.property_id || ''}">
                    <div class="result-label">${result.label}</div>
                    <div class="result-count text-muted small">
                        ${result.property_count} ${result.property_count === 1 ? 'propiedad' : 'propiedades'}
                    </div>
                </li>
            `;
        });
        
        html += '</ul>';
        
        $container.html(html);
        $container.show();
    },

    /**
     * Oculta el autocompletado
     */
    _hideAutocomplete: function() {
        this.$('.autocomplete-container').hide();
    },

    /**
     * Maneja la selección de un resultado de autocompletado
     */
    _onAutocompleteSelect: function(ev) {
        const $result = $(ev.currentTarget);
        const type = $result.data('type');
        
        // Construir parámetros según el tipo seleccionado
        const params = new URLSearchParams(window.location.search);
        
        // Limpiar parámetros de ubicación anteriores
        params.delete('city_id');
        params.delete('state_id');
        params.delete('region_id');
        params.delete('project_id');
        params.delete('search');
        
        // Agregar nuevos parámetros según el tipo
        if (type === 'city' && $result.data('city-id')) {
            params.set('city_id', $result.data('city-id'));
        } else if (type === 'region' && $result.data('region-id')) {
            params.set('region_id', $result.data('region-id'));
        } else if (type === 'project' && $result.data('project-id')) {
            params.set('project_id', $result.data('project-id'));
        } else if (type === 'property' && $result.data('property-id')) {
            // Redirigir directamente a la propiedad
            window.location.href = `/property/get/${$result.data('property-id')}/${this.context}`;
            return;
        }
        
        // Redirigir con los nuevos parámetros
        window.location.href = `/property/search/${this.context}?${params.toString()}`;
    },

    /**
     * Maneja el cambio de subdivisión del autocompletado
     */
    _onSubdivisionChange: function(ev) {
        const $input = this.$('.property-search-input');
        const term = $input.val().trim();
        
        if (term.length >= 2) {
            this._performAutocomplete(term);
        }
    },

    // =================== SISTEMA DE COMPARACIÓN ===================

    /**
     * Agrega una propiedad a la comparación
     */
    _onAddToComparison: function(ev) {
        ev.preventDefault();
        const $btn = $(ev.currentTarget);
        const propertyId = $btn.data('property-id');
        
        if (this.comparisonList.includes(propertyId)) {
            this._showNotification('Esta propiedad ya está en la comparación', 'warning');
            return;
        }
        
        if (this.comparisonList.length >= 4) {
            this._showNotification('Máximo 4 propiedades para comparar', 'warning');
            return;
        }
        
        jsonrpc('/property/comparison/add', {
            property_id: propertyId,
            context: this.context
        }).then((result) => {
            if (result.success) {
                this.comparisonList = result.property_ids;
                this._saveComparisonToStorage();
                this._updateComparisonBadge();
                this._updatePropertyButton($btn, 'added');
                this._showNotification('Propiedad agregada a la comparación', 'success');
            } else {
                this._showNotification(result.message, 'error');
            }
        });
    },

    /**
     * Elimina una propiedad de la comparación
     */
    _onRemoveFromComparison: function(ev) {
        ev.preventDefault();
        const $btn = $(ev.currentTarget);
        const propertyId = $btn.data('property-id');
        
        jsonrpc('/property/comparison/remove', {
            property_id: propertyId
        }).then((result) => {
            if (result.success) {
                this.comparisonList = result.property_ids;
                this._saveComparisonToStorage();
                this._updateComparisonBadge();
                
                // Si estamos en el modal, remover la columna
                if ($btn.closest('.comparison-modal').length) {
                    $btn.closest('.property-column').remove();
                    if (this.comparisonList.length === 0) {
                        $('.comparison-modal').modal('hide');
                    }
                } else {
                    this._updatePropertyButton($btn, 'removed');
                }
                
                this._showNotification('Propiedad eliminada de la comparación', 'info');
            }
        });
    },

    /**
     * Muestra el modal de comparación
     */
    _onViewComparison: function(ev) {
        ev.preventDefault();
        
        if (this.comparisonList.length < 2) {
            this._showNotification('Agrega al menos 2 propiedades para comparar', 'warning');
            return;
        }
        
        this._showComparisonModal();
    },

    /**
     * Limpia toda la lista de comparación
     */
    _onClearComparison: function(ev) {
        ev.preventDefault();
        
        jsonrpc('/property/comparison/clear', {}).then((result) => {
            if (result.success) {
                this.comparisonList = [];
                this._saveComparisonToStorage();
                this._updateComparisonBadge();
                this._showNotification('Lista de comparación limpiada', 'info');
                
                // Si estamos en el modal, cerrarlo
                if ($(ev.currentTarget).closest('.comparison-modal').length) {
                    $('.comparison-modal').modal('hide');
                }
                
                // Actualizar todos los botones
                this.$('.remove-from-comparison').each((i, btn) => {
                    this._updatePropertyButton($(btn), 'removed');
                });
            }
        });
    },

    /**
     * Muestra el modal de comparación con los datos
     */
    _showComparisonModal: function() {
        jsonrpc('/property/comparison/get', {
            context: this.context
        }).then((data) => {
            if (!data.properties || data.properties.length === 0) {
                this._showNotification('No hay propiedades para comparar', 'warning');
                return;
            }
            
            this._renderComparisonModal(data);
        });
    },

    /**
     * Renderiza el modal de comparación
     */
    _renderComparisonModal: function(data) {
        const properties = data.properties;
        const fields = data.fields;
        const differences = data.differences;
        
        let html = `
            <div class="modal fade comparison-modal" tabindex="-1" role="dialog">
                <div class="modal-dialog modal-xl" role="document">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fa fa-balance-scale"></i> Comparación de Propiedades
                            </h5>
                            <button type="button" class="close" data-dismiss="modal">
                                <span>&times;</span>
                            </button>
                        </div>
                        <div class="modal-body">
                            <div class="comparison-table-wrapper">
                                <table class="table table-bordered comparison-table">
                                    <thead>
                                        <tr>
                                            <th class="field-name-column">Característica</th>
                                            ${properties.map(prop => `
                                                <th class="property-column">
                                                    <div class="property-header">
                                                        ${prop.image ? `<img src="data:image/png;base64,${prop.image}" class="property-thumb" />` : ''}
                                                        <div class="property-name">${prop.name}</div>
                                                        <button class="btn btn-sm btn-danger remove-from-comparison mt-2" 
                                                                data-property-id="${prop.id}">
                                                            <i class="fa fa-times"></i> Quitar
                                                        </button>
                                                    </div>
                                                </th>
                                            `).join('')}
                                        </tr>
                                    </thead>
                                    <tbody>
        `;
        
        // Renderizar campos
        fields.forEach((field) => {
            const fieldName = field.name;
            const isDifferent = differences.some(d => d.field === fieldName);
            const rowClass = isDifferent ? 'difference-row' : '';
            
            html += `
                <tr class="${rowClass}">
                    <td class="field-name">
                        ${field.label}
                        ${isDifferent ? '<i class="fa fa-exclamation-triangle text-warning ml-2" title="Diferencia"></i>' : ''}
                    </td>
                    ${properties.map(prop => `
                        <td class="field-value">${prop[fieldName] || '-'}</td>
                    `).join('')}
                </tr>
            `;
        });
        
        html += `
                                    </tbody>
                                </table>
                            </div>
                            
                            ${differences.length > 0 ? `
                                <div class="alert alert-info mt-3">
                                    <h6><i class="fa fa-info-circle"></i> Diferencias Detectadas (${differences.length})</h6>
                                    <ul class="mb-0">
                                        ${differences.map(d => `<li>${d.label}</li>`).join('')}
                                    </ul>
                                </div>
                            ` : `
                                <div class="alert alert-success mt-3">
                                    <i class="fa fa-check-circle"></i> Las propiedades son muy similares
                                </div>
                            `}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary clear-comparison">
                                <i class="fa fa-trash"></i> Limpiar Comparación
                            </button>
                            <button type="button" class="btn btn-primary" onclick="window.print()">
                                <i class="fa fa-print"></i> Imprimir
                            </button>
                            <button type="button" class="btn btn-secondary" data-dismiss="modal">Cerrar</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remover modales anteriores y agregar nuevo
        $('.comparison-modal').remove();
        $('body').append(html);
        
        // Mostrar modal
        $('.comparison-modal').modal('show');
    },

    // =================== MÉTODOS AUXILIARES ===================

    /**
     * Actualiza el badge del contador de comparación
     */
    _updateComparisonBadge: function() {
        const count = this.comparisonList.length;
        const $badge = $('.comparison-badge');
        
        if (count > 0) {
            $badge.text(count).show();
            $('.view-comparison').prop('disabled', count < 2);
        } else {
            $badge.hide();
            $('.view-comparison').prop('disabled', true);
        }
    },

    /**
     * Actualiza el estado visual del botón de una propiedad
     */
    _updatePropertyButton: function($btn, action) {
        const $card = $btn.closest('.property-card');
        
        if (action === 'added') {
            $btn.removeClass('add-to-comparison btn-outline-primary')
                .addClass('remove-from-comparison btn-danger')
                .html('<i class="fa fa-times"></i> Quitar de Comparación');
            $card.addClass('in-comparison');
        } else if (action === 'removed') {
            $btn.removeClass('remove-from-comparison btn-danger')
                .addClass('add-to-comparison btn-outline-primary')
                .html('<i class="fa fa-balance-scale"></i> Comparar');
            $card.removeClass('in-comparison');
        }
    },

    /**
     * Guarda la lista de comparación en localStorage
     */
    _saveComparisonToStorage: function() {
        localStorage.setItem('property_comparison', JSON.stringify(this.comparisonList));
    },

    /**
     * Carga la lista de comparación desde localStorage
     */
    _loadComparisonFromStorage: function() {
        try {
            const stored = localStorage.getItem('property_comparison');
            this.comparisonList = stored ? JSON.parse(stored) : [];
        } catch (e) {
            this.comparisonList = [];
        }
    },

    /**
     * Muestra una notificación temporal
     */
    _showNotification: function(message, type = 'info') {
        const typeClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';
        
        const $notification = $(`
            <div class="alert ${typeClass} property-notification" role="alert">
                ${message}
            </div>
        `);
        
        $('.notification-container').append($notification);
        
        setTimeout(() => {
            $notification.fadeOut(() => $notification.remove());
        }, 3000);
    },

    /**
     * Maneja click en filtros
     */
    _onFilterClick: function(ev) {
        const $filter = $(ev.currentTarget);
        $filter.toggleClass('active');
        
        // Aquí puedes agregar lógica adicional para aplicar filtros
        this._applyFilters();
    },

    /**
     * Aplica los filtros seleccionados
     */
    _applyFilters: function() {
        const params = new URLSearchParams(window.location.search);
        
        // Recopilar filtros activos
        this.$('.property-filter.active').each((i, filter) => {
            const $filter = $(filter);
            const filterName = $filter.data('filter');
            const filterValue = $filter.data('value');
            
            params.set(filterName, filterValue);
        });
        
        // Recargar con nuevos filtros
        window.location.href = window.location.pathname + '?' + params.toString();
    }
});

// =================== INICIALIZACIÓN AL CARGAR EL DOM ===================

$(document).ready(function() {
    // Cerrar autocompletado al hacer click fuera
    $(document).on('click', function(e) {
        if (!$(e.target).closest('.property-search-input, .autocomplete-container').length) {
            $('.autocomplete-container').hide();
        }
    });
    
    // Animaciones de tarjetas de propiedades
    $('.property-card').hover(
        function() {
            $(this).addClass('shadow-lg').css('transform', 'translateY(-5px)');
        },
        function() {
            $(this).removeClass('shadow-lg').css('transform', 'translateY(0)');
        }
    );
    
    // Inicializar tooltips
    $('[data-toggle="tooltip"]').tooltip();
});

export default PropertySearchWidget;

/** @odoo-module **/

import { createElement } from '../utils/dom_helpers';
import { formatPrice, getPriceLabel, formatLocation, formatArea } from '../utils/formatters';
import { PLACEHOLDER_IMAGE } from '../utils/constants';

/**
 * BOHIO Enhanced Property Card Component
 * Tarjeta de propiedad con todas las funcionalidades integradas
 * - Botones flotantes con efectos 3D y glassmorphism
 * - Modales de compartir, reportar, agendar
 * - Integración WhatsApp y Google Maps
 * - Favoritos y comparación
 */

export class PropertyCardEnhanced {
    constructor(property, options = {}) {
        this.property = property;
        this.options = {
            showActions: true,
            showFloatingButtons: true,
            enableCompare: true,
            enableWishlist: true,
            enableShare: true,
            ...options
        };
    }

    /**
     * Crear la tarjeta completa
     */
    create() {
        const card = createElement('div', {
            className: 'bohio-property-card-enhanced position-relative',
            attributes: {
                'data-property-id': this.property.id,
                'data-property-code': this.property.code
            }
        });

        // Contenedor principal con efecto 3D
        const cardInner = createElement('div', {
            className: 'card h-100 shadow-lg border-0 property-card-3d',
            children: [
                this._createImageSection(),
                this._createBodySection(),
                this.options.showFloatingButtons ? this._createFloatingButtons() : null
            ].filter(Boolean)
        });

        card.appendChild(cardInner);
        return card;
    }

    /**
     * Sección de imagen con badges y overlay
     * @private
     */
    _createImageSection() {
        const imageSection = createElement('div', {
            className: 'position-relative property-image-wrapper',
            children: [
                // Imagen principal
                this._createImage(),
                // Badges superiores
                this._createTopBadges(),
                // Overlay con información rápida
                this._createImageOverlay(),
                // Botones de acción rápida
                this.options.showActions ? this._createQuickActions() : null
            ].filter(Boolean)
        });

        return imageSection;
    }

    /**
     * Crear imagen principal
     * @private
     */
    _createImage() {
        const imageUrl = this.property.image_url || PLACEHOLDER_IMAGE;

        return createElement('img', {
            className: 'card-img-top property-image',
            attributes: {
                src: imageUrl,
                alt: this.property.name,
                loading: 'lazy',
                onerror: `this.src='${PLACEHOLDER_IMAGE}'`
            }
        });
    }

    /**
     * Badges superiores (tipo de servicio, destacado, nuevo)
     * @private
     */
    _createTopBadges() {
        const badges = createElement('div', {
            className: 'position-absolute top-0 start-0 p-2 d-flex gap-2 flex-wrap'
        });

        // Badge de tipo de servicio con precio
        const serviceType = this.property.type_service || 'Venta';
        const priceLabel = serviceType === 'Arriendo' ? '/mes' : '';

        badges.appendChild(
            createElement('span', {
                className: `badge bg-danger bg-gradient shadow-sm`,
                children: [
                    createElement('i', `bi bi-${serviceType === 'Arriendo' ? 'key' : 'house'} me-1`),
                    document.createTextNode(`${serviceType} ${formatPrice(this.property.price)}${priceLabel}`)
                ]
            })
        );

        // Badge de proyecto si aplica
        if (this.property.project_id) {
            badges.appendChild(
                createElement('span', {
                    className: 'badge bg-primary bg-gradient shadow-sm',
                    children: [
                        createElement('i', 'bi bi-building me-1'),
                        document.createTextNode(this.property.project_name)
                    ]
                })
            );
        }

        // Badge de nuevo/destacado
        if (this.property.is_new) {
            badges.appendChild(
                createElement('span', {
                    className: 'badge bg-success bg-gradient shadow-sm',
                    text: 'NUEVO'
                })
            );
        }

        return badges;
    }

    /**
     * Overlay con información adicional
     * @private
     */
    _createImageOverlay() {
        return createElement('div', {
            className: 'property-image-overlay',
            children: [
                // Contador de fotos
                this.property.image_count > 0 ? createElement('div', {
                    className: 'photo-counter',
                    children: [
                        createElement('i', 'bi bi-camera-fill me-1'),
                        document.createTextNode(`${this.property.image_count} fotos`)
                    ]
                }) : null,

                // Video tour si existe
                this.property.has_video ? createElement('div', {
                    className: 'video-badge',
                    children: [
                        createElement('i', 'bi bi-play-circle-fill me-1'),
                        document.createTextNode('Video Tour')
                    ]
                }) : null
            ].filter(Boolean)
        });
    }

    /**
     * Botones de acción rápida sobre la imagen
     * @private
     */
    _createQuickActions() {
        return createElement('div', {
            className: 'quick-actions position-absolute top-0 end-0 p-2',
            children: [
                // Botón favoritos
                this._createWishlistButton(),
                // Botón comparar
                this._createCompareButton()
            ]
        });
    }

    /**
     * Botón de favoritos
     * @private
     */
    _createWishlistButton() {
        const isFavorite = this.property.is_favorite || false;

        return createElement('button', {
            className: `btn btn-glass-3d btn-wishlist ${isFavorite ? 'active' : ''}`,
            attributes: {
                type: 'button',
                'data-bs-toggle': 'tooltip',
                'data-bs-placement': 'left',
                title: isFavorite ? 'Quitar de favoritos' : 'Agregar a favoritos',
                onclick: `toggleWishlist(${this.property.id})`
            },
            children: [
                createElement('i', `bi bi-heart${isFavorite ? '-fill' : ''}`)
            ]
        });
    }

    /**
     * Botón de comparar
     * @private
     */
    _createCompareButton() {
        return createElement('button', {
            className: 'btn btn-glass-3d btn-compare ms-2',
            attributes: {
                type: 'button',
                'data-bs-toggle': 'tooltip',
                'data-bs-placement': 'left',
                title: 'Comparar propiedad',
                onclick: `addToCompare(${this.property.id})`
            },
            children: [
                createElement('i', 'bi bi-grid-3x3-gap')
            ]
        });
    }

    /**
     * Sección del cuerpo de la tarjeta
     * @private
     */
    _createBodySection() {
        return createElement('div', {
            className: 'card-body d-flex flex-column',
            children: [
                // Título y código
                this._createHeader(),
                // Ubicación completa con región
                this._createLocationInfo(),
                // Características
                this._createFeatures(),
                // Amenidades
                this._createAmenities(),
                // Precio y condiciones
                this._createPriceSection(),
                // Botón principal
                this._createMainButton()
            ]
        });
    }

    /**
     * Header con título y código
     * @private
     */
    _createHeader() {
        return createElement('div', {
            className: 'mb-2',
            children: [
                createElement('h5', {
                    className: 'card-title text-truncate mb-1',
                    text: this.property.name,
                    attributes: { title: this.property.name }
                }),
                createElement('small', {
                    className: 'text-muted',
                    text: `Código: ${this.property.code || 'N/A'}`
                })
            ]
        });
    }

    /**
     * Información de ubicación completa
     * @private
     */
    _createLocationInfo() {
        const location = [];

        if (this.property.neighborhood) location.push(this.property.neighborhood);
        if (this.property.region_id) location.push(this.property.region_id[1]);
        if (this.property.city) location.push(this.property.city);

        return createElement('div', {
            className: 'location-info mb-3',
            children: [
                createElement('i', 'bi bi-geo-alt-fill text-danger me-2'),
                createElement('span', {
                    className: 'text-muted small',
                    text: location.join(', ')
                })
            ]
        });
    }

    /**
     * Características principales
     * @private
     */
    _createFeatures() {
        return createElement('div', {
            className: 'd-flex justify-content-between mb-3 property-features',
            children: [
                // Área
                this.property.area > 0 ? this._createFeatureItem('bi-rulers', `${formatArea(this.property.area)}`) : null,
                // Habitaciones
                this.property.bedrooms > 0 ? this._createFeatureItem('bi-door-open', `${this.property.bedrooms} Hab`) : null,
                // Baños
                this.property.bathrooms > 0 ? this._createFeatureItem('bi-droplet', `${this.property.bathrooms} Baños`) : null,
                // Parqueaderos
                this.property.parking > 0 ? this._createFeatureItem('bi-car-front', `${this.property.parking} Park`) : null
            ].filter(Boolean)
        });
    }

    /**
     * Item de característica
     * @private
     */
    _createFeatureItem(icon, text) {
        return createElement('div', {
            className: 'feature-item text-center',
            children: [
                createElement('i', `bi ${icon} d-block mb-1 text-primary`),
                createElement('small', {
                    className: 'text-muted',
                    text: text
                })
            ]
        });
    }

    /**
     * Amenidades destacadas
     * @private
     */
    _createAmenities() {
        const amenities = [];

        if (this.property.has_pool) amenities.push({ icon: 'bi-water', text: 'Piscina' });
        if (this.property.has_gym) amenities.push({ icon: 'bi-heart-pulse', text: 'Gimnasio' });
        if (this.property.has_security) amenities.push({ icon: 'bi-shield-check', text: 'Vigilancia' });
        if (this.property.is_furnished) amenities.push({ icon: 'bi-lamp', text: 'Amoblado' });

        if (amenities.length === 0) return null;

        return createElement('div', {
            className: 'd-flex gap-2 mb-3 flex-wrap',
            children: amenities.map(amenity =>
                createElement('span', {
                    className: 'badge bg-light text-dark',
                    children: [
                        createElement('i', `${amenity.icon} me-1`),
                        document.createTextNode(amenity.text)
                    ]
                })
            )
        });
    }

    /**
     * Sección de precio
     * @private
     */
    _createPriceSection() {
        const serviceType = this.property.type_service || 'Venta';
        const priceLabel = serviceType === 'Arriendo' ? 'Arriendo/mes' : 'Precio de venta';

        return createElement('div', {
            className: 'price-section mb-3 mt-auto',
            children: [
                createElement('small', {
                    className: 'text-muted d-block',
                    text: priceLabel
                }),
                createElement('h4', {
                    className: 'text-danger mb-0',
                    text: formatPrice(this.property.price)
                }),
                // Administración si aplica
                this.property.administration_fee && serviceType === 'Arriendo' ?
                    createElement('small', {
                        className: 'text-muted',
                        text: `+ Admin: ${formatPrice(this.property.administration_fee)}`
                    }) : null
            ].filter(Boolean)
        });
    }

    /**
     * Botón principal de ver detalles
     * @private
     */
    _createMainButton() {
        return createElement('a', {
            className: 'btn btn-danger btn-gradient w-100 shadow-sm',
            attributes: {
                href: `/property/${this.property.id}`
            },
            children: [
                createElement('i', 'bi bi-eye me-2'),
                document.createTextNode('Ver detalles')
            ]
        });
    }

    /**
     * Botones flotantes con efectos 3D
     * @private
     */
    _createFloatingButtons() {
        return createElement('div', {
            className: 'floating-actions-container',
            children: [
                // Botón expandible principal
                createElement('button', {
                    className: 'btn-floating-main btn-glass-3d',
                    attributes: {
                        type: 'button',
                        onclick: 'toggleFloatingActions(this)'
                    },
                    children: [
                        createElement('i', 'bi bi-three-dots-vertical')
                    ]
                }),

                // Contenedor de acciones
                createElement('div', {
                    className: 'floating-actions',
                    children: [
                        // WhatsApp
                        this._createFloatingButton('bi-whatsapp', 'WhatsApp', 'success', () => {
                            const message = `Hola, estoy interesado en la propiedad ${this.property.name} (Código: ${this.property.code})`;
                            const phone = '573001234567'; // Número de WhatsApp de la empresa
                            window.open(`https://wa.me/${phone}?text=${encodeURIComponent(message)}`, '_blank');
                        }),

                        // Google Maps
                        this._createFloatingButton('bi-geo-alt-fill', 'Ver en mapa', 'primary', () => {
                            if (this.property.latitude && this.property.longitude) {
                                window.open(`https://maps.google.com/?q=${this.property.latitude},${this.property.longitude}`, '_blank');
                            }
                        }),

                        // Compartir
                        this._createFloatingButton('bi-share-fill', 'Compartir', 'info', () => {
                            this._showShareModal();
                        }),

                        // Agendar cita
                        this._createFloatingButton('bi-calendar-check', 'Agendar cita', 'warning', () => {
                            this._showScheduleModal();
                        }),

                        // Reportar
                        this._createFloatingButton('bi-flag-fill', 'Reportar', 'danger', () => {
                            this._showReportModal();
                        })
                    ]
                })
            ]
        });
    }

    /**
     * Crear botón flotante individual
     * @private
     */
    _createFloatingButton(icon, tooltip, color, onClick) {
        const button = createElement('button', {
            className: `btn-floating btn-glass-3d btn-${color}`,
            attributes: {
                type: 'button',
                'data-bs-toggle': 'tooltip',
                'data-bs-placement': 'left',
                title: tooltip
            },
            children: [
                createElement('i', `bi ${icon}`)
            ]
        });

        button.addEventListener('click', onClick);
        return button;
    }

    /**
     * Modal de compartir
     * @private
     */
    _showShareModal() {
        const url = window.location.origin + `/property/${this.property.id}`;
        const title = this.property.name;

        // Si el navegador soporta Web Share API
        if (navigator.share) {
            navigator.share({
                title: title,
                text: `Mira esta propiedad: ${title}`,
                url: url
            });
        } else {
            // Fallback: mostrar modal con opciones
            this._createShareModalFallback(url, title);
        }
    }

    /**
     * Modal de compartir fallback
     * @private
     */
    _createShareModalFallback(url, title) {
        // Crear modal dinámico con opciones de compartir
        const modal = createElement('div', {
            className: 'modal fade',
            attributes: {
                tabindex: '-1',
                role: 'dialog'
            },
            children: [
                createElement('div', {
                    className: 'modal-dialog modal-dialog-centered',
                    children: [
                        createElement('div', {
                            className: 'modal-content glass-modal',
                            children: [
                                // Header
                                createElement('div', {
                                    className: 'modal-header border-0',
                                    children: [
                                        createElement('h5', {
                                            className: 'modal-title',
                                            text: 'Compartir propiedad'
                                        }),
                                        createElement('button', {
                                            className: 'btn-close',
                                            attributes: {
                                                type: 'button',
                                                'data-bs-dismiss': 'modal'
                                            }
                                        })
                                    ]
                                }),
                                // Body con opciones
                                createElement('div', {
                                    className: 'modal-body',
                                    children: [
                                        // Facebook
                                        this._createShareOption('Facebook', 'bi-facebook', () => {
                                            window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`, '_blank');
                                        }),
                                        // Twitter
                                        this._createShareOption('Twitter', 'bi-twitter', () => {
                                            window.open(`https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title)}`, '_blank');
                                        }),
                                        // LinkedIn
                                        this._createShareOption('LinkedIn', 'bi-linkedin', () => {
                                            window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`, '_blank');
                                        }),
                                        // Copiar enlace
                                        this._createShareOption('Copiar enlace', 'bi-link-45deg', () => {
                                            navigator.clipboard.writeText(url);
                                            // Mostrar toast de confirmación
                                            this._showToast('Enlace copiado al portapapeles');
                                        })
                                    ]
                                })
                            ]
                        })
                    ]
                })
            ]
        });

        // Agregar al DOM y mostrar
        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();

        // Limpiar al cerrar
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }

    /**
     * Opción de compartir
     * @private
     */
    _createShareOption(text, icon, onClick) {
        const button = createElement('button', {
            className: 'btn btn-glass-3d w-100 mb-2 text-start',
            attributes: {
                type: 'button'
            },
            children: [
                createElement('i', `bi ${icon} me-2`),
                document.createTextNode(text)
            ]
        });

        button.addEventListener('click', onClick);
        return button;
    }

    /**
     * Modal de agendar cita
     * @private
     */
    _showScheduleModal() {
        // Similar al modal de compartir, crear formulario para agendar
        console.log('Mostrar modal de agendar cita');
    }

    /**
     * Modal de reportar
     * @private
     */
    _showReportModal() {
        // Modal para reportar problema con la propiedad
        console.log('Mostrar modal de reportar');
    }

    /**
     * Mostrar toast de notificación
     * @private
     */
    _showToast(message) {
        // Crear y mostrar toast de Bootstrap
        const toast = createElement('div', {
            className: 'toast align-items-center text-white bg-success border-0',
            attributes: {
                role: 'alert',
                'aria-live': 'assertive',
                'aria-atomic': 'true'
            },
            children: [
                createElement('div', {
                    className: 'd-flex',
                    children: [
                        createElement('div', {
                            className: 'toast-body',
                            text: message
                        }),
                        createElement('button', {
                            className: 'btn-close btn-close-white me-2 m-auto',
                            attributes: {
                                type: 'button',
                                'data-bs-dismiss': 'toast'
                            }
                        })
                    ]
                })
            ]
        });

        // Contenedor de toasts
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = createElement('div', {
                id: 'toast-container',
                className: 'toast-container position-fixed bottom-0 end-0 p-3'
            });
            document.body.appendChild(toastContainer);
        }

        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remover después de ocultarse
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }
}

/**
 * Funciones globales para los eventos onclick
 */
window.toggleWishlist = function(propertyId) {
    // Lógica para agregar/quitar de favoritos
    console.log('Toggle wishlist:', propertyId);

    // Aquí iría la llamada RPC para actualizar favoritos
    rpc('/api/wishlist/toggle', { property_id: propertyId })
        .then(result => {
            // Actualizar UI
            const button = document.querySelector(`[data-property-id="${propertyId}"] .btn-wishlist`);
            if (button) {
                button.classList.toggle('active');
                const icon = button.querySelector('i');
                icon.className = button.classList.contains('active') ? 'bi bi-heart-fill' : 'bi bi-heart';
            }
        });
};

window.addToCompare = function(propertyId) {
    // Lógica para agregar a comparación
    console.log('Add to compare:', propertyId);
};

window.toggleFloatingActions = function(button) {
    // Toggle del menú flotante
    const container = button.closest('.floating-actions-container');
    container.classList.toggle('active');
};

// Exportar la clase
export default PropertyCardEnhanced;
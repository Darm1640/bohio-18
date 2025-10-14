/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import { createElement } from '../utils/dom_helpers';
import { formatPrice, formatArea } from '../utils/formatters';
import { PLACEHOLDER_IMAGE } from '../utils/constants';

/**
 * BOHIO Clean Property Card Component
 * Diseño limpio y profesional siguiendo mejores prácticas UX
 * Efecto de elevación sutil, sin 3D exagerado
 */

export class PropertyCardClean {
    constructor(property, options = {}) {
        this.property = property;
        this.options = {
            imageQuality: 'medium', // low, medium, high
            showActions: true,
            enableCompare: true,
            enableWishlist: true,
            ...options
        };

        // Optimizar URL de imagen para carga más rápida
        this.imageUrl = this._optimizeImageUrl();
    }

    /**
     * Optimizar URL de imagen según calidad deseada
     * @private
     */
    _optimizeImageUrl() {
        const url = this.property.image_url || PLACEHOLDER_IMAGE;

        // Si es una imagen de Odoo, agregar parámetros de optimización
        if (url.includes('/web/image')) {
            const quality = this.options.imageQuality === 'low' ? 50 :
                           this.options.imageQuality === 'medium' ? 75 : 90;
            const width = this.options.imageQuality === 'low' ? 400 :
                         this.options.imageQuality === 'medium' ? 600 : 800;

            return `${url}?width=${width}&quality=${quality}`;
        }

        return url;
    }

    /**
     * Crear la tarjeta completa
     */
    create() {
        return createElement('div', {
            className: 'property-card-clean',
            attributes: {
                'data-property-id': this.property.id,
                'data-property-code': this.property.default_code || this.property.code
            },
            children: [
                createElement('div', {
                    className: 'card h-100 property-card-elevated',
                    children: [
                        this._createImageSection(),
                        this._createBodySection(),
                        this._createActionsBar()
                    ]
                })
            ]
        });
    }

    /**
     * Sección de imagen con zoom hover
     * @private
     */
    _createImageSection() {
        return createElement('div', {
            className: 'card-img-wrapper position-relative',
            children: [
                // Contenedor de imagen con zoom
                createElement('div', {
                    className: 'image-zoom-container',
                    children: [
                        createElement('img', {
                            className: 'card-img-top property-image',
                            attributes: {
                                src: this.imageUrl,
                                alt: this.property.name,
                                loading: 'lazy',
                                onerror: `this.src='${PLACEHOLDER_IMAGE}'`
                            }
                        })
                    ]
                }),

                // Badge de tipo de servicio
                this._createServiceBadge(),

                // Código Bohío en esquina superior derecha
                this._createCodeBadge(),

                // Botones de acción
                this._createImageActions()
            ]
        });
    }

    /**
     * Badge de tipo de servicio (Arriendo/Venta)
     * @private
     */
    _createServiceBadge() {
        const serviceType = this.property.type_service || 'Venta';
        const isRent = serviceType === 'Arriendo' || serviceType === 'rent';

        return createElement('div', {
            className: 'service-badge position-absolute',
            children: [
                createElement('span', {
                    className: `badge ${isRent ? 'bg-primary' : 'bg-danger'}`,
                    text: isRent ? 'ARRIENDO' : 'VENTA'
                })
            ]
        });
    }

    /**
     * Badge con código de propiedad
     * @private
     */
    _createCodeBadge() {
        const code = this.property.default_code || this.property.code || 'SIN CÓDIGO';

        return createElement('div', {
            className: 'code-badge position-absolute',
            children: [
                createElement('span', {
                    className: 'badge bg-dark bg-opacity-75',
                    children: [
                        createElement('small', { text: 'COD: ' }),
                        createElement('strong', { text: code })
                    ]
                })
            ]
        });
    }

    /**
     * Botones de acción sobre la imagen
     * @private
     */
    _createImageActions() {
        return createElement('div', {
            className: 'image-actions position-absolute',
            children: [
                // Favoritos
                this._createWishlistButton(),
                // Comparar
                this._createCompareButton(),
                // Compartir
                this._createShareButton()
            ]
        });
    }

    /**
     * Botón de favoritos simplificado
     * @private
     */
    _createWishlistButton() {
        const isFavorite = this.property.is_favorite || false;

        const button = createElement('button', {
            className: `btn btn-icon-clean ${isFavorite ? 'active' : ''}`,
            attributes: {
                type: 'button',
                title: 'Agregar a favoritos',
                'data-property-id': this.property.id
            },
            children: [
                createElement('i', `bi bi-heart${isFavorite ? '-fill text-danger' : ''}`)
            ]
        });

        button.addEventListener('click', (e) => {
            e.preventDefault();
            this._toggleWishlist(button);
        });

        return button;
    }

    /**
     * Toggle wishlist con RPC
     * @private
     */
    async _toggleWishlist(button) {
        try {
            const result = await rpc('/api/wishlist/toggle', {
                property_id: this.property.id
            });

            if (result.success) {
                button.classList.toggle('active');
                const icon = button.querySelector('i');
                if (icon.classList.contains('bi-heart')) {
                    icon.className = 'bi bi-heart-fill text-danger';
                } else {
                    icon.className = 'bi bi-heart';
                }
            }
        } catch (error) {
            console.error('Error toggling wishlist:', error);
        }
    }

    /**
     * Botón de comparar
     * @private
     */
    _createCompareButton() {
        return createElement('button', {
            className: 'btn btn-icon-clean',
            attributes: {
                type: 'button',
                title: 'Comparar',
                onclick: `addToCompare(${this.property.id})`
            },
            children: [
                createElement('i', 'bi bi-grid-3x3-gap')
            ]
        });
    }

    /**
     * Botón de compartir
     * @private
     */
    _createShareButton() {
        const button = createElement('button', {
            className: 'btn btn-icon-clean',
            attributes: {
                type: 'button',
                title: 'Compartir'
            },
            children: [
                createElement('i', 'bi bi-share')
            ]
        });

        button.addEventListener('click', () => this._share());
        return button;
    }

    /**
     * Compartir propiedad
     * @private
     */
    _share() {
        const url = `${window.location.origin}/property/${this.property.id}`;
        const title = this.property.name;

        if (navigator.share) {
            navigator.share({ title, url });
        } else {
            navigator.clipboard.writeText(url);
            this._showToast('Enlace copiado');
        }
    }

    /**
     * Sección del cuerpo de la tarjeta
     * @private
     */
    _createBodySection() {
        return createElement('div', {
            className: 'card-body',
            children: [
                // Título
                this._createTitle(),

                // Categoría/Tipo de propiedad
                this._createCategory(),

                // Ubicación
                this._createLocation(),

                // Características principales
                this._createMainFeatures(),

                // Precio
                this._createPrice()
            ]
        });
    }

    /**
     * Título de la propiedad
     * @private
     */
    _createTitle() {
        return createElement('h5', {
            className: 'card-title mb-1',
            text: this.property.name || 'Propiedad sin nombre',
            attributes: {
                title: this.property.name
            }
        });
    }

    /**
     * Categoría/Tipo de propiedad
     * @private
     */
    _createCategory() {
        // Obtener el tipo de propiedad desde selection field
        const propertyType = this._getPropertyTypeLabel();

        if (!propertyType) return null;

        return createElement('p', {
            className: 'property-category text-muted small mb-2',
            text: propertyType
        });
    }

    /**
     * Obtener label del tipo de propiedad
     * @private
     */
    _getPropertyTypeLabel() {
        // Mapeo de valores de selection a labels
        const typeMap = {
            'apartment': 'Apartamento',
            'house': 'Casa',
            'land': 'Lote',
            'commercial': 'Local Comercial',
            'office': 'Oficina',
            'warehouse': 'Bodega',
            'parking': 'Parqueadero',
            'room': 'Habitación',
            'studio': 'Estudio',
            'penthouse': 'Penthouse',
            'country_house': 'Casa Campestre',
            'beach_house': 'Casa de Playa'
        };

        const type = this.property.property_type || this.property.type;
        return typeMap[type] || type || null;
    }

    /**
     * Ubicación
     * @private
     */
    _createLocation() {
        const parts = [];

        // Barrio/Sector
        if (this.property.neighborhood || this.property.sector) {
            parts.push(this.property.neighborhood || this.property.sector);
        }

        // Zona/Comuna/Localidad desde region_id
        if (this.property.region_id) {
            // region_id es un array [id, name]
            if (Array.isArray(this.property.region_id)) {
                parts.push(this.property.region_id[1]);
            } else if (typeof this.property.region_id === 'string') {
                parts.push(this.property.region_id);
            }
        }

        // Ciudad
        if (this.property.city) {
            parts.push(this.property.city);
        }

        if (parts.length === 0) return null;

        return createElement('div', {
            className: 'location-info d-flex align-items-center mb-3',
            children: [
                createElement('i', 'bi bi-geo-alt text-muted me-1 small'),
                createElement('small', {
                    className: 'text-muted',
                    text: parts.join(', ')
                })
            ]
        });
    }

    /**
     * Características principales en línea
     * @private
     */
    _createMainFeatures() {
        const features = [];

        // Área
        if (this.property.area && this.property.area > 0) {
            features.push({
                icon: 'bi-rulers',
                value: `${Math.round(this.property.area)} m²`
            });
        }

        // Habitaciones
        if (this.property.bedrooms && this.property.bedrooms > 0) {
            features.push({
                icon: 'bi-door-closed',
                value: `${this.property.bedrooms}`
            });
        }

        // Baños
        if (this.property.bathrooms && this.property.bathrooms > 0) {
            features.push({
                icon: 'bi-droplet',
                value: `${this.property.bathrooms}`
            });
        }

        // Parqueaderos
        if (this.property.parking && this.property.parking > 0) {
            features.push({
                icon: 'bi-p-square',
                value: `${this.property.parking}`
            });
        }

        if (features.length === 0) return null;

        return createElement('div', {
            className: 'features-inline d-flex gap-3 mb-3',
            children: features.map(feature =>
                createElement('div', {
                    className: 'd-flex align-items-center',
                    children: [
                        createElement('i', `bi ${feature.icon} text-muted me-1`),
                        createElement('span', {
                            className: 'small',
                            text: feature.value
                        })
                    ]
                })
            )
        });
    }

    /**
     * Precio con formato correcto
     * @private
     */
    _createPrice() {
        const serviceType = this.property.type_service || 'Venta';
        const isRent = serviceType === 'Arriendo' || serviceType === 'rent';

        return createElement('div', {
            className: 'price-section mt-auto',
            children: [
                createElement('div', {
                    className: 'd-flex align-items-baseline justify-content-between',
                    children: [
                        createElement('h4', {
                            className: 'price-value mb-0 text-danger',
                            text: formatPrice(this.property.price || 0)
                        }),
                        isRent ? createElement('span', {
                            className: 'price-period text-muted',
                            text: '/mes'
                        }) : null
                    ].filter(Boolean)
                }),

                // Administración si es arriendo
                isRent && this.property.administration_fee ?
                    createElement('small', {
                        className: 'text-muted d-block',
                        text: `Admin: ${formatPrice(this.property.administration_fee)}`
                    }) : null
            ].filter(Boolean)
        });
    }

    /**
     * Barra de acciones inferior
     * @private
     */
    _createActionsBar() {
        return createElement('div', {
            className: 'card-footer bg-transparent border-top-0',
            children: [
                createElement('div', {
                    className: 'd-flex gap-2',
                    children: [
                        // Botón Ver detalles
                        createElement('a', {
                            className: 'btn btn-danger flex-fill',
                            attributes: {
                                href: `/property/${this.property.id}`
                            },
                            text: 'Ver detalles'
                        }),

                        // Botón WhatsApp
                        this._createWhatsAppButton(),

                        // Botón Mapa
                        this._createMapButton()
                    ]
                })
            ]
        });
    }

    /**
     * Botón de WhatsApp
     * @private
     */
    _createWhatsAppButton() {
        const button = createElement('button', {
            className: 'btn btn-success',
            attributes: {
                type: 'button',
                title: 'Contactar por WhatsApp'
            },
            children: [
                createElement('i', 'bi bi-whatsapp')
            ]
        });

        button.addEventListener('click', () => {
            const code = this.property.default_code || this.property.code || 'N/A';
            const message = `Hola, estoy interesado en la propiedad: ${this.property.name} (Código: ${code})`;
            const phone = '573001234567'; // Configurar número real
            window.open(`https://wa.me/${phone}?text=${encodeURIComponent(message)}`, '_blank');
        });

        return button;
    }

    /**
     * Botón de mapa
     * @private
     */
    _createMapButton() {
        const button = createElement('button', {
            className: 'btn btn-primary',
            attributes: {
                type: 'button',
                title: 'Ver en Google Maps'
            },
            children: [
                createElement('i', 'bi bi-geo-alt-fill')
            ]
        });

        button.addEventListener('click', () => {
            if (this.property.latitude && this.property.longitude) {
                window.open(`https://maps.google.com/?q=${this.property.latitude},${this.property.longitude}`, '_blank');
            } else {
                this._showToast('Ubicación no disponible');
            }
        });

        return button;
    }

    /**
     * Mostrar notificación toast
     * @private
     */
    _showToast(message) {
        // Crear contenedor si no existe
        let container = document.getElementById('toast-container');
        if (!container) {
            container = createElement('div', {
                id: 'toast-container',
                className: 'toast-container position-fixed bottom-0 end-0 p-3'
            });
            document.body.appendChild(container);
        }

        // Crear toast
        const toast = createElement('div', {
            className: 'toast',
            attributes: { role: 'alert' },
            children: [
                createElement('div', {
                    className: 'toast-body',
                    text: message
                })
            ]
        });

        container.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
        bsToast.show();

        // Limpiar después de ocultar
        toast.addEventListener('hidden.bs.toast', () => toast.remove());
    }
}

// Función global para comparar (mantener compatibilidad)
window.addToCompare = function(propertyId) {
    console.log('Add to compare:', propertyId);
    // Implementar lógica de comparación
};

export default PropertyCardClean;
/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import { createElement } from '../utils/dom_helpers';
import { formatPrice, formatArea } from '../utils/formatters';
import { PLACEHOLDER_IMAGE } from '../utils/constants';

/**
 * ============================================================================
 * BOHIO Property Card - Componente Unificado
 * ============================================================================
 * Reemplaza 3 archivos anteriores:
 * - property_card_enhanced.js (714 líneas)
 * - property_card_clean.js (612 líneas)
 * - dom/property_cards.js (373 líneas)
 *
 * Soporta 3 modos de visualización:
 * - 'simple': Card básica con información mínima
 * - 'clean': Card profesional con elevación sutil (DEFAULT)
 * - 'enhanced': Card completa con efectos 3D y botones flotantes
 */

export class PropertyCard {
    constructor(property, options = {}) {
        this.property = property;
        this.options = {
            mode: 'clean', // 'simple', 'clean', 'enhanced'
            showActions: true,
            showFloatingButtons: false,
            showWishlist: true,
            showCompare: true,
            showShare: true,
            imageQuality: 'medium', // 'low', 'medium', 'high'
            ...options
        };

        // Auto-detectar modo basado en opciones
        if (this.options.showFloatingButtons) {
            this.options.mode = 'enhanced';
        }
    }

    /**
     * Crear tarjeta según modo seleccionado
     * @returns {HTMLElement}
     */
    create() {
        switch (this.options.mode) {
            case 'simple':
                return this._createSimpleCard();
            case 'enhanced':
                return this._createEnhancedCard();
            case 'clean':
            default:
                return this._createCleanCard();
        }
    }

    // =========================================================================
    // MODO SIMPLE - Card básica
    // =========================================================================

    _createSimpleCard() {
        const col = createElement('div', { className: 'col-md-3' });

        const card = createElement('div', {
            className: 'card h-100 shadow-sm border-0 property-card-simple',
            attributes: {
                'data-property-id': this.property.id
            }
        });

        // Imagen
        card.appendChild(this._createImage());

        // Body
        const body = createElement('div', { className: 'card-body d-flex flex-column' });

        // Título
        body.appendChild(createElement('h5', {
            className: 'card-title text-truncate',
            text: this.property.name,
            attributes: { title: this.property.name }
        }));

        // Ubicación
        body.appendChild(this._createSimpleLocation());

        // Características
        const features = this._createFeatures();
        if (features) body.appendChild(features);

        // Precio
        body.appendChild(this._createSimplePrice());

        // Botón
        body.appendChild(createElement('a', {
            className: 'btn btn-outline-danger w-100 mt-auto',
            attributes: { href: `/property/${this.property.id}` },
            text: 'Ver detalles'
        }));

        card.appendChild(body);
        col.appendChild(card);

        return col;
    }

    _createSimpleLocation() {
        const location = createElement('p', { className: 'text-muted small mb-2' });
        location.appendChild(createElement('i', { className: 'bi bi-geo-alt-fill me-1' }));
        location.appendChild(document.createTextNode(
            this._formatLocation()
        ));
        return location;
    }

    _createSimplePrice() {
        const priceDiv = createElement('div', { className: 'mb-2' });
        priceDiv.appendChild(createElement('small', {
            className: 'text-muted',
            text: this._getPriceLabel()
        }));
        priceDiv.appendChild(createElement('h4', {
            className: 'text-danger mb-0',
            text: formatPrice(this.property.price)
        }));
        return priceDiv;
    }

    // =========================================================================
    // MODO CLEAN - Card profesional (DEFAULT)
    // =========================================================================

    _createCleanCard() {
        const col = createElement('div', { className: 'col-md-6 col-lg-4 col-xl-3 mb-4' });

        const card = createElement('div', {
            className: 'card h-100 property-card-clean shadow-hover border-0',
            attributes: {
                'data-property-id': this.property.id,
                'data-property-code': this.property.code || this.property.default_code
            }
        });

        // Imagen con overlays
        card.appendChild(this._createImageSection());

        // Body
        card.appendChild(this._createBodySection());

        // Footer con botones
        card.appendChild(this._createFooterSection());

        col.appendChild(card);
        return col;
    }

    _createImageSection() {
        const section = createElement('div', { className: 'card-img-wrapper position-relative' });

        // Contenedor de imagen con zoom effect
        const imageContainer = createElement('div', { className: 'image-zoom-container' });
        imageContainer.appendChild(this._createImage());
        section.appendChild(imageContainer);

        // Badge de servicio (Arriendo/Venta)
        section.appendChild(this._createServiceBadge());

        // Código Bohío
        const code = this.property.default_code || this.property.code;
        if (code) {
            section.appendChild(this._createCodeBadge(code));
        }

        // Botones de acción sobre la imagen
        if (this.options.showActions) {
            section.appendChild(this._createImageActions());
        }

        return section;
    }

    _createServiceBadge() {
        const badge = createElement('div', {
            className: 'position-absolute top-0 start-0 m-2'
        });

        const isRent = this._isRent();
        badge.appendChild(createElement('span', {
            className: `badge ${isRent ? 'bg-primary' : 'bg-danger'}`,
            text: isRent ? 'ARRIENDO' : 'VENTA'
        }));

        return badge;
    }

    _createCodeBadge(code) {
        const badge = createElement('div', {
            className: 'position-absolute top-0 end-0 m-2'
        });

        const span = createElement('span', { className: 'badge bg-dark bg-opacity-75' });
        span.appendChild(createElement('small', { text: 'COD: ' }));
        span.appendChild(createElement('strong', { text: code }));
        badge.appendChild(span);

        return badge;
    }

    _createImageActions() {
        const actions = createElement('div', {
            className: 'image-actions position-absolute bottom-0 end-0 m-2 d-flex gap-2'
        });

        if (this.options.showWishlist) {
            actions.appendChild(this._createActionButton('heart', 'Favorito', (e) => {
                e.preventDefault();
                this._toggleWishlist(e.currentTarget);
            }));
        }

        if (this.options.showCompare) {
            actions.appendChild(this._createActionButton('grid-3x3-gap', 'Comparar', (e) => {
                e.preventDefault();
                this._addToCompare();
            }));
        }

        if (this.options.showShare) {
            actions.appendChild(this._createActionButton('share', 'Compartir', (e) => {
                e.preventDefault();
                this._share();
            }));
        }

        return actions;
    }

    _createActionButton(icon, title, onClick) {
        const button = createElement('button', {
            className: 'btn btn-sm btn-light shadow-sm btn-icon-clean',
            attributes: {
                type: 'button',
                title
            }
        });

        button.appendChild(createElement('i', { className: `bi bi-${icon}` }));
        button.addEventListener('click', onClick);

        return button;
    }

    _createBodySection() {
        const body = createElement('div', { className: 'card-body' });

        // Título
        body.appendChild(createElement('h5', {
            className: 'card-title mb-2',
            text: this.property.name,
            attributes: { title: this.property.name }
        }));

        // Tipo de propiedad
        const propertyType = this._getPropertyTypeLabel();
        if (propertyType) {
            body.appendChild(createElement('p', {
                className: 'text-muted small mb-2',
                text: propertyType
            }));
        }

        // Ubicación
        body.appendChild(this._createDetailedLocation());

        // Características
        const features = this._createFeatures();
        if (features) body.appendChild(features);

        // Precio
        body.appendChild(this._createPriceSection());

        return body;
    }

    _createDetailedLocation() {
        const locationDiv = createElement('div', {
            className: 'd-flex align-items-center mb-3'
        });

        locationDiv.appendChild(createElement('i', {
            className: 'bi bi-geo-alt text-muted me-1 small'
        }));

        locationDiv.appendChild(createElement('small', {
            className: 'text-muted',
            text: this._formatLocation()
        }));

        return locationDiv;
    }

    _createPriceSection() {
        const container = createElement('div', { className: 'price-section mt-auto mb-3' });

        const priceDiv = createElement('div', {
            className: 'd-flex align-items-baseline justify-content-between'
        });

        priceDiv.appendChild(createElement('h4', {
            className: 'price-value mb-0 text-danger',
            text: formatPrice(this.property.price || 0)
        }));

        const isRent = this._isRent();
        if (isRent) {
            priceDiv.appendChild(createElement('span', {
                className: 'price-period text-muted',
                text: '/mes'
            }));
        }

        container.appendChild(priceDiv);

        // Administración si aplica
        if (isRent && this.property.administration_fee) {
            container.appendChild(createElement('small', {
                className: 'text-muted d-block',
                text: `Admin: ${formatPrice(this.property.administration_fee)}`
            }));
        }

        return container;
    }

    _createFooterSection() {
        const footer = createElement('div', {
            className: 'card-footer bg-transparent border-top-0 pt-0'
        });

        const buttonsDiv = createElement('div', { className: 'd-flex gap-2' });

        // Botón Ver detalles
        buttonsDiv.appendChild(createElement('a', {
            className: 'btn btn-danger flex-fill',
            attributes: { href: `/property/${this.property.id}` },
            text: 'Ver detalles'
        }));

        // Botón WhatsApp
        const whatsappBtn = createElement('button', {
            className: 'btn btn-success',
            attributes: {
                type: 'button',
                title: 'WhatsApp'
            }
        });
        whatsappBtn.appendChild(createElement('i', { className: 'bi bi-whatsapp' }));
        whatsappBtn.addEventListener('click', () => this._contactWhatsApp());
        buttonsDiv.appendChild(whatsappBtn);

        // Botón Mapa
        if (this.property.latitude && this.property.longitude) {
            const mapBtn = createElement('button', {
                className: 'btn btn-primary',
                attributes: {
                    type: 'button',
                    title: 'Ver en mapa'
                }
            });
            mapBtn.appendChild(createElement('i', { className: 'bi bi-geo-alt-fill' }));
            mapBtn.addEventListener('click', () => this._openMap());
            buttonsDiv.appendChild(mapBtn);
        }

        footer.appendChild(buttonsDiv);
        return footer;
    }

    // =========================================================================
    // MODO ENHANCED - Card con efectos 3D y botones flotantes
    // =========================================================================

    _createEnhancedCard() {
        // Crear base clean
        const cleanCard = this._createCleanCard();
        const card = cleanCard.querySelector('.card');

        // Agregar clases de efectos 3D
        card.classList.add('property-card-3d', 'glass-effect');

        // Agregar botones flotantes si están habilitados
        if (this.options.showFloatingButtons) {
            card.appendChild(this._createFloatingButtons());
        }

        return cleanCard;
    }

    _createFloatingButtons() {
        const container = createElement('div', { className: 'floating-actions-container' });

        // Botón principal
        const mainBtn = createElement('button', {
            className: 'btn-floating-main btn-glass-3d',
            attributes: {
                type: 'button',
                'aria-label': 'Más opciones'
            }
        });
        mainBtn.appendChild(createElement('i', { className: 'bi bi-three-dots-vertical' }));
        mainBtn.addEventListener('click', (e) => {
            e.currentTarget.closest('.floating-actions-container').classList.toggle('active');
        });
        container.appendChild(mainBtn);

        // Acciones
        const actions = createElement('div', { className: 'floating-actions' });

        const buttons = [
            { icon: 'whatsapp', text: 'WhatsApp', color: 'success', action: () => this._contactWhatsApp() },
            { icon: 'geo-alt-fill', text: 'Mapa', color: 'primary', action: () => this._openMap() },
            { icon: 'share-fill', text: 'Compartir', color: 'info', action: () => this._share() },
            { icon: 'calendar-check', text: 'Agendar', color: 'warning', action: () => this._schedule() },
            { icon: 'flag-fill', text: 'Reportar', color: 'danger', action: () => this._report() }
        ];

        buttons.forEach(btn => {
            const floatingBtn = createElement('button', {
                className: `btn-floating btn-glass-3d btn-${btn.color}`,
                attributes: {
                    type: 'button',
                    title: btn.text,
                    'data-bs-toggle': 'tooltip',
                    'data-bs-placement': 'left'
                }
            });
            floatingBtn.appendChild(createElement('i', { className: `bi bi-${btn.icon}` }));
            floatingBtn.addEventListener('click', btn.action);
            actions.appendChild(floatingBtn);
        });

        container.appendChild(actions);
        return container;
    }

    // =========================================================================
    // COMPONENTES COMPARTIDOS
    // =========================================================================

    _createImage() {
        const imageUrl = this._getOptimizedImageUrl();

        return createElement('img', {
            className: 'card-img-top property-image',
            attributes: {
                src: imageUrl,
                alt: this.property.name,
                loading: 'lazy',
                onerror: `this.src='${PLACEHOLDER_IMAGE}'`,
                style: 'height: 200px; object-fit: cover;'
            }
        });
    }

    _getOptimizedImageUrl() {
        const url = this.property.image_url || PLACEHOLDER_IMAGE;

        if (url.includes('/web/image')) {
            const quality = this.options.imageQuality === 'low' ? 50 :
                           this.options.imageQuality === 'medium' ? 75 : 90;
            const width = this.options.imageQuality === 'low' ? 400 :
                         this.options.imageQuality === 'medium' ? 600 : 800;

            return `${url}?width=${width}&quality=${quality}`;
        }

        return url;
    }

    _createFeatures() {
        const features = [];

        if (this.property.area > 0 || this.property.area_constructed > 0 || this.property.area_total > 0) {
            const area = this.property.area || this.property.area_constructed || this.property.area_total;
            features.push({ icon: 'bi-rulers', value: `${Math.round(area)} m²` });
        }

        if (this.property.bedrooms > 0) {
            features.push({ icon: 'bi-door-closed', value: `${this.property.bedrooms}` });
        }

        if (this.property.bathrooms > 0) {
            features.push({ icon: 'bi-droplet', value: `${this.property.bathrooms}` });
        }

        if (this.property.parking > 0 || this.property.parking_spaces > 0) {
            const parking = this.property.parking || this.property.parking_spaces;
            features.push({ icon: 'bi-p-square', value: `${parking}` });
        }

        if (features.length === 0) return null;

        const container = createElement('div', {
            className: 'd-flex justify-content-between mb-3 property-features'
        });

        features.forEach(feature => {
            const div = createElement('div', { className: 'text-center' });
            div.appendChild(createElement('i', {
                className: `bi ${feature.icon} d-block mb-1 text-muted`
            }));
            div.appendChild(createElement('small', {
                className: 'text-muted',
                text: feature.value
            }));
            container.appendChild(div);
        });

        return container;
    }

    // =========================================================================
    // MÉTODOS DE ACCIÓN
    // =========================================================================

    async _toggleWishlist(button) {
        try {
            const result = await rpc('/property/wishlist/toggle', {
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
                this._showToast(result.in_wishlist ? 'Agregado a favoritos' : 'Eliminado de favoritos');
            }
        } catch (error) {
            console.error('Error toggling wishlist:', error);
            this._showToast('Error al actualizar favoritos', 'danger');
        }
    }

    _addToCompare() {
        // Disparar evento personalizado para que el widget de comparación lo maneje
        const event = new CustomEvent('property:addToCompare', {
            detail: { property: this.property }
        });
        window.dispatchEvent(event);
        this._showToast('Agregado a comparación');
    }

    _share() {
        const url = `${window.location.origin}/property/${this.property.id}`;
        const title = this.property.name;

        if (navigator.share) {
            navigator.share({ title, url }).catch(err => {
                console.log('Share cancelled or error:', err);
            });
        } else {
            navigator.clipboard.writeText(url).then(() => {
                this._showToast('Enlace copiado al portapapeles');
            }).catch(() => {
                this._showToast('No se pudo copiar el enlace', 'danger');
            });
        }
    }

    _contactWhatsApp() {
        const code = this.property.default_code || this.property.code || 'N/A';
        const message = `Hola, estoy interesado en la propiedad: ${this.property.name} (Código: ${code})`;
        const phone = '573001234567'; // TODO: Configurar desde constantes
        window.open(`https://wa.me/${phone}?text=${encodeURIComponent(message)}`, '_blank');
    }

    _openMap() {
        if (this.property.latitude && this.property.longitude) {
            window.open(
                `https://maps.google.com/?q=${this.property.latitude},${this.property.longitude}`,
                '_blank'
            );
        } else {
            this._showToast('Ubicación no disponible', 'warning');
        }
    }

    _schedule() {
        // Disparar evento para que el widget de agendamiento lo maneje
        const event = new CustomEvent('property:scheduleAppointment', {
            detail: { property: this.property }
        });
        window.dispatchEvent(event);
    }

    _report() {
        // Disparar evento para que el widget de reportes lo maneje
        const event = new CustomEvent('property:report', {
            detail: { property: this.property }
        });
        window.dispatchEvent(event);
    }

    _showToast(message, type = 'success') {
        // Crear contenedor si no existe
        let container = document.getElementById('toast-container');
        if (!container) {
            container = createElement('div', {
                id: 'toast-container',
                className: 'toast-container position-fixed bottom-0 end-0 p-3',
                attributes: { style: 'z-index: 9999;' }
            });
            document.body.appendChild(container);
        }

        // Crear toast
        const toast = createElement('div', {
            className: `toast align-items-center text-white bg-${type} border-0`,
            attributes: {
                role: 'alert',
                'aria-live': 'assertive',
                'aria-atomic': 'true'
            }
        });

        const toastBody = createElement('div', { className: 'd-flex' });
        toastBody.appendChild(createElement('div', {
            className: 'toast-body',
            text: message
        }));

        const closeBtn = createElement('button', {
            className: 'btn-close btn-close-white me-2 m-auto',
            attributes: {
                type: 'button',
                'data-bs-dismiss': 'toast',
                'aria-label': 'Close'
            }
        });
        toastBody.appendChild(closeBtn);

        toast.appendChild(toastBody);
        container.appendChild(toast);

        // Mostrar toast
        if (typeof bootstrap !== 'undefined') {
            const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
            bsToast.show();

            // Limpiar después de ocultar
            toast.addEventListener('hidden.bs.toast', () => toast.remove());
        } else {
            // Fallback si Bootstrap no está disponible
            setTimeout(() => toast.remove(), 3000);
        }
    }

    // =========================================================================
    // HELPERS
    // =========================================================================

    _isRent() {
        const typeService = this.property.type_service;
        return typeService === 'rent' || typeService === 'Arriendo' || typeService === 'arriendo';
    }

    _getPriceLabel() {
        return this._isRent() ? 'Arriendo/mes' : 'Venta';
    }

    _formatLocation() {
        const parts = [];

        // Barrio/Sector
        if (this.property.neighborhood || this.property.sector) {
            parts.push(this.property.neighborhood || this.property.sector);
        }

        // Zona/Comuna desde region_id
        if (this.property.region_id) {
            if (Array.isArray(this.property.region_id)) {
                parts.push(this.property.region_id[1]); // [id, name]
            } else if (typeof this.property.region_id === 'string') {
                parts.push(this.property.region_id);
            }
        }

        // Ciudad
        if (this.property.city) {
            parts.push(this.property.city);
        }

        // Estado/Departamento
        if (this.property.state && !parts.includes(this.property.state)) {
            parts.push(this.property.state);
        }

        return parts.length > 0 ? parts.join(', ') : 'Ubicación no especificada';
    }

    _getPropertyTypeLabel() {
        const typeMap = {
            'apartment': 'Apartamento',
            'house': 'Casa',
            'land': 'Lote',
            'lot': 'Lote',
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
        return typeMap[type] || null;
    }
}

// =============================================================================
// FUNCIONES HELPER PARA CREAR CARDS RÁPIDAMENTE
// =============================================================================

/**
 * Crea una card simple
 */
export function createSimpleCard(property) {
    return new PropertyCard(property, { mode: 'simple' }).create();
}

/**
 * Crea una card clean (default)
 */
export function createCleanCard(property) {
    return new PropertyCard(property, { mode: 'clean' }).create();
}

/**
 * Crea una card enhanced con botones flotantes
 */
export function createEnhancedCard(property) {
    return new PropertyCard(property, {
        mode: 'enhanced',
        showFloatingButtons: true
    }).create();
}

/**
 * Alias: Crear card básica para DOM helpers (compatibilidad)
 */
export function createPropertyCard(property) {
    return new PropertyCard(property, { mode: 'clean' }).create();
}

/**
 * Crear estado vacío cuando no hay propiedades
 */
export function createEmptyState(options = {}) {
    const col = createElement('div', { className: 'col-12 text-center py-5' });

    const icon = createElement('i', {
        className: `bi ${options.icon || 'bi-house-fill'} fa-3x text-muted mb-3`
    });
    col.appendChild(icon);

    const message = createElement('p', {
        className: 'text-muted',
        text: options.message || 'No hay propiedades disponibles'
    });
    col.appendChild(message);

    return col;
}

/**
 * Crear popup de mapa
 */
export function createMapPopup(property) {
    const container = createElement('div');
    container.style.minWidth = '280px';
    container.style.maxWidth = '300px';

    // Imagen
    const img = document.createElement('img');
    img.src = property.image_url || PLACEHOLDER_IMAGE;
    img.alt = property.name;
    img.style.cssText = 'width: 100%; height: 160px; object-fit: cover; border-radius: 8px; margin-bottom: 12px;';
    img.onerror = function() {
        this.src = PLACEHOLDER_IMAGE;
    };
    container.appendChild(img);

    // Título
    const h6 = createElement('h6', {
        className: 'fw-bold mb-2',
        text: property.name
    });
    h6.style.fontSize = '14px';
    container.appendChild(h6);

    // Ubicación
    const locationP = createElement('p', { className: 'small mb-2 text-muted' });
    locationP.appendChild(createElement('i', { className: 'bi bi-geo-alt-fill text-danger me-1' }));
    const neighborhood = property.neighborhood ? `${property.neighborhood}, ` : '';
    const location = `${neighborhood}${property.city || property.state || ''}`;
    locationP.appendChild(document.createTextNode(location));
    container.appendChild(locationP);

    // Precio
    const priceContainer = createElement('div', { className: 'mb-2' });
    const isRent = property.type_service === 'rent' || property.type_service === 'Arriendo';
    const priceLabel = createElement('small', {
        className: 'text-muted d-block',
        text: isRent ? 'Arriendo/mes' : 'Venta'
    });
    priceContainer.appendChild(priceLabel);

    const price = createElement('p', {
        className: 'mb-2 text-danger fw-bold',
        text: formatPrice(property.price)
    });
    price.style.fontSize = '16px';
    priceContainer.appendChild(price);
    container.appendChild(priceContainer);

    // Botón
    const link = createElement('a', {
        className: 'btn btn-sm btn-danger w-100',
        attributes: {
            href: `/property/${property.id}`,
            style: 'background: #E31E24; border: none;'
        }
    });
    link.appendChild(createElement('i', { className: 'bi bi-eye me-1' }));
    link.appendChild(document.createTextNode('Ver detalles'));
    container.appendChild(link);

    return container;
}

// Exportar por defecto
export default PropertyCard;

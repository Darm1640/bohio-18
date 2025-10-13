/** @odoo-module **/

/**
 * ============================================================================
 * BOHIO PROPERTY WISHLIST (FAVORITOS)
 * ============================================================================
 * Sistema de favoritos para propiedades inmobiliarias.
 * Compatible con product.wishlist de Odoo.
 *
 * Funcionalidades:
 * - Toggle (agregar/remover) favoritos
 * - Actualización de contador en tiempo real
 * - Animaciones suaves
 * - Persistencia por sesión/usuario
 * - Notificaciones visuales
 */

// Estado global del wishlist
let wishlistState = {
    count: 0,
    properties: new Set(),  // Set de IDs de propiedades en wishlist
    loading: false
};

/**
 * Inicializar wishlist al cargar la página
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('❤️ Property Wishlist JS cargado');

    // Cargar estado inicial del wishlist
    initializeWishlist();

    // Verificar si la propiedad actual está en wishlist (si estamos en página de detalle)
    const wishlistBtn = document.getElementById('wishlistBtn');
    if (wishlistBtn) {
        const propertyId = parseInt(wishlistBtn.dataset.propertyId);
        if (propertyId) {
            checkPropertyWishlistStatus(propertyId);
        }
    }

    // Actualizar todos los botones de wishlist en tarjetas (si hay)
    updateAllWishlistButtons();
});

/**
 * Inicializar el wishlist (cargar contador)
 */
async function initializeWishlist() {
    try {
        const response = await fetch('/property/wishlist/count', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: {}
            })
        });

        const data = await response.json();

        if (data.result) {
            wishlistState.count = data.result.count || 0;
            updateWishlistCounters();
            console.log(`✅ Wishlist inicializado: ${wishlistState.count} favoritos`);
        }
    } catch (error) {
        console.error('❌ Error inicializando wishlist:', error);
    }
}

/**
 * Toggle wishlist (agregar o remover propiedad)
 */
window.togglePropertyWishlist = async function(button) {
    // Prevenir múltiples clicks
    if (wishlistState.loading) {
        console.log('⏳ Operación en progreso...');
        return;
    }

    const propertyId = parseInt(button.dataset.propertyId);

    if (!propertyId) {
        console.error('❌ ID de propiedad no encontrado');
        return;
    }

    wishlistState.loading = true;

    // Animación de loading
    const icon = button.querySelector('.wishlist-icon');
    const originalClass = icon.className;
    icon.className = 'bi bi-hourglass-split';
    button.style.pointerEvents = 'none';

    try {
        const response = await fetch('/property/wishlist/toggle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: {
                    property_id: propertyId
                }
            })
        });

        const data = await response.json();

        if (data.result && data.result.success) {
            const result = data.result;

            // Actualizar estado
            wishlistState.count = result.new_count;

            if (result.is_in_wishlist) {
                wishlistState.properties.add(propertyId);
            } else {
                wishlistState.properties.delete(propertyId);
            }

            // Actualizar UI del botón
            updateWishlistButton(button, result.is_in_wishlist);

            // Actualizar contadores globales
            updateWishlistCounters();

            // Mostrar notificación
            showWishlistNotification(result.message, result.action === 'added' ? 'success' : 'info');

            console.log(`✅ Wishlist actualizado: ${result.action} - Total: ${result.new_count}`);

        } else {
            // Error en la operación
            icon.className = originalClass;
            showWishlistNotification(data.result.message || 'Error al actualizar favoritos', 'error');
            console.error('❌ Error en toggle wishlist:', data.result.message);
        }

    } catch (error) {
        // Error de red o servidor
        icon.className = originalClass;
        showWishlistNotification('Error de conexión. Intenta nuevamente.', 'error');
        console.error('❌ Error en petición de wishlist:', error);
    } finally {
        wishlistState.loading = false;
        button.style.pointerEvents = 'auto';
    }
};

/**
 * Verificar estado de una propiedad en el wishlist
 */
async function checkPropertyWishlistStatus(propertyId) {
    try {
        const response = await fetch('/property/wishlist/check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: {
                    property_id: propertyId
                }
            })
        });

        const data = await response.json();

        if (data.result) {
            const isInWishlist = data.result.is_in_wishlist;
            wishlistState.count = data.result.total_count;

            if (isInWishlist) {
                wishlistState.properties.add(propertyId);
            }

            // Actualizar botón
            const button = document.querySelector(`[data-property-id="${propertyId}"]`);
            if (button) {
                updateWishlistButton(button, isInWishlist);
            }

            updateWishlistCounters();
        }

    } catch (error) {
        console.error('❌ Error verificando estado de wishlist:', error);
    }
}

/**
 * Actualizar apariencia de un botón de wishlist
 */
function updateWishlistButton(button, isInWishlist) {
    const icon = button.querySelector('.wishlist-icon');

    if (isInWishlist) {
        // Está en favoritos - corazón lleno rojo
        icon.className = 'bi bi-heart-fill wishlist-icon text-danger';
        button.classList.add('is-favorite');
        button.title = 'Remover de favoritos';

        // Animación de "pop"
        button.style.transform = 'scale(1.2)';
        setTimeout(() => {
            button.style.transform = 'scale(1)';
        }, 200);

    } else {
        // No está en favoritos - corazón vacío
        icon.className = 'bi bi-heart wishlist-icon';
        button.classList.remove('is-favorite');
        button.title = 'Agregar a favoritos';

        // Animación de "shrink"
        button.style.transform = 'scale(0.9)';
        setTimeout(() => {
            button.style.transform = 'scale(1)';
        }, 200);
    }
}

/**
 * Actualizar todos los contadores de wishlist en la página
 */
function updateWishlistCounters() {
    // Actualizar badges/contadores
    const counters = document.querySelectorAll('.wishlist-counter, #wishlist_count, [data-wishlist-count]');

    counters.forEach(counter => {
        counter.textContent = wishlistState.count;

        // Mostrar/ocultar según haya items
        if (wishlistState.count > 0) {
            counter.style.display = '';
            counter.classList.add('has-items');
        } else {
            counter.classList.remove('has-items');
        }
    });
}

/**
 * Actualizar todos los botones de wishlist en tarjetas
 */
function updateAllWishlistButtons() {
    const buttons = document.querySelectorAll('.wishlist-btn[data-property-id]');

    buttons.forEach(button => {
        const propertyId = parseInt(button.dataset.propertyId);
        if (propertyId && wishlistState.properties.has(propertyId)) {
            updateWishlistButton(button, true);
        }
    });
}

/**
 * Mostrar notificación de wishlist
 */
function showWishlistNotification(message, type = 'success') {
    // Crear notificación
    const notification = document.createElement('div');
    notification.className = 'wishlist-notification';

    // Estilo según tipo
    let bgColor = '#25D366';  // Verde success
    let icon = 'bi-check-circle';

    if (type === 'error') {
        bgColor = '#E31E24';  // Rojo error
        icon = 'bi-exclamation-circle';
    } else if (type === 'info') {
        bgColor = '#0d6efd';  // Azul info
        icon = 'bi-info-circle';
    }

    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: ${bgColor};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 9999;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 10px;
        animation: slideInRight 0.3s ease-out;
        max-width: 300px;
    `;

    notification.innerHTML = `
        <i class="bi ${icon}" style="font-size: 20px;"></i>
        <span>${message}</span>
    `;

    document.body.appendChild(notification);

    // Remover después de 3 segundos
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => {
            if (notification.parentNode) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

/**
 * Obtener lista completa de propiedades en wishlist
 */
window.getWishlistProperties = async function() {
    try {
        const response = await fetch('/property/wishlist/list', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: {}
            })
        });

        const data = await response.json();

        if (data.result) {
            console.log('📋 Propiedades en wishlist:', data.result.properties);
            return data.result.properties;
        }

        return [];

    } catch (error) {
        console.error('❌ Error obteniendo lista de wishlist:', error);
        return [];
    }
};

/**
 * Agregar animaciones CSS dinámicamente
 */
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    /* Estilos del botón de wishlist */
    .wishlist-btn {
        position: relative;
        overflow: hidden;
    }

    .wishlist-btn.is-favorite {
        background: #fff5f5 !important;
    }

    .wishlist-btn:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(227, 30, 36, 0.3) !important;
    }

    .wishlist-btn:active {
        transform: scale(0.95);
    }

    .wishlist-icon {
        font-size: 18px;
    }

    /* Contador de wishlist */
    .wishlist-counter {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 20px;
        height: 20px;
        background: #E31E24;
        color: white;
        border-radius: 10px;
        font-size: 11px;
        font-weight: bold;
        padding: 0 6px;
    }

    .wishlist-counter.has-items {
        animation: pulse 0.5s ease;
    }

    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.2);
        }
    }
`;
document.head.appendChild(style);

console.log('✅ Property Wishlist JS completamente cargado');

export default {
    togglePropertyWishlist: window.togglePropertyWishlist,
    getWishlistProperties: window.getWishlistProperties,
    checkPropertyWishlistStatus,
    wishlistState
};

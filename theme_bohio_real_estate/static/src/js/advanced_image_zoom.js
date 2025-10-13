/** @odoo-module **/

/**
 * ============================================================================
 * BOHIO ADVANCED IMAGE ZOOM - Bootstrap 5.3.3
 * ============================================================================
 * Sistema moderno de zoom de imágenes con todas las funcionalidades:
 * - Zoom in/out con rueda del mouse
 * - Pan (arrastrar imagen)
 * - Navegación con teclado
 * - Gestos táctiles (pinch zoom)
 * - Miniaturas interactivas
 * - Transiciones suaves
 * - Fullscreen real
 * - Contador de imágenes
 * - Modo presentación
 */

class AdvancedImageZoom {
    constructor() {
        this.currentIndex = 0;
        this.images = [];
        this.modal = null;
        this.zoomLevel = 1;
        this.minZoom = 1;
        this.maxZoom = 4;
        this.isPanning = false;
        this.startX = 0;
        this.startY = 0;
        this.translateX = 0;
        this.translateY = 0;

        // Touch gestures
        this.touchStartDistance = 0;
        this.initialZoom = 1;

        // Presentación
        this.isPresentationMode = false;
        this.presentationInterval = null;
        this.presentationSpeed = 3000; // 3 segundos

        this.init();
    }

    /**
     * Inicializar el sistema de zoom
     */
    init() {
        console.log('🔍 Advanced Image Zoom inicializando...');

        // Recolectar imágenes del carrusel
        this.collectImages();

        // Setup modal
        this.setupModal();

        // Event listeners
        this.setupEventListeners();

        console.log('✅ Advanced Image Zoom listo -', this.images.length, 'imágenes');
    }

    /**
     * Recolectar todas las imágenes válidas
     */
    collectImages() {
        const carousel = document.getElementById('propertyImageCarousel');
        if (!carousel) return;

        const items = carousel.querySelectorAll('.carousel-item');
        this.images = [];

        // ✅ LIMITAR A 10 IMÁGENES MÁXIMO para evitar ERR_INSUFFICIENT_RESOURCES
        const MAX_IMAGES = 10;

        items.forEach((item, index) => {
            // Detener si ya tenemos suficientes imágenes
            if (this.images.length >= MAX_IMAGES) return;

            const img = item.querySelector('img');
            if (img && img.src && !img.src.includes('banner1.jpg')) {
                this.images.push({
                    src: img.src,
                    alt: img.alt || `Imagen ${index + 1}`,
                    index: index
                });
            }
        });

        console.log(`✅ Colectadas ${this.images.length} imágenes (máximo: ${MAX_IMAGES})`);
    }

    /**
     * Setup del modal de zoom
     */
    setupModal() {
        const modalEl = document.getElementById('imageZoomModal');
        if (!modalEl) {
            console.error('❌ Modal imageZoomModal no encontrado');
            return;
        }

        // Crear instancia de Bootstrap 5.3.3 Modal
        this.modal = new bootstrap.Modal(modalEl, {
            backdrop: 'static',
            keyboard: false // Manejamos nosotros el teclado
        });

        // Event listeners del modal
        modalEl.addEventListener('shown.bs.modal', () => this.onModalShown());
        modalEl.addEventListener('hidden.bs.modal', () => this.onModalHidden());
    }

    /**
     * Setup de event listeners globales
     */
    setupEventListeners() {
        // Teclado
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));

        // Rueda del mouse para zoom
        const zoomImage = document.getElementById('zoomImage');
        if (zoomImage) {
            zoomImage.addEventListener('wheel', (e) => this.handleWheel(e), { passive: false });

            // Pan (arrastrar)
            zoomImage.addEventListener('mousedown', (e) => this.handleMouseDown(e));
            zoomImage.addEventListener('mousemove', (e) => this.handleMouseMove(e));
            zoomImage.addEventListener('mouseup', () => this.handleMouseUp());
            zoomImage.addEventListener('mouseleave', () => this.handleMouseUp());

            // Touch gestures
            zoomImage.addEventListener('touchstart', (e) => this.handleTouchStart(e));
            zoomImage.addEventListener('touchmove', (e) => this.handleTouchMove(e));
            zoomImage.addEventListener('touchend', () => this.handleTouchEnd());
        }
    }

    /**
     * Abrir modal en un índice específico
     */
    open(index = 0) {
        if (this.images.length === 0) {
            console.warn('⚠️ No hay imágenes para mostrar');
            return;
        }

        this.currentIndex = Math.max(0, Math.min(index, this.images.length - 1));
        this.resetZoom();
        this.updateImage();
        this.updateThumbnails();
        this.modal.show();

        console.log('🔍 Zoom abierto -', 'Imagen', this.currentIndex + 1, 'de', this.images.length);
    }

    /**
     * Cerrar modal
     */
    close() {
        this.stopPresentation();
        this.modal.hide();
    }

    /**
     * Cuando el modal se muestra
     */
    onModalShown() {
        // Forzar actualización de la imagen
        this.updateImage();
    }

    /**
     * Cuando el modal se oculta
     */
    onModalHidden() {
        this.stopPresentation();
        this.resetZoom();
    }

    /**
     * Actualizar imagen principal
     */
    updateImage() {
        const img = document.getElementById('zoomImage');
        const counter = document.getElementById('zoomImageIndex');
        const total = document.getElementById('zoomTotalImages');

        if (!img || this.currentIndex >= this.images.length) return;

        const imageData = this.images[this.currentIndex];

        // Aplicar transición suave
        img.style.opacity = '0.5';
        img.style.filter = 'blur(10px)';

        // Precargar imagen
        const tempImg = new Image();
        tempImg.onload = () => {
            img.src = tempImg.src;
            img.alt = imageData.alt;

            // Animación de entrada
            setTimeout(() => {
                img.style.opacity = '1';
                img.style.filter = 'none';
            }, 50);
        };
        tempImg.onerror = () => {
            console.error('❌ Error cargando imagen', this.currentIndex + 1);
            img.style.opacity = '0.7';
            img.style.filter = 'grayscale(100%)';
        };
        tempImg.src = imageData.src;

        // Actualizar contador
        if (counter) counter.textContent = this.currentIndex + 1;
        if (total) total.textContent = this.images.length;

        // Actualizar botones de navegación
        this.updateNavigationButtons();

        // Actualizar miniaturas
        this.updateActiveThumbnail();
    }

    /**
     * Navegación (anterior/siguiente)
     */
    navigate(direction) {
        const newIndex = this.currentIndex + direction;

        if (newIndex < 0 || newIndex >= this.images.length) {
            // Efecto de rebote si está en el límite
            this.bounceEffect();
            return;
        }

        this.currentIndex = newIndex;
        this.resetZoom();
        this.updateImage();
    }

    /**
     * Ir a imagen específica
     */
    goToIndex(index) {
        if (index < 0 || index >= this.images.length) return;

        this.currentIndex = index;
        this.resetZoom();
        this.updateImage();
    }

    /**
     * Zoom In
     */
    zoomIn() {
        this.setZoom(this.zoomLevel * 1.2);
    }

    /**
     * Zoom Out
     */
    zoomOut() {
        this.setZoom(this.zoomLevel / 1.2);
    }

    /**
     * Establecer nivel de zoom
     */
    setZoom(newZoom) {
        const img = document.getElementById('zoomImage');
        if (!img) return;

        this.zoomLevel = Math.max(this.minZoom, Math.min(newZoom, this.maxZoom));

        img.style.transform = `scale(${this.zoomLevel}) translate(${this.translateX}px, ${this.translateY}px)`;
        img.style.cursor = this.zoomLevel > 1 ? 'move' : 'zoom-in';

        // Actualizar indicador de zoom
        this.updateZoomIndicator();
    }

    /**
     * Resetear zoom
     */
    resetZoom() {
        this.zoomLevel = 1;
        this.translateX = 0;
        this.translateY = 0;
        this.setZoom(1);
    }

    /**
     * Handle rueda del mouse (zoom)
     */
    handleWheel(e) {
        if (!this.modal._isShown) return;

        e.preventDefault();

        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        this.setZoom(this.zoomLevel * delta);
    }

    /**
     * Handle mouse down (inicio de pan)
     */
    handleMouseDown(e) {
        if (this.zoomLevel <= 1) return;

        this.isPanning = true;
        this.startX = e.clientX - this.translateX;
        this.startY = e.clientY - this.translateY;

        const img = document.getElementById('zoomImage');
        if (img) img.style.cursor = 'grabbing';
    }

    /**
     * Handle mouse move (pan)
     */
    handleMouseMove(e) {
        if (!this.isPanning) return;

        this.translateX = e.clientX - this.startX;
        this.translateY = e.clientY - this.startY;

        const img = document.getElementById('zoomImage');
        if (img) {
            img.style.transform = `scale(${this.zoomLevel}) translate(${this.translateX}px, ${this.translateY}px)`;
        }
    }

    /**
     * Handle mouse up (fin de pan)
     */
    handleMouseUp() {
        this.isPanning = false;

        const img = document.getElementById('zoomImage');
        if (img && this.zoomLevel > 1) {
            img.style.cursor = 'move';
        }
    }

    /**
     * Handle touch start (gestos móviles)
     */
    handleTouchStart(e) {
        if (e.touches.length === 2) {
            // Pinch zoom
            e.preventDefault();
            const touch1 = e.touches[0];
            const touch2 = e.touches[1];
            this.touchStartDistance = Math.hypot(
                touch2.clientX - touch1.clientX,
                touch2.clientY - touch1.clientY
            );
            this.initialZoom = this.zoomLevel;
        } else if (e.touches.length === 1 && this.zoomLevel > 1) {
            // Pan con un dedo si hay zoom
            const touch = e.touches[0];
            this.isPanning = true;
            this.startX = touch.clientX - this.translateX;
            this.startY = touch.clientY - this.translateY;
        }
    }

    /**
     * Handle touch move
     */
    handleTouchMove(e) {
        if (e.touches.length === 2) {
            // Pinch zoom
            e.preventDefault();
            const touch1 = e.touches[0];
            const touch2 = e.touches[1];
            const distance = Math.hypot(
                touch2.clientX - touch1.clientX,
                touch2.clientY - touch1.clientY
            );
            const scale = distance / this.touchStartDistance;
            this.setZoom(this.initialZoom * scale);
        } else if (e.touches.length === 1 && this.isPanning) {
            // Pan
            e.preventDefault();
            const touch = e.touches[0];
            this.translateX = touch.clientX - this.startX;
            this.translateY = touch.clientY - this.startY;

            const img = document.getElementById('zoomImage');
            if (img) {
                img.style.transform = `scale(${this.zoomLevel}) translate(${this.translateX}px, ${this.translateY}px)`;
            }
        }
    }

    /**
     * Handle touch end
     */
    handleTouchEnd() {
        this.isPanning = false;
        this.touchStartDistance = 0;
    }

    /**
     * Handle teclado
     */
    handleKeyboard(e) {
        if (!this.modal || !this.modal._isShown) return;

        switch(e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                this.navigate(-1);
                break;
            case 'ArrowRight':
                e.preventDefault();
                this.navigate(1);
                break;
            case 'Escape':
                e.preventDefault();
                this.close();
                break;
            case '+':
            case '=':
                e.preventDefault();
                this.zoomIn();
                break;
            case '-':
            case '_':
                e.preventDefault();
                this.zoomOut();
                break;
            case '0':
                e.preventDefault();
                this.resetZoom();
                break;
            case ' ':
                e.preventDefault();
                this.togglePresentation();
                break;
            case 'f':
            case 'F':
                e.preventDefault();
                this.toggleFullscreen();
                break;
        }
    }

    /**
     * Actualizar botones de navegación
     */
    updateNavigationButtons() {
        const prevBtn = document.getElementById('zoomPrevBtn');
        const nextBtn = document.getElementById('zoomNextBtn');

        if (prevBtn) {
            prevBtn.style.opacity = this.currentIndex > 0 ? '1' : '0.3';
            prevBtn.disabled = this.currentIndex === 0;
        }

        if (nextBtn) {
            nextBtn.style.opacity = this.currentIndex < this.images.length - 1 ? '1' : '0.3';
            nextBtn.disabled = this.currentIndex === this.images.length - 1;
        }
    }

    /**
     * Cargar miniaturas
     */
    updateThumbnails() {
        const container = document.getElementById('zoomThumbnails');
        if (!container) return;

        container.innerHTML = '';

        this.images.forEach((img, index) => {
            const thumb = document.createElement('img');
            thumb.src = img.src;
            thumb.alt = img.alt;
            thumb.className = 'zoom-thumbnail';
            thumb.style.cssText = `
                width: 80px;
                height: 60px;
                object-fit: cover;
                cursor: pointer;
                border-radius: 4px;
                transition: all 0.3s ease;
                opacity: 0.6;
                border: 2px solid transparent;
            `;

            if (index === this.currentIndex) {
                thumb.style.opacity = '1';
                thumb.style.border = '2px solid #E31E24';
                thumb.style.transform = 'scale(1.1)';
            }

            thumb.addEventListener('click', () => this.goToIndex(index));
            thumb.addEventListener('mouseenter', () => {
                if (index !== this.currentIndex) {
                    thumb.style.opacity = '0.9';
                    thumb.style.transform = 'scale(1.05)';
                }
            });
            thumb.addEventListener('mouseleave', () => {
                if (index !== this.currentIndex) {
                    thumb.style.opacity = '0.6';
                    thumb.style.transform = 'scale(1)';
                }
            });

            container.appendChild(thumb);
        });
    }

    /**
     * Actualizar miniatura activa
     */
    updateActiveThumbnail() {
        const thumbnails = document.querySelectorAll('.zoom-thumbnail');
        thumbnails.forEach((thumb, index) => {
            if (index === this.currentIndex) {
                thumb.style.opacity = '1';
                thumb.style.border = '2px solid #E31E24';
                thumb.style.transform = 'scale(1.1)';

                // Scroll a la miniatura visible
                thumb.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
            } else {
                thumb.style.opacity = '0.6';
                thumb.style.border = '2px solid transparent';
                thumb.style.transform = 'scale(1)';
            }
        });
    }

    /**
     * Actualizar indicador de zoom
     */
    updateZoomIndicator() {
        let indicator = document.getElementById('zoomLevelIndicator');

        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'zoomLevelIndicator';
            indicator.style.cssText = `
                position: fixed;
                top: 100px;
                right: 20px;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 600;
                z-index: 9999;
                transition: opacity 0.3s ease;
                pointer-events: none;
            `;
            document.body.appendChild(indicator);
        }

        indicator.textContent = `${Math.round(this.zoomLevel * 100)}%`;
        indicator.style.opacity = '1';

        // Ocultar después de 1 segundo
        clearTimeout(this.zoomIndicatorTimeout);
        this.zoomIndicatorTimeout = setTimeout(() => {
            indicator.style.opacity = '0';
        }, 1000);
    }

    /**
     * Efecto de rebote
     */
    bounceEffect() {
        const img = document.getElementById('zoomImage');
        if (!img) return;

        const originalTransform = img.style.transform;
        img.style.transform = `${originalTransform} scale(0.95)`;

        setTimeout(() => {
            img.style.transform = originalTransform;
        }, 100);
    }

    /**
     * Toggle presentación automática
     */
    togglePresentation() {
        if (this.isPresentationMode) {
            this.stopPresentation();
        } else {
            this.startPresentation();
        }
    }

    /**
     * Iniciar presentación
     */
    startPresentation() {
        this.isPresentationMode = true;
        this.presentationInterval = setInterval(() => {
            if (this.currentIndex < this.images.length - 1) {
                this.navigate(1);
            } else {
                this.currentIndex = -1; // Volverá a 0 en el próximo navigate
                this.navigate(1);
            }
        }, this.presentationSpeed);

        console.log('▶️ Presentación iniciada');
        this.showPresentationNotification('▶️ Presentación iniciada');
    }

    /**
     * Detener presentación
     */
    stopPresentation() {
        if (this.presentationInterval) {
            clearInterval(this.presentationInterval);
            this.presentationInterval = null;
        }
        this.isPresentationMode = false;

        console.log('⏸️ Presentación detenida');
    }

    /**
     * Toggle fullscreen
     */
    toggleFullscreen() {
        const modalEl = document.getElementById('imageZoomModal');

        if (!document.fullscreenElement) {
            modalEl.requestFullscreen().then(() => {
                console.log('🖥️ Fullscreen activado');
                this.showPresentationNotification('🖥️ Fullscreen activado');
            }).catch(err => {
                console.error('Error fullscreen:', err);
            });
        } else {
            document.exitFullscreen().then(() => {
                console.log('🖥️ Fullscreen desactivado');
            });
        }
    }

    /**
     * Mostrar notificación de presentación
     */
    showPresentationNotification(message) {
        let notification = document.getElementById('presentationNotification');

        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'presentationNotification';
            notification.style.cssText = `
                position: fixed;
                top: 60px;
                left: 50%;
                transform: translateX(-50%);
                background: rgba(227, 30, 36, 0.95);
                color: white;
                padding: 12px 24px;
                border-radius: 25px;
                font-size: 16px;
                font-weight: 600;
                z-index: 9999;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
                transition: opacity 0.3s ease;
            `;
            document.body.appendChild(notification);
        }

        notification.textContent = message;
        notification.style.opacity = '1';

        clearTimeout(this.notificationTimeout);
        this.notificationTimeout = setTimeout(() => {
            notification.style.opacity = '0';
        }, 2000);
    }
}

// ============================================================================
// INICIALIZACIÓN Y EXPORTS
// ============================================================================

// Crear instancia global
let advancedZoom = null;

document.addEventListener('DOMContentLoaded', () => {
    advancedZoom = new AdvancedImageZoom();

    // Exponer funciones globales para compatibilidad
    window.advancedZoom = advancedZoom;

    // Mantener compatibilidad con código existente
    window.openImageZoom = (index) => advancedZoom.open(index);
    window.navigateZoom = (direction) => advancedZoom.navigate(direction);
});

export default AdvancedImageZoom;

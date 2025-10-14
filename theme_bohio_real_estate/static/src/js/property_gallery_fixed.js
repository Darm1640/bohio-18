/** @odoo-module **/

/**
 * ============================================================================
 * BOHÍO PROPERTY GALLERY - VERSIÓN CORREGIDA Y OPTIMIZADA
 * ============================================================================
 * Sistema de galería con zoom usando PhotoSwipe (alternativa: simple lightbox)
 * Compatible con Bootstrap 5.3.3 y Odoo 18
 */

class PropertyGallery {
    constructor() {
        this.currentIndex = 0;
        this.images = [];
        this.zoomModal = null;
        this.carouselInstance = null;
        this.init();
    }

    init() {
        console.log('🎨 Property Gallery inicializando...');
        
        // Recolectar imágenes
        this.collectImages();
        
        // Configurar carrusel
        this.setupCarousel();
        
        // Configurar modal de zoom
        this.setupZoomModal();
        
        // Event listeners
        this.setupEventListeners();
        
        console.log(`✅ Gallery lista con ${this.images.length} imágenes`);
    }

    /**
     * Recolectar todas las imágenes válidas del carrusel
     */
    collectImages() {
        const carousel = document.getElementById('propertyImageCarousel');
        if (!carousel) {
            console.warn('⚠️ Carrusel no encontrado');
            return;
        }

        const items = carousel.querySelectorAll('.carousel-item img');
        this.images = [];

        items.forEach((img, index) => {
            // Excluir placeholders
            if (img.src && !img.src.includes('banner1.jpg') && !img.src.includes('placeholder')) {
                this.images.push({
                    src: img.src,
                    alt: img.alt || `Imagen ${index + 1}`,
                    index: index,
                    element: img
                });
            }
        });

        console.log(`📸 Encontradas ${this.images.length} imágenes válidas`);
    }

    /**
     * Configurar carrusel de Bootstrap 5
     */
    setupCarousel() {
        const carouselEl = document.getElementById('propertyImageCarousel');
        if (!carouselEl) return;

        // Crear instancia de Bootstrap 5 Carousel
        this.carouselInstance = new bootstrap.Carousel(carouselEl, {
            interval: false, // Sin auto-play
            wrap: true,
            touch: true
        });

        // Listener para actualizar contador
        carouselEl.addEventListener('slid.bs.carousel', (e) => {
            const items = carouselEl.querySelectorAll('.carousel-item');
            const currentIndex = Array.from(items).indexOf(e.relatedTarget) + 1;
            
            const counter = document.getElementById('currentImageIndex');
            if (counter) {
                counter.textContent = currentIndex;
            }
        });
    }

    /**
     * Configurar modal de zoom
     */
    setupZoomModal() {
        const modalEl = document.getElementById('imageZoomModal');
        if (!modalEl) {
            console.warn('⚠️ Modal de zoom no encontrado');
            return;
        }

        // Crear instancia de Bootstrap Modal
        this.zoomModal = new bootstrap.Modal(modalEl, {
            backdrop: 'static',
            keyboard: true
        });

        // Limpiar estado al cerrar
        modalEl.addEventListener('hidden.bs.modal', () => {
            this.resetZoom();
        });
    }

    /**
     * Configurar event listeners
     */
    setupEventListeners() {
        // Click en imágenes del carrusel para abrir zoom
        this.images.forEach((img, index) => {
            if (img.element) {
                img.element.style.cursor = 'zoom-in';
                img.element.addEventListener('click', () => {
                    this.openZoom(index);
                });
            }
        });

        // Navegación con teclado
        document.addEventListener('keydown', (e) => {
            if (!this.zoomModal || !this.zoomModal._isShown) return;

            switch(e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.navigateZoom(-1);
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.navigateZoom(1);
                    break;
                case 'Escape':
                    e.preventDefault();
                    this.closeZoom();
                    break;
            }
        });

        // Botones de navegación en zoom
        const prevBtn = document.getElementById('zoomPrevBtn');
        const nextBtn = document.getElementById('zoomNextBtn');

        if (prevBtn) prevBtn.addEventListener('click', () => this.navigateZoom(-1));
        if (nextBtn) nextBtn.addEventListener('click', () => this.navigateZoom(1));
    }

    /**
     * Abrir modal de zoom
     */
    openZoom(index) {
        if (this.images.length === 0) {
            console.warn('⚠️ No hay imágenes para mostrar');
            return;
        }

        this.currentIndex = Math.max(0, Math.min(index, this.images.length - 1));
        this.updateZoomImage();
        this.loadThumbnails();
        
        if (this.zoomModal) {
            this.zoomModal.show();
        }
    }

    /**
     * Cerrar modal de zoom
     */
    closeZoom() {
        if (this.zoomModal) {
            this.zoomModal.hide();
        }
    }

    /**
     * Navegar entre imágenes en el zoom
     */
    navigateZoom(direction) {
        const newIndex = this.currentIndex + direction;

        if (newIndex < 0 || newIndex >= this.images.length) {
            // Efecto de rebote en los límites
            this.bounceEffect();
            return;
        }

        this.currentIndex = newIndex;
        this.updateZoomImage();
    }

    /**
     * Actualizar imagen en el modal de zoom
     */
    updateZoomImage() {
        const img = document.getElementById('zoomImage');
        const indexSpan = document.getElementById('zoomImageIndex');
        const totalSpan = document.getElementById('zoomTotalImages');
        const prevBtn = document.getElementById('zoomPrevBtn');
        const nextBtn = document.getElementById('zoomNextBtn');

        if (!img || this.currentIndex >= this.images.length) return;

        const imageData = this.images[this.currentIndex];

        // Transición suave
        img.style.opacity = '0.3';

        // Precargar imagen
        const tempImg = new Image();
        tempImg.onload = () => {
            img.src = tempImg.src;
            img.alt = imageData.alt;
            img.style.opacity = '1';
        };
        tempImg.onerror = () => {
            console.error('❌ Error cargando imagen');
            img.style.opacity = '0.5';
        };
        tempImg.src = imageData.src;

        // Actualizar contador
        if (indexSpan) indexSpan.textContent = this.currentIndex + 1;
        if (totalSpan) totalSpan.textContent = this.images.length;

        // Actualizar botones de navegación
        if (prevBtn) {
            prevBtn.style.opacity = this.currentIndex > 0 ? '1' : '0.3';
            prevBtn.disabled = this.currentIndex === 0;
        }
        if (nextBtn) {
            nextBtn.style.opacity = this.currentIndex < this.images.length - 1 ? '1' : '0.3';
            nextBtn.disabled = this.currentIndex === this.images.length - 1;
        }

        // Actualizar miniaturas
        this.updateActiveThumbnail();
    }

    /**
     * Cargar miniaturas en el zoom
     */
    loadThumbnails() {
        const container = document.getElementById('zoomThumbnails');
        if (!container) return;

        container.innerHTML = '';

        this.images.forEach((imgData, index) => {
            const thumbDiv = document.createElement('div');
            thumbDiv.className = 'zoom-thumbnail';
            thumbDiv.style.cssText = `
                cursor: pointer;
                opacity: ${index === this.currentIndex ? '1' : '0.6'};
                border: ${index === this.currentIndex ? '3px solid #E31E24' : '3px solid transparent'};
                border-radius: 8px;
                transition: all 0.3s ease;
                width: 80px;
                height: 60px;
                overflow: hidden;
                flex-shrink: 0;
            `;

            const thumbImg = document.createElement('img');
            thumbImg.src = imgData.src;
            thumbImg.alt = imgData.alt;
            thumbImg.style.cssText = `
                width: 100%;
                height: 100%;
                object-fit: cover;
            `;

            thumbImg.onerror = function() {
                this.style.opacity = '0.3';
            };

            thumbDiv.addEventListener('click', () => {
                this.currentIndex = index;
                this.updateZoomImage();
            });

            thumbDiv.addEventListener('mouseenter', () => {
                if (index !== this.currentIndex) {
                    thumbDiv.style.opacity = '0.9';
                    thumbDiv.style.transform = 'scale(1.05)';
                }
            });

            thumbDiv.addEventListener('mouseleave', () => {
                if (index !== this.currentIndex) {
                    thumbDiv.style.opacity = '0.6';
                    thumbDiv.style.transform = 'scale(1)';
                }
            });

            thumbDiv.appendChild(thumbImg);
            container.appendChild(thumbDiv);
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
                thumb.style.border = '3px solid #E31E24';
                thumb.style.transform = 'scale(1.1)';
                
                // Scroll suave a la miniatura activa
                thumb.scrollIntoView({
                    behavior: 'smooth',
                    block: 'nearest',
                    inline: 'center'
                });
            } else {
                thumb.style.opacity = '0.6';
                thumb.style.border = '3px solid transparent';
                thumb.style.transform = 'scale(1)';
            }
        });
    }

    /**
     * Efecto de rebote en los límites
     */
    bounceEffect() {
        const img = document.getElementById('zoomImage');
        if (!img) return;

        const originalTransform = img.style.transform;
        img.style.transform = 'scale(0.95)';
        
        setTimeout(() => {
            img.style.transform = originalTransform || 'scale(1)';
        }, 150);
    }

    /**
     * Resetear zoom
     */
    resetZoom() {
        this.currentIndex = 0;
    }

    /**
     * Abrir galería en grid
     */
    openGalleryModal() {
        const modalEl = document.getElementById('galleryModal');
        const grid = document.getElementById('galleryGrid');

        if (!modalEl || !grid) return;

        // Limpiar grid
        grid.innerHTML = '';

        // Crear grid de imágenes
        this.images.forEach((imgData, index) => {
            const col = document.createElement('div');
            col.className = 'col-md-4 col-sm-6 mb-3';

            const card = document.createElement('div');
            card.className = 'card border-0 shadow-sm h-100';
            card.style.cssText = 'cursor: pointer; transition: transform 0.2s;';

            card.addEventListener('mouseenter', () => {
                card.style.transform = 'scale(1.05)';
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = 'scale(1)';
            });

            card.addEventListener('click', () => {
                // Cerrar modal de galería
                const galleryModal = bootstrap.Modal.getInstance(modalEl);
                if (galleryModal) galleryModal.hide();

                // Ir a la imagen en el carrusel
                if (this.carouselInstance) {
                    this.carouselInstance.to(index);
                }
            });

            const img = document.createElement('img');
            img.src = imgData.src;
            img.alt = imgData.alt;
            img.className = 'card-img-top';
            img.style.cssText = 'height: 200px; object-fit: cover;';

            const cardBody = document.createElement('div');
            cardBody.className = 'card-body p-2 text-center';
            cardBody.innerHTML = `<small class="text-muted">Imagen ${index + 1}</small>`;

            card.appendChild(img);
            card.appendChild(cardBody);
            col.appendChild(card);
            grid.appendChild(col);
        });

        // Mostrar modal
        const modal = new bootstrap.Modal(modalEl);
        modal.show();
    }
}

// ============================================================================
// FUNCIONES GLOBALES PARA COMPATIBILIDAD
// ============================================================================

let galleryInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    galleryInstance = new PropertyGallery();

    // Exponer funciones globalmente
    window.openImageZoom = (index) => galleryInstance.openZoom(index);
    window.navigateZoom = (direction) => galleryInstance.navigateZoom(direction);
    window.openGalleryModal = () => galleryInstance.openGalleryModal();
});

console.log('✅ Property Gallery Module cargado');

export default PropertyGallery;
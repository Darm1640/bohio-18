/** @odoo-module */
/**
 * Sistema de Galería Mejorado para Propiedades en Odoo 18
 * Implementa zoom, galería y navegación optimizada con Bootstrap 5.3.3
 *
 * @module PropertyGalleryEnhanced
 * @requires Bootstrap 5.3.3
 * @author BOHIO Real Estate
 * @version 18.0.1.0
 */

import { Component } from '@odoo/owl';

export class PropertyGalleryEnhanced {
    constructor(options = {}) {
        this.options = {
            containerId: options.containerId || 'property-gallery',
            images: options.images || [],
            enableZoom: options.enableZoom !== false,
            enableGallery: options.enableGallery !== false,
            enableKeyboard: options.enableKeyboard !== false,
            lazyLoad: options.lazyLoad !== false,
            placeholderImage: options.placeholderImage || '/theme_bohio_real_estate/static/src/img/banner1.jpg',
            ...options
        };

        this.currentIndex = 0;
        this.images = [];
        this.validImages = [];
        this.imageCache = new Map();
        this.loadingImages = new Set();
        this.modals = {};

        this.init();
    }

    /**
     * Inicializa el sistema de galería
     */
    init() {
        this.processImages();
        this.createModals();
        this.setupCarousel();
        this.setupKeyboardNavigation();
        this.setupLazyLoading();
        this.preloadAdjacentImages();
    }

    /**
     * Procesa y valida las imágenes
     */
    processImages() {
        this.validImages = this.options.images.filter(img => {
            if (!img || !img.src) return false;

            // Excluir placeholders
            if (img.src.includes('placeholder') || img.src.includes('banner1.jpg')) {
                return false;
            }

            return true;
        }).map((img, index) => ({
            id: img.id || `img-${index}`,
            src: this.optimizeImageUrl(img.src),
            srcOriginal: img.src,
            alt: img.alt || `Imagen ${index + 1}`,
            title: img.title || '',
            index: index
        }));
    }

    /**
     * Optimiza URLs de imágenes para mejor performance
     */
    optimizeImageUrl(url, size = 'large') {
        if (!url) return this.options.placeholderImage;

        const sizes = {
            thumb: { width: 150, quality: 60 },
            medium: { width: 600, quality: 75 },
            large: { width: 1200, quality: 85 },
            full: { width: 1920, quality: 90 }
        };

        const params = sizes[size] || sizes.large;

        if (url.includes('/web/image')) {
            const separator = url.includes('?') ? '&' : '?';
            return `${url}${separator}width=${params.width}&quality=${params.quality}`;
        }

        return url;
    }

    /**
     * Crea los modales de zoom y galería
     */
    createModals() {
        // Modal de Zoom Fullscreen
        this.createZoomModal();

        // Modal de Galería Grid
        this.createGalleryModal();
    }

    /**
     * Crea el modal de zoom con navegación
     */
    createZoomModal() {
        const modalHtml = `
            <div class="modal fade" id="propertyZoomModal" tabindex="-1" data-bs-backdrop="static">
                <div class="modal-dialog modal-fullscreen">
                    <div class="modal-content bg-dark">
                        <!-- Header con contador -->
                        <div class="modal-header border-0 position-absolute w-100" style="z-index: 1055; background: linear-gradient(to bottom, rgba(0,0,0,0.8), transparent);">
                            <div class="text-white">
                                <i class="bi bi-camera me-2"></i>
                                <span class="zoom-counter">
                                    <span id="zoomCurrentIndex">1</span> / <span id="zoomTotalImages">${this.validImages.length}</span>
                                </span>
                            </div>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>

                        <!-- Body con imagen -->
                        <div class="modal-body d-flex align-items-center justify-content-center p-0">
                            <!-- Navegación izquierda -->
                            <button class="btn btn-light rounded-circle position-absolute start-0 ms-3 zoom-nav zoom-prev" style="z-index: 1055;">
                                <i class="bi bi-chevron-left"></i>
                            </button>

                            <!-- Contenedor de imagen con loading -->
                            <div class="zoom-image-container position-relative">
                                <div class="zoom-loading position-absolute top-50 start-50 translate-middle">
                                    <div class="spinner-border text-light" role="status">
                                        <span class="visually-hidden">Cargando...</span>
                                    </div>
                                </div>
                                <img id="zoomImage" class="zoom-image" alt="Imagen ampliada">
                            </div>

                            <!-- Navegación derecha -->
                            <button class="btn btn-light rounded-circle position-absolute end-0 me-3 zoom-nav zoom-next" style="z-index: 1055;">
                                <i class="bi bi-chevron-right"></i>
                            </button>
                        </div>

                        <!-- Thumbnails en la parte inferior -->
                        <div class="modal-footer border-0 position-absolute bottom-0 w-100" style="background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);">
                            <div class="zoom-thumbnails-container w-100 overflow-auto">
                                <div class="zoom-thumbnails d-flex gap-2 justify-content-center py-2"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Agregar al DOM si no existe
        if (!document.getElementById('propertyZoomModal')) {
            document.body.insertAdjacentHTML('beforeend', modalHtml);
        }

        this.modals.zoom = new bootstrap.Modal(document.getElementById('propertyZoomModal'));
        this.setupZoomEvents();
    }

    /**
     * Configura eventos del modal de zoom
     */
    setupZoomEvents() {
        const modal = document.getElementById('propertyZoomModal');
        if (!modal) return;

        // Navegación con botones
        modal.querySelector('.zoom-prev')?.addEventListener('click', () => this.navigateZoom(-1));
        modal.querySelector('.zoom-next')?.addEventListener('click', () => this.navigateZoom(1));

        // Navegación con teclado (solo cuando el modal está abierto)
        modal.addEventListener('shown.bs.modal', () => {
            this.loadZoomImage(this.currentIndex);
            this.createZoomThumbnails();
            this.preloadAdjacentImages();
        });

        // Swipe gestures para móvil
        this.setupTouchGestures(modal.querySelector('.zoom-image-container'));
    }

    /**
     * Configura gestos táctiles para navegación
     */
    setupTouchGestures(element) {
        if (!element) return;

        let startX = 0;
        let startY = 0;
        let endX = 0;
        let endY = 0;

        element.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });

        element.addEventListener('touchend', (e) => {
            endX = e.changedTouches[0].clientX;
            endY = e.changedTouches[0].clientY;

            const deltaX = endX - startX;
            const deltaY = endY - startY;

            // Detectar swipe horizontal
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
                if (deltaX > 0) {
                    this.navigateZoom(-1); // Swipe derecha = imagen anterior
                } else {
                    this.navigateZoom(1);  // Swipe izquierda = siguiente imagen
                }
            }
        });
    }

    /**
     * Carga imagen en el zoom con manejo de errores
     */
    async loadZoomImage(index) {
        if (index < 0 || index >= this.validImages.length) return;

        const image = this.validImages[index];
        const zoomImg = document.getElementById('zoomImage');
        const loading = document.querySelector('.zoom-loading');

        if (!zoomImg) return;

        // Mostrar loading
        if (loading) loading.style.display = 'block';
        zoomImg.style.opacity = '0';

        try {
            // Verificar cache
            if (this.imageCache.has(image.srcOriginal)) {
                zoomImg.src = this.imageCache.get(image.srcOriginal);
                zoomImg.style.opacity = '1';
                if (loading) loading.style.display = 'none';
            } else {
                // Cargar imagen
                const img = await this.loadImage(image.srcOriginal);
                this.imageCache.set(image.srcOriginal, img.src);
                zoomImg.src = img.src;
                zoomImg.style.opacity = '1';
                if (loading) loading.style.display = 'none';
            }

            // Actualizar contador
            this.updateZoomCounter(index);

            // Actualizar thumbnails activo
            this.updateActiveThumbnail(index);

        } catch (error) {
            console.error('Error loading zoom image:', error);
            zoomImg.src = this.options.placeholderImage;
            zoomImg.style.opacity = '0.7';
            if (loading) loading.style.display = 'none';
        }
    }

    /**
     * Carga una imagen con Promise
     */
    loadImage(src) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = () => reject(new Error(`Failed to load image: ${src}`));
            img.src = src;
        });
    }

    /**
     * Navega entre imágenes del zoom
     */
    navigateZoom(direction) {
        const newIndex = this.currentIndex + direction;

        if (newIndex >= 0 && newIndex < this.validImages.length) {
            this.currentIndex = newIndex;
            this.loadZoomImage(this.currentIndex);

            // Actualizar botones de navegación
            this.updateNavigationButtons();

            // Precargar imágenes adyacentes
            this.preloadAdjacentImages();
        }
    }

    /**
     * Actualiza el estado de los botones de navegación
     */
    updateNavigationButtons() {
        const prevBtn = document.querySelector('.zoom-prev');
        const nextBtn = document.querySelector('.zoom-next');

        if (prevBtn) {
            prevBtn.style.display = this.currentIndex > 0 ? 'block' : 'none';
        }

        if (nextBtn) {
            nextBtn.style.display = this.currentIndex < this.validImages.length - 1 ? 'block' : 'none';
        }
    }

    /**
     * Actualiza el contador del zoom
     */
    updateZoomCounter(index) {
        const currentEl = document.getElementById('zoomCurrentIndex');
        const totalEl = document.getElementById('zoomTotalImages');

        if (currentEl) currentEl.textContent = index + 1;
        if (totalEl) totalEl.textContent = this.validImages.length;
    }

    /**
     * Crea thumbnails para el zoom
     */
    createZoomThumbnails() {
        const container = document.querySelector('.zoom-thumbnails');
        if (!container) return;

        container.innerHTML = '';

        this.validImages.forEach((image, index) => {
            const thumb = document.createElement('div');
            thumb.className = 'zoom-thumbnail';
            thumb.dataset.index = index;

            const img = document.createElement('img');
            img.src = this.optimizeImageUrl(image.src, 'thumb');
            img.alt = image.alt;
            img.loading = 'lazy';

            thumb.appendChild(img);
            thumb.addEventListener('click', () => {
                this.currentIndex = index;
                this.loadZoomImage(index);
            });

            container.appendChild(thumb);
        });

        this.updateActiveThumbnail(this.currentIndex);
    }

    /**
     * Actualiza el thumbnail activo
     */
    updateActiveThumbnail(index) {
        document.querySelectorAll('.zoom-thumbnail').forEach((thumb, i) => {
            if (i === index) {
                thumb.classList.add('active');
                thumb.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
            } else {
                thumb.classList.remove('active');
            }
        });
    }

    /**
     * Crea el modal de galería en grid
     */
    createGalleryModal() {
        const modalHtml = `
            <div class="modal fade" id="propertyGalleryModal" tabindex="-1">
                <div class="modal-dialog modal-xl modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="bi bi-grid me-2"></i>Galería de Imágenes
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="gallery-grid row g-3"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        if (!document.getElementById('propertyGalleryModal')) {
            document.body.insertAdjacentHTML('beforeend', modalHtml);
        }

        this.modals.gallery = new bootstrap.Modal(document.getElementById('propertyGalleryModal'));
    }

    /**
     * Abre la galería en modo grid
     */
    openGallery() {
        const container = document.querySelector('.gallery-grid');
        if (!container) return;

        container.innerHTML = '';

        this.validImages.forEach((image, index) => {
            const col = document.createElement('div');
            col.className = 'col-12 col-sm-6 col-md-4';

            const card = document.createElement('div');
            card.className = 'gallery-item position-relative';
            card.style.cursor = 'pointer';

            const img = document.createElement('img');
            img.src = this.optimizeImageUrl(image.src, 'medium');
            img.alt = image.alt;
            img.className = 'img-fluid rounded';
            img.loading = 'lazy';

            const overlay = document.createElement('div');
            overlay.className = 'gallery-overlay position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center';
            overlay.innerHTML = `
                <div class="text-white">
                    <i class="bi bi-zoom-in fs-2"></i>
                </div>
            `;

            card.appendChild(img);
            card.appendChild(overlay);
            col.appendChild(card);

            card.addEventListener('click', () => {
                this.modals.gallery.hide();
                this.currentIndex = index;
                this.openZoom(index);
            });

            container.appendChild(col);
        });

        this.modals.gallery.show();
    }

    /**
     * Abre el zoom en un índice específico
     */
    openZoom(index = 0) {
        this.currentIndex = index;
        this.modals.zoom.show();
    }

    /**
     * Configura el carousel principal
     */
    setupCarousel() {
        const carousel = document.querySelector(this.options.containerId);
        if (!carousel) return;

        carousel.addEventListener('slid.bs.carousel', (e) => {
            const items = Array.from(carousel.querySelectorAll('.carousel-item'));
            this.currentIndex = items.indexOf(e.relatedTarget);
        });
    }

    /**
     * Configura navegación con teclado
     */
    setupKeyboardNavigation() {
        if (!this.options.enableKeyboard) return;

        document.addEventListener('keydown', (e) => {
            const zoomModal = document.getElementById('propertyZoomModal');
            if (!zoomModal || !zoomModal.classList.contains('show')) return;

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
                    this.modals.zoom.hide();
                    break;
            }
        });
    }

    /**
     * Configura lazy loading para imágenes
     */
    setupLazyLoading() {
        if (!this.options.lazyLoad) return;

        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src && !img.src) {
                        img.src = img.dataset.src;
                        img.classList.add('loaded');
                        observer.unobserve(img);
                    }
                }
            });
        }, {
            rootMargin: '50px'
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
    }

    /**
     * Precarga imágenes adyacentes para navegación fluida
     */
    preloadAdjacentImages() {
        const preloadIndexes = [
            this.currentIndex - 1,
            this.currentIndex + 1
        ].filter(i => i >= 0 && i < this.validImages.length);

        preloadIndexes.forEach(index => {
            const image = this.validImages[index];
            if (!this.imageCache.has(image.srcOriginal) && !this.loadingImages.has(image.srcOriginal)) {
                this.loadingImages.add(image.srcOriginal);

                this.loadImage(image.srcOriginal)
                    .then(img => {
                        this.imageCache.set(image.srcOriginal, img.src);
                        this.loadingImages.delete(image.srcOriginal);
                    })
                    .catch(() => {
                        this.loadingImages.delete(image.srcOriginal);
                    });
            }
        });
    }

    /**
     * Destruye el componente y limpia recursos
     */
    destroy() {
        // Limpiar modales
        Object.values(this.modals).forEach(modal => modal.dispose());

        // Limpiar cache
        this.imageCache.clear();
        this.loadingImages.clear();

        // Remover elementos del DOM
        document.getElementById('propertyZoomModal')?.remove();
        document.getElementById('propertyGalleryModal')?.remove();
    }
}

// Estilos CSS para el componente
const styles = `
<style>
/* Zoom Modal Styles */
.zoom-image-container {
    width: 90vw;
    height: 90vh;
    display: flex;
    align-items: center;
    justify-content: center;
}

.zoom-image {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    transition: opacity 0.3s ease;
}

.zoom-loading {
    display: none;
}

.zoom-nav {
    width: 50px;
    height: 50px;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0.8;
    transition: opacity 0.3s;
}

.zoom-nav:hover {
    opacity: 1;
}

/* Thumbnails */
.zoom-thumbnails-container {
    max-height: 120px;
}

.zoom-thumbnail {
    width: 80px;
    height: 60px;
    cursor: pointer;
    opacity: 0.6;
    transition: all 0.3s;
    border: 2px solid transparent;
    border-radius: 4px;
    overflow: hidden;
}

.zoom-thumbnail img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.zoom-thumbnail.active {
    opacity: 1;
    border-color: #FF1D25;
}

.zoom-thumbnail:hover {
    opacity: 1;
    transform: scale(1.05);
}

/* Gallery Grid Styles */
.gallery-item {
    overflow: hidden;
    border-radius: 8px;
    transition: transform 0.3s;
}

.gallery-item:hover {
    transform: scale(1.02);
}

.gallery-item img {
    width: 100%;
    height: 250px;
    object-fit: cover;
}

.gallery-overlay {
    background: rgba(0,0,0,0);
    transition: background 0.3s;
    opacity: 0;
}

.gallery-item:hover .gallery-overlay {
    background: rgba(0,0,0,0.5);
    opacity: 1;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .zoom-nav {
        width: 40px;
        height: 40px;
    }

    .zoom-thumbnail {
        width: 60px;
        height: 45px;
    }

    .gallery-item img {
        height: 180px;
    }
}
</style>
`;

// Agregar estilos al documento si no existen
if (!document.getElementById('property-gallery-enhanced-styles')) {
    const styleElement = document.createElement('div');
    styleElement.id = 'property-gallery-enhanced-styles';
    styleElement.innerHTML = styles;
    document.head.appendChild(styleElement.querySelector('style'));
}

// Exportar para uso global
export default PropertyGalleryEnhanced;
/** @odoo-module **/

/**
 * ============================================================================
 * LAZY IMAGE LOADER - Optimización Agresiva
 * ============================================================================
 * Sistema de carga progresiva de imágenes para evitar ERR_INSUFFICIENT_RESOURCES
 *
 * Características:
 * - Cola de carga (máximo 6 imágenes simultáneas)
 * - Intersection Observer (carga solo lo visible)
 * - Placeholder blur
 * - Cache de imágenes exitosas
 * - Retry automático para errores
 */

class LazyImageLoader {
    constructor() {
        this.loadingQueue = [];
        this.loadingCount = 0;
        this.MAX_CONCURRENT = 6;  // Máximo 6 imágenes simultáneas
        this.imageCache = new Map();
        this.retryAttempts = new Map();
        this.MAX_RETRIES = 2;

        this.observer = null;
        this.init();
    }

    init() {
        console.log('🖼️ Lazy Image Loader inicializando...');

        // Crear Intersection Observer
        this.observer = new IntersectionObserver(
            (entries) => this.handleIntersection(entries),
            {
                root: null,
                rootMargin: '50px',  // Precargar 50px antes de ser visible
                threshold: 0.01
            }
        );

        // Observar todas las imágenes lazy
        this.observeImages();

        // Re-observar cuando se agreguen nuevas imágenes (mutaciones DOM)
        this.observeMutations();

        console.log('✅ Lazy Image Loader listo');
    }

    /**
     * Observar todas las imágenes con data-lazy
     */
    observeImages() {
        const lazyImages = document.querySelectorAll('img[data-lazy]');
        console.log(`🔍 Encontradas ${lazyImages.length} imágenes lazy`);

        lazyImages.forEach(img => {
            // Agregar placeholder blur
            if (!img.src || img.src.includes('data:image')) {
                img.style.filter = 'blur(10px)';
                img.style.opacity = '0.5';
                img.style.transition = 'all 0.3s ease';
            }

            this.observer.observe(img);
        });
    }

    /**
     * Observar mutaciones del DOM para nuevas imágenes
     */
    observeMutations() {
        const mutationObserver = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) {  // Element node
                        // Verificar si es una imagen lazy
                        if (node.matches && node.matches('img[data-lazy]')) {
                            this.observer.observe(node);
                        }

                        // Verificar imágenes hijas
                        const lazyChildren = node.querySelectorAll && node.querySelectorAll('img[data-lazy]');
                        if (lazyChildren) {
                            lazyChildren.forEach(img => this.observer.observe(img));
                        }
                    }
                });
            });
        });

        mutationObserver.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    /**
     * Manejar intersección (imagen entra en viewport)
     */
    handleIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;

                // Dejar de observar
                this.observer.unobserve(img);

                // Agregar a cola de carga
                this.queueImageLoad(img);
            }
        });
    }

    /**
     * Agregar imagen a la cola de carga
     */
    queueImageLoad(img) {
        // Verificar si ya está en cola
        if (this.loadingQueue.includes(img)) {
            return;
        }

        // Agregar a cola
        this.loadingQueue.push(img);

        // Procesar cola
        this.processQueue();
    }

    /**
     * Procesar cola de carga
     */
    async processQueue() {
        // Si ya estamos en el límite, esperar
        if (this.loadingCount >= this.MAX_CONCURRENT) {
            return;
        }

        // Si no hay nada en cola, salir
        if (this.loadingQueue.length === 0) {
            return;
        }

        // Tomar siguiente imagen de la cola
        const img = this.loadingQueue.shift();

        // Incrementar contador
        this.loadingCount++;

        // Cargar imagen
        await this.loadImage(img);

        // Decrementar contador
        this.loadingCount--;

        // Procesar siguiente en cola (recursivo)
        this.processQueue();
    }

    /**
     * Cargar una imagen individual
     */
    async loadImage(img) {
        const lazySrc = img.dataset.lazy;

        if (!lazySrc) {
            console.warn('⚠️ Imagen sin data-lazy:', img);
            return;
        }

        // Verificar cache
        if (this.imageCache.has(lazySrc)) {
            console.log('✅ Imagen desde cache:', lazySrc);
            this.applyImage(img, lazySrc);
            return;
        }

        try {
            // Precargar imagen
            const tempImg = new Image();

            const loadPromise = new Promise((resolve, reject) => {
                tempImg.onload = () => resolve(tempImg);
                tempImg.onerror = () => reject(new Error('Failed to load'));

                // Timeout de 10 segundos
                setTimeout(() => reject(new Error('Timeout')), 10000);
            });

            tempImg.src = lazySrc;

            // Esperar carga
            await loadPromise;

            // Imagen cargada exitosamente
            this.imageCache.set(lazySrc, true);
            this.applyImage(img, lazySrc);

            console.log('✅ Imagen cargada:', lazySrc.substring(0, 50) + '...');

        } catch (error) {
            console.error('❌ Error cargando imagen:', lazySrc, error);

            // Retry logic
            const retries = this.retryAttempts.get(img) || 0;

            if (retries < this.MAX_RETRIES) {
                console.log(`🔄 Reintentando (${retries + 1}/${this.MAX_RETRIES})...`);
                this.retryAttempts.set(img, retries + 1);

                // Reintentar después de 2 segundos
                setTimeout(() => {
                    this.queueImageLoad(img);
                }, 2000);
            } else {
                // Fallback a placeholder
                console.warn('⚠️ Fallback a placeholder después de', this.MAX_RETRIES, 'intentos');
                this.applyImage(img, img.dataset.placeholder || '/theme_bohio_real_estate/static/src/img/placeholder.jpg');
            }
        }
    }

    /**
     * Aplicar imagen cargada al elemento
     */
    applyImage(img, src) {
        // Animación de entrada
        img.style.opacity = '0';

        setTimeout(() => {
            img.src = src;
            img.removeAttribute('data-lazy');

            // Fade in suave
            img.style.filter = 'none';
            img.style.opacity = '1';

            console.log('🖼️ Imagen aplicada:', src.substring(0, 50) + '...');
        }, 50);
    }

    /**
     * Precargar grupo de imágenes prioritarias
     */
    preloadPriority(images) {
        console.log(`⚡ Precargando ${images.length} imágenes prioritarias...`);

        images.forEach(img => {
            if (img.dataset.lazy) {
                this.queueImageLoad(img);
            }
        });
    }

    /**
     * Limpiar cache (liberar memoria)
     */
    clearCache() {
        console.log('🧹 Limpiando cache de imágenes...');
        this.imageCache.clear();
        this.retryAttempts.clear();
    }

    /**
     * Obtener estadísticas
     */
    getStats() {
        return {
            cached: this.imageCache.size,
            queued: this.loadingQueue.length,
            loading: this.loadingCount,
            maxConcurrent: this.MAX_CONCURRENT
        };
    }
}

// Crear instancia global
const lazyImageLoader = new LazyImageLoader();

// Exponer globalmente
window.lazyImageLoader = lazyImageLoader;

// Comando para limpiar cache manualmente
window.clearImageCache = () => {
    lazyImageLoader.clearCache();
    console.log('✅ Cache de imágenes limpiado');
};

// Mostrar stats en consola
window.imageLoaderStats = () => {
    console.table(lazyImageLoader.getStats());
};

console.log('✅ Lazy Image Loader módulo cargado');

export default lazyImageLoader;

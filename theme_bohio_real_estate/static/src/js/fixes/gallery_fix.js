/** @odoo-module **/

/**
 * Fix para la galería de imágenes en property detail
 * Corrige el modal de galería y el contador de imágenes
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('🖼️ Gallery Fix iniciado');

    // Fix para el contador de imágenes
    function fixImageCounter() {
        const carousel = document.getElementById('propertyImageCarousel');
        if (!carousel) return;

        const totalImages = carousel.querySelectorAll('.carousel-item').length;
        const totalElement = document.getElementById('totalImages');
        const currentElement = document.getElementById('currentImageIndex');

        if (totalElement) {
            totalElement.textContent = totalImages;
        }

        // Actualizar el contador actual basado en el item activo
        const activeItem = carousel.querySelector('.carousel-item.active');
        if (activeItem && currentElement) {
            const activeIndex = Array.from(carousel.querySelectorAll('.carousel-item')).indexOf(activeItem) + 1;
            currentElement.textContent = activeIndex;
        }

        // Escuchar cambios en el carrusel
        carousel.addEventListener('slid.bs.carousel', function(e) {
            const currentIndex = Array.from(e.target.querySelectorAll('.carousel-item')).indexOf(e.relatedTarget) + 1;
            if (currentElement) {
                currentElement.textContent = currentIndex;
            }
            console.log(`📸 Imagen ${currentIndex} de ${totalImages}`);
        });

        console.log(`✅ Contador de imágenes corregido: ${totalImages} imágenes totales`);
    }

    // Fix para el botón de galería
    function fixGalleryButton() {
        const galleryBtn = document.querySelector('.btn-gallery, [onclick*="openGalleryModal"]');

        if (galleryBtn) {
            // Remover onclick inline y agregar event listener
            galleryBtn.removeAttribute('onclick');
            galleryBtn.addEventListener('click', function(e) {
                e.preventDefault();
                openGalleryModal();
            });

            console.log('✅ Botón de galería configurado');
        }
    }

    // Función mejorada para abrir el modal de galería
    window.openGalleryModal = function() {
        console.log('🖼️ Abriendo modal de galería');

        // Crear modal si no existe
        let modalElement = document.getElementById('galleryModal');

        if (!modalElement) {
            console.log('⚠️ Modal no encontrado, creándolo...');
            modalElement = createGalleryModal();
            document.body.appendChild(modalElement);
        }

        // Poblar galería con imágenes
        populateGallery(modalElement);

        // Abrir modal
        try {
            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
                console.log('✅ Modal abierto con Bootstrap 5');
            } else if (typeof $ !== 'undefined' && $.fn.modal) {
                $(modalElement).modal('show');
                console.log('✅ Modal abierto con jQuery');
            } else {
                // Fallback manual
                modalElement.classList.add('show');
                modalElement.style.display = 'block';
                document.body.classList.add('modal-open');

                // Agregar backdrop
                const backdrop = document.createElement('div');
                backdrop.className = 'modal-backdrop fade show';
                backdrop.id = 'gallery-backdrop';
                document.body.appendChild(backdrop);

                console.log('✅ Modal abierto manualmente');
            }
        } catch (error) {
            console.error('❌ Error abriendo modal:', error);
        }
    };

    // Crear estructura del modal de galería
    function createGalleryModal() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = 'galleryModal';
        modal.tabindex = '-1';
        modal.setAttribute('aria-labelledby', 'galleryModalLabel');
        modal.setAttribute('aria-hidden', 'true');

        modal.innerHTML = `
            <div class="modal-dialog modal-xl modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="galleryModalLabel">
                            <i class="bi bi-images me-2"></i>Galería de Imágenes
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row g-3" id="galleryGrid">
                            <!-- Las imágenes se cargarán aquí -->
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Agregar evento de cerrar para el backdrop manual
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeGalleryModal();
            }
        });

        return modal;
    }

    // Poblar galería con imágenes
    function populateGallery(modalElement) {
        const grid = modalElement.querySelector('#galleryGrid');
        if (!grid) return;

        grid.innerHTML = ''; // Limpiar

        const carousel = document.getElementById('propertyImageCarousel');
        if (!carousel) {
            grid.innerHTML = '<div class="col-12 text-center text-muted">No hay imágenes disponibles</div>';
            return;
        }

        const carouselItems = carousel.querySelectorAll('.carousel-item');

        carouselItems.forEach((item, index) => {
            const img = item.querySelector('img');
            if (!img) return;

            const col = document.createElement('div');
            col.className = 'col-md-4 col-sm-6 mb-3';

            const wrapper = document.createElement('div');
            wrapper.className = 'position-relative gallery-item';
            wrapper.style.cursor = 'pointer';

            const imgElement = document.createElement('img');
            imgElement.src = img.src;
            imgElement.alt = img.alt || `Imagen ${index + 1}`;
            imgElement.className = 'img-fluid rounded shadow-sm';
            imgElement.style.cssText = 'width: 100%; height: 250px; object-fit: cover;';

            // Badge con número
            const badge = document.createElement('span');
            badge.className = 'position-absolute top-0 start-0 m-2 badge bg-dark';
            badge.textContent = index + 1;

            // Evento click para ir a esa imagen
            wrapper.addEventListener('click', function() {
                goToSlide(index);
                closeGalleryModal();
            });

            wrapper.appendChild(imgElement);
            wrapper.appendChild(badge);
            col.appendChild(wrapper);
            grid.appendChild(col);
        });

        console.log(`✅ Galería poblada con ${carouselItems.length} imágenes`);
    }

    // Cerrar modal de galería
    window.closeGalleryModal = function() {
        const modal = document.getElementById('galleryModal');
        const backdrop = document.getElementById('gallery-backdrop');

        if (modal) {
            if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
            } else if (typeof $ !== 'undefined' && $.fn.modal) {
                $(modal).modal('hide');
            } else {
                modal.classList.remove('show');
                modal.style.display = 'none';
                document.body.classList.remove('modal-open');
                if (backdrop) backdrop.remove();
            }
        }
    };

    // Ir a una diapositiva específica
    window.goToSlide = function(index) {
        const carousel = document.getElementById('propertyImageCarousel');
        if (!carousel) return;

        // Usar Bootstrap Carousel API
        if (typeof bootstrap !== 'undefined' && bootstrap.Carousel) {
            const bsCarousel = new bootstrap.Carousel(carousel);
            bsCarousel.to(index);
        } else if (typeof $ !== 'undefined' && $.fn.carousel) {
            $(carousel).carousel(index);
        } else {
            // Fallback manual
            const items = carousel.querySelectorAll('.carousel-item');
            const activeItem = carousel.querySelector('.carousel-item.active');

            if (activeItem) activeItem.classList.remove('active');
            if (items[index]) items[index].classList.add('active');

            // Actualizar contador
            const currentElement = document.getElementById('currentImageIndex');
            if (currentElement) {
                currentElement.textContent = index + 1;
            }
        }

        console.log(`📍 Navegando a imagen ${index + 1}`);
    };

    // Fix para el zoom de imágenes
    function fixImageZoom() {
        const carousel = document.getElementById('propertyImageCarousel');
        if (!carousel) return;

        // Agregar cursor pointer a las imágenes
        carousel.querySelectorAll('.carousel-item img').forEach((img, index) => {
            img.style.cursor = 'zoom-in';

            // Si no tiene onclick, agregarlo
            if (!img.onclick) {
                img.onclick = function() {
                    if (typeof window.openImageZoom === 'function') {
                        window.openImageZoom(index);
                    } else {
                        console.warn('⚠️ Función openImageZoom no disponible');
                    }
                };
            }
        });

        console.log('✅ Click para zoom configurado en imágenes');
    }

    // Función para verificar y corregir todo
    function applyAllFixes() {
        fixImageCounter();
        fixGalleryButton();
        fixImageZoom();

        console.log('✅ Todos los fixes de galería aplicados');
    }

    // Aplicar fixes después de un pequeño delay
    setTimeout(applyAllFixes, 500);

    // También aplicar cuando el DOM cambie
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.target.id === 'propertyImageCarousel' ||
                mutation.target.classList && mutation.target.classList.contains('property-gallery')) {
                applyAllFixes();
            }
        });
    });

    const galleryContainer = document.querySelector('.property-gallery-container');
    if (galleryContainer) {
        observer.observe(galleryContainer, {
            childList: true,
            subtree: true
        });
    }
});

// Función global para forzar los fixes
window.forceGalleryFix = function() {
    console.log('🔧 Forzando fixes de galería...');

    // Reejecutar todos los fixes
    const event = new Event('DOMContentLoaded');
    document.dispatchEvent(event);
};

console.log('✅ Gallery Fix completamente cargado');
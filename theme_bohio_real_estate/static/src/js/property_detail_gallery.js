/** @odoo-module **/

// Variables globales para el zoom
let currentZoomIndex = 0;
let zoomImages = [];

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎬 Property Detail Gallery JS cargado');

    const carousel = document.getElementById('propertyImageCarousel');
    if (carousel) {
        carousel.addEventListener('slid.bs.carousel', function(e) {
            const currentIndex = Array.from(e.target.querySelectorAll('.carousel-item')).indexOf(e.relatedTarget) + 1;
            const indexElement = document.getElementById('currentImageIndex');
            if (indexElement) {
                indexElement.textContent = currentIndex;
            }
        });

        // Cargar todas las imágenes para el zoom
        const images = carousel.querySelectorAll('.carousel-item img');
        zoomImages = Array.from(images).map(img => img.src);
        console.log('✅ Imágenes cargadas:', zoomImages.length);
    }

    // Inicializar mapa (solo cuando se muestra)
    initializeMap();

    // Navegación con teclado en el zoom
    document.addEventListener('keydown', function(e) {
        const zoomModal = document.getElementById('imageZoomModal');
        if (zoomModal && zoomModal.classList.contains('show')) {
            if (e.key === 'ArrowLeft') {
                navigateZoom(-1);
            } else if (e.key === 'ArrowRight') {
                navigateZoom(1);
            } else if (e.key === 'Escape') {
                $('#imageZoomModal').modal('hide');
            }
        }
    });
});

// ============= FUNCIONES DE GALERÍA =============

// Abrir modal de zoom con la imagen seleccionada
window.openImageZoom = function(index) {
    console.log('🔍 Abriendo zoom, índice:', index);
    currentZoomIndex = index;
    const modalElement = document.getElementById('imageZoomModal');

    if (!modalElement) {
        console.error('❌ Modal de zoom no encontrado');
        return;
    }

    // Actualizar imagen principal
    updateZoomImage();

    // Cargar miniaturas
    loadZoomThumbnails();

    // Usar jQuery para abrir el modal (Bootstrap 5 en Odoo 18)
    $('#imageZoomModal').modal('show');
};

// Actualizar imagen en el zoom
function updateZoomImage() {
    const zoomImage = document.getElementById('zoomImage');
    const zoomIndexSpan = document.getElementById('zoomImageIndex');
    const zoomTotalSpan = document.getElementById('zoomTotalImages');

    if (!zoomImage || !zoomIndexSpan || !zoomTotalSpan) {
        console.error('❌ Elementos del zoom no encontrados');
        return;
    }

    if (zoomImages.length > 0) {
        zoomImage.src = zoomImages[currentZoomIndex];
        zoomIndexSpan.textContent = currentZoomIndex + 1;
        zoomTotalSpan.textContent = zoomImages.length;

        // Mostrar/ocultar botones de navegación
        const prevBtn = document.getElementById('zoomPrevBtn');
        const nextBtn = document.getElementById('zoomNextBtn');

        if (prevBtn) {
            prevBtn.style.display = currentZoomIndex > 0 ? 'block' : 'none';
        }

        if (nextBtn) {
            nextBtn.style.display = currentZoomIndex < zoomImages.length - 1 ? 'block' : 'none';
        }

        // Actualizar miniaturas activas
        updateActiveThumbnail();
    }
}

// Navegar entre imágenes en el zoom
window.navigateZoom = function(direction) {
    currentZoomIndex += direction;

    // Limitar índices
    if (currentZoomIndex < 0) {
        currentZoomIndex = 0;
    }
    if (currentZoomIndex >= zoomImages.length) {
        currentZoomIndex = zoomImages.length - 1;
    }

    updateZoomImage();
};

// Cargar miniaturas en el zoom
function loadZoomThumbnails() {
    const container = document.getElementById('zoomThumbnails');
    if (!container) return;

    let html = '';

    zoomImages.forEach((src, index) => {
        const isActive = index === currentZoomIndex;
        html += `
            <div class="zoom-thumbnail ${isActive ? 'active' : ''}"
                 onclick="jumpToZoomImage(${index})"
                 style="cursor: pointer; opacity: ${isActive ? '1' : '0.6'}; border: ${isActive ? '2px solid white' : '2px solid transparent'}; border-radius: 4px; transition: all 0.3s;">
                <img src="${src}" style="width: 80px; height: 60px; object-fit: cover; border-radius: 4px;" alt="Miniatura ${index + 1}"/>
            </div>
        `;
    });

    container.innerHTML = html;
}

// Saltar a una imagen específica en el zoom
window.jumpToZoomImage = function(index) {
    currentZoomIndex = index;
    updateZoomImage();
};

// Actualizar miniatura activa
function updateActiveThumbnail() {
    const thumbnails = document.querySelectorAll('.zoom-thumbnail');
    thumbnails.forEach((thumb, index) => {
        if (index === currentZoomIndex) {
            thumb.style.opacity = '1';
            thumb.style.border = '2px solid white';
            thumb.classList.add('active');
            // Scroll horizontal para mantener visible
            thumb.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        } else {
            thumb.style.opacity = '0.6';
            thumb.style.border = '2px solid transparent';
            thumb.classList.remove('active');
        }
    });
}

// Abrir modal de galería
window.openGalleryModal = function() {
    console.log('🖼️ Abriendo galería');
    const modalElement = document.getElementById('galleryModal');
    const grid = document.getElementById('galleryGrid');

    if (!modalElement || !grid) {
        console.error('❌ Modal o grid de galería no encontrado');
        return;
    }

    // Obtener todas las imágenes del carrusel
    const images = document.querySelectorAll('#propertyImageCarousel .carousel-item img');
    let html = '';

    images.forEach((img, index) => {
        html += `
            <div class="col-md-4 col-sm-6">
                <div class="position-relative" style="cursor: pointer;" onclick="goToSlide(${index})">
                    <img src="${img.src}" class="img-fluid rounded shadow-sm" style="width: 100%; height: 200px; object-fit: cover;" alt="Imagen ${index + 1}"/>
                    <div class="position-absolute top-0 start-0 m-2 bg-dark text-white px-2 py-1 rounded">
                        ${index + 1}
                    </div>
                </div>
            </div>
        `;
    });

    grid.innerHTML = html;

    // Usar jQuery para abrir el modal (Bootstrap 5 en Odoo 18)
    $('#galleryModal').modal('show');
};

// Ir a una diapositiva específica
window.goToSlide = function(index) {
    const carouselElement = document.getElementById('propertyImageCarousel');
    if (!carouselElement) return;

    // Usar jQuery/Bootstrap para navegar al slide (Bootstrap 5 en Odoo 18)
    $('#propertyImageCarousel').carousel(index);

    // Cerrar el modal de galería
    $('#galleryModal').modal('hide');
};

// Alternar entre imagen y mapa
window.toggleMapView = function() {
    console.log('🗺️ Toggle mapa');
    const mapSection = document.getElementById('mapViewSection');
    const carouselContainer = document.querySelector('.property-gallery-container');

    if (!mapSection || !carouselContainer) return;

    if (mapSection.style.display === 'none' || !mapSection.style.display) {
        mapSection.style.display = 'block';
        carouselContainer.style.display = 'none';

        // Forzar re-renderizado del mapa
        if (window.propertyMap) {
            window.propertyMap.invalidateSize();
        }
        // Si no está inicializado, inicializarlo ahora
        if (typeof window.initPropertyMap === 'function') {
            window.initPropertyMap();
        }
    } else {
        mapSection.style.display = 'none';
        carouselContainer.style.display = 'block';
    }
};

// Inicializar mapa de Leaflet
function initializeMap() {
    const mapElement = document.getElementById('property_map');
    if (!mapElement) return;

    const lat = parseFloat(mapElement.dataset.lat);
    const lng = parseFloat(mapElement.dataset.lng);
    const name = mapElement.dataset.name;

    if (lat && lng) {
        // Solo inicializar cuando se muestre
        window.initPropertyMap = function() {
            if (window.propertyMap) return; // Ya inicializado

            if (typeof L === 'undefined') {
                console.error('❌ Leaflet no está cargado');
                return;
            }

            window.propertyMap = L.map('property_map').setView([lat, lng], 15);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(window.propertyMap);

            L.marker([lat, lng]).addTo(window.propertyMap)
                .bindPopup('<b>' + name + '</b>')
                .openPopup();
        };
    }
}

// ============= FUNCIONES DE COMPARTIR =============

// Abrir modal de compartir
window.openShareModal = function() {
    console.log('📤 Abriendo modal compartir');
    const modalElement = document.getElementById('shareModal');
    if (!modalElement) {
        console.error('❌ Modal de compartir no encontrado');
        return;
    }
    // Usar jQuery para abrir el modal (Bootstrap 5 en Odoo 18)
    $('#shareModal').modal('show');
};

// Copiar link al portapapeles
window.copyToClipboard = function() {
    const linkInput = document.getElementById('propertyShareLink');
    if (!linkInput) return;

    linkInput.select();
    linkInput.setSelectionRange(0, 99999); // Para móviles

    try {
        document.execCommand('copy');
        // Mostrar mensaje de éxito
        const successMsg = document.getElementById('copySuccess');
        if (successMsg) {
            successMsg.style.display = 'block';
            setTimeout(() => {
                successMsg.style.display = 'none';
            }, 3000);
        }
    } catch (err) {
        console.error('Error al copiar:', err);
        alert('No se pudo copiar el link. Por favor cópialo manualmente.');
    }
};

// Compartir por WhatsApp
window.shareOnWhatsApp = function() {
    const linkInput = document.getElementById('propertyShareLink');
    const titleElement = document.querySelector('#shareModal h6');

    if (!linkInput || !titleElement) return;

    const link = linkInput.value;
    const title = titleElement.textContent.trim();
    const text = encodeURIComponent(`¡Mira esta propiedad en BOHIO!\n\n${title}\n\n${link}`);
    window.open(`https://api.whatsapp.com/send?text=${text}`, '_blank');
};

// Compartir en Facebook
window.shareOnFacebook = function() {
    const linkInput = document.getElementById('propertyShareLink');
    if (!linkInput) return;

    const link = linkInput.value;
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(link)}`, '_blank', 'width=600,height=400');
};

// Compartir en Twitter/X
window.shareOnTwitter = function() {
    const linkInput = document.getElementById('propertyShareLink');
    const titleElement = document.querySelector('#shareModal h6');

    if (!linkInput || !titleElement) return;

    const link = linkInput.value;
    const title = titleElement.textContent.trim();
    const text = encodeURIComponent('¡Mira esta propiedad en BOHIO! ' + title);
    const url = 'https://twitter.com/intent/tweet?text=' + text + '&url=' + encodeURIComponent(link);
    window.open(url, '_blank', 'width=600,height=400');
};

// Compartir por Email
window.shareViaEmail = function() {
    const linkInput = document.getElementById('propertyShareLink');
    const titleElement = document.querySelector('#shareModal h6');

    if (!linkInput || !titleElement) return;

    const link = linkInput.value;
    const title = titleElement.textContent.trim();
    const subject = encodeURIComponent('Te comparto esta propiedad de BOHIO: ' + title);
    const body = encodeURIComponent('Hola,\n\nQuiero compartirte esta propiedad que encontré en BOHIO:\n\n' + title + '\n\nPuedes ver más detalles aquí:\n' + link + '\n\nSaludos');
    const mailto = 'mailto:?subject=' + subject + '&body=' + body;
    window.location.href = mailto;
};

// ============= FUNCIONES DE REPORTE/PQRS =============

// Abrir modal de reporte
window.openReportModal = function() {
    console.log('🚩 Abriendo modal de reporte');
    const modalElement = document.getElementById('reportModal');
    if (!modalElement) {
        console.error('❌ Modal de reporte no encontrado');
        return;
    }
    // Usar jQuery para abrir el modal (Bootstrap 5 en Odoo 18)
    $('#reportModal').modal('show');
};

// Enviar reporte (validaciones y proceso)
window.submitReport = function() {
    const form = document.getElementById('reportForm');
    if (!form) return false;

    // Validar campos
    const problemType = form.querySelector('[name="problem_type"]').value;
    const reporterName = form.querySelector('[name="reporter_name"]').value.trim();
    const reporterEmail = form.querySelector('[name="reporter_email"]').value.trim();
    const description = form.querySelector('[name="description"]').value.trim();

    // Validaciones
    if (!problemType) {
        alert('Por favor selecciona el tipo de problema');
        return false;
    }

    if (!reporterName || reporterName.length < 3) {
        alert('Por favor ingresa tu nombre completo');
        return false;
    }

    if (!reporterEmail || !reporterEmail.includes('@')) {
        alert('Por favor ingresa un email válido');
        return false;
    }

    if (description.length < 20) {
        alert('Por favor proporciona una descripción más detallada (mínimo 20 caracteres)');
        return false;
    }

    // Confirmar envío
    if (!confirm('¿Estás seguro de que deseas enviar este reporte?')) {
        return false;
    }

    // Obtener datos
    const propertyId = form.querySelector('[name="property_id"]').value;
    const propertyName = form.querySelector('[name="property_name"]').value;
    const propertyCode = form.querySelector('[name="property_code"]').value;
    const propertyUrl = form.querySelector('[name="property_url"]').value;

    // Crear el cuerpo del email
    const emailSubject = encodeURIComponent('[REPORTE PQRS] ' + (propertyCode || 'Sin código') + ' - ' + propertyName);
    const emailBody = encodeURIComponent(
        'REPORTE DE PROBLEMA CON PROPIEDAD\n' +
        '=====================================\n\n' +
        'DATOS DE LA PROPIEDAD:\n' +
        '- Nombre: ' + propertyName + '\n' +
        '- Código: ' + (propertyCode || 'N/A') + '\n' +
        '- URL: ' + propertyUrl + '\n' +
        '- ID: ' + propertyId + '\n\n' +
        'TIPO DE PROBLEMA:\n' + problemType + '\n\n' +
        'REPORTADO POR:\n' +
        '- Nombre: ' + reporterName + '\n' +
        '- Email: ' + reporterEmail + '\n\n' +
        'DESCRIPCIÓN DEL PROBLEMA:\n' + description + '\n\n' +
        '=====================================\n' +
        'Este reporte fue generado automáticamente desde el sitio web BOHIO.\n' +
        'Fecha: ' + new Date().toLocaleString()
    );

    // Enviar por email (abre cliente de correo)
    const mailtoUrl = 'mailto:reportes@bohio.com?subject=' + emailSubject + '&body=' + emailBody;
    window.location.href = mailtoUrl;

    // Mostrar mensaje de éxito
    setTimeout(function() {
        alert('¡Gracias por tu reporte!\n\nTu correo electrónico se está preparando.\n\nRecibirás una respuesta en las próximas 24-48 horas.');

        // Cerrar modal usando jQuery
        $('#reportModal').modal('hide');

        // Limpiar formulario
        form.reset();
    }, 500);

    return false;
};

console.log('✅ Property Detail Gallery JS completamente cargado');

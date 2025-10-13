/** @odoo-module **/

// Variables globales para el zoom
let currentZoomIndex = 0;
let validImages = [];  // Array de objetos con info de cada imagen

// Placeholder para imágenes que fallan
const PLACEHOLDER_IMAGE = '/theme_bohio_real_estate/static/src/img/banner1.jpg';

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎬 Property Detail Gallery JS cargado');

    const carousel = document.getElementById('propertyImageCarousel');
    if (carousel) {
        // Actualizar contador cuando cambia el slide
        carousel.addEventListener('slid.bs.carousel', function(e) {
            const currentIndex = Array.from(e.target.querySelectorAll('.carousel-item')).indexOf(e.relatedTarget) + 1;
            const indexElement = document.getElementById('currentImageIndex');
            if (indexElement) {
                indexElement.textContent = currentIndex;
            }
        });

        // Recolectar TODAS las imágenes del carrusel (incluyendo las que están en el DOM)
        const carouselItems = carousel.querySelectorAll('.carousel-item');
        validImages = [];

        carouselItems.forEach((item, index) => {
            const img = item.querySelector('img');
            if (img && img.src) {
                // Solo agregar si NO es el placeholder genérico
                const isPlaceholder = img.src.includes('banner1.jpg') &&
                                     img.alt &&
                                     img.alt.includes('Propiedad BOHIO');

                if (!isPlaceholder) {
                    validImages.push({
                        src: img.src,
                        alt: img.alt || `Imagen ${index + 1}`,
                        index: index,
                        element: img
                    });

                    // Agregar manejo de errores inline
                    img.addEventListener('error', function() {
                        console.warn(`⚠️ Error cargando imagen ${index + 1}: ${this.src}`);
                        // Solo reemplazar si no es ya un placeholder
                        if (!this.src.includes('banner1.jpg')) {
                            this.src = PLACEHOLDER_IMAGE;
                            this.style.opacity = '0.7';
                            this.style.filter = 'grayscale(50%)';
                        }
                    });

                    // Cuando se carga correctamente
                    img.addEventListener('load', function() {
                        if (!this.src.includes('banner1.jpg')) {
                            this.style.opacity = '1';
                            this.style.filter = 'none';
                        }
                    });
                }
            }
        });

        console.log(`✅ Total de imágenes válidas encontradas: ${validImages.length}`);
        if (validImages.length === 0) {
            console.warn('⚠️ No se encontraron imágenes válidas en el carrusel');
        }
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

    if (validImages.length > 0 && currentZoomIndex >= 0 && currentZoomIndex < validImages.length) {
        // Mostrar loading mientras carga
        zoomImage.style.opacity = '0.5';
        zoomImage.style.filter = 'blur(5px)';

        // Crear nueva imagen para precargar
        const tempImg = new Image();

        tempImg.onload = function() {
            // Imagen cargada exitosamente
            zoomImage.src = tempImg.src;
            zoomImage.style.opacity = '1';
            zoomImage.style.filter = 'none';
            console.log(`✅ Imagen ${currentZoomIndex + 1} cargada correctamente`);
        };

        tempImg.onerror = function() {
            // Error al cargar imagen
            console.error(`❌ Error cargando imagen ${currentZoomIndex + 1}`);
            zoomImage.src = PLACEHOLDER_IMAGE;
            zoomImage.style.opacity = '0.7';
            zoomImage.style.filter = 'grayscale(50%)';

            // Mostrar alerta sutil
            showImageErrorNotification();
        };

        // Iniciar carga
        tempImg.src = validImages[currentZoomIndex].src;

        // Actualizar contador
        zoomIndexSpan.textContent = currentZoomIndex + 1;
        zoomTotalSpan.textContent = validImages.length;

        // Mostrar/ocultar botones de navegación
        const prevBtn = document.getElementById('zoomPrevBtn');
        const nextBtn = document.getElementById('zoomNextBtn');

        if (prevBtn) {
            prevBtn.style.display = currentZoomIndex > 0 ? 'flex' : 'none';
        }

        if (nextBtn) {
            nextBtn.style.display = currentZoomIndex < validImages.length - 1 ? 'flex' : 'none';
        }

        // Actualizar miniaturas activas
        updateActiveThumbnail();
    } else {
        console.warn('⚠️ Índice de imagen inválido:', currentZoomIndex, 'Total:', validImages.length);
    }
}

// Mostrar notificación de error en imagen
function showImageErrorNotification() {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: rgba(227, 30, 36, 0.95);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 9999;
        font-weight: 600;
        animation: slideInRight 0.3s ease-out;
    `;
    notification.innerHTML = '<i class="bi bi-exclamation-triangle me-2"></i>No se pudo cargar la imagen';

    document.body.appendChild(notification);

    // Remover después de 3 segundos
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Navegar entre imágenes en el zoom
window.navigateZoom = function(direction) {
    currentZoomIndex += direction;

    // Limitar índices
    if (currentZoomIndex < 0) {
        currentZoomIndex = 0;
    }
    if (currentZoomIndex >= validImages.length) {
        currentZoomIndex = validImages.length - 1;
    }

    updateZoomImage();
};

// Cargar miniaturas en el zoom con manejo de errores
function loadZoomThumbnails() {
    const container = document.getElementById('zoomThumbnails');
    if (!container) return;

    container.innerHTML = ''; // Limpiar primero

    validImages.forEach((imgData, index) => {
        const isActive = index === currentZoomIndex;

        // Crear contenedor de miniatura
        const thumbDiv = document.createElement('div');
        thumbDiv.className = `zoom-thumbnail ${isActive ? "active" : ""}`;
        thumbDiv.onclick = () => window.jumpToZoomImage(index);
        thumbDiv.style.cssText = `
            cursor: pointer;
            opacity: ${isActive ? 1 : 0.6};
            border: ${isActive ? "2px solid white" : "2px solid transparent"};
            border-radius: 4px;
            transition: all 0.3s;
            position: relative;
            width: 80px;
            height: 60px;
            background: #333;
        `;

        // Crear imagen de miniatura
        const thumbImg = document.createElement('img');
        thumbImg.src = imgData.src;
        thumbImg.alt = imgData.alt;
        thumbImg.style.cssText = 'width: 100%; height: 100%; object-fit: cover; border-radius: 4px;';

        // Manejo de error en miniatura
        thumbImg.onerror = function() {
            console.warn(`⚠️ Error en miniatura ${index + 1}`);
            // Mostrar placeholder en miniatura
            thumbImg.src = PLACEHOLDER_IMAGE;
            thumbImg.style.opacity = '0.5';
            thumbImg.style.filter = 'grayscale(100%)';
        };

        // Loading en miniatura
        thumbImg.onload = function() {
            thumbImg.style.opacity = '1';
        };

        thumbDiv.appendChild(thumbImg);
        container.appendChild(thumbDiv);
    });
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
    console.log('🗺️ Toggle mapa - START');
    const mapSection = document.getElementById('mapViewSection');
    const carouselContainer = document.querySelector('.property-gallery-container');

    console.log('  - mapSection:', mapSection ? 'OK' : 'NO ENCONTRADO');
    console.log('  - carouselContainer:', carouselContainer ? 'OK' : 'NO ENCONTRADO');

    if (!mapSection || !carouselContainer) {
        console.error('❌ Elementos de mapa/carrusel no encontrados');
        return;
    }

    if (mapSection.style.display === 'none' || !mapSection.style.display) {
        console.log('  - Mostrando mapa, ocultando carrusel');
        mapSection.style.display = 'block';
        carouselContainer.style.display = 'none';

        // Esperar a que el DOM se actualice antes de inicializar
        setTimeout(() => {
            console.log('  - Verificando Leaflet:', typeof L !== 'undefined' ? 'Cargado' : 'NO CARGADO');

            if (window.propertyMap) {
                console.log('  - Mapa ya existe, invalidando tamaño');
                window.propertyMap.invalidateSize();
            } else if (typeof window.initPropertyMap === 'function') {
                console.log('  - Inicializando mapa por primera vez');
                window.initPropertyMap();

                // Forzar resize después de crear
                setTimeout(() => {
                    if (window.propertyMap) {
                        console.log('  - Forzando resize del mapa');
                        window.propertyMap.invalidateSize();
                    }
                }, 200);
            } else {
                console.error('❌ initPropertyMap no está definida');
            }
        }, 150);
    } else {
        console.log('  - Ocultando mapa, mostrando carrusel');
        mapSection.style.display = 'none';
        carouselContainer.style.display = 'block';
    }

    console.log('🗺️ Toggle mapa - END');
};

// Inicializar mapa de Leaflet
function initializeMap() {
    const mapElement = document.getElementById('property_map');
    if (!mapElement) {
        console.log('  - Elemento property_map NO encontrado');
        return;
    }

    const lat = parseFloat(mapElement.dataset.lat);
    const lng = parseFloat(mapElement.dataset.lng);
    const name = mapElement.dataset.name || 'Propiedad';

    console.log('  - Datos del mapa:', { lat, lng, name });

    if (!lat || !lng || isNaN(lat) || isNaN(lng)) {
        console.warn('❌ Coordenadas inválidas:', { lat, lng });
        return;
    }

    // Definir función de inicialización del mapa
    window.initPropertyMap = function() {
        if (window.propertyMap) {
            console.log('  - Mapa ya existe, solo invalidando tamaño');
            setTimeout(() => {
                window.propertyMap.invalidateSize();
            }, 100);
            return;
        }

        if (typeof L === 'undefined') {
            console.error('❌ Leaflet no está cargado');
            return;
        }

        console.log('  - Creando mapa Leaflet con lat:', lat, 'lng:', lng);

        try {
            // Crear mapa
            window.propertyMap = L.map('property_map', {
                center: [lat, lng],
                zoom: 15,
                scrollWheelZoom: true
            });

            // Agregar tiles
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19
            }).addTo(window.propertyMap);

            // Crear marcador personalizado con Bootstrap Icons
            const markerHtml = `
                <div class="property-detail-marker">
                    <div class="marker-icon-circle">
                        <i class="bi bi-house-fill"></i>
                    </div>
                    <div class="marker-label">${name}</div>
                </div>
            `;

            const icon = L.divIcon({
                className: 'property-detail-marker-container',
                html: markerHtml,
                iconSize: [null, null],
                iconAnchor: [60, 70]
            });

            // Agregar marcador con icono personalizado
            const marker = L.marker([lat, lng], { icon: icon }).addTo(window.propertyMap);

            // Popup con información detallada
            const popupContent = `
                <div class="property-marker-popup">
                    <h6><i class="bi bi-house-fill text-danger me-2"></i>${name}</h6>
                    <p class="small mb-1">
                        <i class="bi bi-geo-alt-fill text-danger me-1"></i>
                        <strong>Coordenadas:</strong>
                    </p>
                    <p class="small mb-0 text-muted">
                        Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}
                    </p>
                </div>
            `;

            marker.bindPopup(popupContent).openPopup();

            console.log('✅ Mapa creado exitosamente');

            // Forzar recálculo de tamaño después de un momento
            setTimeout(() => {
                if (window.propertyMap) {
                    window.propertyMap.invalidateSize();
                    console.log('  - Tamaño del mapa recalculado');
                }
            }, 200);

        } catch (error) {
            console.error('❌ Error al crear mapa:', error);
        }
    };

    console.log('✅ Función initPropertyMap definida');
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
    const priceElement = document.querySelector('.property-price');
    const locationElement = document.querySelector('.property-location');

    if (!linkInput || !titleElement) return;

    const link = linkInput.value;
    const title = titleElement.textContent.trim();
    const price = priceElement ? priceElement.textContent.trim() : '';
    const location = locationElement ? locationElement.textContent.trim() : '';

    let message = `🏠 *¡Mira esta propiedad en BOHIO!*\n\n`;
    message += `📌 ${title}\n\n`;
    if (price) message += `💰 ${price}\n`;
    if (location) message += `📍 ${location}\n`;
    message += `\n🔗 Ver detalles: ${link}\n\n`;
    message += `_Encuentra tu hogar ideal con BOHIO Inmobiliaria_`;

    const text = encodeURIComponent(message);
    window.open(`https://api.whatsapp.com/send?text=${text}`, '_blank');
};

// Compartir en Facebook
window.shareOnFacebook = function() {
    const linkInput = document.getElementById('propertyShareLink');
    const titleElement = document.querySelector('#shareModal h6');

    if (!linkInput) return;

    const link = linkInput.value;
    const title = titleElement ? titleElement.textContent.trim() : '';

    // Facebook sharer con quote (descripción)
    const quote = encodeURIComponent(`🏠 ${title} - Encuentra tu hogar ideal con BOHIO Inmobiliaria`);
    const url = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(link)}&quote=${quote}`;

    window.open(url, '_blank', 'width=600,height=400');
};

// Compartir en Twitter/X
window.shareOnTwitter = function() {
    const linkInput = document.getElementById('propertyShareLink');
    const titleElement = document.querySelector('#shareModal h6');
    const priceElement = document.querySelector('.property-price');

    if (!linkInput || !titleElement) return;

    const link = linkInput.value;
    const title = titleElement.textContent.trim();
    const price = priceElement ? priceElement.textContent.trim() : '';

    // Crear tweet con emojis y hashtags
    let tweetText = `🏠 ${title}\n`;
    if (price) tweetText += `💰 ${price}\n`;
    tweetText += `\n📍 #BohioInmobiliaria #PropiedadesEnVenta #BienesRaices`;

    const text = encodeURIComponent(tweetText);
    const url = `https://twitter.com/intent/tweet?text=${text}&url=${encodeURIComponent(link)}`;

    window.open(url, '_blank', 'width=600,height=400');
};

// Compartir por Email
window.shareViaEmail = function() {
    const linkInput = document.getElementById('propertyShareLink');
    const titleElement = document.querySelector('#shareModal h6');
    const priceElement = document.querySelector('.property-price');
    const locationElement = document.querySelector('.property-location');

    if (!linkInput || !titleElement) return;

    const link = linkInput.value;
    const title = titleElement.textContent.trim();
    const price = priceElement ? priceElement.textContent.trim() : '';
    const location = locationElement ? locationElement.textContent.trim() : '';

    const subject = encodeURIComponent(`🏠 Te comparto esta propiedad de BOHIO: ${title}`);

    let emailBody = 'Hola,\n\n';
    emailBody += 'Quiero compartirte esta propiedad que encontré en BOHIO Inmobiliaria:\n\n';
    emailBody += '====================================\n';
    emailBody += `📌 PROPIEDAD: ${title}\n`;
    if (price) emailBody += `💰 PRECIO: ${price}\n`;
    if (location) emailBody += `📍 UBICACIÓN: ${location}\n`;
    emailBody += '====================================\n\n';
    emailBody += `🔗 Ver detalles completos:\n${link}\n\n`;
    emailBody += '---\n';
    emailBody += 'BOHIO Inmobiliaria\n';
    emailBody += 'Tu hogar ideal te está esperando\n';
    emailBody += 'www.bohio.com';

    const body = encodeURIComponent(emailBody);
    const mailto = `mailto:?subject=${subject}&body=${body}`;
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

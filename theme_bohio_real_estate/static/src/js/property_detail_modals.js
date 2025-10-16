/**
 * ============================================================================
 * BOHÍO PROPERTY DETAIL MODALS
 * ============================================================================
 * Funciones GLOBALES para modales de compartir y reportar en detalle de propiedad
 * IMPORTANTE: NO ES MÓDULO DE ODOO - Script legacy para acceso desde onclick
 */

// ============================================================================
// MODAL DE COMPARTIR
// ============================================================================

/**
 * Abrir modal de compartir
 */
window.openShareModal = function() {
    const modalEl = document.getElementById('shareModal');
    if (!modalEl) {
        console.warn('Modal de compartir no encontrado');
        return;
    }

    const modal = new bootstrap.Modal(modalEl);
    modal.show();
};

/**
 * Copiar link al portapapeles usando Clipboard API moderna
 * Requiere HTTPS o localhost
 */
window.copyToClipboard = async function() {
    const linkInput = document.getElementById('propertyShareLink');
    if (!linkInput) {
        console.error('Campo de enlace no encontrado');
        return;
    }

    // Verificar si Clipboard API está disponible
    if (!navigator.clipboard) {
        console.error('Clipboard API no disponible. Requiere HTTPS o localhost.');
        alert('La función de copiar requiere una conexión segura (HTTPS).');
        return;
    }

    try {
        // Copiar usando Clipboard API moderna
        await navigator.clipboard.writeText(linkInput.value);

        // Mostrar mensaje de éxito
        const successMsg = document.getElementById('copySuccess');
        if (successMsg) {
            successMsg.style.display = 'block';
            setTimeout(() => {
                successMsg.style.display = 'none';
            }, 3000);
        }

        console.log('Enlace copiado al portapapeles');
    } catch (err) {
        console.error('Error al copiar:', err);
        alert('No se pudo copiar el enlace. Por favor, cópialo manualmente.');
    }
};

/**
 * Compartir en WhatsApp
 */
window.shareOnWhatsApp = function() {
    const linkInput = document.getElementById('propertyShareLink');
    if (!linkInput) return;

    const url = linkInput.value;
    const text = document.querySelector('.property-detail-page h1')?.textContent || 'Propiedad';
    const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(text + ' - ' + url)}`;

    window.open(whatsappUrl, '_blank');
};

/**
 * Compartir en Facebook
 */
window.shareOnFacebook = function() {
    const linkInput = document.getElementById('propertyShareLink');
    if (!linkInput) return;

    const url = linkInput.value;
    const facebookUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`;

    window.open(facebookUrl, '_blank', 'width=600,height=400');
};

/**
 * Compartir en Twitter/X
 */
window.shareOnTwitter = function() {
    const linkInput = document.getElementById('propertyShareLink');
    if (!linkInput) return;

    const url = linkInput.value;
    const text = document.querySelector('.property-detail-page h1')?.textContent || 'Propiedad';
    const twitterUrl = `https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`;

    window.open(twitterUrl, '_blank', 'width=600,height=400');
};

/**
 * Compartir por Email
 */
window.shareViaEmail = function() {
    const linkInput = document.getElementById('propertyShareLink');
    if (!linkInput) return;

    const url = linkInput.value;
    const subject = document.querySelector('.property-detail-page h1')?.textContent || 'Propiedad';
    const body = `Te comparto esta propiedad que puede interesarte:\n\n${url}`;

    window.location.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
};

// ============================================================================
// MODAL DE REPORTAR
// ============================================================================

/**
 * Abrir modal de reportar
 */
window.openReportModal = function() {
    const modalEl = document.getElementById('reportModal');
    if (!modalEl) {
        console.warn('Modal de reportar no encontrado');
        return;
    }

    const modal = new bootstrap.Modal(modalEl);
    modal.show();
};

/**
 * Enviar reporte
 */
window.submitReport = async function() {
    const form = document.getElementById('reportForm');
    if (!form) return;

    // Validar formulario
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    // Recopilar datos
    const formData = new FormData(form);
    const reportData = {
        property_id: formData.get('property_id'),
        property_name: formData.get('property_name'),
        property_code: formData.get('property_code'),
        property_url: formData.get('property_url'),
        problem_type: formData.get('problem_type'),
        reporter_name: formData.get('reporter_name'),
        reporter_email: formData.get('reporter_email'),
        description: formData.get('description')
    };

    // Validar descripción mínima
    if (reportData.description.length < 20) {
        alert('La descripción debe tener al menos 20 caracteres');
        return;
    }

    try {
        // Mostrar loading
        const submitBtn = document.querySelector('#reportModal button[onclick="submitReport()"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-1"></i>Enviando...';

        // Enviar a Odoo (puedes personalizar el endpoint)
        const response = await fetch('/property/report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(reportData)
        });

        if (response.ok) {
            // Éxito
            alert('Reporte enviado exitosamente. Gracias por ayudarnos a mejorar.');

            // Cerrar modal
            const modalEl = document.getElementById('reportModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();

            // Limpiar formulario
            form.reset();
        } else {
            throw new Error('Error al enviar reporte');
        }

        // Restaurar botón
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;

    } catch (error) {
        console.error('Error al enviar reporte:', error);
        alert('Error al enviar el reporte. Por favor intenta de nuevo.');

        // Restaurar botón
        const submitBtn = document.querySelector('#reportModal button[onclick="submitReport()"]');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="bi bi-send me-1"></i>Enviar Reporte';
    }
};

// ============================================================================
// TOGGLE MAP VIEW
// ============================================================================

/**
 * Toggle entre imagen y mapa
 */
window.toggleMapView = function() {
    const mapSection = document.getElementById('mapViewSection');
    const carouselContainer = document.querySelector('.property-gallery-container');

    if (!mapSection || !carouselContainer) {
        console.error('Elementos de mapa/carrusel no encontrados');
        return;
    }

    if (mapSection.style.display === 'none' || !mapSection.style.display) {
        // Mostrar mapa
        mapSection.style.display = 'block';
        carouselContainer.style.display = 'none';

        // Inicializar mapa si existe instancia global
        setTimeout(() => {
            if (window.propertyMapInstance) {
                window.propertyMapInstance.initializeMap();
            }
        }, 100);
    } else {
        // Ocultar mapa
        mapSection.style.display = 'none';
        carouselContainer.style.display = 'block';
    }
};

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

console.log('Property Detail Modals cargado');

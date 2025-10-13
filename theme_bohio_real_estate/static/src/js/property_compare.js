/** @odoo-module **/

/**
 * BOHIO Property Comparison System
 * Sistema de comparación de propiedades con almacenamiento en localStorage
 */

// Almacenamiento de propiedades para comparar
const COMPARE_STORAGE_KEY = 'bohio_compare_properties';
const MAX_COMPARE_PROPERTIES = 4;

/**
 * Obtener propiedades en comparación desde localStorage
 */
export function getCompareProperties() {
    const stored = localStorage.getItem(COMPARE_STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
}

/**
 * Guardar propiedades en comparación en localStorage
 */
function saveCompareProperties(properties) {
    localStorage.setItem(COMPARE_STORAGE_KEY, JSON.stringify(properties));
    updateCompareCounter();
}

/**
 * Agregar propiedad a comparación
 */
window.togglePropertyCompare = function(propertyId, propertyName, propertyImage, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    let properties = getCompareProperties();
    const existingIndex = properties.findIndex(p => p.id === propertyId);

    if (existingIndex !== -1) {
        // Remover de comparación
        properties.splice(existingIndex, 1);
        showToast('Propiedad removida de la comparación', 'info');
    } else {
        // Verificar límite
        if (properties.length >= MAX_COMPARE_PROPERTIES) {
            showToast(`Solo puedes comparar hasta ${MAX_COMPARE_PROPERTIES} propiedades`, 'warning');
            return;
        }

        // Agregar a comparación
        properties.push({
            id: propertyId,
            name: propertyName,
            image: propertyImage,
            addedAt: new Date().toISOString()
        });
        showToast('Propiedad agregada para comparar', 'success');
    }

    saveCompareProperties(properties);

    // Actualizar botón
    updateCompareButton(propertyId);
};

/**
 * Verificar si una propiedad está en comparación
 */
window.isPropertyInCompare = function(propertyId) {
    const properties = getCompareProperties();
    return properties.some(p => p.id === propertyId);
};

/**
 * Actualizar botón de comparación
 */
function updateCompareButton(propertyId) {
    const buttons = document.querySelectorAll(`.compare-btn[onclick*="${propertyId}"]`);

    buttons.forEach(btn => {
        const icon = btn.querySelector('i');
        const text = btn.querySelector('.compare-text');
        const isInCompare = isPropertyInCompare(propertyId);

        if (isInCompare) {
            icon.className = 'bi bi-check-circle text-success me-1';
            text.textContent = 'En comparación';
            btn.classList.add('active');
        } else {
            icon.className = 'bi bi-plus-circle text-danger me-1';
            text.textContent = 'Comparar';
            btn.classList.remove('active');
        }
    });
}

/**
 * Actualizar contador de comparación
 */
function updateCompareCounter() {
    const properties = getCompareProperties();
    const counter = document.getElementById('compareCounter');
    const button = document.getElementById('compareFloatingBtn');

    if (counter) {
        counter.textContent = properties.length;
        counter.style.display = properties.length > 0 ? 'block' : 'none';
    }

    if (button) {
        button.style.display = properties.length > 0 ? 'block' : 'none';
    }
}

/**
 * Abrir modal de comparación
 */
window.openCompareModal = function() {
    const properties = getCompareProperties();

    if (properties.length < 2) {
        showToast('Debes seleccionar al menos 2 propiedades para comparar', 'warning');
        return;
    }

    // Redirigir a página de comparación
    const ids = properties.map(p => p.id).join(',');
    window.location.href = `/properties/compare?ids=${ids}`;
};

/**
 * Limpiar comparación
 */
window.clearCompare = function() {
    if (confirm('¿Estás seguro de limpiar todas las propiedades seleccionadas?')) {
        localStorage.removeItem(COMPARE_STORAGE_KEY);
        updateCompareCounter();
        showToast('Comparación limpiada', 'info');

        // Actualizar todos los botones
        document.querySelectorAll('.compare-btn').forEach(btn => {
            const icon = btn.querySelector('i');
            const text = btn.querySelector('.compare-text');
            icon.className = 'bi bi-plus-circle text-danger me-1';
            text.textContent = 'Comparar';
            btn.classList.remove('active');
        });
    }
};

/**
 * Mostrar notificación toast
 */
function showToast(message, type = 'info') {
    // Crear toast
    const toastId = 'toast-' + Date.now();
    const bgClass = {
        success: 'bg-success',
        warning: 'bg-warning',
        info: 'bg-info',
        danger: 'bg-danger'
    }[type] || 'bg-info';

    const iconClass = {
        success: 'fa-check-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle',
        danger: 'fa-times-circle'
    }[type] || 'fa-info-circle';

    const toastHTML = `
        <div id="${toastId}" class="toast-bohio ${bgClass} text-white" style="position: fixed; bottom: 20px; right: 20px; z-index: 9999; min-width: 300px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); animation: slideInRight 0.3s ease;">
            <div class="d-flex align-items-center p-3">
                <i class="fa ${iconClass} me-3" style="font-size: 24px;"></i>
                <div class="flex-grow-1">${message}</div>
                <button class="btn-close btn-close-white ms-3" onclick="document.getElementById('${toastId}').remove()"></button>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', toastHTML);

    // Auto-remover después de 3 segundos
    setTimeout(() => {
        const toast = document.getElementById(toastId);
        if (toast) {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }
    }, 3000);
}

// Inicializar al cargar el DOM
document.addEventListener('DOMContentLoaded', function() {
    updateCompareCounter();

    // Agregar animaciones CSS
    if (!document.getElementById('bohio-compare-animations')) {
        const style = document.createElement('style');
        style.id = 'bohio-compare-animations';
        style.textContent = `
            @keyframes slideInRight {
                from { transform: translateX(400px); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOutRight {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(400px); opacity: 0; }
            }
            .compare-btn.active {
                background-color: #E8F5E9 !important;
                border-color: #4CAF50 !important;
            }
        `;
        document.head.appendChild(style);
    }
});

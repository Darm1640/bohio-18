/** @odoo-module **/

/**
 * Fix para la paginación del property shop
 * Asegura que la paginación se renderice correctamente
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Pagination Fix cargado');

    // Función para verificar y corregir la paginación
    function fixPagination() {
        const container = document.getElementById('paginationContainer');

        if (!container) {
            console.log('No se encontró el contenedor de paginación');
            return;
        }

        // Si el contenedor está vacío y hay datos de paginación
        if (container.innerHTML.trim() === '') {
            console.log('⚠️ Contenedor de paginación vacío. Intentando renderizar...');

            // Buscar si hay instancia del PropertyShop
            if (window.propertyShop && typeof window.propertyShop.renderPagination === 'function') {
                console.log('✅ Renderizando paginación desde PropertyShop');
                window.propertyShop.renderPagination();
            } else {
                console.log('❌ No se encontró instancia de PropertyShop');

                // Renderizado básico de emergencia
                renderBasicPagination(container);
            }
        }
    }

    // Renderizado básico de paginación
    function renderBasicPagination(container) {
        // Obtener datos de la URL
        const urlParams = new URLSearchParams(window.location.search);
        const currentPage = parseInt(urlParams.get('page')) || 1;

        // Obtener total de elementos del contador si existe
        const counterElement = document.querySelector('.property-counter');
        let totalItems = 0;

        if (counterElement) {
            const match = counterElement.textContent.match(/\d+/);
            if (match) {
                totalItems = parseInt(match[0]);
            }
        }

        if (totalItems === 0) {
            // Contar las propiedades visibles
            const propertyCards = document.querySelectorAll('.property-card, .bohio-property-card');
            totalItems = propertyCards.length;
        }

        const itemsPerPage = 40;
        const totalPages = Math.ceil(totalItems / itemsPerPage);

        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        console.log(`📄 Renderizando paginación: Página ${currentPage}/${totalPages}, Total: ${totalItems}`);

        let html = '<nav aria-label="Paginación de propiedades"><ul class="pagination justify-content-center">';

        // Botón anterior
        html += `
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="?page=${currentPage - 1}" aria-label="Anterior">
                    <span aria-hidden="true">&laquo;</span>
                </a>
            </li>
        `;

        // Páginas numeradas
        const maxButtons = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
        let endPage = Math.min(totalPages, startPage + maxButtons - 1);

        if (endPage - startPage < maxButtons - 1) {
            startPage = Math.max(1, endPage - maxButtons + 1);
        }

        // Primera página si no está visible
        if (startPage > 1) {
            html += `<li class="page-item"><a class="page-link" href="?page=1">1</a></li>`;
            if (startPage > 2) {
                html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }

        // Páginas del rango
        for (let i = startPage; i <= endPage; i++) {
            html += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="?page=${i}">${i}</a>
                </li>
            `;
        }

        // Última página si no está visible
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
            html += `<li class="page-item"><a class="page-link" href="?page=${totalPages}">${totalPages}</a></li>`;
        }

        // Botón siguiente
        html += `
            <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="?page=${currentPage + 1}" aria-label="Siguiente">
                    <span aria-hidden="true">&raquo;</span>
                </a>
            </li>
        `;

        html += '</ul></nav>';

        // Info de resultados
        const start = ((currentPage - 1) * itemsPerPage) + 1;
        const end = Math.min(currentPage * itemsPerPage, totalItems);

        html += `
            <div class="text-center mt-3 text-muted small">
                Mostrando ${start} a ${end} de ${totalItems} propiedades
            </div>
        `;

        container.innerHTML = html;

        // Agregar eventos de click
        container.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', function(e) {
                if (this.parentElement.classList.contains('disabled')) {
                    e.preventDefault();
                    return;
                }

                // Si tiene href válido, dejar que navegue normalmente
                if (this.href && !this.href.includes('#')) {
                    return;
                }

                e.preventDefault();
                const page = this.href.match(/page=(\d+)/);
                if (page && page[1]) {
                    const newPage = parseInt(page[1]);
                    updatePage(newPage);
                }
            });
        });
    }

    // Función para actualizar la página
    function updatePage(page) {
        const url = new URL(window.location);
        url.searchParams.set('page', page);

        // Si existe PropertyShop, usar su método
        if (window.propertyShop && typeof window.propertyShop.goToPage === 'function') {
            window.propertyShop.goToPage(page);
        } else {
            // Navegación básica
            window.location.href = url.toString();
        }
    }

    // Ejecutar el fix después de un pequeño delay
    setTimeout(fixPagination, 1000);

    // También ejecutar cuando cambie el contenido dinámicamente
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.target.id === 'propertyResults' ||
                mutation.target.classList.contains('property-grid')) {
                setTimeout(fixPagination, 500);
            }
        });
    });

    // Observar cambios en el contenedor de resultados
    const resultsContainer = document.getElementById('propertyResults');
    if (resultsContainer) {
        observer.observe(resultsContainer, {
            childList: true,
            subtree: true
        });
    }
});

// Función global para forzar el renderizado de la paginación
window.forcePaginationRender = function() {
    const event = new CustomEvent('renderPagination');
    document.dispatchEvent(event);

    // También intentar el fix directamente
    const container = document.getElementById('paginationContainer');
    if (container && window.propertyShop) {
        window.propertyShop.renderPagination();
    }
};

console.log('✅ Pagination Fix completamente cargado');

export default {
    fixPagination: function() {
        window.forcePaginationRender();
    }
};
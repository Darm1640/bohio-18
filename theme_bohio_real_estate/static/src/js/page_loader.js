/** @odoo-module **/

/**
 * BOHIO Page Loader
 * Muestra pantalla de carga con logo al cargar la página
 */

document.addEventListener('DOMContentLoaded', function() {
    // Esperar a que todo el contenido esté cargado
    window.addEventListener('load', function() {
        const loader = document.getElementById('bohio-page-loader');

        if (loader) {
            // Ocultar loader después de 1 segundo
            setTimeout(() => {
                loader.classList.add('hidden');

                // Eliminar del DOM después de la animación
                setTimeout(() => {
                    loader.remove();
                }, 500);
            }, 1000);
        }
    });
});

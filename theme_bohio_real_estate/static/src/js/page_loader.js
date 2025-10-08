/** @odoo-module **/

/**
 * BOHIO Page Loader
 * Muestra pantalla de carga con logo al cargar la página
 */

(function() {
    console.log('BOHIO Loader: Script cargado');

    function hideLoader() {
        const loader = document.getElementById('bohio-page-loader');
        console.log('BOHIO Loader: Intentando ocultar loader', loader ? 'encontrado' : 'NO encontrado');

        if (loader) {
            console.log('BOHIO Loader: Ocultando en 500ms...');
            // Ocultar loader después de 500ms
            setTimeout(() => {
                loader.classList.add('hidden');
                console.log('BOHIO Loader: Clase hidden agregada');

                // Eliminar del DOM después de la animación
                setTimeout(() => {
                    if (loader.parentNode) {
                        loader.remove();
                        console.log('BOHIO Loader: Removido del DOM');
                    }
                }, 500);
            }, 500);
        }
    }

    // Intentar ocultar cuando DOMContentLoaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', hideLoader);
    } else {
        // DOM ya cargado
        hideLoader();
    }

    // Backup: ocultar en window.load si no se ha ocultado
    window.addEventListener('load', function() {
        const loader = document.getElementById('bohio-page-loader');
        if (loader && !loader.classList.contains('hidden')) {
            console.log('BOHIO Loader: Forzando ocultar desde window.load');
            hideLoader();
        }
    });

    // Fallback de seguridad: forzar ocultar después de 3 segundos máximo
    setTimeout(() => {
        const loader = document.getElementById('bohio-page-loader');
        if (loader && !loader.classList.contains('hidden')) {
            console.warn('BOHIO Loader: Timeout alcanzado, forzando ocultar');
            loader.classList.add('hidden');
            setTimeout(() => {
                if (loader.parentNode) {
                    loader.remove();
                }
            }, 500);
        }
    }, 3000);
})();

/** @odoo-module **/
/**
 * Bohío Real Estate - Properties Shop
 * JavaScript para la página de listado/tienda de propiedades
 */

document.addEventListener('DOMContentLoaded', function() {
    // Solo ejecutar si estamos en la página de properties shop
    if (!document.querySelector('.properties-shop, .oe_product')) return;

    console.log('Properties Shop - Initialized');

    // Inicializar filtros
    initFilters();

    // Inicializar vista grid/list toggle
    initViewToggle();

    // Inicializar ordenamiento
    initSorting();
});

/**
 * Inicializar filtros de propiedades
 */
function initFilters() {
    const filterForm = document.querySelector('.property-filters-form, .search-form');
    if (!filterForm) return;

    // Aplicar filtros automáticamente al cambiar selects
    const selects = filterForm.querySelectorAll('select');
    selects.forEach(select => {
        select.addEventListener('change', function() {
            filterForm.submit();
        });
    });

    // Limpiar filtros
    const clearBtn = document.querySelector('.clear-filters-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', function(e) {
            e.preventDefault();
            selects.forEach(select => select.value = '');
            const inputs = filterForm.querySelectorAll('input[type="number"], input[type="text"]');
            inputs.forEach(input => input.value = '');
            filterForm.submit();
        });
    }
}

/**
 * Toggle entre vista grid y lista
 */
function initViewToggle() {
    const gridBtn = document.querySelector('.view-grid-btn');
    const listBtn = document.querySelector('.view-list-btn');
    const container = document.querySelector('.properties-grid, .products-grid');

    if (!gridBtn || !listBtn || !container) return;

    gridBtn.addEventListener('click', function() {
        container.classList.remove('view-list');
        container.classList.add('view-grid');
        gridBtn.classList.add('active');
        listBtn.classList.remove('active');
        localStorage.setItem('properties_view', 'grid');
    });

    listBtn.addEventListener('click', function() {
        container.classList.remove('view-grid');
        container.classList.add('view-list');
        listBtn.classList.add('active');
        gridBtn.classList.remove('active');
        localStorage.setItem('properties_view', 'list');
    });

    // Restaurar vista guardada
    const savedView = localStorage.getItem('properties_view');
    if (savedView === 'list') {
        listBtn.click();
    }
}

/**
 * Inicializar ordenamiento
 */
function initSorting() {
    const sortSelect = document.querySelector('select[name="order"]');
    if (!sortSelect) return;

    sortSelect.addEventListener('change', function() {
        const form = this.closest('form');
        if (form) {
            form.submit();
        } else {
            // Si no hay form, redirigir con parámetro
            const currentUrl = new URL(window.location.href);
            currentUrl.searchParams.set('order', this.value);
            window.location.href = currentUrl.toString();
        }
    });
}

/**
 * Mostrar más propiedades (scroll infinito - opcional)
 */
function initInfiniteScroll() {
    const loadMoreBtn = document.querySelector('.load-more-properties');
    if (!loadMoreBtn) return;

    let loading = false;

    loadMoreBtn.addEventListener('click', async function(e) {
        e.preventDefault();
        if (loading) return;

        loading = true;
        this.classList.add('loading');

        const nextPage = this.dataset.nextPage;
        if (!nextPage) return;

        try {
            const response = await fetch(nextPage);
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            // Agregar nuevas propiedades
            const newProperties = doc.querySelectorAll('.property-card');
            const container = document.querySelector('.properties-grid');
            newProperties.forEach(prop => container.appendChild(prop));

            // Actualizar botón
            const newLoadMoreBtn = doc.querySelector('.load-more-properties');
            if (newLoadMoreBtn) {
                this.dataset.nextPage = newLoadMoreBtn.dataset.nextPage;
            } else {
                this.remove();
            }
        } catch (error) {
            console.error('Error loading more properties:', error);
        } finally {
            loading = false;
            this.classList.remove('loading');
        }
    });
}

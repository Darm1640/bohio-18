/* ========================================
   BOHIO Real Estate - JavaScript Personalizado
   ======================================== */

(function() {
    'use strict';

    // ---- Configuración de modo oscuro ----
    const DarkModeManager = {
        init: function() {
            this.setupDarkModeToggle();
            this.applySavedTheme();
        },

        setupDarkModeToggle: function() {
            // Crear botón de modo oscuro si no existe
            if (!document.getElementById('darkModeToggle')) {
                const toggle = document.createElement('button');
                toggle.id = 'darkModeToggle';
                toggle.className = 'btn btn-sm btn-outline-secondary position-fixed';
                toggle.style.cssText = 'bottom: 20px; right: 20px; z-index: 1000; border-radius: 50%; width: 50px; height: 50px;';
                toggle.innerHTML = '<i class="fa fa-moon"></i>';
                toggle.setAttribute('aria-label', 'Toggle dark mode');
                document.body.appendChild(toggle);

                toggle.addEventListener('click', () => this.toggleDarkMode());
            }
        },

        toggleDarkMode: function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('bohio-theme', newTheme);
            
            this.updateToggleIcon(newTheme);
        },

        applySavedTheme: function() {
            const savedTheme = localStorage.getItem('bohio-theme');
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            const theme = savedTheme || (prefersDark ? 'dark' : 'light');
            
            document.documentElement.setAttribute('data-theme', theme);
            this.updateToggleIcon(theme);
        },

        updateToggleIcon: function(theme) {
            const toggle = document.getElementById('darkModeToggle');
            if (toggle) {
                const icon = toggle.querySelector('i');
                icon.className = theme === 'dark' ? 'fa fa-sun' : 'fa fa-moon';
            }
        }
    };

    // ---- Gestión de búsqueda de propiedades ----
    const PropertySearch = {
        init: function() {
            this.setupPriceSync();
            this.setupCodeSearch();
            this.setupFilterPersistence();
            this.setupLazyLoading();
        },

        setupPriceSync: function() {
            const priceMin = document.getElementById('price_min');
            const priceMax = document.getElementById('price_max');

            if (priceMin && priceMax) {
                const syncPrices = (source, target) => {
                    const sourceValue = parseFloat(source.value) || 0;
                    const targetValue = parseFloat(target.value) || 0;

                    if (sourceValue > 0 && targetValue === 0) {
                        target.value = sourceValue;
                    }
                };

                const validateRange = (min, max) => {
                    const minValue = parseFloat(min.value) || 0;
                    const maxValue = parseFloat(max.value) || 0;

                    if (minValue > 0 && maxValue > 0 && minValue > maxValue) {
                        return false;
                    }
                    return true;
                };

                priceMin.addEventListener('blur', () => syncPrices(priceMin, priceMax));
                priceMax.addEventListener('blur', () => syncPrices(priceMax, priceMin));

                priceMin.addEventListener('input', () => {
                    if (!validateRange(priceMin, priceMax)) {
                        priceMax.value = priceMin.value;
                    }
                });

                priceMax.addEventListener('input', () => {
                    if (!validateRange(priceMin, priceMax)) {
                        priceMin.value = priceMax.value;
                    }
                });
            }
        },

        setupCodeSearch: function() {
            const searchBtn = document.getElementById('search_by_code_btn');
            const codeInput = document.getElementById('property_code_input');

            if (searchBtn && codeInput) {
                searchBtn.addEventListener('click', () => {
                    const code = codeInput.value.trim();
                    if (code) {
                        window.location.href = `/properties?code=${encodeURIComponent(code)}`;
                    } else {
                        this.showAlert('Por favor ingresa un código válido', 'warning');
                    }
                });

                // Búsqueda al presionar Enter
                codeInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        searchBtn.click();
                    }
                });
            }
        },

        setupFilterPersistence: function() {
            // Guardar filtros en localStorage para persistencia
            const form = document.querySelector('.property-search-form');
            if (form) {
                form.addEventListener('submit', () => {
                    const formData = new FormData(form);
                    const filters = {};
                    for (let [key, value] of formData.entries()) {
                        if (value) filters[key] = value;
                    }
                    localStorage.setItem('bohio-last-search', JSON.stringify(filters));
                });
            }
        },

        setupLazyLoading: function() {
            // Lazy loading para imágenes de propiedades
            if ('IntersectionObserver' in window) {
                const imageObserver = new IntersectionObserver((entries, observer) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            if (img.dataset.src) {
                                img.src = img.dataset.src;
                                img.classList.remove('lazy');
                                observer.unobserve(img);
                            }
                        }
                    });
                });

                document.querySelectorAll('img.lazy').forEach(img => {
                    imageObserver.observe(img);
                });
            }
        },

        showAlert: function(message, type = 'info') {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
            alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
            alertDiv.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            document.body.appendChild(alertDiv);

            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }
    };

    // ---- Gestión de propiedades en el carrusel ----
    const PropertyCarousel = {
        init: function() {
            this.setupCarouselControls();
            this.loadFeaturedProperties();
        },

        setupCarouselControls: function() {
            document.querySelectorAll('[data-carousel]').forEach(carousel => {
                const prevBtn = carousel.querySelector('[data-carousel-prev]');
                const nextBtn = carousel.querySelector('[data-carousel-next]');
                const container = carousel.querySelector('[data-carousel-container]');

                if (prevBtn && nextBtn && container) {
                    prevBtn.addEventListener('click', () => this.scroll(container, -1));
                    nextBtn.addEventListener('click', () => this.scroll(container, 1));
                }
            });
        },

        scroll: function(container, direction) {
            const scrollAmount = container.offsetWidth / 3;
            container.scrollBy({
                left: scrollAmount * direction,
                behavior: 'smooth'
            });
        },

        loadFeaturedProperties: async function() {
            // Placeholder para cargar propiedades destacadas vía AJAX
            const containers = [
                '#arriendo-properties',
                '#used-sale-properties',
                '#projects-properties'
            ];

            containers.forEach(selector => {
                const container = document.querySelector(selector);
                if (container) {
                    // Aquí se haría la llamada AJAX para cargar las propiedades
                    this.showLoadingSkeleton(container);
                }
            });
        },

        showLoadingSkeleton: function(container) {
            container.innerHTML = `
                <div class="col-md-4">
                    <div class="card skeleton" style="height: 400px;"></div>
                </div>
                <div class="col-md-4">
                    <div class="card skeleton" style="height: 400px;"></div>
                </div>
                <div class="col-md-4">
                    <div class="card skeleton" style="height: 400px;"></div>
                </div>
            `;
        }
    };

    // ---- Gestión de favoritos ----
    const FavoritesManager = {
        init: function() {
            this.setupFavoriteButtons();
            this.loadFavorites();
        },

        setupFavoriteButtons: function() {
            document.addEventListener('click', (e) => {
                const favoriteBtn = e.target.closest('[data-favorite]');
                if (favoriteBtn) {
                    e.preventDefault();
                    const propertyId = favoriteBtn.dataset.propertyId;
                    this.toggleFavorite(propertyId, favoriteBtn);
                }
            });
        },

        toggleFavorite: function(propertyId, button) {
            let favorites = this.getFavorites();
            const index = favorites.indexOf(propertyId);

            if (index > -1) {
                favorites.splice(index, 1);
                button.classList.remove('active');
                button.innerHTML = '<i class="fa fa-heart-o"></i>';
            } else {
                favorites.push(propertyId);
                button.classList.add('active');
                button.innerHTML = '<i class="fa fa-heart"></i>';
            }

            localStorage.setItem('bohio-favorites', JSON.stringify(favorites));
        },

        getFavorites: function() {
            const favorites = localStorage.getItem('bohio-favorites');
            return favorites ? JSON.parse(favorites) : [];
        },

        loadFavorites: function() {
            const favorites = this.getFavorites();
            document.querySelectorAll('[data-favorite]').forEach(btn => {
                const propertyId = btn.dataset.propertyId;
                if (favorites.includes(propertyId)) {
                    btn.classList.add('active');
                    btn.innerHTML = '<i class="fa fa-heart"></i>';
                }
            });
        }
    };

    // ---- Animaciones de scroll ----
    const ScrollAnimations = {
        init: function() {
            this.setupScrollReveal();
            this.setupSmoothScroll();
        },

        setupScrollReveal: function() {
            if ('IntersectionObserver' in window) {
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            entry.target.classList.add('fade-in');
                            observer.unobserve(entry.target);
                        }
                    });
                }, {
                    threshold: 0.1
                });

                document.querySelectorAll('[data-animate]').forEach(el => {
                    observer.observe(el);
                });
            }
        },

        setupSmoothScroll: function() {
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function(e) {
                    const targetId = this.getAttribute('href');
                    if (targetId !== '#') {
                        e.preventDefault();
                        const target = document.querySelector(targetId);
                        if (target) {
                            target.scrollIntoView({
                                behavior: 'smooth',
                                block: 'start'
                            });
                        }
                    }
                });
            });
        }
    };

    // ---- Formateo de números ----
    const NumberFormatter = {
        init: function() {
            this.formatPrices();
            this.formatAreas();
        },

        formatPrices: function() {
            document.querySelectorAll('[data-price]').forEach(el => {
                const price = parseFloat(el.dataset.price);
                if (!isNaN(price)) {
                    el.textContent = this.formatCurrency(price);
                }
            });
        },

        formatAreas: function() {
            document.querySelectorAll('[data-area]').forEach(el => {
                const area = parseFloat(el.dataset.area);
                if (!isNaN(area)) {
                    el.textContent = `${this.formatNumber(area)} m²`;
                }
            });
        },

        formatCurrency: function(value) {
            return new Intl.NumberFormat('es-CO', {
                style: 'currency',
                currency: 'COP',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }).format(value);
        },

        formatNumber: function(value) {
            return new Intl.NumberFormat('es-CO').format(value);
        }
    };

    // ---- Comparador de propiedades ----
    const PropertyComparison = {
        init: function() {
            this.setupComparisonButtons();
            this.loadComparison();
        },

        setupComparisonButtons: function() {
            document.addEventListener('click', (e) => {
                const compareBtn = e.target.closest('[data-compare]');
                if (compareBtn) {
                    e.preventDefault();
                    const propertyId = compareBtn.dataset.propertyId;
                    this.toggleComparison(propertyId);
                }
            });
        },

        toggleComparison: function(propertyId) {
            let comparison = this.getComparison();
            const index = comparison.indexOf(propertyId);

            if (index > -1) {
                comparison.splice(index, 1);
            } else {
                if (comparison.length >= 3) {
                    PropertySearch.showAlert('Solo puedes comparar hasta 3 propiedades', 'warning');
                    return;
                }
                comparison.push(propertyId);
            }

            localStorage.setItem('bohio-comparison', JSON.stringify(comparison));
            this.updateComparisonUI();
        },

        getComparison: function() {
            const comparison = localStorage.getItem('bohio-comparison');
            return comparison ? JSON.parse(comparison) : [];
        },

        loadComparison: function() {
            this.updateComparisonUI();
        },

        updateComparisonUI: function() {
            const comparison = this.getComparison();
            const badge = document.getElementById('comparison-badge');
            
            if (badge) {
                badge.textContent = comparison.length;
                badge.style.display = comparison.length > 0 ? 'inline' : 'none';
            }
        }
    };

    // ---- Inicialización ----
    document.addEventListener('DOMContentLoaded', function() {
        DarkModeManager.init();
        PropertySearch.init();
        PropertyCarousel.init();
        FavoritesManager.init();
        ScrollAnimations.init();
        NumberFormatter.init();
        PropertyComparison.init();

        // Animación de carga de la página
        document.body.classList.add('loaded');
    });

    // ---- Optimización de rendimiento ----
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            // Código para ejecutar después del resize
            console.log('Resize completed');
        }, 250);
    });

    // ---- Service Worker para PWA (opcional) ----
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', function() {
            navigator.serviceWorker.register('/sw.js').then(
                function(registration) {
                    console.log('ServiceWorker registration successful');
                },
                function(err) {
                    console.log('ServiceWorker registration failed: ', err);
                }
            );
        });
    }

})();

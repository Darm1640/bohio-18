document.addEventListener('DOMContentLoaded', function() {
    let submitTimeout = null;
    const form = document.getElementById('real_estate_filters_form');
    
    if (!form) {
        console.warn('Real estate filters form not found');
        return;
    }

    // Función para formatear números según tipo
    function formatNumber(num, type) {
        const number = parseInt(num) || 0;
        const formatted = number.toLocaleString('es-CO');
        
        switch (type) {
            case 'price':
                return '$' + formatted;
            case 'area':
                return formatted;
            case 'floor':
                return formatted;
            default:
                return formatted;
        }
    }
    
    // Inicializar sliders de rango
    const rangeSliders = document.querySelectorAll('.range-slider');
    
    rangeSliders.forEach(function(slider) {
        const minInput = slider.querySelector('.range-min');
        const maxInput = slider.querySelector('.range-max');
        const container = slider.closest('.mb-4');
        const minVal = container.querySelector('.min-val');
        const maxVal = container.querySelector('.max-val');
        const sliderType = slider.dataset.type || 'number';
        
        if (minInput && maxInput && minVal && maxVal) {
            
            function updateValues() {
                let min = parseInt(minInput.value);
                let max = parseInt(maxInput.value);
                
                // Asegurar que min no sea mayor que max
                if (min > max) {
                    var temp = min;
                    min = max;
                    max = temp;
                    minInput.value = min;
                    maxInput.value = max;
                }
                
                minVal.textContent = formatNumber(min, sliderType);
                maxVal.textContent = formatNumber(max, sliderType);
                
                // Actualizar track visual
                updateTrack(slider, min, max, parseInt(minInput.min), parseInt(maxInput.max));
            }
            
            function updateTrack(slider, min, max, minRange, maxRange) {
                const range = maxRange - minRange;
                if (range <= 0) return;
                
                const minPercent = ((min - minRange) / range) * 100;
                const maxPercent = ((max - minRange) / range) * 100;
                
                slider.style.background = 'linear-gradient(to right, #e9ecef 0%, #e9ecef ' + minPercent + '%, #007bff ' + minPercent + '%, #007bff ' + maxPercent + '%, #e9ecef ' + maxPercent + '%, #e9ecef 100%)';
            }
            
            function debounceSubmit() {
                clearTimeout(submitTimeout);
                submitTimeout = setTimeout(function() {
                    showLoading();
                    form.submit();
                }, 500);
            }
            
            minInput.addEventListener('input', updateValues);
            maxInput.addEventListener('input', updateValues);
            minInput.addEventListener('change', debounceSubmit);
            maxInput.addEventListener('change', debounceSubmit);
            
            // Inicializar valores
            updateValues();
        }
    });
    
    // Auto-submit para otros campos
    form.querySelectorAll('select, input[type="text"]').forEach(function(input) {
        if (input.type === 'text') {
            let textTimeout = null;
            input.addEventListener('input', function() {
                clearTimeout(textTimeout);
                const self = this;
                textTimeout = setTimeout(function() {
                    if (self.value.length === 0 || self.value.length >= 3) {
                        showLoading();
                        form.submit();
                    }
                }, 1000);
            });
        } else {
            input.addEventListener('change', function() {
                setTimeout(function() {
                    showLoading();
                    form.submit();
                }, 300);
            });
        }
    });
    
    // Auto-submit para checkboxes
    form.querySelectorAll('input[type="checkbox"]').forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            // Efecto visual
            this.closest('.form-check-sm').style.backgroundColor = 'rgba(0, 123, 255, 0.1)';
            const self = this;
            setTimeout(function() {
                self.closest('.form-check-sm').style.backgroundColor = '';
            }, 300);
            
            setTimeout(function() {
                showLoading();
                form.submit();
            }, 300);
        });
    });
    
    // Función para mostrar loading
    function showLoading() {
        const sidebar = document.getElementById('real_estate_sidebar');
        if (sidebar) {
            sidebar.classList.add('form-loading');
        }
        
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Buscando...';
        }
    }
    
    // Actualizar contador de filtros activos
    function updateActiveFiltersCount() {
        let activeCount = 0;
        
        // Contar inputs con valor
        form.querySelectorAll('input[type="text"]').forEach(function(input) {
            if (input.value && input.value.trim() !== '') {
                activeCount++;
            }
        });
        
        // Contar selects con valor
        form.querySelectorAll('select').forEach(function(select) {
            if (select.value && select.value !== '') {
                activeCount++;
            }
        });
        
        // Contar checkboxes marcados
        activeCount += form.querySelectorAll('input[type="checkbox"]:checked').length;
        
        // Contar rangos modificados
        form.querySelectorAll('.range-slider').forEach(function(slider) {
            const minInput = slider.querySelector('.range-min');
            const maxInput = slider.querySelector('.range-max');
            if (minInput && maxInput) {
                const defaultMin = parseInt(minInput.min);
                const defaultMax = parseInt(minInput.max);
                const currentMin = parseInt(minInput.value);
                const currentMax = parseInt(maxInput.value);
                
                if (currentMin !== defaultMin || currentMax !== defaultMax) {
                    activeCount++;
                }
            }
        });
        
        // Actualizar indicadores
        const indicators = document.querySelectorAll('.active-filters-count, .active-count-badge');
        indicators.forEach(function(indicator) {
            if (activeCount > 0) {
                indicator.textContent = '(' + activeCount + ')';
                indicator.style.display = 'inline';
            } else {
                indicator.style.display = 'none';
            }
        });
    }
    
    // Actualizar contador al cargar y cuando cambien los filtros
    updateActiveFiltersCount();
    form.addEventListener('change', updateActiveFiltersCount);
    form.addEventListener('input', updateActiveFiltersCount);
});
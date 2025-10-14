/**
 * BOHIO Real Estate - Mejoras de Búsqueda e Integración
 * 
 * Características:
 * 1. Contador de propiedades en Home
 * 2. Búsqueda integrada Home → Shop
 * 3. Filtros dinámicos
 * 4. Mapa mejorado con pins personalizados
 */

(function() {
    'use strict';

    // =================== 1. CONTADOR DE PROPIEDADES EN HOME ===================
    
    /**
     * Carga y muestra contadores de propiedades en el homepage
     */
    async function loadPropertyCounters() {
        try {
            const response = await fetch('/api/properties/count', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {}
                })
            });
            
            const data = await response.json();
            
            if (data.result && data.result.success) {
                const counts = data.result;
                
                // Actualizar contadores en la UI
                updateCounter('total-properties', counts.total);
                updateCounter('rent-properties', counts.rent);
                updateCounter('sale-properties', counts.sale);
                updateCounter('project-properties', counts.projects);
                
                // Mostrar badges con cantidades
                document.querySelectorAll('[data-service]').forEach(btn => {
                    const service = btn.getAttribute('data-service');
                    let count = 0;
                    
                    if (service === 'rent') count = counts.rent;
                    else if (service === 'sale') count = counts.sale;
                    else if (service === 'sale_rent') count = counts.total;
                    
                    if (count > 0) {
                        // Agregar badge con cantidad
                        const badge = document.createElement('span');
                        badge.className = 'badge bg-white text-danger ms-2';
                        badge.textContent = count.toLocaleString();
                        btn.appendChild(badge);
                    }
                });
            }
        } catch (error) {
            console.error('Error cargando contadores:', error);
        }
    }
    
    function updateCounter(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value.toLocaleString();
            // Animar contador
            element.classList.add('counter-animate');
            setTimeout(() => element.classList.remove('counter-animate'), 500);
        }
    }

    // =================== 2. BÚSQUEDA INTELIGENTE HOME → SHOP ===================
    
    /**
     * Maneja la búsqueda desde el homepage y redirige al shop con filtros
     */
    function setupSmartSearch() {
        const searchForm = document.getElementById('searchForm');
        if (!searchForm) return;
        
        searchForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const searchInput = document.getElementById('searchInput');
            const typeServiceInput = document.getElementById('selectedServiceType');
            const propertyTypeInput = document.getElementById('selectedPropertyType');
            
            const searchTerm = searchInput ? searchInput.value.trim() : '';
            const typeService = typeServiceInput ? typeServiceInput.value : '';
            const propertyType = propertyTypeInput ? propertyTypeInput.value : '';
            
            if (!searchTerm) {
                // Si no hay búsqueda, ir al shop con filtros básicos
                let url = '/properties';
                const params = [];
                if (typeService) params.push(`type_service=${typeService}`);
                if (propertyType) params.push(`property_type=${propertyType}`);
                if (params.length > 0) url += '?' + params.join('&');
                
                window.location.href = url;
                return;
            }
            
            // Mostrar loading
            showSearchLoading(true);
            
            try {
                const response = await fetch('/api/search/smart', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        jsonrpc: '2.0',
                        method: 'call',
                        params: {
                            term: searchTerm,
                            type_service: typeService,
                            property_type: propertyType
                        }
                    })
                });
                
                const data = await response.json();
                
                if (data.result && data.result.success) {
                    // Redirigir a la URL generada
                    window.location.href = data.result.redirect_url;
                } else {
                    // Si falla, búsqueda general
                    window.location.href = `/properties?search=${encodeURIComponent(searchTerm)}`;
                }
            } catch (error) {
                console.error('Error en búsqueda:', error);
                window.location.href = `/properties?search=${encodeURIComponent(searchTerm)}`;
            } finally {
                showSearchLoading(false);
            }
        });
    }
    
    function showSearchLoading(show) {
        const searchBtn = document.querySelector('#searchForm button[type="submit"]');
        if (!searchBtn) return;
        
        if (show) {
            searchBtn.disabled = true;
            searchBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Buscando...';
        } else {
            searchBtn.disabled = false;
            searchBtn.innerHTML = '<i class="bi bi-search"></i> Buscar';
        }
    }

    // =================== 3. FILTROS DINÁMICOS EN SHOP ===================
    
    /**
     * Carga filtros dinámicos con contadores actualizados
     */
    async function loadDynamicFilters(currentFilters = {}) {
        try {
            const response = await fetch('/api/properties/filters', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {filters: currentFilters}
                })
            });
            
            const data = await response.json();
            
            if (data.result && data.result.success) {
                updateFilterOptions('property_type', data.result.property_types);
                updateFilterOptions('city_id', data.result.cities);
            }
        } catch (error) {
            console.error('Error cargando filtros:', error);
        }
    }
    
    function updateFilterOptions(filterName, options) {
        const select = document.querySelector(`[data-filter="${filterName}"]`);
        if (!select) return;
        
        // Guardar valor actual
        const currentValue = select.value;
        
        // Limpiar opciones excepto la primera (placeholder)
        while (select.options.length > 1) {
            select.remove(1);
        }
        
        // Agregar nuevas opciones con contadores
        options.forEach(option => {
            const opt = document.createElement('option');
            opt.value = option.value || option.id;
            opt.textContent = `${option.label || option.name} (${option.count})`;
            select.appendChild(opt);
        });
        
        // Restaurar valor si existe
        if (currentValue) {
            select.value = currentValue;
        }
    }

    // =================== 4. MAPA MEJORADO CON PINS PERSONALIZADOS ===================
    
    /**
     * Inicializa mapa con pins personalizados y colores según tipo
     */
    async function initializeImprovedMap(mapElementId, filters = {}) {
        if (typeof L === 'undefined') {
            console.error('Leaflet no está cargado');
            return;
        }
        
        const mapElement = document.getElementById(mapElementId);
        if (!mapElement) return;
        
        // Crear mapa
        const map = L.map(mapElementId).setView([8.7479, -75.8814], 12);
        
        // Agregar tiles con estilo mejorado
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap',
            maxZoom: 19
        }).addTo(map);
        
        // Cargar marcadores
        await loadImprovedMarkers(map, filters);
        
        return map;
    }
    
    async function loadImprovedMarkers(map, filters = {}) {
        try {
            const response = await fetch('/api/properties/map/markers', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {filters: filters}
                })
            });
            
            const data = await response.json();
            
            if (data.result && data.result.success) {
                const markers = data.result.markers;
                const center = data.result.center;
                
                // Centrar mapa
                map.setView([center.lat, center.lng], 12);
                
                // Agregar marcadores personalizados
                markers.forEach(marker => {
                    addCustomMarker(map, marker);
                });
                
                // Ajustar vista a todos los marcadores
                if (markers.length > 0) {
                    const bounds = markers.map(m => [m.lat, m.lng]);
                    map.fitBounds(bounds, {padding: [50, 50]});
                }
            }
        } catch (error) {
            console.error('Error cargando marcadores:', error);
        }
    }
    
    function addCustomMarker(map, markerData) {
        // Crear ícono personalizado con color según tipo
        const iconHtml = `
            <div class="custom-marker" style="background-color: ${markerData.pin_color}">
                <i class="fa ${markerData.icon}"></i>
                <div class="marker-price">${markerData.price_formatted}</div>
            </div>
        `;
        
        const customIcon = L.divIcon({
            html: iconHtml,
            className: 'custom-property-marker',
            iconSize: [40, 50],
            iconAnchor: [20, 50],
            popupAnchor: [0, -50]
        });
        
        // Crear marcador
        const marker = L.marker([markerData.lat, markerData.lng], {
            icon: customIcon
        });
        
        // Crear popup con información
        const popupContent = createMarkerPopup(markerData);
        marker.bindPopup(popupContent, {
            maxWidth: 300,
            className: 'property-popup'
        });
        
        marker.addTo(map);
        
        // Abrir detalle al hacer clic
        marker.on('click', function() {
            window.open(markerData.url, '_blank');
        });
    }
    
    function createMarkerPopup(property) {
        return `
            <div class="property-marker-popup">
                ${property.image_url ? 
                    `<img src="${property.image_url}" alt="${property.title}" class="popup-image"/>` 
                    : ''}
                <div class="popup-content">
                    <h6 class="popup-title">${property.title}</h6>
                    <p class="popup-price">${property.price_formatted}</p>
                    <div class="popup-details">
                        <span><i class="fa fa-bed"></i> ${property.bedrooms}</span>
                        <span><i class="fa fa-bath"></i> ${property.bathrooms}</span>
                        <span><i class="fa fa-arrows-alt"></i> ${property.area}m²</span>
                    </div>
                    <p class="popup-location">
                        <i class="fa fa-map-marker"></i> ${property.city}${property.neighborhood ? ', ' + property.neighborhood : ''}
                    </p>
                    <a href="${property.url}" class="btn btn-sm btn-danger w-100" target="_blank">
                        Ver Detalles <i class="fa fa-arrow-right"></i>
                    </a>
                </div>
            </div>
        `;
    }

    // =================== INICIALIZACIÓN ===================
    
    document.addEventListener('DOMContentLoaded', function() {
        // Cargar contadores en homepage
        if (document.querySelector('.bohio-homepage')) {
            loadPropertyCounters();
            setupSmartSearch();
        }
        
        // Cargar filtros dinámicos en shop
        if (document.querySelector('.bohio-shop-page')) {
            loadDynamicFilters();
            
            // Actualizar filtros cuando cambie el tipo de servicio
            document.querySelectorAll('[data-filter="type_service"]').forEach(select => {
                select.addEventListener('change', function() {
                    loadDynamicFilters({type_service: this.value});
                });
            });
        }
        
        // Inicializar mapa mejorado si existe
        const mapElement = document.getElementById('properties-map');
        if (mapElement) {
            // Esperar a que se active la pestaña del mapa
            document.querySelector('[data-bs-target="#map-view"]')?.addEventListener('shown.bs.tab', function() {
                if (!window.propertyMap) {
                    window.propertyMap = initializeImprovedMap('properties-map');
                }
            });
        }
    });

})();

// =================== CSS PARA MARCADORES PERSONALIZADOS ===================

const markerStyles = `
<style>
.custom-property-marker {
    background: transparent !important;
    border: none !important;
}

.custom-marker {
    position: relative;
    width: 40px;
    height: 50px;
    border-radius: 50% 50% 50% 0;
    transform: rotate(-45deg);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 3px 10px rgba(0,0,0,0.3);
    cursor: pointer;
    transition: all 0.3s ease;
}

.custom-marker:hover {
    transform: rotate(-45deg) scale(1.1);
    box-shadow: 0 5px 15px rgba(0,0,0,0.4);
}

.custom-marker i {
    transform: rotate(45deg);
    color: white;
    font-size: 18px;
}

.marker-price {
    position: absolute;
    top: -25px;
    left: 50%;
    transform: translateX(-50%) rotate(45deg);
    background: white;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: bold;
    color: #333;
    white-space: nowrap;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

.property-marker-popup {
    font-family: 'Inter', sans-serif;
}

.popup-image {
    width: 100%;
    height: 150px;
    object-fit: cover;
    border-radius: 8px 8px 0 0;
    margin-bottom: 10px;
}

.popup-content {
    padding: 5px;
}

.popup-title {
    font-size: 14px;
    font-weight: 600;
    color: #333;
    margin-bottom: 5px;
}

.popup-price {
    font-size: 18px;
    font-weight: 700;
    color: #E31E24;
    margin-bottom: 10px;
}

.popup-details {
    display: flex;
    gap: 15px;
    margin-bottom: 10px;
    font-size: 13px;
    color: #666;
}

.popup-details span {
    display: flex;
    align-items: center;
    gap: 5px;
}

.popup-location {
    font-size: 12px;
    color: #999;
    margin-bottom: 10px;
}

.counter-animate {
    animation: countPulse 0.5s ease;
}

@keyframes countPulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); color: #E31E24; }
}
</style>
`;

// Inyectar estilos
document.head.insertAdjacentHTML('beforeend', markerStyles);

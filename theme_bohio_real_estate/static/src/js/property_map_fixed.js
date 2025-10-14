/** @odoo-module **/

/**
 * ============================================================================
 * BOHÍO PROPERTY MAP - VERSIÓN CORREGIDA
 * ============================================================================
 * Sistema de mapas usando Leaflet para mostrar ubicación de propiedades
 * Compatible con Bootstrap 5.3.3 y Odoo 18
 */

class PropertyMap {
    constructor() {
        this.map = null;
        this.marker = null;
        this.isVisible = false;
        this.init();
    }

    init() {
        console.log('🗺️ Property Map inicializando...');
        
        // Verificar que Leaflet esté cargado
        if (typeof L === 'undefined') {
            console.error('❌ Leaflet no está cargado');
            return;
        }

        // Configurar botón de toggle
        this.setupToggleButton();
        
        console.log('✅ Property Map listo');
    }

    /**
     * Configurar botón de toggle del mapa
     */
    setupToggleButton() {
        const toggleBtn = document.querySelector('[onclick*="toggleMapView"]');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleMap();
            });
        }
    }

    /**
     * Toggle entre imagen y mapa
     */
    toggleMap() {
        const mapSection = document.getElementById('mapViewSection');
        const carouselContainer = document.querySelector('.property-gallery-container');

        if (!mapSection || !carouselContainer) {
            console.error('❌ Elementos de mapa/carrusel no encontrados');
            return;
        }

        if (!this.isVisible) {
            // Mostrar mapa
            mapSection.style.display = 'block';
            carouselContainer.style.display = 'none';
            this.isVisible = true;

            // Inicializar mapa si no existe
            setTimeout(() => {
                if (!this.map) {
                    this.initializeMap();
                } else {
                    // Si ya existe, solo recalcular tamaño
                    this.map.invalidateSize();
                }
            }, 100);
        } else {
            // Ocultar mapa
            mapSection.style.display = 'none';
            carouselContainer.style.display = 'block';
            this.isVisible = false;
        }
    }

    /**
     * Inicializar mapa de Leaflet
     */
    initializeMap() {
        const mapDiv = document.getElementById('property_map');
        
        if (!mapDiv) {
            console.error('❌ Elemento property_map no encontrado');
            return;
        }

        const lat = parseFloat(mapDiv.dataset.lat);
        const lng = parseFloat(mapDiv.dataset.lng);
        const name = mapDiv.dataset.name || 'Propiedad';

        console.log('📍 Coordenadas:', { lat, lng, name });

        if (!lat || !lng || isNaN(lat) || isNaN(lng)) {
            console.error('❌ Coordenadas inválidas:', { lat, lng });
            this.showMapError(mapDiv, 'Coordenadas no disponibles');
            return;
        }

        try {
            // Crear mapa
            this.map = L.map('property_map', {
                center: [lat, lng],
                zoom: 16,
                scrollWheelZoom: true,
                zoomControl: true
            });

            // Agregar capa de tiles
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                maxZoom: 19
            }).addTo(this.map);

            // Crear marcador personalizado
            const markerIcon = L.divIcon({
                className: 'custom-marker',
                html: `
                    <div style="
                        position: relative;
                        width: 40px;
                        height: 40px;
                    ">
                        <div style="
                            width: 40px;
                            height: 40px;
                            background: linear-gradient(135deg, #E31E24 0%, #c91920 100%);
                            border-radius: 50% 50% 50% 0;
                            transform: rotate(-45deg);
                            border: 3px solid white;
                            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        ">
                            <i class="bi bi-house-fill" style="
                                color: white;
                                font-size: 18px;
                                transform: rotate(45deg);
                            "></i>
                        </div>
                    </div>
                `,
                iconSize: [40, 40],
                iconAnchor: [20, 40],
                popupAnchor: [0, -40]
            });

            // Agregar marcador
            this.marker = L.marker([lat, lng], { icon: markerIcon }).addTo(this.map);

            // Agregar popup
            const popupContent = `
                <div style="padding: 10px; min-width: 200px;">
                    <h6 style="margin: 0 0 10px 0; color: #E31E24; font-weight: 600;">
                        <i class="bi bi-house-fill me-2"></i>${name}
                    </h6>
                    <p style="margin: 5px 0; font-size: 13px; color: #666;">
                        <i class="bi bi-geo-alt-fill text-danger me-1"></i>
                        <strong>Coordenadas:</strong>
                    </p>
                    <p style="margin: 0; font-size: 12px; color: #999;">
                        ${lat.toFixed(6)}, ${lng.toFixed(6)}
                    </p>
                    <hr style="margin: 10px 0;">
                    <a href="https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}" 
                       target="_blank" 
                       class="btn btn-sm btn-danger w-100"
                       style="font-size: 12px;">
                        <i class="bi bi-navigation me-1"></i>
                        Cómo llegar
                    </a>
                </div>
            `;

            this.marker.bindPopup(popupContent, {
                maxWidth: 300,
                className: 'custom-popup'
            }).openPopup();

            // Forzar recálculo de tamaño
            setTimeout(() => {
                if (this.map) {
                    this.map.invalidateSize();
                }
            }, 200);

            console.log('✅ Mapa inicializado correctamente');

        } catch (error) {
            console.error('❌ Error al crear mapa:', error);
            this.showMapError(mapDiv, 'Error al cargar el mapa');
        }
    }

    /**
     * Mostrar error en el mapa
     */
    showMapError(container, message) {
        container.innerHTML = `
            <div style="
                height: 400px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #f8f9fa;
                border-radius: 8px;
            ">
                <div class="text-center">
                    <i class="bi bi-exclamation-triangle text-warning" style="font-size: 48px;"></i>
                    <p class="mt-3 text-muted">${message}</p>
                </div>
            </div>
        `;
    }

    /**
     * Abrir mapa en ventana completa (nueva página)
     */
    openFullMap() {
        const mapDiv = document.getElementById('property_map');
        if (!mapDiv) return;

        const lat = parseFloat(mapDiv.dataset.lat);
        const lng = parseFloat(mapDiv.dataset.lng);

        if (!lat || !lng || isNaN(lat) || isNaN(lng)) {
            alert('Coordenadas no disponibles');
            return;
        }

        // Abrir en nueva pestaña con Google Maps
        const url = `https://www.google.com/maps/search/?api=1&query=${lat},${lng}`;
        window.open(url, '_blank');
    }
}

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

let mapInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    mapInstance = new PropertyMap();

    // Exponer funciones globalmente
    window.toggleMapView = () => mapInstance.toggleMap();
    window.openFullMap = () => mapInstance.openFullMap();
});

console.log('✅ Property Map Module cargado');

export default PropertyMap;
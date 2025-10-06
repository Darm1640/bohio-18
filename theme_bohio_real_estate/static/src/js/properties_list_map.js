/** @odoo-module **/

/**
 * Helper function para hacer llamadas JSON-RPC
 */
async function jsonrpc(url, params = {}) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            jsonrpc: '2.0',
            method: 'call',
            params: params,
            id: Math.floor(Math.random() * 1000000),
        }),
    });
    const data = await response.json();
    if (data.error) {
        throw new Error(data.error.data?.message || data.error.message);
    }
    return data.result;
}

export class PropertiesListMap {
    constructor() {
        this.currentView = 'lista';
        this.map = null;
        this.markers = [];
        this.properties = [];
        this.init();
    }

    init() {
        this.loadProperties();
        this.bindEvents();
    }

    bindEvents() {
        // Botones de vista
        document.getElementById('btnLista')?.addEventListener('click', () => this.setView('lista'));
        document.getElementById('btnMapa')?.addEventListener('click', () => this.setView('mapa'));

        // Búsqueda y filtros
        document.getElementById('btnBuscar')?.addEventListener('click', () => this.applyFilters());
        document.getElementById('btnCodigo')?.addEventListener('click', () => this.searchByCode());
        document.getElementById('sortSel')?.addEventListener('change', () => this.renderList());

        // Enter en campo de código
        document.getElementById('inputCodigo')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.searchByCode();
        });
    }

    async loadProperties() {
        try {
            const response = await jsonrpc('/api/properties/search', {
                filters: {},
                page: 1,
                limit: 100
            });

            this.properties = response.properties || [];
            this.renderList();
        } catch (error) {
            console.error('Error loading properties:', error);
            this.showError('Error al cargar las propiedades');
        }
    }

    async applyFilters() {
        const filters = this.getFilters();

        try {
            const response = await jsonrpc('/api/properties/search', {
                filters: filters,
                page: 1,
                limit: 100
            });

            this.properties = response.properties || [];
            this.renderList();

            if (this.currentView === 'mapa') {
                this.renderMap();
            }
        } catch (error) {
            console.error('Error applying filters:', error);
            this.showError('Error al filtrar propiedades');
        }
    }

    async searchByCode() {
        const code = document.getElementById('inputCodigo')?.value.trim();

        if (!code) {
            alert('Por favor ingresa un código de propiedad');
            return;
        }

        try {
            const response = await jsonrpc('/api/properties/search_by_code', {
                code: code
            });

            if (response.found && response.published) {
                // Redirigir a la página de detalle
                window.location.href = response.url;
            } else if (response.found && !response.published) {
                alert(`La propiedad ${response.code} no está publicada en el sitio web.`);
            } else {
                alert(response.error || 'No se encontró ninguna propiedad con ese código');
            }
        } catch (error) {
            console.error('Error searching by code:', error);
            this.showError('Error al buscar por código');
        }
    }

    getFilters() {
        const filters = {};

        const type = document.getElementById('filterType')?.value;
        const city = document.getElementById('filterCity')?.value;
        const mode = document.getElementById('filterMode')?.value;
        const bedrooms = document.getElementById('filterBedrooms')?.value;
        const bathrooms = document.getElementById('filterBathrooms')?.value;
        const priceMin = document.getElementById('priceMin')?.value;
        const priceMax = document.getElementById('priceMax')?.value;

        if (type) filters.property_type = type;
        if (city) filters.city_id = city;
        if (mode) filters.type_service = mode;
        if (bedrooms) filters.bedrooms = bedrooms;
        if (bathrooms) filters.bathrooms = bathrooms;
        if (priceMin) filters.price_min = parseFloat(priceMin);
        if (priceMax) filters.price_max = parseFloat(priceMax);

        return filters;
    }

    sortProperties(properties) {
        const sortBy = document.getElementById('sortSel')?.value || 'newest';
        const sorted = [...properties];

        switch(sortBy) {
            case 'price_asc':
                sorted.sort((a, b) => {
                    const priceA = a.rental_price || a.sale_price || 0;
                    const priceB = b.rental_price || b.sale_price || 0;
                    return priceA - priceB;
                });
                break;

            case 'price_desc':
                sorted.sort((a, b) => {
                    const priceA = a.rental_price || a.sale_price || 0;
                    const priceB = b.rental_price || b.sale_price || 0;
                    return priceB - priceA;
                });
                break;

            case 'rooms_desc':
                sorted.sort((a, b) => {
                    return (b.bedrooms || 0) - (a.bedrooms || 0) || (b.area || 0) - (a.area || 0);
                });
                break;

            case 'area_desc':
                sorted.sort((a, b) => (b.area || 0) - (a.area || 0));
                break;

            case 'newest':
                sorted.sort((a, b) => b.id - a.id);
                break;
        }

        return sorted;
    }

    formatCOP(amount) {
        if (!amount) return 'Consultar';
        return new Intl.NumberFormat('es-CO', {
            style: 'currency',
            currency: 'COP',
            maximumFractionDigits: 0
        }).format(amount);
    }

    getPropertyState(prop) {
        // Determinar estado según campos de Odoo
        const states = {
            'free': { text: 'Disponible', class: '' },
            'rented': { text: 'Arrendado', class: 'rented' },
            'unavailable': { text: 'No Disponible', class: 'unavailable' }
        };
        return states[prop.state] || states['free'];
    }

    renderList() {
        const grid = document.getElementById('lista');
        const countText = document.getElementById('countText');

        if (!grid || !countText) return;

        const sorted = this.sortProperties(this.properties);

        if (sorted.length === 0) {
            grid.innerHTML = `
                <div class="no-results">
                    <p>No se encontraron propiedades con los filtros seleccionados.</p>
                </div>
            `;
            countText.textContent = '0';
            return;
        }

        const cardsHTML = sorted.map(prop => {
            const price = prop.rental_price || prop.sale_price || 0;
            const transactionType = prop.rental_price ? 'Arriendo' : 'Venta';
            const state = this.getPropertyState(prop);

            return `
                <article class="property-card" data-id="${prop.id}" onclick="window.location.href='${prop.url}'">
                    <div class="property-thumb">
                        ${prop.image_url ?
                            `<img src="${prop.image_url}" alt="${prop.name}" loading="lazy"/>` :
                            `<div class="property-placeholder">
                                <svg viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M3 11l9-8 9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1v-9z"/>
                                </svg>
                            </div>`
                        }
                        <div class="price-badge">${this.formatCOP(price)}</div>
                        <div class="type-badge">${prop.property_type_name || 'Propiedad'}</div>
                        <div class="status-badge ${state.class}">${state.text}</div>
                    </div>

                    <div class="property-body">
                        <div class="property-code">${prop.default_code || ''}</div>
                        <div class="property-title">${prop.name}</div>
                        <div class="property-location">
                            <img src="/theme_bohio_real_estate/static/src/img/icons/location.png" alt="" class="meta-icon"/> ${[prop.region, prop.city].filter(Boolean).join(', ')}
                        </div>

                        <div class="property-meta">
                            ${prop.bedrooms ? `<span><img src="/theme_bohio_real_estate/static/src/img/icons/bedroom.png" alt="" class="meta-icon"/> ${prop.bedrooms} Hab.</span>` : ''}
                            ${prop.bathrooms ? `<span><img src="/theme_bohio_real_estate/static/src/img/icons/bathroom.png" alt="" class="meta-icon"/> ${prop.bathrooms} Baños</span>` : ''}
                            ${prop.area ? `<span><img src="/theme_bohio_real_estate/static/src/img/icons/area.png" alt="" class="meta-icon"/> ${prop.area} m²</span>` : ''}
                            <span>${transactionType}</span>
                        </div>
                    </div>
                </article>
            `;
        }).join('');

        grid.innerHTML = cardsHTML;
        countText.textContent = sorted.length;
    }

    initMap() {
        if (!this.map) {
            // Centro inicial: Montería, Córdoba
            this.map = L.map('mapCanvas').setView([8.7479, -75.8814], 13);

            // Tile layer de OpenStreetMap
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                maxZoom: 19
            }).addTo(this.map);
        }
    }

    renderMap() {
        if (!this.map) {
            this.initMap();
        }

        // Limpiar marcadores previos
        this.markers.forEach(marker => this.map.removeLayer(marker));
        this.markers = [];

        const sorted = this.sortProperties(this.properties);
        const validProperties = sorted.filter(p => p.latitude && p.longitude);

        if (validProperties.length === 0) {
            return;
        }

        // Crear marcadores
        validProperties.forEach(prop => {
            // Icono personalizado rojo Bohío
            const iconoRojo = L.divIcon({
                className: 'bohio-map-marker',
                html: `<div class="marker-pin"></div>`,
                iconSize: [28, 28],
                iconAnchor: [14, 28],
                popupAnchor: [0, -28]
            });

            const marker = L.marker([prop.latitude, prop.longitude], { icon: iconoRojo }).addTo(this.map);

            const price = prop.rental_price || prop.sale_price || 0;
            const transactionType = prop.rental_price ? 'Arriendo' : 'Venta';

            const popupContent = `
                <div class="leaflet-popup-bohio">
                    <div class="popup-title">${prop.default_code || ''} - ${prop.property_type_name || 'Propiedad'}</div>
                    <div class="popup-price">${this.formatCOP(price)} (${transactionType})</div>
                    <div class="popup-meta">
                        ${prop.bedrooms ? `<span><img src="/theme_bohio_real_estate/static/src/img/icons/bedroom.png" alt="" class="meta-icon"/> ${prop.bedrooms}H</span>` : ''}
                        ${prop.bathrooms ? `<span><img src="/theme_bohio_real_estate/static/src/img/icons/bathroom.png" alt="" class="meta-icon"/> ${prop.bathrooms}B</span>` : ''}
                        ${prop.area ? `<span><img src="/theme_bohio_real_estate/static/src/img/icons/area.png" alt="" class="meta-icon"/> ${prop.area}m²</span>` : ''}
                    </div>
                    <a href="${prop.url}" class="popup-link">Ver detalles →</a>
                </div>
            `;

            marker.bindPopup(popupContent);
            this.markers.push(marker);
        });

        // Ajustar vista al conjunto de marcadores
        if (this.markers.length > 0) {
            const group = new L.featureGroup(this.markers);
            this.map.fitBounds(group.getBounds().pad(0.1));
        }
    }

    setView(view) {
        this.currentView = view;
        const isMapa = view === 'mapa';

        const btnLista = document.getElementById('btnLista');
        const btnMapa = document.getElementById('btnMapa');
        const listaEl = document.getElementById('lista');
        const mapaWrap = document.getElementById('mapa');

        if (btnLista) {
            btnLista.classList.toggle('active', !isMapa);
            btnLista.setAttribute('aria-selected', !isMapa);
        }

        if (btnMapa) {
            btnMapa.classList.toggle('active', isMapa);
            btnMapa.setAttribute('aria-selected', isMapa);
        }

        if (listaEl) {
            listaEl.style.display = isMapa ? 'none' : 'grid';
        }

        if (mapaWrap) {
            mapaWrap.style.display = isMapa ? 'block' : 'none';
            mapaWrap.setAttribute('aria-hidden', !isMapa);
        }

        if (isMapa) {
            this.renderMap();

            // Fix para Leaflet cuando el contenedor cambia de tamaño
            setTimeout(() => {
                if (this.map) this.map.invalidateSize();
            }, 100);
        }
    }

    showError(message) {
        console.error(message);
        // Opcional: mostrar toast o notificación
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.bohio_properties_map_page')) {
        new PropertiesListMap();
    }
});

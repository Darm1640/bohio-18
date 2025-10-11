# Ejemplos Rápidos - Carruseles Dinámicos

## 🎯 Ejemplo 1: Agregar carrusel al Homepage

### Editar `views/homepage_new.xml`

```xml
<!-- Después de las secciones existentes, agregar: -->
<t t-call="theme_bohio_real_estate.carousel_rent_section"/>
<t t-call="theme_bohio_real_estate.carousel_sale_section"/>
<t t-call="theme_bohio_real_estate.carousel_projects_section"/>
```

## 🎯 Ejemplo 2: Carrusel personalizado de propiedades destacadas

### 1. Crear el HTML

```xml
<section class="py-5 bg-light">
    <div class="container">
        <h2 class="text-center mb-4">Propiedades Destacadas del Mes</h2>
        <div class="property-carousel-container">
            <div id="carousel-featured"></div>
        </div>
    </div>
</section>
```

### 2. Crear controlador personalizado

```python
# En controllers/main.py

@http.route(['/carousel/featured'], type='json', auth='public', website=True, csrf=False)
def carousel_featured(self, limit=8, **kwargs):
    """Carrusel de propiedades destacadas"""
    Property = request.env['product.template'].sudo()

    domain = [
        ('is_property', '=', True),
        ('active', '=', True),
        ('state', '=', 'free'),
        ('is_featured', '=', True),  # Campo personalizado
        ('latitude', '!=', False),
        ('longitude', '!=', False)
    ]

    properties = Property.search(domain, limit=limit, order='create_date DESC')

    # Reusar la serialización existente
    return self._serialize_carousel_properties(properties, 'featured')
```

### 3. JavaScript para inicializar

```javascript
// Crear archivo: static/src/js/featured_carousel.js

document.addEventListener('DOMContentLoaded', function() {
    const featuredCarousel = new PropertyCarousel('carousel-featured', 'featured');
    featuredCarousel.init();
});
```

## 🎯 Ejemplo 3: Carrusel con filtro por ciudad

### Controlador con filtro de ciudad

```python
@http.route(['/carousel/by-city/<int:city_id>'], type='json', auth='public')
def carousel_by_city(self, city_id, limit=12, **kwargs):
    """Carrusel de propiedades filtradas por ciudad"""
    Property = request.env['product.template'].sudo()

    domain = [
        ('is_property', '=', True),
        ('active', '=', True),
        ('state', '=', 'free'),
        ('city_id', '=', city_id),
        ('latitude', '!=', False),
        ('longitude', '!=', False)
    ]

    properties = Property.search(domain, limit=limit)
    # Serializar y retornar
```

### JavaScript para ciudad específica

```javascript
// Cargar propiedades de Medellín (city_id = 1)
async function loadMedellinProperties() {
    const result = await rpc('/carousel/by-city/1', {
        limit: 15
    });

    // Renderizar manualmente o usar PropertyCarousel
}
```

## 🎯 Ejemplo 4: Carrusel con rango de precios

### Controlador con filtro de precio

```python
@http.route(['/carousel/price-range'], type='json', auth='public')
def carousel_price_range(self, min_price=0, max_price=1000000000, **kwargs):
    """Carrusel filtrado por rango de precios"""
    Property = request.env['product.template'].sudo()

    domain = [
        ('is_property', '=', True),
        ('active', '=', True),
        ('state', '=', 'free'),
        ('net_price', '>=', float(min_price)),
        ('net_price', '<=', float(max_price)),
        ('latitude', '!=', False),
        ('longitude', '!=', False)
    ]

    properties = Property.search(domain, limit=12, order='net_price ASC')
    # Serializar y retornar
```

### Llamar desde JavaScript

```javascript
const result = await rpc('/carousel/price-range', {
    min_price: 200000000,  // $200M
    max_price: 500000000   // $500M
});
```

## 🎯 Ejemplo 5: Modificar tarjetas del carrusel

### Personalizar la función createPropertyCard

```javascript
// En property_carousels.js, modificar createPropertyCard():

createPropertyCard(property) {
    // Agregar información adicional
    const stratumBadge = property.stratum ? `
        <span class="badge bg-info">Estrato ${property.stratum}</span>
    ` : '';

    const garageIcon = property.has_garage ? `
        <i class="fa fa-car text-success" title="Garaje"></i>
    ` : '';

    return `
        <div class="col-md-3">
            <div class="card h-100">
                <!-- Imagen -->
                <img src="${property.image_url}" class="card-img-top"/>

                <!-- Contenido -->
                <div class="card-body">
                    <h5>${property.name}</h5>

                    <!-- Badges personalizados -->
                    ${stratumBadge}

                    <!-- Características -->
                    <div class="d-flex gap-2 mb-2">
                        <span>${property.bedrooms} hab</span>
                        <span>${property.bathrooms} baños</span>
                        ${garageIcon}
                    </div>

                    <!-- Precio -->
                    <h4 class="text-danger">${property.price_formatted}</h4>

                    <!-- Botón -->
                    <a href="${property.url}" class="btn btn-danger">Ver detalles</a>
                </div>
            </div>
        </div>
    `;
}
```

## 🎯 Ejemplo 6: Carrusel con búsqueda en tiempo real

### HTML con buscador

```xml
<section class="py-5">
    <div class="container">
        <div class="row mb-4">
            <div class="col-md-6 mx-auto">
                <input type="text"
                       id="carousel-search"
                       class="form-control form-control-lg"
                       placeholder="Buscar propiedades..."/>
            </div>
        </div>
        <div class="property-carousel-container">
            <div id="carousel-searchable"></div>
        </div>
    </div>
</section>
```

### JavaScript con búsqueda

```javascript
let searchTimeout;
const searchInput = document.getElementById('carousel-search');
const carousel = new PropertyCarousel('carousel-searchable', 'sale');

searchInput.addEventListener('input', function(e) {
    clearTimeout(searchTimeout);

    searchTimeout = setTimeout(async () => {
        const searchTerm = e.target.value.trim();

        // Cargar propiedades con búsqueda
        const result = await rpc('/carousel/properties', {
            carousel_type: 'sale',
            search: searchTerm,  // Parámetro adicional
            limit: 12
        });

        // Actualizar carrusel
        carousel.properties = result.properties;
        carousel.render();
        carousel.initBootstrapCarousel();
    }, 500);
});

// Inicializar con búsqueda vacía
carousel.init();
```

## 🎯 Ejemplo 7: Carrusel solo para móviles

### CSS responsive específico

```css
/* Mostrar carrusel solo en móviles */
@media (min-width: 768px) {
    .mobile-only-carousel {
        display: none;
    }
}

@media (max-width: 767px) {
    .desktop-only-grid {
        display: none;
    }
}
```

### HTML con ambas versiones

```xml
<!-- Grid para desktop -->
<div class="desktop-only-grid row">
    <t t-foreach="properties" t-as="prop">
        <div class="col-md-3">
            <!-- Tarjeta de propiedad -->
        </div>
    </t>
</div>

<!-- Carrusel para móvil -->
<div class="mobile-only-carousel">
    <div id="carousel-mobile"></div>
</div>
```

## 🎯 Ejemplo 8: Integrar con formulario de contacto

### Agregar botón de contacto en tarjeta

```javascript
createPropertyCard(property) {
    return `
        <div class="col-md-3">
            <div class="card h-100">
                <!-- ... contenido de la tarjeta ... -->

                <div class="card-footer bg-transparent">
                    <div class="d-grid gap-2">
                        <a href="${property.url}" class="btn btn-outline-danger btn-sm">
                            Ver detalles
                        </a>
                        <button class="btn btn-danger btn-sm"
                                onclick="openContactModal(${property.id})">
                            <i class="fa fa-envelope me-1"></i>Contactar
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Función global para abrir modal de contacto
window.openContactModal = function(propertyId) {
    // Cargar datos de la propiedad
    const property = window.currentCarouselProperties.find(p => p.id === propertyId);

    // Abrir modal de Bootstrap
    const modal = new bootstrap.Modal(document.getElementById('contactModal'));

    // Prellenar formulario
    document.getElementById('property_id').value = propertyId;
    document.getElementById('property_name').value = property.name;

    modal.show();
};
```

## 🎯 Ejemplo 9: Carrusel con animaciones personalizadas

### CSS con animaciones

```css
/* Animación de entrada */
@keyframes slideInFromRight {
    from {
        opacity: 0;
        transform: translateX(100px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.carousel-item.active .bohio-property-card {
    animation: slideInFromRight 0.5s ease-out;
}

/* Stagger animation (efecto escalonado) */
.carousel-item.active .bohio-property-card:nth-child(1) {
    animation-delay: 0s;
}
.carousel-item.active .bohio-property-card:nth-child(2) {
    animation-delay: 0.1s;
}
.carousel-item.active .bohio-property-card:nth-child(3) {
    animation-delay: 0.2s;
}
.carousel-item.active .bohio-property-card:nth-child(4) {
    animation-delay: 0.3s;
}
```

## 🎯 Ejemplo 10: Carrusel con estadísticas

### Agregar contador y estadísticas

```xml
<section class="py-5">
    <div class="container">
        <!-- Estadísticas -->
        <div class="row mb-4">
            <div class="col-md-3 text-center">
                <h3 class="text-danger" id="total-properties">0</h3>
                <p class="text-muted">Propiedades Disponibles</p>
            </div>
            <div class="col-md-3 text-center">
                <h3 class="text-danger" id="avg-price">$0</h3>
                <p class="text-muted">Precio Promedio</p>
            </div>
            <div class="col-md-3 text-center">
                <h3 class="text-danger" id="avg-area">0 m²</h3>
                <p class="text-muted">Área Promedio</p>
            </div>
            <div class="col-md-3 text-center">
                <h3 class="text-danger" id="total-cities">0</h3>
                <p class="text-muted">Ciudades</p>
            </div>
        </div>

        <!-- Carrusel -->
        <div id="carousel-with-stats"></div>
    </div>
</section>
```

### JavaScript para calcular estadísticas

```javascript
async function initCarouselWithStats() {
    const carousel = new PropertyCarousel('carousel-with-stats', 'sale');
    await carousel.init();

    // Calcular estadísticas
    const properties = carousel.properties;

    const total = properties.length;
    const avgPrice = properties.reduce((sum, p) => sum + p.price, 0) / total;
    const avgArea = properties.reduce((sum, p) => sum + p.area, 0) / total;
    const cities = new Set(properties.map(p => p.city)).size;

    // Actualizar DOM
    document.getElementById('total-properties').textContent = total;
    document.getElementById('avg-price').textContent = `$${avgPrice.toLocaleString('es-CO', {maximumFractionDigits: 0})}`;
    document.getElementById('avg-area').textContent = `${avgArea.toFixed(0)} m²`;
    document.getElementById('total-cities').textContent = cities;
}

document.addEventListener('DOMContentLoaded', initCarouselWithStats);
```

---

**Documentación completa**: Ver [CARRUSELES_DINAMICOS.md](CARRUSELES_DINAMICOS.md)

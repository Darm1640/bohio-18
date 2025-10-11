# Sistema de Carruseles Dinámicos de Propiedades

## 📋 Descripción

Sistema completo para mostrar carruseles dinámicos de propiedades cargadas desde la base de datos de Odoo 18. Incluye tres tipos de carruseles:

1. **Propiedades en Arriendo** - Muestra propiedades disponibles para alquiler
2. **Venta de Inmuebles Usados** - Muestra propiedades usadas en venta (sin proyecto)
3. **Proyectos en Venta** - Muestra propiedades nuevas que pertenecen a proyectos

## 🏗️ Arquitectura

### Backend (Python)

**Controlador**: `controllers/main.py`

```python
@http.route(['/carousel/properties'], type='json', auth='public', website=True, csrf=False)
def carousel_properties(self, carousel_type='sale', limit=12, **kwargs):
```

**Parámetros**:
- `carousel_type`: Tipo de carrusel ('rent', 'sale', 'projects')
- `limit`: Número máximo de propiedades (default: 12)

**Filtros aplicados**:
- Solo propiedades activas (`active = True`)
- Solo propiedades disponibles (`state = 'free'`)
- Solo propiedades con ubicación GPS (`latitude != False AND longitude != False`)

**Filtros específicos por tipo**:

| Tipo | Filtro |
|------|--------|
| `rent` | `type_service IN ('rent', 'sale_rent')` |
| `sale` | `type_service IN ('sale', 'sale_rent')` AND `project_worksite_id = False` |
| `projects` | `type_service IN ('sale', 'sale_rent')` AND `project_worksite_id != False` |

### Frontend (JavaScript)

**Archivo**: `static/src/js/property_carousels.js`

**Clase Principal**: `PropertyCarousel`

```javascript
const carousel = new PropertyCarousel('carousel-rent', 'rent');
await carousel.init();
```

**Métodos**:
- `init()` - Inicializa el carrusel
- `loadProperties()` - Carga propiedades desde el servidor vía RPC
- `render()` - Renderiza el HTML del carrusel
- `createPropertyCard()` - Crea tarjeta individual de propiedad
- `initBootstrapCarousel()` - Inicializa Bootstrap Carousel

**Características**:
- Agrupa propiedades en slides de 4 tarjetas cada uno
- Auto-play cada 5 segundos
- Pausa al pasar el mouse
- Controles de navegación (anterior/siguiente)
- Indicadores de slide activo
- Responsive

### Estilos (CSS)

**Archivo**: `static/src/css/property_carousels.css`

**Características**:
- Controles circulares con color Bohío (#E31E24)
- Animaciones suaves en hover
- Indicadores personalizados
- Responsive para mobile, tablet y desktop
- Estados de loading y empty

## 📦 Estructura de Archivos

```
theme_bohio_real_estate/
│
├── controllers/
│   └── main.py                                    # Endpoint /carousel/properties
│
├── static/src/
│   ├── js/
│   │   └── property_carousels.js                 # Lógica del carrusel
│   └── css/
│       └── property_carousels.css                # Estilos
│
├── views/snippets/
│   └── property_carousels_snippet.xml            # Templates QWeb
│
└── __manifest__.py                                # Configuración del módulo
```

## 🚀 Uso

### Opción 1: Usar templates individuales

En tu página QWeb:

```xml
<!-- Carrusel de Arriendo -->
<t t-call="theme_bohio_real_estate.carousel_rent_section"/>

<!-- Carrusel de Venta -->
<t t-call="theme_bohio_real_estate.carousel_sale_section"/>

<!-- Carrusel de Proyectos -->
<t t-call="theme_bohio_real_estate.carousel_projects_section"/>
```

### Opción 2: Crear carrusel personalizado

#### 1. HTML

```html
<div class="property-carousel-container">
    <div id="carousel-custom" class="property-carousel-loading">
        <div class="spinner-border" role="status">
            <span class="visually-hidden">Cargando...</span>
        </div>
    </div>
</div>
```

#### 2. JavaScript

```javascript
document.addEventListener('DOMContentLoaded', function() {
    const customCarousel = new PropertyCarousel('carousel-custom', 'rent');
    customCarousel.init();
});
```

### Opción 3: Usar la API directamente

```javascript
import { rpc } from "@web/core/network/rpc";

const result = await rpc('/carousel/properties', {
    carousel_type: 'sale',
    limit: 20
});

console.log(result.properties); // Array de propiedades
```

## 📊 Estructura de Datos

### Respuesta del Endpoint

```json
{
    "success": true,
    "properties": [
        {
            "id": 123,
            "name": "Apartamento en El Poblado",
            "code": "APT-001",
            "price": 450000000,
            "price_formatted": "$450.000.000",
            "price_label": "Venta",
            "bedrooms": 3,
            "bathrooms": 2,
            "area": 85.5,
            "city": "Medellín",
            "state": "Antioquia",
            "neighborhood": "El Poblado",
            "property_type": "Apartamento",
            "image_url": "/web/image/product.template/123/image_512",
            "url": "/property/123",
            "project_id": 5,
            "project_name": "Torre del Parque",
            "latitude": 6.2442,
            "longitude": -75.5812
        }
    ],
    "total": 12,
    "carousel_type": "projects"
}
```

## 🎨 Personalización

### Cambiar número de propiedades por slide

Edita `property_carousels.js`:

```javascript
// Cambiar de 4 a 6 propiedades por slide
const itemsPerSlide = 6;
```

### Cambiar intervalo de auto-play

```javascript
this.carouselInstance = new bootstrap.Carousel(carouselEl, {
    interval: 8000,  // Cambiar a 8 segundos
    // ...
});
```

### Personalizar estilos

Edita `property_carousels.css`:

```css
/* Cambiar color de los controles */
.property-carousel-container .carousel-control-prev,
.property-carousel-container .carousel-control-next {
    background: rgba(0, 123, 255, 0.8); /* Azul */
}
```

### Agregar filtros adicionales

Edita el controlador en `controllers/main.py`:

```python
# Ejemplo: Solo propiedades con más de 2 habitaciones
if carousel_type == 'rent':
    domain.append(('num_bedrooms', '>=', 3))
```

## 🔧 Configuración

### Agregar a una página existente

1. Edita tu template QWeb
2. Agrega el contenedor del carrusel:

```xml
<section class="py-5">
    <div class="container">
        <h2>Propiedades Destacadas</h2>
        <div class="property-carousel-container">
            <div id="carousel-featured"></div>
        </div>
    </div>
</section>
```

3. Inicializa el carrusel:

```javascript
const featuredCarousel = new PropertyCarousel('carousel-featured', 'rent');
featuredCarousel.init();
```

### Crear endpoint personalizado

```python
@http.route(['/carousel/featured'], type='json', auth='public')
def carousel_featured(self, **kwargs):
    # Tu lógica personalizada
    domain = [
        ('is_property', '=', True),
        ('is_featured', '=', True)  # Campo personalizado
    ]
    properties = request.env['product.template'].sudo().search(domain, limit=10)
    # Serializar y retornar
```

## 📱 Responsive

### Breakpoints

| Ancho | Tarjetas por slide |
|-------|-------------------|
| < 576px | 1 tarjeta |
| 576px - 768px | 2 tarjetas |
| 768px - 992px | 3 tarjetas |
| > 992px | 4 tarjetas |

Para cambiar esto, modifica el HTML generado en `createPropertyCard()`:

```javascript
// Cambiar clases de columnas
return `
    <div class="col-12 col-sm-6 col-md-4 col-lg-3">
        <!-- col-12: 1 por fila en móvil -->
        <!-- col-sm-6: 2 por fila en tablet -->
        <!-- col-md-4: 3 por fila en tablet grande -->
        <!-- col-lg-3: 4 por fila en desktop -->
    </div>
`;
```

## 🐛 Troubleshooting

### Carrusel no se muestra

**Problema**: El contenedor muestra "Cargando..." indefinidamente

**Solución**:
1. Verificar que el endpoint `/carousel/properties` responde
2. Verificar la consola del navegador para errores JavaScript
3. Verificar que Bootstrap está cargado

```javascript
console.log(typeof bootstrap); // Debe ser 'object'
```

### Propiedades no se cargan

**Problema**: `result.properties` está vacío

**Solución**:
1. Verificar que existen propiedades con coordenadas GPS en la BD
2. Verificar el dominio de búsqueda en el controlador
3. Ver logs de Odoo:

```bash
tail -f /var/log/odoo/odoo.log | grep CAROUSEL
```

### Imágenes no se muestran

**Problema**: Las imágenes muestran "placeholder"

**Solución**:
1. Verificar que las propiedades tienen `image_1920` poblada
2. Verificar permisos de acceso a `/web/image`
3. Agregar imagen placeholder:

```bash
cp /ruta/placeholder.jpg theme_bohio_real_estate/static/src/img/
```

## ⚡ Optimización

### Caché del servidor

Agregar caché a la respuesta del controlador:

```python
from werkzeug.wrappers import Response

@http.route(['/carousel/properties'], type='json', auth='public')
def carousel_properties(self, carousel_type='sale', limit=12):
    # ... tu código ...

    response = Response(json.dumps(result))
    response.cache_control.max_age = 300  # 5 minutos
    return response
```

### Lazy loading de imágenes

Ya implementado con `loading="lazy"` en las imágenes.

### Reducir número de queries

El controlador ya usa `sudo()` para reducir checks de permisos.

## 📄 Licencia

LGPL-3

## 👥 Autor

BOHIO Real Estate - Odoo 18

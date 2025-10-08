# Vista de Lista/Mapa de Propiedades - Bohío Real Estate

## 📋 Descripción

Página de búsqueda y visualización de propiedades con dos vistas:
- **Vista Lista**: Grid de tarjetas con información de propiedades
- **Vista Mapa**: Mapa interactivo con OpenStreetMap/Leaflet

## 🎨 Características

### Diseño
- ✅ Tonos corporativos Bohío (Rojo #ff1d25, Negro #000000)
- ✅ Diseño oscuro moderno y profesional
- ✅ Totalmente responsivo (móvil, tablet, desktop)
- ✅ Animaciones y transiciones suaves

### Funcionalidades
- 🔍 **Filtros avanzados**:
  - Tipo de inmueble (apartamento, casa, lote, etc.)
  - Ciudad
  - Modalidad (venta/arriendo)
  - Habitaciones y baños
  - Rango de precio
  - Búsqueda por código (BOH-XXX)

- 📊 **Ordenamiento**:
  - Precio (menor a mayor / mayor a menor)
  - Habitaciones (más a menos)
  - Área (mayor a menor)
  - Más recientes

- 🗺️ **Mapa interactivo**:
  - OpenStreetMap con Leaflet
  - Marcadores personalizados con color Bohío
  - Popups con información de propiedades
  - Auto-ajuste de zoom según propiedades

## 📦 Archivos Creados

```
theme_bohio_real_estate/
├── views/
│   └── properties_list_map.xml          # Template QWeb
├── static/src/
│   ├── js/
│   │   └── properties_list_map.js       # Lógica JS (búsqueda, filtros, mapa)
│   └── scss/
│       └── properties_list_map.scss     # Estilos con tonos Bohío
└── __manifest__.py                       # Actualizado con nuevos assets

bohio_real_estate/
└── controllers/
    └── main.py                           # Ruta /properties/map actualizada
```

## 🚀 Instalación

### 1. Actualizar módulos
```bash
# Actualizar theme_bohio_real_estate
odoo-bin -u theme_bohio_real_estate -d tu_base_de_datos

# O actualizar bohio_real_estate si es necesario
odoo-bin -u bohio_real_estate -d tu_base_de_datos
```

### 2. Acceder a la página
```
http://tu-dominio/properties/map
```

## 🔌 APIs Utilizadas

La página consume las siguientes APIs JSON-RPC de Odoo:

### `/api/properties/search`
Búsqueda de propiedades con filtros

**Request:**
```json
{
  "filters": {
    "property_type": "apartment",
    "city_id": 123,
    "type_service": "rent",
    "bedrooms": 3,
    "bathrooms": 2,
    "price_min": 1000000,
    "price_max": 5000000
  },
  "page": 1,
  "limit": 100
}
```

**Response:**
```json
{
  "properties": [
    {
      "id": 1,
      "name": "Apartamento Moderno",
      "default_code": "BOH-001",
      "property_type": "apartment",
      "property_type_name": "Apartamento",
      "sale_price": 450000000,
      "rental_price": 2800000,
      "bedrooms": 3,
      "bathrooms": 2,
      "area": 85,
      "city": "Montería",
      "state": "Córdoba",
      "region": "El Poblado",
      "latitude": 8.748,
      "longitude": -75.881,
      "image_url": "/web/image/product.template/1/image_1920",
      "url": "/property/1"
    }
  ],
  "total": 25,
  "page": 1,
  "pages": 3,
  "limit": 100
}
```

### `/api/properties/search_by_code`
Búsqueda por código de propiedad

**Request:**
```json
{
  "code": "BOH-001"
}
```

**Response:**
```json
{
  "found": true,
  "id": 1,
  "name": "Apartamento Moderno",
  "code": "BOH-001",
  "url": "/property/1",
  "published": true
}
```

## 🗺️ Integración OpenStreetMap

### Librerías Externas
```html
<!-- CSS -->
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>

<!-- JS -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
```

### Configuración del Mapa
```javascript
// Centro inicial: Montería, Córdoba
map = L.map('mapCanvas').setView([8.7479, -75.8814], 13);

// Tile layer de OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
}).addTo(map);
```

### Marcadores Personalizados
```javascript
const iconoRojo = L.divIcon({
    className: 'bohio-map-marker',
    html: `<div class="marker-pin"></div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 28]
});
```

## 🎨 Personalización de Estilos

### Tonos Bohío (variables SCSS)
```scss
$bohio-red: #ff1d25;
$bohio-red-dark: #cc1720;
$bohio-black: #000000;
$bohio-gray: #333333;
```

### Modificar colores
Editar: `theme_bohio_real_estate/static/src/scss/properties_list_map.scss`

### Ajustar diseño de tarjetas
```scss
.property-card {
    // Personalizar aquí
}
```

## 📱 Responsive

### Breakpoints
- **Desktop**: > 1000px → 3 columnas
- **Tablet**: 640px - 1000px → 2 columnas
- **Móvil**: < 640px → 1 columna

## ⚙️ Campos del Modelo `product.template`

### Campos utilizados de `real_estate_bits`:
- `default_code` - Código BOH-XXX
- `property_type` - Tipo de inmueble
- `property_type_id.name` - Nombre del tipo
- `net_price` - Precio de venta
- `net_rental_price` - Precio de arriendo
- `num_bedrooms` - Habitaciones
- `num_bathrooms` - Baños
- `property_area` - Área en m²
- `latitude` - Latitud GPS
- `longitude` - Longitud GPS
- `city`, `city_id.name` - Ciudad
- `state_id.name` - Departamento
- `region_id.name` - Barrio/Región
- `state` - Estado (free, rented, unavailable)
- `website_published` - Publicado en web

## 🔧 Troubleshooting

### El mapa no se muestra
1. Verificar que Leaflet CSS/JS se carguen correctamente
2. Revisar consola del navegador
3. Verificar que las propiedades tengan coordenadas (`latitude`, `longitude`)

### No aparecen propiedades
1. Verificar que existan propiedades con `is_property=True` y `website_published=True`
2. Revisar filtros activos
3. Verificar endpoint `/api/properties/search` en Network tab

### Estilos no se aplican
```bash
# Limpiar assets
odoo-bin --dev=all -d tu_base_de_datos

# O actualizar módulo
odoo-bin -u theme_bohio_real_estate -d tu_base_de_datos
```

## 📝 Notas Técnicas

- Compatible con **Odoo 18**
- Requiere módulos: `bohio_real_estate`, `real_estate_bits`
- JavaScript usa **Odoo Module System** (`@odoo-module`)
- SCSS compilado automáticamente por Odoo
- Leaflet v1.9.4 (CDN)

## 🎯 Próximas Mejoras

- [ ] Filtros avanzados en mapa (clusters de marcadores)
- [ ] Vista de Street View
- [ ] Guardar búsquedas favoritas
- [ ] Compartir propiedades en redes sociales
- [ ] Comparador de propiedades
- [ ] Exportar resultados a PDF

---

**Desarrollado para Bohío Consultores** 🏠

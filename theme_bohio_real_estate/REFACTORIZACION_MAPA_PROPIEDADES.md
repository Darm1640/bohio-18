# Refactorización del Mapa de Propiedades - BOHIO Real Estate

## 📋 Resumen

Se ha refactorizado completamente el sistema de mapas de propiedades, convirtiéndolo en una estructura modular organizada en carpetas siguiendo las mejores prácticas de Odoo 18.

## 🏗️ Nueva Estructura

```
static/src/js/
├── utils/                    # Utilidades reutilizables
│   ├── geolocation.js       # Geolocalización y cálculo de distancias
│   ├── url_params.js        # Manejo de parámetros URL y filtros
│   └── dom_helpers.js       # Helpers para manipulación DOM
│
├── dom/                      # Manipulación DOM
│   └── markers.js           # Creación de marcadores (sin HTML strings)
│
└── widgets/                  # PublicWidgets
    └── map_widget.js        # Widget del mapa (patrón oficial Odoo 18)
```

## ✨ Características Principales

### 1. **Organización Modular**
- Código separado por responsabilidades
- Fácil mantenimiento y testing
- Reutilización de código en toda la aplicación

### 2. **Sin HTML Strings**
- Todo usa `createElement` (seguro contra XSS)
- Siguiendo las mejores prácticas investigadas

### 3. **Soporte de Filtros desde URL**
- Mantiene filtros del homepage/búsqueda
- No borra resultados previos
- Compatible con autocompletado

### 4. **PublicWidget Pattern**
- Patrón oficial de Odoo 18
- Lifecycle methods (start, destroy)
- Event handlers organizados

## 📂 Archivos Creados

### `utils/geolocation.js` (100+ líneas)

**Funciones exportadas:**
- `calculateDistance(lat1, lng1, lat2, lng2)` - Fórmula de Haversine
- `formatDistance(distanceKm)` - Formato legible (m/km)
- `tryGeolocation()` - Promise para obtener ubicación
- `isGeolocationSupported()` - Verifica soporte del navegador

**Constantes:**
- `DISTANCE_THRESHOLD_KM` - Umbral para mostrar nombres (5km)
- `ZOOM_WITH_USER` - Zoom cuando se muestra ubicación (13)
- `DEFAULT_CENTER` - Centro por defecto [Montería]
- `DEFAULT_ZOOM` - Zoom por defecto (12)

### `utils/url_params.js` (150+ líneas)

**Funciones exportadas:**
- `getUrlParam(key, defaultValue)` - Obtiene parámetro individual
- `updateUrlParams(params, replace)` - Actualiza URL sin recargar
- `getPropertyFiltersFromUrl()` - Extrae todos los filtros
- `filtersToUrlParams(filters)` - Convierte filtros a params
- `hasActiveFilters()` - Verifica si hay filtros activos
- `cleanFilters(filters)` - Limpia valores nulos

**Filtros soportados:**
- `search` - Búsqueda por texto
- `service` - Tipo de servicio (rent/sale/sale_rent)
- `property_type` - Tipo de propiedad
- `city`, `neighborhood`, `state` - Ubicación
- `price_min`, `price_max` - Rango de precio
- `bedrooms`, `bathrooms` - Características
- `area_min`, `area_max` - Rango de área
- `project_id` - Proyecto específico

### `utils/dom_helpers.js` (300+ líneas)

**Categorías de funciones:**

**Selectores:**
- `getElement(selector, context)` - Selector con validación
- `getElements(selector, context)` - Múltiples elementos
- `elementExists(selector, context)` - Verifica existencia

**Creación:**
- `createElement(tag, className, textContent)` - Crea elemento con clase
- `createButton(options)` - Botón con icono Bootstrap
- `createLink(options)` - Link con icono Bootstrap

**Manipulación:**
- `showElement(element)` - Muestra elemento
- `hideElement(element)` - Oculta elemento
- `toggleElement(element)` - Toggle visibilidad
- `addClass(element, className)` - Agrega clases
- `removeClass(element, className)` - Remueve clases
- `clearElement(element)` - Limpia contenido
- `removeElement(element)` - Remueve del DOM

**Eventos:**
- `addEventListener(element, event, handler)` - Event listener con validación
- `removeEventListener(element, event, handler)` - Remueve listener

**Estados:**
- `showLoading(element, message)` - Muestra loading
- `hideLoading(element)` - Oculta loading
- `disableElement(element)` - Deshabilita
- `enableElement(element)` - Habilita

### `dom/markers.js` (300+ líneas)

**Funciones privadas (creación de elementos):**
- `createMarkerIcon(type)` - Icono según tipo
- `createMarkerIconContainer(type)` - Contenedor del icono
- `createMarkerPrice(price)` - Elemento de precio
- `createMarkerName(name)` - Elemento de nombre
- `createMarkerElement(property)` - Elemento completo del marcador

**Funciones de popup:**
- `createPopupTitle(name)` - Título del popup
- `createPopupPrice(price)` - Precio en popup
- `createPopupFeature(iconClass, text)` - Característica individual
- `createPopupButton(url)` - Botón de detalles
- `createPopupElement(property)` - Popup completo

**Funciones exportadas:**
- `createPropertyMarker(property, L)` - Marcador de Leaflet completo
- `updateMarkersDistance(markers, userLocation)` - Actualiza según distancia
- `createUserLocationIcon(L)` - Icono del usuario
- `createUserMarker(userLocation, L)` - Marcador del usuario

### `widgets/map_widget.js` (500+ líneas)

**Estructura del Widget:**
```javascript
const BohioMapWidget = publicWidget.Widget.extend({
    selector: '.bohio-map-container',

    events: {
        'click .btn-geolocate': '_onGeolocateClick',
        'click .btn-reset-filters': '_onResetFiltersClick',
    },

    // Lifecycle
    start: function() { ... },
    destroy: function() { ... },

    // Métodos públicos
    manualGeolocate: async function() { ... },

    // Métodos privados
    _initState: function() { ... },
    _initMap: async function() { ... },
    _loadProperties: async function() { ... },
    _createMap: function(data) { ... },
    _createMarkers: function(properties) { ... },
    _showUserLocation: function() { ... },
    _reloadProperties: async function(newFilters) { ... },
    // ... más métodos
});
```

**Características del Widget:**
- ✅ Validación DOM completa
- ✅ Manejo de errores robusto
- ✅ Soporte de filtros desde URL
- ✅ No borra resultados previos
- ✅ Actualización dinámica de marcadores
- ✅ Geolocalización condicional (solo si no hay filtros)
- ✅ Event handlers organizados
- ✅ Lifecycle methods implementados

## 🔄 Flujo de Datos

### Caso 1: Carga Directa (sin filtros)
```
Usuario accede a /mapa
  ↓
MapWidget.start()
  ↓
_initState() → filters = {} (vacío)
  ↓
tryGeolocation() → obtiene ubicación
  ↓
_loadProperties() → params = { user_lat, user_lng }
  ↓
RPC /api/properties/mapa
  ↓
Crear marcadores + mostrar usuario
```

### Caso 2: Con Filtros desde Homepage
```
Usuario busca en homepage: "Montería, Arriendo, Apartamento"
  ↓
Redirect a /mapa?search=Montería&service=rent&property_type=apartment
  ↓
MapWidget.start()
  ↓
_initState() → filters = { search, service, property_type }
  ↓
NO llama tryGeolocation() (ya hay filtros)
  ↓
_loadProperties() → params = { search, service, property_type }
  ↓
RPC /api/properties/mapa
  ↓
Crear marcadores (sin ubicación de usuario)
  ↓
Mostrar mensaje: "Mostrando X propiedades - Búsqueda: Montería | Servicio: Arriendo | Tipo: Apartamento"
```

### Caso 3: Geolocalización Manual
```
Usuario hace clic en botón "Mi Ubicación"
  ↓
_onGeolocateClick()
  ↓
tryGeolocation() → obtiene ubicación
  ↓
_showUserLocation() → muestra marcador azul
  ↓
_reloadProperties() → mantiene filtros existentes + agrega ubicación
  ↓
Actualiza mapa con nuevos marcadores cerca del usuario
```

## 📦 Actualización de __manifest__.py

```python
'assets': {
    'web.assets_frontend': [
        # ... otros assets ...

        # JavaScript - Utils (Orden: utils primero, luego DOM, luego widgets)
        'theme_bohio_real_estate/static/src/js/utils/geolocation.js',
        'theme_bohio_real_estate/static/src/js/utils/url_params.js',
        'theme_bohio_real_estate/static/src/js/utils/dom_helpers.js',

        # JavaScript - DOM Manipulation
        'theme_bohio_real_estate/static/src/js/dom/markers.js',

        # JavaScript - Widgets (PublicWidget)
        'theme_bohio_real_estate/static/src/js/widgets/map_widget.js',
    ],
}
```

**IMPORTANTE:** El orden es crítico:
1. Utils primero (geolocation, url_params, dom_helpers)
2. DOM después (markers usa utils)
3. Widgets al final (map_widget usa todo lo anterior)

## 🎯 Ventajas de la Nueva Estructura

### Para Desarrollo
- ✅ Código más limpio y organizado
- ✅ Fácil de entender y mantener
- ✅ Testeable (funciones puras)
- ✅ Reutilizable en otros módulos

### Para Seguridad
- ✅ Sin HTML strings (previene XSS)
- ✅ Validación DOM completa
- ✅ Manejo de errores robusto

### Para UX
- ✅ Mantiene filtros del usuario
- ✅ No borra búsquedas previas
- ✅ Geolocalización inteligente
- ✅ Mensajes claros y contextuales

### Para Odoo 18
- ✅ Sigue el patrón PublicWidget oficial
- ✅ Lifecycle methods implementados
- ✅ Imports desde @web/ paths
- ✅ Uso de rpc nativo

## 📖 Cómo Usar

### En Templates XML

```xml
<!-- Contenedor del mapa con clase correcta -->
<div class="bohio-map-container">
    <!-- Loading overlay -->
    <div id="map-loading" class="map-loading" style="display: none;">
        <div class="spinner-border text-danger"></div>
        <p>Cargando mapa...</p>
    </div>

    <!-- Contenedor del mapa Leaflet -->
    <div id="bohio-map" style="height: 600px;"></div>

    <!-- Contador de propiedades (opcional) -->
    <div class="property-count">
        Mostrando <span id="property-count">0</span> propiedades
    </div>

    <!-- Botones de acción (opcional) -->
    <button class="btn btn-primary btn-geolocate">
        <i class="bi bi-geo-alt-fill"></i> Mi Ubicación
    </button>

    <button class="btn btn-outline-danger btn-reset-filters">
        <i class="bi bi-x-circle"></i> Limpiar Filtros
    </button>

    <!-- Mensaje de filtros activos (opcional) -->
    <div class="filters-active-message" style="display: none;"></div>
</div>
```

### Desde JavaScript (programáticamente)

```javascript
import { rpc } from "@web/core/network/rpc";
import { updateUrlParams } from '../utils/url_params';

// Actualizar filtros y redirigir al mapa
async function searchProperties(filters) {
    // Actualizar URL con filtros
    updateUrlParams(filters);

    // Redirigir al mapa
    window.location.href = '/mapa';
}

// Ejemplo: Buscar apartamentos en arriendo en Montería
searchProperties({
    search: 'Montería',
    service: 'rent',
    property_type: 'apartment'
});
```

## 🔍 Debugging

### Console Logs Importantes

```javascript
// Al inicializar
'[MapWidget] Initializing map...'
'[MapWidget] Filters from URL: {...}'
'[MapWidget] Has active filters: true/false'

// Al cargar propiedades
'[MapWidget] Loading properties with params: {...}'
'[MapWidget] Properties loaded: 42'

// Al crear mapa
'[MapWidget] Map created at [8.7479, -75.8814] zoom 12'
'[MapWidget] Created 42 markers'

// Geolocalización
'[Geolocation] User location obtained: {lat: ..., lng: ...}'
'[MapWidget] User location shown on map'
```

### Verificar Filtros Activos

```javascript
// En consola del navegador
import { getPropertyFiltersFromUrl, hasActiveFilters } from '../utils/url_params';

const filters = getPropertyFiltersFromUrl();
console.log('Filtros activos:', filters);
console.log('¿Tiene filtros?:', hasActiveFilters());
```

## 🚀 Próximos Pasos

1. ✅ **COMPLETADO:** Estructura modular con utils, dom, widgets
2. ✅ **COMPLETADO:** Sin HTML strings (todo createElement)
3. ✅ **COMPLETADO:** Soporte de filtros desde URL
4. ✅ **COMPLETADO:** PublicWidget pattern
5. ⏳ **PENDIENTE:** Testing unitario de utilidades
6. ⏳ **PENDIENTE:** Documentación de API endpoints
7. ⏳ **PENDIENTE:** Refactorizar otros componentes con el mismo patrón

## 📝 Notas Importantes

1. **Leaflet debe estar cargado** antes del widget (hereda de `real_estate_bits`)
2. **El selector `.bohio-map-container`** debe existir en el DOM
3. **Los filtros se leen automáticamente** de la URL al inicializar
4. **La geolocalización es condicional:** solo se ejecuta si NO hay filtros activos
5. **El widget limpia recursos** correctamente en el método `destroy()`

## 🛠️ Mantenimiento

### Agregar Nuevo Filtro

1. Actualizar `getPropertyFiltersFromUrl()` en `url_params.js`
2. Actualizar `_updateFiltersMessage()` en `map_widget.js`
3. Actualizar endpoint `/api/properties/mapa` en backend

### Agregar Nueva Utilidad

1. Crear función en archivo correspondiente (`utils/`, `dom/`)
2. Exportar la función
3. Importar donde se necesite
4. Actualizar esta documentación

## 📚 Referencias

- [Odoo 18 PublicWidget Pattern](.claude/knowledge/odoo-website/publicwidget-patterns.md)
- [DOM Validation Patterns](.claude/knowledge/javascript/dom-validation-patterns.md)
- [Odoo 18 Development Standards](.claude/principles/odoo-18-development-standards.md)
- [Investigación Oficial Odoo 18](INVESTIGACION_ODOO18_REPOSITORIO_OFICIAL.md)

---

**Autor:** Claude Code Agent
**Fecha:** 2025-01-13
**Versión:** 1.0.0
**Módulo:** theme_bohio_real_estate
**Odoo Version:** 18.0

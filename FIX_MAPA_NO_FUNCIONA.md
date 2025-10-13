# FIX: Mapa en Detalle de Propiedad No Funciona

## Fecha: 2025-10-12
## Problema: El botón "Mapa" no muestra el mapa correctamente

---

## 🔍 DIAGNÓSTICO

### Flujo del Mapa:

1. **Página carga** → `DOMContentLoaded` (línea 8)
2. **Se ejecuta** → `initializeMap()` (línea 234)
3. **Se CREA la función** → `window.initPropertyMap()` (línea 244)
4. **Usuario click en "Mapa"** → `toggleMapView()` (línea 208)
5. **Se llama** → `window.initPropertyMap()` (línea 224)
6. **Se inicializa** → Leaflet Map (línea 252)

### Código Actual (property_detail_gallery.js):

**Línea 234-263** - Función `initializeMap()`:
```javascript
function initializeMap() {
    const mapElement = document.getElementById('property_map');
    if (!mapElement) return;

    const lat = parseFloat(mapElement.dataset.lat);
    const lng = parseFloat(mapElement.dataset.lng);
    const name = mapElement.dataset.name;

    if (lat && lng) {
        // Solo inicializar cuando se muestre
        window.initPropertyMap = function() {
            if (window.propertyMap) return; // Ya inicializado

            if (typeof L === 'undefined') {  // <-- VERIFICAR ESTO
                console.error('❌ Leaflet no está cargado');
                return;
            }

            window.propertyMap = L.map('property_map').setView([lat, lng], 15);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(window.propertyMap);

            L.marker([lat, lng]).addTo(window.propertyMap)
                .bindPopup('<b>' + name + '</b>')
                .openPopup();
        };
    }
}
```

---

## 🧪 VERIFICACIONES A HACER

### Verificación 1: ¿Leaflet está cargado?

Abrir la consola del navegador en `/property/15360`:

```javascript
// Verificar si Leaflet está disponible
console.log('Leaflet disponible:', typeof L !== 'undefined');
console.log('Objeto L:', window.L);

// Ver versión si está disponible
if (typeof L !== 'undefined') {
    console.log('Leaflet version:', L.version);
}
```

**Resultado esperado**:
- Si `L` es `undefined` → **Leaflet NO se está cargando**
- Si `L` existe → **Leaflet OK, problema en inicialización**

### Verificación 2: ¿El elemento #property_map existe?

```javascript
// Verificar elemento del mapa
const mapEl = document.getElementById('property_map');
console.log('Elemento mapa:', mapEl);

if (mapEl) {
    console.log('Latitud:', mapEl.dataset.lat);
    console.log('Longitud:', mapEl.dataset.lng);
    console.log('Nombre:', mapEl.dataset.name);
}
```

**Resultado esperado**:
- Si es `null` → **El elemento no está en el HTML**
- Si existe pero NO tiene lat/lng → **Propiedad sin coordenadas**

### Verificación 3: ¿La función initPropertyMap se crea?

```javascript
// Verificar si la función existe
console.log('initPropertyMap existe:', typeof window.initPropertyMap === 'function');

// Intentar llamarla manualmente
if (typeof window.initPropertyMap === 'function') {
    window.initPropertyMap();
}
```

**Resultado esperado**:
- Si la función existe → Debería inicializar el mapa
- Si no existe → Hay un error en `initializeMap()`

### Verificación 4: ¿Qué pasa al hacer click en "Mapa"?

Abrir consola y hacer click en el botón "Mapa":

```javascript
// Ver consola al hacer click
// Debería aparecer: "🗺️ Toggle mapa"
```

**Errores posibles**:
- `TypeError: Cannot read property 'invalidateSize' of undefined` → El mapa no se creó
- `L is not defined` → Leaflet no está cargado
- Nada aparece → El elemento `#mapViewSection` no existe

---

## 🔧 POSIBLES PROBLEMAS Y SOLUCIONES

### Problema 1: Leaflet No Está Cargado

**Causa**: El CDN de Leaflet no se está cargando o hay un error de red.

**Verificación en __manifest__.py** (líneas 71-73):
```python
'web.assets_frontend': [
    # External - Leaflet Maps
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',  # CSS
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',   # JS
```

**Solución 1A**: Descargar Leaflet localmente

1. Descargar archivos:
   - `https://unpkg.com/leaflet@1.9.4/dist/leaflet.css`
   - `https://unpkg.com/leaflet@1.9.4/dist/leaflet.js`

2. Guardar en:
   - `theme_bohio_real_estate/static/src/lib/leaflet/leaflet.css`
   - `theme_bohio_real_estate/static/src/lib/leaflet/leaflet.js`

3. Actualizar manifest:
```python
'web.assets_frontend': [
    # External - Leaflet Maps (LOCAL)
    'theme_bohio_real_estate/static/src/lib/leaflet/leaflet.css',
    'theme_bohio_real_estate/static/src/lib/leaflet/leaflet.js',
```

**Solución 1B**: Agregar verificación con fallback

```javascript
// En property_detail_gallery.js, línea 247
if (typeof L === 'undefined') {
    console.error('❌ Leaflet no está cargado');
    alert('El mapa no puede cargarse. Por favor recarga la página.');
    return;
}
```

### Problema 2: El elemento #property_map no existe

**Causa**: El template no renderiza el div del mapa o está oculto.

**Verificación en property_detail_template.xml** (líneas 243-251):
```xml
<!-- Mapa (inicialmente oculto) -->
<div id="mapViewSection" class="mb-4" style="display: none;">
    <hr/>
    <h5><i class="fa fa-map text-primary"/> Ubicación en el Mapa</h5>
    <div id="property_map" style="height: 400px; width: 100%;" class="mb-4"
         t-att-data-lat="property.latitude"
         t-att-data-lng="property.longitude"
         t-att-data-name="property.name"/>
</div>
```

**Solución 2**: Verificar que la propiedad TIENE coordenadas

Si `property.latitude` o `property.longitude` son `False`, el mapa no se mostrará.

**Agregar debug** al template:
```xml
<!-- ANTES del mapa, agregar esto temporalmente -->
<div class="alert alert-info">
    DEBUG: Lat=<span t-esc="property.latitude"/> / Lng=<span t-esc="property.longitude"/>
</div>
```

### Problema 3: El mapa se inicializa pero no se ve

**Causa**: CSS o tamaño del contenedor incorrecto.

**Solución 3**: Asegurar que el mapa tenga altura explícita

```javascript
// Modificar toggleMapView() línea 208
window.toggleMapView = function() {
    console.log('🗺️ Toggle mapa');
    const mapSection = document.getElementById('mapViewSection');
    const carouselContainer = document.querySelector('.property-gallery-container');

    if (!mapSection || !carouselContainer) {
        console.error('❌ Elementos de mapa/carrusel no encontrados');
        return;
    }

    if (mapSection.style.display === 'none' || !mapSection.style.display) {
        mapSection.style.display = 'block';
        carouselContainer.style.display = 'none';

        // IMPORTANTE: Esperar a que el DOM se actualice
        setTimeout(() => {
            // Forzar re-renderizado del mapa
            if (window.propertyMap) {
                window.propertyMap.invalidateSize();
            } else if (typeof window.initPropertyMap === 'function') {
                window.initPropertyMap();

                // Forzar resize después de inicializar
                setTimeout(() => {
                    if (window.propertyMap) {
                        window.propertyMap.invalidateSize();
                    }
                }, 100);
            }
        }, 100);  // <-- AGREGAR DELAY
    } else {
        mapSection.style.display = 'none';
        carouselContainer.style.display = 'block';
    }
};
```

### Problema 4: Botón "Mapa" no aparece

**Causa**: La condición `t-if` no se cumple.

**Verificación en property_detail_template.xml** (línea 113):
```xml
<button class="btn btn-light px-3 py-2 fw-bold" onclick="toggleMapView()"
        t-if="property.latitude and property.longitude">
    <i class="fa fa-map me-2"></i>Mapa
</button>
```

**Solución 4**: Verificar que la propiedad tenga coordenadas guardadas.

Si no las tiene, agregar coordenadas de prueba:

```python
# En Python (consola o script)
property = env['product.template'].browse(15360)
property.write({
    'latitude': 8.7538,  # Montería, Colombia
    'longitude': -75.8818
})
```

---

## 🎯 SOLUCIÓN RÁPIDA (MEJORADA)

Voy a mejorar la función `toggleMapView()` para agregar logs y manejar mejor los timeouts:

**Reemplazar en property_detail_gallery.js (línea 208-231)**:

```javascript
// Alternar entre imagen y mapa
window.toggleMapView = function() {
    console.log('🗺️ Toggle mapa - START');
    const mapSection = document.getElementById('mapViewSection');
    const carouselContainer = document.querySelector('.property-gallery-container');

    console.log('  - mapSection:', mapSection ? 'OK' : 'NO ENCONTRADO');
    console.log('  - carouselContainer:', carouselContainer ? 'OK' : 'NO ENCONTRADO');

    if (!mapSection || !carouselContainer) {
        console.error('❌ Elementos de mapa/carrusel no encontrados');
        return;
    }

    if (mapSection.style.display === 'none' || !mapSection.style.display) {
        console.log('  - Mostrando mapa, ocultando carrusel');
        mapSection.style.display = 'block';
        carouselContainer.style.display = 'none';

        // Esperar a que el DOM se actualice antes de inicializar
        setTimeout(() => {
            console.log('  - Verificando Leaflet:', typeof L !== 'undefined' ? 'Cargado' : 'NO CARGADO');

            if (window.propertyMap) {
                console.log('  - Mapa ya existe, invalidando tamaño');
                window.propertyMap.invalidateSize();
            } else if (typeof window.initPropertyMap === 'function') {
                console.log('  - Inicializando mapa por primera vez');
                window.initPropertyMap();

                // Forzar resize después de crear
                setTimeout(() => {
                    if (window.propertyMap) {
                        console.log('  - Forzando resize del mapa');
                        window.propertyMap.invalidateSize();
                    }
                }, 200);
            } else {
                console.error('❌ initPropertyMap no está definida');
            }
        }, 150);
    } else {
        console.log('  - Ocultando mapa, mostrando carrusel');
        mapSection.style.display = 'none';
        carouselContainer.style.display = 'block';
    }

    console.log('🗺️ Toggle mapa - END');
};
```

---

## 📋 CHECKLIST DE DEBUGGING

Por favor ejecutar estas verificaciones:

- [ ] Verificación 1: Leaflet cargado (`typeof L`)
- [ ] Verificación 2: Elemento `#property_map` existe
- [ ] Verificación 3: Función `initPropertyMap` existe
- [ ] Verificación 4: Click en botón "Mapa"
- [ ] Verificar que la propiedad tiene lat/lng
- [ ] Ver errores en consola al hacer click

---

## 🚀 PRÓXIMOS PASOS

1. **PRIMERO**: Ejecutar las 4 verificaciones arriba y reportar resultados
2. **SEGUNDO**: Aplicar la solución mejorada de `toggleMapView()`
3. **TERCERO**: Si Leaflet no está cargado, descargar localmente (Solución 1A)

**Con esta información sabré exactamente dónde está el problema.**

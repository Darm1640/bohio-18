# Correcciones Finales: Mapa y Geolocalización

## Problemas Corregidos

### 1. Error "L is not defined"

**Causa:** Leaflet se intentaba usar antes de cargarse

**Solución:**
- Agregado timeout máximo de 10 segundos
- Logs detallados de carga
- Mejor manejo de errores

```javascript
initMap() {
    console.log('[MAP] Esperando a que Leaflet este disponible...');

    let attempts = 0;
    const maxAttempts = 100;
    const checkLeaflet = setInterval(() => {
        attempts++;
        if (typeof L !== 'undefined') {
            clearInterval(checkLeaflet);
            console.log('[MAP] Leaflet disponible, creando mapa...');
            this.createMap();
        } else if (attempts >= maxAttempts) {
            clearInterval(checkLeaflet);
            console.error('[MAP] Leaflet no se cargo despues de 10 segundos');
        }
    }, 100);
}
```

---

### 2. Geolocalización del Usuario Implementada

**Nueva funcionalidad:**
- Al abrir el mapa, solicita ubicación del usuario
- Centra el mapa en la ubicación del usuario
- Muestra pin azul con la ubicación
- Carga propiedades cercanas ordenadas por distancia

```javascript
getUserLocation() {
    console.log('[MAP] Solicitando ubicacion del usuario...');

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const userLat = position.coords.latitude;
            const userLng = position.coords.longitude;

            console.log(`[MAP] Ubicacion del usuario: ${userLat}, ${userLng}`);

            // Centrar mapa
            this.map.setView([userLat, userLng], 13);

            // Agregar pin de usuario
            const userIcon = L.divIcon({
                className: 'user-location-marker',
                html: `<div style="
                    background: #4285F4;
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    border: 3px solid white;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                "></div>`
            });

            L.marker([userLat, userLng], { icon: userIcon })
                .addTo(this.map)
                .bindPopup('<b>Tu ubicación</b>');

            // Cargar propiedades cercanas
            this.loadNearbyProperties(userLat, userLng);
        },
        (error) => {
            console.warn('[MAP] No se pudo obtener ubicacion:', error.message);
            // Cargar propiedades normales
            this.loadMapProperties();
        }
    );
}
```

---

### 3. Popup del Mapa Mejorado

**Información mostrada:**
- Imagen de la propiedad (180px altura)
- Tipo de propiedad (Apartamento, Casa, etc.)
- **Barrio, Ciudad** (formato: "Centro, Montería")
- Precio formateado
- Área en m²
- Habitaciones
- Baños
- **Distancia desde ubicación** (badge azul)
- Botón "Ver Detalles"

```javascript
// Construir ubicación: Barrio, Ciudad
let locationParts = [];
if (prop.neighborhood || prop.region) {
    locationParts.push(prop.neighborhood || prop.region);
}
if (prop.city) {
    locationParts.push(prop.city);
}
const location = locationParts.join(', ');

// Tipo de propiedad traducido
const propertyTypeLabels = {
    'apartment': 'Apartamento',
    'house': 'Casa',
    'lot': 'Lote',
    'commercial': 'Comercial'
};
const propertyType = propertyTypeLabels[prop.property_type] || '';

// Distancia si está disponible
const distanceText = prop.distance_km ?
    `<span class="badge bg-info">${prop.distance_km} km</span>` : '';
```

**Popup HTML:**
```html
<div class="property-popup-card">
    <div class="popup-image">
        <img src="..."/>
        <div class="badge bg-info">2.5 km</div>  <!-- Distancia -->
    </div>
    <div class="popup-content">
        <h6>Apartamento Centro</h6>
        <p><i class="fa fa-building"></i> Apartamento</p>  <!-- Tipo -->
        <p><i class="fa fa-map-marker-alt"></i> Centro, Montería</p>  <!-- Barrio, Ciudad -->
        <p class="price">$250.000.000</p>
        <div class="features">
            <span><i class="fa fa-ruler-combined"></i> 85 m²</span>
            <span><i class="fa fa-bed"></i> 3 hab</span>
            <span><i class="fa fa-bath"></i> 2 baños</span>
        </div>
        <a href="/property/123" class="btn btn-danger">
            Ver Detalles <i class="fa fa-arrow-right"></i>
        </a>
    </div>
</div>
```

---

### 4. Carga de Propiedades Cercanas

```javascript
async loadNearbyProperties(userLat, userLng) {
    console.log(`[MAP] Cargando propiedades cercanas a: ${userLat}, ${userLng}`);

    try {
        const result = await rpc('/bohio/api/properties/map', {
            ...this.filters,
            ref_lat: userLat,  // Ubicación del usuario
            ref_lng: userLng,
            limit: 200
        });

        if (result.success) {
            const mapProperties = result.properties || [];
            console.log(`[MAP] Propiedades cercanas encontradas: ${mapProperties.length}`);

            // Las propiedades vienen ordenadas por distancia
            this.updateMap(mapProperties);
        }
    } catch (error) {
        console.error('[MAP] Error cargando propiedades cercanas:', error);
        this.loadMapProperties();
    }
}
```

---

## Flujo Completo

### 1. Usuario abre página `/properties`

```
[MAP] Contenedor del mapa no encontrado  (grid view activo)
```

### 2. Usuario hace click en "Vista Mapa"

```
[MAP] Esperando a que Leaflet este disponible...
[MAP] Leaflet disponible, creando mapa...
[MAP] Creando mapa...
[MAP] Mapa creado exitosamente
[MAP] Solicitando ubicacion del usuario...
```

### 3A. Usuario PERMITE geolocalización

```
[MAP] Ubicacion del usuario: 10.9685, -74.7813
[MAP] Cargando propiedades cercanas a: 10.9685, -74.7813
[MAP] Respuesta del endpoint: {success: true, properties: Array(150)}
[MAP] Propiedades cercanas encontradas: 150
[MAP] Actualizando mapa con 150 propiedades
[MAP] Propiedad: 1 Lat: 10.9690 Lng: -74.7820
[MAP] Propiedad: 2 Lat: 10.9700 Lng: -74.7830
...
[MAP] Markers agregados: 150 de 150
[MAP] Ajustando vista a 150 puntos
```

### 3B. Usuario DENIEGA geolocalización

```
[MAP] No se pudo obtener ubicacion: User denied geolocation
[MAP] Cargando propiedades para mapa con filtros: {}
[MAP] Respuesta del endpoint: {success: true, properties: Array(200)}
[MAP] Propiedades con coordenadas: 200
[MAP] Actualizando mapa con 200 propiedades
...
[MAP] Markers agregados: 200 de 200
```

---

## Visualización del Mapa

### Pin de Usuario
```
┌────────────┐
│            │
│     ●      │  ← Pin azul circular
│            │
└────────────┘
```

### Pin de Propiedad
```
┌──────────────────┐
│   $250.000.000   │  ← Precio en pin rojo
└────────┬─────────┘
         │
         ▼  ← Flecha
```

### Popup al hacer Click
```
╔═══════════════════════════╗
║ [Imagen de la propiedad]  ║
║ [Badge: 2.5 km]           ║
╠═══════════════════════════╣
║ Apartamento Centro        ║
║ 🏢 Apartamento            ║
║ 📍 Centro, Montería       ║
║ $250.000.000              ║
║                           ║
║ 📏 85m² 🛏️ 3hab 🚿 2baños║
║                           ║
║ [Ver Detalles →]          ║
╚═══════════════════════════╝
```

---

## Permiso de Geolocalización

El navegador mostrará un popup:

```
┌─────────────────────────────────────┐
│ bohioconsultores.com desea          │
│ conocer tu ubicación                │
│                                     │
│  [Bloquear]      [Permitir]        │
└─────────────────────────────────────┘
```

**Si permite:**
- Mapa centrado en tu ubicación
- Pin azul en tu posición
- Propiedades ordenadas por cercanía
- Badge con distancia en km

**Si bloquea:**
- Mapa centrado en Montería
- Propiedades ordenadas por cercanía a oficina BOHIO
- Sin badge de distancia

---

## Logs de Depuración

### Logs Normales (éxito)
```
[MAP] Esperando a que Leaflet este disponible...
[MAP] Leaflet disponible, creando mapa...
[MAP] Creando mapa...
[MAP] Mapa creado exitosamente
[MAP] Solicitando ubicacion del usuario...
[MAP] Ubicacion del usuario: 10.9685, -74.7813
[MAP] Cargando propiedades cercanas a: 10.9685, -74.7813
[MAP] Respuesta del endpoint: {success: true, count: 150}
[MAP] Propiedades cercanas encontradas: 150
[MAP] Actualizando mapa con 150 propiedades
[MAP] Markers agregados: 150 de 150
[MAP] Ajustando vista a 150 puntos
```

### Logs de Error (Leaflet no carga)
```
[MAP] Esperando a que Leaflet este disponible...
[MAP] Esperando a que Leaflet este disponible...
... (100 intentos)
[MAP] Leaflet no se cargo despues de 10 segundos
```

### Logs de Advertencia (sin coordenadas)
```
[MAP] Actualizando mapa con 40 propiedades
[MAP] Propiedad: 1 Lat: null Lng: null
[MAP] Propiedad sin coordenadas: 1 Apartamento Centro
...
[MAP] Markers agregados: 0 de 40
[MAP] No hay coordenadas para ajustar vista
```

---

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `static/src/js/property_shop.js` | getUserLocation(), loadNearbyProperties(), popup mejorado, logs |

---

## Próximos Pasos Opcionales

### 1. Cache de Ubicación
```javascript
// Guardar ubicación en sessionStorage
sessionStorage.setItem('user_location', JSON.stringify({
    lat: userLat,
    lng: userLng,
    timestamp: Date.now()
}));

// Leer ubicación guardada (válida por 1 hora)
const cached = sessionStorage.getItem('user_location');
if (cached) {
    const {lat, lng, timestamp} = JSON.parse(cached);
    if (Date.now() - timestamp < 3600000) {
        return {lat, lng};
    }
}
```

### 2. Botón "Usar mi ubicación"
```html
<button class="btn btn-outline-primary" id="use-my-location">
    <i class="fa fa-crosshairs"></i> Usar mi ubicación
</button>
```

### 3. Filtro de Radio
```html
<label>Radio de búsqueda</label>
<select id="search-radius">
    <option value="1">1 km</option>
    <option value="5" selected>5 km</option>
    <option value="10">10 km</option>
    <option value="20">20 km</option>
</select>
```

---

## Resumen

Ahora el mapa:
1. ✅ Espera a que Leaflet se cargue
2. ✅ Solicita ubicación del usuario
3. ✅ Centra en ubicación del usuario (o Montería)
4. ✅ Muestra pin azul de ubicación
5. ✅ Carga propiedades cercanas ordenadas por distancia
6. ✅ Muestra popup con barrio, tipo, características y distancia
7. ✅ Tiene logs detallados para depuración

**Para probar:**
1. Reiniciar Odoo
2. Ir a `/properties`
3. Click en "Vista Mapa"
4. Permitir acceso a ubicación
5. Ver logs en consola (F12)

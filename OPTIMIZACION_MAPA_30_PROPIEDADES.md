# Optimización del Mapa: 30 Propiedades y Filtros Mejorados

## Cambios Implementados

### 1. Límite de 30 Propiedades en el Mapa

**Archivo:** `static/src/js/property_shop.js`

**Antes:**
```javascript
limit: 200  // Muchas propiedades, carga lenta
```

**Después:**
```javascript
limit: 30  // Solo 30 propiedades más cercanas
```

**Beneficios:**
- ⚡ Carga más rápida
- 🎯 Muestra solo propiedades relevantes
- 📱 Mejor rendimiento en móvil
- 🗺️ Mapa más limpio y legible

---

### 2. Filtros de Productos No-Propiedades

**Archivo:** `controllers/main.py`

**Problema:** El endpoint devolvía comisiones, pagos y otros servicios.

**Solución:**
```python
domain = [
    ('is_property', '=', True),
    ('active', '=', True),
    ('state', '=', 'free'),
    ('latitude', '!=', False),
    ('longitude', '!=', False),
    ('latitude', '!=', 0),
    ('longitude', '!=', 0),
    # Excluir productos que no son propiedades reales
    ('name', 'not ilike', 'COMISION'),
    ('name', 'not ilike', 'PAGO'),
    ('name', 'not ilike', 'Pago'),
]
```

**Excluye:**
- ❌ "COMISION POR ARRIENDO"
- ❌ "Pago Extraordinario - Préstamo"
- ❌ "PAGO DE SERVICIOS"
- ✅ Solo propiedades reales con coordenadas

---

### 3. Centrado Mejorado en Ubicación del Usuario

**Archivo:** `static/src/js/property_shop.js`

```javascript
async loadNearbyProperties(userLat, userLng) {
    const result = await rpc('/bohio/api/properties/map', {
        ...this.filters,
        ref_lat: userLat,
        ref_lng: userLng,
        limit: 30
    });

    if (result.success) {
        const mapProperties = result.properties || [];

        // Centrar mapa en la ubicación del usuario
        if (this.map && mapProperties.length > 0) {
            // Ajustar zoom según cantidad de propiedades
            const zoom = mapProperties.length > 10 ? 12 : 13;
            this.map.setView([userLat, userLng], zoom);
            console.log(`[MAP] Mapa centrado en usuario: ${userLat}, ${userLng} (zoom: ${zoom})`);
        }

        this.updateMap(mapProperties);
    }
}
```

**Mejoras:**
- 🎯 Centra en ubicación del usuario (NO en Montería)
- 📏 Ajusta zoom dinámicamente:
  - Más de 10 propiedades: zoom 12 (más alejado)
  - Menos de 10: zoom 13 (más cercano)
- 📍 Pin azul marca ubicación del usuario

---

## Flujo Completo

### 1. Usuario abre Vista Mapa

```
[MAP] Leaflet disponible, creando mapa...
[MAP] Solicitando ubicacion del usuario...
```

### 2. Usuario PERMITE ubicación

```
[MAP] Ubicacion del usuario: 10.3795, -75.4721
[MAP] Cargando propiedades cercanas a: 10.3795, -75.4721
```

### 3. Endpoint devuelve 30 propiedades cercanas

```
[MAP] Respuesta del endpoint: {
    success: true,
    properties: Array(30),
    count: 30
}
```

### 4. Mapa se centra en usuario

```
[MAP] Mapa centrado en usuario: 10.3795, -75.4721 (zoom: 12)
[MAP] Propiedades cercanas encontradas: 30
[MAP] Actualizando mapa con 30 propiedades
```

### 5. Markers se agregan

```
[MAP] Propiedad: 732 Lat: 8.7509 Lng: -75.8786
[MAP] Propiedad: 733 Lat: 8.7509 Lng: -75.8786
...
[MAP] Markers agregados: 30 de 30
[MAP] Ajustando vista a 30 puntos
```

---

## Resultados Esperados

### Antes (126 propiedades)
- ⏱️ Carga lenta (5-10 segundos)
- 🗺️ Mapa sobrecargado con pins
- ❌ Incluía comisiones y pagos
- 📍 Centrado en Montería siempre

### Después (30 propiedades)
- ⚡ Carga rápida (1-2 segundos)
- 🎯 Mapa limpio con propiedades relevantes
- ✅ Solo propiedades reales con coordenadas
- 📍 Centrado en ubicación del usuario

---

## Logs Esperados

### Caso 1: Usuario con propiedades cercanas

```
[MAP] Ubicacion del usuario: 8.7500, -75.8800
[MAP] Cargando propiedades cercanas...
[MAP] Propiedades cercanas encontradas: 30
[MAP] Mapa centrado en usuario: 8.7500, -75.8800 (zoom: 12)
[MAP] Markers agregados: 30 de 30
```

### Caso 2: Usuario sin propiedades cercanas

```
[MAP] Ubicacion del usuario: 10.9685, -74.7813
[MAP] Cargando propiedades cercanas...
[MAP] Propiedades cercanas encontradas: 8
[MAP] Mapa centrado en usuario: 10.9685, -74.7813 (zoom: 13)
[MAP] Markers agregados: 8 de 8
```

### Caso 3: Usuario deniega ubicación

```
[MAP] No se pudo obtener ubicacion: User denied geolocation
[MAP] Cargando propiedades para mapa con filtros: {}
[MAP] Propiedades con coordenadas: 30
[MAP] Markers agregados: 30 de 30
[MAP] Mapa centrado en Colombia (vista general)
```

---

## Cálculo de Distancia

Las propiedades vienen ordenadas por distancia desde la ubicación del usuario:

```
Propiedad 1: 0.5 km
Propiedad 2: 0.8 km
Propiedad 3: 1.2 km
...
Propiedad 30: 15 km
```

Solo se muestran las **30 más cercanas**.

---

## Visualización del Mapa

### Pin Azul (Usuario)
```
      ●  ← Tu ubicación
```

### Pins Rojos (Propiedades)
```
┌──────────────┐
│ $250.000.000 │  ← Propiedad 1 (0.5 km)
└──────────────┘

┌──────────────┐
│ $180.000.000 │  ← Propiedad 2 (0.8 km)
└──────────────┘
```

### Pin Rojo Especial (Oficina BOHIO)
```
┌───────────────────┐
│ OFICINA BOHIO     │  ← Siempre visible
└───────────────────┘
```

---

## Archivos Modificados

| Archivo | Cambio | Línea |
|---------|--------|-------|
| `controllers/main.py` | Filtros para excluir comisiones/pagos | 805-817 |
| `controllers/main.py` | Default limit cambiado de 100 a 30 | 795 |
| `static/src/js/property_shop.js` | Variable mapProperties agregada | 65 |
| `static/src/js/property_shop.js` | Límite a 30 propiedades | 733 |
| `static/src/js/property_shop.js` | Guardar en this.mapProperties | 739-750 |
| `static/src/js/property_shop.js` | Límite en propiedades cercanas | 886 |
| `static/src/js/property_shop.js` | Guardar en this.mapProperties | 890-901 |
| `static/src/js/property_shop.js` | Centrar mapa en usuario | 894-898 |
| `static/src/js/property_shop.js` | Usar mapProperties en tab | 813-815 |

---

## Pruebas

### 1. Permitir ubicación
```bash
1. Ir a /properties
2. Click en "Vista Mapa"
3. Permitir acceso a ubicación
4. Ver mapa centrado en TU ubicación
5. Ver solo 30 propiedades cercanas
```

### 2. Denegar ubicación
```bash
1. Ir a /properties
2. Click en "Vista Mapa"
3. Bloquear acceso a ubicación
4. Ver mapa centrado en Colombia (vista general)
5. Ver 30 propiedades (ordenadas desde oficina BOHIO)
```

### 3. Aplicar filtros
```bash
1. Seleccionar tipo "Apartamento"
2. Click en "Vista Mapa"
3. Ver solo 30 apartamentos cercanos
4. Cambiar a tipo "Casa"
5. Ver 30 casas cercanas actualizadas
```

---

## Optimizaciones Adicionales (Opcionales)

### 1. Clustering de Markers
```javascript
// Agrupar pins cuando estén muy cerca
const markers = L.markerClusterGroup();
```

### 2. Cache de Ubicación
```javascript
// Guardar ubicación por 1 hora
sessionStorage.setItem('user_location', JSON.stringify({
    lat, lng, timestamp: Date.now()
}));
```

### 3. Radio de Búsqueda Ajustable
```html
<select id="search-radius">
    <option value="5">5 km</option>
    <option value="10" selected>10 km</option>
    <option value="20">20 km</option>
</select>
```

---

## Problema Detectado y Solucionado

### Síntoma
El mapa mostraba "Markers agregados: 2 de 40" - se cargaban 40 propiedades pero solo 2 tenían coordenadas.

### Causa Raíz
Cuando se cambiaba al tab del mapa, el evento `shown.bs.tab` llamaba a `updateMap(this.currentProperties)`, usando las propiedades del GRID en lugar de las del endpoint del mapa.

Las propiedades del grid (`this.currentProperties`):
- Son 40 propiedades por página
- Incluyen propiedades SIN coordenadas
- Vienen del endpoint `/bohio/api/properties`

Las propiedades del mapa (`this.mapProperties`):
- Son máximo 30 propiedades
- Solo incluyen propiedades CON coordenadas válidas
- Vienen del endpoint `/bohio/api/properties/map`

### Solución Implementada

1. **Creada variable separada** `this.mapProperties` (línea 65)
2. **Actualizado `loadMapProperties()`** para guardar en `this.mapProperties` (líneas 739-750)
3. **Actualizado `loadNearbyProperties()`** para guardar en `this.mapProperties` (líneas 890-901)
4. **Cambiado evento del tab** para usar `this.mapProperties` en lugar de `this.currentProperties` (líneas 813-815)
5. **Default limit del backend** cambiado de 100 a 30 (línea 795)

### Código ANTES (Incorrecto)
```javascript
mapTab.addEventListener('shown.bs.tab', () => {
    setTimeout(() => {
        this.map.invalidateSize();
        this.updateMap(this.currentProperties);  // ❌ Usa propiedades del grid
    }, 100);
});
```

### Código DESPUÉS (Correcto)
```javascript
mapTab.addEventListener('shown.bs.tab', () => {
    setTimeout(() => {
        this.map.invalidateSize();
        // Usar mapProperties que ya tiene las propiedades con coordenadas
        if (this.mapProperties && this.mapProperties.length > 0) {
            this.updateMap(this.mapProperties);  // ✅ Usa propiedades del mapa
        }
    }, 100);
});
```

---

## Resumen

✅ **Mapa limitado a 30 propiedades** para mejor rendimiento
✅ **Filtrados comisiones y pagos** del endpoint
✅ **Centrado en ubicación del usuario** automáticamente
✅ **Zoom dinámico** según cantidad de propiedades
✅ **Solo propiedades con coordenadas válidas**
✅ **Separación correcta** entre propiedades del grid y del mapa

**Resultado:** Mapa rápido, limpio y centrado en la ubicación del usuario mostrando exactamente las 30 propiedades más cercanas con coordenadas válidas.

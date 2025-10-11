# Solución Final: Mapa con Filtros y Coordenadas

## Cambios Implementados

### 1. Nuevo Endpoint para Mapa con Coordenadas

**Archivo:** `theme_bohio_real_estate/controllers/main.py`

**Endpoint:** `/bohio/api/properties/map`

**Características:**
- Devuelve SOLO propiedades con coordenadas GPS (latitude y longitude)
- Aplica los mismos filtros que la vista de grid
- Calcula distancia desde la oficina BOHIO
- Ordena por proximidad (más cercanas primero)
- Límite por defecto: 200 propiedades

**Parámetros que acepta:**
```javascript
{
    type_service: 'sale' | 'rent' | 'vacation_rent',
    property_type: 'apartment' | 'house' | 'lot' | 'commercial',
    bedrooms: 2,
    bathrooms: 2,
    min_price: 100000000,
    max_price: 500000000,
    ref_lat: 8.7479,  // Punto de referencia para distancia
    ref_lng: -75.8814,
    limit: 200
}
```

**Respuesta:**
```javascript
{
    success: true,
    properties: [
        {
            id: 123,
            name: 'Apartamento Centro',
            latitude: 8.7496,
            longitude: -75.8840,
            list_price: 250000000,
            bedrooms: 3,
            bathrooms: 2,
            area_constructed: 85,
            city: 'Montería',
            region: 'Centro',
            image_url: '/web/image/...',
            distance_km: 0.45  // Distancia desde oficina
        }
    ],
    count: 15,
    reference_point: {
        lat: 8.7479,
        lng: -75.8814,
        name: 'Oficina BOHIO'
    }
}
```

---

### 2. Método JavaScript para Cargar Propiedades del Mapa

**Archivo:** `theme_bohio_real_estate/static/src/js/property_shop.js`

**Método:** `loadMapProperties()`

```javascript
async loadMapProperties() {
    console.log('[MAP] Cargando propiedades para mapa con filtros:', this.filters);

    try {
        const result = await rpc('/bohio/api/properties/map', {
            ...this.filters,  // Aplica TODOS los filtros activos
            limit: 200
        });

        if (result.success) {
            const mapProperties = result.properties || [];
            console.log(`[MAP] Propiedades con coordenadas: ${mapProperties.length}`);
            this.updateMap(mapProperties);
        }
    } catch (error) {
        console.error('[MAP] Error cargando propiedades del mapa:', error);
        this.updateMap([]);
    }
}
```

**Se llama automáticamente:**
- Después de `loadProperties()` (carga del grid)
- Usa los MISMOS filtros aplicados en el grid
- Solo muestra propiedades con coordenadas

---

### 3. Logs de Depuración Mejorados

**Consola del navegador mostrará:**

```
[MAP] Cargando propiedades para mapa con filtros: {property_type: 'house', bedrooms: '3'}
[MAP] Respuesta del endpoint: {success: true, properties: Array(25), count: 25}
[MAP] Propiedades con coordenadas: 25
[MAP] Actualizando mapa con 25 propiedades
[MAP] Propiedad: 1 Lat: 8.7496 Lng: -75.8840
[MAP] Propiedad: 2 Lat: 8.7510 Lng: -75.8850
...
[MAP] Markers agregados: 25 de 25
[MAP] Ajustando vista a 25 puntos
```

---

## Flujo de Funcionamiento

### 1. Usuario aplica filtros
```
Usuario selecciona:
- Tipo: Casa
- Habitaciones: 3+
- Baños: 2+
```

### 2. Se ejecuta loadProperties()
```javascript
// Carga grid (40 propiedades con paginación)
await rpc('/bohio/api/properties', {
    property_type: 'house',
    bedrooms: 3,
    bathrooms: 2,
    limit: 40,
    offset: 0
});
```

### 3. Se ejecuta loadMapProperties()
```javascript
// Carga mapa (200 propiedades con coordenadas, sin paginación)
await rpc('/bohio/api/properties/map', {
    property_type: 'house',
    bedrooms: 3,
    bathrooms: 2,
    limit: 200
});
```

### 4. Resultado
- **Grid:** Muestra 40 propiedades (página 1 de N)
- **Mapa:** Muestra TODAS las propiedades con coordenadas que cumplan los filtros (hasta 200)

---

## Visualización en el Mapa

### Pin con Precio
```html
<div class="map-pin">
    <div class="pin-price">$250M</div>
    <div class="pin-arrow"></div>
</div>
```

### Popup al hacer Click
```html
<div class="property-popup-card">
    <img src="/web/image/..." alt="Propiedad">
    <h6>Apartamento Centro</h6>
    <p class="text-muted">Centro, Montería</p>
    <p class="text-danger">$250.000.000</p>
    <div>
        <span>85 m²</span>
        <span>3 hab</span>
        <span>2 baños</span>
    </div>
    <a href="/property/123" class="btn btn-danger">Ver Detalles</a>
</div>
```

---

## Ejemplos de Uso

### Ejemplo 1: Filtrar por Tipo "Casa"
```javascript
// Usuario selecciona tipo "Casa"
this.filters.property_type = 'house';
await this.loadProperties();

// Resultado:
// Grid: 40 casas
// Mapa: 120 casas con coordenadas (ordenadas por distancia)
```

### Ejemplo 2: Filtrar por Tipo "Apartamento" + 3 Habitaciones
```javascript
this.filters.property_type = 'apartment';
this.filters.bedrooms = 3;
await this.loadProperties();

// Resultado:
// Grid: 40 apartamentos con 3+ habitaciones
// Mapa: 85 apartamentos con 3+ habitaciones y coordenadas
```

### Ejemplo 3: Sin Filtros
```javascript
this.filters = {};
await this.loadProperties();

// Resultado:
// Grid: 40 propiedades (todas)
// Mapa: 200 propiedades con coordenadas (las más cercanas)
```

---

## Cálculo de Distancia

**Fórmula Haversine:**
```python
import math

def calculate_distance(lat1, lon1, lat2, lon2):
    # Convertir a radianes
    lat1, lon1 = math.radians(lat1), math.radians(lon1)
    lat2, lon2 = math.radians(lat2), math.radians(lon2)

    # Diferencias
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Fórmula Haversine
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    # Distancia en km (radio de la Tierra = 6371 km)
    distance_km = 6371 * c

    return round(distance_km, 2)
```

**Punto de referencia:**
- Oficina BOHIO en Montería
- Latitud: 8.7479
- Longitud: -75.8814

---

## Verificación

### 1. Abrir consola (F12)

### 2. Aplicar un filtro
```
Seleccionar tipo: Casa
```

### 3. Revisar logs
```
[FILTER] Filtro property_type aplicado: house
Cargando propiedades con filtros: {property_type: 'house'}
[MAP] Cargando propiedades para mapa con filtros: {property_type: 'house'}
[MAP] Respuesta del endpoint: {success: true, properties: Array(45)}
[MAP] Propiedades con coordenadas: 45
[MAP] Actualizando mapa con 45 propiedades
```

### 4. Cambiar a Vista Mapa
- Ver pins con precios
- Hacer click en un pin
- Ver popup con imagen y detalles

---

## Filtros Soportados

| Filtro | Campo | Ejemplo |
|--------|-------|---------|
| Tipo de Servicio | type_service | 'sale', 'rent', 'vacation_rent' |
| Tipo de Propiedad | property_type | 'apartment', 'house', 'lot', 'commercial' |
| Habitaciones | bedrooms | 3 (muestra 3+) |
| Baños | bathrooms | 2 (muestra 2+) |
| Precio Mínimo | min_price | 100000000 |
| Precio Máximo | max_price | 500000000 |
| Garaje | garage | true |
| Piscina | pool | true |
| Jardín | garden | true |
| Ascensor | elevator | true |

---

## Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `controllers/main.py` | Nuevo endpoint `/bohio/api/properties/map` |
| `static/src/js/property_shop.js` | Método `loadMapProperties()` + logs |

---

## Próximos Pasos

### 1. Agregar coordenadas a propiedades

**Opción A: Manual**
```sql
-- En PostgreSQL
UPDATE product_template
SET latitude = 8.7479, longitude = -75.8814
WHERE is_property = TRUE
  AND (latitude IS NULL OR longitude IS NULL);
```

**Opción B: Script Python**
```python
# En Odoo shell
properties = env['product.template'].search([
    ('is_property', '=', True),
    '|',
    ('latitude', '=', False),
    ('longitude', '=', False)
])

for prop in properties:
    prop.write({
        'latitude': 8.7479,  # Montería centro
        'longitude': -75.8814
    })

print(f"Actualizadas {len(properties)} propiedades")
```

### 2. Implementar Filtros Dinámicos

- Los filtros deben cambiar según tipo de propiedad
- Casa/Apartamento: habitaciones, baños
- Lote: solo área total (en hectáreas)
- Comercial: área, parqueaderos

---

## Resultado Final

Ahora cuando aplicas un filtro:

1. El GRID muestra propiedades paginadas (40 por página)
2. El MAPA muestra TODAS las propiedades que cumplen el filtro Y tienen coordenadas
3. El mapa se actualiza automáticamente al cambiar filtros
4. Los pins muestran el precio
5. Al hacer click, se ve imagen y detalles
6. Las propiedades están ordenadas por proximidad a la oficina

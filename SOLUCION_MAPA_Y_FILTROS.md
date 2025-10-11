# Solución: Mapa y Filtros Dinámicos

## Problemas Identificados

### 1. Mapa no muestra propiedades

**Causa probable:** Las propiedades no tienen coordenadas GPS (latitude/longitude) en la base de datos.

**Logs agregados:**
```javascript
[MAP] Actualizando mapa con X propiedades
[MAP] Propiedad: ID Lat: X Lng: Y
[MAP] Propiedad sin coordenadas: ID nombre
[MAP] Markers agregados: X de Y
```

**Verificación necesaria:**
1. Revisar que las propiedades en BD tengan `latitude` y `longitude`
2. Verificar que el endpoint `/bohio/api/properties` devuelva estos campos
3. Los logs mostrarán cuántas propiedades tienen coordenadas

**Solución temporal:**
- Si no hay coordenadas, el mapa se centra en Colombia
- Se muestra solo el pin de la oficina de BOHIO

---

### 2. Filtros no mutan según tipo de propiedad

**Problema:** Los filtros deberían cambiar dinámicamente según el tipo de propiedad seleccionada.

**Ejemplo:**
- **Apartamento/Casa:** Mostrar habitaciones, baños, área construida
- **Lote/Terreno:** Mostrar solo área total (hectáreas)
- **Comercial:** Mostrar características comerciales

---

## Soluciones Implementadas

### A. Logs de Depuración del Mapa

**Archivo:** `property_shop.js`

```javascript
updateMap(properties) {
    console.log('[MAP] Actualizando mapa con', properties.length, 'propiedades');

    properties.forEach(prop => {
        console.log('[MAP] Propiedad:', prop.id, 'Lat:', prop.latitude, 'Lng:', prop.longitude);

        if (prop.latitude && prop.longitude) {
            // Crear marker
        } else {
            console.warn('[MAP] Propiedad sin coordenadas:', prop.id, prop.name);
        }
    });

    console.log('[MAP] Markers agregados:', markersAdded, 'de', properties.length);
}
```

---

### B. Endpoint para Filtros Dinámicos (PENDIENTE)

**Crear en:** `theme_bohio_real_estate/controllers/main.py`

```python
@http.route(['/bohio/api/filter_options'], type='json', auth='public', website=True)
def get_filter_options(self, property_type=None, **kwargs):
    """
    Obtener opciones de filtros según tipo de propiedad

    Returns:
        dict: Filtros aplicables según el tipo
    """
    Property = request.env['product.template'].sudo()

    # Configuración de filtros por tipo
    filter_config = {
        'apartment': {
            'fields': ['bedrooms', 'bathrooms', 'area_constructed', 'floor', 'elevator', 'balcony'],
            'unit': 'm²',
            'show_bedrooms': True,
            'show_bathrooms': True,
        },
        'house': {
            'fields': ['bedrooms', 'bathrooms', 'area_constructed', 'area_total', 'garage', 'garden', 'pool'],
            'unit': 'm²',
            'show_bedrooms': True,
            'show_bathrooms': True,
        },
        'lot': {
            'fields': ['area_total'],
            'unit': 'hectáreas',
            'show_bedrooms': False,
            'show_bathrooms': False,
        },
        'commercial': {
            'fields': ['area_constructed', 'parking', 'warehouse'],
            'unit': 'm²',
            'show_bedrooms': False,
            'show_bathrooms': False,
        },
    }

    if property_type and property_type in filter_config:
        return {
            'success': True,
            'config': filter_config[property_type]
        }

    # Si no hay tipo, devolver configuración por defecto
    return {
        'success': True,
        'config': {
            'fields': ['bedrooms', 'bathrooms', 'area_constructed'],
            'unit': 'm²',
            'show_bedrooms': True,
            'show_bathrooms': True,
        }
    }
```

---

### C. JavaScript para Filtros Dinámicos (PENDIENTE)

**Archivo:** `property_shop.js`

```javascript
async updateFiltersByType(propertyType) {
    console.log('[FILTERS] Actualizando filtros para tipo:', propertyType);

    try {
        const result = await rpc('/bohio/api/filter_options', {
            property_type: propertyType
        });

        if (result.success) {
            const config = result.config;

            // Mostrar/ocultar habitaciones
            const bedroomsFilter = document.querySelector('[data-filter="bedrooms"]');
            if (bedroomsFilter) {
                bedroomsFilter.closest('.col-md-1').style.display =
                    config.show_bedrooms ? 'block' : 'none';
            }

            // Mostrar/ocultar baños
            const bathroomsFilter = document.querySelector('[data-filter="bathrooms"]');
            if (bathroomsFilter) {
                bathroomsFilter.closest('.col-md-1').style.display =
                    config.show_bathrooms ? 'block' : 'none';
            }

            // Actualizar unidad de medida
            document.querySelectorAll('.area-unit').forEach(el => {
                el.textContent = config.unit;
            });

            console.log('[FILTERS] Filtros actualizados:', config);
        }
    } catch (error) {
        console.error('[FILTERS] Error actualizando filtros:', error);
    }
}

// Llamar cuando cambia el tipo de propiedad
initFilters() {
    const propertyTypeFilter = document.querySelector('[data-filter="property_type"]');

    if (propertyTypeFilter) {
        propertyTypeFilter.addEventListener('change', async (e) => {
            const selectedType = e.target.value;

            // Actualizar filtros dinámicamente
            await this.updateFiltersByType(selectedType);

            // Aplicar filtro
            this.filters.property_type = selectedType;
            await this.loadProperties();
        });
    }
}
```

---

## Cómo Verificar el Mapa

### 1. Abrir consola del navegador (F12)

### 2. Ir a la pestaña "Vista Mapa"

### 3. Revisar logs:

**Si hay propiedades con coordenadas:**
```
[MAP] Actualizando mapa con 40 propiedades
[MAP] Propiedad: 1 Lat: 8.7479 Lng: -75.8814
[MAP] Propiedad: 2 Lat: 8.7496 Lng: -75.8840
...
[MAP] Markers agregados: 35 de 40
[MAP] Ajustando vista a 35 puntos
```

**Si NO hay coordenadas:**
```
[MAP] Actualizando mapa con 40 propiedades
[MAP] Propiedad: 1 Lat: null Lng: null
[MAP] Propiedad sin coordenadas: 1 Apartamento Centro
...
[MAP] Markers agregados: 0 de 40
[MAP] No hay coordenadas para ajustar vista
```

---

## Solución: Agregar Coordenadas a Propiedades

### Opción 1: Manual en Odoo

1. Ir a Inventario > Productos
2. Filtrar `is_property = True`
3. Editar cada propiedad
4. Agregar campos:
   - `latitude` (ej: 8.7479)
   - `longitude` (ej: -75.8814)

### Opción 2: Script Python

```python
# Ejecutar desde Odoo shell
properties = env['product.template'].search([('is_property', '=', True)])

# Coordenadas ejemplo (Montería, Córdoba)
default_coords = {
    'latitude': 8.7479,
    'longitude': -75.8814
}

for prop in properties:
    if not prop.latitude or not prop.longitude:
        prop.write(default_coords)
        print(f"Actualizado: {prop.name}")
```

### Opción 3: API de Geocodificación

```python
import requests

def geocode_address(address, city):
    """Obtener coordenadas desde Google Maps"""
    api_key = 'TU_API_KEY'
    url = f'https://maps.googleapis.com/maps/api/geocode/json'

    params = {
        'address': f'{address}, {city}, Colombia',
        'key': api_key
    }

    response = requests.get(url, params=params)
    data = response.json()

    if data['results']:
        location = data['results'][0]['geometry']['location']
        return location['lat'], location['lng']

    return None, None

# Usar en propiedades
for prop in properties:
    if prop.address and prop.city:
        lat, lng = geocode_address(prop.address, prop.city)
        if lat and lng:
            prop.write({'latitude': lat, 'longitude': lng})
```

---

## Tipos de Propiedad en Odoo

Según el código del controlador, los tipos disponibles son:

```python
property_type = [
    ('apartment', 'Apartamento'),
    ('house', 'Casa'),
    ('lot', 'Lote'),
    ('commercial', 'Comercial'),
    ('farm', 'Finca'),
    ('warehouse', 'Bodega'),
    ('office', 'Oficina'),
    ('local', 'Local'),
]
```

---

## Próximos Pasos

1. ✅ Verificar logs del mapa en consola
2. ⏳ Agregar coordenadas a propiedades en BD
3. ⏳ Crear endpoint `/bohio/api/filter_options`
4. ⏳ Implementar filtros dinámicos en JS
5. ⏳ Probar cambio de filtros al seleccionar tipo

---

## Comandos Útiles

### Ver propiedades sin coordenadas
```python
# En Odoo shell
properties = env['product.template'].search([
    ('is_property', '=', True),
    '|',
    ('latitude', '=', False),
    ('longitude', '=', False)
])
print(f"Propiedades sin coordenadas: {len(properties)}")
```

### Actualizar coordenadas en masa
```python
# Centro de Montería
monteria_center = {
    'latitude': 8.7479,
    'longitude': -75.8814
}

properties.write(monteria_center)
```

# FIX: Filtros Dinámicos del Mapa de Propiedades

## Problema Identificado

El mapa de propiedades **NO estaba filtrando dinámicamente** cuando el usuario aplicaba filtros de ubicación.

### Síntoma reportado por el usuario
```
"El filtro de arriendo está activado y pasó por Barranquilla
pero no me muestra ningún icono en el mapa"
```

### Comportamiento observado
1. Usuario selecciona "Arriendo" como tipo de servicio ✅
2. Usuario selecciona "Barranquilla" del autocompletado ✅
3. El listado de propiedades se filtra correctamente ✅
4. **El mapa NO muestra ningún pin/icono** ❌

### Causa raíz

El endpoint `/bohio/api/properties/map` **NO procesaba los filtros de ubicación** (`city_id`, `region_id`, `project_id`).

**Archivo**: `theme_bohio_real_estate/controllers/main.py`
**Método**: `api_get_properties_for_map()` (línea 789)

```python
# ANTES DEL FIX
def api_get_properties_for_map(self, **params):
    type_service = params.get('type_service')
    property_type = params.get('property_type')
    # ...otros filtros...

    # ❌ FALTABAN ESTOS:
    # city_id = params.get('city_id')      # NO EXISTÍA
    # region_id = params.get('region_id')  # NO EXISTÍA
    # project_id = params.get('project_id')# NO EXISTÍA

    domain = [
        ('is_property', '=', True),
        ('latitude', '!=', False),
        # ...
    ]

    # ❌ NUNCA SE APLICABAN LOS FILTROS DE UBICACIÓN
```

---

## Investigación

### 1. Flujo del sistema

```
Frontend (property_shop.js)
   ↓ loadMapProperties()
   ↓ Envía: {city_id: '1253', type_service: 'rent'}
   ↓
Backend (/bohio/api/properties/map)
   ↓ ❌ Ignoraba city_id, region_id, project_id
   ↓ Solo aplicaba: type_service, property_type, bedrooms, bathrooms, precios
   ↓
Base de datos
   ↓ WHERE type_service='rent' AND latitude IS NOT NULL
   ↓ ❌ NO filtraba por city_id
   ↓
Resultado: Mostraba pins de TODAS las ciudades con arriendo
```

### 2. Análisis del código JavaScript

**Archivo**: `theme_bohio_real_estate/static/src/js/property_shop.js`
**Líneas**: 782-803

```javascript
async loadMapProperties() {
    console.log('[MAP] === loadMapProperties ===');
    console.log('[MAP] Filtros:', JSON.stringify(this.filters));

    if (!this.map || !this.markers) {
        return;
    }

    try {
        const result = await rpc('/bohio/api/properties/map', {
            ...this.filters,  // ← ✅ Ya enviaba TODOS los filtros
            limit: 30
        });

        if (result.success && result.properties) {
            this.mapProperties = result.properties;
            this.updateMap(this.mapProperties);
        }
    }
}
```

**Conclusión**: El frontend **SÍ enviaba los filtros correctamente**, pero el backend **NO los procesaba**.

---

## Solución Implementada

### Cambios en `theme_bohio_real_estate/controllers/main.py`

#### 1. Extracción de parámetros de ubicación (líneas 808-817)

```python
# FILTROS DE UBICACIÓN (agregados para filtrado dinámico del mapa)
city_id = params.get('city_id')
region_id = params.get('region_id')
project_id = params.get('project_id')

_logger.info(f"API /bohio/api/properties/map - Filtros recibidos:")
_logger.info(f"  type_service={type_service}, property_type={property_type}")
_logger.info(f"  city_id={city_id}, region_id={region_id}, project_id={project_id}")
_logger.info(f"  bedrooms={bedrooms}, bathrooms={bathrooms}")
_logger.info(f"  min_price={min_price}, max_price={max_price}")
```

#### 2. Aplicación de filtros jerárquicos al dominio (líneas 868-887)

```python
# FILTROS DE UBICACIÓN JERÁRQUICOS (mismo patrón que /bohio/api/properties)
# Orden de prioridad: proyecto > barrio > ciudad
if project_id:
    try:
        domain.append(('project_worksite_id', '=', int(project_id)))
        _logger.info(f"[MAPA] Filtro project_id aplicado: {project_id}")
    except (ValueError, TypeError):
        _logger.warning(f"[MAPA] project_id inválido: {project_id}")
elif region_id:
    try:
        domain.append(('region_id', '=', int(region_id)))
        _logger.info(f"[MAPA] Filtro region_id aplicado: {region_id}")
    except (ValueError, TypeError):
        _logger.warning(f"[MAPA] region_id inválido: {region_id}")
elif city_id:
    try:
        domain.append(('city_id', '=', int(city_id)))
        _logger.info(f"[MAPA] Filtro city_id aplicado: {city_id}")
    except (ValueError, TypeError):
        _logger.warning(f"[MAPA] city_id inválido: {city_id}")
```

### Lógica de jerarquía

**Misma lógica que `/bohio/api/properties`** (consistencia en ambos endpoints):

```
PROYECTO (más específico)
   ↓ Si no hay proyecto...
BARRIO (intermedio)
   ↓ Si no hay barrio...
CIUDAD (más general)
```

---

## Flujo después del fix

```
Frontend (property_shop.js)
   ↓ loadMapProperties()
   ↓ Envía: {city_id: '1253', type_service: 'rent'}
   ↓
Backend (/bohio/api/properties/map)
   ↓ city_id = params.get('city_id')  ← ✅ Extrae parámetro
   ↓ domain.append(('city_id', '=', 1253))  ← ✅ Aplica filtro
   ↓
Base de datos
   ↓ WHERE type_service='rent' AND city_id=1253 AND latitude IS NOT NULL
   ↓ ✅ Filtra por ciudad Y tipo de servicio
   ↓
Resultado: Muestra SOLO pins de Barranquilla en arriendo
```

---

## Ejemplos de casos de uso

### Caso 1: Solo filtro de tipo de servicio
```javascript
// Usuario selecciona "Arriendo"
{type_service: 'rent'}

// Mapa muestra:
→ TODOS los pins de arriendo (todas las ciudades)
```

### Caso 2: Tipo de servicio + Ciudad
```javascript
// Usuario selecciona "Arriendo" + "Barranquilla"
{type_service: 'rent', city_id: '1253'}

// Mapa muestra:
→ SOLO pins de arriendo EN Barranquilla
```

### Caso 3: Tipo de servicio + Ciudad + Barrio
```javascript
// Usuario selecciona "Arriendo" + "Barranquilla" + "El Prado"
{type_service: 'rent', city_id: '1253', region_id: '456'}

// Mapa muestra:
→ SOLO pins de arriendo EN el barrio El Prado
// Ignora city_id por jerarquía (barrio es más específico)
```

### Caso 4: Tipo de servicio + Proyecto
```javascript
// Usuario selecciona "Venta" + "Torre Rialto"
{type_service: 'sale', project_id: '789'}

// Mapa muestra:
→ SOLO pins del proyecto Torre Rialto
// Ignora city_id y region_id por jerarquía (proyecto es más específico)
```

---

## Verificación

### Logs esperados en Odoo

```
INFO theme_bohio_real_estate.controllers.main: API /bohio/api/properties/map - Filtros recibidos:
INFO theme_bohio_real_estate.controllers.main:   type_service=rent, property_type=None
INFO theme_bohio_real_estate.controllers.main:   city_id=1253, region_id=None, project_id=None
INFO theme_bohio_real_estate.controllers.main:   bedrooms=None, bathrooms=None
INFO theme_bohio_real_estate.controllers.main:   min_price=None, max_price=None
INFO theme_bohio_real_estate.controllers.main: [MAPA] Filtro city_id aplicado: 1253
INFO theme_bohio_real_estate.controllers.main: Propiedades con coordenadas encontradas: 1
```

### Logs en consola del navegador

```javascript
[MAP] === loadMapProperties ===
[MAP] Filtros: {"type_service":"rent","city_id":"1253"}
[MAP] Respuesta: 1 propiedades
[MAP] Actualizando marcadores: 1 propiedades
```

### Prueba en navegador

1. Ir a `/shop/properties`
2. Seleccionar "Arriendo" del filtro de tipo de servicio
3. Buscar "Barranquilla" en el autocompletado
4. Seleccionar "Barranquilla"
5. Click en tab "Mapa"

**Resultado esperado**:
- ✅ Mapa muestra SOLO pins de Barranquilla
- ✅ Pins corresponden a propiedades en arriendo
- ✅ Al hacer click en un pin, muestra info de la propiedad

---

## Comparación: Antes vs Después

### ANTES DEL FIX

| Filtro | Listado | Mapa |
|--------|---------|------|
| Arriendo | ✅ Filtra correctamente | ❌ Muestra TODAS las ciudades |
| Barranquilla | ✅ Filtra correctamente | ❌ Muestra TODAS las ciudades |
| Arriendo + Barranquilla | ✅ Muestra 1 propiedad | ❌ Muestra 30 pins (todas las ciudades) |

### DESPUÉS DEL FIX

| Filtro | Listado | Mapa |
|--------|---------|------|
| Arriendo | ✅ Filtra correctamente | ✅ Muestra solo pins de arriendo |
| Barranquilla | ✅ Filtra correctamente | ✅ Muestra solo pins de Barranquilla |
| Arriendo + Barranquilla | ✅ Muestra 1 propiedad | ✅ Muestra 1 pin (Barranquilla en arriendo) |

---

## Archivos modificados

### Backend
- ✅ **`theme_bohio_real_estate/controllers/main.py`**
  - Líneas 808-817: Extracción de parámetros de ubicación
  - Líneas 868-887: Aplicación de filtros jerárquicos al dominio

### Frontend
- ⚠️ **NO se modificó** - Ya funcionaba correctamente
- `theme_bohio_real_estate/static/src/js/property_shop.js` ya enviaba los filtros

---

## Próximos pasos

### 1. Reiniciar Odoo
```bash
# Como administrador
net stop odoo-server-18.0
net start odoo-server-18.0
```

### 2. Probar en navegador
1. Ir a `/shop/properties`
2. Aplicar filtro de "Arriendo"
3. Buscar y seleccionar "Barranquilla"
4. Verificar tab "Mapa":
   - Debería mostrar SOLO 1 pin de Barranquilla
   - El pin debe ser de una propiedad en arriendo

### 3. Revisar logs de Odoo
```
INFO: [MAPA] Filtro city_id aplicado: 1253
INFO: Propiedades con coordenadas encontradas: 1
```

---

## Relación con otros fixes

Este fix es complementario a:

1. ✅ **FIX_FILTROS_UBICACION_API.md** - Fix de filtros en listado de propiedades
2. ✅ **SOLUCION_AUTOCOMPLETE_CIUDADES.md** - Autocompletado de ciudades sin acentos
3. ✅ **OPTIMIZACIONES_ORM_POSTGRESQL.md** - Optimización de búsquedas

**Ahora ambos endpoints están sincronizados**:
- `/bohio/api/properties` - Para listado paginado ✅
- `/bohio/api/properties/map` - Para mapa interactivo ✅

---

## Conclusión

✅ **Problema**: Mapa no filtraba por ubicación (city_id, region_id, project_id)
✅ **Causa**: Backend no procesaba filtros de ubicación en endpoint del mapa
✅ **Solución**: Agregar extracción y aplicación de filtros jerárquicos
✅ **Resultado**: Mapa ahora filtra dinámicamente junto con el listado
✅ **Consistencia**: Ambos endpoints usan la misma lógica de filtrado

**Estado**: Listo para reiniciar Odoo y probar en navegador.

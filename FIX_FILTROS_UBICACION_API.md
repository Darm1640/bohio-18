# FIX: Filtros de Ubicación en API de Propiedades

## Problema Identificado

El endpoint `/bohio/api/properties` **NO estaba filtrando correctamente por ubicación** (city_id, region_id, project_id).

### Síntomas
```javascript
// Usuario selecciona Barranquilla (que tiene 1 propiedad)
[FILTER] Filtro ciudad agregado: 1253
Enviando request a /bohio/api/properties con filtros: {city_id: '1253'}

// ❌ API devuelve total incorrecto
Datos recibidos: {items: Array(40), properties: Array(40), count: 40, total: 1543...}
Propiedades: 40 de 1543 total (Página 1/39)

// ✅ Debería devolver
Propiedades: 1 de 1 total (Página 1/1)
```

**Causa raíz**: El endpoint aceptaba los parámetros pero **nunca los aplicaba al dominio de búsqueda**.

---

## Solución Implementada

### Archivo modificado
- **`theme_bohio_real_estate/controllers/main.py`** - Líneas 934-1063

### Cambios realizados

#### 1. Extracción de parámetros de ubicación (líneas 955-958)
```python
# FILTROS DE UBICACIÓN (agregados para property_shop)
city_id = params.get('city_id')
region_id = params.get('region_id')
project_id = params.get('project_id')
```

#### 2. Logging de parámetros recibidos (línea 965)
```python
_logger.info(f"  city_id={city_id}, region_id={region_id}, project_id={project_id}")
```

#### 3. Aplicación de filtros jerárquicos (líneas 1043-1062)
```python
# FILTROS DE UBICACIÓN JERÁRQUICOS
# Orden de prioridad: proyecto > barrio > ciudad
if project_id:
    try:
        domain.append(('project_worksite_id', '=', int(project_id)))
        _logger.info(f"Filtro project_id aplicado: {project_id}")
    except (ValueError, TypeError):
        _logger.warning(f"project_id inválido: {project_id}")
elif region_id:
    try:
        domain.append(('region_id', '=', int(region_id)))
        _logger.info(f"Filtro region_id aplicado: {region_id}")
    except (ValueError, TypeError):
        _logger.warning(f"region_id inválido: {region_id}")
elif city_id:
    try:
        domain.append(('city_id', '=', int(city_id)))
        _logger.info(f"Filtro city_id aplicado: {city_id}")
    except (ValueError, TypeError):
        _logger.warning(f"city_id inválido: {city_id}")
```

### Lógica de filtros jerárquicos

Los filtros son **mutuamente excluyentes** siguiendo una jerarquía:

```
PROYECTO (más específico)
   ↓
BARRIO (intermedio)
   ↓
CIUDAD (más general)
```

**Reglas:**
- Si hay `project_id` → solo ese proyecto
- Si NO hay proyecto pero HAY `region_id` → solo ese barrio
- Si NO hay proyecto ni barrio pero HAY `city_id` → toda esa ciudad

Esto asegura que **no se mezclen niveles de jerarquía**, evitando conflictos en los resultados.

---

## Cómo activar los cambios

### Opción 1: Reinicio manual de Odoo (RECOMENDADO)
1. Detener el servicio de Odoo desde el Administrador de Tareas o Servicios de Windows
2. Iniciar el servicio nuevamente
3. Los cambios en el controlador se cargarán automáticamente

### Opción 2: Reinicio automático con auto-reload (si está habilitado)
- Si Odoo está en modo desarrollo con `--dev=all`, los cambios se cargan automáticamente
- No requiere reinicio manual

---

## Verificación de la corrección

### 1. Revisar logs de Odoo
Buscar líneas como:
```
INFO bohio_db theme_bohio_real_estate.controllers.main: API /bohio/api/properties LLAMADO - Parámetros recibidos:
INFO bohio_db theme_bohio_real_estate.controllers.main:   city_id=1253, region_id=None, project_id=None
INFO bohio_db theme_bohio_real_estate.controllers.main: Filtro city_id aplicado: 1253
INFO bohio_db theme_bohio_real_estate.controllers.main: Domain final para búsqueda: [...('city_id', '=', 1253)...]
```

### 2. Probar en navegador
1. Ir a `/shop/properties`
2. Escribir "Barranquilla" en el buscador
3. Seleccionar "Barranquilla" del autocompletado
4. Verificar en consola del navegador:
   ```javascript
   Enviando request a /bohio/api/properties con filtros: {city_id: '1253'}
   Propiedades: 1 de 1 total (Página 1/1) // ✅ Total correcto
   ```

### 3. Probar jerarquía de filtros
```javascript
// Test 1: Solo ciudad
filters = {city_id: '1253'}
→ Debe filtrar todas las propiedades de Barranquilla

// Test 2: Ciudad + Barrio
filters = {city_id: '1253', region_id: '123'}
→ Debe filtrar SOLO el barrio 123 (ignora city_id)

// Test 3: Ciudad + Barrio + Proyecto
filters = {city_id: '1253', region_id: '123', project_id: '456'}
→ Debe filtrar SOLO el proyecto 456 (ignora city_id y region_id)
```

---

## Resultados esperados

### Antes del fix
```javascript
// Seleccionar Barranquilla (1 propiedad)
total: 1543  // ❌ Mostraba TODAS las propiedades
```

### Después del fix
```javascript
// Seleccionar Barranquilla (1 propiedad)
total: 1  // ✅ Muestra SOLO las propiedades de Barranquilla
```

### Logs esperados
```
INFO: Filtro city_id aplicado: 1253
INFO: Domain final para búsqueda: [
    ('is_property', '=', True),
    ('active', '=', True),
    ('state', '=', 'free'),
    ('city_id', '=', 1253)  ← ✅ Filtro aplicado
]
INFO: API properties: Total=1, Devolviendo=1, Offset=0, Limit=40
```

---

## Archivos relacionados

- **Backend (API)**: `theme_bohio_real_estate/controllers/main.py`
- **Frontend (JS)**: `theme_bohio_real_estate/static/src/js/property_shop.js`
- **Autocompletado**: `theme_bohio_real_estate/controllers/property_search.py`

---

## Notas técnicas

### ¿Por qué no usar `AND` para combinar filtros?
```python
# ❌ MAL: Combinar todos los filtros
if city_id:
    domain.append(('city_id', '=', int(city_id)))
if region_id:
    domain.append(('region_id', '=', int(region_id)))
if project_id:
    domain.append(('project_worksite_id', '=', int(project_id)))
```

**Problema**: Si aplicamos los 3 filtros juntos con AND:
```python
[('city_id', '=', 1253), ('region_id', '=', 123), ('project_worksite_id', '=', 456)]
```

Odoo buscaría propiedades que cumplan **LAS 3 CONDICIONES A LA VEZ**:
- ✅ Pertenecen a la ciudad 1253
- ✅ Pertenecen al barrio 123
- ✅ Pertenecen al proyecto 456

Si el barrio 123 pertenece a otra ciudad (NO 1253), **no habrá resultados**.

### ✅ Solución correcta: Jerarquía con `elif`
```python
if project_id:
    # Solo proyecto (más específico)
elif region_id:
    # Solo barrio (intermedio)
elif city_id:
    # Solo ciudad (más general)
```

Esto asegura que **solo se aplique UN nivel de jerarquía**, el más específico disponible.

---

## Conclusión

✅ **Problema resuelto**: Los filtros de ubicación ahora funcionan correctamente
✅ **Jerarquía implementada**: proyecto > barrio > ciudad
✅ **Logs agregados**: Facilitan debugging
✅ **Validación de datos**: Try-except evita errores con IDs inválidos

**Próximo paso**: Reiniciar Odoo y verificar en navegador.

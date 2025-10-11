# MAPEO DE CAMPOS: ODOO 17 (CloudPepper) → ODOO 18 (Odoo.com)

**Fecha:** 2025-10-11

---

## RESUMEN EJECUTIVO

| Aspecto | CloudPepper (Odoo 17) | Odoo.com (Odoo 18) |
|---------|----------------------|---------------------|
| **Departamento** | `state_id` → `res.country.state` | `property_state_id` → `res.country.state` |
| **Ciudad** | `city_id` → `res.city` | `property_city_id` → `res.city` |
| **Región/Barrio** | `region_id` → `region.region` | `property_region_id` → `property.region` |
| **Barrio** | NO EXISTE | `property_neighborhood_id` → `property.neighborhood` |

---

## MAPEO DETALLADO DE CAMPOS

### 1. UBICACIÓN

#### Departamento/Estado
```python
# ORIGEN (CloudPepper - Odoo 17)
state_id = Many2one('res.country.state')

# DESTINO (Odoo.com - Odoo 18)
property_state_id = Many2one('res.country.state')
```

**Mapeo:**
- `state_id` → `property_state_id`
- ✅ Mismo modelo: `res.country.state`
- ✅ Solo cambió el nombre del campo

---

#### Ciudad
```python
# ORIGEN (CloudPepper - Odoo 17)
city_id = Many2one('res.city')

# DESTINO (Odoo.com - Odoo 18)
property_city_id = Many2one('res.city')
```

**Mapeo:**
- `city_id` → `property_city_id`
- ✅ Mismo modelo: `res.city`
- ✅ Solo cambió el nombre del campo

---

#### Región/Barrio (CAMBIO IMPORTANTE)
```python
# ORIGEN (CloudPepper - Odoo 17)
region_id = Many2one('region.region')
# Etiqueta: "Barrio"
# Modelo: region.region

# DESTINO (Odoo.com - Odoo 18)
property_region_id = Many2one('property.region')
# Etiqueta: "Región"
# Modelo: property.region

property_neighborhood_id = Many2one('property.neighborhood')
# Etiqueta: "Barrio"
# Modelo: property.neighborhood
```

**Mapeo:**
- `region_id` → `property_region_id` (si se interpreta como región)
- `region_id` → `property_neighborhood_id` (si se interpreta como barrio)

⚠️ **PROBLEMA:** En CloudPepper, `region_id` se etiqueta como "Barrio" pero apunta a `region.region`. En Odoo 18, hay dos campos separados: región Y barrio.

**SOLUCIÓN:**
1. Leer el valor de `region_id` en CloudPepper
2. Buscar o crear el registro en `property.region` o `property.neighborhood` en Odoo 18
3. Asignar al campo correspondiente según la lógica de negocio

---

#### Coordenadas GPS y Dirección
```python
# COMUNES EN AMBAS VERSIONES
latitude = Float
longitude = Float
street = Char
street2 = Char
zip = Char
```

**Mapeo:**
- ✅ Mismos nombres en ambas versiones
- ✅ Sin cambios necesarios

---

### 2. CARACTERÍSTICAS

#### Habitaciones, Baños, Garajes
```python
# ORIGEN (CloudPepper - Odoo 17)
num_bedrooms = Integer  # N° De Habitaciones
num_bathrooms = Integer  # N° De Baños
n_garage = Integer  # N° Garaje

# DESTINO (Odoo.com - Odoo 18)
property_bedrooms = Integer
property_bathrooms = Integer
property_garages = Integer
```

**Mapeo:**
- `num_bedrooms` → `property_bedrooms`
- `num_bathrooms` → `property_bathrooms`
- `n_garage` → `property_garages`

---

#### Área
```python
# ORIGEN (CloudPepper - Odoo 17)
property_area = Float  # Área de la Propiedad
area_in_m2 = Float  # Área en M² (Interno)

# DESTINO (Odoo.com - Odoo 18)
property_area_built = Float
property_area_total = Float
```

**Mapeo:**
- `property_area` → `property_area_total`
- `area_in_m2` → `property_area_built`

---

#### Piso y Unidad
```python
# ORIGEN (CloudPepper - Odoo 17)
floor_number = Integer  # N° De Piso

# DESTINO (Odoo.com - Odoo 18)
property_floor_number = Integer
property_unit_number = Integer
```

**Mapeo:**
- `floor_number` → `property_floor_number`
- NO HAY EQUIVALENTE para `property_unit_number` en origen

---

### 3. PRECIOS

#### Precio de Venta
```python
# ORIGEN (CloudPepper - Odoo 17)
list_price = Float  # Sales Price

# DESTINO (Odoo.com - Odoo 18)
list_price = Float  # Sales Price
```

**Mapeo:**
- ✅ Mismo campo: `list_price`

---

#### Precio de Arriendo
```python
# ORIGEN (CloudPepper - Odoo 17)
rental_fee = Float  # Tarifa de alquiler

# DESTINO (Odoo.com - Odoo 18)
property_price_rent = Float
```

**Mapeo:**
- `rental_fee` → `property_price_rent`

---

### 4. TIPO Y ESTADO

#### Tipo de Propiedad
```python
# ORIGEN (CloudPepper - Odoo 17)
property_type = Selection  # Tipo de Inmueble (selection)
property_type_id = Many2one('property.type')  # Tipo de Propiedad

# DESTINO (Odoo.com - Odoo 18)
property_type_id = Many2one('property.type')
property_subtype_id = Many2one('property.subtype')
```

**Mapeo:**
- `property_type_id` → `property_type_id`
- ✅ Mismo modelo: `property.type`

---

#### Estado de la Propiedad
```python
# ORIGEN (CloudPepper - Odoo 17)
property_status = Selection  # Estado del Inmueble

# DESTINO (Odoo.com - Odoo 18)
property_status = Selection
```

**Mapeo:**
- ✅ Mismo campo: `property_status`

---

#### Es Propiedad
```python
# COMÚN EN AMBAS VERSIONES
is_property = Boolean
```

**Mapeo:**
- ✅ Mismo campo: `is_property`

---

### 5. MODELOS DE UBICACIÓN

#### Departamento (res.country.state)
```python
# MODELO ESTÁNDAR ODOO - Sin cambios
class ResCountryState:
    name = Char
    code = Char
    country_id = Many2one('res.country')
```

---

#### Ciudad (res.city)
```python
# MODELO ESTÁNDAR ODOO - Sin cambios
class ResCity:
    name = Char
    state_id = Many2one('res.country.state')
    country_id = Many2one('res.country')
    zipcode = Char
```

---

#### Región (CAMBIO DE MODELO)
```python
# ORIGEN (CloudPepper - Odoo 17)
class RegionRegion:
    _name = 'region.region'
    name = Char
    # Relación con ciudad?

# DESTINO (Odoo.com - Odoo 18)
class PropertyRegion:
    _name = 'property.region'
    name = Char
    city_id = Many2one('res.city')
```

⚠️ **IMPORTANTE:** Los modelos son DIFERENTES. Hay que migrar registros de `region.region` a `property.region`.

---

#### Barrio (NUEVO EN ODOO 18)
```python
# NO EXISTE en CloudPepper

# NUEVO en Odoo.com (Odoo 18)
class PropertyNeighborhood:
    _name = 'property.neighborhood'
    name = Char
    region_id = Many2one('property.region')
    city_id = Many2one('res.city')
```

⚠️ **IMPORTANTE:** El modelo `property.neighborhood` NO EXISTE en CloudPepper. Hay que decidir cómo mapear los datos.

---

## ESTRATEGIA DE MIGRACIÓN

### PASO 1: Migrar Departamentos
```python
# Leer de CloudPepper
state_id = property['state_id']  # [660, 'Córdoba CO (CO)']
state_name = state_id[1] if state_id else None

# Buscar o crear en Odoo 18
target_state_id = find_or_create_state(state_name)

# Asignar
vals['property_state_id'] = target_state_id
```

---

### PASO 2: Migrar Ciudades
```python
# Leer de CloudPepper
city_id = property['city_id']  # [1554, 'MONTERÍA (230017)']
city_name = city_id[1] if city_id else None

# Buscar o crear en Odoo 18
target_city_id = find_or_create_city(city_name, target_state_id)

# Asignar
vals['property_city_id'] = target_city_id
```

---

### PASO 3: Migrar Región/Barrio
```python
# Leer de CloudPepper
region_id = property['region_id']  # False o [123, 'Santa Bárbara']

if region_id:
    # Buscar registro en region.region
    region_data = get_region_from_cloudpepper(region_id[0])
    region_name = region_data['name']

    # OPCIÓN A: Tratar como región
    target_region_id = find_or_create_region(region_name, target_city_id)
    vals['property_region_id'] = target_region_id

    # OPCIÓN B: Tratar como barrio
    target_neighborhood_id = find_or_create_neighborhood(region_name, target_region_id)
    vals['property_neighborhood_id'] = target_neighborhood_id
```

---

### PASO 4: Migrar Características
```python
vals = {
    'property_bedrooms': property.get('num_bedrooms'),
    'property_bathrooms': property.get('num_bathrooms'),
    'property_garages': property.get('n_garage'),
    'property_area_total': property.get('property_area'),
    'property_area_built': property.get('area_in_m2'),
    'property_floor_number': property.get('floor_number'),
}
```

---

### PASO 5: Migrar Precios
```python
vals = {
    'list_price': property.get('list_price'),
    'property_price_rent': property.get('rental_fee'),
    'standard_price': property.get('standard_price'),
}
```

---

## TABLA RESUMEN DE MAPEO

| Campo Origen (Odoo 17) | Campo Destino (Odoo 18) | Cambio Requerido |
|------------------------|-------------------------|------------------|
| `state_id` | `property_state_id` | ✅ Renombrar |
| `city_id` | `property_city_id` | ✅ Renombrar |
| `region_id` → `region.region` | `property_region_id` → `property.region` | ⚠️ Migrar modelo |
| (NO EXISTE) | `property_neighborhood_id` | ⚠️ Crear lógica |
| `num_bedrooms` | `property_bedrooms` | ✅ Renombrar |
| `num_bathrooms` | `property_bathrooms` | ✅ Renombrar |
| `n_garage` | `property_garages` | ✅ Renombrar |
| `property_area` | `property_area_total` | ✅ Renombrar |
| `area_in_m2` | `property_area_built` | ✅ Renombrar |
| `floor_number` | `property_floor_number` | ✅ Renombrar |
| `rental_fee` | `property_price_rent` | ✅ Renombrar |
| `list_price` | `list_price` | ✅ Sin cambio |
| `property_type_id` | `property_type_id` | ✅ Sin cambio |
| `property_status` | `property_status` | ✅ Sin cambio |
| `is_property` | `is_property` | ✅ Sin cambio |

---

## ARCHIVOS GENERADOS

1. **cloudpepper_property_fields.json** - Lista completa de campos en CloudPepper
2. **comparacion_template_models.json** - Comparación completa entre DBs
3. **migrate_properties_17_to_18.py** - Script de migración (ACTUALIZAR)

---

## PRÓXIMOS PASOS

1. ✅ Identificar campos correctos en CloudPepper
2. ✅ Mapear campos entre versiones
3. 🔄 Actualizar script migrate_properties_17_to_18.py
4. 🔄 Probar migración con 10 propiedades
5. 🔄 Validar datos migrados
6. 🔄 Migración masiva de 2498 propiedades
7. 🔄 Migrar imágenes usando product.image

---

**Conclusión:** La migración requiere adaptación de nombres de campos y conversión del modelo `region.region` a `property.region` / `property.neighborhood`.

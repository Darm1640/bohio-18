# 📊 ANÁLISIS DEL MODELO PROPERTY - real_estate_bits

## 🏗️ Información General

**Modelo:** `Property`
**Hereda de:** `product.template`
**Archivo:** `real_estate_bits/models/property.py`
**Descripción:** Modelo principal para gestión de propiedades inmobiliarias
**Orden:** Por `sequence` e `id`

---

## 📋 CATEGORÍAS DE CAMPOS

### 1. **INFORMACIÓN BÁSICA (BASIC INFO)**

#### Estado y Secuencia
| Campo | Tipo | Valores | Descripción |
|---|---|---|---|
| `state` | Selection | free, reserved, on_lease, sold, blocked | Estado de la propiedad |
| `sequence` | Integer | - | Orden de visualización |
| `default_code` | Char | BOH-XXX | Código interno automático (trigram index) |
| `partner_id` | Many2one | res.partner | Propietario principal |
| `region_id` | Many2one | region.region | Barrio |
| `property_date` | Date | - | Fecha de registro |
| `country_code` | Char | - | Código del país (relacionado) |
| `note` | Html | - | Notas adicionales |
| `description` | Text | - | Descripción de la propiedad |

**Características:**
- ✅ Código automático: `BOH-{sequence}` generado por `_compute_default_code()`
- ✅ Tracking habilitado en todos
- ✅ Índices: trigram en `default_code` para búsqueda rápida

---

### 2. **TIPOS DE PROPIEDAD (PROPERTY TYPES)**

| Campo | Tipo | Descripción |
|---|---|---|
| `property_type_id` | Many2one | Referencia a property.type |
| `property_type` | Selection | Tipo de inmueble (relacionado, almacenado) |

**Relación:** Campo relacionado que almacena el tipo para consultas eficientes

---

### 3. **UBICACIÓN (LOCATION)** ⭐

#### Campos de Dirección Básica
| Campo | Tipo | Index | Descripción |
|---|---|---|---|
| `address` | Char | trigram | Dirección completa |
| `department` | Char | trigram | Departamento (texto libre) |
| `municipality` | Char | trigram | Municipio (texto libre) |
| `neighborhood` | Char | trigram | Barrio (texto libre) |
| `street` | Char | trigram | Dirección principal |
| `street2` | Char | trigram | Dirección secundaria |
| `zip` | Char | normal | Código postal |
| `city` | Char | trigram | Ciudad (texto) |

#### Campos de Ubicación Estructurada
| Campo | Tipo | Dominio | Descripción |
|---|---|---|---|
| `city_id` | Many2one | res.city | Ciudad (relacional) |
| `state_id` | Many2one | res.country.state | Departamento (relacional) |
| `country_id` | Many2one | res.country | País (default: país de compañía) |

**Nota:** Mezcla campos de texto libre (CharField) con relaciones (Many2one) para flexibilidad

---

### 4. **GEOLOCALIZACIÓN AUTOMÁTICA** 🌍

| Campo | Tipo | Precisión | Descripción |
|---|---|---|---|
| `latitude` | Float | (10, 8) | Latitud GPS automática |
| `longitude` | Float | (11, 8) | Longitud GPS automática |
| `geocoding_status` | Selection | pending/success/failed/manual | Estado de geocodificación |
| `full_computed_address` | Char | Computed, Stored | Dirección completa para geocodificación |

**Métodos relacionados:**
- `_compute_full_address_geo()` - Construye dirección completa
- Geocodificación automática basada en dirección

---

### 5. **DETALLES DE PROPIEDAD (PROPERTY DETAILS)**

#### Clasificación
| Campo | Tipo | Valores | Descripción |
|---|---|---|---|
| `stratum` | Selection | 1-6, commercial, no_stratified | Estrato socioeconómico |
| `type_service` | Selection | sale, rent, sale_rent, vacation_rent | Tipo de servicio |
| `property_status` | Selection | new, used, remodeled | Estado del inmueble |

---

### 6. **MEDIDAS (MEASUREMENTS)** 📏

| Campo | Tipo | Precisión | Descripción |
|---|---|---|---|
| `property_area` | Float | (16, 8) | Área en unidad seleccionada |
| `unit_of_measure` | Selection | m, yard, hectare | Unidad de medida |
| `unit_label` | Char | Computed | Etiqueta de unidad |
| `area_in_m2` | Float | (16, 8) | Área convertida a m² (interno) |
| `unit_iso_code` | Char | Computed | Código ISO de unidad |
| `unit_display_name` | Char | Computed | Nombre de unidad para display |
| `front_meters` | Float | (10, 2) | Frente en metros |
| `depth_meters` | Float | (10, 2) | Fondo en metros |

**Métodos de conversión:**
- `_compute_unit_label()` - Etiqueta de unidad
- `_compute_area_in_m2()` - Conversión a m²
- `_compute_unit_iso_info()` - Información ISO

---

### 7. **CARACTERÍSTICAS BÁSICAS (BASIC CHARACTERISTICS)**

| Campo | Tipo | Descripción |
|---|---|---|
| `num_bedrooms` | Integer | Número de habitaciones |
| `num_bathrooms` | Integer | Número de baños |
| `property_age` | Integer | Antigüedad del inmueble |
| `num_living_room` | Integer | Número de salas |
| `floor_number` | Integer | Número de piso |
| `number_of_levels` | Integer | Número de niveles |

---

### 8. **SALAS Y ESPACIOS (ROOMS AND SPACES)** 🏠

#### Salas y Comedores
| Campo | Tipo | Descripción |
|---|---|---|
| `living_room` | Boolean | ¿Tiene sala? |
| `living_dining_room` | Boolean | ¿Tiene sala comedor? |
| `main_dining_room` | Boolean | ¿Tiene comedor? |
| `auxiliary_dining_room` | Boolean | ¿Tiene comedor auxiliar? |
| `study` | Boolean | ¿Tiene estudio? |
| `entrance_hall` | Boolean | ¿Tiene hall? |

#### Cocinas
| Campo | Tipo | Descripción |
|---|---|---|
| `simple_kitchen` | Boolean | Cocina sencilla |
| `integral_kitchen` | Boolean | Cocina integral |
| `american_kitchen` | Boolean | Cocina tipo americano |
| `mixed_integral_kitchen` | Boolean | Cocina integral mixta |

#### Cuartos de Servicio
| Campo | Tipo | Descripción |
|---|---|---|
| `service_room` | Boolean | Alcoba de servicio |
| `service_bathroom` | Boolean | Baño de servicio |
| `auxiliary_bathroom` | Boolean | Baño auxiliar |
| `utility_room` | Boolean | Cuarto útil |

#### Almacenamiento
| Campo | Tipo | Descripción |
|---|---|---|
| `closet` | Boolean | ¿Tiene clóset? |
| `n_closet` | Integer | Número de clósets |
| `walk_in_closet` | Boolean | Walk-in closet |
| `dressing_room` | Boolean | Vestidor |
| `n_dressing_room` | Integer | Número de vestidores |
| `warehouse` | Boolean | Depósito/Bodega |

---

### 9. **ÁREAS EXTERIORES (OUTDOOR AREAS)** 🌳

| Campo | Tipo | Descripción |
|---|---|---|
| `patio` | Boolean | Patio |
| `garden` | Boolean | Jardín |
| `balcony` | Boolean | Balcón |
| `terrace` | Boolean | Terraza |
| `solar_area` | Boolean | Solar |
| `solarium` | Boolean | Solarium |
| `laundry_area` | Boolean | Zona de lavandería |

---

### 10. **PISOS Y ACABADOS (FLOORS AND FINISHES)**

#### Tipo de Piso
| Campo | Tipo | Valores |
|---|---|---|
| `floor_type` | Selection | tile, wood, ceramic, porcelain, marble, carpet, aluminum, fiberglass |
| `marble_floor` | Boolean | Piso en baldosa/mármol |

#### Puertas y Ventanas
| Campo | Tipo | Valores/Descripción |
|---|---|---|
| `door_type` | Selection | wood, metal, glass, aluminum, fiberglass |
| `security_door` | Boolean | Puerta de seguridad |
| `truck_door` | Boolean | Puerta camión |
| `blinds` | Boolean | Persianas |

---

### 11. **PARQUEADERO (PARKING)** 🚗

| Campo | Tipo | Descripción |
|---|---|---|
| `garage` | Boolean | ¿Tiene garaje? |
| `n_garage` | Integer | Número de garajes |
| `covered_parking` | Integer | Parqueaderos cubiertos |
| `uncovered_parking` | Integer | Parqueaderos descubiertos |
| `linear_double_parking` | Boolean | Parqueadero doble lineal |
| `parallel_double_parking` | Boolean | Parqueadero doble paralelo |
| `visitors_parking` | Boolean | Parqueadero visitantes |
| `common_parking` | Boolean | Parqueadero común |

---

### 12. **SERVICIOS PÚBLICOS (UTILITIES AND SERVICES)** ⚡

#### Gas
| Campo | Tipo | Descripción |
|---|---|---|
| `gas_installation` | Boolean | Red de gas |
| `gas_heating` | Boolean | Calentador a gas |
| `no_gas` | Boolean | Sin gas |

#### Electricidad
| Campo | Tipo | Descripción |
|---|---|---|
| `electric_heating` | Boolean | Calentador eléctrico |
| `electric_plant` | Boolean | Planta eléctrica |
| `electrical_capacity` | Char | Capacidad eléctrica |
| `lamps_included` | Boolean | Lámparas incluidas |

#### Agua (Optimizado - NUEVO)
| Campo | Tipo | Descripción | Uso |
|---|---|---|---|
| `has_water` | Boolean | ¿Tiene agua? | Disponibilidad general |
| `hot_water` | Boolean | Agua caliente | Propiedades residenciales |
| `water_nearby` | Boolean | Agua cerca | Terrenos |
| `aqueduct_access` | Boolean | Acceso al acueducto | Conexión pública |

#### Aire Acondicionado
| Campo | Tipo | Descripción |
|---|---|---|
| `air_conditioning` | Boolean | Aire acondicionado |
| `n_air_conditioning` | Integer | Cantidad de aires |
| `ac_connections` | Boolean | Acometidas A/C |
| `n_ac_connections` | Integer | Cantidad de acometidas |

#### Comunicaciones
| Campo | Tipo | Descripción |
|---|---|---|
| `phone_lines` | Integer | Líneas telefónicas |
| `intercom` | Boolean | Citófono |

---

### 13. **SEGURIDAD (SECURITY)** 🔒

| Campo | Tipo | Descripción |
|---|---|---|
| `has_security` | Boolean | ¿Tiene seguridad? (consolidado) |
| `security_cameras` | Boolean | Cámaras de vigilancia |
| `alarm` | Boolean | Alarma |

---

### 14. **AMENIDADES DEL EDIFICIO (BUILDING AMENITIES)**

#### Portería
| Campo | Tipo | Valores | Descripción |
|---|---|---|---|
| `doorman` | Selection | 24_hours, daytime, virtual, none | Tipo de portería |
| `doorman_hours` | Char | - | Horario de portería |
| `doorman_phone` | Char | - | Teléfono portería |

#### Ascensores
| Campo | Tipo | Descripción |
|---|---|---|
| `elevator` | Boolean | Ascensor |
| `private_elevator` | Boolean | Ascensor privado |

---

## 🔧 MÉTODOS PRINCIPALES

### 1. **Cálculo de Código Automático**
```python
@api.depends('property_type_id')
def _compute_default_code(self):
    """Generar código automático BOH-XXX"""
    for rec in self:
        if not rec.default_code and rec.id:
            sequence = self.env['ir.sequence'].next_by_code('property.code') or str(rec.id).zfill(3)
            rec.default_code = f"BOH-{sequence}"
```

### 2. **Dirección Completa para Geocodificación**
```python
@api.depends('street', 'city', 'state_id', 'country_id')
def _compute_full_address_geo(self):
    """Construye dirección completa para servicios de geocodificación"""
    # Combina campos de dirección disponibles
```

### 3. **Conversión de Unidades de Medida**
```python
@api.depends('property_area', 'unit_of_measure')
def _compute_area_in_m2(self):
    """Convierte área a m² para cálculos internos"""
    # Factores de conversión:
    # - m² = 1
    # - Yarda² = 0.836127
    # - Hectárea = 10000
```

### 4. **Información ISO de Unidades**
```python
@api.depends('unit_of_measure')
def _compute_unit_iso_info(self):
    """Obtiene código ISO y nombre de unidad"""
    # Mapeo de unidades a códigos ISO
```

---

## 📊 ÍNDICES Y OPTIMIZACIONES

### Índices Trigram (Búsqueda de texto)
- `default_code` - Código de propiedad
- `address` - Dirección completa
- `department` - Departamento
- `municipality` - Municipio
- `neighborhood` - Barrio
- `street` - Dirección principal
- `street2` - Dirección secundaria
- `city` - Ciudad

**Ventaja:** Búsquedas rápidas con coincidencias parciales

### Índices Normales
- `state` - Estado de propiedad
- `sequence` - Orden
- `partner_id` - Propietario
- `region_id` - Barrio
- `property_date` - Fecha
- `property_type_id` - Tipo
- `property_type` - Tipo relacionado
- Todos los campos Integer de características

---

## 🎯 CARACTERÍSTICAS DESTACADAS

### ✅ Ventajas del Diseño

1. **Tracking Completo**
   - Todos los campos tienen `tracking=True`
   - Auditoría automática de cambios

2. **Búsqueda Optimizada**
   - Índices trigram en campos de texto
   - Índices normales en campos relacionales y numéricos

3. **Geocodificación Automática**
   - Cálculo de coordenadas desde dirección
   - Estado de geocodificación trackeable

4. **Flexibilidad de Ubicación**
   - Campos de texto libre para datos no estructurados
   - Campos relacionales para datos estructurados
   - Permite migración gradual

5. **Conversión de Unidades**
   - Soporte para m², yardas², hectáreas
   - Conversión automática a m² para cálculos

6. **Código Automático**
   - Generación de código BOH-XXX
   - Secuencia automática

---

## 🔍 CAMPOS NO MOSTRADOS EN EL ANÁLISIS PARCIAL

El archivo tiene **2,300+ líneas**, por lo que hay más campos relacionados con:

- Precios y valores (list_price, sale_price, etc.)
- Impuestos y administración
- Características adicionales del inmueble
- Amenidades del conjunto/edificio
- Contratos y reservas
- Imágenes y adjuntos
- Estados de aprobación
- Campos computados adicionales
- Métodos de negocio
- Integraciones externas

---

## 📝 RECOMENDACIONES

1. **Mantener índices trigram** en campos de búsqueda frecuente
2. **Usar campos computados stored** para datos derivados frecuentes
3. **Tracking selectivo** - evaluar si todos los campos necesitan tracking
4. **Consolidar campos similares** - como los de agua (ya optimizado)
5. **Documentar métodos** de geocodificación y conversión de unidades

---

**Total de campos mostrados:** ~100+
**Categorías principales:** 14
**Métodos computados:** 4+ (en sección mostrada)
**Líneas del archivo:** 2,300+

Este análisis cubre aproximadamente el **10-15%** del archivo completo.

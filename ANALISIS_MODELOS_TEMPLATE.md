# ANÁLISIS COMPARATIVO: product.template entre Bases de Datos

**Fecha:** 2025-10-11
**Bases de Datos Analizadas:**
- **DB1 (Producción):** CloudPepper - https://inmobiliariabohio.cloudpepper.site
- **DB2 (Desarrollo):** Odoo.com - https://darm1640-bohio-18.odoo.com

---

## 1. RESUMEN EJECUTIVO

| Métrica | CloudPepper (Producción) | Odoo.com (Desarrollo) |
|---------|--------------------------|------------------------|
| **Total Campos** | 449 | 442 |
| **Campos Comunes** | 415 | 415 |
| **Campos Exclusivos** | 34 | 27 |
| **Campos de Propiedades** | 130 | 137 |
| **Diferencias de Tipo** | 0 | 0 |

### Conclusiones Principales:
- ✅ **Alta compatibilidad:** 415 campos comunes (92%)
- ✅ **Sin conflictos de tipo:** No hay campos con tipos diferentes entre DBs
- ⚠️ **7 campos más de propiedades en Desarrollo:** Incluye mejoras importantes
- ⚠️ **34 campos exclusivos en Producción:** Mayormente módulos adicionales

---

## 2. CAMPOS CRÍTICOS PARA MIGRACIÓN DE IMÁGENES

### ✅ DISPONIBLES EN AMBAS BASES DE DATOS

Los siguientes campos existen en ambas DBs y son seguros para usar:

- `image_1920` - Imagen principal del producto
- `property_state_id` - Departamento/Estado
- `property_city_id` - Ciudad
- `property_neighborhood_id` - Barrio
- `property_region_id` - Región
- `latitude` - Latitud GPS
- `longitude` - Longitud GPS
- `street` - Calle/Dirección
- `property_type_id` - Tipo de propiedad

### ⭐ CAMPOS EXCLUSIVOS EN DESARROLLO (Odoo.com)

Estos campos **SOLO existen en Desarrollo** y son fundamentales para el sistema de imágenes:

#### 🎯 Sistema de Imágenes (NUEVO)
```python
property_image_ids = One2many('property.image')
  # Galería completa de imágenes de la propiedad
  # Relación con modelo property.image

image_count = Integer (readonly)
  # Contador de imágenes en la galería
  # Calculado automáticamente
```

#### 📄 Sistema de Documentos (NUEVO)
```python
property_attachment_ids = One2many('ir.attachment')
  # Documentos asociados a la propiedad
  # Contratos, planos, certificados, etc.

document_count = Integer (readonly)
  # Contador de documentos adjuntos
  # Calculado automáticamente
```

#### 🔐 Sistema de Vendedores Exclusivos (NUEVO)
```python
exclusive_salesperson_ids = Many2many('res.users')
  # Vendedores con acceso exclusivo a la propiedad
  # Útil para asignación de propiedades específicas
```

#### 🗺️ Geocodificación Mejorada (NUEVO)
```python
full_computed_address = Char (readonly)
  # Dirección completa pre-calculada
  # Optimizada para servicios de geocodificación
```

#### 🖼️ Hover Image (NUEVO)
```python
hover_image = Binary
  # Imagen alternativa al pasar mouse
  # Para efectos visuales en website
```

### ⚠️ CAMPOS EXCLUSIVOS EN PRODUCCIÓN (CloudPepper)

Estos campos **SOLO existen en Producción:**

#### 📋 Sistema de Documentos (Versión Antigua)
```python
attachment_line_ids = One2many('attachment.line')
  # Sistema de documentos más simple
  # Puede estar reemplazado por property_attachment_ids en Desarrollo

dr_document_ids = Many2many('ir.attachment')
  # Documentos descargables desde eCommerce
  # Funcionalidad específica de CloudPepper
```

#### 💰 Precio de Referencia
```python
line_price_reference = Float
  # Campo para precio de referencia
  # No presente en Desarrollo
```

#### 🧾 Cuenta de Reembolso
```python
property_account_refund_id = Many2one('account.account')
  # Configuración contable específica
  # No presente en Desarrollo
```

---

## 3. IMPACTO EN MIGRACIÓN DE IMÁGENES

### ✅ ESCENARIO ACTUAL (Desarrollo → Producción)

#### Modelo `property.image` Existe en:
- ✅ **Desarrollo (Odoo.com):** Sí, con campo `property_image_ids`
- ❓ **Producción (CloudPepper):** **Posiblemente NO** (no aparece `property_image_ids`)

### ⚠️ RIESGO IDENTIFICADO

El script `create_images_in_odoo.py` y `extract_property_images.py` están diseñados para:

```python
# Crear registros en property.image
vals = {
    'name': filename,
    'property_id': property_id,  # Relación con product.template
    'sequence': sequence,
    'is_cover': is_cover,
    'image_type': 'main',
    'image_1920': image_base64,
    'is_public': True
}

models.execute_kw(
    db, uid, password,
    'property.image', 'create',  # ⚠️ Modelo puede no existir en Producción
    [vals]
)
```

### 🔧 SOLUCIONES POSIBLES

#### Opción 1: Verificar si property.image existe en Producción
```python
# Añadir al script de migración
try:
    models.execute_kw(db, uid, password,
        'ir.model', 'search',
        [[('model', '=', 'property.image')]]
    )
    print("✅ Modelo property.image disponible")
except:
    print("❌ Modelo property.image NO existe")
```

#### Opción 2: Usar solo image_1920 (campo principal)
```python
# Actualizar directamente product.template
models.execute_kw(
    db, uid, password,
    'product.template', 'write',
    [[property_id], {'image_1920': first_image_base64}]
)
```

#### Opción 3: Instalar módulo real_estate_bits en Producción
- Verificar si `real_estate_bits` está instalado en CloudPepper
- Si no está, instalarlo primero
- Esto añadiría el modelo `property.image`

---

## 4. CAMPOS DE UBICACIÓN: ANÁLISIS COMPLETO

### ✅ Campos Comunes (Disponibles en Ambas DBs)

```python
# Campos de ubicación estándar
property_state_id = Many2one('res.country.state')
  # Departamento/Estado (Córdoba, Antioquia, etc.)

property_city_id = Many2one('res.city')
  # Ciudad (Montería, Medellín, etc.)

property_neighborhood_id = Many2one('property.neighborhood')
  # Barrio/Vecindario

property_region_id = Many2one('property.region')
  # Región dentro de la ciudad

# Coordenadas GPS
latitude = Float
longitude = Float

# Dirección
street = Char
street2 = Char
zip = Char
```

### 📊 Estado de Datos de Ubicación

Según análisis previos en `migrate_property_location.py`:
- ⚠️ Muchas propiedades tienen `city_id` vacío
- ⚠️ Necesitan migración desde nombres de texto a IDs
- ⚠️ Requieren normalización y matching con res.city

---

## 5. RECOMENDACIONES PARA MIGRACIÓN

### 🎯 Plan de Acción Inmediato

#### Paso 1: Verificar Disponibilidad de Modelos
```bash
# Ejecutar script de verificación
python verify_property_image_model.py
```

#### Paso 2: Si property.image NO existe en Producción
- **Opción A:** Instalar módulo `real_estate_bits` en CloudPepper
- **Opción B:** Modificar scripts para usar solo `image_1920` en `product.template`
- **Opción C:** Crear módulo personalizado que añada `property.image`

#### Paso 3: Priorizar Migración
1. ✅ Migrar imágenes principales (`image_1920` en product.template) - Seguro
2. ✅ Verificar campos de ubicación (city_id, neighborhood_id, etc.) - Existen en ambas
3. ⚠️ Galería de imágenes (`property_image_ids`) - Verificar disponibilidad primero

### 📋 Orden Sugerido de Operaciones

```
1. Completar descarga de imágenes desde bohioconsultores.com
   → Ejecutar: python batch_download_from_list.py 100

2. Verificar modelo property.image en Producción
   → Crear script de verificación

3a. SI property.image existe:
    → Usar create_images_in_odoo.py sin cambios

3b. SI property.image NO existe:
    → Modificar script para usar solo image_1920
    → O instalar módulo necesario primero

4. Corregir datos de ubicación (city_id vacíos)
   → Ya tienes migrate_property_location.py (corregido)

5. Migrar imágenes en lotes
   → 100 propiedades a la vez para control
```

---

## 6. DIFERENCIAS EN CAMPOS DE INVENTARIO

### Solo en Desarrollo (Odoo.com)

```python
lot_valuated = Boolean
  # Valoración por número de lote/serie
  # Útil para propiedades numeradas (apartamentos en torres)

biz_total_sale_count = Integer
  # Contador de ventas totales
  # Análisis de rendimiento

taxes_id = Many2many('account.tax')
  # Impuestos de venta
  # Configuración fiscal

uom_po_id = Many2one('uom.uom')
  # Unidad de medida para compras
  # Gestión de inventario
```

**Impacto:** Bajo - No afecta migración de imágenes

---

## 7. PRÓXIMOS PASOS RECOMENDADOS

1. ✅ **COMPLETADO:** Análisis comparativo de modelos
2. 🔄 **PENDIENTE:** Verificar existencia de `property.image` en CloudPepper
3. 🔄 **PENDIENTE:** Decidir estrategia de migración de galería de imágenes
4. 🔄 **PENDIENTE:** Completar descarga de 2485 propiedades restantes
5. 🔄 **PENDIENTE:** Ejecutar migración de ubicaciones (city_id)
6. 🔄 **PENDIENTE:** Cargar imágenes a Odoo (según disponibilidad de modelo)

---

## 8. ARCHIVOS DE REFERENCIA

- **Comparación JSON:** `comparacion_template_models.json`
- **Script de Comparación:** `compare_template_models.py`
- **Modelo Propiedades:** `real_estate_bits/models/property_attachments.py`
- **Script Extracción:** `extract_property_images.py`
- **Script Creación Odoo:** `create_images_in_odoo.py`
- **Migración Ubicación:** `migrate_property_location.py` (CORREGIDO)

---

**Análisis generado:** 2025-10-11
**Bases analizadas:** CloudPepper (Producción) vs Odoo.com (Desarrollo)
**Total campos analizados:** 891 (449 + 442)

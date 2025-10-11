# GUÍA DE MIGRACIÓN DE IMÁGENES - ODOO 18

**Fecha:** 2025-10-11

## RESUMEN DE HALLAZGOS

### ✅ SOLUCIÓN: Usar modelo estándar product.image

En Odoo 18, **NO se necesita `property.image`** personalizado. El modelo estándar `product.image` funciona perfectamente para galerías de imágenes.

---

## DIFERENCIAS ENTRE BASES DE DATOS

| Aspecto | CloudPepper (Producción) | Odoo.com (Desarrollo) |
|---------|---------------------------|------------------------|
| **product.image** | ✅ SÍ (estándar) | ✅ SÍ (estándar) |
| **property.image** | ❌ NO | ✅ SÍ (personalizado) |
| **product_template_image_ids** | ✅ SÍ → product.image | ✅ SÍ → product.image |
| **property_image_ids** | ❌ NO | ✅ SÍ → property.image |

### Conclusión:
- **product.image** existe en AMBAS bases
- **property.image** solo existe en Desarrollo (requiere theme_bohio_real_estate)

---

## LÓGICA DE ODOO 18 PARA IMÁGENES

### Modelo Estándar: product.image

```python
class ProductImage(models.Model):
    _name = 'product.image'

    name = fields.Char('Name')
    sequence = fields.Integer('Sequence')  # 0 = imagen principal
    image_1920 = fields.Binary('Image')
    product_tmpl_id = fields.Many2one('product.template')
    product_variant_id = fields.Many2one('product.product')
```

### Relación en product.template:

```python
class ProductTemplate(models.Model):
    _name = 'product.template'

    # Imagen principal (sincronizada automáticamente con sequence=0)
    image_1920 = fields.Binary('Image')

    # Galería de imágenes adicionales
    product_template_image_ids = fields.One2many(
        'product.image',
        'product_tmpl_id',
        string='Extra Product Media'
    )
```

### 🎯 LÓGICA AUTOMÁTICA DE ODOO 18:

1. **Primera imagen (sequence=0):**
   - Se crea en `product.image`
   - Se **sincroniza automáticamente** con `product.template.image_1920`
   - Es la imagen principal que aparece en vistas de lista/kanban

2. **Imágenes adicionales (sequence > 0):**
   - Solo se guardan en `product.image`
   - Forman la galería en `product_template_image_ids`

---

## EQUIVALENCIA DE CAMPOS

### property.image (PERSONALIZADO - No recomendado)

```python
{
    'property_id': 123,           # Relación con product.template
    'is_cover': True,              # Marca imagen principal
    'image_type': 'main',          # Tipo de imagen
    'is_public': True,             # Visibilidad pública
    'sequence': 1,
    'image_1920': base64_data,
}
```

### product.image (ESTÁNDAR ODOO 18 - Recomendado)

```python
{
    'product_tmpl_id': 123,        # Relación con product.template
    'sequence': 0,                 # 0 = principal, 1+ = galería
    'image_1920': base64_data,
    'name': 'Imagen 1',
}
```

**Mapeo de lógica:**
- `is_cover=True` → `sequence=0`
- `is_cover=False` → `sequence > 0`
- `image_type`, `is_public` → No necesarios (lógica por sequence)

---

## SCRIPT ACTUALIZADO PARA ODOO 18

### Versión ANTERIOR (con property.image):

```python
# ❌ NO FUNCIONA en CloudPepper
vals = {
    'name': filename,
    'property_id': property_id,      # Campo no existe en product.image
    'is_cover': is_cover,             # Campo no existe en product.image
    'image_type': 'main',             # Campo no existe en product.image
    'is_public': True,                # Campo no existe en product.image
    'sequence': sequence,
    'image_1920': image_base64,
}

models.execute_kw(db, uid, password, 'property.image', 'create', [vals])
```

### Versión NUEVA (con product.image):

```python
# ✅ FUNCIONA en ambas bases
vals = {
    'name': filename,
    'product_tmpl_id': property_id,   # Campo estándar Odoo 18
    'sequence': sequence,              # 0 para principal, 1+ para galería
    'image_1920': image_base64,
}

models.execute_kw(db, uid, password, 'product.image', 'create', [vals])
```

---

## VENTAJAS DEL MODELO ESTÁNDAR

### ✅ Ventajas de usar product.image:

1. **Compatibilidad universal:** Funciona en CloudPepper Y Odoo.com
2. **Sin dependencias:** No requiere módulos personalizados
3. **Integración automática:** Sincroniza con image_1920
4. **eCommerce listo:** Compatible con website/shop
5. **Mantenible:** Usa estándares de Odoo
6. **Actualizable:** Sobrevivirá a upgrades futuros

### ⚠️ Desventajas de usar property.image:

1. **Solo en Desarrollo:** No existe en CloudPepper
2. **Requiere módulo:** Necesita theme_bohio_real_estate instalado
3. **Campos extra:** is_cover, image_type, is_public no son estándar
4. **Dependencia personalizada:** Puede romperse en upgrades

---

## PLAN DE MIGRACIÓN RECOMENDADO

### FASE 1: Actualizar Scripts ✅

1. Modificar `create_images_in_odoo.py`:
   - Cambiar modelo: `'property.image'` → `'product.image'`
   - Cambiar relación: `'property_id'` → `'product_tmpl_id'`
   - Cambiar lógica: `is_cover=True` → `sequence=0`
   - Eliminar campos: `is_cover`, `image_type`, `is_public`

2. Actualizar `extract_property_images.py`:
   - Cambiar generación de código SQL
   - Usar sintaxis de product.image

### FASE 2: Migrar a CloudPepper (Producción)

```bash
# Descargar imágenes de bohioconsultores.com
python batch_download_from_list.py 100

# Subir a CloudPepper usando product.image
python create_images_in_odoo_v18.py \
    --db inmobiliariabohio.cloudpepper.site \
    --url https://inmobiliariabohio.cloudpepper.site
```

### FASE 3: Migrar a Odoo.com (Desarrollo)

```bash
# Misma lógica, diferente configuración
python create_images_in_odoo_v18.py \
    --db darm1640-bohio-18-main-24081960 \
    --url https://darm1640-bohio-18.odoo.com
```

---

## VALIDACIÓN DE SINCRONIZACIÓN

### Verificar imagen principal sincronizada:

```python
# Buscar propiedad
property_ids = models.execute_kw(
    db, uid, password,
    'product.template', 'search',
    [[('default_code', '=', 'BOH-8935')]]
)

# Leer imagen principal
property = models.execute_kw(
    db, uid, password,
    'product.template', 'read',
    [property_ids],
    {'fields': ['image_1920', 'product_template_image_ids']}
)[0]

# Validar
if property['image_1920']:
    print("✅ Imagen principal sincronizada")

if property['product_template_image_ids']:
    print(f"✅ Galería con {len(property['product_template_image_ids'])} imágenes")
```

---

## PRÓXIMOS PASOS

### 1. Crear script actualizado
```bash
python create_images_in_odoo_v18.py
```

### 2. Probar con 10 propiedades
```bash
python create_images_in_odoo_v18.py --test --limit 10
```

### 3. Validar resultados
- Verificar image_1920 en product.template
- Verificar product_template_image_ids tiene registros
- Abrir propiedad en Odoo y ver galería

### 4. Migración masiva
```bash
python create_images_in_odoo_v18.py --batch 100
```

---

## REFERENCIAS

- **Modelo Estándar:** `odoo/addons/product/models/product_template.py`
- **Documentación:** https://www.odoo.com/documentation/18.0/developer/reference/backend/orm.html
- **Script Actualizado:** `create_images_in_odoo_v18.py`
- **Análisis Previo:** `ANALISIS_MODELOS_TEMPLATE.md`

---

**Conclusión:** Usar `product.image` (estándar) en lugar de `property.image` (personalizado) garantiza compatibilidad universal y mantenibilidad a largo plazo.

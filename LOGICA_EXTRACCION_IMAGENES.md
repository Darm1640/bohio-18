# LÓGICA DE EXTRACCIÓN Y MIGRACIÓN DE IMÁGENES DE PROPIEDADES

## RESUMEN EJECUTIVO

Sistema completo para extraer imágenes de propiedades desde `bohioconsultores.com` y migrarlas a Odoo 18 con clasificación automática por código de propiedad.

---

## 1. ESTRUCTURA DE URLs

### URLs de Propiedades
```
https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8935
https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta%20y%20Arriendo-8933
```

**Patrón detectado:** El ID de la propiedad está al **final de la URL** después del último guion

### URLs de Imágenes
```
https://bohio.arrendasoft.co/img/big/800x600_GOPR6519.JPG
https://bohio.arrendasoft.co/img/big/800x600_GOPR7041.JPG
```

**Características:**
- Dominio externo: `bohio.arrendasoft.co`
- Path fijo: `/img/big/`
- Formato: `800x600_[NOMBRE_ARCHIVO].JPG`
- Tamaño: 800x600 pixels

---

## 2. PROCESO DE EXTRACCIÓN

### Script: `extract_property_images.py`

```python
# USO
python extract_property_images.py "URL_DE_LA_PROPIEDAD"

# EJEMPLO
python extract_property_images.py "https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8935"
```

### Pasos del Proceso

1. **Extracción del ID**
   - Parsea la URL
   - Extrae número al final (ej: `8935`, `8933`)
   - Valida que existe

2. **Descarga del HTML**
   - Hace request HTTP a la página
   - Obtiene HTML completo

3. **Parsing de Imágenes**
   - Busca tags `<img>` y `<a>`
   - Filtra solo imágenes de `bohio.arrendasoft.co`
   - Extrae URLs completas

4. **Clasificación Automática**
   - **Primera imagen** → `is_cover=True`, `image_type='main'`
   - **Resto de imágenes** → `is_cover=False`, `image_type='other'`
   - Asigna `sequence` del 1 al N

5. **Generación de Script**
   - Crea archivo `migrate_property_[ID]_images.py`
   - Incluye todas las imágenes con metadata

---

## 3. RESULTADOS DE EXTRACCIÓN

### Propiedad 8935
- **Total imágenes:** 26
- **Primera (portada):** `800x600_GOPR6519.JPG`
- **Script generado:** `migrate_property_8935_images.py`

### Propiedad 8933
- **Total imágenes:** 23
- **Primera (portada):** `800x600_GOPR7041.JPG`
- **Script generado:** `migrate_property_8933_images.py`

---

## 4. MIGRACIÓN A ODOO 18

### Modelo de Datos: `property.image`

```python
{
    'name': 'Nombre del archivo',
    'property_id': ID de la propiedad (product.template),
    'sequence': Orden de visualización (1, 2, 3...),
    'is_cover': True si es portada, False si no,
    'image_type': 'main', 'exterior', 'interior', etc.,
    'image_1920': Imagen en base64,
    'is_public': True para mostrar en website
}
```

### Script de Migración

```python
# Para cada propiedad se genera un script individual
python migrate_property_8935_images.py
python migrate_property_8933_images.py
```

#### Proceso de Migración

1. **Conexión a Odoo**
   ```python
   ODOO_URL = 'http://localhost:8069'
   ODOO_DB = 'bohio_db'
   ODOO_USER = 'admin'
   ODOO_PASS = 'admin'
   ```

2. **Búsqueda de Propiedad**
   ```python
   # Busca por código interno
   [('default_code', '=', 'BOH-8935')]
   ```

   **IMPORTANTE:** Ajustar el criterio de búsqueda según tu sistema:
   - Por `default_code` (código interno)
   - Por `id` directo
   - Por algún campo personalizado

3. **Descarga de Imágenes**
   - Hace HTTP GET a cada URL de `bohio.arrendasoft.co`
   - Descarga imagen completa
   - Convierte a base64

4. **Creación en Odoo**
   - Crea registro en modelo `property.image`
   - Asocia a la propiedad
   - Mantiene orden y clasificación

---

## 5. VENTAJAS DE ESTE SISTEMA

### Clasificación Automática
- ✅ ID de propiedad extraído automáticamente
- ✅ Primera imagen siempre es portada
- ✅ Secuencia ordenada (1, 2, 3...)
- ✅ Scripts individuales por propiedad

### Trazabilidad
- ✅ Script generado guarda URL original
- ✅ Metadata completa de cada imagen
- ✅ Nombres de archivo originales preservados

### Flexibilidad
- ✅ Puede ejecutarse propiedad por propiedad
- ✅ O en batch para múltiples propiedades
- ✅ Fácil de modificar criterios de búsqueda

---

## 6. EJEMPLO COMPLETO DE USO

### Paso 1: Extraer Imágenes
```bash
python extract_property_images.py "https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8935"
```

**Output:**
```
================================================================================
🏠 EXTRACTOR DE IMÁGENES DE PROPIEDADES
================================================================================

✅ ID de Propiedad: 8935
📥 Obteniendo página...
📸 Total imágenes encontradas: 26

🖼️  Lista de imágenes:
    1. ⭐ PRINCIPAL 800x600_GOPR6519.JPG
    2.    800x600_GOPR6515.JPG
    ...

💾 Script de migración guardado: migrate_property_8935_images.py
```

### Paso 2: Revisar Script Generado
```bash
# Revisar el archivo generado
type migrate_property_8935_images.py
```

### Paso 3: Ajustar Búsqueda (si es necesario)
```python
# Editar línea 27 del script generado
# ANTES:
[[('default_code', '=', 'BOH-8935')]]

# OPCIONES:
[[('id', '=', 123)]]  # Si conoces el ID
[[('name', 'ilike', 'Apartamento%')]]  # Por nombre
[[('x_custom_field', '=', '8935')]]  # Campo personalizado
```

### Paso 4: Ejecutar Migración
```bash
python migrate_property_8935_images.py
```

**Output:**
```
✅ Propiedad encontrada: ID=123

📥 Descargando: 800x600_GOPR6519.JPG
   ✅ Imagen creada: ID=1

📥 Descargando: 800x600_GOPR6515.JPG
   ✅ Imagen creada: ID=2

...

✅ Migración completada
```

---

## 7. INTEGRACIÓN CON ODOO 18

### Modelo Existente: `property.image`

Ubicado en: `real_estate_bits/models/property_attachments.py:43`

```python
class PropertyImage(models.Model):
    _name = 'property.image'
    _description = 'Imagen de Propiedad'
    _inherit = ['image.mixin']
    _order = 'sequence, id'

    name = fields.Char('Nombre', required=True)
    sequence = fields.Integer('Secuencia', default=10)
    property_id = fields.Many2one('product.template', 'Propiedad', required=True)
    image_1920 = fields.Image('Imagen', max_width=1920, max_height=1920)

    image_type = fields.Selection([
        ('main', 'Principal'),
        ('exterior', 'Exterior'),
        ('interior', 'Interior'),
        ('bathroom', 'Baño'),
        ('kitchen', 'Cocina'),
        ('bedroom', 'Habitación'),
        ('amenity', 'Amenidad'),
        ('view', 'Vista'),
        ('floor_plan', 'Plano'),
        ('other', 'Otra')
    ], default='other')

    is_cover = fields.Boolean('Portada', default=False)
    is_public = fields.Boolean('Pública', default=True)
```

### Relación con Propiedad

```python
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    property_image_ids = fields.One2many('property.image', 'property_id')
    image_count = fields.Integer(compute='_compute_image_count')
```

---

## 8. CASOS DE USO AVANZADOS

### Batch Processing (Múltiples Propiedades)

```python
# Crear archivo: batch_extract_images.py

urls = [
    "https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8935",
    "https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8933",
    "https://bohioconsultores.com/detalle-propiedad/?Casa-en-Venta-7821",
    # ... más URLs
]

for url in urls:
    os.system(f'python extract_property_images.py "{url}"')
```

### Sincronización Automática

```python
# Agregar a extract_property_images.py
def auto_migrate():
    """Ejecuta migración automáticamente después de extraer"""
    # Generar script
    script_path = generate_migration_script()

    # Ejecutar inmediatamente
    os.system(f'python {script_path}')
```

---

## 9. TROUBLESHOOTING

### Error: Propiedad no encontrada

```python
# Verificar que existe en Odoo
# En Odoo shell o XML-RPC:
property_ids = env['product.template'].search([
    ('default_code', '=', 'BOH-8935')
])
print(f"Encontradas: {len(property_ids)}")
```

### Error: No se pueden descargar imágenes

```
❌ Error: HTTPError 403
```

**Solución:** Agregar headers HTTP
```python
headers = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': 'https://bohioconsultores.com/'
}
response = requests.get(url, headers=headers)
```

### Error: Imagen ya existe

```python
# Agregar validación en el script
existing = models.execute_kw(
    ODOO_DB, uid, ODOO_PASS,
    'property.image', 'search',
    [[('property_id', '=', property_id), ('name', '=', filename)]]
)

if existing:
    print(f"⚠️  Imagen ya existe, saltando: {filename}")
    continue
```

---

## 10. PRÓXIMOS PASOS

### Mejoras Sugeridas

1. **API de Arrendasoft**
   - Conectar directamente a su API si está disponible
   - Evitar scraping de HTML

2. **Clasificación Inteligente**
   - Usar IA para detectar tipo de imagen (cocina, baño, etc.)
   - Basado en contenido visual

3. **Optimización de Imágenes**
   - Redimensionar automáticamente
   - Comprimir antes de subir a Odoo

4. **Sincronización Bidireccional**
   - Actualizar cuando cambien en bohioconsultores.com
   - Webhook o cron job

5. **Interface Web**
   - Dashboard para gestionar migraciones
   - Ver progreso en tiempo real

---

## CONCLUSIÓN

Este sistema permite:
- ✅ Extraer imágenes desde URLs de bohioconsultores.com
- ✅ Clasificar automáticamente por código de propiedad
- ✅ Migrar a Odoo 18 preservando orden y metadata
- ✅ Scripts individuales para trazabilidad
- ✅ Fácil de extender y personalizar

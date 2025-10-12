# CÓMO FUNCIONA LA GALERÍA DE IMÁGENES - SISTEMA COMPLETO

## RESUMEN
El sistema de galería de imágenes en la página de detalle de propiedades utiliza el modelo `product.image` de Odoo 18 (heredado del módulo `website_sale`) para mostrar múltiples imágenes en un carrusel, galería en cuadrícula y vista de zoom/lightbox.

---

## 1. MODELO DE DATOS - product.image

### Ubicación del Modelo
- **Módulo:** `website_sale` (módulo core de Odoo 18)
- **Modelo:** `product.image`
- **Relación:** `product.template` → `product_template_image_ids` (One2many)

### Campos Principales
```python
# En product.template
product_template_image_ids = fields.One2many(
    'product.image',
    'product_tmpl_id',
    string='Imágenes Extra'
)

# En product.image
class ProductImage(models.Model):
    _name = 'product.image'
    _description = 'Imágenes de Producto'

    name = fields.Char(string='Nombre')
    sequence = fields.Integer(default=10)
    image_1920 = fields.Image(string='Imagen', max_width=1920, max_height=1920)
    product_tmpl_id = fields.Many2one('product.template', string='Producto', ondelete='cascade')
```

### Jerarquía de Imágenes
1. **Imagen Principal:** `property.image_1920` (campo directo en `product.template`)
2. **Galería Extra:** `property.product_template_image_ids` (relación One2many con `product.image`)

---

## 2. CONTROLADOR - Cómo se Pasa al Template

### Archivo
**`bohio_real_estate/controllers/website.py`** - Líneas 181-193

### Código del Controlador
```python
@http.route('/property/<int:property_id>', type='http', auth='public', website=True)
def property_detail(self, property_id, **kw):
    # Buscar la propiedad
    prop = request.env['product.template'].sudo().search([
        ('id', '=', property_id),
        ('is_property', '=', True)
    ], limit=1)

    if not prop:
        return request.redirect('/properties')

    # Renderizar template con el objeto propiedad
    return request.render('theme_bohio_real_estate.property_detail', {
        'property': prop
    })
```

### ¿Qué Pasa Aquí?
1. **Route:** `/property/<int:property_id>` - Captura el ID de la propiedad desde la URL
2. **Browse:** `sudo().search()` obtiene el registro completo de `product.template`
3. **Render:** Pasa el objeto `prop` como variable `property` al template QWeb
4. **Acceso Automático:** El template QWeb puede acceder directamente a `property.product_template_image_ids` porque es un campo relacional del modelo

---

## 3. TEMPLATE QWEB - Cómo se Obtienen las Imágenes

### Archivo
**`theme_bohio_real_estate/views/property_detail_template.xml`** - Líneas 36-80

### 3.1 Obtener Lista de Imágenes (Línea 36)
```xml
<!-- Establecer variable con todas las imágenes de la galería -->
<t t-set="images_list" t-value="property.product_template_image_ids or []"/>
```

**Explicación:**
- `t-set`: Crea una variable llamada `images_list`
- `t-value`: Asigna el valor desde el recordset de Odoo
- `property.product_template_image_ids`: Accede al campo One2many
- `or []`: Si no hay imágenes, usa lista vacía

### 3.2 Validar si Hay Imágenes (Línea 38)
```xml
<t t-if="len(images_list) > 0">
    <!-- Hay imágenes en la galería -->
</t>
```

### 3.3 Iterar sobre las Imágenes (Línea 40)
```xml
<t t-foreach="images_list" t-as="img">
    <!-- 'img' es un registro de product.image -->
    <!-- 'img_index' se genera automáticamente (0, 1, 2...) -->
</t>
```

**Explicación:**
- `t-foreach`: Itera sobre cada registro en `images_list`
- `t-as="img"`: Cada elemento se llama `img` dentro del loop
- `img_index`: Variable automática con el índice (0-based)
- `img_value`: Variable automática con el valor actual
- `img_first`: Boolean, True si es el primer elemento
- `img_last`: Boolean, True si es el último

### 3.4 Generar URL de Imagen (Línea 43)
```xml
<img t-att-src="'/web/image/product.image/%s/image_1920' % img.id"
     class="position-absolute top-0 start-0 w-100 h-100"
     style="object-fit: cover;"
     t-att-alt="property.name"
     t-att-data-index="img_index"/>
```

**Explicación de la URL:**
- `/web/image/` - Endpoint de Odoo para servir imágenes
- `product.image` - Modelo de la imagen
- `%s` - Se reemplaza con `img.id` (ID del registro)
- `image_1920` - Campo de imagen (tamaño 1920x1920)
- Ejemplo: `/web/image/product.image/42/image_1920`

---

## 4. JAVASCRIPT - Cómo se Cargan las Imágenes

### Archivo
**`theme_bohio_real_estate/views/property_detail_template.xml`** - Líneas 358-560

### 4.1 Cargar Imágenes al Cargar la Página (Líneas 372-375)
```javascript
// Cargar todas las imágenes para el zoom
const images = carousel.querySelectorAll('.carousel-item img');
zoomImages = Array.from(images).map(img => img.src);
```

**Explicación:**
1. `carousel.querySelectorAll('.carousel-item img')` - Selecciona todas las imágenes del carrusel
2. `Array.from(images)` - Convierte NodeList a Array
3. `.map(img => img.src)` - Extrae solo las URLs (atributo `src`)
4. `zoomImages` - Array global con todas las URLs de imágenes

**Ejemplo del Array:**
```javascript
zoomImages = [
    '/web/image/product.image/42/image_1920',
    '/web/image/product.image/43/image_1920',
    '/web/image/product.image/44/image_1920',
    // ...
]
```

### 4.2 Abrir Zoom con Imagen Específica (Líneas 396-407)
```javascript
function openImageZoom(index) {
    currentZoomIndex = index;
    const modal = new bootstrap.Modal(document.getElementById('imageZoomModal'));

    // Actualizar imagen principal
    updateZoomImage();

    // Cargar miniaturas
    loadZoomThumbnails();

    modal.show();
}
```

**Llamada desde el Template:**
```xml
<div t-att-onclick="'openImageZoom(%s)' % img_index">
```
- Se ejecuta cuando el usuario hace clic en una imagen del carrusel
- Pasa el índice de la imagen (0, 1, 2...) como parámetro

### 4.3 Actualizar Imagen en el Zoom (Líneas 410-427)
```javascript
function updateZoomImage() {
    const zoomImage = document.getElementById('zoomImage');
    const zoomIndexSpan = document.getElementById('zoomImageIndex');
    const zoomTotalSpan = document.getElementById('zoomTotalImages');

    if (zoomImages.length > 0) {
        // Cambiar la imagen por su URL
        zoomImage.src = zoomImages[currentZoomIndex];

        // Actualizar contador (1/21)
        zoomIndexSpan.textContent = currentZoomIndex + 1;
        zoomTotalSpan.textContent = zoomImages.length;

        // Mostrar/ocultar botones de navegación
        document.getElementById('zoomPrevBtn').style.display =
            currentZoomIndex > 0 ? 'block' : 'none';
        document.getElementById('zoomNextBtn').style.display =
            currentZoomIndex < zoomImages.length - 1 ? 'block' : 'none';

        // Actualizar miniaturas activas
        updateActiveThumbnail();
    }
}
```

### 4.4 Cargar Miniaturas en el Zoom (Líneas 441-456)
```javascript
function loadZoomThumbnails() {
    const container = document.getElementById('zoomThumbnails');
    let html = '';

    // Iterar sobre todas las imágenes
    zoomImages.forEach((src, index) => {
        html += `
            <div class="zoom-thumbnail ${index === currentZoomIndex ? 'active' : ''}"
                 onclick="jumpToZoomImage(${index})"
                 style="cursor: pointer; opacity: ${index === currentZoomIndex ? '1' : '0.6'};
                        border: ${index === currentZoomIndex ? '2px solid white' : '2px solid transparent'};">
                <img src="${src}" style="width: 80px; height: 60px; object-fit: cover;"/>
            </div>
        `;
    });

    container.innerHTML = html;
}
```

### 4.5 Navegación entre Imágenes (Líneas 430-438)
```javascript
function navigateZoom(direction) {
    currentZoomIndex += direction; // +1 o -1

    // Limitar índices
    if (currentZoomIndex < 0) currentZoomIndex = 0;
    if (currentZoomIndex >= zoomImages.length) currentZoomIndex = zoomImages.length - 1;

    updateZoomImage();
}
```

**Controles del Usuario:**
- **Flechas:** Botones con `onclick="navigateZoom(-1)"` (anterior) y `onclick="navigateZoom(1)"` (siguiente)
- **Teclado:** Event listener para teclas ← y →
- **Miniaturas:** Click en miniatura específica llama `jumpToZoomImage(index)`

---

## 5. FLUJO COMPLETO - De Base de Datos a Pantalla

```
┌─────────────────────────────────────────────────────────────────┐
│  1. BASE DE DATOS - PostgreSQL                                  │
│     - Tabla: product_template (registro de propiedad)           │
│     - Tabla: product_image (múltiples imágenes)                 │
│     - Relación: product_template_image_ids → product.image      │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. CONTROLADOR - website.py                                    │
│     @http.route('/property/<int:property_id>')                  │
│     - Browse: property = env['product.template'].browse(id)     │
│     - Render: {'property': property}                            │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. TEMPLATE QWEB - property_detail_template.xml                │
│     <t t-set="images_list"                                      │
│        t-value="property.product_template_image_ids"/>          │
│                                                                  │
│     <t t-foreach="images_list" t-as="img">                      │
│         <img t-att-src="'/web/image/product.image/%s/image_1920'│
│                         % img.id"/>                             │
│     </t>                                                         │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. SERVIDOR WEB - Odoo HTTP                                    │
│     GET /web/image/product.image/42/image_1920                  │
│     - Lee ir.attachment o campo Binary                          │
│     - Retorna imagen como bytes (JPEG/PNG)                      │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. NAVEGADOR - DOM + JavaScript                                │
│     - Renderiza <img src="/web/image/..."/>                     │
│     - JavaScript:                                               │
│       const images = querySelectorAll('.carousel-item img')     │
│       zoomImages = Array.from(images).map(img => img.src)       │
│     - Usuario hace click → openImageZoom(index)                 │
│     - Modal de zoom muestra imagen: zoomImage.src = zoomImages[index]│
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. ENDPOINTS DE IMAGEN EN ODOO

### 6.1 Formato General
```
/web/image/<modelo>/<id_registro>/<campo_imagen>
```

### 6.2 Ejemplos Reales
```bash
# Imagen principal de la propiedad
/web/image/product.template/123/image_1920

# Imágenes de la galería
/web/image/product.image/42/image_1920
/web/image/product.image/43/image_1920
/web/image/product.image/44/image_1920

# Con parámetros adicionales
/web/image/product.image/42/image_1920?unique=1234567890  # Cache busting
/web/image/product.image/42/image_512                      # Tamaño más pequeño
```

### 6.3 Tamaños Disponibles
- `image_1920` - 1920x1920px (alta resolución)
- `image_1024` - 1024x1024px (resolución media)
- `image_512` - 512x512px (thumbnails)
- `image_256` - 256x256px (iconos)
- `image_128` - 128x128px (avatares pequeños)

---

## 7. FALLBACKS - Qué Pasa Si No Hay Imágenes

### 7.1 Si No Hay Galería Extra (Líneas 52-63)
```xml
<t t-elif="property.image_1920">
    <!-- Mostrar solo la imagen principal -->
    <div class="carousel-item active">
        <img t-att-src="'/web/image/product.template/%s/image_1920' % property.id"/>
    </div>
</t>
```

### 7.2 Si No Hay Ninguna Imagen (Líneas 64-79)
```xml
<t t-else="">
    <!-- Placeholder con imagen genérica -->
    <div class="carousel-item active">
        <img src="/theme_bohio_real_estate/static/src/img/banner1.jpg"
             style="opacity: 0.7; filter: brightness(0.8);"/>
        <div class="position-absolute top-50 start-50 translate-middle">
            <i class="fa fa-image fa-3x"></i>
            <p>Imagen no disponible</p>
        </div>
    </div>
</t>
```

---

## 8. CONTADOR DE IMÁGENES (Línea 102)

```xml
<t t-set="total_images"
   t-value="len(property.product_template_image_ids)
            if property.product_template_image_ids
            else (1 if property.image_1920 else 1)"/>

<span id="currentImageIndex">1</span> / <span id="totalImages" t-esc="total_images"/>
```

**Lógica:**
1. Si hay galería: `len(product_template_image_ids)`
2. Si solo hay imagen principal: `1`
3. Si no hay nada: `1` (mostrará el placeholder)

---

## 9. RESUMEN TÉCNICO

### ¿Cómo Obtiene las Imágenes?
1. **Controlador:** `request.env['product.template'].sudo().search()` obtiene el registro completo
2. **Template:** Accede automáticamente a `property.product_template_image_ids` (campo One2many)
3. **Loop QWeb:** `t-foreach` itera sobre cada registro de `product.image`
4. **URL:** Genera `/web/image/product.image/{id}/image_1920` para cada imagen
5. **JavaScript:** Captura todas las URLs con `querySelectorAll()` y las almacena en array

### ¿Por Qué Funciona?
- **ORM de Odoo:** Al hacer `browse()` o `search()`, Odoo carga automáticamente los campos relacionados
- **QWeb:** Acceso directo a campos del modelo con notación de punto (`property.product_template_image_ids`)
- **Endpoint /web/image:** Odoo expone automáticamente todos los campos de imagen como URLs

### Ventajas de Este Enfoque
- ✅ No requiere queries adicionales
- ✅ Lazy loading de imágenes (Odoo solo carga cuando se accede)
- ✅ URLs optimizadas con cache
- ✅ Soporte nativo para múltiples tamaños
- ✅ Integración con website_sale (modelo estándar de Odoo)

---

## 10. EJEMPLO PRÁCTICO

### Caso Real: Propiedad con 21 Imágenes

1. **Base de Datos:**
```sql
-- product.template (ID: 123)
SELECT id, name, image_1920 FROM product_template WHERE id = 123;

-- product.image (galería)
SELECT id, name, product_tmpl_id FROM product_image WHERE product_tmpl_id = 123;
-- Retorna 21 registros
```

2. **Controlador:**
```python
prop = request.env['product.template'].sudo().search([('id', '=', 123)])
# prop.product_template_image_ids → recordset con 21 imágenes
```

3. **Template QWeb:**
```xml
<t t-set="images_list" t-value="property.product_template_image_ids"/>
<!-- images_list ahora tiene 21 registros -->

<t t-foreach="images_list" t-as="img">
    <!-- Se ejecuta 21 veces -->
    <!-- img_index: 0, 1, 2, ..., 20 -->
</t>
```

4. **JavaScript:**
```javascript
const images = carousel.querySelectorAll('.carousel-item img');
// NodeList con 21 elementos

zoomImages = Array.from(images).map(img => img.src);
// Array con 21 URLs:
// ['/web/image/product.image/42/image_1920',
//  '/web/image/product.image/43/image_1920',
//  ...
//  '/web/image/product.image/62/image_1920']
```

5. **Usuario hace click:**
```javascript
openImageZoom(5); // Click en la imagen #6 (índice 5)
↓
updateZoomImage();
↓
zoomImage.src = zoomImages[5]; // Muestra imagen #6
↓
Contador: "6 / 21"
```

---

## CONCLUSIÓN

El sistema accede a todas las imágenes mediante:
1. **Relación One2many** entre `product.template` y `product.image`
2. **QWeb loop** con `t-foreach` sobre `product_template_image_ids`
3. **URLs dinámicas** generadas con `/web/image/product.image/{id}/image_1920`
4. **JavaScript** que captura las URLs del DOM y las almacena para navegación

**No hay consultas adicionales** ni endpoints personalizados - todo utiliza la estructura estándar de Odoo 18.

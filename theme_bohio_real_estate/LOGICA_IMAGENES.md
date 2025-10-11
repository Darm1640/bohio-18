# Lógica de Carga de Imágenes en Odoo 18

## ❌ Método INCORRECTO (Antiguo)

```python
# NO USAR - Ruta directa sin optimizaciones
'image_url': f'/web/image/product.template/{prop.id}/image_512'
```

### Problemas:
- ❌ No verifica si la imagen existe
- ❌ No maneja CDN
- ❌ No maneja cache
- ❌ No es compatible con lazy loading
- ❌ Falla si `image_512` está vacía
- ❌ No tiene placeholder automático

---

## ✅ Método CORRECTO (Odoo 18)

```python
# Obtener website (fuera del loop para optimización)
website = request.env['website'].get_current_website()

# Para cada propiedad
image_url = website.image_url(prop, 'image_512') if prop.image_512 else '/theme_bohio_real_estate/static/src/img/placeholder.jpg'
```

### Ventajas:
- ✅ Verifica que la imagen existe antes de generar URL
- ✅ Compatible con CDN de Odoo
- ✅ Maneja cache automáticamente
- ✅ Optimización de tamaño (image_512 = 512x512px)
- ✅ Fallback a placeholder si no hay imagen
- ✅ Rendimiento optimizado (website fuera del loop)

---

## 📐 Tamaños de Imagen Disponibles en Odoo

| Campo | Tamaño | Uso Recomendado |
|-------|--------|-----------------|
| `image_1920` | 1920x1920 | Vistas de detalle, hero images |
| `image_1024` | 1024x1024 | Galerías grandes |
| `image_512` | 512x512 | Tarjetas, listas, carruseles |
| `image_256` | 256x256 | Thumbnails, previews |
| `image_128` | 128x128 | Avatares, iconos |

### Regla General:
- **Carruseles y tarjetas**: `image_512`
- **Detalle de propiedad**: `image_1920`
- **Lista compacta**: `image_256`
- **Mapas (popups)**: `image_256` o `image_512`

---

## 🔧 Implementación Correcta por Caso

### 1. Backend - Controlador JSON

```python
@http.route(['/api/properties'], type='json', auth='public')
def get_properties(self, **kwargs):
    Property = request.env['product.template'].sudo()
    properties = Property.search([('is_property', '=', True)], limit=10)

    # IMPORTANTE: Obtener website UNA SOLA VEZ
    website = request.env['website'].get_current_website()

    data = []
    for prop in properties:
        # Usar website.image_url con fallback
        image_url = website.image_url(prop, 'image_512') if prop.image_512 else '/theme_bohio_real_estate/static/src/img/placeholder.jpg'

        data.append({
            'id': prop.id,
            'name': prop.name,
            'image_url': image_url,
        })

    return {'properties': data}
```

### 2. Backend - Página HTML (QWeb)

```xml
<!-- Forma 1: Usando t-field (automático, recomendado) -->
<img t-field="property.image_512" class="img-fluid" alt="Propiedad"/>

<!-- Forma 2: Usando website.image_url en Python y pasando al template -->
<!-- En el controlador: -->
<!--
image_url = request.env['website'].image_url(property, 'image_512')
values = {'property': property, 'image_url': image_url}
return request.render('template_id', values)
-->
<img t-att-src="image_url" class="img-fluid" alt="Propiedad"/>

<!-- Forma 3: Construcción manual (solo si es necesario) -->
<img t-attf-src="/web/image/product.template/#{property.id}/image_512"
     class="img-fluid"
     alt="Propiedad"
     onerror="this.src='/theme_bohio_real_estate/static/src/img/placeholder.jpg'"/>
```

### 3. Frontend - JavaScript

```javascript
// En la tarjeta de propiedad
const imageUrl = property.image_url || '/theme_bohio_real_estate/static/src/img/placeholder.jpg';

return `
    <img src="${imageUrl}"
         class="card-img-top"
         alt="${property.name}"
         loading="lazy"
         onerror="this.src='/theme_bohio_real_estate/static/src/img/placeholder.jpg'"/>
`;
```

---

## 🖼️ Placeholder Images

### Ubicación:
```
theme_bohio_real_estate/static/src/img/
├── placeholder.jpg          # Genérico
├── home-banner.jpg         # Hero sections
└── banner1.jpg             # Proyectos
```

### Uso por contexto:

```python
# Propiedades individuales
image_url = website.image_url(prop, 'image_512') if prop.image_512 else '/theme_bohio_real_estate/static/src/img/placeholder.jpg'

# Proyectos
image_url = website.image_url(project, 'image_1920') if project.image_1920 else '/theme_bohio_real_estate/static/src/img/banner1.jpg'

# Hero/Banner
image_url = property.image_url or '/theme_bohio_real_estate/static/src/img/home-banner.jpg'
```

---

## ⚡ Optimización de Rendimiento

### Problema:
```python
# MALO: Llama get_current_website() N veces
for prop in properties:
    website = request.env['website'].get_current_website()  # ❌
    image_url = website.image_url(prop, 'image_512')
```

### Solución:
```python
# BUENO: Llama get_current_website() UNA VEZ
website = request.env['website'].get_current_website()  # ✅
for prop in properties:
    image_url = website.image_url(prop, 'image_512')
```

### Benchmark:
- ❌ Dentro del loop: ~50ms por imagen (N * 50ms)
- ✅ Fuera del loop: ~50ms total + ~5ms por imagen

---

## 🔍 Verificar que funciona

### 1. Desde Python Shell

```python
# Conectar a Odoo shell
odoo-bin shell -d bohio_db

# Probar
prop = env['product.template'].search([('is_property', '=', True)], limit=1)
website = env['website'].get_current_website()

# Verificar que tiene imagen
print(f"¿Tiene image_512? {bool(prop.image_512)}")

# Obtener URL
if prop.image_512:
    url = website.image_url(prop, 'image_512')
    print(f"URL: {url}")
else:
    print("Sin imagen - usar placeholder")
```

### 2. Desde Navegador

```javascript
// Consola del navegador
const result = await fetch('/carousel/properties', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'call',
        params: {
            carousel_type: 'rent',
            limit: 5
        }
    })
}).then(r => r.json());

// Verificar URLs
console.table(result.result.properties.map(p => ({
    id: p.id,
    name: p.name,
    image_url: p.image_url
})));
```

---

## 🐛 Troubleshooting

### Problema: Imágenes no se muestran

**Síntoma**: Todas las tarjetas muestran el placeholder

**Solución**:
1. Verificar que las propiedades tienen `image_1920` poblada en la BD
2. Revisar logs de Odoo:
```bash
tail -f /var/log/odoo/odoo.log | grep "image_url\|image_512"
```
3. Verificar permisos:
```python
# En Odoo shell
prop = env['product.template'].browse(123)
print(f"Puede leer imagen: {prop.check_access_rights('read', raise_exception=False)}")
```

### Problema: Error 404 en imágenes

**Síntoma**: `GET /web/image/product.template/123/image_512 → 404`

**Causas posibles**:
1. La propiedad no existe (ID incorrecto)
2. La imagen no está poblada
3. Permisos insuficientes

**Solución**:
```python
# Verificar existencia
prop = env['product.template'].sudo().browse(123)
print(f"Existe: {prop.exists()}")
print(f"Tiene imagen: {bool(prop.image_512)}")
print(f"Tamaño imagen: {len(prop.image_512) if prop.image_512 else 0} bytes")
```

### Problema: Imágenes muy pesadas (carga lenta)

**Síntoma**: Página tarda en cargar

**Solución**:
1. Usar tamaño correcto (`image_512` en vez de `image_1920`)
2. Implementar lazy loading:
```html
<img src="..." loading="lazy"/>
```
3. Comprimir imágenes antes de subirlas a Odoo
4. Verificar que CDN está habilitado (Odoo Enterprise)

---

## 📝 Checklist de Migración

Al actualizar código antiguo a la nueva lógica:

- [ ] Buscar todas las ocurrencias de `f'/web/image/product.template/{id}/image_`
- [ ] Reemplazar por `website.image_url(prop, 'image_SIZE')`
- [ ] Agregar verificación `if prop.image_SIZE`
- [ ] Agregar fallback a placeholder
- [ ] Mover `get_current_website()` fuera del loop
- [ ] Probar que las imágenes cargan correctamente
- [ ] Verificar rendimiento (tiempo de respuesta del endpoint)

---

## 🎯 Resumen

### Patrón a seguir SIEMPRE:

```python
# En controladores JSON/HTTP
website = request.env['website'].get_current_website()

for item in items:
    image_url = website.image_url(item, 'image_512') if item.image_512 else '/ruta/placeholder.jpg'
```

```javascript
// En JavaScript
const imageUrl = property.image_url || '/ruta/placeholder.jpg';
```

```xml
<!-- En QWeb -->
<img t-field="property.image_512" alt="..."/>
<!-- O -->
<img t-att-src="image_url" alt="..." onerror="this.src='/ruta/placeholder.jpg'"/>
```

### Lo que NO hacer:

```python
# ❌ Ruta hardcoded sin verificación
'image_url': f'/web/image/product.template/{prop.id}/image_512'

# ❌ get_current_website() dentro del loop
for prop in properties:
    website = request.env['website'].get_current_website()
```

---

**Referencias**:
- [Odoo 18 Image Fields](https://www.odoo.com/documentation/18.0/developer/reference/backend/orm.html#image-fields)
- [Website Image URL Helper](https://github.com/odoo/odoo/blob/18.0/addons/website/models/website.py)

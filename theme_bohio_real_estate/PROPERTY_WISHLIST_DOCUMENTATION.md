# ❤️ PROPERTY WISHLIST (FAVORITOS) - Documentación Completa

## 📋 RESUMEN

Sistema completo de **Favoritos/Wishlist** para propiedades inmobiliarias integrado con Odoo 18. Permite a los usuarios (registrados o anónimos) guardar propiedades favoritas y consultarlas posteriormente.

---

## 🎯 CARACTERÍSTICAS

### ✅ Funcionalidades Implementadas

1. **Toggle de Favoritos** (Agregar/Remover)
   - Clic en el corazón para agregar/quitar de favoritos
   - Animaciones suaves y feedback visual
   - Persistencia por sesión o usuario

2. **Contador en Tiempo Real**
   - Badge con número de favoritos
   - Actualización automática al agregar/remover
   - Sincronización en toda la aplicación

3. **Soporte Multi-Usuario**
   - **Usuarios registrados**: Favoritos guardados en su cuenta
   - **Usuarios anónimos**: Favoritos guardados por sesión
   - Migración automática al iniciar sesión

4. **Compatibilidad Total con Odoo**
   - Usa el modelo nativo `product.wishlist`
   - Extiende `WebsiteSaleWishlist`
   - Compatible con e-commerce de Odoo

5. **Notificaciones Visuales**
   - Mensajes de confirmación
   - Animaciones de estado
   - Indicadores de carga

6. **API REST Completa**
   - Endpoints JSON para AJAX
   - Respuestas estructuradas
   - Manejo robusto de errores

---

## 🏗️ ARQUITECTURA

### Backend (Python)

```
theme_bohio_real_estate/controllers/property_wishlist.py
├── BohioPropertyWishlist (extends WebsiteSaleWishlist)
│   ├── /property/wishlist/add          → Agregar propiedad
│   ├── /property/wishlist/remove       → Remover propiedad
│   ├── /property/wishlist/toggle       → Toggle (add/remove)
│   ├── /property/wishlist/check        → Verificar estado
│   ├── /property/wishlist/count        → Obtener contador
│   └── /property/wishlist/list         → Listar propiedades
```

### Frontend (JavaScript)

```
theme_bohio_real_estate/static/src/js/property_wishlist.js
├── Estado Global
│   ├── wishlistState.count            → Contador total
│   ├── wishlistState.properties       → Set de IDs
│   └── wishlistState.loading          → Estado de carga
├── Funciones Principales
│   ├── togglePropertyWishlist()       → Toggle con animación
│   ├── checkPropertyWishlistStatus()  → Verificar estado
│   ├── updateWishlistButton()         → Actualizar UI
│   ├── showWishlistNotification()     → Mostrar notificación
│   └── getWishlistProperties()        → Obtener lista completa
└── Animaciones CSS
    ├── slideInRight / slideOutRight   → Notificaciones
    ├── pulse                          → Contador
    └── scale                          → Botones
```

### Template (XML)

```xml
property_detail_template.xml (líneas 21-29)
├── <button id="wishlistBtn">
│   ├── data-property-id="{property.id}"
│   └── onclick="togglePropertyWishlist(this)"
└── <i class="bi bi-heart wishlist-icon">
```

---

## 📖 GUÍA DE USO

### 1. Botón de Favoritos en Property Detail

El botón ya está incluido en [property_detail_template.xml](c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\theme_bohio_real_estate\views\property_detail_template.xml:21-29).

**Cómo funciona**:
- **Corazón vacío** (❤️): No está en favoritos
- **Corazón lleno rojo** (❤️ rojo): Está en favoritos
- **Clic**: Toggle (agregar/remover)

### 2. Agregar Botón en Tarjetas de Propiedades

Para agregar el botón de wishlist en las tarjetas de la lista de propiedades:

```xml
<!-- En property_shop_templates.xml o similar -->
<div class="property-card">
    <!-- Imagen y contenido de la tarjeta -->

    <!-- Botón de Wishlist (esquina superior derecha) -->
    <button class="btn btn-light rounded-circle shadow wishlist-btn position-absolute top-0 end-0 m-2"
            style="width: 35px; height: 35px; z-index: 10;"
            t-att-data-property-id="property.id"
            onclick="togglePropertyWishlist(this)"
            title="Agregar a favoritos">
        <i class="bi bi-heart wishlist-icon"></i>
    </button>
</div>
```

### 3. Contador de Favoritos en Header

Agregar contador en el header/navbar:

```xml
<!-- En header_template.xml -->
<a href="/my/wishlist" class="nav-link">
    <i class="bi bi-heart"></i>
    Favoritos
    <span class="badge bg-danger wishlist-counter" id="wishlist_count">0</span>
</a>
```

El contador se actualiza automáticamente vía JavaScript.

### 4. Página de Favoritos

Crear una página que liste todos los favoritos:

```xml
<template id="my_wishlist" name="Mis Favoritos">
    <t t-call="website.layout">
        <div id="wrap" class="oe_structure">
            <div class="container my-5">
                <h1>Mis Propiedades Favoritas</h1>
                <div id="wishlist-properties" class="row">
                    <!-- Se carga dinámicamente vía JavaScript -->
                </div>
            </div>
        </div>
    </t>
</template>
```

Con JavaScript:

```javascript
// Cargar propiedades favoritas
async function loadWishlistPage() {
    const properties = await getWishlistProperties();

    const container = document.getElementById('wishlist-properties');
    container.innerHTML = '';

    if (properties.length === 0) {
        container.innerHTML = '<p class="text-center">No tienes propiedades favoritas</p>';
        return;
    }

    properties.forEach(prop => {
        const card = createPropertyCard(prop);
        container.appendChild(card);
    });
}

// Llamar al cargar la página
document.addEventListener('DOMContentLoaded', loadWishlistPage);
```

---

## 🔌 API ENDPOINTS

### POST `/property/wishlist/toggle`

**Toggle** (agregar/remover) una propiedad del wishlist.

**Request**:
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "property_id": 123
    }
}
```

**Response**:
```json
{
    "result": {
        "success": true,
        "message": "Propiedad agregada a favoritos",
        "new_count": 5,
        "is_in_wishlist": true,
        "action": "added"  // "added" o "removed"
    }
}
```

### POST `/property/wishlist/check`

**Verificar** si una propiedad está en el wishlist.

**Request**:
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "property_id": 123
    }
}
```

**Response**:
```json
{
    "result": {
        "is_in_wishlist": true,
        "total_count": 5
    }
}
```

### POST `/property/wishlist/count`

**Obtener** el contador total de favoritos.

**Request**:
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {}
}
```

**Response**:
```json
{
    "result": {
        "count": 5
    }
}
```

### POST `/property/wishlist/list`

**Obtener** lista completa de propiedades favoritas.

**Request**:
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {}
}
```

**Response**:
```json
{
    "result": {
        "properties": [
            {
                "id": 123,
                "name": "Casa en Poblado",
                "code": "PROP-001",
                "property_type": "house",
                "type_service": "sale",
                "price": 450000000,
                "area": 120,
                "bedrooms": 3,
                "bathrooms": 2,
                "city": "Medellín",
                "image_url": "/web/image/product.template/123/image_512",
                "url": "/property/123"
            },
            // ... más propiedades
        ],
        "count": 5
    }
}
```

---

## 💻 EJEMPLOS DE CÓDIGO

### Ejemplo 1: Toggle Simple

```javascript
// HTML
<button class="btn btn-primary"
        data-property-id="123"
        onclick="togglePropertyWishlist(this)">
    <i class="bi bi-heart wishlist-icon"></i>
    Agregar a Favoritos
</button>

// La función ya está disponible globalmente
// No necesitas código adicional
```

### Ejemplo 2: Verificar Estado al Cargar

```javascript
// Verificar si una propiedad está en favoritos
const propertyId = 123;

const response = await fetch('/property/wishlist/check', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'call',
        params: { property_id: propertyId }
    })
});

const data = await response.json();
const isInWishlist = data.result.is_in_wishlist;

console.log(`Propiedad ${propertyId} en wishlist: ${isInWishlist}`);
```

### Ejemplo 3: Listar Favoritos

```javascript
// Obtener todas las propiedades favoritas
const properties = await getWishlistProperties();

console.table(properties);
// [
//   {id: 123, name: "Casa...", price: 450000000, ...},
//   {id: 456, name: "Apartamento...", price: 320000000, ...},
//   ...
// ]
```

### Ejemplo 4: Actualizar Múltiples Botones

```javascript
// Si tienes múltiples botones de wishlist en la página
// (ej: lista de propiedades)
document.querySelectorAll('.wishlist-btn').forEach(btn => {
    const propertyId = parseInt(btn.dataset.propertyId);

    // Verificar estado para cada uno
    checkPropertyWishlistStatus(propertyId);
});
```

---

## 🎨 PERSONALIZACIÓN DE ESTILOS

### Cambiar Color del Corazón

```css
/* En tu CSS custom */
.wishlist-icon.text-danger {
    color: #E31E24 !important;  /* Rojo BOHIO */
}

/* Hover effect */
.wishlist-btn:hover .wishlist-icon {
    color: #c91920 !important;
}
```

### Cambiar Animación del Botón

```css
/* Personalizar animación */
.wishlist-btn {
    transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.wishlist-btn:hover {
    transform: scale(1.15) rotate(10deg);
}

.wishlist-btn.is-favorite {
    background: linear-gradient(135deg, #fff5f5 0%, #ffe0e0 100%);
}
```

### Cambiar Estilo de Notificación

```javascript
// Editar en property_wishlist.js, función showWishlistNotification
function showWishlistNotification(message, type = 'success') {
    // ... código existente ...

    notification.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: linear-gradient(135deg, #E31E24 0%, #c91920 100%);
        /* ... más estilos personalizados ... */
    `;
}
```

---

## 🔧 CONFIGURACIÓN AVANZADA

### 1. Agregar Dependencia de `website_sale_wishlist`

Si el módulo `website_sale_wishlist` no está instalado:

**En `__manifest__.py`**:
```python
'depends': [
    'website',
    'bohio_real_estate',
    'website_sale_wishlist',  # Agregar esta dependencia
],
```

### 2. Personalizar Mensajes

Editar los mensajes en [property_wishlist.py](c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\theme_bohio_real_estate\controllers\property_wishlist.py):

```python
# Línea ~89
'message': _('¡Propiedad guardada en tus favoritos!'),  # Personalizado

# Línea ~153
'message': _('Propiedad eliminada de favoritos'),  # Personalizado
```

### 3. Limitar Número de Favoritos

```python
# En property_wishlist.py, método add_property_to_wishlist
def add_property_to_wishlist(self, property_id, **kw):
    # ... código existente ...

    # Verificar límite
    current_count = len(wishlist.current())
    MAX_WISHLIST = 20

    if current_count >= MAX_WISHLIST:
        return {
            'success': False,
            'message': _('Has alcanzado el límite de %s favoritos') % MAX_WISHLIST,
            'new_count': current_count,
            'is_in_wishlist': False
        }

    # ... continuar con el código ...
```

### 4. Agregar Analytics

```javascript
// En property_wishlist.js, función togglePropertyWishlist
window.togglePropertyWishlist = async function(button) {
    // ... código existente ...

    if (data.result && data.result.success) {
        // Enviar evento a Google Analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'wishlist_action', {
                'event_category': 'Property',
                'event_label': `Property ${propertyId}`,
                'action': result.action
            });
        }

        // ... resto del código ...
    }
};
```

---

## 🐛 TROUBLESHOOTING

### Problema 1: Botón no responde

**Síntoma**: Clic en el corazón no hace nada.

**Solución**:
1. Verificar que el JavaScript está cargado:
   ```javascript
   console.log(typeof togglePropertyWishlist);
   // Debe mostrar: "function"
   ```

2. Verificar que el `data-property-id` está presente:
   ```javascript
   const btn = document.getElementById('wishlistBtn');
   console.log(btn.dataset.propertyId);
   // Debe mostrar el ID de la propiedad
   ```

3. Verificar en Network tab que se hace la petición a `/property/wishlist/toggle`

### Problema 2: Contador no se actualiza

**Síntoma**: El número de favoritos no cambia.

**Solución**:
```javascript
// Forzar actualización manual
wishlistState.count = 5;
updateWishlistCounters();
```

Verificar que tienes un elemento con clase `wishlist-counter`:
```html
<span class="wishlist-counter" id="wishlist_count">0</span>
```

### Problema 3: Error 404 en endpoint

**Síntoma**: `POST /property/wishlist/toggle → 404 Not Found`

**Solución**:
1. Verificar que el controlador está registrado en `__init__.py`:
   ```python
   from . import property_wishlist
   ```

2. Reiniciar Odoo:
   ```bash
   sudo systemctl restart odoo
   ```

3. Actualizar el módulo:
   ```bash
   odoo-bin -u theme_bohio_real_estate -d bohio_db
   ```

### Problema 4: Favoritos no persisten

**Síntoma**: Al recargar la página, los favoritos desaparecen.

**Causa**: El modelo `product.wishlist` usa `session_id` para usuarios anónimos.

**Solución**:
- Para usuarios anónimos: Los favoritos se pierden al cerrar navegador (comportamiento esperado)
- Para usuarios registrados: Los favoritos persisten indefinidamente
- Sugerencia: Incentivar registro/login para guardar favoritos permanentemente

---

## ✅ CHECKLIST DE INSTALACIÓN

- [x] Crear `property_wishlist.py` en `controllers/`
- [x] Registrar en `controllers/__init__.py`
- [x] Agregar botón en `property_detail_template.xml`
- [x] Crear `property_wishlist.js` en `static/src/js/`
- [x] Registrar JS en `__manifest__.py`
- [x] Agregar dependencia `website_sale_wishlist` (opcional)
- [ ] Reiniciar servidor Odoo
- [ ] Actualizar módulo: `odoo-bin -u theme_bohio_real_estate`
- [ ] Probar en navegador
- [ ] Verificar en modo incógnito (usuario anónimo)
- [ ] Verificar con usuario registrado
- [ ] Probar en móvil

---

## 🚀 PRÓXIMAS MEJORAS

Ideas para mejorar el sistema:

1. **Página de Favoritos**
   - Vista dedicada `/my/wishlist`
   - Comparación de propiedades favoritas
   - Ordenar/filtrar favoritos

2. **Email Alerts**
   - Notificar cuando baje el precio
   - Avisar cuando la propiedad cambie de estado
   - Resumen semanal de favoritos

3. **Compartir Favoritos**
   - Generar link público de wishlist
   - Compartir por WhatsApp/Email
   - Exportar a PDF

4. **Integración CRM**
   - Crear lead automático si tiene >3 favoritos
   - Seguimiento de interés por tipo de propiedad
   - Score de intención de compra

5. **Analytics Avanzado**
   - Propiedades más guardadas en favoritos
   - Tiempo promedio antes de contactar
   - Conversión de favorito → lead

---

## 📞 SOPORTE

Para problemas o consultas:
- **Email**: soporte@bohio.com
- **Documentación Odoo**: https://www.odoo.com/documentation/18.0/
- **GitHub Issues**: (tu repositorio)

---

**Autor**: BOHIO Inmobiliaria - Equipo de Desarrollo
**Fecha**: Octubre 2025
**Versión**: 1.0.0

# Integración de Bootstrap Icons en Theme Bohio Real Estate

## Fecha: 2025-10-13
## Módulo: theme_bohio_real_estate
## Versión Bootstrap Icons: 1.11.3

---

## 📦 INSTALACIÓN

Bootstrap Icons ha sido instalado y configurado en el tema de Odoo 18.

### Pasos Realizados:

1. **Instalación de paquete NPM**:
   ```bash
   npm i bootstrap-icons
   ```

2. **Copia de archivos a static**:
   ```bash
   cp -r node_modules/bootstrap-icons/font/* theme_bohio_real_estate/static/src/lib/bootstrap-icons/
   ```

3. **Agregado al manifest** (`__manifest__.py` línea 76):
   ```python
   'assets': {
       'web.assets_frontend': [
           # Bootstrap Icons
           'theme_bohio_real_estate/static/src/lib/bootstrap-icons/bootstrap-icons.min.css',
           # ...
       ],
   }
   ```

---

## 📂 ESTRUCTURA DE ARCHIVOS

```
theme_bohio_real_estate/
└── static/
    └── src/
        └── lib/
            └── bootstrap-icons/
                ├── bootstrap-icons.css           (versión completa)
                ├── bootstrap-icons.min.css       (versión minificada - USADA)
                ├── bootstrap-icons.scss          (para compilación)
                ├── bootstrap-icons.json          (metadata)
                └── fonts/
                    ├── bootstrap-icons.woff
                    └── bootstrap-icons.woff2
```

---

## 🎨 CÓMO USAR BOOTSTRAP ICONS

### Sintaxis Básica:

```html
<i class="bi bi-{nombre-icono}"></i>
```

### Ejemplos:

```html
<!-- Casa -->
<i class="bi bi-house-fill"></i>

<!-- Corazón -->
<i class="bi bi-heart-fill"></i>

<!-- Ubicación -->
<i class="bi bi-geo-alt-fill"></i>

<!-- Teléfono -->
<i class="bi bi-telephone-fill"></i>

<!-- Email -->
<i class="bi bi-envelope-fill"></i>

<!-- Estrella -->
<i class="bi bi-star-fill"></i>

<!-- Buscar -->
<i class="bi bi-search"></i>

<!-- Calendario -->
<i class="bi bi-calendar-event"></i>

<!-- Dinero -->
<i class="bi bi-currency-dollar"></i>

<!-- Cama -->
<i class="bi bi-bed"></i>

<!-- Coche/Garage -->
<i class="bi bi-car-front"></i>

<!-- Piscina -->
<i class="bi bi-water"></i>

<!-- Jardín -->
<i class="bi bi-flower2"></i>

<!-- Ascensor -->
<i class="bi bi-arrow-up-square"></i>

<!-- Área/Medida -->
<i class="bi bi-rulers"></i>

<!-- Compartir -->
<i class="bi bi-share-fill"></i>

<!-- Imprimir -->
<i class="bi bi-printer-fill"></i>

<!-- Descargar -->
<i class="bi bi-download"></i>

<!-- Mapa -->
<i class="bi bi-map-fill"></i>

<!-- Imágenes -->
<i class="bi bi-images"></i>

<!-- Video -->
<i class="bi bi-camera-video-fill"></i>

<!-- WhatsApp -->
<i class="bi bi-whatsapp"></i>

<!-- Facebook -->
<i class="bi bi-facebook"></i>

<!-- Instagram -->
<i class="bi bi-instagram"></i>

<!-- X/Twitter -->
<i class="bi bi-twitter-x"></i>
```

### Tamaños:

```html
<!-- Con clases de Bootstrap -->
<i class="bi bi-house-fill fs-1"></i>  <!-- Extra grande -->
<i class="bi bi-house-fill fs-3"></i>  <!-- Grande -->
<i class="bi bi-house-fill fs-5"></i>  <!-- Normal -->

<!-- Con CSS personalizado -->
<i class="bi bi-house-fill" style="font-size: 2rem;"></i>
<i class="bi bi-house-fill" style="font-size: 1.5rem;"></i>
```

### Colores:

```html
<!-- Con clases de Bootstrap -->
<i class="bi bi-heart-fill text-danger"></i>
<i class="bi bi-star-fill text-warning"></i>
<i class="bi bi-house-fill text-primary"></i>

<!-- Con CSS personalizado -->
<i class="bi bi-house-fill" style="color: #E31E24;"></i>
<i class="bi bi-heart-fill" style="color: #E31E24;"></i>
```

---

## 🔄 DIFERENCIAS CON FONT AWESOME

### Font Awesome:
```html
<i class="fa fa-home"></i>
<i class="fas fa-heart"></i>
<i class="fab fa-whatsapp"></i>
```

### Bootstrap Icons:
```html
<i class="bi bi-house-fill"></i>
<i class="bi bi-heart-fill"></i>
<i class="bi bi-whatsapp"></i>
```

**Ventajas de Bootstrap Icons**:
- ✅ Más ligero (solo ~105KB vs ~700KB de Font Awesome)
- ✅ Mejor integración con Bootstrap 5
- ✅ Iconos más modernos y consistentes
- ✅ Mayor cantidad de iconos (2000+)
- ✅ Sin variantes confusas (fa, fas, fab, far, fal, fad, etc.)

---

## 📋 ICONOS RECOMENDADOS PARA INMOBILIARIA

### Características de Propiedades:
```html
<i class="bi bi-bed"></i>                    <!-- Habitaciones -->
<i class="bi bi-droplet"></i>                <!-- Baños (o bi-shower) -->
<i class="bi bi-car-front"></i>              <!-- Garage -->
<i class="bi bi-water"></i>                  <!-- Piscina -->
<i class="bi bi-flower2"></i>                <!-- Jardín -->
<i class="bi bi-arrow-up-square"></i>        <!-- Ascensor -->
<i class="bi bi-rulers"></i>                 <!-- Área/m² -->
<i class="bi bi-building"></i>               <!-- Piso/Nivel -->
```

### Acciones:
```html
<i class="bi bi-search"></i>                 <!-- Buscar -->
<i class="bi bi-heart-fill"></i>             <!-- Favoritos -->
<i class="bi bi-share-fill"></i>             <!-- Compartir -->
<i class="bi bi-printer-fill"></i>           <!-- Imprimir -->
<i class="bi bi-download"></i>               <!-- Descargar -->
<i class="bi bi-calendar-event"></i>         <!-- Agendar visita -->
<i class="bi bi-envelope-fill"></i>          <!-- Contactar -->
<i class="bi bi-telephone-fill"></i>         <!-- Llamar -->
<i class="bi bi-whatsapp"></i>               <!-- WhatsApp -->
```

### Navegación:
```html
<i class="bi bi-house-fill"></i>             <!-- Inicio -->
<i class="bi bi-grid-3x3-gap-fill"></i>      <!-- Propiedades/Grid -->
<i class="bi bi-map-fill"></i>               <!-- Mapa -->
<i class="bi bi-list-ul"></i>                <!-- Lista -->
<i class="bi bi-filter"></i>                 <!-- Filtros -->
<i class="bi bi-arrow-left"></i>             <!-- Volver -->
<i class="bi bi-arrow-right"></i>            <!-- Siguiente -->
<i class="bi bi-chevron-down"></i>           <!-- Expandir -->
```

### Ubicación:
```html
<i class="bi bi-geo-alt-fill"></i>           <!-- Pin de ubicación -->
<i class="bi bi-pin-map-fill"></i>           <!-- Mapa pin -->
<i class="bi bi-compass"></i>                <!-- Brújula -->
<i class="bi bi-signpost-2"></i>             <!-- Dirección -->
```

### Finanzas:
```html
<i class="bi bi-currency-dollar"></i>        <!-- Precio -->
<i class="bi bi-cash-stack"></i>             <!-- Dinero -->
<i class="bi bi-credit-card"></i>            <!-- Pago -->
<i class="bi bi-percent"></i>                <!-- Descuento -->
```

### Multimedia:
```html
<i class="bi bi-images"></i>                 <!-- Galería fotos -->
<i class="bi bi-camera-fill"></i>            <!-- Cámara -->
<i class="bi bi-camera-video-fill"></i>      <!-- Video -->
<i class="bi bi-play-circle-fill"></i>       <!-- Reproducir -->
<i class="bi bi-eye-fill"></i>               <!-- Ver/Visualizar -->
```

### Estados:
```html
<i class="bi bi-check-circle-fill"></i>      <!-- Disponible -->
<i class="bi bi-x-circle-fill"></i>          <!-- No disponible -->
<i class="bi bi-exclamation-circle"></i>     <!-- Advertencia -->
<i class="bi bi-star-fill"></i>              <!-- Destacado -->
<i class="bi bi-fire"></i>                   <!-- Popular/Hot -->
<i class="bi bi-patch-check-fill"></i>       <!-- Verificado -->
```

---

## 🎯 EJEMPLOS DE USO EN EL TEMA

### En Cards de Propiedades:

```html
<div class="property-features">
    <span class="feature">
        <i class="bi bi-bed"></i> 3 Habitaciones
    </span>
    <span class="feature">
        <i class="bi bi-droplet"></i> 2 Baños
    </span>
    <span class="feature">
        <i class="bi bi-rulers"></i> 120 m²
    </span>
    <span class="feature">
        <i class="bi bi-car-front"></i> 2 Garages
    </span>
</div>
```

### En Botones de Acción:

```html
<button class="btn btn-primary">
    <i class="bi bi-heart-fill me-2"></i> Agregar a Favoritos
</button>

<button class="btn btn-success">
    <i class="bi bi-whatsapp me-2"></i> Contactar por WhatsApp
</button>

<button class="btn btn-info">
    <i class="bi bi-share-fill me-2"></i> Compartir Propiedad
</button>
```

### En Filtros de Búsqueda:

```html
<div class="filter-group">
    <label>
        <i class="bi bi-geo-alt-fill text-danger"></i> Ubicación
    </label>
    <input type="text" class="form-control" placeholder="Ciudad o barrio">
</div>

<div class="filter-group">
    <label>
        <i class="bi bi-currency-dollar text-success"></i> Precio
    </label>
    <input type="number" class="form-control" placeholder="Precio máximo">
</div>
```

### En el Header/Menú:

```html
<nav class="navbar">
    <a class="nav-link" href="/">
        <i class="bi bi-house-fill"></i> Inicio
    </a>
    <a class="nav-link" href="/properties">
        <i class="bi bi-grid-3x3-gap-fill"></i> Propiedades
    </a>
    <a class="nav-link" href="/properties?map=1">
        <i class="bi bi-map-fill"></i> Mapa
    </a>
</nav>
```

### En el Footer/Redes Sociales:

```html
<div class="social-links">
    <a href="https://facebook.com/bohio" target="_blank">
        <i class="bi bi-facebook fs-4"></i>
    </a>
    <a href="https://instagram.com/bohio" target="_blank">
        <i class="bi bi-instagram fs-4"></i>
    </a>
    <a href="https://wa.me/573001234567" target="_blank">
        <i class="bi bi-whatsapp fs-4"></i>
    </a>
</div>
```

---

## 🚀 ACTUALIZAR EL MÓDULO

Después de los cambios, es necesario actualizar el módulo:

### Opción 1: Via Script Python (Recomendado)
```bash
cd c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18
python actualizar_modulo.py
```

### Opción 2: Via Odoo CLI
```bash
cd "C:\Program Files\Odoo 18.0.20250830\server"
..\python\python.exe odoo-bin -c odoo.conf -d bohio_db -u theme_bohio_real_estate --stop-after-init
```

### Opción 3: Via Interfaz Web
1. Ir a Aplicaciones
2. Buscar "Theme Bohio Real Estate"
3. Click en "Actualizar"

**IMPORTANTE**: Después de actualizar, hacer **Ctrl + Shift + R** en el navegador.

---

## 🔍 VERIFICAR INSTALACIÓN

Para verificar que Bootstrap Icons está cargado correctamente:

1. **Abrir cualquier página del sitio**
2. **Abrir DevTools (F12)**
3. **Ir a la pestaña Console**
4. **Ejecutar**:
   ```javascript
   // Verificar si el CSS está cargado
   Array.from(document.styleSheets).find(s => s.href && s.href.includes('bootstrap-icons'))

   // Debe retornar un objeto CSSStyleSheet
   ```

5. **Verificar visualmente**:
   - Agregar temporalmente un icono en cualquier página:
     ```html
     <i class="bi bi-house-fill" style="font-size: 3rem; color: #E31E24;"></i>
     ```
   - Si se ve el icono, Bootstrap Icons está funcionando ✅
   - Si se ve "?" o un cuadrado, hay un problema con la carga ❌

---

## 📚 RECURSOS

- **Documentación Oficial**: https://icons.getbootstrap.com/
- **Lista Completa de Iconos**: https://icons.getbootstrap.com/#icons
- **Ejemplos de Uso**: https://icons.getbootstrap.com/#usage
- **GitHub**: https://github.com/twbs/icons

---

## 🎨 PERSONALIZACIÓN AVANZADA

### Crear Clases Personalizadas:

```css
/* En tu archivo CSS personalizado */
.icon-large {
    font-size: 2.5rem;
}

.icon-bohio-primary {
    color: #E31E24;
}

.icon-with-background {
    background: #E31E24;
    color: white;
    padding: 0.5rem;
    border-radius: 50%;
}
```

Uso:
```html
<i class="bi bi-house-fill icon-large icon-bohio-primary"></i>
<i class="bi bi-heart-fill icon-with-background"></i>
```

### Animaciones:

```css
.icon-pulse {
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.icon-spin {
    animation: spin 2s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
```

Uso:
```html
<i class="bi bi-heart-fill text-danger icon-pulse"></i>
<i class="bi bi-arrow-repeat icon-spin"></i>
```

---

## ✅ CHECKLIST POST-INSTALACIÓN

- [x] Paquete NPM instalado
- [x] Archivos copiados a static/src/lib/
- [x] CSS agregado al manifest
- [ ] Módulo actualizado en Odoo
- [ ] Hard refresh en navegador (Ctrl + Shift + R)
- [ ] Verificar carga en DevTools
- [ ] Probar un icono en una página

---

**Estado**: ✅ **INSTALADO Y CONFIGURADO**

**Próximo Paso**: Actualizar módulo y probar iconos en las páginas del sitio.

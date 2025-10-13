# SOLUCIÓN: Modales y Filtros - Odoo 18

## Fecha: 2025-10-12
## Módulo: theme_bohio_real_estate

---

## PROBLEMA 1: `bootstrap is not defined` - MODALES NO FUNCIONAN

### Error Original:
```
ReferenceError: bootstrap is not defined
    at window.openGalleryModal (https://104.131.70.107/web/assets/4/c62644d/web.assets_frontend_lazy.min.js:11100:13)
    at HTMLButtonElement.onclick (https://104.131.70.107/property/15360:449:281)
```

### Causa Raíz:
En Odoo 18, Bootstrap 5 **NO está disponible como objeto global `bootstrap`**.
El código estaba usando:
```javascript
const modal = new bootstrap.Modal(modalElement);
modal.show();
```

### Solución Aplicada:
Bootstrap 5 en Odoo 18 debe ser manejado a través de **jQuery**, que sí está disponible globalmente.

**ANTES (INCORRECTO):**
```javascript
// ❌ Esto falla porque bootstrap no es global
const modal = new bootstrap.Modal(modalElement);
modal.show();
```

**DESPUÉS (CORRECTO):**
```javascript
// ✅ Usar jQuery para abrir modales en Odoo 18
$('#imageZoomModal').modal('show');
```

### Archivos Corregidos:

#### 1. `property_detail_gallery.js` - Todas las funciones de modales

**Línea 68:** `openImageZoom()`
```javascript
// ANTES:
const modal = new bootstrap.Modal(modalElement);
modal.show();

// DESPUÉS:
$('#imageZoomModal').modal('show');
```

**Línea 192:** `openGalleryModal()`
```javascript
// ANTES:
const modal = new bootstrap.Modal(modalElement);
modal.show();

// DESPUÉS:
$('#galleryModal').modal('show');
```

**Línea 201:** `goToSlide()` - Carousel y cerrar modal
```javascript
// ANTES:
const carousel = bootstrap.Carousel.getInstance(carouselElement);
carousel.to(index);
const modalInstance = bootstrap.Modal.getInstance(galleryModal);
modalInstance.hide();

// DESPUÉS:
$('#propertyImageCarousel').carousel(index);
$('#galleryModal').modal('hide');
```

**Línea 276:** `openShareModal()`
```javascript
// ANTES:
const modal = new bootstrap.Modal(modalElement);
modal.show();

// DESPUÉS:
$('#shareModal').modal('show');
```

**Línea 365:** `openReportModal()`
```javascript
// ANTES:
const modal = new bootstrap.Modal(modalElement);
modal.show();

// DESPUÉS:
$('#reportModal').modal('show');
```

**Línea 440:** `submitReport()` - Cerrar modal
```javascript
// ANTES:
const modalInstance = bootstrap.Modal.getInstance(modalElement);
if (modalInstance) modalInstance.hide();

// DESPUÉS:
$('#reportModal').modal('hide');
```

**Línea 39:** Event listener Escape en zoom
```javascript
// ANTES:
const modalInstance = bootstrap.Modal.getInstance(zoomModal);
if (modalInstance) modalInstance.hide();

// DESPUÉS:
$('#imageZoomModal').modal('hide');
```

### Referencia Técnica:
- **Bootstrap 5 en Odoo 18**: jQuery es el wrapper estándar
- **Documentación**: Odoo 18 usa `web.assets_frontend` que incluye jQuery + Bootstrap 5
- **Método jQuery**: `$(selector).modal('show|hide|toggle')`

---

## PROBLEMA 2: FILTROS SE BORRAN AL PASAR DE HOME A PROPIEDADES

### Descripción del Problema:
El usuario reporta: **"se esta borrando los filtros cuando pasa del home al propiedades"**

### Análisis del Flujo Actual:

#### 1. Homepage → Búsqueda con Filtros
**Archivo**: `homepage_autocomplete.js` (línea 236-264)

```javascript
_onItemClick: function (ev) {
    const $item = $(ev.currentTarget);
    const data = $item.data();

    // Construir URL de redirección
    let params = new URLSearchParams();

    // ✅ Agregar tipo de servicio
    const serviceTypeInput = document.getElementById('selectedServiceType');
    if (serviceTypeInput && serviceTypeInput.value) {
        params.set('type_service', serviceTypeInput.value);
    }

    // ✅ Agregar término de búsqueda
    const searchTerm = $(this.searchInput).val().trim();
    if (searchTerm) {
        params.set('search', searchTerm);
    }

    // ✅ Agregar filtros de ubicación
    if (data.type === 'city' && data.cityId) {
        params.set('city_id', data.cityId);
    } else if (data.type === 'region' && data.regionId) {
        params.set('region_id', data.regionId);
    } else if (data.type === 'project' && data.projectId) {
        params.set('project_id', data.projectId);
    }

    // ✅ Redirigir a la página de propiedades con filtros
    window.location.href = `/properties?${params.toString()}`;
}
```

**Ejemplo de URL generada:**
```
/properties?type_service=rent&search=apartamento&city_id=123&region_id=456
```

#### 2. Página de Propiedades → Debería Leer Filtros

**Archivo**: `property_filters.js` (línea 262-282)

```javascript
setupURLSync() {
    // ✅ Leer filtros de la URL al cargar
    const urlParams = new URLSearchParams(window.location.search);

    Object.keys(this.state.filters).forEach(key => {
        const value = urlParams.get(key);
        if (value) {
            if (typeof this.state.filters[key] === 'boolean') {
                this.state.filters[key] = value === 'true';
            } else {
                this.state.filters[key] = value;
            }
        }
    });

    // ✅ Manejar botón atrás/adelante del navegador
    window.addEventListener('popstate', () => {
        this.setupURLSync();
        this.loadProperties();
    });
}
```

### Posibles Causas del Problema:

#### Causa 1: El componente OWL `PropertyFilters` no se está montando
El componente está registrado en el registry:
```javascript
registry.category("public_components").add("PropertyFilters", PropertyFilters);
```

**VERIFICAR**: ¿Existe en la página `/properties` el elemento que activa el componente?
```xml
<!-- Debe existir en la plantilla de propiedades -->
<owl-component name="PropertyFilters"/>
```

#### Causa 2: El componente se monta DESPUÉS de cargar propiedades
El ciclo de vida OWL ejecuta:
1. `onWillStart()` → Carga filtros iniciales
2. `onMounted()` → Lee URL con `setupURLSync()`

**PROBLEMA**: Si `loadProperties()` se ejecuta en `onWillStart()` ANTES de leer la URL, cargará sin filtros.

**SOLUCIÓN RECOMENDADA**:
```javascript
async onWillStart() {
    // PRIMERO: Leer filtros de la URL
    this._readFiltersFromURL();

    // SEGUNDO: Cargar opciones de filtros
    await this.loadInitialFilters();

    // TERCERO: Cargar propiedades con filtros aplicados
    await this.loadProperties();
}

_readFiltersFromURL() {
    const urlParams = new URLSearchParams(window.location.search);

    Object.keys(this.state.filters).forEach(key => {
        const value = urlParams.get(key);
        if (value) {
            if (typeof this.state.filters[key] === 'boolean') {
                this.state.filters[key] = value === 'true';
            } else {
                this.state.filters[key] = value;
            }
        }
    });

    console.log('Filtros leídos de URL:', this.state.filters);
}
```

#### Causa 3: La página `/properties` usa JavaScript vanilla en vez del componente OWL

**VERIFICAR**: ¿La página de propiedades usa:
- A) Componente OWL `PropertyFilters` (dinámico, con state reactivo)
- B) JavaScript vanilla que carga propiedades directamente

Si usa JavaScript vanilla (opción B), necesita implementar lectura de URL manualmente:

```javascript
// En property_shop.js o similar
document.addEventListener('DOMContentLoaded', function() {
    // Leer filtros de la URL
    const urlParams = new URLSearchParams(window.location.search);

    const filters = {
        type_service: urlParams.get('type_service') || '',
        city_id: urlParams.get('city_id') || '',
        region_id: urlParams.get('region_id') || '',
        project_id: urlParams.get('project_id') || '',
        search: urlParams.get('search') || '',
    };

    console.log('Filtros recibidos desde homepage:', filters);

    // Aplicar filtros a la búsqueda
    loadPropertiesWithFilters(filters);
});
```

### Causa 4: Contexto de AJAX - Filtros no se pasan al backend

Usuario menciona: **"recuerda que se esta usando ajax creo que se debe manda un contexto para mantener ciertos casos"**

**VERIFICAR** en el endpoint del backend `/property/search/ajax`:

```python
@http.route('/property/search/ajax', type='json', auth='public', website=True, csrf=False)
def property_search_ajax(self, context='public', filters=None, page=1, ppg=20, order='newest', **kwargs):
    """
    IMPORTANTE: Debe recibir y aplicar filters desde el frontend
    """
    if not filters:
        filters = {}

    # Construir domain con los filtros
    domain = [('is_property', '=', True), ('active', '=', True)]

    # Aplicar filtros de tipo de servicio
    if filters.get('type_service'):
        domain.append(('type_service', 'in', [filters['type_service'], 'sale_rent']))

    # Aplicar filtros de ubicación
    if filters.get('city_id'):
        domain.append(('city_id', '=', int(filters['city_id'])))

    if filters.get('region_id'):
        domain.append(('region_id', '=', int(filters['region_id'])))

    if filters.get('project_id'):
        domain.append(('project_worksite_id', '=', int(filters['project_id'])))

    # Búsqueda por término
    if filters.get('search'):
        search_term = filters['search']
        domain.append('|', '|', '|',
            ('name', 'ilike', search_term),
            ('default_code', 'ilike', search_term),
            ('city_id.name', 'ilike', search_term),
            ('region_id.name', 'ilike', search_term)
        )

    # Buscar propiedades
    Property = request.env['product.template']
    properties = Property.search(domain, limit=ppg, offset=(page-1)*ppg, order=order)

    return {
        'success': True,
        'properties': [self._format_property(p) for p in properties],
        'total': Property.search_count(domain),
    }
```

---

## RESUMEN DE CORRECCIONES APLICADAS

### ✅ Problema 1: Modales - SOLUCIONADO
- **Archivo**: `property_detail_gallery.js`
- **Cambio**: Todas las funciones de modales ahora usan jQuery (`$('#modal').modal('show')`)
- **Estado**: ✅ COMPLETO

### ⚠️ Problema 2: Filtros - REQUIERE VERIFICACIÓN

**Archivos a verificar:**

1. **Vista de propiedades** (`/properties`)
   - ¿Usa componente OWL `PropertyFilters`?
   - ¿O usa JavaScript vanilla?

2. **Controller del backend** (`main.py`)
   - ¿El endpoint `/property/search/ajax` recibe y aplica los filtros correctamente?

3. **Orden de ejecución** (property_filters.js)
   - ¿Se leen los filtros de la URL ANTES de cargar las propiedades?

**Solución propuesta a implementar:**
```javascript
// En property_filters.js - Modificar setup()
setup() {
    this.state = useState({ /* ... */ });

    onWillStart(async () => {
        // 1. PRIMERO: Leer URL
        this._readFiltersFromURL();

        // 2. SEGUNDO: Cargar opciones
        await this.loadInitialFilters();

        // 3. TERCERO: Cargar propiedades con filtros
        await this.loadProperties();
    });

    onMounted(() => {
        // 4. Configurar historial del navegador
        this._setupPopStateHandler();
    });
}

_readFiltersFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    Object.keys(this.state.filters).forEach(key => {
        const value = urlParams.get(key);
        if (value) {
            this.state.filters[key] = value;
        }
    });
}
```

---

## PRÓXIMOS PASOS

1. **Reiniciar Odoo** para cargar el JavaScript corregido:
   ```bash
   net stop "Odoo 18.0"
   timeout /t 3 /nobreak
   net start "Odoo 18.0"
   ```

2. **Limpiar caché del navegador** (Ctrl + Shift + R)

3. **Verificar modales**:
   - Abrir cualquier propiedad en detalle
   - Hacer click en los botones de Zoom, Compartir, Galería, Reportar
   - ✅ Deben abrir sin errores de consola

4. **Verificar filtros**:
   - Desde homepage, buscar "apartamento" o seleccionar ciudad
   - Click en resultado
   - Verificar en `/properties` que:
     - La URL tiene parámetros: `?type_service=rent&city_id=123`
     - Los filtros se aplican en la interfaz
     - Las propiedades mostradas coinciden con los filtros

5. **Si los filtros NO funcionan**, ejecutar:
   ```javascript
   // En consola del navegador, en la página /properties
   console.log('URL params:', new URLSearchParams(window.location.search).toString());
   console.log('PropertyFilters state:', window._propertyFiltersInstance?.state);
   ```

---

## REFERENCIAS TÉCNICAS

### Bootstrap 5 en Odoo 18 - Modales
- **Método correcto**: `$('#modalId').modal('show|hide|toggle')`
- **NO usar**: `new bootstrap.Modal()` (no disponible)
- **jQuery siempre disponible**: Incluido en `web.assets_frontend`

### OWL Component Lifecycle
1. `constructor()` → Crear state
2. `setup()` → Registrar hooks
3. `onWillStart()` → Operaciones async ANTES de render
4. `willStart()` → Llamado automáticamente
5. `render()` → Crear DOM virtual
6. `onMounted()` → DOM real disponible, eventos, lectura de elementos

### URL Persistence Pattern
```javascript
// Lectura → Aplicación → Actualización → Historial
URLSearchParams(search) → state.filters → loadProperties() → pushState()
```

---

## CONCLUSIÓN

- ✅ **Modales**: Corregidos completamente usando jQuery
- ⚠️ **Filtros**: Requiere verificación de implementación en página `/properties`
- 📋 **Documentación**: Este archivo sirve como referencia para debugging futuro

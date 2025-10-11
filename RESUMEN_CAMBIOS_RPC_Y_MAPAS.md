# RESUMEN DE CAMBIOS - RPC NATIVO Y CORRECCIONES

**Fecha**: 2025-10-10
**Objetivo**: Migrar todos los archivos JavaScript a RPC nativo de Odoo 18 y corregir problemas de carga de propiedades

---

## 1. PROBLEMA CRÍTICO RESUELTO: Importaciones RPC Incorrectas

### ❌ **Error Original**
Todos los archivos JS intentaban importar desde módulos que NO están disponibles en `web.assets_frontend`:
```javascript
import { jsonrpc } from "@web/core/network/rpc_service";  // ❌ NO EXISTE en frontend
import { jsonrpc } from "@web/legacy/js/core/rpc";        // ❌ NO EXISTE en frontend
```

### ✅ **Solución Aplicada**
Usar el módulo RPC que SÍ está disponible en `web.assets_frontend`:
```javascript
import { rpc } from "@web/core/network/rpc";  // ✅ CORRECTO
```

---

## 2. ARCHIVOS MODIFICADOS

### 📄 **theme_bohio_real_estate/static/src/js/homepage_properties.js**

**Línea 3** - Importación corregida:
```javascript
import { rpc } from "@web/core/network/rpc";
```

**Líneas 193-207** - Endpoint y parámetros corregidos:
```javascript
async function loadProperties(params) {
    try {
        const result = await rpc('/property/search/ajax', {
            context: 'public',
            filters: params,
            page: 1,
            ppg: params.limit || 20,
            order: params.order || 'relevance'
        });
        return result;
    } catch (error) {
        console.error('Error cargando propiedades:', error);
        return { properties: [] };
    }
}
```

**Líneas 213-285** - Carga de propiedades con ubicación:
```javascript
// Arriendo: 20 propiedades más recientes con ubicación
const rentData = await loadProperties({
    type_service: 'rent',
    has_location: true,
    limit: 20,
    order: 'newest'
});

// Venta usada: 20 propiedades más recientes con ubicación
const usedSaleData = await loadProperties({
    type_service: 'sale',
    is_project: false,
    has_location: true,
    limit: 20,
    order: 'newest'
});

// Proyectos: 20 propiedades más recientes con ubicación
const projectsData = await loadProperties({
    type_service: 'sale',
    is_project: true,
    has_location: true,
    limit: 20,
    order: 'newest'
});
```

---

### 📄 **theme_bohio_real_estate/static/src/js/homepage_autocomplete.js**

**Línea 3** - Importación corregida:
```javascript
import { rpc } from "@web/core/network/rpc";
```

**Línea 138** - Uso de RPC nativo:
```javascript
const result = await rpc('/property/search/autocomplete', {
    term: term,
    context: this.options.context,
    subdivision: this.options.subdivision,
    limit: this.options.maxResults
});
```

**Línea 378** - Inicialización con nuevo input:
```javascript
const heroSearchInput = document.getElementById('homepage-search-input');
```

---

### 📄 **theme_bohio_real_estate/static/src/js/property_filters.js**

**Líneas 4-5** - Importaciones corregidas:
```javascript
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
```

**Líneas 95, 115, 139** - Uso de RPC nativo (reemplazados TODOS los `jsonrpc` por `rpc`):
```javascript
const result = await rpc('/property/filters/options', {...});
const result = await rpc('/property/search/ajax', {...});
```

**Línea 328** - Registro en public_components:
```javascript
registry.category("public_components").add("PropertyFilters", PropertyFilters);
```

---

### 📄 **theme_bohio_real_estate/static/src/js/property_shop.js**

**Línea 3** - Importación agregada:
```javascript
import { rpc } from "@web/core/network/rpc";
```

**Línea 117** - Autocompletado con RPC:
```javascript
const result = await rpc('/property/search/autocomplete/' + this.context, {
    term: term,
    subdivision: subdivision,
    limit: 10
});
```

**Línea 299** - Carga de propiedades con RPC:
```javascript
const result = await rpc('/bohio/api/properties', {
    ...this.filters,
    context: this.context,
    limit: this.itemsPerPage,
    offset: (this.currentPage - 1) * this.itemsPerPage
});
```

---

### 📄 **theme_bohio_real_estate/views/homepage_new.xml**

**Líneas 80-86** - Input de búsqueda con autocompletado:
```xml
<!-- Antes: <select> -->
<!-- Ahora: <input> con autocompletado -->
<input type="text"
       name="search"
       id="homepage-search-input"
       class="form-control form-control-lg"
       placeholder="¿Dónde quieres vivir?"
       autocomplete="off"
       style="background: rgba(255,255,255,0.95); border: none; border-radius: 10px; height: 55px; font-size: 15px;"/>
```

---

### 📄 **theme_bohio_real_estate/hooks.py**

**Líneas 13-49** - Corrección de `pre_init_hook`:
```python
def pre_init_hook(cr):
    """
    Hook ejecutado ANTES de instalar/actualizar el módulo

    IMPORTANTE:
    - Este hook NO tiene acceso al registry ni a modelos ORM
    - Solo se pueden ejecutar queries SQL directas
    - No usar api.Environment aquí
    """
    _clean_obsolete_views(cr)  # ✅ Sin parámetro env
    _clean_obsolete_assets(cr)
    _clean_duplicate_menus(cr)
    _clean_theme_cache(cr)
```

**Líneas 52+** - Funciones helper corregidas:
```python
def _clean_obsolete_views(cr):  # ✅ Solo cr, sin env
    """Usa solo SQL directo"""
    cr.execute("""...""")

def _clean_obsolete_assets(cr):  # ✅ Solo cr, sin env
    """Usa solo SQL directo"""
    cr.execute("""...""")
```

---

## 3. ¿POR QUÉ FUNCIONAN AHORA LOS CAMBIOS?

### Módulos disponibles en `web.assets_frontend`:

Según el archivo `__manifest__.py` de Odoo 18:
```python
'web.assets_frontend': [
    'web/static/src/core/**/*',  # ✅ Incluye rpc.js, registry.js
    'web/static/src/public/public_component_service.js',  # ✅ Servicio de componentes públicos
    'web/static/lib/owl/owl.js',  # ✅ OWL framework
]
```

Por lo tanto:
- ✅ `@web/core/network/rpc` → **SÍ está disponible**
- ✅ `@web/core/registry` → **SÍ está disponible**
- ✅ `@odoo/owl` → **SÍ está disponible**
- ❌ `@web/core/network/rpc_service` → **NO está disponible** (solo en backend)
- ❌ `@web/legacy/js/core/rpc` → **NO está disponible**

---

## 4. ENDPOINTS CORRECTOS

### ❌ **Endpoints que NO existen**:
- `/properties/api/list`

### ✅ **Endpoints correctos**:
- `/property/search/ajax` - Búsqueda con filtros (usado en homepage y shop)
- `/property/search/autocomplete` - Autocompletado
- `/bohio/api/properties` - API de propiedades (usado en property_shop.js)

---

## 5. MEJORAS IMPLEMENTADAS

### Homepage (`homepage_properties.js`):
1. ✅ Carga 20 propiedades de cada tipo (arriendo, venta, proyectos)
2. ✅ Solo carga propiedades con `has_location: true` (coordenadas GPS)
3. ✅ Ordena por más recientes `order: 'newest'`
4. ✅ Muestra solo 4 en el grid, pero carga 20 para el mapa
5. ✅ Uso correcto del endpoint `/property/search/ajax`

### Autocompletado:
1. ✅ Cambiado de `<select>` a `<input type="text">`
2. ✅ ID único: `homepage-search-input`
3. ✅ Autocompletado funcional con RPC nativo

### Filtros (property_filters.js):
1. ✅ Componente OWL registrado en `public_components`
2. ✅ Uso de RPC nativo en lugar de fetch
3. ✅ Preparado para filtros dinámicos y unidades de medida

---

## 6. PARA APLICAR LOS CAMBIOS

### En Odoo:
1. **Actualizar el módulo**:
   ```bash
   # Desde Odoo CLI
   odoo-bin -u theme_bohio_real_estate -d tu_base_de_datos

   # O desde la UI
   Aplicaciones → Buscar "bohio" → Actualizar
   ```

2. **Regenerar assets** (importante):
   - Modo debug: Activar modo desarrollador
   - Ir a: Configuración → Técnico → Vistas → Assets
   - Buscar: `web.assets_frontend`
   - Clic en: "Regenerar Assets"

3. **Limpiar caché del navegador**:
   - Presionar `Ctrl + Shift + R` (forzar recarga)
   - O limpiar caché completamente

---

## 7. RESULTADOS ESPERADOS

### ✅ **Lo que debería funcionar**:
1. Sin errores en consola sobre módulos no disponibles
2. Barra de búsqueda con autocompletado funcionando
3. Homepage cargando 20 propiedades de arriendo, venta y proyectos
4. Solo propiedades con ubicación GPS
5. Filtros funcionando en `/properties`
6. Mapas con markers funcionando

### 🔍 **Verificación rápida**:
Abrir consola del navegador (F12) y buscar:
- ✅ "BOHIO Homepage JS cargado"
- ✅ "Propiedades de arriendo cargadas: X"
- ✅ "Propiedades usadas cargadas: X"
- ✅ "Proyectos cargados: X"
- ❌ NO debe haber errores de "modules are needed but have not been defined"

---

## 8. PRÓXIMOS PASOS PENDIENTES

Según los requerimientos del usuario, aún faltan:

1. **Precios dinámicos**: Mostrar ambos precios (venta y arriendo) según tipo de servicio
2. **Filtros dinámicos**: Adaptar filtros según tipo de propiedad
3. **Unidades de medida**: m² vs hectáreas según tipo de propiedad
4. **Grid de 4 columnas**: Cambiar sección de productos de 2 a 4 columnas
5. **Formato de números**: Mejorar visualización de números en filtros
6. **Animaciones**: Agregar transiciones a filtros y toggles booleanos
7. **Geolocalización**: Centrar mapa en ciudad del usuario
8. **Autocompletado mejorado**: Mostrar "Barrio - Ciudad, Departamento"

---

**Autor**: Claude (Anthropic)
**Versión Odoo**: 18.0
**Fecha**: 2025-10-10

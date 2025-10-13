# INSTRUCCIONES DE ACTUALIZACIÓN FINAL

## CAMBIOS REALIZADOS

### ✅ Implementado Sistema Nativo de Snippets:

1. **Creado**: `data/property_snippet_filters.xml`
   - 3 `ir.filters` con dominios de búsqueda
   - 3 `website.snippet.filter` conectando filters + campos

2. **Modificado**: `__manifest__.py`
   - Agregada dependencia: `web_editor`
   - Agregado data file: `property_snippet_filters.xml`
   - **Comentado**: `options.js` (NO se necesita)

3. **Modificado**: `homepage_new.xml`
   - Agregado: `t-att-data-filter-id` a los 3 snippets
   - Agregado: `<div class="dynamic_snippet_template">`

4. **Simplificado**: `000.js`
   - Eliminados métodos personalizados de filtrado
   - Solo hereda `_getMainPageUrl()`

5. **Eliminado**: `models/website_snippet_filter.py`
   - Ya NO se necesita (usamos modelo nativo)

## ERROR ACTUAL

```
The following modules are needed by other modules but have not been defined:
- @web_editor/js/editor/snippets.options
- @website/snippets/s_dynamic_snippet_carousel/options
```

**CAUSA**: El módulo NO ha sido actualizado. Odoo todavía está intentando cargar el `options.js` antiguo.

**SOLUCIÓN**: Actualizar el módulo para que Odoo:
1. Cargue los nuevos filtros XML
2. Deje de intentar cargar `options.js`
3. Actualice el HTML del homepage

## PASOS PARA RESOLVER

### PASO 1: Actualizar el Módulo

**Opción A: Vía Interfaz Web (RECOMENDADO)**

1. Abre: **http://localhost:8069/web**
2. **Configuración** → **Activar el modo desarrollador**
3. **Apps** → Quitar filtro "Apps"
4. Busca: **"theme_bohio_real_estate"**
5. Click en **"Actualizar"** (Upgrade button)
6. Espera 30-60 segundos
7. Verifica que diga "Actualizado exitosamente"

**Opción B: Vía Comando (Si tienes permisos)**

```bash
"C:\Program Files\Odoo 18.0.20250830\python\python.exe" "C:\Program Files\Odoo 18.0.20250830\server\odoo-bin" -c "C:\Program Files\Odoo 18.0.20250830\server\odoo.conf" -d bohio_db -u theme_bohio_real_estate --stop-after-init
```

### PASO 2: Reiniciar Odoo (IMPORTANTE)

Después de actualizar, **reinicia el servicio de Odoo**:

1. Busca el proceso de Odoo en Task Manager
2. Cierra Odoo completamente
3. Reinicia el servicio

**O usa el comando:**
```bash
taskkill /F /IM odoo.exe
# Luego reinicia Odoo desde el servicio
```

### PASO 3: Limpiar Cache del Navegador (CRÍTICO)

**MUY IMPORTANTE - Los archivos JS están en cache:**

1. Presiona **Ctrl + Shift + Delete**
2. Selecciona **"Todo el tiempo"**
3. Marca TODAS las opciones:
   - ✅ Historial de navegación
   - ✅ Cookies y datos de sitios
   - ✅ Imágenes y archivos en caché
   - ✅ JavaScript en caché
   - ✅ CSS en caché
4. Click en **"Borrar datos"**

**Alternativa más agresiva:**

1. Cierra TODAS las pestañas de Odoo
2. Cierra el navegador completamente
3. Abre el navegador en modo incógnito
4. Ve a: http://localhost:8069

### PASO 4: Verificar en el Frontend

1. Ve a: **http://localhost:8069** (homepage)
2. Presiona **F12** → Pestaña **Console**
3. Recarga la página (**Ctrl + Shift + R** para forzar)

**Deberías ver:**
- ✅ 3 secciones con propiedades cargadas
- ✅ Arriendo: 12 propiedades
- ✅ Venta Usados: 12 propiedades
- ✅ Proyectos: 6 propiedades

**NO deberías ver:**
- ❌ "The following modules are needed..."
- ❌ "Cannot read properties of undefined"
- ❌ Errores de `options.js`

### PASO 5: Si Aún Hay Errores

#### Error: "Cannot find module ir.filters"

**Solución**: Verifica que el archivo XML se cargó:

```python
# Ejecuta en la consola Python de Odoo:
self.env['website.snippet.filter'].search([('name', 'ilike', 'Propiedades')])
```

Debería devolver 3 registros.

#### Error: "Template not found"

**Solución**: Verifica que los templates existen:

```python
self.env['ir.ui.view'].search([('key', 'ilike', 'dynamic_filter_template_property')])
```

Debería devolver 4 templates.

#### Error: Snippets no cargan propiedades

**Solución**: Verifica el HTML generado:

1. Inspecciona el elemento del snippet
2. Debe tener: `data-filter-id="[número]"`
3. Debe tener: `<div class="dynamic_snippet_template">...</div>`

Si NO tiene `data-filter-id`, el template NO se renderizó con QWeb.

## VERIFICACIÓN COMPLETA

### En el Backend:

```sql
-- Verifica los filtros creados
SELECT id, name, limit FROM website_snippet_filter
WHERE name LIKE '%Propiedades%';

-- Debería mostrar 3 registros:
-- 1. Propiedades en Arriendo (limit: 12)
-- 2. Propiedades Usadas en Venta (limit: 12)
-- 3. Proyectos Nuevos (limit: 6)
```

### En el Frontend (F12 → Console):

```javascript
// Verifica que el snippet está registrado
odoo.__DEBUG__.services['public.widget'].registry.dynamic_snippet_properties

// Debería devolver el widget registrado
```

### En el HTML (F12 → Elements):

```html
<!-- Busca este patrón en el homepage -->
<div class="s_dynamic_snippet_properties"
     data-filter-id="123"
     data-template-key="..."
     data-number-of-records="12">
    <div class="dynamic_snippet_template">
        <!-- Aquí deben aparecer las propiedades -->
    </div>
</div>
```

## TROUBLESHOOTING

### Problema 1: "Module already loaded"

**Causa**: El módulo está en cache
**Solución**:
```bash
# Borra el directorio de cache
rm -rf "C:\Program Files\Odoo 18.0.20250830\sessions\*"
```

### Problema 2: "Template rendering error"

**Causa**: El template QWeb tiene errores
**Solución**: Revisa el log de Odoo en busca de errores de QWeb

### Problema 3: "Filter not found"

**Causa**: Los registros XML no se crearon
**Solución**:
1. Verifica que `property_snippet_filters.xml` está en el manifest
2. Actualiza el módulo con `-u theme_bohio_real_estate`
3. Revisa el log para ver si hubo errores al crear los registros

### Problema 4: Propiedades no aparecen

**Causa**: El dominio del filtro no encuentra propiedades
**Solución**:
```python
# Verifica que hay propiedades que cumplan el dominio
self.env['product.template'].search([
    ('is_property', '=', True),
    ('active', '=', True),
    ('state', '=', 'free'),
    ('type_service', 'in', ['rent', 'sale_rent'])
])
```

## RESUMEN

**Pasos críticos:**
1. ✅ Actualizar módulo en Odoo
2. ✅ Reiniciar Odoo
3. ✅ Limpiar cache del navegador
4. ✅ Verificar en homepage

**Si sigues todos estos pasos, el error debe desaparecer.**

---

**Última actualización:** 2025-10-12
**Archivo de referencia:** [SOLUCION_CORRECTA_SNIPPETS_DINAMICOS.md](SOLUCION_CORRECTA_SNIPPETS_DINAMICOS.md)

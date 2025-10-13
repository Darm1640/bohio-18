# INSTRUCCIONES PARA ACTUALIZAR EL MÓDULO MANUALMENTE

## PROBLEMA ACTUAL

Los archivos del snippet dinámico de propiedades ya están creados y registrados en el manifest, PERO Odoo no los ha cargado aún porque el módulo no se ha actualizado.

No podemos actualizar por comando porque Windows no permite a Odoo escribir en `C:\Program Files\`.

## SOLUCIÓN: ACTUALIZAR VÍA WEB

### PASO 1: Activar Modo Desarrollador

1. Abre tu navegador
2. Ve a: **http://localhost:8069**
3. Inicia sesión como **admin**
4. Ve a **Configuración** (Settings) en el menú superior
5. Scroll hasta el final de la página
6. En la sección "Developer Tools", haz click en **"Activar el modo desarrollador"**

### PASO 2: Ir a Apps

1. En el menú principal, haz click en **"Apps"** (Aplicaciones)
2. En la barra de búsqueda, **quita el filtro "Apps"** (hay un botón X al lado)
3. Busca: **theme_bohio_real_estate**

### PASO 3: Actualizar el Módulo

1. Deberías ver el módulo "Theme Bohio Real Estate" en la lista
2. Haz click en el botón **"Actualizar"** (Upgrade) o el botón con el ícono de actualización
3. Espera 30-60 segundos mientras se actualiza
4. Debería aparecer un mensaje de "Módulo actualizado exitosamente"

### PASO 4: Limpiar Cache del Navegador

**MUY IMPORTANTE:** Odoo cachea los archivos JavaScript y CSS agresivamente.

1. Presiona **Ctrl + Shift + Delete**
2. Selecciona **"Todo el tiempo"** o **"Desde el principio"**
3. Marca:
   - ✅ Imágenes y archivos en caché
   - ✅ Archivos JavaScript en caché
   - ✅ CSS en caché
4. Haz click en **"Borrar datos"** o **"Clear data"**

### PASO 5: Forzar Recarga de Assets (Opcional pero Recomendado)

Si después de limpiar el cache aún no ves los cambios:

1. Ve a **Configuración → Técnico → Assets**
2. Busca: **web.assets_frontend**
3. Haz click en el registro
4. Haz click en el botón **"Invalidar cache"** o **"Regenerar"**

### PASO 6: Verificar en el Homepage

1. Abre una **nueva pestaña** del navegador
2. Ve a: **http://localhost:8069**
3. Deberías ver 3 secciones de propiedades:
   - **ARRIENDO** - Propiedades en arriendo/renta
   - **VENTA USADOS** - Propiedades de venta sin proyecto
   - **PROYECTOS** - Propiedades de venta con proyecto

### PASO 7: Verificar en la Consola JavaScript

1. Presiona **F12** para abrir las DevTools
2. Ve a la pestaña **Console**
3. **NO deberías ver** estos errores:
   - ❌ "Cannot read properties of undefined (reading 'querySelectorAll')"
   - ❌ "odoo.define is not a function"
   - ❌ "modules are needed but have not been defined"

## QUÉ ESPERAR DESPUÉS DE ACTUALIZAR

### ✅ FUNCIONANDO CORRECTAMENTE:

1. El homepage carga sin errores JavaScript
2. Las 3 secciones muestran propiedades filtradas por tipo:
   - Sección 1: Propiedades en **ARRIENDO** (type_service = rent o sale_rent)
   - Sección 2: Propiedades **USADAS** (sin project_worksite_id)
   - Sección 3: **PROYECTOS** (con project_worksite_id)
3. Cada tarjeta muestra:
   - Imagen de la propiedad
   - Precio
   - Ubicación (ciudad/barrio)
   - Características (habitaciones, baños, área)

### ❌ SI AÚN NO FUNCIONA:

Si después de seguir todos los pasos aún no ves las propiedades, verifica:

1. **¿Tienes propiedades creadas en la base de datos?**
   ```python
   # Ejecuta este script para verificar:
   python -c "
   import xmlrpc.client
   URL = 'http://localhost:8069'
   DB = 'bohio_db'
   USERNAME = 'admin'
   PASSWORD = 'admin'

   common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
   uid = common.authenticate(DB, USERNAME, PASSWORD, {})
   models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

   # Contar propiedades por tipo
   count_rent = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_count',
       [[('is_property', '=', True), ('type_service', 'in', ['rent', 'sale_rent'])]])

   count_sale_used = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_count',
       [[('is_property', '=', True), ('type_service', 'in', ['sale', 'sale_rent']), ('project_worksite_id', '=', False)]])

   count_projects = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_count',
       [[('is_property', '=', True), ('type_service', 'in', ['sale', 'sale_rent']), ('project_worksite_id', '!=', False)]])

   print(f'Arriendo: {count_rent}')
   print(f'Venta Usados: {count_sale_used}')
   print(f'Proyectos: {count_projects}')
   "
   ```

2. **¿El módulo website está funcionando?**
   - Verifica que puedas editar otras páginas del sitio web
   - Verifica que otros snippets estén funcionando

3. **¿Hay errores en el log de Odoo?**
   - Revisa el archivo de log de Odoo
   - Busca errores relacionados con `theme_bohio_real_estate`

## ARCHIVOS QUE SE CARGARÁN AL ACTUALIZAR

El módulo cargará estos nuevos archivos:

### Python Backend:
- `models/website_snippet_filter.py` - Lógica de filtrado

### XML Templates:
- `views/snippets/property_snippet_templates.xml` - 4 templates de renderizado
- `views/snippets/s_dynamic_snippet_properties.xml` - Definición del snippet

### JavaScript Frontend:
- `static/src/snippets/s_dynamic_snippet_properties/000.js` - Widget del snippet

### JavaScript Backend (Website Builder):
- `static/src/snippets/s_dynamic_snippet_properties/options.js` - Opciones del editor

### CSS:
- `static/src/css/property_snippets.css` - Estilos de las tarjetas

## RESUMEN DE CAMBIOS APLICADOS

### ✅ Archivos Creados: 7
1. `models/__init__.py`
2. `models/website_snippet_filter.py`
3. `views/snippets/property_snippet_templates.xml`
4. `views/snippets/s_dynamic_snippet_properties.xml`
5. `static/src/snippets/s_dynamic_snippet_properties/000.js`
6. `static/src/snippets/s_dynamic_snippet_properties/options.js`
7. `static/src/css/property_snippets.css`

### ✅ Archivos Modificados: 3
1. `__init__.py` - Importa modelos
2. `__manifest__.py` - Registra archivos y assets
3. `views/homepage_new.xml` - Usa snippets dinámicos

### ✅ Errores Corregidos: 3
1. PWA error (`pwa_fix.xml`)
2. JavaScript `odoo.define` error (movido a manifest)
3. `querySelectorAll` undefined (validaciones agregadas)

---

**IMPORTANTE:** Una vez actualizado el módulo, **DEBES limpiar el cache del navegador** o los cambios NO se verán.

# COMO ACTUALIZAR EL MÓDULO EN ODOO.COM

## El Problema
La homepage no muestra propiedades porque está cargando código viejo (antes del commit).
Los logs nuevos `[HOMEPAGE]` no aparecen en la consola.

## La Solución: Actualizar el Módulo Manualmente

### PASO 1: Activar Modo Desarrollador
1. Ve a: https://darm1640-bohio-18.odoo.com
2. Inicia sesión con: darm1640@hotmail.com
3. En la esquina superior derecha, click en tu nombre
4. Ve a "Preferencias" o "Settings"
5. Busca "Activar modo desarrollador" o "Activate Developer Mode"
6. Click en "Activar"

### PASO 2: Ir a Apps
1. En el menú principal, busca el ícono de cuadrícula (9 puntos)
2. Click en "Apps" o "Aplicaciones"
3. Verás un filtro que dice "Apps" en la barra de búsqueda
4. **IMPORTANTE:** Quita ese filtro para ver TODOS los módulos

### PASO 3: Buscar y Actualizar el Módulo
1. En la barra de búsqueda escribe: `theme_bohio`
2. Deberías ver: **Theme Bohio Real Estate**
3. Click en el módulo para abrirlo
4. Verás un botón que dice **"Actualizar"** o **"Update"**
5. Click en ese botón
6. Espera a que termine la actualización (puede tardar 30-60 segundos)

### PASO 4: Limpiar Caché del Navegador
1. Presiona: `Ctrl + Shift + Delete`
2. Selecciona:
   - Cookies
   - Archivos en caché
   - Imágenes en caché
3. Período: "Última hora" o "Todo"
4. Click en "Borrar datos"

### PASO 5: Cerrar TODO y Abrir Nueva Ventana
1. Cierra TODAS las pestañas de Odoo
2. Cierra el navegador completamente
3. Abre el navegador de nuevo
4. Ve a: https://darm1640-bohio-18.odoo.com/home

### PASO 6: Verificar en la Consola
1. Presiona `F12` para abrir la consola
2. Recarga la página con `Ctrl + F5` (forzar recarga)
3. Busca en la consola los mensajes:
   ```
   [HOMEPAGE] Iniciando carga de propiedades
   [HOMEPAGE] Cargando propiedades de ARRIENDO...
   [HOMEPAGE] ✅ X propiedades de arriendo cargadas
   ```

### PASO 7: Verificar Visualmente
Si todo funcionó, deberías ver:
- **Sección "Arriendo"**: 4 propiedades con tarjetas
- **Sección "Venta de inmuebles usados"**: 4 propiedades con tarjetas
- **Sección "Proyectos en venta"**: Puede estar vacía (0 proyectos por ahora)

---

## Si NO Funciona Después de Esto

### Opción A: Verificar que el módulo se actualizó
1. Ve a: Apps > Theme Bohio Real Estate
2. Revisa la fecha de "Última actualización"
3. Debería ser de hoy y hora reciente

### Opción B: Regenerar Assets
1. Modo desarrollador activo
2. Ve a: Configuración > Técnico > User Interface > Assets
3. O directamente: https://darm1640-bohio-18.odoo.com/web#menu_id=107&action=base.action_ui_view
4. En el menú superior: Bug icon > "Regenerate Assets"

### Opción C: Desinstalar y Reinstalar (ÚLTIMO RECURSO)
**ADVERTENCIA: Esto borrará configuraciones del módulo**
1. Apps > Theme Bohio Real Estate
2. Click en "Desinstalar"
3. Confirmar
4. Esperar a que termine
5. Buscar el módulo de nuevo
6. Click en "Instalar"

---

## Qué Cambios Esperar

### Antes (Lo que ves ahora):
- Secciones vacías con botón "Explora la categoría"
- Logs en consola: "BOHIO Loader: Script cargado"
- NO hay logs con `[HOMEPAGE]`

### Después (Lo que verás):
- Tarjetas de propiedades en cada sección
- Logs detallados con `[HOMEPAGE]`
- Imágenes de propiedades
- Información de precio, ubicación, etc.

---

## Contacto

Si después de seguir TODOS estos pasos aún no funciona:
1. Toma screenshot de la consola (F12)
2. Toma screenshot de la página
3. Envíame ambas imágenes

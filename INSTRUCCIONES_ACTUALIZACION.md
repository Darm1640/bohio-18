# INSTRUCCIONES PARA ACTUALIZAR MÓDULO EN ODOO.COM

## Paso 1: Acceder a Modo Desarrollador
1. Ve a: https://darm1640-bohio-18.odoo.com
2. En la barra superior, busca el ícono de "Ajustes/Settings" (engranaje)
3. Baja hasta el final y busca "Activar modo desarrollador"
   - O ve directamente a: https://darm1640-bohio-18.odoo.com/web?debug=1

## Paso 2: Actualizar Módulo desde Apps
1. Ve al menú "Apps" (Aplicaciones)
2. Quita el filtro "Apps" en la barra de búsqueda (para ver todos los módulos)
3. Busca "Theme Bohio Real Estate"
4. Click en el módulo
5. Click en "Actualizar" (Update)
   - Si no ves el botón, activa modo desarrollador primero

## Paso 3: Actualizar Assets (Importante)
Después de actualizar el módulo, necesitas limpiar el caché de assets:

1. Ve a: Configuración > Técnico > Assets
2. O directamente: https://darm1640-bohio-18.odoo.com/web#action=base.action_ui_view
3. En el menú superior: "Depurar" > "Regenerar Assets" (Regenerate Assets)
4. O ejecuta en la consola del navegador:
   ```javascript
   window.location.href = '/web/webclient/version_info?debug=assets'
   ```

## Paso 4: Forzar Recarga Completa
1. Cierra todas las pestañas de Odoo
2. Limpia caché del navegador (Ctrl + Shift + Delete)
3. Abre nueva pestaña
4. Ve a: https://darm1640-bohio-18.odoo.com/home

## Paso 5: Verificar en Consola
Deberías ver los nuevos logs:
- `[HOMEPAGE] Iniciando carga de propiedades`
- `[HOMEPAGE] Cargando propiedades de ARRIENDO...`
- `[HOMEPAGE] ✅ X propiedades de arriendo cargadas`

## Si aún no funciona:

### Opción A: Actualizar vía XML-RPC (Python)
Ejecutar este script para forzar actualización:

```python
import xmlrpc.client

url = 'https://darm1640-bohio-18.odoo.com'
db = 'darm1640-bohio-18'
username = 'darm1640@hotmail.com'
password = 'tE^9E6*9'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Actualizar módulo
models.execute_kw(db, uid, password, 'ir.module.module', 'button_immediate_upgrade', 
    [[models.execute_kw(db, uid, password, 'ir.module.module', 'search', 
        [[('name', '=', 'theme_bohio_real_estate')]])]])

print("Módulo actualizado")
```

### Opción B: Reinstalar Assets
En Odoo shell:
```bash
./odoo-bin shell -d darm1640-bohio-18
```

```python
env['ir.qweb'].clear_caches()
env['ir.ui.view'].clear_caches()
env['ir.asset'].sudo().search([]).unlink()
```


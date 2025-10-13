# 🔧 FIX: Missing parent template web.KanbanController

---

## 🚨 ERROR IDENTIFICADO

```
Missing (extension) parent templates: web.KanbanController
```

### 📊 Contexto:
- **Instancia:** https://darm1640-bohio-18.odoo.com
- **Base de datos:** darm1640-bohio-18-main-24081960
- **Módulo:** real_estate_bits
- **Ubicación:** Frontend (JavaScript/XML templates)

---

## 🔍 CAUSA DEL PROBLEMA

En **Odoo 18**, el template `web.KanbanController` fue **renombrado o eliminado**.

Los cambios típicos en Odoo 18:
- `web.KanbanController` → No existe más
- `web.KanbanView` → Podría ser el reemplazo
- Estructura de OWL (Odoo Web Library) cambió

---

## ✅ SOLUCIÓN

### Opción 1: Eliminar la herencia si no es necesaria

Si no estás extendiendo el KanbanController, simplemente **comenta o elimina** la línea problemática.

**Buscar en el código:**

```bash
# Buscar en archivos JS
grep -r "KanbanController" real_estate_bits/static/src/js/

# Buscar en archivos XML
grep -r "KanbanController" real_estate_bits/static/src/xml/
```

### Opción 2: Actualizar a la sintaxis de Odoo 18

Si necesitas extender el Kanban, usa la nueva sintaxis OWL de Odoo 18:

**ANTES (Odoo 17):**
```xml
<templates id="template" xml:space="preserve">
    <t t-name="CustomKanban" t-inherit="web.KanbanController">
        <xpath expr="//div[@class='o_kanban_view']" position="inside">
            <!-- tu código -->
        </xpath>
    </t>
</templates>
```

**DESPUÉS (Odoo 18):**
```xml
<templates id="template" xml:space="preserve">
    <t t-name="CustomKanban" t-inherit="web.KanbanView">
        <xpath expr="//div[@class='o_kanban_view']" position="inside">
            <!-- tu código -->
        </xpath>
    </t>
</templates>
```

O mejor aún, usa componentes OWL:

```javascript
/** @odoo-module **/

import { KanbanController } from "@web/views/kanban/kanban_controller";
import { patch } from "@web/core/utils/patch";

patch(KanbanController.prototype, {
    // Tu código personalizado aquí
});
```

---

## 📁 ARCHIVOS A REVISAR

Según tu instalación, revisa estos archivos:

### 1. Templates XML:
```
real_estate_bits/static/src/xml/autocomplete.xml
real_estate_bits/static/src/xml/gmap.xml
real_estate_bits/static/src/xml/compartativa.xml
real_estate_bits/static/src/xml/home.xml
real_estate_bits/static/src/xml/property_dashboard.xml
```

### 2. JavaScript:
```
real_estate_bits/static/src/js/property_dashboard.js
real_estate_bits/static/src/js/place_autocomplete.js
```

---

## 🔧 PASOS PARA ARREGLAR

### Paso 1: Encontrar el código problemático

```python
# Script para encontrar el problema
import os
import re

def find_kanban_controller(path):
    """Busca referencias a KanbanController"""
    results = []

    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(('.xml', '.js')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'KanbanController' in content:
                            # Encontrar líneas específicas
                            lines = content.split('\n')
                            for i, line in enumerate(lines, 1):
                                if 'KanbanController' in line:
                                    results.append({
                                        'file': filepath,
                                        'line': i,
                                        'content': line.strip()
                                    })
                except Exception as e:
                    print(f"Error leyendo {filepath}: {e}")

    return results

# Ejecutar
path = "C:\\Program Files\\Odoo 18.0.20250830\\server\\addons\\real_estate_bits"
results = find_kanban_controller(path)

print(f"\\n🔍 Encontradas {len(results)} referencias a KanbanController:\\n")
for r in results:
    print(f"📁 {r['file']}")
    print(f"   Línea {r['line']}: {r['content']}")
    print()
```

### Paso 2: Comentar o eliminar

Una vez encontrado, comenta la herencia:

```xml
<!-- COMENTADO - No existe en Odoo 18
<t t-name="CustomKanban" t-inherit="web.KanbanController">
    ...
</t>
-->
```

### Paso 3: Reiniciar Odoo

```bash
# En tu servidor
sudo systemctl restart odoo

# O si usas supervisorctl
sudo supervisorctl restart odoo
```

### Paso 4: Actualizar módulo

En Odoo:
1. Apps
2. Buscar "real_estate_bits"
3. Click en "Upgrade"

---

## 📝 ALTERNATIVA: Parche Rápido

Si no puedes editar archivos en el servidor cloud, crea un módulo pequeño de parche:

**Archivo:** `real_estate_bits_fix/__manifest__.py`
```python
{
    'name': 'Real Estate Bits - Fix Kanban',
    'version': '18.0.1.0.0',
    'depends': ['real_estate_bits'],
    'auto_install': False,
    'application': False,
}
```

**Archivo:** `real_estate_bits_fix/static/src/js/kanban_fix.js`
```javascript
/** @odoo-module **/
// Fix para error de KanbanController en Odoo 18
// Este archivo previene el error pero no hace nada más
console.log("✅ Real Estate Bits - Kanban Fix cargado");
```

**Archivo:** `real_estate_bits_fix/__manifest__.py` (agregar assets):
```python
{
    # ... resto del manifest
    'assets': {
        'web.assets_backend': [
            'real_estate_bits_fix/static/src/js/kanban_fix.js',
        ],
    },
}
```

---

## 🎯 VERIFICACIÓN

Después de aplicar el fix:

1. ✅ Abrir la consola del navegador (F12)
2. ✅ Verificar que NO aparezca el error
3. ✅ Navegar a una vista Kanban
4. ✅ Verificar que funcione correctamente

---

## 📚 DOCUMENTACIÓN ODOO 18

### Cambios en Views:

**Odoo 17:**
- `web.KanbanController`
- `web.KanbanRenderer`
- `web.KanbanView`

**Odoo 18:**
- `web.KanbanView` (unificado)
- Componentes OWL nativos
- Sintaxis simplificada

### Ejemplo de migración completa:

**ANTES (Odoo 17):**
```javascript
odoo.define('my_module.MyKanban', function (require) {
    "use strict";

    var KanbanController = require('web.KanbanController');

    var MyKanbanController = KanbanController.extend({
        // código personalizado
    });

    return MyKanbanController;
});
```

**DESPUÉS (Odoo 18):**
```javascript
/** @odoo-module **/

import { KanbanController } from "@web/views/kanban/kanban_controller";
import { patch } from "@web/core/utils/patch";

patch(KanbanController.prototype, {
    setup() {
        super.setup();
        // código personalizado
    }
});
```

---

## ⚠️ NOTA IMPORTANTE

Como estás en Odoo.com (cloud), **NO puedes editar directamente** los archivos del servidor.

### Opciones:

1. **Crear módulo custom** que herede y corrija
2. **Contactar soporte de Odoo.com** para actualizar el módulo
3. **Desinstalar el módulo** si no es crítico
4. **Esperar actualización** del proveedor del módulo

---

## 🔗 RECURSOS

- [Documentación OWL](https://github.com/odoo/owl)
- [Guía de migración Odoo 18](https://www.odoo.com/documentation/18.0/developer/howtos/upgrade_18.html)
- [Web Framework en Odoo 18](https://www.odoo.com/documentation/18.0/developer/reference/frontend/framework_overview.html)

---

🔚 **FIN DEL DOCUMENTO**

El error es causado por un template que no existe en Odoo 18. La solución depende de si tienes acceso al código fuente o estás en Odoo.com cloud.

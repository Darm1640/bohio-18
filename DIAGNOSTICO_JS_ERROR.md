# 🔍 DIAGNÓSTICO: Error odoo.define is not a function

## 🐛 ERROR

```
web.assets_web.min.js:3 Uncaught TypeError: odoo.define is not a function
```

---

## 🎯 CAUSAS POSIBLES

Este error ocurre cuando un archivo JavaScript usa **sintaxis antigua de Odoo** (`odoo.define`) en lugar de la **sintaxis moderna de Odoo 18** (`@odoo-module`).

### **Archivos que PUEDEN causar este error:**

1. Archivos JavaScript antiguos que no se han actualizado
2. Módulos de terceros no compatibles con Odoo 18
3. Código personalizado con sintaxis obsoleta

---

## 🔎 CÓMO IDENTIFICAR EL ARCHIVO PROBLEMÁTICO

### **Opción 1: Ver el error completo en consola**

1. Abrir consola del navegador (F12)
2. Click en el error para expandir
3. Buscar el **stack trace** que muestra qué archivo lo causa
4. Anotar el nombre del archivo

---

### **Opción 2: Buscar archivos con odoo.define**

Buscar en tu proyecto archivos que usen la sintaxis antigua:

```bash
cd theme_bohio_real_estate
grep -r "odoo.define" static/src/
```

**Si encuentra archivos:**
- Esos archivos necesitan ser actualizados a sintaxis Odoo 18

---

### **Opción 3: Revisar archivos JS del proyecto**

```bash
# Listar todos los JS en el proyecto
find theme_bohio_real_estate/static/src/ -name "*.js" -type f
```

Revisar cada uno para verificar que use:
```javascript
/** @odoo-module **/
import ...
```

Y NO:
```javascript
odoo.define('nombre_modulo', function (require) {
    ...
});
```

---

## ✅ ARCHIVOS QUE YA ESTÁN CORRECTOS

Los siguientes archivos **YA usan sintaxis correcta de Odoo 18**:

✅ **theme_bohio_real_estate/static/src/snippets/s_dynamic_snippet_properties/000.js**
```javascript
/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import DynamicSnippetCarousel from "@website/snippets/s_dynamic_snippet_carousel/000";
```

✅ **theme_bohio_real_estate/static/src/snippets/s_dynamic_snippet_properties/options.js**
```javascript
/** @odoo-module **/
import options from "@web_editor/js/editor/snippets.options";
import s_dynamic_snippet_carousel_options from "@website/snippets/s_dynamic_snippet_carousel/options";
```

---

## 🔧 SOLUCIÓN

### **Si el error viene de archivos de theme_bohio_real_estate:**

#### **1. Identificar archivo problemático**

```bash
cd theme_bohio_real_estate/static/src/js/
ls -la
# Ver cada archivo .js
```

#### **2. Convertir de sintaxis antigua a moderna**

**ANTES (Odoo 17 y anteriores):**
```javascript
odoo.define('mi_modulo', function (require) {
    "use strict";

    var publicWidget = require('web.public.widget');

    var MiWidget = publicWidget.Widget.extend({
        selector: '.mi_selector',
        // ...
    });

    publicWidget.registry.mi_widget = MiWidget;

    return MiWidget;
});
```

**AHORA (Odoo 18):**
```javascript
/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

const MiWidget = publicWidget.Widget.extend({
    selector: '.mi_selector',
    // ...
});

publicWidget.registry.mi_widget = MiWidget;

export default MiWidget;
```

---

### **Si el error viene de otro módulo instalado:**

#### **1. Verificar módulos instalados**

```
Apps → Remover filtro "Apps"
Buscar módulos de terceros
Verificar si son compatibles con Odoo 18
```

#### **2. Actualizar o deshabilitar módulos problemáticos**

```
Apps → Buscar módulo → Desinstalar
```

O contactar al proveedor del módulo para obtener versión compatible con Odoo 18.

---

## 🚨 SI EL ERROR PERSISTE

### **Desactivar temporalmente JavaScript problemático**

Si el error viene de un archivo específico y no lo necesitas inmediatamente:

```xml
<!-- En __manifest__.py, comentar el archivo JS: -->
'assets': {
    'web.assets_frontend': [
        # 'theme_bohio_real_estate/static/src/js/archivo_problematico.js',  # COMENTADO
    ],
},
```

---

## 📝 PASOS RECOMENDADOS

1. **Ver el error completo en consola** (F12)
2. **Identificar qué archivo lo causa**
3. **Si es de theme_bohio_real_estate:** Actualizar sintaxis
4. **Si es de otro módulo:** Actualizar o deshabilitar
5. **Actualizar módulo:** Apps → theme_bohio_real_estate → Upgrade
6. **Limpiar cache:** Ctrl+Shift+Delete → Vaciar cache
7. **Refrescar:** Ctrl+F5

---

## 📊 ARCHIVOS JS EN theme_bohio_real_estate

Para listar todos:

```bash
find theme_bohio_real_estate/static/src/ -name "*.js" -type f
```

Revisar cada uno y asegurarse que:
- ✅ Tiene `/** @odoo-module **/` al inicio
- ✅ Usa `import` en lugar de `require`
- ✅ Usa `export default` en lugar de `return`
- ❌ NO tiene `odoo.define`

---

## 🆘 AYUDA ADICIONAL

Si el error persiste después de todo esto, comparte:

1. **Stack trace completo del error** (desde consola F12)
2. **Lista de archivos JS** del proyecto
3. **Módulos instalados** (especialmente de terceros)

Y te ayudaré a identificar el archivo específico que causa el problema.

---

**Última actualización:** 2025-10-12
**Nota:** Los snippets de propiedades **NO son la causa** de este error.

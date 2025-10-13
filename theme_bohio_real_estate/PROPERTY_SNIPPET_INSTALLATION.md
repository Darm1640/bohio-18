# 🚀 INSTALACIÓN: Property Dynamic Snippet

## ✅ ARCHIVOS CREADOS

```
theme_bohio_real_estate/
├── models/
│   ├── __init__.py                             ✅ NUEVO
│   └── website_snippet_filter.py               ✅ NUEVO
├── views/snippets/
│   ├── property_snippet_templates.xml          ✅ NUEVO (4 plantillas)
│   ├── s_dynamic_snippet_properties.xml        ✅ NUEVO (opciones)
│   └── property_carousels_dynamic_example.xml  ✅ NUEVO (ejemplos)
├── static/src/
│   ├── css/
│   │   └── property_snippets.css               ✅ NUEVO
│   └── snippets/s_dynamic_snippet_properties/
│       ├── 000.js                              ✅ NUEVO
│       └── options.js                          ✅ NUEVO
├── __init__.py                                 ✏️ MODIFICADO
├── __manifest__.py                             ✏️ MODIFICADO
├── PROPERTY_SNIPPET_GUIDE.md                   📖 DOCUMENTACIÓN
└── PROPERTY_SNIPPET_INSTALLATION.md            📖 ESTE ARCHIVO
```

---

## 📋 PASO A PASO

### **PASO 1: Verificar Archivos**

Asegúrate de que todos los archivos nuevos existen:

```bash
# Desde el directorio bohio-18/
ls -la theme_bohio_real_estate/models/
ls -la theme_bohio_real_estate/views/snippets/
ls -la theme_bohio_real_estate/static/src/css/property_snippets.css
ls -la theme_bohio_real_estate/static/src/snippets/s_dynamic_snippet_properties/
```

---

### **PASO 2: Actualizar el Módulo**

```bash
# Opción A: Desde línea de comandos
"C:\Program Files\Odoo 18.0.20250830\python\python.exe" \
  "C:\Program Files\Odoo 18.0.20250830\server\odoo-bin" \
  -c "C:\Program Files\Odoo 18.0.20250830\server\odoo.conf" \
  -d bohio_db \
  -u theme_bohio_real_estate \
  --stop-after-init

# Opción B: Desde interfaz de Odoo
# Apps → theme_bohio_real_estate → Upgrade
```

---

### **PASO 3: Verificar Instalación**

#### **3.1 Verificar Modelo Python**

```bash
# En shell de Odoo
"C:\Program Files\Odoo 18.0.20250830\python\python.exe" -c "
from odoo import SUPERUSER_ID
import odoo

registry = odoo.registry('bohio_db')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, SUPERUSER_ID, {})

    # Verificar que el modelo se cargó
    snippet_filter = env['website.snippet.filter']
    print('✅ Modelo website.snippet.filter cargado correctamente')

    # Verificar método custom
    if hasattr(snippet_filter, '_get_properties'):
        print('✅ Método _get_properties() existe')
    else:
        print('❌ Método _get_properties() NO existe')
"
```

#### **3.2 Verificar Templates**

```bash
# Buscar templates en la base de datos
"C:\Program Files\Odoo 18.0.20250830\python\python.exe" -c "
from odoo import SUPERUSER_ID
import odoo

registry = odoo.registry('bohio_db')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, SUPERUSER_ID, {})

    templates = [
        'dynamic_filter_template_property_card',
        'dynamic_filter_template_property_banner',
        'dynamic_filter_template_property_compact',
        'dynamic_filter_template_property_list',
        's_dynamic_snippet_properties',
    ]

    for template in templates:
        exists = env['ir.ui.view'].search([
            ('key', '=', f'theme_bohio_real_estate.{template}')
        ])
        if exists:
            print(f'✅ Template {template} existe')
        else:
            print(f'❌ Template {template} NO existe')
"
```

#### **3.3 Verificar Assets JavaScript**

Abrir en navegador:
```
http://localhost:8069/web/assets/debug-assets/web.assets_frontend.js
```

Buscar (Ctrl+F):
- `DynamicSnippetProperties`
- `s_dynamic_snippet_properties`

Si aparecen = ✅ JavaScript cargado correctamente

---

### **PASO 4: Probar en Website Builder**

1. **Abrir Website Builder:**
   ```
   http://localhost:8069/website
   → Click "Editar"
   ```

2. **Buscar el Snippet:**
   - Panel izquierdo → Tab "Bloques"
   - Buscar "Properties" o "Propiedades"
   - Debería aparecer el nuevo snippet

3. **Arrastrar a la Página:**
   - Arrastrar "Properties" a la página
   - Verificar que aparece

4. **Configurar Opciones:**
   - Click en el snippet
   - Panel derecho → Ver opciones:
     - ✅ Tipo de Servicio
     - ✅ Tipo de Propiedad
     - ✅ Ciudad
     - ✅ Barrio/Región
     - ✅ Rangos de precio
     - ✅ Características mínimas

---

### **PASO 5: Probar Carga de Propiedades**

#### **5.1 Verificar que existen propiedades**

```bash
"C:\Program Files\Odoo 18.0.20250830\python\python.exe" -c "
from odoo import SUPERUSER_ID
import odoo

registry = odoo.registry('bohio_db')
with registry.cursor() as cr:
    env = odoo.api.Environment(cr, SUPERUSER_ID, {})

    # Contar propiedades
    total = env['product.template'].search_count([
        ('is_property', '=', True),
        ('active', '=', True),
        ('state', '=', 'free')
    ])
    print(f'Total propiedades: {total}')

    # Por tipo de servicio
    rent = env['product.template'].search_count([
        ('is_property', '=', True),
        ('active', '=', True),
        ('state', '=', 'free'),
        ('type_service', 'in', ['rent', 'sale_rent'])
    ])
    print(f'En arriendo: {rent}')

    sale = env['product.template'].search_count([
        ('is_property', '=', True),
        ('active', '=', True),
        ('state', '=', 'free'),
        ('type_service', 'in', ['sale', 'sale_rent']),
        ('project_worksite_id', '=', False)
    ])
    print(f'Venta usadas: {sale}')

    projects = env['product.template'].search_count([
        ('is_property', '=', True),
        ('active', '=', True),
        ('state', '=', 'free'),
        ('type_service', 'in', ['sale', 'sale_rent']),
        ('project_worksite_id', '!=', False)
    ])
    print(f'Proyectos: {projects}')
"
```

#### **5.2 Probar snippet en página**

Crear una página de prueba:

```xml
<template id="test_snippet_page" name="Test Snippet">
    <t t-call="website.layout">
        <div id="wrap" class="container py-5">
            <h1>Test Property Snippet</h1>

            <h2>Arriendo</h2>
            <div class="s_dynamic_snippet_properties"
                 data-type-service="rent"
                 data-limit="4">
            </div>

            <h2 class="mt-5">Venta</h2>
            <div class="s_dynamic_snippet_properties"
                 data-type-service="sale_used"
                 data-limit="4">
            </div>
        </div>
    </t>
</template>
```

---

## 🔧 TROUBLESHOOTING

### ❌ Error: "Module has no attribute '_get_properties'"

**Causa:** El modelo Python no se cargó correctamente

**Solución:**
```bash
# 1. Verificar que models/__init__.py existe
cat theme_bohio_real_estate/models/__init__.py

# 2. Verificar que __init__.py principal importa models
cat theme_bohio_real_estate/__init__.py

# 3. Actualizar con --init
python odoo-bin -u theme_bohio_real_estate -d bohio_db --init=theme_bohio_real_estate
```

---

### ❌ Error: "Template not found"

**Causa:** Los templates XML no se cargaron

**Solución:**
```bash
# 1. Verificar que están en __manifest__.py
grep "property_snippet_templates.xml" theme_bohio_real_estate/__manifest__.py

# 2. Actualizar módulo
python odoo-bin -u theme_bohio_real_estate -d bohio_db --stop-after-init

# 3. Si persiste, eliminar cache
rm -rf ~/.local/share/Odoo/sessions/*
```

---

### ❌ Snippet no aparece en Website Builder

**Causa:** Assets JavaScript no se cargaron

**Solución:**
```bash
# 1. Limpiar assets
# En Odoo: Settings → Technical → Assets
# Buscar "s_dynamic_snippet_properties" y eliminar

# 2. Actualizar módulo
python odoo-bin -u theme_bohio_real_estate -d bohio_db --stop-after-init

# 3. Limpiar cache del navegador
# Chrome: Ctrl+Shift+Delete → Clear cache
```

---

### ❌ Las propiedades no se muestran

**Causa:** Dominio de búsqueda muy restrictivo o sin propiedades

**Solución:**
```python
# Verificar propiedades en shell de Odoo
env['product.template'].search([
    ('is_property', '=', True),
    ('active', '=', True),
    ('state', '=', 'free')
], limit=5)

# Si no hay resultados, ajustar el dominio o crear propiedades de prueba
```

---

### ❌ Error: "QWebException"

**Causa:** Error de sintaxis en template XML

**Solución:**
```bash
# Verificar sintaxis XML
xmllint --noout theme_bohio_real_estate/views/snippets/*.xml

# Ver logs detallados
tail -f /var/log/odoo/odoo-server.log
```

---

## ✨ SIGUIENTE: MIGRAR CARRUSELES EXISTENTES

Una vez que el snippet funcione correctamente, puedes migrar los carruseles existentes:

**Ver:** `property_carousels_dynamic_example.xml` para ejemplos completos

**Pasos resumidos:**

1. **Backup de carruseles actuales**
2. **Reemplazar en homepage_new.xml:**
   ```xml
   <!-- ANTES -->
   <t t-call="theme_bohio_real_estate.carousel_rent_section"/>

   <!-- AHORA -->
   <t t-call="theme_bohio_real_estate.carousel_rent_section_dynamic"/>
   ```
3. **Actualizar módulo**
4. **Verificar que funciona**
5. **(Opcional) Eliminar JS y CSS antiguos**

---

## 📊 CHECKLIST DE INSTALACIÓN

```
✅ Archivos creados en theme_bohio_real_estate/
✅ __init__.py actualizado (imports models)
✅ __manifest__.py actualizado (data files)
✅ Módulo actualizado en Odoo
✅ Modelo Python cargado (_get_properties existe)
✅ Templates XML cargados (4 plantillas)
✅ JavaScript assets cargados (DynamicSnippetProperties)
✅ CSS assets cargados (property_snippets.css)
✅ Snippet aparece en Website Builder
✅ Opciones de filtrado visibles en panel
✅ Propiedades se cargan correctamente
✅ Plantillas renderizan correctamente
✅ Sin errores en consola del navegador
✅ Sin errores en logs de Odoo
```

---

## 🎓 PRÓXIMOS PASOS

1. ✅ **Instalación completa**
2. 📖 **Leer:** [PROPERTY_SNIPPET_GUIDE.md](PROPERTY_SNIPPET_GUIDE.md)
3. 🔄 **Migrar carruseles existentes** (opcional)
4. 🎨 **Crear plantillas personalizadas** (opcional)
5. 🚀 **Usar en producción**

---

## 📞 SOPORTE

Si encuentras problemas:

1. **Revisar logs:**
   ```bash
   tail -f /var/log/odoo/odoo-server.log
   ```

2. **Consola del navegador:**
   - F12 → Console tab
   - Buscar errores relacionados con "snippet" o "properties"

3. **Verificar permisos:**
   - El usuario debe tener acceso a `website.snippet.filter`
   - Verificar grupos de seguridad

---

**Última actualización:** 2025-10-12
**Versión:** 1.0
**Autor:** BOHIO Real Estate Development Team

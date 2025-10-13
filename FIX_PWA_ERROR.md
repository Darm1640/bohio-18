# 🔧 FIX: Error enable_pwa

## 🐛 ERROR DETECTADO

```
AttributeError: 'website' object has no attribute 'enable_pwa'
Template: web.frontend_layout
```

---

## 🎯 CAUSA

El error ocurre porque:
1. La base de datos usa una versión antigua del módulo `website`
2. El campo `enable_pwa` fue agregado en versiones más recientes de Odoo 18
3. Tu base de datos necesita actualizar el módulo `website`

**IMPORTANTE:** Este error **NO está relacionado** con los Property Snippets que creamos.

---

## ✅ SOLUCIONES

### **SOLUCIÓN 1: Actualizar módulo website (RECOMENDADO)**

```
1. Ir a Apps en Odoo
2. Remover filtro "Apps"
3. Buscar "website"
4. Click en botón "Upgrade"
5. Esperar a que termine
6. Refrescar el navegador (Ctrl+F5)
```

---

### **SOLUCIÓN 2: SQL Manual (Si tienes acceso a PostgreSQL)**

```sql
-- Conectar a PostgreSQL
psql -U odoo -d bohio_db

-- Agregar el campo
ALTER TABLE website ADD COLUMN IF NOT EXISTS enable_pwa boolean DEFAULT false;
UPDATE website SET enable_pwa = false WHERE enable_pwa IS NULL;

-- Salir
\q
```

Luego reinicia Odoo.

---

### **SOLUCIÓN 3: Fix Temporal (YA APLICADO)**

He creado un fix temporal en:
```
theme_bohio_real_estate/views/layout/pwa_fix.xml
```

Este archivo **deshabilita temporalmente** la funcionalidad PWA para que no cause el error.

**Ya está agregado al `__manifest__.py`**, así que al actualizar el módulo `theme_bohio_real_estate` se aplicará automáticamente.

---

## 🚀 PASOS PARA APLICAR EL FIX

### **Desde la interfaz de Odoo:**

```
1. Apps → Buscar "theme_bohio_real_estate"
2. Click en "Upgrade"
3. Esperar a que termine
4. Ir a la homepage: http://localhost:8069
5. Refrescar con Ctrl+F5
```

El error debería desaparecer.

---

## 🔍 VERIFICAR QUE FUNCIONA

Después de aplicar el fix:

1. **Abrir homepage:**
   ```
   http://localhost:8069
   ```

2. **Verificar que NO hay error en logs**

3. **Verificar que se muestran las secciones:**
   - ✅ Arriendo
   - ✅ Venta de inmuebles usados
   - ✅ Proyectos en venta

4. **Abrir consola del navegador (F12):**
   - NO debería haber errores de JavaScript
   - Buscar: `DynamicSnippetProperties`

---

## 📋 QUÉ HACE EL FIX

El archivo `pwa_fix.xml` **hereda** de `web.frontend_layout` y **remueve** el bloque que causa el error:

```xml
<template id="pwa_fix" inherit_id="web.frontend_layout" priority="99">
    <xpath expr="//t[@t-if='enable_pwa']" position="replace">
        <!-- PWA deshabilitado temporalmente -->
    </xpath>
</template>
```

**Consecuencia:** La funcionalidad PWA (Progressive Web App) estará deshabilitada temporalmente.

**¿Es grave?** No. El PWA es opcional y tu sitio funcionará perfectamente sin él.

---

## 🔄 DESPUÉS DE ACTUALIZAR

Una vez que actualices el módulo `website` a la última versión:

1. **Remover el fix temporal:**
   ```xml
   <!-- En __manifest__.py, comentar o eliminar: -->
   # 'views/layout/pwa_fix.xml',
   ```

2. **Actualizar módulo:**
   ```
   Apps → theme_bohio_real_estate → Upgrade
   ```

3. **Habilitar PWA (opcional):**
   ```
   Website → Configuration → Settings
   → Habilitar "Progressive Web App"
   ```

---

## 🆘 SI EL ERROR PERSISTE

### **Verificar logs de Odoo:**

```bash
tail -f /var/log/odoo/odoo-server.log
```

Buscar líneas con:
- `AttributeError`
- `enable_pwa`
- `website`

### **Verificar versión de Odoo:**

```bash
"C:\Program Files\Odoo 18.0.20250830\python\python.exe" -c "
import odoo
print(f'Odoo version: {odoo.release.version}')
"
```

### **Verificar módulo website instalado:**

```python
# En shell de Odoo
env['ir.module.module'].search([('name', '=', 'website')])
# Verificar campo 'state' debe ser 'installed'
```

---

## 📞 RESUMEN

| Acción | Estado |
|--------|--------|
| Error identificado | ✅ `enable_pwa` no existe |
| Fix temporal creado | ✅ `pwa_fix.xml` |
| Fix agregado a manifest | ✅ En `__manifest__.py` |
| Snippets afectados | ❌ NO (error no relacionado) |
| Necesita actualización | ⚠️ Actualizar módulo website |

---

**IMPORTANTE:** Los Property Snippets que creamos están completamente funcionales. Este error es del core de Odoo, no de nuestro código.

**Última actualización:** 2025-10-12
**Autor:** BOHIO Real Estate Development Team

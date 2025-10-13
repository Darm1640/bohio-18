# INSTRUCCIONES: Reiniciar Odoo para Aplicar Cambios

## Fecha: 2025-10-12
## Motivo: Aplicar fix del modal de reporte (error QWeb corregido)

---

## PROBLEMA ACTUAL

El modal de reporte NO se muestra porque:
1. Corregimos el error de sintaxis QWeb en `property_detail_template.xml` (líneas 424 y 500)
2. Cambiamos `t-att-value` con `str()` → `t-attf-value` con `#{}`
3. **PERO** el servidor de Odoo NO ha recargado el template XML corregido

---

## SOLUCIÓN: Reiniciar Servicio de Odoo

### OPCIÓN A: Desde Servicios de Windows (RECOMENDADO)

1. Presionar `Win + R`
2. Escribir: `services.msc`
3. Presionar `Enter`
4. En la lista, buscar: **"Odoo"** o **"odoo-server-18.0"**
5. Click derecho sobre el servicio
6. Seleccionar: **"Reiniciar"**
7. Esperar 10-15 segundos hasta que el estado sea **"En ejecución"**
8. Ir al navegador
9. Presionar `Ctrl + Shift + R` (hard refresh)
10. Probar abrir el modal de reporte

### OPCIÓN B: Desde Terminal (Como Administrador)

```bash
# Detener servicio
net stop odoo-server-18.0

# Esperar 5 segundos

# Iniciar servicio
net start odoo-server-18.0
```

### OPCIÓN C: Actualizar Módulo Manualmente

```bash
# Abrir terminal como Administrador
# Ir a la carpeta de Odoo
cd "C:\Program Files\Odoo 18.0.20250830\server"

# Actualizar el módulo específico
..\python\python.exe odoo-bin -c odoo.conf -d bohio_db -u theme_bohio_real_estate --stop-after-init
```

---

## VERIFICACIÓN DESPUÉS DE REINICIAR

### 1. En la consola del navegador (F12):

```javascript
// Verificar que el modal existe ahora
console.log('Modal reportModal:', document.getElementById('reportModal'));

// Contar todos los modales
const modales = document.querySelectorAll('.modal');
console.log('Total modales:', modales.length);  // Debe ser 4
modales.forEach(m => console.log(' -', m.id));

// Resultado esperado:
//  - galleryModal
//  - imageZoomModal
//  - shareModal
//  - reportModal  <-- ESTE DEBE APARECER AHORA
```

### 2. Probar abrir el modal:

```javascript
// Intentar abrir el modal
openReportModal();

// Debe mostrar en consola:
// 🚩 Abriendo modal de reporte
// Y el modal debe abrirse en pantalla
```

### 3. Ver código fuente HTML:

1. En la página de la propiedad: `http://localhost:8069/property/15360`
2. Presionar `Ctrl + U` (ver código fuente)
3. Buscar (Ctrl + F): `reportModal`
4. Debe encontrar el elemento `<div id="reportModal" class="modal fade">`

---

## SI EL MODAL SIGUE SIN APARECER

### Verificar que el archivo XML tiene los cambios:

1. Abrir: `c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\theme_bohio_real_estate\views\property_detail_template.xml`

2. **Buscar línea 424** - Debe decir:
```xml
<input type="text" class="form-control" id="propertyShareLink" readonly="readonly"
       t-attf-value="#{request.httprequest.url_root.rstrip('/')}/property/#{property.id}"/>
```

**NO debe decir**:
```xml
t-att-value="... + str(property.id)"/>  <!-- INCORRECTO -->
```

3. **Buscar línea 500** - Debe decir:
```xml
<input type="hidden" name="property_url"
       t-attf-value="#{request.httprequest.url_root.rstrip('/')}/property/#{property.id}"/>
```

**NO debe decir**:
```xml
t-att-value="... + str(property.id)"/>  <!-- INCORRECTO -->
```

### Si los cambios NO están en el archivo:

Significa que el archivo no se guardó correctamente. Volver a aplicar los cambios:

**Línea 424** - REEMPLAZAR:
```xml
<!-- BUSCAR ESTO (INCORRECTO): -->
<input type="text" class="form-control" id="propertyShareLink" readonly="readonly"
       t-att-value="request.httprequest.url_root.rstrip('/') + '/property/' + str(property.id)"/>

<!-- POR ESTO (CORRECTO): -->
<input type="text" class="form-control" id="propertyShareLink" readonly="readonly"
       t-attf-value="#{request.httprequest.url_root.rstrip('/')}/property/#{property.id}"/>
```

**Línea 500** - REEMPLAZAR:
```xml
<!-- BUSCAR ESTO (INCORRECTO): -->
<input type="hidden" name="property_url"
       t-att-value="request.httprequest.url_root.rstrip('/') + '/property/' + str(property.id)"/>

<!-- POR ESTO (CORRECTO): -->
<input type="hidden" name="property_url"
       t-attf-value="#{request.httprequest.url_root.rstrip('/')}/property/#{property.id}"/>
```

Después de corregir, reiniciar el servicio de Odoo nuevamente.

---

## RESUMEN DE CAMBIOS APLICADOS

| Archivo | Línea | Cambio | Estado |
|---------|-------|--------|--------|
| property_detail_template.xml | 424 | `t-att` → `t-attf` | ✅ Corregido |
| property_detail_template.xml | 500 | `t-att` → `t-attf` | ✅ Corregido |
| property_detail_gallery.js | 125-131 | Template literals sin comillas simples | ✅ Corregido |
| property_shop.js | 109-113 | Agregados filtros de ubicación | ✅ Corregido |

---

## PRÓXIMOS PASOS

1. ✅ **Reiniciar servicio de Odoo** (Opción A, B o C)
2. ✅ **Hard refresh en navegador** (Ctrl + Shift + R)
3. ✅ **Verificar en consola** que el modal existe
4. ✅ **Probar abrir modal** de reporte
5. ✅ **Confirmar que funciona** y reportar resultado

---

## CONTACTO DE EMERGENCIA

Si después de reiniciar el servicio el modal SIGUE sin aparecer:

1. Verificar logs de Odoo: `C:\Program Files\Odoo 18.0.20250830\server\odoo.log`
2. Buscar errores relacionados con `theme_bohio_real_estate` o `property_detail_template`
3. Verificar que el módulo está instalado: Ir a Odoo → Aplicaciones → Buscar "theme_bohio_real_estate"
4. Ejecutar script de diagnóstico completo (crear si es necesario)

---

**Estado**: ⚠️ Pendiente de reiniciar servicio de Odoo

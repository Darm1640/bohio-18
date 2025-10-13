# DIAGNÓSTICO: Modal de Reporte No Encontrado

## Fecha: 2025-10-12
## Problema: `document.getElementById('reportModal')` retorna `null`

---

## 🔍 ANÁLISIS INICIAL

### Ubicación del Modal en el XML
**Archivo**: `property_detail_template.xml`
**Líneas**: 479-580

```xml
<!-- Line 479: Comentario -->
<!-- Line 480-580: Modal HTML -->
<div class="modal fade" id="reportModal" tabindex="-1" aria-hidden="true">
    ...
</div>
```

### Estructura del Template:
```
Line 4:   <t t-call="website.layout">
Line 5:       <div id="wrap">
Line 300:     </div>  <!-- Cierra #wrap -->
Line 302:     <!-- Gallery Modal --> ✅ FUNCIONA
Line 320:     <!-- Zoom Modal --> ✅ FUNCIONA
Line 358:     <!-- Share Modal --> ✅ FUNCIONA
Line 479:     <!-- Report Modal --> ❌ NO FUNCIONA
Line 581: </t>  <!-- Cierra t-call -->
```

**CONCLUSIÓN**: El modal SÍ está dentro del `<t t-call="website.layout">`, en la misma ubicación que los otros modales que SÍ funcionan.

---

## 🔬 HIPÓTESIS

### Hipótesis 1: Comentario XML mal formado (DESCARTADA)
- No hay comentario `<!-- MODAL DE REPORTE/PQRS -->` en línea 479
- El modal inicia directamente en línea 480

### Hipótesis 2: Error de sintaxis QWeb (A VERIFICAR)
Posibles problemas:
1. Uso de `t-att-value` con expresiones complejas
2. Uso de funciones Python en atributos (`str(property.id)`)

### Hipótesis 3: El modal NO se está renderizando (MÁS PROBABLE)
Posibles causas:
1. El template tiene errores de QWeb que detienen el renderizado
2. El modal está siendo excluido por alguna condición
3. Hay un error de parsing que corta el template

---

## 🧪 PRUEBAS A REALIZAR

### Prueba 1: Inspeccionar DOM en el navegador
```javascript
// En la consola del navegador:
console.log(document.getElementById('reportModal'));
console.log(document.getElementById('shareModal'));  // Este SÍ funciona
console.log(document.querySelectorAll('.modal').length);  // Contar modales
```

**Resultado esperado**:
- Si `reportModal` es `null` pero `shareModal` existe → El HTML no se está renderizando
- Si ambos son `null` → Problema con la carga del template completo

### Prueba 2: Ver HTML renderizado
```bash
# Ir a http://localhost:8069/property/15360
# Abrir DevTools → Elements
# Buscar: id="reportModal"
```

**Resultado esperado**:
- Si NO aparece → El template tiene un error de QWeb o sintaxis
- Si SÍ aparece → El problema es de JavaScript/timing

### Prueba 3: Verificar logs de Odoo
```bash
# Buscar en odoo.log:
grep -i "reportModal\|qweb\|template.*error" "C:\Program Files\Odoo 18.0.20250830\server\odoo.log" | tail -50
```

**Resultado esperado**:
- Buscar errores de QWeb parsing
- Buscar warnings de template rendering

---

## 🔧 POSIBLES SOLUCIONES

### Solución 1: Simplificar atributos QWeb
Cambiar líneas como:
```xml
<!-- ANTES -->
<input type="hidden" name="property_url" t-att-value="request.httprequest.url_root.rstrip('/') + '/property/' + str(property.id)"/>

<!-- DESPUÉS -->
<input type="hidden" name="property_url" t-attf-value="#{request.httprequest.url_root.rstrip('/')}/property/#{property.id}"/>
```

### Solución 2: Mover el modal ANTES del modal de Share
Si hay un error de QWeb en el modal de reporte, moverlo antes de los otros modales que SÍ funcionan podría ayudar a identificar el problema.

### Solución 3: Crear un template separado
```xml
<template id="property_report_modal" name="Property Report Modal">
    <div class="modal fade" id="reportModal" tabindex="-1" aria-hidden="true">
        <!-- Contenido del modal -->
    </div>
</template>

<!-- Luego incluirlo en property_detail -->
<t t-call="theme_bohio_real_estate.property_report_modal"/>
```

---

## 📋 CHECKLIST DE DEBUGGING

- [ ] Inspeccionar DOM en navegador (Prueba 1)
- [ ] Ver HTML fuente renderizado (Prueba 2)
- [ ] Revisar logs de Odoo (Prueba 3)
- [ ] Verificar caché del navegador (Ctrl + Shift + R)
- [ ] Actualizar módulo: `odoo-bin -u theme_bohio_real_estate -d bohio_db`
- [ ] Reiniciar servidor Odoo
- [ ] Comparar con modal de Share (que SÍ funciona)
- [ ] Simplificar atributos QWeb (Solución 1)
- [ ] Buscar errores de consola JavaScript

---

## 🎯 PRÓXIMO PASO

**ACCIÓN INMEDIATA**: Actualizar el módulo para forzar el re-rendering del template

```bash
"C:\Program Files\Odoo 18.0.20250830\python\python.exe" "C:\Program Files\Odoo 18.0.20250830\server\odoo-bin" -c "C:\Program Files\Odoo 18.0.20250830\server\odoo.conf" -d bohio_db -u theme_bohio_real_estate --stop-after-init
```

**VERIFICACIÓN**: Abrir `http://localhost:8069/property/15360` e inspeccionar si `#reportModal` existe en el DOM.

# FIX: Modal de Reporte No Funciona

## Fecha: 2025-10-12
## Problema: Modal de reporte no se encuentra en el DOM

---

## 🔍 DIAGNÓSTICO

### Console Error:
```javascript
🚩 Abriendo modal de reporte
❌ Modal de reporte no encontrado
```

### Código JavaScript (property_detail_gallery.js línea 357):
```javascript
window.openReportModal = function() {
    console.log('🚩 Abriendo modal de reporte');
    const modalElement = document.getElementById('reportModal');
    if (!modalElement) {
        console.error('❌ Modal de reporte no encontrado');  // <-- ESTO SE EJECUTA
        return;
    }
    $('#reportModal').modal('show');
};
```

### Estado Actual del Template:
- **Archivo**: `property_detail_template.xml`
- **Modal Gallery** (línea 302): ✅ FUNCIONA
- **Modal Zoom** (línea 320): ✅ FUNCIONA
- **Modal Share** (línea 358): ✅ FUNCIONA
- **Modal Report** (línea 480): ❌ NO FUNCIONA

**TODOS LOS MODALES ESTÁN EN LA MISMA UBICACIÓN** - Dentro de `<t t-call="website.layout">`, después del cierre de `#wrap` (línea 300).

---

## 🧪 PASOS DE VERIFICACIÓN

### PASO 1: Verificar si el HTML se está renderizando

1. Abrir en el navegador: `http://localhost:8069/property/15360` (o cualquier propiedad)
2. Abrir DevTools (F12)
3. Ir a la pestaña **Console**
4. Ejecutar estos comandos:

```javascript
// Verificar si el modal existe en el DOM
console.log('Gallery Modal:', document.getElementById('galleryModal'));
console.log('Share Modal:', document.getElementById('shareModal'));
console.log('Report Modal:', document.getElementById('reportModal'));

// Contar todos los modales
console.log('Total modales:', document.querySelectorAll('.modal').length);

// Listar IDs de todos los modales
document.querySelectorAll('.modal').forEach(m => console.log(' -', m.id));
```

**Resultado esperado**:
- Si `reportModal` es `null` → **El HTML no se renderiza**
- Si `reportModal` existe → **Problema de JavaScript/timing**

### PASO 2: Ver el HTML fuente

1. En la misma página, click derecho → **Ver código fuente** (Ctrl + U)
2. Buscar (Ctrl + F): `id="reportModal"`
3. Verificar si aparece

**Resultado esperado**:
- Si NO aparece → **Template con error de QWeb**
- Si SÍ aparece → **Modal existe, problema de JavaScript**

### PASO 3: Verificar en Elements (Inspector)

1. En DevTools, ir a **Elements** (o Inspector)
2. Presionar Ctrl + F
3. Buscar: `reportModal`
4. Ver si aparece en el DOM

---

## 🔧 SOLUCIÓN TEMPORAL (MIENTRAS SE INVESTIGA)

Si el modal NO se está renderizando, podemos:

### Opción A: Simplificar los atributos QWeb

Hay atributos complejos que podrían estar causando errores de parsing:

**ANTES** (línea 497-500):
```xml
<input type="hidden" name="property_id" t-att-value="property.id"/>
<input type="hidden" name="property_name" t-att-value="property.name"/>
<input type="hidden" name="property_code" t-att-value="property.default_code or ''"/>
<input type="hidden" name="property_url" t-att-value="request.httprequest.url_root.rstrip('/') + '/property/' + str(property.id)"/>
```

**DESPUÉS** (simplificado):
```xml
<input type="hidden" name="property_id" t-attf-value="{{property.id}}"/>
<input type="hidden" name="property_name" t-attf-value="{{property.name}}"/>
<input type="hidden" name="property_code" t-attf-value="{{property.default_code or ''}}"/>
<input type="hidden" name="property_url" t-attf-value="#{request.httprequest.url_root.rstrip('/')}/property/#{property.id}"/>
```

### Opción B: Crear template separado

Crear un nuevo archivo: `views/modals/property_report_modal.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <template id="property_report_modal" name="Property Report Modal">
        <div class="modal fade" id="reportModal" tabindex="-1" aria-hidden="true">
            <!-- TODO: Contenido del modal aquí -->
        </div>
    </template>
</odoo>
```

Luego en `property_detail_template.xml` (línea 479):
```xml
<!-- Reemplazar todo el modal por: -->
<t t-call="theme_bohio_real_estate.property_report_modal"/>
```

Y agregar el archivo al `__manifest__.py`:
```python
'data': [
    # ...
    'views/modals/property_report_modal.xml',  # NUEVO
    'views/property_detail_template.xml',
    # ...
],
```

---

## 📋 CHECKLIST

Por favor, ejecutar los 3 pasos de verificación y reportar:

- [ ] Resultado de PASO 1 (console.log)
- [ ] Resultado de PASO 2 (código fuente)
- [ ] Resultado de PASO 3 (Elements inspector)

Con esa información sabré si:
1. **El template NO se renderiza** → Arreglar QWeb
2. **El template SÍ se renderiza** → Arreglar JavaScript

---

## 🎯 PRÓXIMO PASO

**ACCIÓN REQUERIDA DEL USUARIO**:

Por favor ejecuta los 3 pasos de verificación arriba y reporta los resultados.

Mientras tanto, voy a revisar el mapa que tampoco funciona.

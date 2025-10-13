# 🔍 DIAGNÓSTICO: Propiedades No Se Muestran en Homepage

## 📍 Problema Reportado

Las 3 secciones de la homepage NO muestran propiedades:
1. **Arriendo** - Sin propiedades en grid/mapa
2. **Venta de inmuebles usados** - Sin propiedades en grid/mapa
3. **Proyectos en venta** - Sin propiedades en grid/mapa

## 🔎 Análisis del Código Actual

### 1. Vista XML (homepage_new.xml)

La vista define 3 secciones con:
- Grid: `<div id="arriendo-properties-grid"/>`
- Mapa: `<div id="arriendo-properties-map"/>`

**✅ Estructura correcta** - Los contenedores están bien definidos.

### 2. JavaScript (homepage_properties.js)

El script hace llamadas a:
```javascript
await rpc('/property/search/ajax', {
    context: 'public',
    filters: params,
    page: 1,
    ppg: params.limit || 20,
    order: params.order || 'newest'
});
```

**Parámetros para Arriendo:**
```javascript
{
    type_service: 'rent',
    limit: 10,
    order: 'newest'
}
```

**Parámetros para Venta Usada:**
```javascript
{
    type_service: 'sale',
    has_project: false,  // SIN proyecto
    limit: 10,
    order: 'newest'
}
```

**Parámetros para Proyectos:**
```javascript
{
    type_service: 'sale',
    has_project: true,   // CON proyecto
    limit: 10,
    order: 'newest'
}
```

### 3. Controlador Python (property_search.py:139-193)

El endpoint `/property/search/ajax` existe y:
- Construye dominio base
- Aplica filtros de ubicación, propiedad, precio, amenidades
- Retorna JSON con `properties`, `total`, `page`, etc.

**✅ Endpoint correcto** - La lógica está implementada.

## 🐛 Posibles Causas del Problema

### ❌ Causa 1: Sin Propiedades en la BD

Si no hay propiedades con:
- `is_property = True`
- `active = True`
- `state = 'free'`
- `type_service = 'rent'` o `'sale'`

**Solución**: Verificar que existan propiedades en la base de datos.

### ❌ Causa 2: Filtro `has_project` Mal Implementado

En el controlador (línea 312-318):
```python
if 'has_project' in filters:
    if filters['has_project']:
        domain.append(('project_worksite_id', '!=', False))
    else:
        domain.append(('project_worksite_id', '=', False))
```

**PROBLEMA**: JavaScript envía `has_project: false` pero Python podría estar interpretando el booleano incorrectamente en JSON-RPC.

### ❌ Causa 3: Campo de Precio Incorrecto

El método `_get_price_field_by_context()` (línea 380-384) retorna:
- `'net_rental_price'` para arriendo
- `'net_price'` para venta

**PROBLEMA**: Si las propiedades no tienen estos campos poblados, podrían no aparecer.

### ❌ Causa 4: Error de JavaScript No Visible

Si `rpc()` falla silenciosamente, el código muestra mensaje de "No hay propiedades" sin dar error.

```javascript
catch (error) {
    console.error('Error cargando propiedades:', error);
    return { properties: [] };  // Retorna vacío sin notificar
}
```

### ❌ Causa 5: Módulo No Actualizado

Si el módulo `theme_bohio_real_estate` no está actualizado, el JavaScript podría no estar cargado.

## ✅ SOLUCIÓN PROPUESTA

Voy a crear un **script de diagnóstico completo** que:

1. **Verifica propiedades en BD**
   - Cuenta propiedades de arriendo
   - Cuenta propiedades de venta sin proyecto
   - Cuenta propiedades de venta con proyecto

2. **Prueba el endpoint directamente**
   - Llama `/property/search/ajax` con los mismos parámetros
   - Registra la respuesta completa

3. **Verifica configuración del módulo**
   - Confirma que el JS está en __manifest__.py
   - Confirma que la ruta está registrada

4. **Genera informe detallado**
   - Dominio aplicado
   - Propiedades encontradas
   - Campos faltantes

## 📝 Script de Diagnóstico

Ver: `diagnostico_homepage.py`

## 🔧 Pasos para Ejecutar

1. **Ejecutar script de diagnóstico:**
   ```bash
   "C:\Program Files\Odoo 18.0.20250830\python\python.exe" diagnostico_homepage.py
   ```

2. **Revisar consola del navegador:**
   - Abrir Homepage
   - Presionar F12
   - Ver mensajes de console.log
   - Ver errores en Network tab

3. **Verificar logs de Odoo:**
   ```bash
   tail -f "C:\Program Files\Odoo 18.0.20250830\server\odoo.log"
   ```

## 🎯 Acciones Correctivas Esperadas

### Si NO hay propiedades en BD:
- Importar propiedades de prueba
- Verificar migración de datos

### Si el filtro `has_project` falla:
- Corregir interpretación de booleanos en JSON-RPC
- Usar `has_project: 'true'` o `has_project: 'false'` (strings)

### Si campos de precio están vacíos:
- Actualizar propiedades con precios
- Modificar dominio para no requerir precio

### Si JavaScript no carga:
- Actualizar módulo: `odoo-bin -u theme_bohio_real_estate`
- Limpiar cache del navegador (Ctrl+Shift+Del)

### Si hay error de RPC:
- Verificar csrf_token
- Verificar auth='public' en la ruta

---

**Fecha**: 2025-10-11
**Módulo**: theme_bohio_real_estate
**Archivos Involucrados**:
- `views/homepage_new.xml`
- `static/src/js/homepage_properties.js`
- `controllers/property_search.py`

# ERROR: Actualización de módulo bohio_crm

## Problema

Al intentar actualizar el módulo `bohio_crm`, se produce un error de validación XML:

```
AssertionError: Element odoo has extra content: record, line 8
File: /home/odoo/src/user/bohio_crm/data/crm_automated_actions.xml
```

Además, hay campos faltantes en la base de datos:
```
column crm_lead.marketing_campaign_type does not exist
```

## Análisis

### Error #1: XML Validation
El archivo `crm_automated_actions.xml` tiene un problema de formato en la línea 8. Odoo no puede validar el XML.

### Error #2: Columnas faltantes
Los siguientes campos existen en el modelo Python pero no en la base de datos:
- `marketing_campaign_type`
- `marketing_quantity`
- `marketing_schedule`
- `marketing_estimated_reach`
- `marketing_budget_allocated`
- `marketing_start_date`
- `marketing_end_date`
- `marketing_description`

## Solución temporal aplicada

**Archivo**: `bohio_crm/__manifest__.py`

Se desactivó temporalmente el archivo XML problemático:

```python
'data': [
    # Seguridad
    'security/ir.model.access.csv',

    # Datos
    # 'data/crm_automated_actions.xml',  # TEMPORALMENTE DESACTIVADO: Error de formato XML

    # Vistas
    'views/bohio_crm_complete_views.xml',
    ...
]
```

## Pasos para resolver completamente

### Opción 1: Actualización manual desde la interfaz web (RECOMENDADO)

1. **Commit y push de cambios**:
   ```bash
   cd c:/Users/darm1/OneDrive/Documentos/GitHub/bohio-18
   git add bohio_crm/__manifest__.py
   git commit -m "fix: Desactivar crm_automated_actions.xml temporalmente"
   git push
   ```

2. **Actualizar en Odoo.com**:
   - Ir a https://darm1640-bohio-18.odoo.com
   - Aplicaciones → Buscar `bohio_crm`
   - Click en los 3 puntos → **Actualizar**

3. **Verificar**:
   - Los campos de marketing deberían crearse en la base de datos
   - El módulo debería actualizar sin errores

### Opción 2: Investigar error de XML

El error indica que hay contenido extra en el elemento `odoo` en la línea 8.

**Archivo**: `bohio_crm/data/crm_automated_actions.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- ============================================
         ACCIONES AUTOMÁTICAS DEL CRM
         ============================================ -->

    <!-- Acción: Crear Actividad al Programar Visita -->
    <record id="action_create_visit_activity" model="base.automation">  ← LÍNEA 8
```

**Posible causa**:
- El validador de Odoo puede estar detectando algo en el comentario o estructura
- Puede ser un problema de encoding
- Puede ser un problema de orden de elementos

**Solución propuesta**:
1. Revisar que no haya caracteres invisibles
2. Verificar que el encoding sea UTF-8 sin BOM
3. Intentar sin los comentarios HTML

## Estado actual

### ✅ Funcionando
- **theme_bohio_real_estate**: Actualizado correctamente
  - Filtros de listado ✅
  - Filtros de mapa ✅

### ⚠️ Pendiente
- **bohio_crm**: Error de actualización
  - Campos de marketing no creados en BD
  - Acciones automáticas no cargadas

## Impacto

### Bajo impacto inmediato
- Los campos de marketing son opcionales
- Las acciones automáticas son mejoras de UX, no críticas
- El CRM funciona sin estos elementos

### Funcionalidades afectadas
- ❌ No se pueden crear campañas de marketing desde CRM
- ❌ No se disparan actividades automáticas al programar visitas
- ❌ No se envían recordatorios de documentos de crédito
- ❌ No se notifica automáticamente cuando se aprueba un crédito

## Próximos pasos recomendados

1. **Hacer commit y push** del cambio en `__manifest__.py`
2. **Actualizar bohio_crm** desde la interfaz web
3. **Verificar** que los campos se crean correctamente
4. **Investigar** el error de XML en `crm_automated_actions.xml`
5. **Reactivar** el archivo XML una vez corregido

## Comandos útiles

```bash
# Commit de cambios
cd c:/Users/darm1/OneDrive/Documentos/GitHub/bohio-18
git status
git add bohio_crm/__manifest__.py
git commit -m "fix: Desactivar crm_automated_actions.xml temporalmente"
git push

# Verificar en Odoo.com después de actualizar
# SQL para verificar si las columnas existen:
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'crm_lead'
  AND column_name LIKE 'marketing%';
```

## Documentación relacionada

- [Odoo 18 Module Documentation](https://www.odoo.com/documentation/18.0/developer/reference/backend/module.html)
- [Odoo XML Data Files](https://www.odoo.com/documentation/18.0/developer/reference/backend/data.html)
- [Base Automation (Automated Actions)](https://www.odoo.com/documentation/18.0/developer/reference/backend/actions.html)

---

**Fecha**: 2025-10-11
**Estado**: Pendiente de resolución
**Prioridad**: Media (no crítico, pero importante para funcionalidad completa)

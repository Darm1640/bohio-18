# Fix: Acciones Automaticas bohio_crm para Odoo 18

## Problema Identificado

```
ValueError: Invalid field 'code' on model 'base.automation'
```

En **Odoo 18**, el modelo `base.automation` **NO tiene** un campo llamado `code`.

## Cambio Arquitectónico Odoo 18

### Antes (Odoo 17 y anteriores)
```xml
<record id="mi_accion" model="base.automation">
    <field name="name">Mi Acción</field>
    <field name="model_id" ref="crm.model_crm_lead"/>
    <field name="trigger">on_create</field>
    <field name="code">
        # Código Python aquí
        record.do_something()
    </field>
</record>
```

### Ahora (Odoo 18)
```xml
<!-- PASO 1: Definir ir.actions.server con el código -->
<record id="action_code_mi_accion" model="ir.actions.server">
    <field name="name">Codigo: Mi Acción</field>
    <field name="model_id" ref="crm.model_crm_lead"/>
    <field name="state">code</field>
    <field name="code"><![CDATA[
        # Código Python aquí
        record.do_something()
    ]]></field>
</record>

<!-- PASO 2: Definir base.automation que referencia la server action -->
<record id="automation_mi_accion" model="base.automation">
    <field name="name">CRM: Mi Acción</field>
    <field name="model_id" ref="crm.model_crm_lead"/>
    <field name="trigger">on_create</field>
    <field name="filter_domain">[('campo', '=', 'valor')]</field>
    <field name="action_server_ids" eval="[(4, ref('action_code_mi_accion'))]"/>
</record>
```

## Solución Implementada

### Archivos Creados

#### 1. `bohio_crm/data/crm_server_actions.xml`
Contiene **6 ir.actions.server** con código Python:

- `action_code_create_visit_activity` - Crear actividad al programar visita
- `action_code_notify_visit_conflict` - Notificar conflicto de visitas
- `action_code_remind_loan_documents` - Recordar documentos de crédito
- `action_code_update_capture_commission` - Actualizar comisión de captación
- `action_code_notify_loan_approval` - Notificar aprobación de crédito
- `action_code_create_reservation_on_won` - Sugerir crear reserva al ganar

#### 2. `bohio_crm/data/crm_automated_actions_v2.xml`
Contiene **6 base.automation** que referencian las server actions:

- `automation_create_visit_activity`
- `automation_notify_visit_conflict`
- `automation_remind_loan_documents`
- `automation_update_capture_commission`
- `automation_notify_loan_approval`
- `automation_create_reservation_on_won`

### Orden de Carga en `__manifest__.py`

**CRÍTICO**: Los server actions deben cargarse ANTES que las automations:

```python
'data': [
    'security/ir.model.access.csv',
    'data/crm_server_actions.xml',       # ← PRIMERO: define las actions
    'data/crm_automated_actions_v2.xml',  # ← SEGUNDO: las referencia
    # ... resto de archivos
]
```

## Pasos para Actualizar el Módulo

### Opción 1: Actualización Manual desde Odoo.com (RECOMENDADO)

1. **Los cambios ya están en GitHub** ✅
   - Commit: `c5f70f1` y `a6f5af9`
   - Branch: `main`

2. **Ir a Odoo.com**
   ```
   https://darm1640-bohio-18.odoo.com
   ```

3. **Actualizar Lista de Aplicaciones**
   - Ir a: **Aplicaciones** (Apps)
   - Click en el botón **"Actualizar Lista de Aplicaciones"**
   - Confirmar

4. **Actualizar bohio_crm**
   - Buscar: `bohio_crm`
   - Click en **"..."** (tres puntos)
   - Seleccionar: **"Actualizar"**
   - Esperar a que complete (puede tomar 30-60 segundos)

5. **Verificar**
   - Ir a: **CRM → Configuración → Acciones Automatizadas**
   - Buscar acciones que empiecen con `CRM:`
   - Deberías ver 6 acciones automatizadas

### Opción 2: Actualización via XML-RPC (Script Python)

```bash
cd "c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18"
"C:\Program Files\Odoo 18.0.20250830\python\python.exe" update_bohio_crm_fixed.py
```

**NOTA**: Este método puede fallar si Odoo.com no ha sincronizado los archivos desde GitHub aún.

## Verificación Post-Actualización

### 1. Verificar Acciones Automatizadas

Ir a: **CRM → Configuración → Acciones Automatizadas**

Deberías ver:
- ✅ CRM: Crear Actividad al Programar Visita
- ✅ CRM: Notificar Conflicto de Visitas
- ✅ CRM: Recordar Documentos de Crédito Pendientes
- ✅ CRM: Actualizar Comisión de Captación
- ✅ CRM: Notificar Aprobación de Crédito
- ✅ CRM: Sugerir Crear Reserva al Ganar Oportunidad

### 2. Verificar Campos de Marketing

Crear una nueva oportunidad en CRM y verificar que existan los campos:

```
Sección: Marketing
- Tipo de Campaña
- Cantidad de Publicaciones/Anuncios
- Horario Preferido para Publicidad
- Personas Estimadas a Alcanzar
- Presupuesto Asignado al Marketing
- Fecha Inicio de Campaña
- Fecha Fin de Campaña
- Descripción de la Campaña
```

### 3. Testing de Acciones

#### Test 1: Visita Programada
1. Crear oportunidad
2. Ir a pestaña **"Visitas y Reuniones"**
3. Llenar campo **"Fecha Ideal de Visita"**
4. Guardar
5. **VERIFICAR**: Debería crearse una actividad automáticamente

#### Test 2: Aprobación de Crédito
1. Crear oportunidad con financiamiento
2. Cambiar **"Estado de Crédito"** a **"Aprobado"**
3. Guardar
4. **VERIFICAR**: Debería crearse una actividad de llamada

#### Test 3: Ganada → Reserva
1. Crear oportunidad con propiedad
2. Moverla a etapa **"Ganada"**
3. **VERIFICAR**: Debería crearse una actividad para crear reserva

## Troubleshooting

### Error: "Invalid field 'code' on model 'base.automation'"
**Causa**: Odoo.com aún no sincronizó los archivos desde GitHub

**Solución**:
1. Esperar 5 minutos
2. Ir a **Aplicaciones → Actualizar Lista de Aplicaciones**
3. Intentar nuevamente

### Error: "column crm_lead.marketing_campaign_type does not exist"
**Causa**: El modelo Python no se actualizó, las columnas no se crearon

**Solución**:
1. Verificar que los cambios estén en GitHub (commit a6f5af9)
2. Actualizar lista de aplicaciones en Odoo.com
3. Actualizar el módulo bohio_crm

### Las acciones automatizadas no se disparan
**Causa Posible 1**: Las acciones están desactivadas

**Solución**:
- Ir a CRM → Configuración → Acciones Automatizadas
- Verificar que estén **Activas** (toggle verde)

**Causa Posible 2**: El filter_domain no se cumple

**Solución**:
- Revisar los logs en: Configuración → Técnico → Registro del Servidor
- Verificar que los campos existan y tengan los valores correctos

## Archivos de Respaldo

- `bohio_crm/data/crm_automated_actions_original_backup.xml` - Archivo original antes de los cambios
- `bohio_crm/data/crm_automated_actions.xml` - **OBSOLETO** (NO se usa, tiene la versión vieja con errores)

## Scripts de Utilidad

- `validate_crm_xml.py` - Validar sintaxis XML de todos los archivos del módulo
- `update_bohio_crm_fixed.py` - Actualizar módulo via XML-RPC (requiere que GitHub esté sincronizado)

## Diferencias Técnicas

### base.automation (Odoo 18)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | Char | Nombre de la automatización |
| `model_id` | Many2one | Modelo objetivo |
| `trigger` | Selection | on_create, on_write, on_create_or_write, on_unlink, on_time |
| `filter_domain` | Char | Dominio de filtro `[('campo', '=', 'valor')]` |
| `action_server_ids` | Many2many | Referencias a ir.actions.server |

**NO tiene**: `code` field

### ir.actions.server (Odoo 18)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | Char | Nombre de la acción |
| `model_id` | Many2one | Modelo objetivo |
| `state` | Selection | **code** para ejecutar Python |
| `code` | Text | Código Python a ejecutar |

## Fecha de Implementación
2025-10-11

## Autor
Claude Code

## Referencias
- [Odoo 18 Base Automation](https://www.odoo.com/documentation/18.0/developer/reference/backend/actions.html#automated-actions-base-automation)
- [Odoo 18 Server Actions](https://www.odoo.com/documentation/18.0/developer/reference/backend/actions.html#server-actions-ir-actions-server)

# Migración a Sistema Nativo de Documentos

## Resumen

El módulo `real_estate_bits` ahora usa el sistema nativo de Odoo (`ir.attachment`) en lugar del modelo personalizado `attachment.line`.

## Cambios Implementados

### 1. **Modelo attachment.line DEPRECATED**
- ✅ Marcado como obsoleto
- ✅ Se mantiene temporalmente para compatibilidad
- ✅ Log de advertencia al crear nuevos registros
- ✅ `image_1920` ya no es requerido

### 2. **Nuevo Archivo: property_attachments.py**
- ✅ Extiende `ir.attachment` con campos inmobiliarios:
  - `document_type`: Legal, Técnico, Foto, Plano, Certificado, etc.
  - `is_property_document`: Flag para filtrar
  - `is_brochure`: Marca folletos
  - `document_sequence`: Ordenamiento
  - `video_url`: URL de videos
  - `expiration_date` / `is_expired`: Vencimiento

### 3. **Modelos Actualizados**

#### product.template (Propiedades)
```python
property_attachment_ids  # One2many filtrado por res_model/res_id
document_count          # Contador
action_view_documents() # Acción para abrir documentos
```

#### property.contract (Contratos)
```python
contract_attachment_ids      # Documentos del contrato
contract_document_count      # Contador
```

#### project.worksite (Proyectos)
```python
project_attachment_ids       # Documentos del proyecto
project_document_count       # Contador
```

### 4. **Vistas Actualizadas**

#### Vista de Propiedad (view_property.xml)
- ✅ Botón stat "Documentos" en el header
- ✅ Nuevo campo `property_attachment_ids` en pestaña Documentos
- ✅ Alert informativo sobre nuevo sistema
- ✅ `attachment_line_ids` movido abajo con label DEPRECATED

#### Vista de Contrato (view_property_contract.xml)
- ✅ Campo `contract_attachment_ids` en pestaña Documents
- ✅ Sistema nuevo arriba, antiguo abajo separado

#### Vista de Proyecto (view_project_worksite.xml)
- ✅ Campo `project_attachment_ids` en ambas vistas de proyecto
- ✅ Compatibilidad con sistema antiguo

## Migración de Datos

El módulo `bohio_real_estate` incluye un script de migración automática:

**Ubicación:** `bohio_real_estate/migrations/1.0.1/post-migrate_attachment_line.py`

### Proceso:
1. Lee todos los registros de `attachment.line`
2. Crea `ir.attachment` equivalentes
3. Mantiene relaciones (property_id → res_model/res_id)
4. Convierte imágenes a tipo 'photo'
5. Preserva campo `is_brochure`

### Ejecución:
Se ejecuta automáticamente al actualizar `bohio_real_estate` si ya existe `real_estate_bits` instalado.

## Uso

### Agregar Documentos (Nuevo Sistema)

**Desde Formulario:**
```xml
<field name="property_attachment_ids"
       context="{'default_res_model': 'product.template',
                 'default_res_id': id,
                 'default_is_property_document': True}">
    <list editable="bottom">
        <field name="name"/>
        <field name="document_type"/>
        <field name="datas" filename="name"/>
        <field name="is_brochure"/>
    </list>
</field>
```

**Desde Botón Stat:**
1. Click en botón "Documentos" (icono documento)
2. Se abre vista filtrada de `ir.attachment`
3. Crear/Editar documentos directamente

### Python API

```python
# Crear documento para una propiedad
property = env['product.template'].browse(property_id)
attachment = env['ir.attachment'].create({
    'name': 'Escritura.pdf',
    'datas': base64_data,
    'res_model': 'product.template',
    'res_id': property.id,
    'is_property_document': True,
    'document_type': 'legal',
    'is_brochure': False,
})

# Contar documentos
doc_count = property.document_count

# Acceder a documentos
docs = property.property_attachment_ids
```

## Beneficios

1. **Sistema Nativo**
   - Compatible con módulo `documents` de Odoo
   - Integrado con chatter
   - Permisos y seguridad estándar

2. **Mejor Organización**
   - Tipos clasificados
   - Búsqueda mejorada
   - Vencimientos

3. **Rendimiento**
   - Usa `ir.attachment` optimizado
   - Índices nativos de Odoo
   - Storage en filesystem o DB

4. **Mantenimiento**
   - Sin modelo custom que mantener
   - Actualizaciones automáticas de Odoo
   - Menos código propio

## Compatibilidad

### Fase Actual: COEXISTENCIA
- ✅ Ambos sistemas funcionan simultáneamente
- ✅ Datos antiguos visibles pero marcados como DEPRECATED
- ✅ Nuevos documentos usan sistema nativo
- ⚠️ NO eliminar `attachment.line` todavía

### Fase Futura: LIMPIEZA (Opcional)
Una vez migrados TODOS los datos:

1. Verificar que no hay registros en `attachment_line_ids`
2. Eliminar campos `attachment_line_ids` de vistas
3. Remover modelo `attachment.line`
4. Eliminar archivo `models/attachment_line.py`
5. Actualizar `models/__init__.py`

## Notas Importantes

- ✅ **NO** se pierde información
- ✅ Script de migración preserva metadata
- ✅ Videos mantienen URL
- ✅ Folletos mantienen flag `is_brochure`
- ⚠️ Hacer **backup** antes de migrar
- ⚠️ Probar en ambiente de desarrollo primero

## Integración con bohio_real_estate

El módulo `bohio_real_estate` extiende aún más el sistema:
- Modelo `property.image` para galería dedicada
- Vistas kanban de imágenes
- Imagen de portada automática
- Control de visibilidad pública

Ver: `bohio_real_estate/MIGRATION_DOCUMENTS.md`
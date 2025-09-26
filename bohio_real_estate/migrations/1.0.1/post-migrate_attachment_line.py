import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Migra datos de attachment.line (modelo custom) a ir.attachment (nativo)
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    _logger.info("=== Iniciando migración de attachment.line a ir.attachment ===")

    if not env['ir.model'].search([('model', '=', 'attachment.line')]):
        _logger.info("El modelo attachment.line no existe, saltando migración")
        return

    AttachmentLine = env['attachment.line']
    IrAttachment = env['ir.attachment']

    attachment_lines = AttachmentLine.search([])
    _logger.info(f"Encontrados {len(attachment_lines)} registros en attachment.line")

    migrated_count = 0
    error_count = 0

    for line in attachment_lines:
        try:
            vals = {
                'name': line.name or 'Documento sin nombre',
                'datas': line.file if line.file else line.image_1920,
                'is_property_document': True,
                'document_sequence': line.sequence,
                'is_brochure': line.is_brochure if hasattr(line, 'is_brochure') else False,
                'description': f"Migrado desde attachment.line ID: {line.id}",
            }

            if line.property_id:
                vals.update({
                    'res_model': 'product.template',
                    'res_id': line.property_id.id,
                })
                if line.image_1920 and not line.file:
                    vals['document_type'] = 'photo'

            elif line.contract_id:
                vals.update({
                    'res_model': 'property.contract',
                    'res_id': line.contract_id.id,
                    'document_type': 'contract',
                })

            elif line.project_worksite_id:
                vals.update({
                    'res_model': 'project.worksite',
                    'res_id': line.project_worksite_id.id,
                    'document_type': 'technical',
                })

            elif line.project_plan_id:
                vals.update({
                    'res_model': 'project.worksite',
                    'res_id': line.project_plan_id.id,
                    'document_type': 'plan',
                })

            if vals.get('datas'):
                attachment = IrAttachment.create(vals)
                migrated_count += 1
                _logger.info(f"Migrado: {line.name} -> ir.attachment ID: {attachment.id}")
            else:
                _logger.warning(f"Sin datos para migrar: attachment.line ID {line.id}")
                error_count += 1

        except Exception as e:
            _logger.error(f"Error migrando attachment.line ID {line.id}: {str(e)}")
            error_count += 1
            continue

    _logger.info(f"=== Migración completada: {migrated_count} exitosos, {error_count} errores ===")

    if migrated_count > 0:
        _logger.info("IMPORTANTE: Revisar los datos migrados antes de eliminar attachment.line")
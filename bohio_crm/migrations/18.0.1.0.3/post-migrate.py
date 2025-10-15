# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

"""
Migración 18.0.1.0.3 - Post-Migration: Limpieza de Campos Antiguos
===================================================================

OBJETIVO:
Eliminar campos duplicados obsoletos después de consolidar datos.

CAMPOS A ELIMINAR:
1. num_bedrooms_min
2. num_bedrooms_max
3. num_bathrooms_min
4. property_area_min
5. property_area_max
6. num_occupants
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Post-migration: Eliminar campos obsoletos después de consolidación
    """
    _logger.info('=' * 80)
    _logger.info('POST-MIGRATION 18.0.1.0.3: Eliminación de Campos Duplicados')
    _logger.info('=' * 80)

    # Lista de campos a eliminar
    fields_to_drop = [
        'num_bedrooms_min',
        'num_bedrooms_max',
        'num_bathrooms_min',
        'property_area_min',
        'property_area_max',
        'num_occupants',
    ]

    # Eliminar cada campo
    for field_name in fields_to_drop:
        _drop_field_if_exists(cr, field_name)

    # Limpiar registros de ir.model.fields
    _clean_ir_model_fields(cr, fields_to_drop)

    # Limpiar registros de mail.tracking.value (historial de cambios)
    _clean_mail_tracking_values(cr, fields_to_drop)

    _logger.info('POST-MIGRATION 18.0.1.0.3: Completada exitosamente')
    _logger.info('=' * 80)


def _drop_field_if_exists(cr, field_name):
    """Eliminar un campo de la tabla crm_lead si existe"""
    # Verificar si el campo existe
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'crm_lead'
        AND column_name = %s
    """, (field_name,))

    if cr.fetchone():
        _logger.info(f'  → Eliminando campo: {field_name}')
        try:
            cr.execute(f"""
                ALTER TABLE crm_lead
                DROP COLUMN IF EXISTS {field_name} CASCADE
            """)
            _logger.info(f'  ✓ Campo {field_name} eliminado exitosamente')
        except Exception as e:
            _logger.warning(f'  ✗ Error al eliminar {field_name}: {e}')
    else:
        _logger.info(f'  ✓ Campo {field_name} ya no existe (OK)')


def _clean_ir_model_fields(cr, field_names):
    """Limpiar registros de ir.model.fields para campos eliminados"""
    _logger.info('Limpiando registros de ir.model.fields...')

    cr.execute("""
        SELECT id, name
        FROM ir_model_fields
        WHERE model = 'crm.lead'
        AND name IN %s
    """, (tuple(field_names),))

    records = cr.fetchall()
    if records:
        record_ids = [r[0] for r in records]
        _logger.info(f'  → Eliminando {len(record_ids)} registros de ir.model.fields')

        cr.execute("""
            DELETE FROM ir_model_fields
            WHERE id IN %s
        """, (tuple(record_ids),))

        _logger.info(f'  ✓ Eliminados {cr.rowcount} registros de ir.model.fields')
    else:
        _logger.info('  ✓ No hay registros de ir.model.fields para limpiar')


def _clean_mail_tracking_values(cr, field_names):
    """Limpiar registros de mail.tracking.value para campos eliminados"""
    _logger.info('Limpiando registros de mail.tracking.value...')

    # Primero, obtener los IDs de los campos en ir.model.fields
    cr.execute("""
        SELECT id, name
        FROM ir_model_fields
        WHERE model = 'crm.lead'
        AND name IN %s
    """, (tuple(field_names),))

    field_records = cr.fetchall()
    if not field_records:
        _logger.info('  ✓ No hay registros de tracking para limpiar')
        return

    field_ids = [r[0] for r in field_records]

    # Eliminar registros de mail.tracking.value
    cr.execute("""
        DELETE FROM mail_tracking_value
        WHERE field_id IN %s
    """, (tuple(field_ids),))

    count = cr.rowcount
    if count > 0:
        _logger.info(f'  ✓ Eliminados {count} registros de mail.tracking.value')
    else:
        _logger.info('  ✓ No hay registros de mail.tracking.value para limpiar')

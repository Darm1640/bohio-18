# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

"""
Migración 18.0.1.0.3 - Consolidación de Campos Duplicados
==========================================================

OBJETIVO:
Eliminar campos duplicados en crm.lead y consolidar datos en campos únicos.

CAMPOS A CONSOLIDAR:
1. num_bedrooms_min + num_bedrooms_max → min_bedrooms + max_bedrooms
2. num_bathrooms_min → min_bathrooms + max_bathrooms (nuevo)
3. property_area_min + property_area_max → min_area + max_area
4. num_occupants → number_of_occupants

ESTRATEGIA:
- PRE-MIGRATION: Copiar datos de campos antiguos a campos nuevos
- POST-MIGRATION: Eliminar campos antiguos de la base de datos
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Pre-migration: Consolidar datos de campos duplicados
    """
    _logger.info('=' * 80)
    _logger.info('PRE-MIGRATION 18.0.1.0.3: Consolidación de Campos Duplicados')
    _logger.info('=' * 80)

    # 1. Migrar campos de habitaciones
    _migrate_bedrooms(cr)

    # 2. Migrar campos de baños
    _migrate_bathrooms(cr)

    # 3. Migrar campos de área
    _migrate_area(cr)

    # 4. Migrar campos de ocupantes
    _migrate_occupants(cr)

    _logger.info('PRE-MIGRATION 18.0.1.0.3: Completada exitosamente')
    _logger.info('=' * 80)


def _migrate_bedrooms(cr):
    """Migrar num_bedrooms_min/max a min_bedrooms/max_bedrooms"""
    _logger.info('Migrando campos de habitaciones...')

    # Verificar si los campos antiguos existen
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'crm_lead'
        AND column_name IN ('num_bedrooms_min', 'num_bedrooms_max')
    """)
    old_fields = [row[0] for row in cr.fetchall()]

    if not old_fields:
        _logger.info('  ✓ Campos antiguos de habitaciones no encontrados (ya migrados)')
        return

    # Verificar si los campos nuevos existen
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'crm_lead'
        AND column_name IN ('min_bedrooms', 'max_bedrooms')
    """)
    new_fields = [row[0] for row in cr.fetchall()]

    if 'min_bedrooms' not in new_fields:
        _logger.info('  → Creando campo min_bedrooms...')
        cr.execute("""
            ALTER TABLE crm_lead
            ADD COLUMN IF NOT EXISTS min_bedrooms INTEGER
        """)

    if 'max_bedrooms' not in new_fields:
        _logger.info('  → Creando campo max_bedrooms...')
        cr.execute("""
            ALTER TABLE crm_lead
            ADD COLUMN IF NOT EXISTS max_bedrooms INTEGER
        """)

    # Migrar datos: priorizar campos nuevos si ya tienen datos
    if 'num_bedrooms_min' in old_fields:
        cr.execute("""
            UPDATE crm_lead
            SET min_bedrooms = COALESCE(min_bedrooms, num_bedrooms_min)
            WHERE num_bedrooms_min IS NOT NULL
        """)
        count = cr.rowcount
        _logger.info(f'  ✓ Migrados {count} registros de num_bedrooms_min → min_bedrooms')

    if 'num_bedrooms_max' in old_fields:
        cr.execute("""
            UPDATE crm_lead
            SET max_bedrooms = COALESCE(max_bedrooms, num_bedrooms_max)
            WHERE num_bedrooms_max IS NOT NULL
        """)
        count = cr.rowcount
        _logger.info(f'  ✓ Migrados {count} registros de num_bedrooms_max → max_bedrooms')


def _migrate_bathrooms(cr):
    """Migrar num_bathrooms_min a min_bathrooms y crear max_bathrooms"""
    _logger.info('Migrando campos de baños...')

    # Verificar si el campo antiguo existe
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'crm_lead'
        AND column_name = 'num_bathrooms_min'
    """)
    old_field_exists = cr.fetchone() is not None

    if not old_field_exists:
        _logger.info('  ✓ Campo antiguo num_bathrooms_min no encontrado (ya migrado)')
        return

    # Crear campos nuevos si no existen
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'crm_lead'
        AND column_name IN ('min_bathrooms', 'max_bathrooms')
    """)
    new_fields = [row[0] for row in cr.fetchall()]

    if 'min_bathrooms' not in new_fields:
        _logger.info('  → Creando campo min_bathrooms...')
        cr.execute("""
            ALTER TABLE crm_lead
            ADD COLUMN IF NOT EXISTS min_bathrooms INTEGER
        """)

    if 'max_bathrooms' not in new_fields:
        _logger.info('  → Creando campo max_bathrooms...')
        cr.execute("""
            ALTER TABLE crm_lead
            ADD COLUMN IF NOT EXISTS max_bathrooms INTEGER
        """)

    # Migrar datos
    cr.execute("""
        UPDATE crm_lead
        SET min_bathrooms = COALESCE(min_bathrooms, num_bathrooms_min)
        WHERE num_bathrooms_min IS NOT NULL
    """)
    count = cr.rowcount
    _logger.info(f'  ✓ Migrados {count} registros de num_bathrooms_min → min_bathrooms')


def _migrate_area(cr):
    """Migrar property_area_min/max a min_area/max_area"""
    _logger.info('Migrando campos de área...')

    # Verificar si los campos antiguos existen
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'crm_lead'
        AND column_name IN ('property_area_min', 'property_area_max')
    """)
    old_fields = [row[0] for row in cr.fetchall()]

    if not old_fields:
        _logger.info('  ✓ Campos antiguos de área no encontrados (ya migrados)')
        return

    # Verificar si los campos nuevos existen
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'crm_lead'
        AND column_name IN ('min_area', 'max_area')
    """)
    new_fields = [row[0] for row in cr.fetchall()]

    if 'min_area' not in new_fields:
        _logger.info('  → Creando campo min_area...')
        cr.execute("""
            ALTER TABLE crm_lead
            ADD COLUMN IF NOT EXISTS min_area NUMERIC
        """)

    if 'max_area' not in new_fields:
        _logger.info('  → Creando campo max_area...')
        cr.execute("""
            ALTER TABLE crm_lead
            ADD COLUMN IF NOT EXISTS max_area NUMERIC
        """)

    # Migrar datos: priorizar campos nuevos si ya tienen datos
    if 'property_area_min' in old_fields:
        cr.execute("""
            UPDATE crm_lead
            SET min_area = COALESCE(min_area, property_area_min)
            WHERE property_area_min IS NOT NULL
        """)
        count = cr.rowcount
        _logger.info(f'  ✓ Migrados {count} registros de property_area_min → min_area')

    if 'property_area_max' in old_fields:
        cr.execute("""
            UPDATE crm_lead
            SET max_area = COALESCE(max_area, property_area_max)
            WHERE property_area_max IS NOT NULL
        """)
        count = cr.rowcount
        _logger.info(f'  ✓ Migrados {count} registros de property_area_max → max_area')


def _migrate_occupants(cr):
    """Migrar num_occupants a number_of_occupants"""
    _logger.info('Migrando campos de ocupantes...')

    # Verificar si el campo antiguo existe
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'crm_lead'
        AND column_name = 'num_occupants'
    """)
    old_field_exists = cr.fetchone() is not None

    if not old_field_exists:
        _logger.info('  ✓ Campo antiguo num_occupants no encontrado (ya migrado)')
        return

    # Verificar si el campo nuevo existe
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'crm_lead'
        AND column_name = 'number_of_occupants'
    """)
    new_field_exists = cr.fetchone() is not None

    if not new_field_exists:
        _logger.info('  → Creando campo number_of_occupants...')
        cr.execute("""
            ALTER TABLE crm_lead
            ADD COLUMN IF NOT EXISTS number_of_occupants INTEGER
        """)

    # Migrar datos: priorizar campo nuevo si ya tiene datos
    cr.execute("""
        UPDATE crm_lead
        SET number_of_occupants = COALESCE(number_of_occupants, num_occupants)
        WHERE num_occupants IS NOT NULL
    """)
    count = cr.rowcount
    _logger.info(f'  ✓ Migrados {count} registros de num_occupants → number_of_occupants')

# -*- coding: utf-8 -*-
"""
Hooks para Theme BOHIO Real Estate
Pre-init, Post-init, Uninstall hooks
"""

import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """
    Hook ejecutado ANTES de instalar/actualizar el módulo

    Args:
        cr (odoo.sql_db.Cursor): Database cursor

    IMPORTANTE:
    - Este hook NO tiene acceso al registry ni a modelos ORM
    - Solo se pueden ejecutar queries SQL directas
    - No usar api.Environment aquí
    - Ninguna modificación de BD del módulo estará disponible aún

    Propósito:
    - Limpiar datos obsoletos mediante SQL directo
    - Preparar la base de datos para cambios estructurales
    - Eliminar registros que causan conflictos
    """
    _logger.info("="*80)
    _logger.info("BOHIO Real Estate - Ejecutando pre_init_hook")
    _logger.info("="*80)

    # NOTA: NO crear Environment aquí, solo usar SQL directo

    # 1. Limpiar vistas obsoletas del tema que puedan causar conflicto
    _clean_obsolete_views(cr)

    # 2. Limpiar assets obsoletos
    _clean_obsolete_assets(cr)

    # 3. Limpiar registros de menú duplicados
    _clean_duplicate_menus(cr)

    # 4. Limpiar datos de caché del tema
    _clean_theme_cache(cr)

    _logger.info("✓ Pre-init hook completado exitosamente")


def _clean_obsolete_views(cr):
    """
    Limpia vistas obsoletas del tema que puedan causar conflictos

    Estrategia:
    - Buscar vistas con arch_db vacío o inválido
    - Desactivar vistas con errores de herencia
    - Limpiar vistas duplicadas por external_id
    """
    _logger.info("→ Limpiando vistas obsoletas del tema...")

    try:
        # Buscar vistas del módulo con problemas
        cr.execute("""
            SELECT id, name, key
            FROM ir_ui_view
            WHERE key LIKE 'theme_bohio_real_estate.%%'
            AND (
                arch_db IS NULL
                OR arch_db = ''
                OR active = FALSE
            )
        """)

        obsolete_views = cr.fetchall()

        if obsolete_views:
            view_ids = [v[0] for v in obsolete_views]
            _logger.warning(f"  Encontradas {len(obsolete_views)} vistas obsoletas: {[v[1] for v in obsolete_views]}")

            # Eliminar vistas obsoletas
            cr.execute("""
                DELETE FROM ir_ui_view
                WHERE id IN %s
            """, (tuple(view_ids),))

            _logger.info(f"  ✓ Eliminadas {len(obsolete_views)} vistas obsoletas")
        else:
            _logger.info("  ✓ No se encontraron vistas obsoletas")

    except Exception as e:
        _logger.warning(f"  ⚠ Error limpiando vistas obsoletas: {e}")


def _clean_obsolete_assets(cr, env):
    """
    Limpia assets JS/CSS obsoletos que puedan causar conflictos

    Odoo 18 cambió el sistema de assets, algunos registros antiguos
    pueden causar conflictos
    """
    _logger.info("→ Limpiando assets obsoletos...")

    try:
        # Buscar assets del módulo sin bundle válido
        cr.execute("""
            SELECT id, name, path
            FROM ir_asset
            WHERE path LIKE 'theme_bohio_real_estate/%%'
            AND (
                bundle IS NULL
                OR bundle = ''
                OR active = FALSE
            )
        """)

        obsolete_assets = cr.fetchall()

        if obsolete_assets:
            asset_ids = [a[0] for a in obsolete_assets]
            _logger.warning(f"  Encontrados {len(obsolete_assets)} assets obsoletos")

            cr.execute("""
                DELETE FROM ir_asset
                WHERE id IN %s
            """, (tuple(asset_ids),))

            _logger.info(f"  ✓ Eliminados {len(obsolete_assets)} assets obsoletos")
        else:
            _logger.info("  ✓ No se encontraron assets obsoletos")

    except Exception as e:
        _logger.warning(f"  ⚠ Error limpiando assets obsoletos: {e}")


def _clean_duplicate_menus(cr, env):
    """
    Limpia menús duplicados del tema

    A veces al actualizar se crean menús duplicados
    """
    _logger.info("→ Limpiando menús duplicados...")

    try:
        # Buscar menús duplicados por nombre y parent_id
        cr.execute("""
            SELECT name, parent_id, COUNT(*) as count
            FROM ir_ui_menu
            WHERE name LIKE '%%BOHIO%%'
            OR name LIKE '%%Real Estate%%'
            GROUP BY name, parent_id
            HAVING COUNT(*) > 1
        """)

        duplicates = cr.fetchall()

        if duplicates:
            _logger.warning(f"  Encontrados {len(duplicates)} grupos de menús duplicados")

            for name, parent_id, count in duplicates:
                # Mantener solo el más reciente
                cr.execute("""
                    DELETE FROM ir_ui_menu
                    WHERE name = %s
                    AND parent_id %s
                    AND id NOT IN (
                        SELECT id FROM ir_ui_menu
                        WHERE name = %s
                        AND parent_id %s
                        ORDER BY create_date DESC
                        LIMIT 1
                    )
                """, (name, '= %s' % parent_id if parent_id else 'IS NULL',
                      name, '= %s' % parent_id if parent_id else 'IS NULL'))

            _logger.info(f"  ✓ Limpiados menús duplicados")
        else:
            _logger.info("  ✓ No se encontraron menús duplicados")

    except Exception as e:
        _logger.warning(f"  ⚠ Error limpiando menús duplicados: {e}")


def _clean_theme_cache(cr, env):
    """
    Limpia datos de caché del tema almacenados en ir.config_parameter
    """
    _logger.info("→ Limpiando caché del tema...")

    try:
        # Eliminar parámetros de configuración del tema antiguo
        cr.execute("""
            DELETE FROM ir_config_parameter
            WHERE key LIKE 'theme_bohio_real_estate.cache.%%'
        """)

        rows_deleted = cr.rowcount
        if rows_deleted > 0:
            _logger.info(f"  ✓ Eliminados {rows_deleted} parámetros de caché")
        else:
            _logger.info("  ✓ No se encontraron parámetros de caché")

    except Exception as e:
        _logger.warning(f"  ⚠ Error limpiando caché del tema: {e}")


def post_init_hook(cr, registry):
    """
    Hook ejecutado DESPUÉS de instalar el módulo

    Propósito:
    - Crear datos demo/iniciales si es necesario
    - Configurar valores por defecto
    - Indexar datos para búsqueda
    """
    _logger.info("="*80)
    _logger.info("BOHIO Real Estate - Ejecutando post_init_hook")
    _logger.info("="*80)

    env = api.Environment(cr, SUPERUSER_ID, {})

    # 1. Crear datos demo si no existen (opcional)
    # _create_demo_data(cr, env)

    # 2. Configurar valores por defecto del tema
    _configure_theme_defaults(cr, env)

    # 3. Reindexar campos de búsqueda si usa trigram
    _reindex_search_fields(cr, env)

    _logger.info("✓ Post-init hook completado exitosamente")


def _configure_theme_defaults(cr, env):
    """Configurar valores por defecto del tema"""
    _logger.info("→ Configurando valores por defecto del tema...")

    try:
        IrConfigParam = env['ir.config_parameter'].sudo()

        # Configuraciones por defecto
        defaults = {
            'theme_bohio_real_estate.homepage_properties_limit': '4',
            'theme_bohio_real_estate.autocomplete_min_chars': '2',
            'theme_bohio_real_estate.autocomplete_debounce_ms': '300',
            'theme_bohio_real_estate.map_default_zoom': '11',
            'theme_bohio_real_estate.map_default_lat': '4.7110',
            'theme_bohio_real_estate.map_default_lng': '-74.0721',
        }

        for key, value in defaults.items():
            if not IrConfigParam.get_param(key):
                IrConfigParam.set_param(key, value)
                _logger.info(f"  ✓ Configurado: {key} = {value}")

        _logger.info("  ✓ Valores por defecto configurados")

    except Exception as e:
        _logger.warning(f"  ⚠ Error configurando valores por defecto: {e}")


def _reindex_search_fields(cr, env):
    """Reindexar campos de búsqueda con trigram si está disponible"""
    _logger.info("→ Verificando índices de búsqueda...")

    try:
        # Verificar si la extensión pg_trgm está disponible
        cr.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm')")
        has_trigram = cr.fetchone()[0]

        if has_trigram:
            _logger.info("  ✓ Extensión pg_trgm disponible")

            # Crear índices GIN para búsqueda rápida (si no existen)
            indices = [
                ("idx_product_template_name_trgm", "product_template", "name"),
                ("idx_res_city_name_trgm", "res_city", "name"),
            ]

            for idx_name, table, column in indices:
                cr.execute(f"""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_indexes
                        WHERE indexname = '{idx_name}'
                    )
                """)

                if not cr.fetchone()[0]:
                    try:
                        cr.execute(f"""
                            CREATE INDEX {idx_name}
                            ON {table}
                            USING gin ({column} gin_trgm_ops)
                        """)
                        _logger.info(f"  ✓ Creado índice: {idx_name}")
                    except Exception as e:
                        _logger.warning(f"  ⚠ No se pudo crear índice {idx_name}: {e}")
        else:
            _logger.info("  ℹ Extensión pg_trgm no disponible (búsqueda sin optimización)")

    except Exception as e:
        _logger.warning(f"  ⚠ Error verificando índices: {e}")


def uninstall_hook(cr, registry):
    """
    Hook ejecutado al DESINSTALAR el módulo

    Propósito:
    - Limpiar datos específicos del módulo que no se eliminan automáticamente
    - Eliminar configuraciones
    - NO eliminar datos de negocio (propiedades, contactos, etc.)
    """
    _logger.info("="*80)
    _logger.info("BOHIO Real Estate - Ejecutando uninstall_hook")
    _logger.info("="*80)

    env = api.Environment(cr, SUPERUSER_ID, {})

    # 1. Eliminar configuraciones del tema
    _remove_theme_config(cr, env)

    # 2. Eliminar assets registrados
    _remove_theme_assets(cr, env)

    _logger.info("✓ Uninstall hook completado exitosamente")
    _logger.warning("⚠ Los datos de negocio (propiedades, contactos) se mantienen intactos")


def _remove_theme_config(cr, env):
    """Eliminar configuraciones del tema"""
    _logger.info("→ Eliminando configuraciones del tema...")

    try:
        cr.execute("""
            DELETE FROM ir_config_parameter
            WHERE key LIKE 'theme_bohio_real_estate.%%'
        """)

        rows_deleted = cr.rowcount
        _logger.info(f"  ✓ Eliminados {rows_deleted} parámetros de configuración")

    except Exception as e:
        _logger.warning(f"  ⚠ Error eliminando configuraciones: {e}")


def _remove_theme_assets(cr, env):
    """Eliminar assets del tema registrados dinámicamente"""
    _logger.info("→ Eliminando assets del tema...")

    try:
        cr.execute("""
            DELETE FROM ir_asset
            WHERE path LIKE 'theme_bohio_real_estate/%%'
        """)

        rows_deleted = cr.rowcount
        _logger.info(f"  ✓ Eliminados {rows_deleted} assets")

    except Exception as e:
        _logger.warning(f"  ⚠ Error eliminando assets: {e}")

from . import models
from . import controllers
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Hook ejecutado después de instalar/actualizar el módulo"""
    # Eliminar acción antigua ir.actions.act_window si existe
    old_action = env.ref('bohio_crm.action_crm_salesperson_dashboard', raise_if_not_found=False)
    if old_action and old_action._name == 'ir.actions.act_window':
        old_action.unlink()


def uninstall_hook(env):
    """
    Hook ejecutado durante la desinstalación del módulo.
    Limpia todos los registros, menús y datos relacionados con bohio_crm.
    """
    _logger.info("BOHIO CRM: Iniciando desinstalación limpia...")

    try:
        # 1. ELIMINAR MENÚS Y ACCIONES
        _cleanup_menus_and_actions(env)

        # 2. ELIMINAR VISTAS PERSONALIZADAS
        _cleanup_custom_views(env)

        # 3. ELIMINAR ACCIONES AUTOMATIZADAS
        _cleanup_automated_actions(env)

        # 4. ELIMINAR DATOS DE CONFIGURACIÓN
        _cleanup_config_data(env)

        _logger.info("BOHIO CRM: Desinstalación completada correctamente")

    except Exception as e:
        _logger.error(f"BOHIO CRM: Error durante desinstalación: {str(e)}", exc_info=True)
        # No lanzar excepción para no bloquear la desinstalación


def _cleanup_menus_and_actions(env):
    """Eliminar menús y acciones creadas por el módulo"""
    _logger.info("Limpiando menús y acciones...")

    # Lista de XML IDs de menús a eliminar
    menu_xmlids = [
        'bohio_crm.menu_bohio_crm_root',
        'bohio_crm.menu_crm_my_dashboard',
        'bohio_crm.menu_bohio_crm_opportunities',
        'bohio_crm.menu_crm_my_opportunities',
        'bohio_crm.menu_crm_all_opportunities',
        'bohio_crm.menu_crm_my_leads',
        'bohio_crm.menu_bohio_crm_reports',
        'bohio_crm.menu_crm_pipeline_report',
        'bohio_crm.menu_crm_commission_report',
        'bohio_crm.menu_crm_activities',
        'bohio_crm.menu_bohio_crm_config',
        'bohio_crm.menu_crm_stages',
        'bohio_crm.menu_crm_teams',
        'bohio_crm.menu_crm_activity_types',
        'bohio_crm.menu_crm_tags',
        'bohio_crm.menu_crm_lost_reasons',
    ]

    for xmlid in menu_xmlids:
        try:
            menu = env.ref(xmlid, raise_if_not_found=False)
            if menu:
                menu.unlink()
                _logger.info(f"Menú eliminado: {xmlid}")
        except Exception as e:
            _logger.warning(f"No se pudo eliminar menú {xmlid}: {e}")

    # Lista de XML IDs de acciones a eliminar
    action_xmlids = [
        'bohio_crm.action_crm_salesperson_dashboard_client',
        'bohio_crm.action_bohio_crm_my_opportunities',
        'bohio_crm.action_bohio_crm_all_opportunities',
        'bohio_crm.action_bohio_crm_my_leads',
        'bohio_crm.action_bohio_crm_pipeline_report',
        'bohio_crm.action_bohio_crm_commission_report',
        'bohio_crm.action_bohio_crm_activities_report',
    ]

    for xmlid in action_xmlids:
        try:
            action = env.ref(xmlid, raise_if_not_found=False)
            if action:
                action.unlink()
                _logger.info(f"Acción eliminada: {xmlid}")
        except Exception as e:
            _logger.warning(f"No se pudo eliminar acción {xmlid}: {e}")


def _cleanup_custom_views(env):
    """Eliminar vistas personalizadas del módulo"""
    _logger.info("Limpiando vistas personalizadas...")

    # Buscar y eliminar vistas que usan js_class de bohio_crm
    views_to_cleanup = env['ir.ui.view'].search([
        '|', '|', '|',
        ('arch_db', 'ilike', 'bohio_crm_dashboard_kanban'),
        ('arch_db', 'ilike', 'bohio_crm_kanban_modern'),
        ('arch_db', 'ilike', 'js_class="bohio_crm'),
        ('xml_id', 'ilike', 'bohio_crm.')
    ])

    for view in views_to_cleanup:
        try:
            _logger.info(f"Eliminando vista: {view.name} (ID: {view.id})")
            view.unlink()
        except Exception as e:
            _logger.warning(f"No se pudo eliminar vista {view.name}: {e}")


def _cleanup_automated_actions(env):
    """Eliminar acciones automatizadas (ir.cron, base.automation)"""
    _logger.info("Limpiando acciones automatizadas...")

    # Eliminar ir.actions.server del módulo
    server_actions = env['ir.actions.server'].search([
        ('xml_id', 'ilike', 'bohio_crm.')
    ])

    for action in server_actions:
        try:
            _logger.info(f"Eliminando server action: {action.name}")
            action.unlink()
        except Exception as e:
            _logger.warning(f"No se pudo eliminar server action {action.name}: {e}")

    # Eliminar base.automation (automated actions)
    automated_actions = env['base.automation'].search([
        '|',
        ('xml_id', 'ilike', 'bohio_crm.'),
        ('name', 'ilike', 'BOHIO CRM')
    ])

    for automation in automated_actions:
        try:
            _logger.info(f"Eliminando automated action: {automation.name}")
            automation.unlink()
        except Exception as e:
            _logger.warning(f"No se pudo eliminar automation {automation.name}: {e}")


def _cleanup_config_data(env):
    """Eliminar datos de configuración y parámetros del sistema"""
    _logger.info("Limpiando datos de configuración...")

    # Buscar ir.config_parameter relacionados
    config_params = env['ir.config_parameter'].search([
        ('key', 'ilike', 'bohio_crm%')
    ])

    for param in config_params:
        try:
            _logger.info(f"Eliminando parámetro: {param.key}")
            param.unlink()
        except Exception as e:
            _logger.warning(f"No se pudo eliminar parámetro {param.key}: {e}")

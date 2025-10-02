from . import models
from . import controllers


def post_init_hook(env):
    """Hook ejecutado después de instalar/actualizar el módulo"""
    # Eliminar acción antigua ir.actions.act_window si existe
    old_action = env.ref('bohio_crm.action_crm_salesperson_dashboard', raise_if_not_found=False)
    if old_action and old_action._name == 'ir.actions.act_window':
        old_action.unlink()

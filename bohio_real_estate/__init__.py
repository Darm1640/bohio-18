from . import models
from . import controllers


def pre_init_hook(env):
    env.cr.execute("""
        DELETE FROM ir_ui_view
        WHERE model = 'crm.lead'
        AND name LIKE '%bohio%'
    """)
    env.cr.execute("""
        DELETE FROM ir_ui_view
        WHERE model = 'product.template'
        AND name LIKE '%bohio%'
    """)
    env.cr.commit()


def post_init_hook(env):
    from .models.portal_menu import post_init_hook as setup_portal
    setup_portal(env)
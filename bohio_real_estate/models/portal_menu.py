from odoo import api, models, SUPERUSER_ID


def _setup_portal_menus(env):
    """Crea los menús del portal si no existen"""

    # Buscar o crear el menú padre "My Account" del portal
    portal_menu = env['website.menu'].search([
        ('url', '=', '/my'),
        '|', ('name', '=', 'My Account'),
        ('name', '=', 'Mi Cuenta')
    ], limit=1)

    if not portal_menu:
        # Buscar website principal
        website = env['website'].search([], limit=1)
        if not website:
            return

        portal_menu = env['website.menu'].create({
            'name': 'Mi Cuenta',
            'url': '/my',
            'website_id': website.id,
            'sequence': 99,
        })

    # Definir menús a crear
    menus_to_create = [
        {
            'id': 'bohio_real_estate.portal_menu_opportunities',
            'name': 'Mis Oportunidades',
            'url': '/my/opportunities',
            'sequence': 10,
        },
        {
            'id': 'bohio_real_estate.portal_menu_properties',
            'name': 'Mis Propiedades',
            'url': '/my/properties',
            'sequence': 20,
        },
        {
            'id': 'bohio_real_estate.portal_menu_contracts',
            'name': 'Mis Contratos',
            'url': '/my/contracts',
            'sequence': 30,
        },
        {
            'id': 'bohio_real_estate.portal_menu_payments',
            'name': 'Mis Pagos',
            'url': '/my/payments',
            'sequence': 40,
        },
    ]

    for menu_data in menus_to_create:
        # Verificar si ya existe
        existing = env['website.menu'].search([
            ('url', '=', menu_data['url']),
            ('parent_id', '=', portal_menu.id)
        ], limit=1)

        if not existing:
            menu = env['website.menu'].create({
                'name': menu_data['name'],
                'url': menu_data['url'],
                'parent_id': portal_menu.id,
                'sequence': menu_data['sequence'],
                'website_id': portal_menu.website_id.id,
            })

            # Crear external ID para referencia
            env['ir.model.data'].create({
                'name': menu_data['id'].split('.')[-1],
                'module': 'bohio_real_estate',
                'model': 'website.menu',
                'res_id': menu.id,
            })


class WebsiteMenu(models.Model):
    _inherit = 'website.menu'

    @api.model
    def _init_portal_menus(self):
        """Hook llamado después de instalar el módulo"""
        _setup_portal_menus(self.env)


def post_init_hook(env):
    """Hook ejecutado después de instalar el módulo"""
    _setup_portal_menus(env)
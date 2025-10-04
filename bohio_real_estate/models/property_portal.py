from odoo import models, fields, api


class ProductTemplatePortal(models.Model):
    _inherit = 'product.template'

    managed_by_bohio = fields.Boolean(
        string='Administrado por BOHIO',
        default=False,
        help='Indica si la propiedad es administrada directamente por BOHIO. '
             'Las propiedades administradas no pueden ser editadas desde el portal.',
        tracking=True
    )

    can_edit_portal = fields.Boolean(
        string='Puede Editar en Portal',
        compute='_compute_can_edit_portal',
        store=True,
        help='Indica si el propietario puede editar la propiedad desde el portal'
    )

    @api.depends('managed_by_bohio')
    def _compute_can_edit_portal(self):
        """Determina si el propietario puede editar desde el portal"""
        for record in self:
            record.can_edit_portal = not record.managed_by_bohio


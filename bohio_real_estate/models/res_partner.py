from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Campos de clasificación
    customer_type = fields.Selection([
        ('final', 'Cliente Final'),
        ('marketer', 'Comercializador'),
        ('distributor', 'Distribuidor')
    ], string='Tipo de Cliente', default='final')

    # Campos de autorización
    tratamiento_datos = fields.Selection([
        ('not_selected', 'No seleccionado'),
        ('authorized', 'Autorizado'),
        ('rejected', 'Rechazado'),
        ('pending', 'Pendiente')
    ], string='Tratamiento de Datos', default='not_selected')

    is_autorizado = fields.Boolean(
        string='Estado de Autorización',
        default=False,
        help='True si el cliente ha autorizado el tratamiento de datos'
    )

    # Campos de identificación personal
    commercial_name = fields.Char(
        string='Nombre Comercial/Razón Social',
        size=128,
        help='Nombre comercial o razón social de la empresa'
    )

    first_name = fields.Char(
        string='Primer Nombre',
        size=32
    )

    middle_name = fields.Char(
        string='Segundo Nombre',
        size=32
    )

    surname = fields.Char(
        string='Primer Apellido',
        size=32
    )

    mother_name = fields.Char(
        string='Segundo Apellido',
        size=32
    )

    @api.depends('first_name', 'middle_name', 'surname', 'mother_name', 'commercial_name')
    def _compute_display_name(self):
        """Calcula el nombre completo basado en los campos personalizados"""
        for partner in self:
            if partner.is_company and partner.commercial_name:
                partner.display_name = partner.commercial_name
            elif partner.first_name or partner.surname:
                name_parts = []
                if partner.first_name:
                    name_parts.append(partner.first_name)
                if partner.middle_name:
                    name_parts.append(partner.middle_name)
                if partner.surname:
                    name_parts.append(partner.surname)
                if partner.mother_name:
                    name_parts.append(partner.mother_name)
                partner.display_name = ' '.join(name_parts)
            else:
                super(ResPartner, partner)._compute_display_name()
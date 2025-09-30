from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectCategory(models.Model):
    _name = "project.worksite.category"
    _description = "Project Worksite Category"

    name = fields.Char()


class Amenities(models.Model):
    _name = "project.amenities"
    _description = "Project Amenities"

    name = fields.Char("Amenity", required=True)


class PropertyUtilities(models.Model):
    _name = "property.utilities"
    _description = "Servicios de Propiedad"

    price = fields.Float("Price")
    project_id = fields.Many2one("project.worksite")
    name = fields.Char("Nombre del Servicio", required=True)
    price = fields.Float("Precio", required=True)
    property_id = fields.Many2one("product.template", "Propiedad")
    utility_type = fields.Selection([
        ('water', 'Agua'),
        ('electricity', 'Electricidad'),
        ('gas', 'Gas'),
        ('internet', 'Internet'),
        ('cable', 'Cable TV'),
        ('security', 'Seguridad'),
        ('cleaning', 'Limpieza'),
        ('maintenance', 'Mantenimiento'),
        ('other', 'Otro')
    ], string="Tipo de Servicio", default='other')


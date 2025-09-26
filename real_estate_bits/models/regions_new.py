# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class Regions(models.Model):
    """
    Modelo para gestión de Barrios.
    Integrado con res.city para usar las ciudades nativas de Odoo.
    """
    _name = "region.region"
    _description = "Barrio"
    _order = "name"

    _inherit = ["mail.thread", "mail.activity.mixin"]

    # Información básica del barrio
    name = fields.Char(
        string="Nombre del Barrio",
        required=True,
        tracking=True,
        index=True
    )

    code = fields.Char(
        string="Código",
        help="Código único del barrio",
        index=True
    )

    active = fields.Boolean(
        string="Activo",
        default=True,
        tracking=True
    )

    # Relación con ciudad nativa de Odoo
    city_id = fields.Many2one(
        comodel_name='res.city',
        string='Ciudad',
        required=True,
        tracking=True,
        index=True,
        help="Ciudad a la que pertenece este barrio"
    )

    # Campos computados desde city_id
    state_id = fields.Many2one(
        related='city_id.state_id',
        string="Departamento/Estado",
        store=True,
        readonly=True
    )

    country_id = fields.Many2one(
        related='city_id.country_id',
        string="País",
        store=True,
        readonly=True
    )

    city_zipcode = fields.Char(
        related='city_id.zipcode',
        string="Código Postal Ciudad",
        readonly=True
    )

    # Información adicional del barrio
    zipcode = fields.Char(
        string="Código Postal del Barrio",
        help="Código postal específico del barrio si difiere del de la ciudad"
    )

    street = fields.Char(string="Dirección Principal")
    street2 = fields.Char(string="Dirección Secundaria")

    # Cuentas contables
    discount_account = fields.Many2one(
        comodel_name="account.account",
        string="Cuenta de Descuento"
    )

    expanses_account = fields.Many2one(
        comodel_name="account.account",
        string="Cuenta de Gastos Gerenciales"
    )

    # Compañía
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Compañía",
        default=lambda self: self.env.company
    )

    # Geolocalización
    latitude = fields.Float(
        string="Latitud",
        digits=(10, 7),
        help="Latitud GPS del centro del barrio"
    )

    longitude = fields.Float(
        string="Longitud",
        digits=(10, 7),
        help="Longitud GPS del centro del barrio"
    )

    lat_lng_ids = fields.One2many(
        comodel_name="lat.lng.line",
        inverse_name="region_id",
        string="Puntos Geográficos",
        copy=True
    )

    # Contadores
    project_count = fields.Integer(
        compute="_compute_counts",
        string="Proyectos"
    )

    property_count = fields.Integer(
        compute="_compute_counts",
        string="Propiedades"
    )



    @api.depends('name', 'city_id.name', 'state_id.name')
    def _compute_display_name(self):
        """Calcula el nombre completo del barrio con ciudad y estado."""
        for barrio in self:
            parts = []
            if barrio.name:
                parts.append(barrio.name)
            if barrio.city_id:
                parts.append(barrio.city_id.name)
            if barrio.state_id:
                parts.append(barrio.state_id.name)

            barrio.display_name = " - ".join(parts) if parts else _("Nuevo Barrio")

    def _compute_counts(self):
        """Calcula el número de proyectos y propiedades del barrio."""
        # Contar proyectos
        project_data = self.env['project.worksite'].read_group(
            [('region_id', 'in', self.ids), ('parent_id', '=', False)],
            ['region_id'],
            ['region_id']
        )
        project_map = {x['region_id'][0]: x['region_id_count'] for x in project_data if x['region_id']}

        # Contar propiedades
        property_data = self.env['product.template'].read_group(
            [('region_id', 'in', self.ids), ('is_property', '=', True)],
            ['region_id'],
            ['region_id']
        )
        property_map = {x['region_id'][0]: x['region_id_count'] for x in property_data if x['region_id']}

        for barrio in self:
            barrio.project_count = project_map.get(barrio.id, 0)
            barrio.property_count = property_map.get(barrio.id, 0)

    @api.onchange('city_id')
    def _onchange_city_id(self):
        """Actualiza campos relacionados cuando cambia la ciudad."""
        if self.city_id:
            # Si el barrio no tiene código postal propio, usar el de la ciudad
            if not self.zipcode and self.city_id.zipcode:
                self.zipcode = self.city_id.zipcode
        else:
            # Limpiar código postal si no hay ciudad
            if not self._origin.zipcode:
                self.zipcode = False

    @api.constrains('code', 'company_id')
    def _check_code_unique(self):
        """Valida que el código sea único por compañía."""
        for barrio in self:
            if barrio.code:
                domain = [
                    ('code', '=', barrio.code),
                    ('company_id', '=', barrio.company_id.id),
                    ('id', '!=', barrio.id)
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(
                        _("El código '%s' ya está en uso en otro barrio.") % barrio.code
                    )

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Búsqueda por nombre o código del barrio."""
        args = args or []
        if name:
            # Buscar por código exacto primero
            records = self.search([('code', '=', name)] + args, limit=limit)
            if not records:
                # Buscar por nombre o código parcial
                domain = ['|', ('name', operator, name), ('code', operator, name)]
                records = self.search(domain + args, limit=limit)
            return records.name_get()
        return super().name_search(name, args, operator, limit)

    def name_get(self):
        """Define cómo se muestra el barrio en campos Many2one."""
        result = []
        for barrio in self:
            # Mostrar: "Nombre Barrio (Ciudad)"
            if barrio.city_id:
                name = f"{barrio.name} ({barrio.city_id.name})"
            else:
                name = barrio.name
            result.append((barrio.id, name))
        return result

    def action_view_projects(self):
        """Abre la vista de proyectos del barrio."""
        self.ensure_one()
        return {
            'name': _("Proyectos de %s") % self.display_name,
            'view_mode': 'list,kanban,form',
            'res_model': 'project.worksite',
            'type': 'ir.actions.act_window',
            'domain': [('region_id', '=', self.id), ('parent_id', '=', False)],
            'context': {
                'default_region_id': self.id,
                'default_city_id': self.city_id.id,
            }
        }

    def action_view_properties(self):
        """Abre la vista de propiedades del barrio."""
        self.ensure_one()
        return {
            'name': _("Propiedades en %s") % self.display_name,
            'view_mode': 'kanban,list,form',
            'res_model': 'product.template',
            'type': 'ir.actions.act_window',
            'domain': [('region_id', '=', self.id), ('is_property', '=', True)],
            'context': {
                'default_region_id': self.id,
                'default_city_id': self.city_id.id,
                'default_is_property': True,
            }
        }

    def create_property_project(self):
        """Crea un nuevo proyecto en el barrio."""
        self.ensure_one()
        return {
            'name': _("Nuevo Proyecto en %s") % self.name,
            'view_mode': 'form',
            'res_model': 'project.worksite',
            'type': 'ir.actions.act_window',
            'context': {
                'default_region_id': self.id,
                'default_city_id': self.city_id.id,
                'default_state_id': self.state_id.id,
                'default_country_id': self.country_id.id,
            },
            'target': 'current',
        }


class LatLngLine(models.Model):
    """Modelo para almacenar múltiples coordenadas geográficas."""
    _name = "lat.lng.line"
    _description = 'Coordenadas Geográficas'
    _rec_name = 'name'

    name = fields.Char(
        string="Descripción",
        help="Descripción del punto geográfico"
    )

    lat = fields.Float(
        string="Latitud",
        digits=(10, 7),
        required=True
    )

    lng = fields.Float(
        string="Longitud",
        digits=(10, 7),
        required=True
    )

    url = fields.Char(
        string="URL del Mapa",
        help="Enlace a Google Maps o servicio similar"
    )

    region_id = fields.Many2one(
        comodel_name="region.region",
        string="Barrio",
        ondelete='cascade'
    )

    unit_id = fields.Many2one(
        comodel_name="product.template",
        string="Propiedad",
        domain=[("is_property", "=", True)],
        help="Propiedad asociada a estas coordenadas"
    )

    @api.onchange("url")
    def _onchange_url(self):
        """Intenta extraer información de la URL."""
        if self.url:
            try:
                # Intentar extraer coordenadas de una URL de Google Maps
                import re
                # Patrón para Google Maps: @latitud,longitud,
                pattern = r'@(-?\d+\.\d+),(-?\d+\.\d+)'
                match = re.search(pattern, self.url)
                if match:
                    self.lat = float(match.group(1))
                    self.lng = float(match.group(2))
            except Exception as e:
                _logger.debug(f"No se pudieron extraer coordenadas de la URL: {e}")

    def name_get(self):
        """Define cómo se muestran las coordenadas."""
        result = []
        for line in self:
            if line.name:
                name = line.name
            else:
                name = f"({line.lat:.4f}, {line.lng:.4f})"
            result.append((line.id, name))
        return result
from odoo import _, api, fields, models, tools
from .project_worksite import PROJECT_WORKSITE_TYPE
import logging
import pytz
import threading
from ast import literal_eval
from collections import OrderedDict, defaultdict
from datetime import date, datetime, timedelta
from markupsafe import Markup
from psycopg2 import sql



class Regions(models.Model):
    _name = "region.region"
    _description = "Barrio"
    _parent_name = "region_id"
    _parent_store = True
    _order = "complete_name"
    _rec_name = "complete_name"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    @api.depends("name", "region_id.complete_name")
    def _compute_complete_name(self):
        """Formar nombre completo de región desde padre hasta hijo."""
        for region in self:
            if region.region_id and region.region_id.complete_name:
                region.complete_name = f"{region.region_id.complete_name} / {region.name}"
            else:
                region.complete_name = region.name

    name = fields.Char("Nombre", required=True)
    complete_name = fields.Char("Nombre Completo", compute="_compute_complete_name", recursive=True, store=True)
    region_id = fields.Many2one("region.region", "Región Padre", ondelete="cascade")
    child_ids = fields.One2many("region.region", "region_id", "Regiones Hijas")
    parent_left = fields.Integer("Padre Izquierdo", index=True)
    parent_right = fields.Integer("Padre Derecho", index=True)
    discount_account = fields.Many2one("account.account", "Cuenta de Descuento")
    expanses_account = fields.Many2one("account.account", "Cuenta de Gastos Gerenciales")
    parent_path = fields.Char(index=True)
    company_id = fields.Many2one("res.company", string="Compañía", default=lambda self: self.env.company)
    lat_lng_ids = fields.One2many("lat.lng.line", "region_id", string="Lista Lat Lng", copy=True)
    map = fields.Char("Mapa")
    street = fields.Char("Calle")
    street2 = fields.Char("Calle 2")
    zip = fields.Char("Código Postal", change_default=True)
    city = fields.Char("Ciudad")
    city_id = fields.Many2one(comodel_name='res.city', string='Ciudad', readonly=False, store=True, 
                             domain="[('country_id', '=?', country_id)]")
    state_id = fields.Many2one("res.country.state", string="Departamento", ondelete="restrict",
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one("res.country", string="País", ondelete="restrict")
    country_code = fields.Char(related="country_id.code", string="Código País")
    project_count = fields.Integer(compute="_compute_project_count")
    address = fields.Char("Dirección")
    country_enforce_cities = fields.Boolean(related='country_id.enforce_cities')

    @api.depends('name', 'city_id', 'state_id')
    def _compute_display_name(self):
        for template in self:
            template.display_name = False if not template.name else ('{}{}{}'.format(
                template.name or '',
                ' [%s ' % template.city_id.name if template.city_id else '',
                '- %s] ' % template.city_id.state_id.name if template.city_id and template.city_id.state_id else ''
            ))

    def _compute_project_count(self):
        for rec in self:
            rec.project_count = len(
                self.env["project.worksite"].search([("region_id", "=", rec.id), ("parent_id", "=", False)]))

    def action_view_all_project(self):
        action = self.env.ref("real_estate_bits.action_project_worksite_act_window").read()[0]
        action["domain"] = [("region_id", "=", self.id), ("parent_id", "=", False)]
        action["context"] = {"default_region_id": self.id}
        return action

    @api.onchange('city_id')
    def _onchange_city_id(self):
        if self.city_id:
            self.city = self.city_id.name
            self.zip = self.city_id.zipcode
            self.state_id = self.city_id.state_id
        elif self._origin:
            self.city = False
            self.zip = False
            self.state_id = False

    def create_property_project(self):
        self.ensure_one()
        return {
            "name": _("Proyecto"),
            "view_mode": "form",
            "res_model": "project.worksite",
            "type": "ir.actions.act_window",
            "context": {"default_region_id": self.id},
        }


class LatLagLine(models.Model):
    _name = "lat.lng.line"
    _description = 'Línea Lat Lng'

    name = fields.Char("Nombre")
    lat = fields.Float("Latitud", digits=(9, 6), required=True)
    lng = fields.Float("Longitud", digits=(9, 6), required=True)
    url = fields.Char("URL")
    region_id = fields.Many2one("region.region", "Región")
    unit_id = fields.Many2one("product.template", "Unidad", 
                              domain=[("is_property", "=", True)], required=True)

    @api.onchange("url")
    def onchange_url(self):
        if self.url:
            url = self.url
            self.unit_id = int(((url.split("#")[1]).split("&")[0]).split("=")[1])
        else:
            self.unit_id = None
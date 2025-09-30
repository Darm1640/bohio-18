# -*- coding: utf-8 -*-
from odoo import fields, models

class CrmWidget(models.Model):
    _name = "crm.widget"
    _description = "CRM widget básico"
    _auto = False
    _table_query = "0"

    name = fields.Char('Nombre')
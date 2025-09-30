# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import datetime
from datetime import date
from dateutil.relativedelta import relativedelta


class SaleOrder(models.Model):
    _inherit = "sale.order"


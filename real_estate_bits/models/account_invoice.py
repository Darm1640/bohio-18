# -*- coding: utf-8 -*-
import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
# from openerp import models, fields, api
# from openerp.exceptions import UserError, ValidationError
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMoveInheritCommission(models.Model):
    _inherit = "account.move"

    # All commission logic removed


class HrPayslipLine(models.Model):
    _inherit = "hr.payslip.line"

    commissioned = fields.Boolean("Commissioned")
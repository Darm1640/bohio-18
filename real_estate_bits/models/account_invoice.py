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

    # Relación con línea de préstamo/renta
    rental_line_id = fields.Many2one(
        'loan.line',
        string='Línea de Renta',
        copy=False,
        index=True,
        help='Línea de cuota de renta relacionada con esta factura'
    )

    # Código de codificación para facturas automáticas
    auto_invoice_code = fields.Char(
        string='Código de Factura Automática',
        copy=False,
        index=True,
        help='Código único para identificar facturas generadas automáticamente'
    )

    def generate_auto_invoice_code(self, contract, line, owner=None, property_line=None):
        """
        Genera código único de factura automática
        Formato: CONT-[ID_CONTRATO]-CUOTA-[NUM_CUOTA]-[TIPO]-[ID_EXTRA]

        Ejemplos:
        - CONT-001-CUOTA-001-SINGLE
        - CONT-001-CUOTA-001-OWNER-123
        - CONT-001-CUOTA-001-PROP-456
        """
        parts = [
            'CONT',
            str(contract.id).zfill(6),
            'CUOTA',
            str(line.installment_no or 0).zfill(3)
        ]

        if owner:
            parts.extend(['OWNER', str(owner.id).zfill(6)])
        elif property_line:
            parts.extend(['PROP', str(property_line.id).zfill(6)])
        else:
            parts.append('SINGLE')

        return '-'.join(parts)


class HrPayslipLine(models.Model):
    _inherit = "hr.payslip.line"

    commissioned = fields.Boolean("Commissioned")
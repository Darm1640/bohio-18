# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountPaymentMethod(models.Model):
    """Extensión del método de pago para tesorería"""
    _inherit = 'account.payment.method'

    treasury_code = fields.Char(
        string='Código Tesorería',
        size=10,
        help='Código corto para identificar este método de pago (ej: EFE, CHQ, TRANSF)'
    )

    treasury_sequence_id = fields.Many2one(
        'ir.sequence',
        string='Secuencia de Tesorería',
        help='Secuencia específica para este método de pago en tesorería'
    )

    use_treasury_numbering = fields.Boolean(
        string='Usar Numeración Especial',
        default=False,
        help='Genera numeración consecutiva especial para este método de pago'
    )
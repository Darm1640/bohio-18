# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AdvanceReconciliation(models.Model):
    """Modelo para registrar conciliaciones de anticipos"""
    _name = 'advance.reconciliation'
    _description = 'Conciliación de Anticipo'
    _order = 'date desc'

    request_id = fields.Many2one(
        'advance.request',
        string='Solicitud de Anticipo',
        required=True,
        ondelete='cascade'
    )

    invoice_id = fields.Many2one(
        'account.move',
        string='Factura',
        required=True,
        domain=[('move_type', 'in', ['out_invoice', 'in_invoice'])]
    )

    amount = fields.Monetary(
        string='Monto Aplicado',
        currency_field='currency_id',
        required=True
    )

    currency_id = fields.Many2one(
        related='request_id.currency_id',
        string='Moneda'
    )

    date = fields.Date(
        string='Fecha',
        default=fields.Date.today,
        required=True
    )

    notes = fields.Text(
        string='Notas'
    )
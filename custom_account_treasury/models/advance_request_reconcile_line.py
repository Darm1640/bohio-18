# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AdvanceRequestReconcileLine(models.Model):
    _name = 'advance.request.reconcile.line'
    _description = 'Línea de Aplicación de Anticipo'
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
        domain="[('move_type', 'in', ['out_invoice', 'in_invoice']), ('state', '=', 'posted')]"
    )

    date = fields.Date(
        string='Fecha',
        required=True,
        default=fields.Date.today
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='request_id.currency_id'
    )

    invoice_amount = fields.Monetary(
        string='Monto Factura',
        currency_field='currency_id',
        compute='_compute_invoice_amount',
        store=True
    )

    amount_applied = fields.Monetary(
        string='Monto Aplicado',
        currency_field='currency_id',
        required=True
    )

    balance = fields.Monetary(
        string='Saldo',
        currency_field='currency_id',
        compute='_compute_balance',
        store=True
    )

    @api.depends('invoice_id')
    def _compute_invoice_amount(self):
        for line in self:
            if line.invoice_id:
                line.invoice_amount = line.invoice_id.amount_total
            else:
                line.invoice_amount = 0.0

    @api.depends('invoice_amount', 'amount_applied')
    def _compute_balance(self):
        for line in self:
            line.balance = line.invoice_amount - line.amount_applied
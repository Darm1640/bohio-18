# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class AccountMoveLine(models.Model):
    """
    Extensión unificada de account.move.line con todas las funcionalidades
    """
    _inherit = "account.move.line"



    is_advance_line = fields.Boolean(
        string='Es Línea de Anticipo',
        compute='_compute_is_advance_line',
        store=True,
        help='Indica si esta línea corresponde a un anticipo'
    )

    is_advance_payment_line = fields.Boolean(
        string='Es Línea de Pago de Anticipo',
        compute='_compute_is_advance_line',
        store=True
    )

    advance_payment_id = fields.Many2one(
        'account.payment',
        string='Pago de Anticipo',
        help='Pago de anticipo asociado a esta línea'
    )

    advance_applied_amount = fields.Monetary(
        string='Anticipo Aplicado',
        currency_field='currency_id',
        help='Monto de anticipo aplicado en esta línea'
    )


    line_pay = fields.Many2one(
        'account.move.line',
        string='Línea de Pago Origen',
        help='Línea de detalle de pago que generó este asiento contable'
    )

    payment_detail_id = fields.Many2one(
        'account.payment.detail',
        string='Detalle de Pago',
        help='Línea de detalle de pago que generó este asiento'
    )

    inv_id = fields.Many2one(
        'account.move',
        string='Factura Origen',
        help='Factura que originó este apunte contable'
    )

    inv_ids = fields.Many2many(
        'account.move',
        'move_line_invoice_rel',
        'move_line_id',
        'move_id',
        string='Facturas Relacionadas',
        help='Facturas relacionadas con este apunte (modo consolidado)'
    )

    invoice_ids = fields.Many2many(
        'account.move',
        'move_line_invoice_rel2',
        'line_id',
        'invoice_id',
        string='Facturas Relacionadas',
        help='Facturas relacionadas en modo consolidado'
    )

    line_pay_ids = fields.Many2many(
        'account.move.line',
        'move_line_payment_detail_rel',
        'move_line_id',
        'payment_detail_id',
        string='Líneas de Pago Relacionadas',
        help='Líneas de detalle de pago relacionadas (modo consolidado)'
    )

    payment_line_ids = fields.Many2many(
        'account.move.line',
        'move_line_payment_rel',
        'line_id',
        'payment_line_id',
        string='Líneas de Pago',
        help='Líneas de pago relacionadas en modo consolidado'
    )

    reconcile_line_ids = fields.Many2many(
        'account.move.line',
        'move_line_reconcile_rel',
        'line_id',
        'reconcile_line_id',
        string='Líneas para Reconciliar',
        help='Líneas que deben reconciliarse con esta'
    )

    force_partner_id = fields.Many2one(
        'res.partner',
        string='Tercero Forzado',
        help='Tercero específico para esta línea (multi-tercero)'
    )

    use_multi_partner = fields.Boolean(
        related='move_id.enable_multi_partner',
        string='Usa Multi-tercero'
    )

    @api.depends('account_id', 'account_id.used_for_advance_payment', 'payment_id')
    def _compute_is_advance_line(self):
        """Identifica líneas de anticipo"""
        for line in self:
            is_advance = (
                line.account_id.used_for_advance_payment or
                (line.payment_id and line.payment_id.advance)
            )
            line.is_advance_line = is_advance
            line.is_advance_payment_line = is_advance

    @api.depends('move_id.move_type', 'move_id.partner_id', 'use_multi_partner')
    def _compute_partner_id(self):
        """Override para respetar multi-tercero"""
        super()._compute_partner_id()

        for line in self:
            if line.use_multi_partner and line.force_partner_id:
                line.partner_id = line.force_partner_id
            elif line.use_multi_partner and line._origin.partner_id:
                line.partner_id = line._origin.partner_id

    @api.depends('move_id.move_type', 'move_id.partner_id',
                 'move_id.force_partner_account', 'move_id.forced_account_id')
    def _compute_account_id(self):
        """Calcula la cuenta considerando cuenta forzada"""
        super()._compute_account_id()

        for line in self:
            if line.display_type == 'payment_term' or (
                line.account_id and
                line.account_id.account_type in ('asset_receivable', 'liability_payable')
            ):
                if line.move_id.force_partner_account and line.move_id.forced_account_id:
                    line.account_id = line.move_id.forced_account_id


    def reconcile_with_advance(self, advance_payment):
        """
        Reconcilia esta línea con un anticipo
        """
        self.ensure_one()

        if not self.account_id.reconcile:
            raise UserError(_('La cuenta %s no permite reconciliación') % self.account_id.display_name)

        if not advance_payment.move_id:
            raise UserError(_('El anticipo no tiene asiento contable'))

        advance_lines = advance_payment.move_id.line_ids.filtered(
            lambda l: l.account_id == self.account_id and not l.reconciled
        )

        if not advance_lines:
            raise UserError(_('No se encontró línea de anticipo para reconciliar'))

        # Reconciliar
        return (self | advance_lines[0]).reconcile()

    def get_advance_balance(self):
        """
        Obtiene el saldo de anticipo disponible en esta línea
        """
        self.ensure_one()

        if not self.is_advance_line:
            return 0.0

        return abs(self.amount_residual)

    def apply_advance_to_invoice(self, invoice_line, amount=None):
        """
        Aplica el saldo de esta línea de anticipo a una línea de factura
        """
        self.ensure_one()
        invoice_line.ensure_one()

        if not self.is_advance_line:
            raise UserError(_('Esta no es una línea de anticipo'))

        if not amount:
            amount = min(abs(self.amount_residual), abs(invoice_line.amount_residual))

        if float_is_zero(amount, precision_rounding=self.currency_id.rounding):
            return False

        move_vals = {
            'move_type': 'entry',
            'date': fields.Date.today(),
            'journal_id': self.journal_id.id,
            'ref': _('Aplicación anticipo a %s') % invoice_line.move_id.name,
            'line_ids': []
        }

        if invoice_line.move_id.move_type == 'out_invoice':
            move_vals['line_ids'] = [
                (0, 0, {
                    'account_id': self.account_id.id,
                    'partner_id': self.partner_id.id,
                    'name': _('Aplicación anticipo'),
                    'debit': amount,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'account_id': invoice_line.account_id.id,
                    'partner_id': invoice_line.partner_id.id,
                    'name': _('Aplicación a factura'),
                    'debit': 0.0,
                    'credit': amount,
                })
            ]
        else:
            move_vals['line_ids'] = [
                (0, 0, {
                    'account_id': invoice_line.account_id.id,
                    'partner_id': invoice_line.partner_id.id,
                    'name': _('Aplicación a factura'),
                    'debit': amount,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'account_id': self.account_id.id,
                    'partner_id': self.partner_id.id,
                    'name': _('Aplicación anticipo'),
                    'debit': 0.0,
                    'credit': amount,
                })
            ]

        cross_move = self.env['account.move'].create(move_vals)
        cross_move.action_post()

        # Reconciliar líneas
        for line in cross_move.line_ids:
            if line.account_id == self.account_id:
                (self | line).reconcile()
            elif line.account_id == invoice_line.account_id:
                (invoice_line | line).reconcile()

        # Registrar aplicación
        self.advance_applied_amount += amount

        return cross_move

    @api.model
    def search_advances_for_partner(self, partner, advance_type='all'):
        """
        Busca líneas de anticipo disponibles para un partner
        """
        domain = [
            ('partner_id', '=', partner.commercial_partner_id.id),
            ('account_id.used_for_advance_payment', '=', True),
            ('reconciled', '=', False),
            ('parent_state', '=', 'posted'),
            ('amount_residual', '!=', 0)
        ]

        if advance_type == 'customer':
            domain.append(('balance', '<', 0))
        elif advance_type == 'supplier':
            domain.append(('balance', '>', 0))

        return self.search(domain, order='date asc')

    # ========================================================================
    # OVERRIDE METHODS
    # ========================================================================

    @api.onchange('account_id')
    def _onchange_account_id_advance(self):
        """Detecta y configura líneas de anticipo"""
        if self.account_id and self.account_id.used_for_advance_payment:
            advance_type = self.env['advance.type'].search([
                ('advance_account_id', '=', self.account_id.id),
                ('company_ids', 'in', self.company_id.id)
            ], limit=1)

            if advance_type:
                if not self.name:
                    self.name = _('Anticipo - %s') % advance_type.name

                if not self.partner_id and self.move_id.partner_id:
                    self.partner_id = self.move_id.partner_id

    @api.onchange('partner_id')
    def _onchange_partner_id_account(self):
        if not self.use_multi_partner or not self.partner_id:
            return

        if self.display_type == 'payment_term':
            if self.move_id.move_type in ('out_invoice', 'out_refund'):
                self.account_id = self.partner_id.property_account_receivable_id
            elif self.move_id.move_type in ('in_invoice', 'in_refund'):
                self.account_id = self.partner_id.property_account_payable_id

    @api.model_create_multi
    def create(self, vals_list):
        """Override para manejar multi-tercero"""
        if self._context.get('enable_multi_partner'):
            for vals in vals_list:
                if 'force_partner_id' not in vals and 'partner_id' in vals:
                    vals['force_partner_id'] = vals['partner_id']

        return super().create(vals_list)

    def write(self, vals):
        if self._context.get('enable_multi_partner'):
            if 'partner_id' in vals and self.force_partner_id:
                vals['force_partner_id'] = vals['partner_id']
                del vals['partner_id']

        return super().write(vals)

    def reconcile(self):
        advance_lines = self.filtered('is_advance_line')

        if advance_lines:
            # Log para auditoría
            for line in advance_lines:
                if line.payment_id:
                    line.payment_id.message_post(
                        body=_('Anticipo reconciliado con: %s') %
                        ', '.join(self.mapped('move_id.name'))
                    )

        return super().reconcile()

    def remove_move_reconcile(self):
        advance_lines = self.filtered('is_advance_line')

        if advance_lines:
            for line in advance_lines:
                if line.payment_id:
                    line.payment_id.message_post(
                        body=_('Anticipo desreconciliado')
                    )
                line.advance_applied_amount = 0

        return super().remove_move_reconcile()

    def _check_reconcile_validity(self):
        advance_accounts = self.mapped('account_id').filtered('used_for_advance_payment')

        if advance_accounts:
            other_accounts = self.mapped('account_id') - advance_accounts

            for account in other_accounts:
                if account.account_type not in ('asset_receivable', 'liability_payable'):
                    return super()._check_reconcile_validity()
            return
        return super()._check_reconcile_validity()

    def _get_computed_account(self):
        if self.move_id.force_partner_account and self.move_id.forced_account_id:
            if self.display_type == 'payment_term':
                return self.move_id.forced_account_id
            elif not self.product_id and not self.account_id:
                if self.move_id.is_sale_document(include_receipts=True):
                    return self.move_id.forced_account_id
                elif self.move_id.is_purchase_document(include_receipts=True):
                    return self.move_id.forced_account_id

        return super()._get_computed_account()
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json


class AccountPayment(models.Model):
    """Extiende account.payment para gestión de anticipos"""
    _inherit = 'account.payment'

    # Relación con solicitud de anticipo
    advance_request_id = fields.Many2one(
        'advance.request',
        string='Solicitud de Anticipo',
        readonly=True,
        ondelete='restrict'
    )

    is_advance = fields.Boolean(
        string='Es Anticipo',
        help='Indica si este pago es un anticipo'
    )

    advance_balance = fields.Monetary(
        string='Saldo de Anticipo',
        currency_field='currency_id',
        compute='_compute_advance_balance',
        store=True,
        help='Saldo disponible del anticipo'
    )

    advance_reconciled_amount = fields.Monetary(
        string='Monto Aplicado',
        currency_field='currency_id',
        compute='_compute_advance_balance',
        store=True,
        help='Monto del anticipo aplicado a facturas'
    )

    # Widget para anticipos existentes
    advance_selection_ids = fields.Many2many(
        'account.payment',
        'payment_advance_rel',
        'payment_id',
        'advance_id',
        string='Anticipos a Aplicar',
        domain="[('partner_id', '=', partner_id), ('is_advance', '=', True), ('advance_balance', '>', 0)]",
        help='Seleccione anticipos existentes para aplicar'
    )

    show_advance_widget = fields.Boolean(
        string='Mostrar Widget Anticipos',
        compute='_compute_show_advance_widget'
    )

    @api.depends('partner_id', 'payment_type')
    def _compute_show_advance_widget(self):
        """Determina si mostrar el widget de anticipos"""
        for payment in self:
            if payment.partner_id and not payment.is_advance:
                # Buscar anticipos disponibles
                domain = [
                    ('partner_id', '=', payment.partner_id.id),
                    ('is_advance', '=', True),
                    ('state', '=', 'posted'),
                    ('advance_balance', '>', 0)
                ]
                payment.show_advance_widget = bool(self.search(domain, limit=1))
            else:
                payment.show_advance_widget = False

    @api.depends('amount', 'advance_request_id.reconciliation_ids')
    def _compute_advance_balance(self):
        """Calcula el saldo del anticipo"""
        for payment in self:
            if payment.is_advance and payment.state == 'posted':
                # Calcular monto reconciliado
                if payment.advance_request_id:
                    reconciliations = payment.advance_request_id.reconciliation_ids
                    payment.advance_reconciled_amount = sum(reconciliations.mapped('amount'))
                else:
                    # Buscar reconciliaciones directas
                    payment.advance_reconciled_amount = 0

                payment.advance_balance = payment.amount - payment.advance_reconciled_amount
            else:
                payment.advance_balance = 0
                payment.advance_reconciled_amount = 0

    def action_post(self):
        """Override para actualizar estado de solicitud de anticipo"""
        res = super().action_post()

        for payment in self.filtered('advance_request_id'):
            request = payment.advance_request_id
            # Actualizar estado de la solicitud
            if request.state == 'approved':
                request.write({
                    'state': 'paid',
                    'date_paid': fields.Datetime.now()
                })

                # Auto-conciliar si está configurado
                if request.auto_reconcile:
                    request.auto_reconcile_advances()

        return res

    def action_apply_advances(self):
        """Aplica anticipos seleccionados a facturas"""
        self.ensure_one()

        if not self.advance_selection_ids:
            raise UserError(_('Por favor seleccione al menos un anticipo para aplicar'))

        # Crear wizard de reconciliación
        wizard = self.env['advance.reconciliation.wizard'].create({
            'payment_id': self.id,
            'advance_ids': [(6, 0, self.advance_selection_ids.ids)]
        })

        return {
            'name': _('Aplicar Anticipos'),
            'type': 'ir.actions.act_window',
            'res_model': 'advance.reconciliation.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new'
        }

    def action_view_advance_details(self):
        """Ver detalles del anticipo"""
        self.ensure_one()

        if self.advance_request_id:
            return {
                'name': _('Solicitud de Anticipo'),
                'type': 'ir.actions.act_window',
                'res_model': 'advance.request',
                'res_id': self.advance_request_id.id,
                'view_mode': 'form',
                'target': 'current'
            }


class AccountJournal(models.Model):
    """Extiende account.journal para dashboard de tesorería"""
    _inherit = 'account.journal'

    # Saldos de anticipos
    total_advance_balance = fields.Monetary(
        string='Saldo de Anticipos',
        currency_field='currency_id',
        compute='_compute_advance_balances'
    )

    customer_advance_balance = fields.Monetary(
        string='Anticipos de Clientes',
        currency_field='currency_id',
        compute='_compute_advance_balances'
    )

    supplier_advance_balance = fields.Monetary(
        string='Anticipos a Proveedores',
        currency_field='currency_id',
        compute='_compute_advance_balances'
    )

    # Pagos por validar
    pending_payment_count = fields.Integer(
        string='Pagos por Validar',
        compute='_compute_pending_payments'
    )

    pending_payment_amount = fields.Monetary(
        string='Monto por Validar',
        currency_field='currency_id',
        compute='_compute_pending_payments'
    )

    # Información adicional para dashboard
    bank_balance = fields.Monetary(
        string='Saldo Bancario',
        currency_field='currency_id',
        compute='_compute_bank_balance'
    )

    projected_balance = fields.Monetary(
        string='Saldo Proyectado',
        currency_field='currency_id',
        compute='_compute_projected_balance',
        help='Saldo bancario + cobros pendientes - pagos pendientes'
    )

    @api.depends('type')
    def _compute_advance_balances(self):
        """Calcula saldos de anticipos"""
        for journal in self:
            if journal.type == 'bank':
                # Anticipos de clientes
                customer_advances = self.env['account.payment'].search([
                    ('journal_id', '=', journal.id),
                    ('is_advance', '=', True),
                    ('payment_type', '=', 'inbound'),
                    ('state', '=', 'posted'),
                    ('advance_balance', '>', 0)
                ])
                journal.customer_advance_balance = sum(customer_advances.mapped('advance_balance'))

                # Anticipos a proveedores
                supplier_advances = self.env['account.payment'].search([
                    ('journal_id', '=', journal.id),
                    ('is_advance', '=', True),
                    ('payment_type', '=', 'outbound'),
                    ('state', '=', 'posted'),
                    ('advance_balance', '>', 0)
                ])
                journal.supplier_advance_balance = sum(supplier_advances.mapped('advance_balance'))

                journal.total_advance_balance = journal.customer_advance_balance - journal.supplier_advance_balance
            else:
                journal.customer_advance_balance = 0
                journal.supplier_advance_balance = 0
                journal.total_advance_balance = 0

    def _compute_pending_payments(self):
        """Calcula pagos pendientes de validación"""
        for journal in self:
            pending_payments = self.env['account.payment'].search([
                ('journal_id', '=', journal.id),
                ('state', '=', 'draft')
            ])
            journal.pending_payment_count = len(pending_payments)
            journal.pending_payment_amount = sum(pending_payments.mapped('amount'))

    def _compute_bank_balance(self):
        """Calcula saldo bancario actual"""
        for journal in self:
            if journal.type == 'bank':
                # Obtener cuenta bancaria
                bank_account = journal.default_account_id
                if bank_account:
                    # Calcular saldo
                    domain = [
                        ('account_id', '=', bank_account.id),
                        ('parent_state', '=', 'posted')
                    ]
                    move_lines = self.env['account.move.line'].search(domain)
                    journal.bank_balance = sum(move_lines.mapped('balance'))
                else:
                    journal.bank_balance = 0
            else:
                journal.bank_balance = 0

    def _compute_projected_balance(self):
        """Calcula saldo proyectado"""
        for journal in self:
            if journal.type == 'bank':
                # Cobros pendientes
                pending_inbound = self.env['account.payment'].search([
                    ('journal_id', '=', journal.id),
                    ('payment_type', '=', 'inbound'),
                    ('state', '=', 'draft')
                ])
                total_inbound = sum(pending_inbound.mapped('amount'))

                # Pagos pendientes
                pending_outbound = self.env['account.payment'].search([
                    ('journal_id', '=', journal.id),
                    ('payment_type', '=', 'outbound'),
                    ('state', '=', 'draft')
                ])
                total_outbound = sum(pending_outbound.mapped('amount'))

                journal.projected_balance = journal.bank_balance + total_inbound - total_outbound
            else:
                journal.projected_balance = 0

    def action_view_pending_payments(self):
        """Ver pagos pendientes de validación"""
        self.ensure_one()
        return {
            'name': _('Pagos por Validar'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [
                ('journal_id', '=', self.id),
                ('state', '=', 'draft')
            ],
            'context': {
                'default_journal_id': self.id,
                'search_default_group_by_payment_type': 1
            }
        }

    def action_view_advances(self):
        """Ver anticipos del diario"""
        self.ensure_one()
        return {
            'name': _('Anticipos'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [
                ('journal_id', '=', self.id),
                ('is_advance', '=', True),
                ('advance_balance', '>', 0)
            ],
            'context': {
                'default_journal_id': self.id,
                'search_default_group_by_payment_type': 1
            }
        }

    def open_action_with_context(self):
        """Override para incluir información de anticipos en dashboard"""
        action = super().open_action_with_context()

        # Agregar información adicional al contexto
        if self.type == 'bank':
            action['context'].update({
                'bank_balance': self.bank_balance,
                'total_advance_balance': self.total_advance_balance,
                'pending_payment_count': self.pending_payment_count,
                'pending_payment_amount': self.pending_payment_amount
            })

        return action


class AccountMove(models.Model):
    """Extiende account.move para mostrar anticipos disponibles"""
    _inherit = 'account.move'

    # Anticipos disponibles del partner
    available_advance_ids = fields.Many2many(
        'account.payment',
        compute='_compute_available_advances',
        string='Anticipos Disponibles'
    )

    available_advance_amount = fields.Monetary(
        string='Total Anticipos Disponibles',
        currency_field='currency_id',
        compute='_compute_available_advances'
    )

    show_advance_section = fields.Boolean(
        string='Mostrar Sección Anticipos',
        compute='_compute_available_advances'
    )

    @api.depends('partner_id', 'move_type', 'state')
    def _compute_available_advances(self):
        """Calcula anticipos disponibles para la factura"""
        for move in self:
            if move.move_type in ['out_invoice', 'in_invoice'] and move.partner_id:
                # Buscar anticipos disponibles
                domain = [
                    ('partner_id', '=', move.partner_id.id),
                    ('is_advance', '=', True),
                    ('state', '=', 'posted'),
                    ('advance_balance', '>', 0)
                ]

                if move.move_type == 'out_invoice':
                    domain.append(('payment_type', '=', 'inbound'))
                else:
                    domain.append(('payment_type', '=', 'outbound'))

                advances = self.env['account.payment'].search(domain)
                move.available_advance_ids = advances
                move.available_advance_amount = sum(advances.mapped('advance_balance'))
                move.show_advance_section = bool(advances)
            else:
                move.available_advance_ids = False
                move.available_advance_amount = 0
                move.show_advance_section = False

    def action_apply_advances(self):
        """Aplica anticipos disponibles a la factura"""
        self.ensure_one()

        if not self.available_advance_ids:
            raise UserError(_('No hay anticipos disponibles para aplicar'))

        return {
            'name': _('Aplicar Anticipos'),
            'type': 'ir.actions.act_window',
            'res_model': 'advance.apply.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_invoice_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_available_advance_ids': [(6, 0, self.available_advance_ids.ids)]
            }
        }
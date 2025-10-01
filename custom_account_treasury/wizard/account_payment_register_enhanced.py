# -*- coding: utf-8 -*-
from odoo import Command, models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero, float_round
from collections import defaultdict
import logging

_logger = logging.getLogger(__name__)


class AccountPaymentRegisterEnhanced(models.TransientModel):
    """
    Extensión mejorada del wizard de pagos con soporte completo para:
    - Anticipos y excedentes
    - Transferencias internas multi-moneda
    - Cruces automáticos sin pagos asociados
    - Forzar cuentas desde facturas
    """
    _inherit = 'account.payment.register'

    # === Campos de Configuración ===
    use_payment_lines = fields.Boolean(
        string='Usar Líneas de Pago Detalladas',
        default=True,
        help='Crear líneas detalladas para cada factura'
    )

    create_advance_for_excess = fields.Boolean(
        string='Crear Anticipo con Excedente',
        compute='_compute_create_advance_for_excess',
        store=True,
        readonly=False,
        help='Crear anticipo automático si el pago excede el monto adeudado'
    )

    # === Líneas de Pago ===
    payment_line_ids = fields.One2many(
        'account.payment.register.line',
        'register_id',
        string='Líneas de Pago'
    )

    additional_line_ids = fields.One2many(
        'account.payment.register.additional.line',
        'register_id',
        string='Líneas Adicionales'
    )

    # === Campos de Anticipo ===
    is_advance_payment = fields.Boolean(
        string='Es Anticipo',
        help='Marcar si este pago es un anticipo'
    )

    advance_type_id = fields.Many2one(
        'advance.type',
        string='Tipo de Anticipo'
    )

    advance_account_id = fields.Many2one(
        'account.account',
        string='Cuenta de Anticipo',
        compute='_compute_advance_account',
        store=True,
        readonly=False,
        domain="[('deprecated', '=', False), ('company_ids', '=', company_id)]"
    )

    # === Transferencia Interna ===
    is_internal_transfer = fields.Boolean(
        string='Transferencia Interna',
        compute='_compute_is_internal_transfer',
        store=True
    )

    destination_journal_id = fields.Many2one(
        'account.journal',
        string='Diario Destino',
        domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash')), ('id', '!=', journal_id)]"
    )

    # === Multi-Moneda ===
    manual_currency_rate_active = fields.Boolean(
        string='Aplicar Tipo de Cambio Manual'
    )

    current_exchange_rate = fields.Float(
        string='Tipo de Cambio',
        digits=(12, 12),
        default=1.0,
        compute='_compute_current_exchange_rate',
        store=True,
        readonly=False
    )

    exchange_diff_type = fields.Selection([
        ('native', 'Diferencia Nativa'),
        ('custom', 'Diferencia Personalizada')
    ], string='Tipo de Diferencia de Cambio', default='native')

    # === Forzar Cuenta ===
    force_destination_account = fields.Boolean(
        string='Forzar Cuenta Destino',
        help='Permite forzar una cuenta diferente a la del partner'
    )

    forced_destination_account_id = fields.Many2one(
        'account.account',
        string='Cuenta Forzada',
        domain="[('deprecated', '=', False), ('company_ids', '=', company_id)]"
    )

    # === Campos de Cruce ===
    create_cross_entry = fields.Boolean(
        string='Crear Cruce sin Pago',
        help='Crear solo el cruce contable sin generar un pago'
    )

    # === Métodos Compute ===

    @api.depends('payment_type', 'partner_id')
    def _compute_is_internal_transfer(self):
        """Determina si es transferencia interna."""
        for record in self:
            record.is_internal_transfer = (
                record.payment_type == 'transfer' or
                (not record.partner_id and record.journal_id and record.destination_journal_id)
            )

    @api.depends('payment_difference', 'company_id')
    def _compute_create_advance_for_excess(self):
        """Determina si crear anticipo con excedente."""
        for record in self:
            record.create_advance_for_excess = (
                record.company_id.advance_excess_as_advance and
                record.payment_difference > 0
            )

    @api.depends('partner_type', 'company_id', 'advance_type_id', 'is_advance_payment')
    def _compute_advance_account(self):
        """Calcula la cuenta de anticipo según configuración."""
        for record in self:
            if record.advance_type_id:
                record.advance_account_id = record.advance_type_id.account_id
            elif record.is_advance_payment:
                company = record.company_id
                if record.partner_type == 'customer':
                    record.advance_account_id = company.default_customer_advance_account_id
                elif record.partner_type == 'supplier':
                    record.advance_account_id = company.default_supplier_advance_account_id
                elif record.partner_type == 'employee':
                    record.advance_account_id = company.default_employee_advance_account_id
                else:
                    record.advance_account_id = company.third_party_advance_account_id
            else:
                record.advance_account_id = False

    @api.depends('currency_id', 'company_currency_id', 'payment_date', 'manual_currency_rate_active')
    def _compute_current_exchange_rate(self):
        """Calcula tipo de cambio con opción manual."""
        for record in self:
            if record.manual_currency_rate_active:
                continue

            if record.currency_id and record.currency_id != record.company_currency_id:
                rate = self.env['res.currency']._get_conversion_rate(
                    from_currency=record.company_currency_id,
                    to_currency=record.currency_id,
                    company=record.company_id,
                    date=record.payment_date
                )
                record.current_exchange_rate = 1 / rate if rate else 1.0
            else:
                record.current_exchange_rate = 1.0

    # === Override métodos nativos ===

    @api.depends('line_ids')
    def _compute_from_lines(self):
        """Override para crear líneas de pago al cargar facturas."""
        super()._compute_from_lines()

        for wizard in self:
            if wizard.use_payment_lines and wizard.line_ids:
                wizard._create_payment_lines_from_invoices()

    def _create_payment_lines_from_invoices(self):
        """Crea líneas de pago desde facturas seleccionadas con previsión mejorada."""
        self.ensure_one()

        # Limpiar líneas existentes
        self.payment_line_ids.unlink()

        lines_to_create = []
        total_amount = 0

        # Agrupar líneas por factura para mejor manejo
        invoice_groups = defaultdict(lambda: self.env['account.move.line'])
        for line in self.line_ids:
            invoice_groups[line.move_id] |= line

        for move, lines in invoice_groups.items():
            # Calcular monto total de la factura
            total_residual = sum(abs(l.amount_residual) for l in lines)

            # Calcular monto a pagar
            if self.currency_id == move.currency_id:
                amount_to_pay = total_residual
            else:
                amount_to_pay = move.company_currency_id._convert(
                    total_residual,
                    self.currency_id,
                    self.company_id,
                    self.payment_date
                )

            is_partial = False
            if self.amount and total_amount + amount_to_pay > self.amount:
                amount_to_pay = self.amount - total_amount
                is_partial = True

            if self.force_destination_account and self.forced_destination_account_id:
                account_id = self.forced_destination_account_id.id
            else:
                account_id = lines[0].account_id.id

            lines_to_create.append({
                'register_id': self.id,
                'move_line_ids': [(6, 0, lines.ids)],
                'invoice_id': move.id,
                'partner_id': move.partner_id.id,
                'account_id': account_id,
                'name': move.name or move.ref,
                'invoice_amount': abs(move.amount_total_signed),
                'amount_residual': total_residual,
                'payment_amount': amount_to_pay,
                'is_partial': is_partial,
                'currency_id': self.currency_id.id,
                'invoice_currency_id': move.currency_id.id if move.currency_id else self.company_currency_id.id,
            })

            total_amount += amount_to_pay

            if is_partial:
                break

        # Crear todas las líneas
        if lines_to_create:
            self.payment_line_ids = [(0, 0, vals) for vals in lines_to_create]

        # Actualizar monto si no está establecido
        if not self.amount:
            self.amount = total_amount

    @api.onchange('payment_line_ids', 'additional_line_ids')
    def _onchange_payment_lines(self):
        """Actualizar monto del pago basado en cambios en líneas."""
        if self.payment_line_ids or self.additional_line_ids:
            total = sum(self.payment_line_ids.mapped('payment_amount'))
            total += sum(self.additional_line_ids.mapped('amount'))
            self.amount = total

    @api.onchange('force_destination_account')
    def _onchange_force_destination_account(self):
        """Limpiar cuenta forzada si se desmarca la opción."""
        if not self.force_destination_account:
            self.forced_destination_account_id = False

    # === Métodos de creación de pagos ===

    def action_create_payments(self):
        """Override para manejar todas las opciones de pago."""
        if self.create_cross_entry:
            return self._create_cross_entries()
        elif self.is_internal_transfer and self.destination_journal_id:
            return self._create_internal_transfer()
        else:
            return super().action_create_payments()

    def _create_cross_entries(self):
        """Crear cruces contables sin generar pagos."""
        self.ensure_one()

        moves_to_post = self.env['account.move']

        for line in self.payment_line_ids:
            if not line.payment_amount:
                continue

            # Crear asiento de cruce
            move_vals = {
                'move_type': 'entry',
                'date': self.payment_date,
                'journal_id': self.journal_id.id,
                'ref': _('Cruce: %s') % line.invoice_id.name,
                'line_ids': []
            }

            # Línea de la factura
            invoice_line_vals = {
                'account_id': line.account_id.id,
                'partner_id': line.partner_id.id,
                'name': _('Cruce de %s') % line.invoice_id.name,
                'debit': line.payment_amount if line.invoice_id.move_type in ('out_invoice', 'in_refund') else 0,
                'credit': line.payment_amount if line.invoice_id.move_type in ('in_invoice', 'out_refund') else 0,
            }

            # Línea de contrapartida
            counterpart_account = self.advance_account_id if self.is_advance_payment else self.journal_id.default_account_id
            counterpart_vals = {
                'account_id': counterpart_account.id,
                'partner_id': line.partner_id.id,
                'name': self.communication or _('Cruce'),
                'debit': line.payment_amount if line.invoice_id.move_type in ('in_invoice', 'out_refund') else 0,
                'credit': line.payment_amount if line.invoice_id.move_type in ('out_invoice', 'in_refund') else 0,
            }

            move_vals['line_ids'] = [
                (0, 0, invoice_line_vals),
                (0, 0, counterpart_vals)
            ]

            move = self.env['account.move'].create(move_vals)
            moves_to_post |= move

            # Reconciliar con las líneas originales
            lines_to_reconcile = line.move_line_ids
            lines_to_reconcile |= move.line_ids.filtered(
                lambda l: l.account_id == line.account_id
            )
            lines_to_reconcile.reconcile()

        # Contabilizar todos los asientos
        moves_to_post.action_post()

        # Retornar vista de asientos creados
        if len(moves_to_post) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': moves_to_post.id,
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'list,form',
                'domain': [('id', 'in', moves_to_post.ids)],
            }

    def _create_payment_vals_from_wizard(self, batch_result):
        """Override para agregar campos personalizados."""
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)

        # Agregar tipo de cambio manual
        if self.manual_currency_rate_active:
            payment_vals.update({
                'manual_currency_rate_active': True,
                'current_exchange_rate': self.current_exchange_rate,
                'exchange_diff_type': self.exchange_diff_type,
            })

        # Agregar líneas de pago si están habilitadas
        if self.use_payment_lines and self.payment_line_ids:
            payment_line_vals = []
            for line in self.payment_line_ids:
                if line.payment_amount > 0:
                    line_vals = line._prepare_payment_line_vals()
                    payment_line_vals.append((0, 0, line_vals))

            # Agregar líneas adicionales
            for add_line in self.additional_line_ids:
                if add_line.amount > 0:
                    add_vals = add_line._prepare_payment_line_vals()
                    payment_line_vals.append((0, 0, add_vals))

            if payment_line_vals:
                payment_vals['payment_line_ids'] = payment_line_vals

        # Manejar anticipos
        if self.is_advance_payment:
            payment_vals.update({
                'advance': True,
                'advance_type_id': self.advance_type_id.id if self.advance_type_id else False,
            })

        # Forzar cuenta destino si está configurado
        if self.force_destination_account and self.forced_destination_account_id:
            payment_vals['destination_account_id'] = self.forced_destination_account_id.id

        # Manejar excedentes como anticipos
        if self.create_advance_for_excess and self.payment_difference > 0:
            payment_vals['payment_difference_handling'] = 'reconcile'
            if self.advance_account_id:
                payment_vals['writeoff_account_id'] = self.advance_account_id.id
                payment_vals['writeoff_label'] = _('Anticipo por excedente')

        return payment_vals

    def _create_internal_transfer(self):
        """Crear transferencia interna mejorada."""
        self.ensure_one()

        if not self.destination_journal_id:
            raise UserError(_('Por favor seleccione un diario destino para la transferencia interna.'))

        # Crear pago de salida
        outbound_vals = {
            'payment_type': 'outbound',
            'partner_type': False,
            'partner_id': False,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'date': self.payment_date,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'destination_account_id': self.destination_journal_id.default_account_id.id,
            'ref': self.communication or _('Transferencia Interna'),
            'is_internal_transfer': True,
        }

        # Agregar tipo de cambio manual si está configurado
        if self.manual_currency_rate_active:
            outbound_vals.update({
                'manual_currency_rate_active': True,
                'current_exchange_rate': self.current_exchange_rate,
                'exchange_diff_type': self.exchange_diff_type,
            })

        outbound_payment = self.env['account.payment'].create(outbound_vals)

        # Crear pago de entrada
        dest_currency = self.destination_journal_id.currency_id or self.company_currency_id

        if self.currency_id != dest_currency:
            # Convertir monto para diario destino
            if self.manual_currency_rate_active:
                inbound_amount = self.amount * self.current_exchange_rate
            else:
                inbound_amount = self.currency_id._convert(
                    self.amount,
                    dest_currency,
                    self.company_id,
                    self.payment_date
                )
        else:
            inbound_amount = self.amount

        inbound_vals = {
            'payment_type': 'inbound',
            'partner_type': False,
            'partner_id': False,
            'amount': inbound_amount,
            'currency_id': dest_currency.id,
            'date': self.payment_date,
            'journal_id': self.destination_journal_id.id,
            'company_id': self.company_id.id,
            'destination_account_id': self.journal_id.default_account_id.id,
            'ref': _('Transferencia desde %s') % self.journal_id.name,
            'is_internal_transfer': True,
        }

        inbound_payment = self.env['account.payment'].create(inbound_vals)

        # Vincular ambos pagos
        outbound_payment.paired_internal_transfer_payment_id = inbound_payment
        inbound_payment.paired_internal_transfer_payment_id = outbound_payment

        # Manejar diferencia de cambio si es multi-moneda
        if self.company_id.auto_create_exchange_diff:
            if self.currency_id != self.company_currency_id or dest_currency != self.company_currency_id:
                self._handle_transfer_exchange_difference(outbound_payment, inbound_payment)

        # Contabilizar pagos
        (outbound_payment + inbound_payment).action_post()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'res_id': outbound_payment.id,
        }

    def _handle_transfer_exchange_difference(self, outbound_payment, inbound_payment):
        """Crear entrada de diferencia de cambio para transferencias multi-moneda."""
        # Calcular diferencia en moneda de la compañía
        outbound_company = outbound_payment.amount
        inbound_company = inbound_payment.amount

        if outbound_payment.currency_id != self.company_currency_id:
            outbound_company = outbound_payment.currency_id._convert(
                outbound_payment.amount,
                self.company_currency_id,
                self.company_id,
                self.payment_date
            )

        if inbound_payment.currency_id != self.company_currency_id:
            inbound_company = inbound_payment.currency_id._convert(
                inbound_payment.amount,
                self.company_currency_id,
                self.company_id,
                self.payment_date
            )

        diff = outbound_company - inbound_company

        # Solo crear si la diferencia excede el umbral
        if abs(diff) > self.company_id.exchange_diff_threshold:
            # Determinar cuenta de ganancia/pérdida
            if diff > 0:
                account = self.company_id.expense_currency_exchange_account_id
            else:
                account = self.company_id.income_currency_exchange_account_id

            if not account:
                raise UserError(_('Por favor configure las cuentas de diferencia de cambio en la configuración de la compañía.'))

            # Crear asiento de ajuste
            move_vals = {
                'journal_id': self.company_id.currency_exchange_journal_id.id or self.journal_id.id,
                'date': self.payment_date,
                'ref': _('Diferencia de cambio para transferencia'),
                'line_ids': [
                    (0, 0, {
                        'account_id': self.journal_id.default_account_id.id,
                        'debit': abs(diff) if diff < 0 else 0,
                        'credit': abs(diff) if diff > 0 else 0,
                    }),
                    (0, 0, {
                        'account_id': account.id,
                        'debit': abs(diff) if diff > 0 else 0,
                        'credit': abs(diff) if diff < 0 else 0,
                    }),
                ],
            }

            move = self.env['account.move'].create(move_vals)
            move.action_post()

            # Vincular a los pagos
            outbound_payment.move_diff_ids = [(4, move.id)]
            inbound_payment.move_diff_ids = [(4, move.id)]

    # === Métodos de utilidad ===

    def action_add_additional_line(self):
        """Agregar línea adicional manualmente."""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment.register.additional.line',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_register_id': self.id,
                'default_currency_id': self.currency_id.id,
            }
        }

    def action_load_supplier_invoices(self):
        """Cargar facturas de proveedores pendientes."""
        self.ensure_one()

        if not self.partner_id:
            raise UserError(_('Por favor seleccione un proveedor primero.'))

        domain = [
            ('partner_id', '=', self.partner_id.id),
            ('amount_residual', '!=', 0),
            ('move_id.state', '=', 'posted'),
            ('account_id.account_type', '=', 'liability_payable'),
            ('move_id.move_type', 'in', ('in_invoice', 'in_refund')),
        ]

        move_lines = self.env['account.move.line'].search(domain, order='date_maturity')

        if move_lines:
            self.line_ids = [(6, 0, move_lines.ids)]
            self._create_payment_lines_from_invoices()

        return {'type': 'ir.actions.do_nothing'}


class AccountPaymentRegisterLine(models.TransientModel):
    """Línea de pago del registro mejorada."""
    _name = 'account.payment.register.line'
    _description = 'Línea de Registro de Pago'

    register_id = fields.Many2one(
        'account.payment.register',
        string='Registro',
        required=True,
        ondelete='cascade'
    )

    move_line_ids = fields.Many2many(
        'account.move.line',
        string='Líneas de Diario'
    )

    invoice_id = fields.Many2one('account.move', string='Factura')
    partner_id = fields.Many2one('res.partner', string='Empresa')
    account_id = fields.Many2one('account.account', string='Cuenta')

    name = fields.Char(string='Descripción')

    invoice_amount = fields.Monetary(
        string='Monto Factura',
        currency_field='invoice_currency_id',
        readonly=True
    )

    amount_residual = fields.Monetary(
        string='Monto Adeudado',
        currency_field='currency_id',
        readonly=True
    )

    payment_amount = fields.Monetary(
        string='Monto a Pagar',
        currency_field='currency_id'
    )

    is_partial = fields.Boolean(
        string='Pago Parcial',
        compute='_compute_is_partial',
        store=True
    )

    currency_id = fields.Many2one('res.currency', string='Moneda de Pago')
    invoice_currency_id = fields.Many2one('res.currency', string='Moneda Factura')

    @api.depends('payment_amount', 'amount_residual')
    def _compute_is_partial(self):
        """Verificar si es pago parcial."""
        for line in self:
            line.is_partial = (
                line.payment_amount > 0 and
                line.amount_residual > 0 and
                float_compare(
                    line.payment_amount,
                    line.amount_residual,
                    precision_rounding=line.currency_id.rounding
                ) < 0
            )

    def _prepare_payment_line_vals(self):
        """Preparar valores para crear account.payment.detail."""
        self.ensure_one()

        return {
            'move_line_id': self.move_line_ids[0].id if self.move_line_ids else False,
            'invoice_id': self.invoice_id.id,
            'partner_id': self.partner_id.id,
            'account_id': self.account_id.id,
            'name': self.name,
            'payment_amount': self.payment_amount,
            'currency_id': self.currency_id.id,
            'payment_currency_id': self.currency_id.id,
            'to_pay': True,
            'payment_difference_handling': 'open' if self.is_partial else 'reconcile',
        }


class AccountPaymentRegisterAdditionalLine(models.TransientModel):
    """Línea adicional para el registro de pago."""
    _name = 'account.payment.register.additional.line'
    _description = 'Línea Adicional de Pago'

    register_id = fields.Many2one(
        'account.payment.register',
        string='Registro',
        required=True,
        ondelete='cascade'
    )

    account_id = fields.Many2one(
        'account.account',
        string='Cuenta',
        required=True,
        domain="[('deprecated', '=', False)]"
    )

    partner_id = fields.Many2one('res.partner', string='Empresa')

    name = fields.Char(string='Descripción', required=True)

    amount = fields.Monetary(
        string='Monto',
        currency_field='currency_id',
        required=True
    )

    currency_id = fields.Many2one('res.currency', string='Moneda')

    analytic_distribution = fields.Json(string='Distribución Analítica')

    tax_ids = fields.Many2many('account.tax', string='Impuestos')

    def _prepare_payment_line_vals(self):
        """Preparar valores para crear línea de pago adicional."""
        self.ensure_one()

        return {
            'account_id': self.account_id.id,
            'partner_id': self.partner_id.id if self.partner_id else False,
            'name': self.name,
            'payment_amount': self.amount,
            'currency_id': self.currency_id.id,
            'payment_currency_id': self.currency_id.id,
            'analytic_distribution': self.analytic_distribution,
            'tax_ids': [(6, 0, self.tax_ids.ids)] if self.tax_ids else False,
            'is_main': False,
            'display_type': 'entry',
        }
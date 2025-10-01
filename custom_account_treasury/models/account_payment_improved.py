# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from collections import defaultdict
import logging

_logger = logging.getLogger(__name__)

class AccountPaymentImproved(models.Model):
    """
    Mejoras al modelo account.payment para el módulo custom_account_treasury
    Incluye:
    - Cruce de anticipos mejorado
    - Lógica de reversión de impuestos mejorada
    - Cómputo de impuestos optimizado
    - Creación de líneas mejorada
    - Diferencia cambiaria en asientos cuando no existe
    """
    _inherit = 'account.payment'

    # ========================================================================
    # MÉTODOS DE CRUCE DE ANTICIPOS
    # ========================================================================

    def action_cross_advances_with_invoices(self):
        """
        Permite cruzar anticipos existentes con facturas pendientes de pago.
        Este método identifica anticipos disponibles y los aplica a las facturas
        seleccionadas en el pago.
        """
        self.ensure_one()

        if not self.payment_line_ids:
            raise UserError(_("No hay documentos seleccionados para cruzar con anticipos."))

        # Buscar anticipos disponibles
        advance_lines = self._get_available_advances()

        if not advance_lines:
            raise UserError(_("No hay anticipos disponibles para este partner."))

        # Aplicar anticipos a las líneas de pago
        remaining_advances = advance_lines
        for payment_line in self.payment_line_ids.filtered(lambda l: l.to_pay):
            if not remaining_advances:
                break

            # Aplicar anticipos hasta cubrir el monto de la línea
            amount_to_cover = abs(payment_line.payment_amount)
            for advance_line in remaining_advances:
                if float_compare(amount_to_cover, 0.0, precision_rounding=self.currency_id.rounding) <= 0:
                    break

                advance_amount = abs(advance_line.amount_residual)
                if self.currency_id != self.company_currency_id:
                    advance_amount = self.company_currency_id._convert(
                        advance_amount,
                        self.currency_id,
                        self.company_id,
                        self.date
                    )

                # Aplicar el anticipo (total o parcialmente)
                applied_amount = min(amount_to_cover, advance_amount)

                # Crear línea de aplicación de anticipo
                self._create_advance_application_line(advance_line, applied_amount, payment_line)

                amount_to_cover -= applied_amount

                # Si el anticipo fue aplicado completamente, removerlo de la lista
                if float_compare(applied_amount, advance_amount, precision_rounding=self.currency_id.rounding) >= 0:
                    remaining_advances -= advance_line

        # Recomputar líneas dinámicas
        self._recompute_dynamic_lines_payment()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Anticipos Cruzados'),
                'message': _('Se han aplicado los anticipos disponibles a los documentos seleccionados.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def _get_available_advances(self):
        """
        Obtiene los anticipos disponibles para el partner del pago.
        Busca en cuentas marcadas como anticipos y en tipos de anticipo configurados.
        """
        self.ensure_one()

        # Obtener cuentas de anticipo
        advance_accounts = self._get_advance_accounts()

        # Buscar líneas de anticipo no reconciliadas
        domain = [
            ('partner_id', '=', self.partner_id.commercial_partner_id.id),
            ('account_id', 'in', advance_accounts.ids),
            ('reconciled', '=', False),
            ('amount_residual', '!=', 0),
            ('parent_state', '=', 'posted')
        ]

        # Filtrar por tipo de partner
        if self.partner_type == 'customer':
            domain.append(('balance', '<', 0))  # Anticipos de cliente (créditos)
        else:
            domain.append(('balance', '>', 0))  # Anticipos de proveedor (débitos)

        return self.env['account.move.line'].search(domain, order='date asc')

    def _get_advance_accounts(self):
        """
        Obtiene todas las cuentas configuradas como anticipos.
        Incluye cuentas de tipos de anticipo y cuentas marcadas directamente.
        """
        self.ensure_one()

        accounts = self.env['account.account']

        # Cuentas de tipos de anticipo
        advance_types = self.env['advance.type'].search([
            ('company_ids', 'in', self.company_id.id),
            ('active', '=', True)
        ])
        accounts |= advance_types.mapped('account_id')

        # Cuentas marcadas como anticipos
        accounts |= self.env['account.account'].search([
            ('used_for_advance_payment', '=', True),
            ('company_ids', '=', self.company_id.id)
        ])

        return accounts

    def _create_advance_application_line(self, advance_line, amount, payment_line):
        """
        Crea una línea de aplicación de anticipo en el pago.
        """
        self.ensure_one()

        vals = {
            'payment_id': self.id,
            'move_line_id': advance_line.id,
            'account_id': advance_line.account_id.id,
            'partner_id': advance_line.partner_id.id,
            'payment_amount': amount,
            'currency_id': self.currency_id.id,
            'to_pay': True,
            'display_type': 'advance',
            'name': _('Aplicación de Anticipo %s') % (advance_line.payment_id.code_advance if advance_line.payment_id else advance_line.move_id.name),
            'is_advance_application': True,
        }

        return self.env['account.payment.detail'].create(vals)

    # ========================================================================
    # MÉTODOS DE REVERSIÓN Y CÓMPUTO DE IMPUESTOS
    # ========================================================================

    def _compute_tax_lines_improved(self):
        """
        Cómputo mejorado de líneas de impuestos con soporte para reversión.
        Maneja impuestos normales y revertidos de forma separada.
        """
        self.ensure_one()

        tax_lines = []

        for line in self.payment_line_ids.filtered(lambda l: not l.auto_tax_line):
            if not (line.tax_ids or line.reverse_tax_ids):
                continue

            base_amount = abs(line.payment_amount or line.balance)

            # Procesar impuestos normales
            if line.tax_ids:
                tax_lines.extend(self._compute_tax_for_line(line, line.tax_ids, base_amount, is_refund=False))

            # Procesar impuestos revertidos (para notas de crédito)
            if line.reverse_tax_ids:
                tax_lines.extend(self._compute_tax_for_line(line, line.reverse_tax_ids, base_amount, is_refund=True))

        return tax_lines

    def _compute_tax_for_line(self, line, taxes, base_amount, is_refund=False):
        """
        Calcula las líneas de impuesto para una línea de pago específica.
        """
        tax_lines = []

        for tax in taxes:
            tax_compute = tax.compute_all(
                base_amount,
                currency=line.currency_id or self.currency_id,
                quantity=1,
                product=line.product_id,
                partner=line.partner_id,
                is_refund=is_refund,
                handle_price_include=True,
            )

            for tax_res in tax_compute.get('taxes', []):
                if tax_res.get('id') != tax.id:
                    continue

                tax_amount = tax_res.get('amount', 0.0)
                if is_refund:
                    tax_amount = -tax_amount  # Invertir signo para reversión

                # Determinar cuenta del impuesto
                account_id = tax_res.get('account_id')
                if not account_id and tax.invoice_repartition_line_ids:
                    account_id = tax.invoice_repartition_line_ids[0].account_id.id

                tax_line_vals = {
                    'payment_id': self.id,
                    'partner_id': line.partner_id.id,
                    'account_id': account_id,
                    'name': f"{'Reversión ' if is_refund else ''}{tax_res.get('name', tax.name)}",
                    'payment_amount': tax_amount,
                    'tax_repartition_line_id': tax_res.get('tax_repartition_line_id'),
                    'tax_tag_ids': [(6, 0, tax_res.get('tag_ids', []))],
                    'auto_tax_line': True,
                    'tax_line_id2': tax.id,
                    'tax_base_amount': base_amount,
                    'parent_line_id': line.id,
                    'currency_id': line.currency_id.id or self.currency_id.id,
                    'is_tax_reversal': is_refund,
                }

                # Calcular débito y crédito
                if tax_amount != 0:
                    if self.payment_type == 'inbound':
                        if tax_amount > 0:
                            tax_line_vals['debit'] = abs(tax_amount)
                            tax_line_vals['credit'] = 0
                        else:
                            tax_line_vals['debit'] = 0
                            tax_line_vals['credit'] = abs(tax_amount)
                    else:  # outbound
                        if tax_amount > 0:
                            tax_line_vals['debit'] = 0
                            tax_line_vals['credit'] = abs(tax_amount)
                        else:
                            tax_line_vals['debit'] = abs(tax_amount)
                            tax_line_vals['credit'] = 0

                tax_lines.append(tax_line_vals)

        return tax_lines

    # ========================================================================
    # MÉTODOS DE CREACIÓN DE LÍNEAS MEJORADA
    # ========================================================================

    def _prepare_move_lines_improved(self):
        """
        Preparación mejorada de líneas de asiento con manejo optimizado.
        """
        self.ensure_one()

        lines = []

        # Líneas principales del pago
        if self.payment_line_ids:
            if self.payment_line_mode == 'consolidated':
                lines.extend(self._prepare_consolidated_lines_improved())
            else:
                lines.extend(self._prepare_detailed_lines_improved())

        # Líneas de impuestos
        tax_lines = self._compute_tax_lines_improved()
        lines.extend(tax_lines)

        # Línea de liquidez (banco/caja)
        liquidity_line = self._prepare_liquidity_line_improved()
        if liquidity_line:
            lines.append(liquidity_line)

        # Línea de diferencia si es necesario
        diff_line = self._prepare_difference_line_improved(lines)
        if diff_line:
            lines.append(diff_line)

        return lines

    def _prepare_detailed_lines_improved(self):
        """
        Prepara líneas detalladas con manejo mejorado de impuestos y anticipos.
        """
        lines = []

        for line in self.payment_line_ids.filtered(lambda l: not l.auto_tax_line):
            line_vals = {
                'name': line.name or '/',
                'debit': line.debit,
                'credit': line.credit,
                'balance': line.balance,
                'amount_currency': line.amount_currency or line.balance,
                'account_id': line.account_id.id,
                'partner_id': line.partner_id.commercial_partner_id.id or line.partner_id.id,
                'currency_id': self.currency_id.id if self.currency_id != self.company_currency_id else False,
                'payment_id': self.id,
                'analytic_distribution': line.analytic_distribution,
            }

            # Agregar información de factura si existe
            if line.invoice_id:
                line_vals['invoice_id'] = line.invoice_id.id
            elif line.move_line_id and line.move_line_id.move_id:
                line_vals['invoice_id'] = line.move_line_id.move_id.id

            # Agregar información de línea origen para reconciliación
            if line.move_line_id:
                line_vals['counterpart_line_id'] = line.move_line_id.id

            # Manejo de impuestos (solo si no hay reversión)
            if line.tax_ids and not line.reverse_tax_ids:
                line_vals.update({
                    'tax_ids': [(6, 0, line.tax_ids.ids)],
                    'tax_tag_ids': [(6, 0, line.tax_tag_ids.ids)],
                    'tax_repartition_line_id': line.tax_repartition_line_id.id,
                    'tax_base_amount': line.tax_base_amount,
                })

            lines.append(line_vals)

        return lines

    def _prepare_consolidated_lines_improved(self):
        """
        Prepara líneas consolidadas agrupando por partner y cuenta.
        """
        consolidated = defaultdict(lambda: {
            'debit': 0.0,
            'credit': 0.0,
            'balance': 0.0,
            'amount_currency': 0.0,
            'invoice_ids': [],
            'line_ids': [],
            'tax_ids': set(),
            'analytic_distribution': False,
        })

        for line in self.payment_line_ids.filtered(lambda l: not l.auto_tax_line):
            # Clave de agrupación
            partner_id = line.partner_id.commercial_partner_id.id or line.partner_id.id
            key = (partner_id, line.account_id.id)

            # Acumular valores
            consolidated[key]['debit'] += line.debit
            consolidated[key]['credit'] += line.credit
            consolidated[key]['balance'] += line.balance
            consolidated[key]['amount_currency'] += line.amount_currency or line.balance

            # Agregar referencias
            if line.invoice_id:
                consolidated[key]['invoice_ids'].append(line.invoice_id.id)
            if line.move_line_id:
                consolidated[key]['line_ids'].append(line.move_line_id.id)

            # Agregar impuestos
            if line.tax_ids:
                consolidated[key]['tax_ids'].update(line.tax_ids.ids)

            # Mantener distribución analítica si todas las líneas la tienen
            if line.analytic_distribution and not consolidated[key]['analytic_distribution']:
                consolidated[key]['analytic_distribution'] = line.analytic_distribution

        # Convertir a lista de diccionarios
        lines = []
        for (partner_id, account_id), vals in consolidated.items():
            line_vals = {
                'name': _('Pago consolidado'),
                'debit': vals['debit'],
                'credit': vals['credit'],
                'balance': vals['balance'],
                'amount_currency': vals['amount_currency'],
                'account_id': account_id,
                'partner_id': partner_id,
                'currency_id': self.currency_id.id if self.currency_id != self.company_currency_id else False,
                'payment_id': self.id,
                'analytic_distribution': vals['analytic_distribution'],
            }

            # Agregar referencias múltiples
            if vals['invoice_ids']:
                line_vals['invoice_ids'] = [(6, 0, list(set(vals['invoice_ids'])))]
            if vals['line_ids']:
                line_vals['reconcile_line_ids'] = [(6, 0, vals['line_ids'])]

            # Agregar impuestos consolidados
            if vals['tax_ids']:
                line_vals['tax_ids'] = [(6, 0, list(vals['tax_ids']))]

            lines.append(line_vals)

        return lines

    def _prepare_liquidity_line_improved(self):
        """
        Prepara la línea de liquidez (banco/caja) con manejo mejorado.
        """
        self.ensure_one()

        if not self.outstanding_account_id:
            return None

        # Calcular monto total
        total_amount = self.amount
        if self.payment_type == 'outbound':
            total_amount = -total_amount

        line_vals = {
            'name': self.memo or _('Pago'),
            'account_id': self.outstanding_account_id.id,
            'partner_id': self.partner_id.id,
            'payment_id': self.id,
        }

        # Determinar débito/crédito
        if total_amount > 0:
            line_vals['debit'] = abs(total_amount)
            line_vals['credit'] = 0
        else:
            line_vals['debit'] = 0
            line_vals['credit'] = abs(total_amount)

        line_vals['balance'] = total_amount

        # Monto en moneda si es diferente
        if self.currency_id != self.company_currency_id:
            line_vals['currency_id'] = self.currency_id.id
            line_vals['amount_currency'] = -self.amount if self.payment_type == 'outbound' else self.amount

        return line_vals

    def _prepare_difference_line_improved(self, existing_lines):
        """
        Prepara línea de diferencia para cuadrar el asiento si es necesario.
        """
        self.ensure_one()

        # Calcular totales
        total_debit = sum(l.get('debit', 0) for l in existing_lines)
        total_credit = sum(l.get('credit', 0) for l in existing_lines)

        difference = total_debit - total_credit

        if float_compare(difference, 0.0, precision_rounding=self.company_currency_id.rounding) == 0:
            return None

        # Determinar cuenta de diferencia
        if self.writeoff_account_id:
            diff_account = self.writeoff_account_id
        else:
            if difference > 0:
                diff_account = self.company_id.income_currency_exchange_account_id
            else:
                diff_account = self.company_id.expense_currency_exchange_account_id

        if not diff_account:
            raise UserError(_('Configure las cuentas de diferencia cambiaria en la compañía.'))

        line_vals = {
            'name': _('Diferencia de cambio'),
            'account_id': diff_account.id,
            'partner_id': self.partner_id.id,
            'payment_id': self.id,
        }

        # Aplicar diferencia para cuadrar
        if difference > 0:
            line_vals['debit'] = 0
            line_vals['credit'] = abs(difference)
        else:
            line_vals['debit'] = abs(difference)
            line_vals['credit'] = 0

        line_vals['balance'] = -difference

        return line_vals

    # ========================================================================
    # MÉTODOS DE DIFERENCIA CAMBIARIA
    # ========================================================================

    def _create_exchange_difference_entry(self):
        """
        Crea un asiento de diferencia cambiaria cuando no existe automáticamente.
        Usado cuando exchange_diff_type = 'custom'.
        """
        self.ensure_one()

        if self.exchange_diff_type != 'custom':
            return

        # Calcular diferencias para cada línea
        exchange_lines = []

        for line in self.payment_line_ids:
            if not line.move_line_id:
                continue

            # Calcular diferencia cambiaria
            diff_amount = line._calculate_exchange_difference()

            if float_compare(diff_amount, 0.0, precision_rounding=self.company_currency_id.rounding) == 0:
                continue

            # Determinar cuenta de diferencia
            if diff_amount > 0:
                account = self.company_id.income_currency_exchange_account_id
            else:
                account = self.company_id.expense_currency_exchange_account_id

            if not account:
                raise UserError(_('Configure las cuentas de diferencia cambiaria en la compañía.'))

            # Línea de diferencia
            exchange_lines.append({
                'name': _('Diferencia cambiaria - %s') % line.move_line_id.move_id.name,
                'account_id': account.id,
                'partner_id': line.partner_id.id,
                'debit': abs(diff_amount) if diff_amount > 0 else 0,
                'credit': abs(diff_amount) if diff_amount < 0 else 0,
                'currency_id': self.currency_id.id if self.currency_id != self.company_currency_id else False,
            })

            # Contrapartida
            exchange_lines.append({
                'name': _('Ajuste - %s') % line.move_line_id.move_id.name,
                'account_id': line.account_id.id,
                'partner_id': line.partner_id.id,
                'debit': abs(diff_amount) if diff_amount < 0 else 0,
                'credit': abs(diff_amount) if diff_amount > 0 else 0,
                'currency_id': self.currency_id.id if self.currency_id != self.company_currency_id else False,
            })

        if not exchange_lines:
            return

        # Crear asiento de diferencia
        move_vals = {
            'move_type': 'entry',
            'date': self.date,
            'journal_id': self.company_id.currency_exchange_journal_id.id or self.journal_id.id,
            'ref': _('Diferencia cambiaria - Pago %s') % self.name,
            'line_ids': [(0, 0, line) for line in exchange_lines],
        }

        exchange_move = self.env['account.move'].create(move_vals)
        exchange_move.action_post()

        # Relacionar con el pago
        self.move_diff_ids = [(4, exchange_move.id)]

        return exchange_move

    # ========================================================================
    # OVERRIDE DE MÉTODOS PRINCIPALES
    # ========================================================================

    def action_post(self):
        """
        Override del método action_post con todas las mejoras implementadas.
        """
        # Validaciones previas
        for payment in self:
            # Validar anticipos
            if payment.advance and not payment.advance_type_id:
                raise UserError(_("Los anticipos requieren un tipo de anticipo configurado."))

            # Validar cruce de documentos
            if payment.is_document_cross and not payment._validate_advance_cross():
                raise UserError(_("No hay anticipos disponibles para cruzar."))

        # Procesar líneas de impuestos mejoradas
        for payment in self:
            if payment.payment_line_ids:
                # Recalcular líneas de impuestos con lógica mejorada
                payment._update_tax_lines_improved()

        # Llamar al método padre
        res = super().action_post()

        # Post-procesamiento
        for payment in self:
            # Crear diferencia cambiaria personalizada si es necesario
            if payment.exchange_diff_type == 'custom' and payment.manual_currency_rate_active:
                payment._create_exchange_difference_entry()

            # Procesar cruces de anticipos
            if payment.is_document_cross and payment.advance:
                payment._process_advance_reconciliation()

        return res

    def _update_tax_lines_improved(self):
        """
        Actualiza las líneas de impuestos usando la lógica mejorada.
        """
        self.ensure_one()

        # Eliminar líneas de impuesto existentes
        self.payment_line_ids.filtered('auto_tax_line').unlink()

        # Crear nuevas líneas de impuesto
        tax_lines = self._compute_tax_lines_improved()
        for tax_line_vals in tax_lines:
            self.env['account.payment.detail'].create(tax_line_vals)

    def _process_advance_reconciliation(self):
        """
        Procesa la reconciliación de anticipos con documentos.
        """
        self.ensure_one()

        if not self.move_id:
            return

        # Buscar líneas para reconciliar
        for line in self.move_id.line_ids:
            if not line.account_id.used_for_advance_payment:
                continue

            # Buscar anticipos pendientes
            advance_lines = self.env['account.move.line'].search([
                ('partner_id', '=', line.partner_id.id),
                ('account_id', '=', line.account_id.id),
                ('reconciled', '=', False),
                ('id', '!=', line.id),
                ('parent_state', '=', 'posted')
            ])

            if advance_lines:
                # Reconciliar
                (line | advance_lines).reconcile()


class AccountPaymentDetailImproved(models.Model):
    """
    Mejoras al modelo account.payment.detail
    """
    _inherit = 'account.payment.detail'

    # Campos adicionales para mejoras
    is_advance_application = fields.Boolean(
        string='Es Aplicación de Anticipo',
        default=False
    )

    is_tax_reversal = fields.Boolean(
        string='Es Reversión de Impuesto',
        default=False
    )

    parent_line_id = fields.Many2one(
        'account.payment.detail',
        string='Línea Padre',
        help='Línea de pago de la cual se deriva esta línea de impuesto'
    )

    def _calculate_exchange_difference(self):
        """
        Calcula la diferencia cambiaria para esta línea.
        """
        self.ensure_one()

        if not self.move_line_id or not self.payment_id.manual_currency_rate_active:
            return 0.0

        # Fecha original del documento
        original_date = self.move_line_id.date or self.move_line_id.move_id.date
        payment_date = self.payment_id.date

        if original_date == payment_date:
            return 0.0

        # Monto en moneda de la compañía al tipo de cambio original
        amount_original = self.company_currency_id._convert(
            self.payment_amount,
            self.payment_currency_id,
            self.company_id,
            original_date
        )

        # Monto en moneda de la compañía al tipo de cambio manual
        if self.payment_id.manual_currency_rate:
            amount_manual = self.payment_amount * self.payment_id.manual_currency_rate
        else:
            amount_manual = self.company_currency_id._convert(
                self.payment_amount,
                self.payment_currency_id,
                self.company_id,
                payment_date
            )

        return amount_manual - amount_original
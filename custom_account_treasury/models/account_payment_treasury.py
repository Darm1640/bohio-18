# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountPaymentTreasury(models.Model):
    _inherit = 'account.payment'

    treasury_receipt_number = fields.Char(
        string='Número Recibo Tesorería',
        readonly=True,
        copy=False,
        help='Número consecutivo único de tesorería por tipo de pago'
    )

    treasury_payment_method_number = fields.Char(
        string='Número por Método de Pago',
        readonly=True,
        copy=False,
        help='Número consecutivo según el método de pago utilizado'
    )

    use_treasury_numbering = fields.Boolean(
        string='Usar Numeración de Tesorería',
        default=True,
        help='Si está activo, genera números consecutivos especiales de tesorería'
    )

    treasury_code_prefix = fields.Char(
        string='Código Prefijo',
        compute='_compute_treasury_code_prefix',
        store=True,
        help='Código prefijo basado en el método de pago'
    )

    @api.depends('payment_method_line_id', 'payment_method_line_id.payment_method_id')
    def _compute_treasury_code_prefix(self):
        for payment in self:
            if payment.payment_method_line_id and payment.payment_method_line_id.payment_method_id:
                payment_method = payment.payment_method_line_id.payment_method_id

                # Usar código personalizado si existe
                if hasattr(payment_method, 'treasury_code') and payment_method.treasury_code:
                    payment.treasury_code_prefix = payment_method.treasury_code
                else:
                    # Códigos por defecto
                    payment_code = payment_method.code or ''
                    if payment_code == 'manual':
                        payment.treasury_code_prefix = 'EFE'
                    elif payment_code == 'check_printing':
                        payment.treasury_code_prefix = 'CHQ'
                    elif payment_code in ['electronic', 'batch_payment']:
                        payment.treasury_code_prefix = 'TRANSF'
                    else:
                        payment.treasury_code_prefix = payment_code[:3].upper() if payment_code else 'PAG'
            else:
                payment.treasury_code_prefix = 'PAG'

    @api.model
    def create(self, vals):
        payment = super().create(vals)
        if payment.use_treasury_numbering and not payment.treasury_receipt_number:
            payment._generate_treasury_numbers()
        return payment

    def action_post(self):
        for payment in self:
            if payment.use_treasury_numbering and not payment.treasury_receipt_number:
                payment._generate_treasury_numbers()
        return super().action_post()

    def _generate_treasury_numbers(self):
        """Genera los números consecutivos de tesorería según el tipo y método de pago"""
        for payment in self:
            if payment.treasury_receipt_number:
                continue

            # Número principal según tipo de pago
            if payment.payment_type == 'inbound':
                sequence_code = 'treasury.receipt.inbound'
            elif payment.payment_type == 'outbound':
                sequence_code = 'treasury.receipt.outbound'
            else:  # transfer
                sequence_code = 'treasury.receipt.transfer'

            # Generar número principal de tesorería
            sequence = self.env['ir.sequence'].sudo().search([
                ('code', '=', sequence_code),
                '|',
                ('company_id', '=', payment.company_id.id),
                ('company_id', '=', False)
            ], limit=1)

            if sequence:
                payment.treasury_receipt_number = sequence.next_by_id()

            # Número según método de pago
            payment_method_code = payment.payment_method_line_id.payment_method_id.code

            method_sequence_code = False
            if payment_method_code == 'manual':
                method_sequence_code = 'treasury.payment.cash'
            elif payment_method_code == 'check_printing':
                method_sequence_code = 'treasury.payment.check'
            elif payment_method_code in ['electronic', 'batch_payment']:
                method_sequence_code = 'treasury.payment.transfer'

            if method_sequence_code:
                method_sequence = self.env['ir.sequence'].sudo().search([
                    ('code', '=', method_sequence_code),
                    '|',
                    ('company_id', '=', payment.company_id.id),
                    ('company_id', '=', False)
                ], limit=1)

                if method_sequence:
                    payment.treasury_payment_method_number = method_sequence.next_by_id()

    def name_get(self):
        """Incluye el código del método de pago al inicio del nombre"""
        result = []
        for payment in self:
            code_prefix = payment.treasury_code_prefix or 'PAG'

            # Construir el nombre con el código al inicio
            if payment.treasury_receipt_number:
                name = f"{code_prefix}-{payment.treasury_receipt_number}"
            elif payment.name:
                name = f"{code_prefix}-{payment.name}"
            else:
                name = f"{code_prefix}-{_('Draft Payment')}"

            result.append((payment.id, name))
        return result

    @api.depends('name', 'treasury_receipt_number', 'treasury_code_prefix')
    def _compute_display_name(self):
        for payment in self:
            code_prefix = payment.treasury_code_prefix or 'PAG'

            # Construir el nombre con el código al inicio
            if payment.treasury_receipt_number:
                payment.display_name = f"{code_prefix}-{payment.treasury_receipt_number}"
            elif payment.name:
                payment.display_name = f"{code_prefix}-{payment.name}"
            else:
                payment.display_name = f"{code_prefix}-{_('Draft Payment')}"

class AccountPaymentMethod(models.Model):
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
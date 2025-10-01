# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class TaxRefundLine(models.Model):
    """Líneas de devolución de impuestos"""
    _name = 'account.tax.refund.line'
    _description = 'Línea de Devolución de Impuestos'
    _order = 'sequence, id'

    refund_id = fields.Many2one(
        'account.tax.refund',
        string='Devolución',
        required=True,
        ondelete='cascade',
        index=True
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )

    # Tipo de documento origen
    source_document_type = fields.Selection([
        ('expense', 'Gasto'),
        ('invoice', 'Factura'),
        ('payment', 'Pago'),
        ('manual', 'Manual')
    ],
        string='Tipo Documento Origen',
        required=True,
        default='manual'
    )

    # Referencias a documentos origen
    expense_line_id = fields.Many2one(
        'hr.expense',
        string='Línea de Gasto',
        help='Gasto del cual se solicita devolución'
    )

    invoice_line_id = fields.Many2one(
        'account.move.line',
        string='Línea de Factura',
        domain=[('display_type', '=', False)],
        help='Línea de factura de la cual se solicita devolución'
    )

    payment_line_id = fields.Many2one(
        'account.payment.detail',
        string='Línea de Pago',
        help='Línea de pago de la cual se solicita devolución'
    )

    description = fields.Text(
        string='Descripción',
        required=True
    )

    # Tipo de devolución
    refund_type = fields.Selection([
        ('total', 'Total'),
        ('partial', 'Parcial'),
        ('percentage', 'Porcentaje')
    ],
        string='Tipo de Devolución',
        required=True,
        default='total'
    )

    percentage = fields.Float(
        string='Porcentaje',
        default=0.0,
        help='Porcentaje a devolver cuando el tipo es porcentaje'
    )

    # Montos originales (del documento base)
    original_amount_untaxed = fields.Monetary(
        string='Base Original',
        currency_field='currency_id',
        compute='_compute_original_amounts',
        store=True
    )

    original_amount_tax = fields.Monetary(
        string='Impuesto Original',
        currency_field='currency_id',
        compute='_compute_original_amounts',
        store=True
    )

    original_amount_total = fields.Monetary(
        string='Total Original',
        currency_field='currency_id',
        compute='_compute_original_amounts',
        store=True
    )

    # Montos a devolver
    amount_untaxed = fields.Monetary(
        string='Base a Devolver',
        currency_field='currency_id',
        required=True
    )

    amount_tax = fields.Monetary(
        string='Impuesto a Devolver',
        currency_field='currency_id',
        required=True
    )

    amount_total = fields.Monetary(
        string='Total a Devolver',
        currency_field='currency_id',
        compute='_compute_amount_total',
        store=True
    )

    # Selección de impuestos específicos
    tax_ids = fields.Many2many(
        'account.tax',
        string='Impuestos',
        help='Impuestos específicos a devolver'
    )

    # Cuenta contable para la devolución
    account_id = fields.Many2one(
        'account.account',
        string='Cuenta Contable',
        help='Cuenta contable para registrar la devolución'
    )

    currency_id = fields.Many2one(
        related='refund_id.currency_id',
        string='Moneda',
        store=True
    )

    company_id = fields.Many2one(
        related='refund_id.company_id',
        string='Compañía',
        store=True
    )

    state = fields.Selection(
        related='refund_id.state',
        string='Estado',
        store=True
    )

    # Información adicional
    notes = fields.Text(
        string='Notas'
    )

    @api.depends('expense_line_id', 'invoice_line_id', 'payment_line_id')
    def _compute_original_amounts(self):
        """Calcula los montos originales del documento base"""
        for line in self:
            amount_untaxed = 0.0
            amount_tax = 0.0
            
            if line.source_document_type == 'expense' and line.expense_line_id:
                amount_untaxed = line.expense_line_id.untaxed_amount
                amount_tax = line.expense_line_id.total_amount - line.expense_line_id.untaxed_amount
            
            elif line.source_document_type == 'invoice' and line.invoice_line_id:
                amount_untaxed = line.invoice_line_id.price_subtotal
                amount_tax = line.invoice_line_id.price_total - line.invoice_line_id.price_subtotal
            
            elif line.source_document_type == 'payment' and line.payment_line_id:
                # Para pagos, considerar si tiene impuestos
                if line.payment_line_id.tax_ids:
                    amount_untaxed = line.payment_line_id.balance / (1 + sum(line.payment_line_id.tax_ids.mapped('amount')) / 100)
                    amount_tax = line.payment_line_id.balance - amount_untaxed
                else:
                    amount_untaxed = line.payment_line_id.balance
                    amount_tax = 0.0
            
            line.original_amount_untaxed = amount_untaxed
            line.original_amount_tax = amount_tax
            line.original_amount_total = amount_untaxed + amount_tax

    @api.depends('amount_untaxed', 'amount_tax')
    def _compute_amount_total(self):
        """Calcula el total a devolver"""
        for line in self:
            line.amount_total = line.amount_untaxed + line.amount_tax

    @api.onchange('refund_type', 'percentage', 'original_amount_untaxed', 'original_amount_tax')
    def _onchange_refund_type(self):
        """Calcula los montos según el tipo de devolución"""
        if self.refund_type == 'total':
            self.amount_untaxed = self.original_amount_untaxed
            self.amount_tax = self.original_amount_tax
            self.percentage = 100
        
        elif self.refund_type == 'percentage' and self.percentage:
            self.amount_untaxed = self.original_amount_untaxed * (self.percentage / 100)
            self.amount_tax = self.original_amount_tax * (self.percentage / 100)
        
        elif self.refund_type == 'partial':
            # En modo parcial, el usuario ingresa manualmente los montos
            pass

    @api.onchange('expense_line_id')
    def _onchange_expense_line_id(self):
        """Carga información desde la línea de gasto"""
        if self.expense_line_id:
            self.description = self.expense_line_id.name
            # Cargar impuestos si existen
            if hasattr(self.expense_line_id, 'tax_ids'):
                self.tax_ids = self.expense_line_id.tax_ids

    @api.onchange('invoice_line_id')
    def _onchange_invoice_line_id(self):
        """Carga información desde la línea de factura"""
        if self.invoice_line_id:
            self.description = self.invoice_line_id.name or self.invoice_line_id.product_id.display_name
            self.tax_ids = self.invoice_line_id.tax_ids
            self.account_id = self.invoice_line_id.account_id

    @api.onchange('payment_line_id')
    def _onchange_payment_line_id(self):
        """Carga información desde la línea de pago"""
        if self.payment_line_id:
            self.description = self.payment_line_id.name or self.payment_line_id.ref
            self.tax_ids = self.payment_line_id.tax_ids
            self.account_id = self.payment_line_id.account_id

    @api.constrains('percentage')
    def _check_percentage(self):
        """Valida el porcentaje"""
        for line in self:
            if line.refund_type == 'percentage':
                if line.percentage < 0 or line.percentage > 100:
                    raise ValidationError(_('El porcentaje debe estar entre 0 y 100'))

    @api.constrains('amount_untaxed', 'amount_tax', 'original_amount_untaxed', 'original_amount_tax')
    def _check_amounts(self):
        """Valida que los montos no excedan los originales"""
        for line in self:
            if float_compare(line.amount_untaxed, line.original_amount_untaxed, precision_digits=2) > 0:
                raise ValidationError(_('El monto base a devolver no puede exceder el monto original'))
            
            if float_compare(line.amount_tax, line.original_amount_tax, precision_digits=2) > 0:
                raise ValidationError(_('El monto de impuesto a devolver no puede exceder el impuesto original'))

    def create_payment_line(self, payment):
        """
        Crea una línea de pago para esta devolución
        """
        self.ensure_one()
        
        # Crear línea de pago principal
        line_vals = {
            'payment_id': payment.id,
            'name': self.description,
            'account_id': self.account_id.id if self.account_id else False,
            'partner_id': self.refund_id.partner_id.id,
            'payment_amount': self.amount_total,
            'is_tax_reversal': True,
            'tax_ids': [(6, 0, self.tax_ids.ids)] if self.tax_ids else False,
        }
        
        # Asociar con documento origen
        if self.invoice_line_id:
            line_vals['move_line_id'] = self.invoice_line_id.id
            line_vals['invoice_id'] = self.invoice_line_id.move_id.id
        
        return self.env['account.payment.detail'].create(line_vals)
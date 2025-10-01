# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero
import logging

_logger = logging.getLogger(__name__)


class TaxRefund(models.Model):
    """Modelo para gestionar devoluciones de impuestos"""
    _name = 'account.tax.refund'
    _description = 'Devolución de Impuestos'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Referencia',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default='Nuevo'
    )

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('approved', 'Aprobado'),
        ('paid', 'Pagado'),
        ('cancelled', 'Cancelado')
    ],
        string='Estado',
        default='draft',
        tracking=True
    )

    date = fields.Date(
        string='Fecha',
        required=True,
        default=fields.Date.today,
        tracking=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        required=True,
        default=lambda self: self.env.company.currency_id
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Proveedor/Cliente',
        required=True,
        tracking=True
    )

    refund_type = fields.Selection([
        ('expense', 'Devolución de Gasto'),
        ('tax', 'Devolución de Impuesto'),
        ('mixed', 'Mixto (Gasto + Impuesto)')
    ],
        string='Tipo de Devolución',
        required=True,
        default='tax'
    )

    # Documento base para asociación
    base_document_type = fields.Selection([
        ('expense', 'Gasto'),
        ('invoice', 'Factura'),
        ('payment', 'Pago'),
        ('other', 'Otro')
    ],
        string='Tipo Documento Base',
        required=True
    )

    expense_id = fields.Many2one(
        'hr.expense',
        string='Gasto Relacionado',
        help='Gasto del cual se solicita devolución'
    )

    invoice_id = fields.Many2one(
        'account.move',
        string='Factura Relacionada',
        domain=[('move_type', 'in', ['in_invoice', 'out_invoice'])],
        help='Factura de la cual se solicita devolución'
    )

    payment_id = fields.Many2one(
        'account.payment',
        string='Pago Relacionado',
        help='Pago del cual se solicita devolución'
    )

    # Líneas de devolución
    line_ids = fields.One2many(
        'account.tax.refund.line',
        'refund_id',
        string='Líneas de Devolución',
        copy=True
    )

    # Totales
    amount_untaxed = fields.Monetary(
        string='Base Imponible',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True
    )

    amount_tax = fields.Monetary(
        string='Impuestos',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True
    )

    amount_total = fields.Monetary(
        string='Total',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True
    )

    amount_refunded = fields.Monetary(
        string='Monto Devuelto',
        currency_field='currency_id',
        compute='_compute_amount_refunded',
        store=True
    )

    amount_pending = fields.Monetary(
        string='Monto Pendiente',
        currency_field='currency_id',
        compute='_compute_amount_refunded',
        store=True
    )

    # Pagos de devolución
    payment_refund_ids = fields.One2many(
        'account.payment',
        'tax_refund_id',
        string='Pagos de Devolución'
    )

    payment_count = fields.Integer(
        string='# Pagos',
        compute='_compute_payment_count'
    )

    notes = fields.Text(
        string='Notas'
    )

    @api.depends('line_ids.amount_untaxed', 'line_ids.amount_tax')
    def _compute_amounts(self):
        """Calcula los montos totales"""
        for refund in self:
            amount_untaxed = 0.0
            amount_tax = 0.0
            
            for line in refund.line_ids:
                amount_untaxed += line.amount_untaxed
                amount_tax += line.amount_tax
            
            refund.amount_untaxed = amount_untaxed
            refund.amount_tax = amount_tax
            refund.amount_total = amount_untaxed + amount_tax

    @api.depends('payment_refund_ids', 'payment_refund_ids.state', 'payment_refund_ids.amount')
    def _compute_amount_refunded(self):
        """Calcula el monto devuelto y pendiente"""
        for refund in self:
            amount_refunded = sum(
                refund.payment_refund_ids.filtered(lambda p: p.state == 'posted').mapped('amount')
            )
            refund.amount_refunded = amount_refunded
            refund.amount_pending = refund.amount_total - amount_refunded

    @api.depends('payment_refund_ids')
    def _compute_payment_count(self):
        """Cuenta los pagos de devolución"""
        for refund in self:
            refund.payment_count = len(refund.payment_refund_ids)

    @api.model_create_multi
    def create(self, vals_list):
        """Genera secuencia al crear"""
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('account.tax.refund') or 'Nuevo'
        return super().create(vals_list)

    def action_confirm(self):
        """Confirma la solicitud de devolución"""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('Debe agregar al menos una línea de devolución'))
        
        self.state = 'confirmed'
        self.message_post(body=_('Solicitud de devolución confirmada'))

    def action_approve(self):
        """Aprueba la solicitud de devolución"""
        self.ensure_one()
        self.state = 'approved'
        self.message_post(body=_('Solicitud de devolución aprobada'))

    def action_create_payment(self):
        """Crea el pago de devolución"""
        self.ensure_one()
        
        if self.state != 'approved':
            raise UserError(_('La solicitud debe estar aprobada para crear el pago'))
        
        # Determinar tipo de pago según el tipo de devolución
        if self.refund_type in ['expense', 'tax']:
            payment_type = 'inbound'  # Recibimos dinero
            partner_type = 'supplier'
        else:
            payment_type = 'outbound'  # Devolvemos dinero
            partner_type = 'customer'
        
        return {
            'name': _('Pago de Devolución'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'form',
            'context': {
                'default_tax_refund_id': self.id,
                'default_payment_type': payment_type,
                'default_partner_type': partner_type,
                'default_partner_id': self.partner_id.id,
                'default_amount': self.amount_pending,
                'default_ref': _('Devolución %s') % self.name,
                'default_is_tax_refund': True,
            },
            'target': 'current',
        }

    def action_view_payments(self):
        """Ver pagos de devolución"""
        self.ensure_one()
        return {
            'name': _('Pagos de Devolución'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('tax_refund_id', '=', self.id)],
            'context': {'create': False}
        }

    def action_cancel(self):
        """Cancela la solicitud"""
        self.ensure_one()
        if self.payment_refund_ids.filtered(lambda p: p.state == 'posted'):
            raise UserError(_('No puede cancelar una solicitud con pagos confirmados'))
        
        self.state = 'cancelled'
        self.message_post(body=_('Solicitud de devolución cancelada'))

    def action_draft(self):
        """Regresa a borrador"""
        self.ensure_one()
        if self.payment_refund_ids:
            raise UserError(_('No puede regresar a borrador una solicitud con pagos'))
        
        self.state = 'draft'
        self.message_post(body=_('Solicitud regresada a borrador'))

    @api.onchange('base_document_type')
    def _onchange_base_document_type(self):
        """Limpia los campos de documento según el tipo"""
        if self.base_document_type != 'expense':
            self.expense_id = False
        if self.base_document_type != 'invoice':
            self.invoice_id = False
        if self.base_document_type != 'payment':
            self.payment_id = False

    @api.onchange('expense_id')
    def _onchange_expense_id(self):
        """Carga información desde el gasto"""
        if self.expense_id:
            self.partner_id = self.expense_id.employee_id.partner_id
            # Cargar líneas desde el gasto
            self._load_lines_from_expense()

    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        """Carga información desde la factura"""
        if self.invoice_id:
            self.partner_id = self.invoice_id.partner_id
            self.currency_id = self.invoice_id.currency_id
            # Cargar líneas desde la factura
            self._load_lines_from_invoice()

    def _load_lines_from_expense(self):
        """Carga líneas desde un gasto"""
        self.line_ids = [(5, 0, 0)]  # Limpiar líneas existentes
        
        if not self.expense_id:
            return
        
        # Crear línea desde el gasto
        line_vals = {
            'source_document_type': 'expense',
            'expense_line_id': self.expense_id.id,
            'description': self.expense_id.name,
            'amount_untaxed': self.expense_id.untaxed_amount,
            'amount_tax': self.expense_id.total_amount - self.expense_id.untaxed_amount,
            'refund_type': 'total',
            'percentage': 100,
        }
        
        self.line_ids = [(0, 0, line_vals)]

    def _load_lines_from_invoice(self):
        """Carga líneas desde una factura"""
        self.line_ids = [(5, 0, 0)]  # Limpiar líneas existentes
        
        if not self.invoice_id:
            return
        
        lines = []
        for invoice_line in self.invoice_id.invoice_line_ids.filtered(lambda l: not l.display_type):
            line_vals = {
                'source_document_type': 'invoice',
                'invoice_line_id': invoice_line.id,
                'description': invoice_line.name or invoice_line.product_id.display_name,
                'amount_untaxed': invoice_line.price_subtotal,
                'amount_tax': invoice_line.price_total - invoice_line.price_subtotal,
                'refund_type': 'partial',
                'percentage': 0,
            }
            lines.append((0, 0, line_vals))
        
        self.line_ids = lines
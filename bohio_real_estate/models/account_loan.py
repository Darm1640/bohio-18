# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

class AccountLoan(models.Model):
    _inherit = 'account.loan'

    # Campos de relación con contactos
    partner_id = fields.Many2one(
        'res.partner',
        string='Prestatario/Prestamista',
        tracking=True,
        help='Contacto relacionado con este préstamo (puede ser el prestatario o prestamista)'
    )

    loan_type = fields.Selection([
        ('given', 'Préstamo Otorgado'),
        ('received', 'Préstamo Recibido'),
    ], string='Tipo de Préstamo', tracking=True,
        help='Préstamo Otorgado: La empresa presta dinero al contacto\n'
             'Préstamo Recibido: La empresa recibe dinero del contacto')

    # Campos para facturación
    late_payment_rate = fields.Float(
        string='Tasa de Mora (%)',
        default=2.0,
        help='Porcentaje de interés de mora por cada día de retraso'
    )

    admin_fee = fields.Monetary(
        string='Cuota de Administración',
        currency_field='currency_id',
        help='Cargo fijo por administración del préstamo'
    )

    insurance_fee = fields.Monetary(
        string='Seguro',
        currency_field='currency_id',
        help='Cargo por seguro del préstamo'
    )

    payment_period = fields.Selection([
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('semiannual', 'Semestral'),
        ('annual', 'Anual'),
    ], string='Periodo de Pago', default='monthly', tracking=True)

    auto_generate_invoices = fields.Boolean(
        string='Auto-generar Facturas',
        default=True,
        help='Generar facturas automáticamente según el período de pago'
    )

    # Productos para facturación
    interest_product_id = fields.Many2one(
        'product.product',
        string='Producto: Interés',
        help='Producto usado para facturar intereses del préstamo'
    )

    late_fee_product_id = fields.Many2one(
        'product.product',
        string='Producto: Mora',
        help='Producto usado para facturar intereses de mora'
    )

    admin_fee_product_id = fields.Many2one(
        'product.product',
        string='Producto: Cuota Administración',
        help='Producto usado para facturar cuota de administración'
    )

    insurance_product_id = fields.Many2one(
        'product.product',
        string='Producto: Seguro',
        help='Producto usado para facturar seguro'
    )

    # Relación con facturas
    invoice_ids = fields.One2many(
        'account.move',
        'loan_id',
        string='Facturas',
        help='Facturas generadas para este préstamo'
    )

    invoice_count = fields.Integer(
        string='Nº Facturas',
        compute='_compute_invoice_count'
    )

    # Líneas de pagos especiales
    special_payment_ids = fields.One2many(
        'account.loan.special.payment',
        'loan_id',
        string='Pagos Especiales',
        help='Cuotas extras, pagos anticipados, mora, ajustes, etc.'
    )

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for loan in self:
            loan.invoice_count = len(loan.invoice_ids)

    def action_generate_invoice(self):
        """Generar factura manual para el préstamo"""
        self.ensure_one()

        if not self.partner_id:
            raise UserError(_('Debe asignar un contacto (Prestatario/Prestamista) al préstamo'))

        # Buscar o crear productos si no existen
        self._ensure_loan_products()

        # Preparar valores de factura
        invoice_vals = self._prepare_loan_invoice()

        # Crear factura
        invoice = self.env['account.move'].create(invoice_vals)

        # Mensaje en chatter
        self.message_post(
            body=_('Factura generada: %s') % invoice.name,
            subject=_('Factura de Préstamo')
        )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _ensure_loan_products(self):
        """Asegurar que existan los productos para facturación"""
        Product = self.env['product.product']

        # Producto de interés
        if not self.interest_product_id:
            self.interest_product_id = Product.search([('default_code', '=', 'LOAN_INTEREST')], limit=1)
            if not self.interest_product_id:
                self.interest_product_id = Product.create({
                    'name': 'Interés de Préstamo',
                    'type': 'service',
                    'default_code': 'LOAN_INTEREST',
                    'list_price': 0.0,
                })

        # Producto de mora
        if not self.late_fee_product_id:
            self.late_fee_product_id = Product.search([('default_code', '=', 'LOAN_LATE_FEE')], limit=1)
            if not self.late_fee_product_id:
                self.late_fee_product_id = Product.create({
                    'name': 'Interés de Mora - Préstamo',
                    'type': 'service',
                    'default_code': 'LOAN_LATE_FEE',
                    'list_price': 0.0,
                })

        # Producto administración
        if not self.admin_fee_product_id:
            self.admin_fee_product_id = Product.search([('default_code', '=', 'LOAN_ADMIN')], limit=1)
            if not self.admin_fee_product_id:
                self.admin_fee_product_id = Product.create({
                    'name': 'Cuota de Administración - Préstamo',
                    'type': 'service',
                    'default_code': 'LOAN_ADMIN',
                    'list_price': 0.0,
                })

        # Producto seguro
        if not self.insurance_product_id:
            self.insurance_product_id = Product.search([('default_code', '=', 'LOAN_INSURANCE')], limit=1)
            if not self.insurance_product_id:
                self.insurance_product_id = Product.create({
                    'name': 'Seguro - Préstamo',
                    'type': 'service',
                    'default_code': 'LOAN_INSURANCE',
                    'list_price': 0.0,
                })

    def _prepare_loan_invoice(self):
        """Preparar valores para la factura del préstamo"""
        self.ensure_one()

        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if not journal:
            raise UserError(_('No se encontró un diario de ventas'))

        # Determinar el tipo de factura según el tipo de préstamo
        move_type = 'out_invoice' if self.loan_type == 'given' else 'in_invoice'

        invoice_lines = []

        # Línea de interés (si aplica)
        if self.interest > 0:
            invoice_lines.append((0, 0, {
                'name': f'Interés - {self.name}',
                'product_id': self.interest_product_id.id,
                'quantity': 1,
                'price_unit': self.interest,
            }))

        # Línea de cuota de administración
        if self.admin_fee > 0:
            invoice_lines.append((0, 0, {
                'name': f'Cuota de Administración - {self.name}',
                'product_id': self.admin_fee_product_id.id,
                'quantity': 1,
                'price_unit': self.admin_fee,
            }))

        # Línea de seguro
        if self.insurance_fee > 0:
            invoice_lines.append((0, 0, {
                'name': f'Seguro - {self.name}',
                'product_id': self.insurance_product_id.id,
                'quantity': 1,
                'price_unit': self.insurance_fee,
            }))

        return {
            'move_type': move_type,
            'partner_id': self.partner_id.id,
            'journal_id': journal.id,
            'invoice_date': fields.Date.today(),
            'ref': f'Préstamo: {self.name}',
            'loan_id': self.id,
            'invoice_line_ids': invoice_lines,
        }

    def action_view_invoices(self):
        """Ver facturas del préstamo"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Facturas del Préstamo'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('loan_id', '=', self.id)],
            'context': {'create': False},
        }


class AccountLoanSpecialPayment(models.Model):
    _name = 'account.loan.special.payment'
    _description = 'Línea de Pago Especial de Préstamo'
    _order = 'date desc, id desc'

    loan_id = fields.Many2one(
        'account.loan',
        string='Préstamo',
        required=True,
        ondelete='cascade',
        index=True
    )

    name = fields.Char(
        string='Descripción',
        required=True,
        help='Descripción del pago especial'
    )

    payment_type = fields.Selection([
        ('extra_payment', 'Pago Extraordinario'),
        ('early_payment', 'Pago Anticipado'),
        ('late_fee', 'Mora'),
        ('adjustment', 'Ajuste'),
        ('admin_fee', 'Cuota Administración'),
        ('insurance', 'Seguro'),
        ('other', 'Otro'),
    ], string='Tipo', required=True, default='extra_payment')

    date = fields.Date(
        string='Fecha',
        required=True,
        default=fields.Date.today,
        index=True
    )

    amount = fields.Monetary(
        string='Monto',
        required=True,
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='loan_id.currency_id',
        string='Moneda',
        readonly=True
    )

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('invoiced', 'Facturado'),
        ('paid', 'Pagado'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='draft', tracking=True)

    invoice_id = fields.Many2one(
        'account.move',
        string='Factura',
        copy=False,
        readonly=True,
        help='Factura generada para este pago especial'
    )

    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        help='Producto a usar en la factura'
    )

    notes = fields.Text(
        string='Notas'
    )

    # Campo para cálculo automático de mora
    days_late = fields.Integer(
        string='Días de Retraso',
        help='Número de días de retraso (para cálculo de mora)'
    )

    reference_line_id = fields.Many2one(
        'account.loan.line',
        string='Línea de Referencia',
        help='Línea del préstamo a la que hace referencia este pago'
    )

    def action_confirm(self):
        """Confirmar el pago especial"""
        for payment in self:
            payment.state = 'confirmed'

    def action_generate_invoice(self):
        """Generar factura para este pago especial"""
        self.ensure_one()

        if self.state == 'invoiced':
            raise UserError(_('Este pago especial ya tiene una factura generada'))

        if not self.product_id:
            # Usar producto por defecto según el tipo
            self.product_id = self._get_default_product()

        # Preparar valores de factura
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        move_type = 'out_invoice' if self.loan_id.loan_type == 'given' else 'in_invoice'

        invoice_vals = {
            'move_type': move_type,
            'partner_id': self.loan_id.partner_id.id,
            'journal_id': journal.id,
            'invoice_date': self.date,
            'ref': f'Préstamo: {self.loan_id.name} - {self.name}',
            'loan_id': self.loan_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': self.name,
                'product_id': self.product_id.id,
                'quantity': 1,
                'price_unit': self.amount,
            })],
        }

        # Crear factura
        invoice = self.env['account.move'].create(invoice_vals)

        # Actualizar el pago especial
        self.write({
            'invoice_id': invoice.id,
            'state': 'invoiced'
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _get_default_product(self):
        """Obtener producto por defecto según el tipo de pago"""
        Product = self.env['product.product']

        product_codes = {
            'late_fee': 'LOAN_LATE_FEE',
            'admin_fee': 'LOAN_ADMIN',
            'insurance': 'LOAN_INSURANCE',
            'extra_payment': 'LOAN_EXTRA_PAYMENT',
        }

        code = product_codes.get(self.payment_type, 'LOAN_OTHER')
        product = Product.search([('default_code', '=', code)], limit=1)

        if not product:
            # Crear producto si no existe
            product_names = {
                'late_fee': 'Interés de Mora - Préstamo',
                'admin_fee': 'Cuota de Administración - Préstamo',
                'insurance': 'Seguro - Préstamo',
                'extra_payment': 'Pago Extraordinario - Préstamo',
            }
            name = product_names.get(self.payment_type, 'Otro - Préstamo')

            product = Product.create({
                'name': name,
                'type': 'service',
                'default_code': code,
                'list_price': 0.0,
            })

        return product

    def action_cancel(self):
        """Cancelar el pago especial"""
        for payment in self:
            if payment.state == 'invoiced':
                raise UserError(_('No puede cancelar un pago que ya tiene factura. Cancele primero la factura.'))
            payment.state = 'cancelled'

    def action_set_to_draft(self):
        """Regresar a borrador"""
        for payment in self:
            payment.state = 'draft'


class AccountMove(models.Model):
    _inherit = 'account.move'

    loan_id = fields.Many2one(
        'account.loan',
        string='Préstamo',
        copy=False,
        help='Préstamo relacionado con esta factura'
    )

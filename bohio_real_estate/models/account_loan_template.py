# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountLoanTemplate(models.Model):
    _name = 'account.loan.template'
    _description = 'Plantilla de Préstamo'
    _order = 'sequence, name'

    # Campos básicos
    name = fields.Char(
        string='Nombre de Plantilla',
        required=True,
        help='Nombre descriptivo de la plantilla'
    )

    active = fields.Boolean(
        string='Activo',
        default=True
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de visualización'
    )

    description = fields.Text(
        string='Descripción',
        help='Descripción detallada de la plantilla'
    )

    # Tipo de préstamo
    loan_type = fields.Selection([
        ('given', 'Préstamo Otorgado'),
        ('received', 'Préstamo Recibido'),
    ], string='Tipo de Préstamo', required=True, default='given')

    # Configuración financiera
    duration = fields.Integer(
        string='Duración (meses)',
        default=12,
        help='Duración del préstamo en meses'
    )

    interest_rate = fields.Float(
        string='Tasa de Interés (%)',
        digits=(5, 2),
        help='Tasa de interés anual del préstamo'
    )

    late_payment_rate = fields.Float(
        string='Tasa de Mora (%)',
        default=2.0,
        digits=(5, 2),
        help='Porcentaje de interés de mora por cada día de retraso'
    )

    # Cargos adicionales
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

    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    # Configuración de facturación
    payment_period = fields.Selection([
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('semiannual', 'Semestral'),
        ('annual', 'Anual'),
    ], string='Periodo de Pago', default='monthly')

    auto_generate_invoices = fields.Boolean(
        string='Auto-generar Facturas',
        default=True,
        help='Generar facturas automáticamente según el período de pago'
    )

    # Cuentas contables
    long_term_account_id = fields.Many2one(
        'account.account',
        string='Cuenta Largo Plazo',
        domain="[('account_type', '=', 'liability_non_current')]",
        help='Cuenta contable para la parte del préstamo a largo plazo'
    )

    short_term_account_id = fields.Many2one(
        'account.account',
        string='Cuenta Corto Plazo',
        domain="[('account_type', '=', 'liability_current')]",
        help='Cuenta contable para la parte del préstamo a corto plazo'
    )

    expense_account_id = fields.Many2one(
        'account.account',
        string='Cuenta de Gastos',
        domain="[('account_type', 'in', ['expense', 'expense_depreciation'])]",
        help='Cuenta contable para registrar los gastos de intereses'
    )

    journal_id = fields.Many2one(
        'account.journal',
        string='Diario',
        help='Diario contable para los asientos del préstamo'
    )

    # Productos para facturación
    interest_product_id = fields.Many2one(
        'product.product',
        string='Producto: Interés',
        domain=[('type', '=', 'service')],
        help='Producto usado para facturar intereses del préstamo'
    )

    late_fee_product_id = fields.Many2one(
        'product.product',
        string='Producto: Mora',
        domain=[('type', '=', 'service')],
        help='Producto usado para facturar intereses de mora'
    )

    admin_fee_product_id = fields.Many2one(
        'product.product',
        string='Producto: Cuota Administración',
        domain=[('type', '=', 'service')],
        help='Producto usado para facturar cuota de administración'
    )

    insurance_product_id = fields.Many2one(
        'product.product',
        string='Producto: Seguro',
        domain=[('type', '=', 'service')],
        help='Producto usado para facturar seguro'
    )

    # Configuración de pagos especiales predefinidos
    default_special_payment_ids = fields.One2many(
        'account.loan.template.special.payment',
        'template_id',
        string='Pagos Especiales Predefinidos',
        help='Pagos especiales que se crearán automáticamente al usar esta plantilla'
    )

    # Información adicional
    notes = fields.Html(
        string='Notas',
        help='Notas e instrucciones adicionales para usar esta plantilla'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company,
        required=True
    )

    # Estadísticas
    loan_count = fields.Integer(
        string='Préstamos Creados',
        compute='_compute_loan_count'
    )

    @api.depends('name')
    def _compute_loan_count(self):
        """Contar préstamos creados con esta plantilla"""
        for template in self:
            # Buscar préstamos que tengan referencia a esta plantilla en las notas o nombre
            template.loan_count = 0  # Placeholder - implementar lógica si se necesita tracking

    def action_create_loan_from_template(self):
        """Crear un nuevo préstamo desde esta plantilla"""
        self.ensure_one()

        # Preparar valores del préstamo
        loan_vals = {
            'name': f"Nuevo - {self.name}",
            'loan_type': self.loan_type,
            'duration': self.duration,
            'late_payment_rate': self.late_payment_rate,
            'admin_fee': self.admin_fee,
            'insurance_fee': self.insurance_fee,
            'payment_period': self.payment_period,
            'auto_generate_invoices': self.auto_generate_invoices,
            'currency_id': self.currency_id.id,
        }

        # Agregar cuentas contables si están definidas
        if self.long_term_account_id:
            loan_vals['long_term_account_id'] = self.long_term_account_id.id
        if self.short_term_account_id:
            loan_vals['short_term_account_id'] = self.short_term_account_id.id
        if self.expense_account_id:
            loan_vals['expense_account_id'] = self.expense_account_id.id
        if self.journal_id:
            loan_vals['journal_id'] = self.journal_id.id

        # Agregar productos si están definidos
        if self.interest_product_id:
            loan_vals['interest_product_id'] = self.interest_product_id.id
        if self.late_fee_product_id:
            loan_vals['late_fee_product_id'] = self.late_fee_product_id.id
        if self.admin_fee_product_id:
            loan_vals['admin_fee_product_id'] = self.admin_fee_product_id.id
        if self.insurance_product_id:
            loan_vals['insurance_product_id'] = self.insurance_product_id.id

        # Crear el préstamo
        loan = self.env['account.loan'].create(loan_vals)

        # Crear pagos especiales predefinidos si existen
        if self.default_special_payment_ids:
            for payment_template in self.default_special_payment_ids:
                self.env['account.loan.special.payment'].create({
                    'loan_id': loan.id,
                    'name': payment_template.name,
                    'payment_type': payment_template.payment_type,
                    'amount': payment_template.amount,
                    'product_id': payment_template.product_id.id if payment_template.product_id else False,
                    'notes': payment_template.notes,
                })

        # Retornar acción para abrir el préstamo creado
        return {
            'type': 'ir.actions.act_window',
            'name': _('Préstamo desde Plantilla'),
            'res_model': 'account.loan',
            'res_id': loan.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_loans(self):
        """Ver préstamos creados con esta plantilla"""
        self.ensure_one()
        # Placeholder - implementar si se agrega tracking de plantilla en préstamos
        return {
            'type': 'ir.actions.act_window',
            'name': _('Préstamos'),
            'res_model': 'account.loan',
            'view_mode': 'list,form',
            'domain': [],
            'context': {'default_loan_type': self.loan_type},
        }


class AccountLoanTemplateSpecialPayment(models.Model):
    _name = 'account.loan.template.special.payment'
    _description = 'Pago Especial Predefinido en Plantilla'
    _order = 'sequence, id'

    template_id = fields.Many2one(
        'account.loan.template',
        string='Plantilla',
        required=True,
        ondelete='cascade'
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10
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

    amount = fields.Monetary(
        string='Monto',
        required=True,
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='template_id.currency_id',
        string='Moneda',
        readonly=True
    )

    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        domain=[('type', '=', 'service')],
        help='Producto a usar en la factura'
    )

    notes = fields.Text(
        string='Notas'
    )

    auto_create = fields.Boolean(
        string='Crear Automáticamente',
        default=True,
        help='Crear automáticamente este pago cuando se use la plantilla'
    )

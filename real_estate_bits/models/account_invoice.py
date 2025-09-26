# -*- coding: utf-8 -*-
import datetime
from datetime import date
from dateutil.relativedelta import relativedelta
# from openerp import models, fields, api
# from openerp.exceptions import UserError, ValidationError
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountInvoice(models.Model):
    _inherit = "account.move"

    real_estate_ref = fields.Char("Real Estate Ref.")
    line_id = fields.Many2one("loan.line", "Contract Line")
    destinatario = fields.Selection([
        ('propietario', 'Propietario'),
        ('arrendatario', 'Arrendatario'),
        ('int', 'Intereses'),
        ('ninguno', 'Ninguno'),
    ], string='Tipo de factura Inmobiliaria', default='ninguno')
    sale_commission_id = fields.Many2one('sales.commission', string='Sales Commission',
                                         )
    commission_manager_id = fields.Many2one('sales.commission.line', string='Sales Commission for Manager')
    commission_person_id = fields.Many2one('sales.commission.line', string='Sales Commission for Member')

    @api.model
    def get_category_wise_commission(self):
        sum_line_manager = []
        sum_line_person = []
        amount_person = amount_manager = 0.0
        for order in self:
            for line in order.invoice_line_ids:
                commission_type = line.product_id.categ_id.commission_type
                if commission_type:
                    if line.product_id.categ_id.commission_range_ids:
                        sales_manager_commission = 0.0
                        sales_person_commission = 0.0

                        total = line.price_subtotal
                        if line.move_id.company_id.currency_id != line.move_id.currency_id:
                            amount = line.move_id.currency_id.compute(line.price_subtotal,
                                                                      line.move_id.company_id.currency_id)
                            total = amount

                        for range in line.product_id.categ_id.commission_range_ids:
                            if range.starting_range <= total <= range.ending_range:  # 2500 0 - 5000
                                if commission_type == 'fix':
                                    sales_manager_commission = range.sales_manager_commission_amount
                                    sales_person_commission = range.sales_person_commission_amount
                                else:
                                    sales_manager_commission = (line.price_subtotal *
                                                                range.sales_manager_commission) / 100
                                    sales_person_commission = (line.price_subtotal *
                                                               range.sales_person_commission) / 100

                        sum_line_manager.append(sales_manager_commission)
                        sum_line_person.append(sales_person_commission)

            amount_manager = sum(sum_line_manager)
            amount_person = sum(sum_line_person)
        return amount_person, amount_manager

    def get_product_wise_commission(self):
        sum_line_manager = []
        sum_line_person = []
        amount_person = amount_manager = 0.0
        for order in self:
            for line in order.invoice_line_ids:
                commission_type = line.product_id.commission_type
                if commission_type:
                    if line.product_id.commission_range_ids:
                        sales_manager_commission = 0.0
                        sales_person_commission = 0.0

                        total = line.price_subtotal
                        if line.move_id.company_id.currency_id != line.move_id.currency_id:
                            amount = line.move_id.currency_id.compute(line.price_subtotal,
                                                                      line.move_id.company_id.currency_id)
                            total = amount

                        for range in line.product_id.commission_range_ids:
                            if range.starting_range <= total <= range.ending_range:  # 2500 0 - 5000
                                if commission_type == 'fix':
                                    sales_manager_commission = range.sales_manager_commission_amount
                                    sales_person_commission = range.sales_person_commission_amount
                                else:
                                    sales_manager_commission = (
                                                                       line.price_subtotal * range.sales_manager_commission) / 100
                                    sales_person_commission = (
                                                                      line.price_subtotal * range.sales_person_commission) / 100

                    sum_line_manager.append(sales_manager_commission)
                    sum_line_person.append(sales_person_commission)

            amount_manager = sum(sum_line_manager)
            amount_person = sum(sum_line_person)
        return amount_person, amount_manager

    def get_team_wise_commission(self):
        sum_line_manager = []
        sum_line_person = []
        amount_person = amount_manager = 0.0
        for order in self:
            commission_type = order.team_id.commission_type
            if commission_type:
                if order.team_id.commission_range_ids:
                    sales_manager_commission = 0.0
                    sales_person_commission = 0.0

                    total = order.amount_untaxed
                    if order.company_id.currency_id != order.currency_id:
                        amount = order.currency_id.compute(order.amount_untaxed, order.company_id.currency_id)
                        total = amount
                    for range in order.team_id.commission_range_ids:
                        if total >= range.starting_range and total <= range.ending_range:  # 2500 0 - 5000
                            if commission_type == 'fix':
                                sales_manager_commission = range.sales_manager_commission_amount
                                sales_person_commission = range.sales_person_commission_amount
                            else:
                                sales_manager_commission = (order.amount_untaxed * range.sales_manager_commission) / 100
                                sales_person_commission = (order.amount_untaxed * range.sales_person_commission) / 100

                    amount_manager = sales_manager_commission
                    amount_person = sales_person_commission
        return amount_person, amount_manager

    def create_commission(self, amount, commission, type):
        commission_obj = self.env['sales.commission.line']
        product = self.env['product.product'].search([('is_commission_product', '=', 1)], limit=1)
        for invoice in self:
            date_invoice = invoice.invoice_date
            if not date_invoice:
                date_invoice = fields.Date.context_today(self)
            name_origin = ''
            if invoice.name:
                name_origin = invoice.name
            if invoice.invoice_origin:
                name_origin = name_origin + '-' + invoice.invoice_origin

            if amount != 0.0:
                commission_value = {
                    'amount': amount,
                    'origin': name_origin,
                    'type': type,
                    'product_id': product.id,
                    'date': date_invoice,
                    'src_invoice_id': invoice.id,
                    'sales_commission_id': commission.id,
                    'sales_team_id': invoice.team_id and invoice.team_id.id or False,
                    'company_id': invoice.company_id.id,
                    'currency_id': invoice.company_id.currency_id.id,
                }
                commission_id = commission_obj.create(commission_value)
                if type == 'sales_person':
                    invoice.commission_person_id = commission_id.id
                if type == 'sales_manager':
                    invoice.commission_manager_id = commission_id.id
        return True

    def create_base_commission(self, type):
        commission_obj = self.env['sales.commission']
        product = self.env['product.product'].search([('is_commission_product', '=', 1)], limit=1)
        for order in self:
            if type == 'sales_person':
                user = order.user_id.id
            if type == 'sales_manager':
                user = order.team_id.user_id.id
            first_day_tz, last_day_tz = self.env['sales.commission']._get_utc_start_end_date()

            commission_value = {
                'start_date': first_day_tz,
                'end_date': last_day_tz,
                'product_id': product.id,
                'commission_user_id': user,
                'company_id': order.company_id.id,
                'currency_id': order.currency_id.id,
            }
            commission_id = commission_obj.create(commission_value)
        return commission_id

    def action_post(self):
        res = super(AccountInvoice, self).action_post()
        when_to_pay = self.env.company.when_to_pay
        if when_to_pay == 'invoice_validate':
            for invoice in self:
                commission_based_on = invoice.company_id.commission_based_on if invoice.company_id else self.env.company.commission_based_on
                if invoice.move_type == 'out_invoice':
                    if commission_based_on == 'sales_team':
                        amount_person, amount_manager = invoice.get_team_wise_commission()
                    elif commission_based_on == 'product_category':
                        amount_person, amount_manager = invoice.get_category_wise_commission()
                    elif commission_based_on == 'product_template':
                        amount_person, amount_manager = invoice.get_product_wise_commission()

                    date_invoice = invoice.invoice_date
                    if not date_invoice:
                        date_invoice = fields.Date.context_today(self)

                    commission = self.env['sales.commission'].search([
                        ('commission_user_id', '=', invoice.user_id.id),
                        ('start_date', '<', date_invoice),
                        ('end_date', '>', date_invoice),
                        ('state', '=', 'draft'),
                        ('company_id', '=', invoice.company_id.id),
                    ], limit=1)

                    if not commission:
                        commission = invoice.create_base_commission(type='sales_person')
                    invoice.create_commission(amount_person, commission, type='sales_person')

                    if not invoice.user_id.id == invoice.team_id.user_id.id and invoice.team_id.user_id:
                        commission = self.env['sales.commission'].search([
                            ('commission_user_id', '=', invoice.team_id.user_id.id),
                            ('start_date', '<', date_invoice),
                            ('end_date', '>', date_invoice),
                            ('state', '=', 'draft'),
                            ('company_id', '=', invoice.company_id.id),
                        ], limit=1)
                        if not commission:
                            commission = invoice.create_base_commission(type='sales_manager')
                        invoice.create_commission(amount_manager, commission, type='sales_manager')
        return res

    def button_cancel(self):
        res = super(AccountInvoice, self).button_cancel()
        for rec in self:
            if rec.commission_manager_id:
                rec.commission_manager_id.state = 'exception'
            if rec.commission_person_id:
                rec.commission_person_id.state = 'exception'
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    commissioned = fields.Boolean("Commissioned")


class AccountTax(models.Model):
    _inherit = "account.tax"

    bohio = fields.Boolean('Escenario', default=False)
    
class AccountAccount(models.Model):
    _inherit = "account.account"

    bohio = fields.Boolean('Escenario', default=False)
    
class ContractScenery(models.Model):
    _name = 'contract_scenery.contract_scenery'
    _description = 'Escenario de Contrato'
    _order = 'name'
    _rec_name = 'name'

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    # Moneda heredada de la compañía (solo lectura – útil para campos Monetary)
    currency_id = fields.Many2one(
        related='company_id.currency_id',
        store=True,
        readonly=True,
    )
    code = fields.Char(string='Codigo Escenario', required=True, tracking=True)
    name = fields.Char(string='Nombre', required=True, tracking=True)
    description = fields.Html(string='Descripción')

    income_account_inq = fields.Many2one(
        'account.account',
        string='Cuenta de Ingreso Inquilino',
        required=True,
        check_company=True,
        domain="[('company_ids', '=', company_id), ('deprecated', '=', False)]",
    )
    account_receivable_inq = fields.Many2one(
        'account.account',
        string='Cuenta por Cobrar Inquilino',
        required=True,
        check_company=True,
        domain="[('company_ids', '=', company_id), ('deprecated', '=', False)]",
    )

    income_account_own = fields.Many2one(
        'account.account',
        string='Cuenta de Ingreso Propietario',
        required=True,
        check_company=True,
        domain="[('company_ids', '=', company_id), ('deprecated', '=', False)]",
    )
    account_receivable_own = fields.Many2one(
        'account.account',
        string='Cuenta por Cobrar Propietario',
        required=True,
        check_company=True,
        domain="[('company_ids', '=', company_id), ('deprecated', '=', False)]",
    )

    account_payment_own = fields.Many2one(
        'account.account',
        string='Cuenta de Banco para pagos a Propietarios',
        check_company=True,
        domain="[('company_ids', '=', company_id), ('deprecated', '=', False), ('account_type', '=', 'asset_cash')]",
    )

    credit_limit = fields.Monetary(
        string='Límite de Crédito',
        currency_field='currency_id',
        help='Crédito máximo (en moneda de la compañía) que admite este escenario.',
    )


    inq_tax_ids = fields.Many2many(
        'account.tax',
        'account_tax_contract_esc_inq_rel',  # tabla rel-m2m
        'tax_id', 'esc_id',
        string='Impuestos Inquilinos',
        check_company=True,
        domain="[('company_id', '=', company_id), ('type_tax_use', '=', 'sale'), ('bohio', '=', True)]",
    )
    prop_tax_ids = fields.Many2many(
        'account.tax',
        'account_tax_contract_esc_prop_rel',
        'tax_id', 'esc_id',
        string='Impuestos Propietarios',
        check_company=True,
        domain="[('company_id', '=', company_id), ('type_tax_use', '=', 'sale'), ('bohio', '=', False)]",
    )

    _sql_constraints = [
        ('name_company_unique',
         'unique(name, company_id)',
         'El nombre del escenario debe ser único por compañía.'),
    ]


class ContractOwnerPartner(models.Model):
    _name = 'contract.owner.partner'
    _description = 'Propietario del Contrato'
    _order = 'is_main_owner, id'
    

    partner_id = fields.Many2one("res.partner", "Propietario", required=True)
    product_id = fields.Many2one("product.template", "Propiedad", index=True)
    ownership_percentage = fields.Float("Porcentaje de Propiedad", default=100.0)
    is_main_owner = fields.Boolean("Propietario Principal", default=False)
    start_date = fields.Date("Fecha de Inicio")
    end_date = fields.Date("Fecha de Fin")
    notes = fields.Text("Notas")
    contract_scenery_id = fields.Many2one(
        comodel_name='contract_scenery.contract_scenery',
        string='Escenario')

    @api.constrains('ownership_percentage')
    def _check_ownership_percentage(self):
        for record in self:
            if record.ownership_percentage < 0 or record.ownership_percentage > 100:
                raise UserError("El porcentaje de propiedad debe estar entre 0 y 100")

    @api.model
    def create(self, vals):
        if vals.get('is_main_owner') and vals.get('product_id'):
            existing_main = self.search([
                ('product_id', '=', vals['product_id']),
                ('is_main_owner', '=', True)
            ])
            existing_main.write({'is_main_owner': False})
        return super().create(vals)   
    

    @api.depends('product_id', 'partner_id', 'ownership_percentage')
    def _compute_display_name(self):
        for template in self:
            partner_name = template.partner_id.name or ''
            percentage = template.ownership_percentage or 0
            product_name =  ''
            
            if partner_name and percentage:
                template.display_name = f'[{percentage}% ] {partner_name}'
            elif partner_name:
                template.display_name = f'[{partner_name}] {product_name}'
            else:
                template.display_name = product_name



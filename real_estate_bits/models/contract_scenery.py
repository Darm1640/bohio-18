from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


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
            product_name = ''

            if partner_name and percentage:
                template.display_name = f'[{percentage}% ] {partner_name}'
            elif partner_name:
                template.display_name = f'[{partner_name}] {product_name}'
            else:
                template.display_name = product_name
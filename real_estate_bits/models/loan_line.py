import calendar
import datetime
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from calendar import monthrange
from odoo import api, fields, models
from odoo.exceptions import UserError, AccessError
from odoo.tools.translate import _


class LoanLine(models.Model):
    _name = "loan.line"
    _description = "Loan Line"
    _order = "id"

    name = fields.Char("Name")
    date = fields.Date("Date")
    serial = fields.Integer("#")
    amount = fields.Float("Payment", digits=(16, 2))
    paid = fields.Boolean("Paid")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)

    reservation_id = fields.Many2one("property.reservation", "", ondelete="cascade", readonly=True)
    contract_id = fields.Many2one("property.contract", "", ondelete="cascade", readonly=True)

    partner_id = fields.Many2one('res.partner', string="Partner")
    region_id = fields.Many2one('region.region', string="Region")
    project_id = fields.Many2one('project.worksite', string="Project")
    property_id = fields.Many2one('product.template', string="Property")
    user_id = fields.Many2one('res.users', string="User")

    journal_id = fields.Many2one('account.journal')
    invoice_id = fields.Many2one("account.move", string="Invoice", )
    payment_state = fields.Selection(related="invoice_id.payment_state", readonly=True)
    invoice_state = fields.Selection(related="invoice_id.state", readonly=True)
    amount_residual = fields.Monetary(related="invoice_id.amount_residual", readonly=True)
    currency_id = fields.Many2one(related="invoice_id.currency_id", readonly=True)
    tax_ids = fields.Many2many("account.tax", string="Tax")
    commission = fields.Float("Comisión", digits=(16, 2))
    period_start = fields.Date("Inicio del periodo")
    period_end = fields.Date("Fin del periodo")
    commission_invoice_ids = fields.Many2many('account.move', string='Facturas de Comisión', copy=False)


    def make_invoice(self):
        move_obj = self.env['account.move']
        journal_pool = self.env["account.journal"]
        product_obj = self.env['product.product']

        if not move_obj.check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                raise UserError(_("You do not have access to create or edit invoices"))

        for rec in self:
            contract = rec.contract_id
            scenery = contract.contract_scenery_id

            if not scenery:
                raise UserError(_("¡Establezca un escenario de contrato para este contrato!"))

            if not scenery.income_account_inq:
                raise UserError(_("¡Establezca una cuenta de ingresos en el escenario del contrato!"))

            if not scenery.account_receivable_inq:
                raise UserError(_("¡Establezca una cuenta por cobrar en el escenario del contrato!"))

            journal = journal_pool.search([("type", "=", "sale")], limit=1)
            inv_dict = {
                "move_type": "out_invoice",
                "journal_id": journal.id,
                "partner_id": contract.partner_id.id,
                "line_id": rec.id,
                "destinatario": "arrendatario",
                "invoice_date_due": rec.date,
                "ref": (contract.name + " - " + rec.name),
                "currency_id": self.env.company.currency_id.id,
                "invoice_user_id": self.env.user.id,
                "company_id": self.env.company.id,
                "invoice_line_ids": [],
            }

            # Usar la cuenta por cobrar del escenario
            inv_dict["pay_sell_force_account_id"] = scenery.account_receivable_inq.id

            # Obtener el producto variante
            product_variant = product_obj.search([('product_tmpl_id', '=', contract.property_id.id)], limit=1)
            if not product_variant:
                raise UserError(_("No product variant found for the specified product template!"))

            # Verificar si hay múltiples propietarios
            owners = contract.property_id.owners_lines
            if owners:
                total_percentage = sum(owner.percentage for owner in owners)
                for owner in owners:
                    owner_percentage = owner.percentage / total_percentage
                    owner_amount = rec.amount * owner_percentage
                    if owner.contract_scenery_id:
                        scenery = owners.contract_scenery_id
                    line_vals = self._prepare_invoice_line(rec, product_variant, owner_amount, owner.partner_id, scenery)
                    inv_dict["invoice_line_ids"].append((0, 0, line_vals))
            else:
                # Si no hay propietarios definidos, usar el partner principal del contrato
                line_vals = self._prepare_invoice_line(rec, product_variant, rec.amount, contract.partner_is_owner_id, scenery)
                inv_dict["invoice_line_ids"].append((0, 0, line_vals))

            invoice = move_obj.create(inv_dict)
            self.invoice_id = invoice.id
            self.make_owner_invoice() 

    def _prepare_invoice_line(self, rec, product_variant, amount, partner, scenery):
        self.with_context(manage_partner_in_invoice_lines=True)
        line_vals = {
            "name": f"{rec.contract_id.property_id.name} - {rec.name}",
            "quantity": 1,
            "price_unit": amount,
            "product_id": product_variant.id,
            "partner_id": partner.id,
            #"line_partner_id": partner.id,
            "account_id": scenery.income_account_inq.id,  # Usar la cuenta de ingreso del escenario
        }
        # Usar los impuestos del escenario
        if scenery.inq_tax_ids:
            line_vals.update({"tax_ids": [(6, 0, scenery.inq_tax_ids.ids)]})
        return line_vals

    def make_owner_invoice(self):
        move_obj = self.env['account.move']
        journal_pool = self.env["account.journal"]
        product_obj = self.env['product.product']

        if not move_obj.check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                raise UserError(_("You do not have access to create or edit invoices"))

        for rec in self:
            contract = rec.contract_id
            scenery = contract.contract_scenery_id

            if not scenery:
                raise UserError(_("Please set a contract scenery for this contract!"))

            if not scenery.income_account_own:
                raise UserError(_("Please set an income account for the owner in the contract scenery!"))

            if not scenery.account_receivable_own:
                raise UserError(_("Please set a receivable account for the owner in the contract scenery!"))

            journal = journal_pool.search([("type", "=", "sale")], limit=1)

            # Buscar o crear el producto de comisión
            commission_product = product_obj.search([('default_code', '=', 'COMISION')], limit=1)
            if not commission_product:
                commission_product = product_obj.create({
                    'name': 'COMISION POR ARRIENDO',
                    'type': 'service',
                    'default_code': 'COMISION',
                })

            created_invoices = []

            if contract.partner_is_owner_id and not contract.property_id.owners_lines:
                # Caso de un solo propietario
                owner = contract.partner_is_owner_id
                inv_dict = self._prepare_owner_invoice(rec, contract, scenery, owner, commission_product, rec.commission)
                invoice = move_obj.create(inv_dict)
                created_invoices.append(invoice.id)
            else:
                # Caso de múltiples propietarios
                owners = contract.property_id.owners_lines
                if not owners:
                    raise UserError(_("No owners defined for this property!"))

                total_percentage = sum(owner.percentage for owner in owners)
                for owner in owners:
                    if self.contract_id.is_escenary_propiedad:
                        scenery = owner.contract_scenery_id
                    owner_percentage = owner.percentage / total_percentage
                    commission_amount = rec.commission * owner_percentage
                    inv_dict = self._prepare_owner_invoice(rec, contract, scenery, owner.partner_id, commission_product, commission_amount)
                    invoice = move_obj.create(inv_dict)
                    created_invoices.append(invoice.id)

            # Guardar las facturas creadas en el campo many2many
            rec.commission_invoice_ids = [(6, 0, created_invoices)]

        return True

    def _prepare_owner_invoice(self, rec, contract, scenery, partner, commission_product, amount):
        return {
            "move_type": "out_invoice",
            "journal_id": self.env["account.journal"].search([("type", "=", "sale")], limit=1).id,
            "partner_id": partner.id,
            "line_id": rec.id,
            "destinatario": "propietario",
            "invoice_date_due": rec.date,
            "ref": f"{contract.name} - {rec.name} - Comisión por Arriendo",
            "currency_id": self.env.company.currency_id.id,
            "invoice_user_id": self.env.user.id,
            "company_id": self.env.company.id,
            "pay_sell_force_account_id": scenery.account_receivable_own.id,
            "invoice_line_ids": [(0, 0, {
                "name": f"Comisión por Arriendo: {contract.name} - {rec.name}",
                "quantity": 1,
                "price_unit": amount,
                "product_id": commission_product.id,
                "account_id": scenery.income_account_own.id,
                "tax_ids": [(6, 0, scenery.prop_tax_ids.ids)] if scenery.prop_tax_ids else [],
            })],
        }

    def view_invoice(self):
        # Buscar los registros relacionados
        moves = self.env["account.move"].sudo().search([("line_id", "=", self.id)])
        
        # Si no se encuentra ningún registro, devolver una advertencia
        if not moves:
            return {
                "type": "ir.actions.act_window.message",
                "title": _("No se encontraron registros"),
                "message": _("No se encontraron facturas relacionadas con este registro."),
                "close_button_title": _("Cerrar"),
            }
        
        # Si se encuentra un solo registro, abrir la vista de formulario
        if len(moves) == 1:
            return {
                "name": _("Invoice"),
                "view_type": "form",
                "res_id": moves.id,
                "view_mode": "form",
                "res_model": "account.move",
                "type": "ir.actions.act_window",
                "target": "current",
            }
        
        # Si se encuentran múltiples registros, abrir la vista de lista
        else:
            return {
                "name": _("Invoices"),
                "view_type": "form",
                "view_mode": "list,form",
                "res_model": "account.move",
                "type": "ir.actions.act_window",
                "domain": [("id", "in", moves.ids)],
                "target": "current",
            }

    def send_multiple_installments_rent(self):
        ir_model_data = self.env["ir.model.data"]
        template_id = ir_model_data.get_object_reference(
            "real_estate_bits", "email_template_installment_notification_rent"
        )[1]
        template_res = self.env["mail.template"]
        template = template_res.browse(template_id)
        template.send_mail(self.id, force_send=True)

class AccountMove(models.Model):
    _inherit = 'account.move'

    pay_sell_force_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Forzar cuenta por cobrar o pagar'
    )
    destinatario = fields.Selection([
        ('propietario', 'Propietario'),
        ('arrendatario', 'Arrendatario')], string='Destinatario')
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        super()._onchange_partner_id()
        self._get_change_account()

    @api.onchange('invoice_line_ids')
    def _onchange_quick_edit_line_ids(self):
        super()._onchange_quick_edit_line_ids()
        self._get_change_account()

    @api.onchange('currency_id') 
    def _onchange_currency_change_account(self):
        self._get_change_account()

    def _get_change_account(self):
        if self.journal_id and self.currency_id:
            account_output = False
            if self.pay_sell_force_account_id:
                if self.move_type in ['out_invoice', 'out_refund']:
                    account_output = self.pay_sell_force_account_id
                elif self.move_type in ['in_invoice', 'out_refund']:
                    account_output = self.pay_sell_force_account_id
            if account_output:
                for line in self.line_ids:
                    if line.display_type == 'payment_term':
                        line.update({'account_id': account_output.id})

    def write(self, vals):
        res = super().write(vals)
        for move in self:
            move.with_context(tracking_disable=True)._get_change_account()
        return res
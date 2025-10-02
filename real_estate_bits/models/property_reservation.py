import calendar
import datetime
from datetime import date, datetime, timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from .project_worksite import PROJECT_WORKSITE_TYPE


class PropertyReservation(models.Model):
    _name = "property.reservation"
    _description = "Reserva de Propiedad"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    def _contract_count(self):
        property_contract = self.env["property.contract"]
        for rec in self:
            contract_ids = property_contract.search([("reservation_id", "=", rec.id)])
            rec.contract_count_own = len(contract_ids.filtered(lambda x: x.contract_type == "is_ownership"))
            rec.contract_count_rent = len(contract_ids.filtered(lambda x: x.contract_type == "is_rental"))

    def _deposit_count(self):
        """Cuenta los pagos/depósitos relacionados a la reserva"""
        for rec in self:
            rec.deposit_count = self.env["account.payment"].search_count([
                ("reservation_id", "=", rec.id)
            ])

    account_income = fields.Many2one("account.account", "Cuenta de Ingresos")

    contract_count_own = fields.Integer(compute="_contract_count", string="Ventas")
    contract_count_rent = fields.Integer(compute="_contract_count", string="Arrendamientos")

    deposit_count = fields.Integer(compute="_deposit_count", string="Depósitos")

    # RELACIÓN CON CONTRATO CREADO
    contract_id = fields.Many2one(
        'property.contract',
        string='Contrato Creado',
        help='Contrato generado desde esta reserva'
    )

    # ESTADO DE CONVERSIÓN
    conversion_state = fields.Selection([
        ('pending', 'Pendiente'),
        ('converted', 'Convertida a Contrato'),
        ('sale_order_created', 'Orden de Venta Creada'),
        ('expired', 'Expirada')
    ], string='Estado de Conversión', default='pending', tracking=True)

    # RELACIÓN CON ORDEN DE VENTA
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Orden de Venta',
        help='Orden de venta generada desde esta reserva'
    )

    # Reservation Info
    name = fields.Char("Nombre", size=64, default='New')
    booking_type = fields.Selection([('is_rental', 'Arrendamiento'), ('is_ownership', 'Propiedad')], default='is_rental')
    date = fields.Datetime("Fecha de Reserva", default=fields.Datetime.now())
    maintenance_deposit = fields.Float(string="Depósito de Mantenimiento", required=False)
    payment_type = fields.Selection(string="Tipo de Pago", selection=[("cash", "Efectivo"),
                                                                      ("debit", "Débito")], required=False)
    date_payment = fields.Date("Fecha Primer Pago")

    # Project Info
    project_id = fields.Many2one("project.worksite", "Proyecto")
    project_code = fields.Char("Código de Proyecto", related='project_id.default_code', store=True)

    # Property Info
    type = fields.Selection(selection=PROJECT_WORKSITE_TYPE + [('shop', 'Local')], string="Tipo de Proyecto")
    property_id = fields.Many2one("product.template", "Propiedad", required=True,
                                  domain=[("is_property", "=", True), ("state", "=", "free")])
    property_code = fields.Char("Código de Propiedad", related='property_id.default_code', store=True)
    property_price_type = fields.Selection(related='property_id.property_price_type', store=True)
    price_per_m = fields.Float('Precio Por m²', related='property_id.price_per_unit', store=True)
    property_area = fields.Float("Área de la Propiedad", related='property_id.property_area', store=True)
    floor = fields.Integer("Piso", related='property_id.floor', store=True)
    address = fields.Char("Dirección", related='property_id.address', store=True)
    net_price = fields.Float("Precio de Venta")

    template_id = fields.Many2one("installment.template", "Plantilla de Pago")
    contract_id = fields.Many2one("property.contract", "Contrato de Propiedad")

    property_type_id = fields.Many2one("property.type", "Tipo de Propiedad", related='property_id.property_type_id',
                                       store=True)
    region_id = fields.Many2one("region.region", "Barrio")
    user_id = fields.Many2one("res.users", "Responsable", default=lambda self: self.env.user)
    partner_id = fields.Many2one("res.partner", "Cliente")
    loan_line_ids = fields.One2many("loan.line", "reservation_id")
    state = fields.Selection([("draft", "Borrador"), ("confirmed", "Confirmado"), ("contracted", "Contratado"),
                              ("canceled", "Cancelado")], "Estado", default="draft")
    company_id = fields.Many2one("res.company", string="Compañía", default=lambda self: self.env.company)
    deposit = fields.Float("Depósito", digits=(16, 2), )
    advance_payment_type = fields.Selection([("percentage", "Porcentaje"), ("amount", "Monto")],
                                            "Tipo de Pago Anticipado")

    advance_payment = fields.Float("Pago Anticipado")

    channel_partner_id = fields.Many2one("res.partner")
    channel_partner_commission = fields.Float("Comisión")
    commission_status = fields.Selection([("percentage", "Porcentaje"), ("amount", "Monto")], default="percentage")
    commission_base_amount_selection = fields.Selection(
        [("sales_price", "Precio de Venta"), ("tax_base_amount", "Monto Base de Impuesto")],
        default="sales_price", string="Selección de Monto Base de Comisión")
    commission_base_amount = fields.Float("Monto Base de Comisión", compute="_compute_commission" ,store=True)
    total_commission = fields.Float("Comisión Total", compute="_compute_commission", store=True)

    @api.depends('commission_base_amount_selection', 'commission_status', 'commission_base_amount',
                 'channel_partner_commission')
    def _compute_commission(self):
        if self.commission_base_amount_selection == "tax_base_amount":
            self.commission_base_amount = self.property_id.tax_base_amount
        else:
            self.commission_base_amount = self.property_id.net_price

        if self.commission_status == "percentage":
            self.total_commission = (self.channel_partner_commission * self.commission_base_amount) / 100
        else:
            self.total_commission = self.channel_partner_commission

    def unlink(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("No puede eliminar una reserva que no esté en estado borrador"))
        super(PropertyReservation, self).unlink()

    @api.onchange("property_id")
    def onchange_property(self):
        self.property_type_id = self.property_id.property_type_id.id
        self.project_id = self.property_id.project_worksite_id.id
        self.region_id = self.property_id.region_id.id
        self.net_price = self.property_id.net_price

    def action_draft(self):
        self.write({"state": "draft"})

    def action_cancel(self):
        self.write({"state": "canceled"})
        self.property_id.write({"state": "free"})

    def action_confirm(self):
        if self.name == 'New' or not self.name:
            self.name = self.env["ir.sequence"].next_by_code("property.booking")
        self.write({"state": "confirmed"})
        self.property_id.write({"state": "reserved"})

    def action_receive_deposit(self):
        if not self.deposit:
            raise UserError(_("¡Por favor establezca el monto del depósito!"))

        return {
            "name": _("Pago"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "account.payment",
            "view_id": self.env.ref("account.view_account_payment_form").id,
            "type": "ir.actions.act_window",
            "context": {
                "form_view_initial_mode": "edit",
                "default_payment_type": "inbound",
                "default_partner_type": "customer",
                "default_amount": self.deposit,
                "default_partner_id": self.partner_id.id,
                "default_reservation_id": self.id,
            },
            "target": "current",
        }

    def view_deposits(self):
        """Vista de depósitos/pagos de la reserva"""
        # Usar search_read para obtener solo IDs
        payments_data = self.env["account.payment"].search_read(
            [("reservation_id", "=", self.id)],
            ['id']
        )
        payment_ids = [p['id'] for p in payments_data]

        return {
            "name": _("Depósitos"),
            "domain": [("id", "in", payment_ids)],
            "view_type": "form",
            "view_mode": "list,form",
            "res_model": "account.payment",
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "view_id": False,
            "target": "current",
        }

    def action_contract_ownership(self):
        return {
            "name": _("Ownership Contract"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "property.contract",
            "view_id": self.env.ref("real_estate_bits.view_property_contract_form").id,
            "type": "ir.actions.act_window",
            "context": {
                "form_view_initial_mode": "edit",
                "default_contract_type": "is_ownership",
                "default_project_id": self.project_id.id,
                "default_partner_id": self.partner_id.id,
                "default_property_id": self.property_id.id,
                "default_type": self.type,
                "default_pricing": self.net_price,
                "default_price_per_m": self.price_per_m,
                "default_property_price_type": self.property_price_type,
                "default_reservation_id": self.id,
                "default_deposit": self.deposit,
                "default_advance_payment_type": self.advance_payment_type,
            },
            "target": "current",
        }

    def action_contract_rental(self):
        """Crear contrato desde reserva con valores automáticos"""
        contract = self.env['property.contract'].create_from_reservation(self.id)

        return {
            "name": _("Contrato de Arrendamiento"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "property.contract",
            "res_id": contract.id,
            "type": "ir.actions.act_window",
            "target": "current",
        }

    def action_create_contract_with_template(self):
        """Crear contrato desde reserva usando plantilla"""
        return {
            'name': 'Crear Contrato desde Reserva',
            'type': 'ir.actions.act_window',
            'res_model': 'create.contract.from.reservation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_reservation_id': self.id}
        }

    def action_create_sale_order(self):
        """Generar orden de venta desde reserva"""
        if not self.property_id:
            raise UserError(_("Debe seleccionar una propiedad para generar la orden"))

        # Buscar producto variante de la propiedad
        product_variant = self.env['product.product'].search([
            ('product_tmpl_id', '=', self.property_id.id)
        ], limit=1)

        if not product_variant:
            raise UserError(_("No se encontró variante del producto para la propiedad"))

        # Crear orden de venta
        order_vals = {
            'partner_id': self.partner_id.id,
            'user_id': self.user_id.id,
            'origin': f"Reserva: {self.name}",
            'client_order_ref': self.name,
            'order_line': [(0, 0, {
                'product_id': product_variant.id,
                'product_uom_qty': 1,
                'price_unit': self.amount,
                'name': f"Reserva de {self.property_id.name}",
            })]
        }

        sale_order = self.env['sale.order'].create(order_vals)

        # Relacionar reserva con orden
        self.write({
            'sale_order_id': sale_order.id,
            'state': 'sale_order_created'
        })

        return {
            'name': _('Orden de Venta'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def view_contract_own(self):
        """Vista de contratos de propiedad (ownership)"""
        # Usar search_read para obtener solo IDs
        contracts_data = self.env["property.contract"].search_read(
            [("reservation_id", "=", self.id), ('contract_type', '=', 'is_ownership')],
            ['id']
        )
        contract_ids = [c['id'] for c in contracts_data]

        return {
            "name": _("Contrato de Propiedad"),
            "domain": [("id", "in", contract_ids)],
            "view_type": "form",
            "view_mode": "list,form",
            "res_model": "property.contract",
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "view_id": False,
            "target": "current",
        }

    def view_contract_rent(self):
        """Vista de contratos de arrendamiento"""
        # Usar search_read para obtener solo IDs
        contracts_data = self.env["property.contract"].search_read(
            [("reservation_id", "=", self.id), ('contract_type', '=', "is_rental")],
            ['id']
        )
        contract_ids = [c['id'] for c in contracts_data]

        return {
            "name": _("Contrato de Arrendamiento"),
            "domain": [("id", "in", contract_ids)],
            "view_type": "form",
            "view_mode": "list,form",
            "res_model": "property.contract",
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "view_id": False,
            "target": "current",
        }

    def add_months(self, source_date, months):
        month = source_date.month - 1 + months
        year = int(source_date.year + month / 12)
        month = month % 12 + 1
        day = min(source_date.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)

    def _prepare_lines(self, date_payment):
        loan_line_ids = []
        if self.template_id:
            net_price = self.net_price
            mon = self.template_id.duration_month
            yr = self.template_id.duration_year
            repetition = self.template_id.repetition_rate
            advance_percent = self.template_id.adv_payment_rate
            deduct = self.template_id.deduct
            if not date_payment:
                raise UserError(_("Please select first payment date!"))
            adv_payment = net_price * float(advance_percent) / 100
            if mon > 12:
                x = mon / 12
                mon = (x * 12) + mon % 12
            mons = mon + (yr * 12)
            if adv_payment:
                loan_line_ids.append(
                    (
                        0,
                        0,
                        {
                            "amount": adv_payment,
                            "date": date_payment,
                            "name": _("Advance Payment"),
                        },
                    )
                )
                if deduct:
                    net_price -= adv_payment
            loan_amount = (net_price / float(mons)) * repetition
            m = 0
            i = 2
            while m < mons:
                loan_line_ids.append(
                    (
                        0,
                        0,
                        {
                            "amount": loan_amount,
                            "date": date_payment,
                            "name": _("Loan Installment"),
                        },
                    )
                )
                i += 1
                date_payment = self.add_months(date_payment, repetition)
                m += repetition
        return loan_line_ids

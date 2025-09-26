import calendar
from datetime import date

from dateutil.relativedelta import relativedelta
from calendar import monthrange
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError
from .project_worksite import PROJECT_WORKSITE_TYPE

from odoo import api, fields, models, _, Command
from odoo.tools import format_date, formatLang, frozendict, date_utils
from odoo.tools.float_utils import float_round
import logging

_logger = logging.getLogger(__name__)


def days360(start_date, end_date, method_eu=True):
    """Compute number of days between two dates regarding all months
    as 30-day months"""
    start_day = start_date.day
    start_month = start_date.month
    start_year = start_date.year
    end_day = end_date.day
    end_month = end_date.month
    end_year = end_date.year

    if (
            start_day == 31 or
            (
                method_eu is False and
                start_month == 2 and (
                    start_day == 29 or (
                        start_day == 28 and
                        calendar.isleap(start_year) is False
                    )
                )
            )
    ):
        start_day = 30

    if end_day == 31:
        if method_eu is False and start_day != 30:
            end_day = 1

            if end_month == 12:
                end_year += 1
                end_month = 1
            else:
                end_month += 1
        else:
            end_day = 30
    if end_month == 2 and end_day in (28, 29):
        end_day = 30

    return (
        end_day + end_month * 30 + end_year * 360 -
        start_day - start_month * 30 - start_year * 360 + 1
    )


def add_months(source_date, months):
    month = source_date.month - 1 + months
    year = int(source_date.year + month / 12)
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def subtract_month(date_a, year=0, month=0):
    year, month = divmod(year * 12 + month, 12)
    if date_a.month <= month:
        year = date_a.year - year - 1
        month = date_a.month - month + 12
    else:
        year = date_a.year - year
        month = date_a.month - month
    return date_a.replace(year=year, month=month)


class Contract(models.Model):
    _name = "property.contract"
    _description = "Contrato de Propiedad"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True
    
    def _default_security_deposit_account(self):
        return self.env["ir.config_parameter"].sudo().get_param("real_estate_bits.security_deposit_account")

    def _default_income_account(self):
        return self.env["ir.config_parameter"].sudo().get_param("real_estate_bits.income_account")

    name = fields.Char("Numero", size=64, default='New')
    origin = fields.Char("Documento Fuente", size=64)
    contract_type = fields.Selection([
        ('is_rental', 'Arrendamiento'), 
        ('is_ownership', 'Propiedad')
    ], default='is_rental', string="Tipo de Contrato")
    type = fields.Selection(
        selection=PROJECT_WORKSITE_TYPE + [('shop', 'Tienda')], 
        string="Tipo de Propiedad"
    )
    user_id = fields.Many2one("res.users", "Vendedor", default=lambda self: self.env.user)
    partner_id = fields.Many2one("res.partner", "Inquilino O Propietario", required=True)
    company_id = fields.Many2one("res.company", string="Compañía", default=lambda self: self.env.company)
    
    date = fields.Date("Fecha de Inicio", default=fields.Date.context_today)
    date_from = fields.Date("Fecha de Inicio", required=True, default=fields.Date.context_today)
    date_to = fields.Date("Fecha de Fin")
    date_end = fields.Date("Fecha de Terminación de Contrato")
    date_payment = fields.Date("Fecha del Primer Pago", default=fields.Date.context_today)
    first_invoice_date = fields.Date("Fecha de Primera Factura", default=fields.Date.today(), tracking=True)
    advance_payment_date = fields.Date("Fecha de Pago Anticipado")
    date_maintenance = fields.Date("Fecha de Mantenimiento")
    
    state = fields.Selection([
        ("draft", "Borrador"), 
        ("confirmed", "Confirmado"), 
        ("renew", "Renovado"),
        ("cancel", "Cancelado")
    ], "Estado", default=lambda *a: "draft")
    
    apply_tax = fields.Boolean("Aplicar Impuesto")
    tax_status = fields.Selection([
        ("per_installment", "Por Cuota"), 
        ("tax_base_amount", "Monto Base de Impuesto")
    ], default="per_installment", string="Estado de Impuesto")
    
    reservation_id = fields.Many2one("property.reservation", "Reserva")
    
    paid = fields.Float(compute="_check_amounts", string="Monto Pagado")
    balance = fields.Float(compute="_check_amounts", string="Saldo")
    amount_total = fields.Float(compute="_check_amounts", string="Monto Total")
    
    project_id = fields.Many2one("project.worksite", related="reservation_id.project_id", store=True)
    project_code = fields.Char("Código", related="project_id.default_code", store=True)
    
    property_id = fields.Many2one(
        "product.template", 
        "Propiedad", 
        copy=False, 
        required=True,
        domain=[("is_property", "=", True), ("state", "=", "free")]
    )
    partner_is_owner_id = fields.Many2one(related="property_id.partner_id")
    is_multi_propietario = fields.Boolean(related="property_id.is_multi_owner")
    owners_lines = fields.One2many(related="property_id.owners_lines")
    property_code = fields.Char("Código de Propiedad", related="property_id.default_code", store=True)
    property_area = fields.Float("Área de Propiedad", related="property_id.property_area", store=True)
    price_per_m = fields.Float("Precio Base", related="property_id.price_per_unit", store=True)
    floor = fields.Integer("Piso", related="property_id.floor", store=True)
    address = fields.Char("Dirección", related="property_id.street", store=True)
    
    rent = fields.Integer("Renta (en meses)")
    insurance_fee = fields.Integer("Tarifa de Seguro", required=True)
    rental_fee = fields.Float("Tarifa de Alquiler", compute="_compute_rental_fee", digits=(25, 2), store=True)
    
    contract_scenery_id = fields.Many2one(
        comodel_name='contract_scenery.contract_scenery',
        string='Escenario',
        required=True
    )
    
    loan_line_ids = fields.One2many("loan.line", "contract_id")
    debit_line_ids = fields.One2many(
        "account.debit.term.line",
        "contract_id",
        string="Notas de Débito Programadas",
        help="Configure notas de débito automáticas para intereses"
    )
    region_id = fields.Many2one("region.region", "Región")
    
    account_income = fields.Many2one("account.account", "Cuenta de Ingresos", default=_default_income_account)
    account_security_deposit = fields.Many2one(
        "account.account", 
        "Cuenta de Depósito de Seguridad",
        default=_default_security_deposit_account
    )
    
    voucher_count = fields.Integer("Cantidad de Comprobantes", compute="_voucher_count")
    entry_count = fields.Integer("Cantidad de Entradas", compute="_entry_count")
    
    periodicity = fields.Selection([
        ('1', 'Mensual'),
        ('3', 'Trimestral'),
        ('6', 'Semestral'),
        ('12', 'Anual')
    ], string="Periodicidad", required=True, default='1', tracking=True,
       help="Período entre cada facturación (en meses)")

    recurring_interval = fields.Integer(
        string="Período de Facturación",
        help="Número de períodos",
        required=True,
        default=1,
        tracking=True
    )

    prorata_computation_type = fields.Selection([
        ('none', 'Sin Prorrateo'),
        ('constant_periods', 'Períodos Constantes'),
        ('daily_computation', 'Basado en Días')
    ], string="Tipo de Cálculo", required=True, default='daily_computation', tracking=True,
       help="Método para calcular el prorrateo del primer y último período")
    
    deposit = fields.Float("Depósito")
    deposit_return_status = fields.Selection([
        ('is_deposit_return_manually', 'Devolución de Depósito Manual'), 
        ('is_deposit_return_from_installment', 'Devolución de Depósito Desde Cuota')
    ], default='is_deposit_return_manually', string="Estado de Devolución de Depósito")
    
    rental_agreement = fields.Selection(
        selection=[("per_sft", "Por SFT"), ("fixed", "Monto Fijo")],  
        default="per_sft",
        string="Acuerdo de Alquiler"
    )
    
    increment_recurring_interval = fields.Integer("Intervalo de Incremento Recurrente")
    increment_period = fields.Selection([
        ("months", "Meses"), 
        ("years", "Años")
    ], string="Recurrencia de Incremento", required=True, default="years", tracking=True)
    increment_percentage = fields.Float("Porcentaje de Incremento")
    
    prorate_first_period = fields.Boolean(
        "Prorratear Períodos",
        default=True,
        tracking=True,
        help="Si está activo, el primer y último período se prorratearan según los días reales"
    )
    billing_date = fields.Integer(
        "Día de Facturación",
        default=1,
        tracking=True,
        help="Día del mes en que se genera la factura (1-31)"
    )
    is_escenary_propiedad = fields.Boolean("Usar Escenario de Propiedad", default=False, tracking=True)
    commission_rate = fields.Float("Tasa de Comisión (%)", default=0.0, tracking=True)
    
    pricing = fields.Float("Precio", digits="Product Price")
    template_id = fields.Many2one("installment.template", "Plantilla de Cuotas")
    tax_base_amount = fields.Float("Monto Base de Impuesto", related="property_id.tax_base_amount")
    tax_ids = fields.One2many("price.taxes", "contract_id")
    sales_price = fields.Float("Precio de Venta", compute="_compute_tax_and_ownership_tax")
    
    maintenance = fields.Float(string="Mantenimiento", digits="Product Price")
    maintenance_type = fields.Selection([
        ("percentage", "Porcentaje"), 
        ("amount", "Monto")
    ], string="Tipo de Mantenimiento")
    
    advance_payment_method = fields.Selection([
        ("default", "Predeterminado"), 
        ("custom", "Personalizado")
    ], default='custom', string="Método de Pago Anticipado")
    advance_payment_type = fields.Selection([
        ("percentage", "Porcentaje"), 
        ("amount", "Monto")
    ], default='percentage', string="Tipo de Pago Anticipado")
    advance_payment_rate = fields.Float(
        compute="_compute_advance_payment", 
        string="% de Pago Anticipado", 
        store=True
    )
    advance_payment = fields.Float(
        "Valor de Pago Anticipado", 
        compute="_compute_advance_payment", 
        store=True
    )
    advance_payment_journal_id = fields.Many2one("account.journal", string="Diario de Pago Anticipado")
    advance_payment_payment_id = fields.Many2one("account.payment", string="Pago Anticipado")
    
    descripcion = fields.Text('Descripción')
    contract_use = fields.Selection([
        ('trade', 'Comercial'),
        ('home', 'Vivienda')
    ], string='Uso')

    interest_rate = fields.Float(
        string='Tasa de Interés Mensual (%)',
        default=0.0,
        tracking=True,
        help='Tasa de interés mensual por mora'
    )
    interest_days_grace = fields.Integer(
        string='Días de Gracia',
        default=5,
        tracking=True,
        help='Días de gracia antes de aplicar intereses'
    )
    apply_interest = fields.Boolean(
        string='Aplicar Intereses por Mora',
        default=False,
        tracking=True
    )
    interest_method = fields.Selection([
        ('simple', 'Interés Simple'),
        ('compound', 'Interés Compuesto')
    ], string='Método de Cálculo', default='simple', tracking=True)

    def action_cancel_contract_wizard(self):
        return {
            'name': 'Cancelar Contrato',
            'type': 'ir.actions.act_window',
            'res_model': 'cancel.contract.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_termination_date': self.date_to}
        }

    def action_change_client_wizard(self):
        return {
            'name': 'Cambiar Cliente',
            'type': 'ir.actions.act_window',
            'res_model': 'change.client.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    def action_modify_payment_wizard(self):
        return {
            'name': 'Modificar Pagos',
            'type': 'ir.actions.act_window',
            'res_model': 'modify.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_new_rental_fee': self.rental_fee}
        }

    def action_reactivate_contract_wizard(self):
        return {
            'name': 'Reactivar Contrato',
            'type': 'ir.actions.act_window',
            'res_model': 'reactivate.contract.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    def compute_interest(self, base_amount, days_overdue):
        """
        Calcula el interés por mora de manera simplificada
        :param base_amount: Monto base sobre el cual calcular interés
        :param days_overdue: Días de mora
        :return: Monto de interés calculado
        """
        self.ensure_one()

        if not self.apply_interest or days_overdue <= self.interest_days_grace:
            return 0.0

        effective_days = days_overdue - self.interest_days_grace

        if self.interest_method == 'simple':
            # Interés Simple: I = P * r * t
            # Donde t es en meses (días / 30)
            interest = base_amount * (self.interest_rate / 100) * (effective_days / 30)
        else:
            # Interés Compuesto: A = P * (1 + r)^t - P
            months = effective_days / 30
            interest = base_amount * ((1 + self.interest_rate / 100) ** months - 1)

        return self.company_id.currency_id.round(interest)

    def get_interest_preview_html(self):
        """
        Genera vista previa HTML del cálculo de intereses
        """
        self.ensure_one()

        if not self.apply_interest:
            return "<p class='text-muted'>Los intereses por mora no están activados</p>"

        currency = self.company_id.currency_id
        base_amount = self.rental_fee or 1000.0

        preview_html = "<div class='o_interest_preview'>"
        preview_html += f"<p><strong>Ejemplo de Cálculo de Intereses</strong></p>"
        preview_html += f"<p>Monto base: {formatLang(self.env, base_amount, monetary=True, currency_obj=currency)}</p>"
        preview_html += f"<p>Tasa: {self.interest_rate}% mensual</p>"
        preview_html += f"<p>Días de gracia: {self.interest_days_grace} días</p>"
        preview_html += f"<p>Método: {dict(self._fields['interest_method'].selection).get(self.interest_method)}</p>"
        preview_html += "<table class='table table-sm'>"
        preview_html += "<thead><tr><th>Días Mora</th><th>Interés</th><th>Total</th></tr></thead><tbody>"

        for days in [10, 30, 60, 90]:
            interest = self.compute_interest(base_amount, days)
            total = base_amount + interest
            preview_html += f"<tr>"
            preview_html += f"<td>{days}</td>"
            preview_html += f"<td>{formatLang(self.env, interest, monetary=True, currency_obj=currency)}</td>"
            preview_html += f"<td>{formatLang(self.env, total, monetary=True, currency_obj=currency)}</td>"
            preview_html += f"</tr>"

        preview_html += "</tbody></table></div>"
        return preview_html

    @api.depends('tax_base_amount', 'tax_ids')
    def _compute_tax_and_ownership_tax(self):
        for rec in self:
            rec.sales_price = rec.tax_base_amount + sum(rec.tax_ids.mapped("calculated_tax"))

    @api.depends("loan_line_ids.amount", "loan_line_ids.amount_residual")
    def _check_amounts(self):
        total_paid = 0
        total_non_paid = 0
        amount_total = 0
        for rec in self:
            for line in rec.loan_line_ids:
                amount_total += line.amount
                total_non_paid += line.amount_residual
                total_paid += line.amount - line.amount_residual

            rec.paid = sum(rec.loan_line_ids.filtered(lambda x: x.payment_state == 'paid').mapped('amount'))
            rec.balance = total_non_paid
            rec.amount_total = amount_total

    def _voucher_count(self):
        voucher_obj = self.env["account.payment"]
        voucher_ids = voucher_obj.search([("real_estate_ref", "ilike", self.name)])
        self.voucher_count = len(voucher_ids)

    def _entry_count(self):
        move_obj = self.env["account.move"]
        move_ids = move_obj.search([("rental_id", "in", self.ids)])
        self.entry_count = len(move_ids)

    def auto_rental_invoice(self):
        try:
            rental_pool = self.env["loan.line"]
            rental_line_ids = rental_pool.search([
                ("contract_id.state", "=", "confirmed"),
                ("date", "<=", fields.Date.today())
            ])
            account_move_obj = self.env["account.move"]
            journal_pool = self.env["account.journal"]
            journal = journal_pool.search([("type", "=", "sale")], limit=1)

            for line in rental_line_ids:
                if not line.invoice_id:
                    inv_dict = {
                        "journal_id": journal.id,
                        "partner_id": line.contract_id.partner_id.id,
                        "move_type": "out_invoice",
                        "rental_line_id": line.id,
                        "invoice_date_due": line.date,
                        "ref": (line.contract_id.name + " - " + line.name),
                    }

                    vals = {
                        "name": (line.contract_id.name + " - " + line.name),
                        "quantity": 1,
                        "price_unit": line.amount,
                    }

                    if line.tax_status == 'per_installment':
                        tax_ids = [(6, 0, self.env.company.account_sale_tax_id.ids,)]
                        vals.update({"tax_ids": tax_ids})

                    inv_dict["invoice_line_ids"] = [(0, None, vals)]
                    invoice = account_move_obj.create(inv_dict)
                    invoice.action_post()
                    line.invoice_id = invoice.id
        except:
            return "Error Interno"

    @api.depends("rent", "property_area", "property_id", "rental_agreement")
    def _compute_rental_fee(self):
        for rec in self:
            rec.rental_fee = rec.property_id.rent_value_from

    @api.constrains("recurring_interval")
    def _check_recurring_interval(self):
        for record in self:
            if record.recurring_interval <= 0:
                raise ValidationError(_("El intervalo recurrente debe ser positivo"))

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for contract in self:
            if contract.date_to and contract.date_from > contract.date_to:
                raise ValidationError(_("La fecha de inicio del contrato debe ser menor que la fecha de fin del contrato."))

            if contract.date_from and contract.first_invoice_date:
                if contract.first_invoice_date < contract.date_from:
                    raise ValidationError(_("La fecha de primera factura no puede ser anterior a la fecha de inicio del contrato."))

    @api.constrains('billing_date')
    def _check_billing_date(self):
        for contract in self:
            if contract.billing_date and not (1 <= contract.billing_date <= 31):
                raise ValidationError(_("El día de facturación debe estar entre 1 y 31"))

    @api.constrains('rental_fee')
    def _check_rental_fee(self):
        for contract in self:
            if contract.contract_type == 'is_rental' and contract.rental_fee <= 0:
                raise ValidationError(_("El valor del canon debe ser mayor a cero para contratos de arrendamiento"))

    @api.constrains('increment_percentage', 'increment_recurring_interval')
    def _check_increment(self):
        for contract in self:
            if contract.increment_percentage < 0:
                raise ValidationError(_("El porcentaje de incremento no puede ser negativo"))
            if contract.increment_percentage > 0 and contract.increment_recurring_interval <= 0:
                raise ValidationError(_("Debe especificar un intervalo de incremento válido"))

    @api.constrains('interest_rate', 'interest_days_grace')
    def _check_interest_config(self):
        for contract in self:
            if contract.apply_interest:
                if contract.interest_rate < 0:
                    raise ValidationError(_("La tasa de interés no puede ser negativa"))
                if contract.interest_rate > 50:
                    raise ValidationError(_("La tasa de interés parece muy alta (>50%). Verifique el valor."))
                if contract.interest_days_grace < 0:
                    raise ValidationError(_("Los días de gracia no pueden ser negativos"))

    @api.onchange("contract_type")
    def action_calculate(self):
        if self.contract_type == 'is_rental' and self.rental_fee > 0:
            self.prepare_lines()
        elif self.contract_type == 'is_ownership' and self.pricing > 0:
            self.loan_line_ids = self._prepare_lines(self.date_payment)

    @api.onchange("region_id")
    def onchange_region(self):
        if self.region_id:
            project_ids = self.env["project.worksite"].search([("region_id", "=", self.region_id.id)])
            projects = []
            for u in project_ids:
                projects.append(u.id)
            return {"domain": {"property_id": [("id", "in", projects)]}}

    @api.onchange("project_id")
    def onchange_project(self):
        if self.project_id:
            proper_ids = self.env["product.template"].search([
                ("is_property", "=", True),
                ("project_worksite_id", "=", self.project_id.id),
                ("state", "=", "free")
            ])
            property_ids = []
            for u in proper_ids:
                property_ids.append(u.id)

            project_obj = self.env["project.worksite"].browse(self.project_id.id)
            region = project_obj.region_id.id
            owner = project_obj.partner_id.id
            if project_obj:
                return {
                    "value": {"region": region, "partner_id": owner},
                    "domain": {"property_id": [("id", "in", property_ids)]},
                }

    @api.onchange("property_id")
    def onchange_unit(self):
        self.type = self.property_id.project_type
        self.project_id = self.property_id.project_worksite_id.id
        self.region_id = self.property_id.region_id.id
        self.rental_fee = self.property_id.rental_fee
        self.insurance_fee = self.property_id.insurance_fee

    def generate_entries(self):
        journal_pool = self.env["account.journal"]
        journal = journal_pool.search([("type", "=", "sale")], limit=1)
        if not journal:
            raise UserError(_("¡Por favor configure el diario contable de ventas!"))
        account_move_obj = self.env["account.move"]
        total = 0
        for rec in self:
            if not rec.partner_id.property_account_receivable_id:
                raise UserError(_("¡Por favor configure la cuenta por cobrar para el socio!"))
            if not rec.account_income:
                raise UserError(_("¡Por favor configure la cuenta de ingresos para este contrato!"))
            if rec.insurance_fee and not rec.account_security_deposit:
                raise UserError(_("¡Por favor configure la cuenta de depósito de seguridad para este contrato!"))

            for line in rec.loan_line_ids:
                total += line.amount
            if total <= 0:
                raise UserError(_("¡Monto de alquiler inválido!"))

            account_move_obj.create({
                "ref": rec.name, 
                "journal_id": journal.id, 
                "rental_id": rec.id,
                "line_ids": [
                    (0, 0, {
                        "name": rec.name,
                        "partner_id": rec.partner_id.id,
                        "account_id": rec.partner_id.property_account_receivable_id.id,
                        "debit": total,
                        "credit": 0.0
                    }),
                    (0, 0, {
                        "name": rec.name,
                        "partner_id": rec.partner_id.id,
                        "account_id": rec.account_income.id,
                        "debit": 0.0,
                        "credit": (total - rec.insurance_fee),
                    }),
                    (0, 0, {
                        "name": rec.name,
                        "partner_id": rec.partner_id.id,
                        "account_id": rec.account_security_deposit.id,
                        "debit": 0.0,
                        "credit": rec.insurance_fee,
                    }),
                ]
            })

    def prepare_lines(self):
        """Genera las líneas de cobro de canon usando lógica similar a account_asset"""
        self.ensure_one()
        self.loan_line_ids = False
        rental_lines = []

        if not (self.periodicity and self.date_from and self.date_to and self.first_invoice_date):
            return

        # Fecha de inicio efectiva
        start_date = max(self.date_from, self.first_invoice_date)
        end_date = self.date_to
        rental_fee = self.rental_fee
        period_months = int(self.periodicity)

        if not rental_fee or rental_fee <= 0:
            raise ValidationError(_("El valor del canon debe ser mayor a cero"))

        current_date = start_date
        serial = 1

        # Variables para incrementos
        last_increment_date = start_date
        current_rental_fee = rental_fee

        while current_date <= end_date:
            # Calcular período
            period_start = current_date
            period_end = self._get_period_end_date(current_date, period_months, end_date)

            # Calcular monto prorrateado
            if serial == 1 and self.prorate_first_period:
                # Primer período con prorrateo
                prorated_amount = self._compute_prorated_amount(
                    period_start, period_end, current_rental_fee, is_first=True
                )
            elif period_end >= end_date and self.prorate_first_period:
                # Último período con prorrateo
                prorated_amount = self._compute_prorated_amount(
                    period_start, period_end, current_rental_fee, is_last=True
                )
            else:
                # Período completo
                prorated_amount = current_rental_fee

            # Aplicar incremento si corresponde
            if self.increment_recurring_interval and self.increment_percentage:
                months_since_increment = self._get_months_between(last_increment_date, period_start)
                increment_interval_months = self.increment_recurring_interval * (12 if self.increment_period == 'years' else 1)

                if months_since_increment >= increment_interval_months:
                    current_rental_fee = current_rental_fee * (1 + self.increment_percentage / 100)
                    prorated_amount = current_rental_fee
                    last_increment_date = period_start

            # Calcular comisión
            commission = prorated_amount * (self.commission_rate / 100) if self.commission_rate else 0

            # Fecha de facturación (día específico del mes siguiente o día de corte)
            invoice_date = self._get_invoice_date(period_end)

            rental_lines.append((0, 0, {
                "serial": serial,
                "amount": self.company_id.currency_id.round(prorated_amount),
                "date": invoice_date,
                "name": _("Canon período %s - %s") % (
                    period_start.strftime('%d/%m/%Y'),
                    period_end.strftime('%d/%m/%Y')
                ),
                "commission": self.company_id.currency_id.round(commission),
                "period_start": period_start,
                "period_end": period_end,
            }))

            # Avanzar al siguiente período
            current_date = period_end + relativedelta(days=1)
            serial += 1

            # Prevenir loops infinitos
            if serial > 1000:
                raise ValidationError(_("Se excedió el límite de períodos (1000). Verifique las fechas del contrato."))

        self.write({"loan_line_ids": rental_lines})

    def _get_period_end_date(self, start_date, period_months, contract_end_date):
        """Calcula la fecha de fin del período"""
        period_end = start_date + relativedelta(months=period_months, days=-1)
        return min(period_end, contract_end_date)

    def _get_invoice_date(self, period_end_date):
        """Calcula la fecha de facturación basada en billing_date"""
        if self.billing_date and self.billing_date > 0:
            try:
                invoice_date = period_end_date.replace(day=self.billing_date)
                if invoice_date < period_end_date:
                    invoice_date = invoice_date + relativedelta(months=1)
                return invoice_date
            except ValueError:
                # Si el día no existe en el mes (ej: 31 en febrero)
                invoice_date = period_end_date + relativedelta(months=1, day=1)
                return invoice_date
        else:
            # Por defecto, primer día del mes siguiente
            return period_end_date + relativedelta(months=1, day=1)

    def _compute_prorated_amount(self, period_start, period_end, base_amount, is_first=False, is_last=False):
        """Calcula el monto prorrateado según el tipo de cálculo"""
        if self.prorata_computation_type == 'none':
            return base_amount

        if self.prorata_computation_type == 'daily_computation':
            # Cálculo basado en días reales
            days_in_period = (period_end - period_start).days + 1
            total_days_in_month = monthrange(period_start.year, period_start.month)[1]
            return base_amount * (days_in_period / total_days_in_month)

        elif self.prorata_computation_type == 'constant_periods':
            # Cálculo basado en días 360 (30 días por mes)
            days_in_period = days360(period_start, period_end)
            return (base_amount / 30) * days_in_period

        return base_amount

    def _get_months_between(self, start_date, end_date):
        """Calcula meses entre dos fechas"""
        return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)

    def days_between(self, start_date, end_date):
        s1, e1 = start_date, end_date + timedelta(days=1)
        s360 = (s1.year * 12 + s1.month) * 30 + s1.day
        e360 = (e1.year * 12 + e1.month) * 30 + e1.day
        res = divmod(e360 - s360, 30)
        return ((res[0] * 30) + res[1]) or 0

    @api.onchange("reservation_id")
    def onchange_reservation(self):
        self.project_id = self.reservation_id.project_id.id
        self.region_id = self.reservation_id.region_id.id
        self.partner_id = self.reservation_id.partner_id.id
        self.property_id = self.reservation_id.property_id.id
        self.address = self.reservation_id.address
        self.floor = self.reservation_id.floor
        self.pricing = self.reservation_id.net_price
        self.date_payment = self.reservation_id.date_payment
        self.template_id = self.reservation_id.template_id.id
        self.type = self.reservation_id.type
        self.property_area = self.reservation_id.property_area

    def action_receive_deposit(self):
        if not self.advance_payment_journal_id:
            raise UserError(_("¡Por favor configure el Diario de Pago Anticipado!"))
        if not self.advance_payment_date:
            raise UserError(_("¡Por favor configure la Fecha de Pago Anticipado!"))
        
        custom_adv_payment = self.advance_payment
        rec = self.env["account.payment"].create({
            "payment_type": "inbound",
            "partner_type": "customer",
            "amount": custom_adv_payment,
            "partner_id": self.partner_id.id,
            "date": self.advance_payment_date,
        })
        rec.action_post()
        self.advance_payment_payment_id = rec.id

    @api.depends("template_id", "advance_payment_type", "advance_payment_method")
    def _compute_advance_payment(self):
        if self.advance_payment_method == 'default':
            self.advance_payment_type = "percentage"
            self.advance_payment_rate = self.template_id.adv_payment_rate
            self.advance_payment = self.pricing * float(self.advance_payment_rate) / 100
        else:
            if self.advance_payment_type == "percentage":
                self.advance_payment = self.pricing * float(self.advance_payment_rate) / 100

    def _prepare_lines(self, date_payment):
        self.loan_line_ids = None
        loan_lines = []
        if self.template_id:
            ind = 1
            pricing = self.pricing
            custom_adv_payment = self.advance_payment

            mon = self.template_id.duration_month
            yr = self.template_id.duration_year
            repetition = self.template_id.repetition_rate
            advance_percent = self.template_id.adv_payment_rate
            deduct = self.template_id.deduct
            
            if not date_payment:
                raise UserError(_("¡Por favor seleccione la fecha del primer pago!"))
            
            adv_payment = self.advance_payment
            if mon > 12:
                x = mon / 12
                mon = (x * 12) + mon % 12
            mons = mon + (yr * 12)
            
            if adv_payment:
                loan_lines.append((0, 0, {
                    "name": _("Pago Anticipado"),
                    "serial": ind,
                    "journal_id": int(
                        self.env["ir.config_parameter"].sudo().get_param("real_estate_bits.income_journal")
                    ),
                    "amount": adv_payment,
                    "date": self.advance_payment_date,
                }))
                ind += 1
                if deduct:
                    pricing -= adv_payment

            if self.deposit > 0.0:
                pricing -= self.deposit

            loan_amount = (pricing / float(mons or 1)) * repetition
            m = 0
            while m < mons:
                loan_lines.append((0, 0, {
                    "name": _("Cuota de Préstamo"),
                    "serial": ind,
                    "journal_id": int(
                        self.env["ir.config_parameter"].sudo().get_param("real_estate_bits.income_journal")
                    ),
                    "amount": loan_amount,
                    "date": date_payment,
                }))
                ind += 1
                date_payment = add_months(date_payment, int(repetition))
                m += repetition
                self.date_to = date_payment

            if self.maintenance:
                loan_lines.append((0, 0, {
                    "name": _("Mantenimiento"),
                    "serial": ind,
                    "journal_id": int(
                        self.env["ir.config_parameter"].sudo().get_param("real_estate_bits.maintenance_journal")
                    ),
                    "amount": self.maintenance
                    if self.maintenance_type == "amount"
                    else self.pricing * (self.maintenance / 100),
                    "date": self.date_maintenance,
                }))
                ind += 1

        return loan_lines

    def action_confirm(self):
        for contract_id in self:
            # Validaciones antes de confirmar
            if not contract_id.loan_line_ids and not contract_id.debit_line_ids:
                raise ValidationError(_("Debe generar las líneas de pago antes de confirmar el contrato"))

            if not contract_id.partner_id:
                raise ValidationError(_("Debe especificar un cliente/inquilino"))

            if not contract_id.property_id:
                raise ValidationError(_("Debe especificar una propiedad"))

            # Verificar contratos activos para la misma propiedad
            overlapping_contracts = self.env['property.contract'].search([
                ('id', '!=', contract_id.id),
                ('property_id', '=', contract_id.property_id.id),
                ('state', '=', 'confirmed'),
                ('date_from', '<=', contract_id.date_to or fields.Date.today()),
                ('date_to', '>=', contract_id.date_from)
            ])

            if overlapping_contracts:
                raise ValidationError(_(
                    "La propiedad %s ya tiene un contrato activo en el período seleccionado. "
                    "Contratos traslapados: %s"
                ) % (contract_id.property_id.name, ', '.join(overlapping_contracts.mapped('name'))))

            if contract_id.contract_type == 'is_rental':
                contract_id.property_id.write({"state": "on_lease"})
                contract_id.name = self.env["ir.sequence"].next_by_code("rental.contract")

            if contract_id.contract_type == "is_ownership":
                contract_id.property_id.write({"state": "sold"})
                contract_id.name = self.env["ir.sequence"].next_by_code("ownership.contract")

        self.write({"state": "confirmed"})

        # Log en el chatter
        for contract in self:
            contract.message_post(
                body=_("Contrato confirmado. Período: %s - %s") % (
                    contract.date_from.strftime('%d/%m/%Y') if contract.date_from else '',
                    contract.date_to.strftime('%d/%m/%Y') if contract.date_to else ''
                )
            )

    def action_cancel(self):
        for contract_obj in self:
            contract_obj.property_id.write({"state": "free"})
            contract_obj.write({"state": "cancel"})

            for line in contract_obj.loan_line_ids:
                line.invoice_id.button_draft()
                line.invoice_id.button_cancel()

    def unlink(self):
        for rec in self:
            if rec.state != "draft":
                raise UserError(_("No puede eliminar un contrato que no esté en estado borrador"))
            super(Contract, rec).unlink()

    def view_vouchers(self):
        vouchers = []
        voucher_obj = self.env["account.payment"]
        voucher_ids = voucher_obj.search([("real_estate_ref", "=", self.name)])
        for obj in voucher_ids:
            vouchers.append(obj.id)

        return {
            "name": _("Recibos"),
            "domain": [("id", "in", vouchers)],
            "view_type": "form",
            "view_mode": "list,form",
            "res_model": "account.payment",
            "type": "ir.actions.act_window",
            "view_id": False,
            "target": "current",
        }

    def view_entries(self):
        entries = []
        entry_obj = self.env["account.move"]
        entry_ids = entry_obj.search([("rental_id", "in", self.ids)])
        for obj in entry_ids:
            entries.append(obj.id)

        return {
            "name": _("Asientos Contables"),
            "domain": [("id", "in", entries)],
            "view_type": "form",
            "view_mode": "list,form",
            "res_model": "account.move",
            "type": "ir.actions.act_window",
            "view_id": False,
            "target": "current",
        }

    def create_move(self, rec, debit, credit, move, account):
        move_line_obj = self.env["account.move.line"]
        move_line_obj.create({
            "name": rec.name,
            "partner_id": rec.partner_id.id,
            "account_id": account,
            "debit": debit,
            "credit": credit,
            "move_id": move,
        })

    def generate_cancel_entries(self):
        journal_pool = self.env["account.journal"]
        journal = journal_pool.search([("type", "=", "sale")], limit=1)
        if not journal:
            raise UserError(_("¡Por favor configure el diario contable de ventas!"))
        account_move_obj = self.env["account.move"]
        total = 0
        for rec in self:
            if not rec.partner_id.property_account_receivable_id:
                raise UserError(_("¡Por favor configure la cuenta por cobrar para el socio!"))

            if not rec.account_income:
                raise UserError(_("¡Por favor configure la cuenta de ingresos para este contrato!"))

            for line in rec.loan_line_ids:
                total += line.amount

            account_move_obj.create({
                "ref": rec.name,
                "journal_id": journal.id,
                "rental_id": rec.id,
                "line_ids": [
                    (0, 0, {
                        "name": rec.name,
                        "partner_id": rec.partner_id.id,
                        "account_id": rec.partner_id.property_account_receivable_id.id,
                        "debit": 0.0,
                        "credit": total,
                    }),
                    (0, 0, {
                        "name": rec.name,
                        "partner_id": rec.partner_id.id,
                        "account_id": rec.account_income.id,
                        "debit": total,
                        "credit": 0.0,
                    }),
                ],
            })


class AccountDebitTermLine(models.Model):
    """Línea simplificada para notas de débito/intereses"""
    _name = "account.debit.term.line"
    _description = "Líneas de Débito"
    _order = "sequence"

    sequence = fields.Integer(default=10)
    contract_id = fields.Many2one(
        'property.contract',
        string='Contrato',
        required=True,
        ondelete='cascade'
    )

    name = fields.Char(
        string='Descripción',
        required=True,
        default='Nota de Débito'
    )

    value_amount = fields.Float(
        string='Porcentaje (%)',
        default=100.0,
        help="Porcentaje del monto base a aplicar"
    )

    nb_days = fields.Integer(
        string='Días Después del Vencimiento',
        default=0,
        help="Días después del vencimiento de la cuota para generar la nota de débito"
    )

    @api.constrains('value_amount')
    def _check_values(self):
        for line in self:
            if not 0.0 <= line.value_amount <= 100.0:
                raise ValidationError(_('Los porcentajes deben estar entre 0 y 100'))

    @api.constrains('nb_days')
    def _check_days(self):
        for line in self:
            if line.nb_days < 0:
                raise ValidationError(_('Los días no pueden ser negativos'))

    def _get_due_date(self, date_ref):
        """Calcula la fecha de vencimiento"""
        self.ensure_one()
        return date_ref + relativedelta(days=self.nb_days)
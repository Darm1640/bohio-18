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
    _inherit = ["mail.thread", "mail.activity.mixin", "portal.mixin"]
    _check_company_auto = True
    
    def _default_security_deposit_account(self):
        return self.env["ir.config_parameter"].sudo().get_param("real_estate_bits.security_deposit_account")

    def _default_income_account(self):
        return self.env["ir.config_parameter"].sudo().get_param("real_estate_bits.income_account")

    name = fields.Char("Numero", size=64, default='New')
    origin = fields.Char("Documento Fuente", size=64)
    contract_type = fields.Selection([
        ('is_rental', 'Arrendamiento')
    ], default='is_rental', string="Tipo de Contrato")
    type = fields.Selection(
        selection=PROJECT_WORKSITE_TYPE + [('shop', 'Tienda')], 
        string="Tipo de Propiedad"
    )
    user_id = fields.Many2one("res.users", "Vendedor", default=lambda self: self.env.user)
    partner_id = fields.Many2one("res.partner", "Inquilino O Propietario", required=True)
    company_id = fields.Many2one("res.company", string="Compañía", default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Moneda', related='company_id.currency_id', store=True, readonly=True)
    
    # FECHAS PRINCIPALES (Limpiar redundancias)
    date_from = fields.Date("Fecha de Inicio", required=True, default=fields.Date.context_today, tracking=True)
    date_to = fields.Date("Fecha de Fin", tracking=True)
    date_end = fields.Date("Fecha de Terminación Real", help="Fecha real de terminación del contrato")
    first_invoice_date = fields.Date("Fecha de Primera Factura", default=fields.Date.today(), tracking=True)

    # FECHAS CALCULADAS
    first_billing_date = fields.Date(
        string='Fecha Primera Factura Calculada',
        compute='_compute_first_billing_date',
        store=True,
        readonly=False,
        help='Fecha real de la primera factura considerando día de facturación'
    )
    next_payment_date = fields.Date(
        string='Próximo Pago',
        compute='_compute_next_payment_info',
        help='Fecha del próximo pago pendiente'
    )
    last_payment_date = fields.Date(
        string='Último Pago',
        compute='_compute_last_payment_info',
        help='Fecha del último pago realizado'
    )
    
    state = fields.Selection([
        ("quotation", "Cotización"),
        ("draft", "Pre-Contrato"),
        ("pending_signature", "Pendiente de Firma"),
        ("confirmed", "Confirmado"),
        ("renew", "Renovado"),
        ("cancel", "Cancelado")
    ], "Estado", default=lambda *a: "quotation")

    signature_state = fields.Selection([
        ("not_required", "No Requerida"),
        ("pending", "Pendiente"),
        ("signed", "Firmado"),
        ("rejected", "Rechazado")
    ], string="Estado de Firma", default="pending", tracking=True)

    skip_signature = fields.Boolean(
        string="Omitir Firma",
        default=False,
        tracking=True,
        help="Si está activado, el contrato no requiere firma digital"
    )

    show_payment_schedule = fields.Boolean(
        string="Mostrar Tabla de Pagos en Cotización",
        default=False,
        help="Si está activado, la cotización mostrará la tabla detallada de pagos mes a mes"
    )

    color = fields.Integer(
        string="Color",
        compute="_compute_color",
        store=False,
        help="Color del contrato según días restantes: Rojo (<30 días), Naranja (30-60 días), Verde (>60 días)"
    )

    apply_tax = fields.Boolean("Aplicar Impuesto")
    tax_status = fields.Selection([
        ("per_installment", "Por Cuota"), 
        ("tax_base_amount", "Monto Base de Impuesto")
    ], default="per_installment", string="Estado de Impuesto")
    
    
    paid = fields.Float(compute="_check_amounts", string="Monto Pagado")
    balance = fields.Float(compute="_check_amounts", string="Saldo")
    amount_total = fields.Float(compute="_check_amounts", string="Monto Total")

    project_id = fields.Many2one("project.worksite", related="property_id.project_worksite_id", string="Proyecto", store=True)
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

    # CAMPOS MULTI-PROPIEDAD
    is_multi_property = fields.Boolean(
        string='Contrato Multi-Propiedad',
        default=False,
        tracking=True,
        help='Indica si este contrato cubre múltiples propiedades'
    )
    contract_line_ids = fields.One2many(
        'property.contract.line',
        'contract_id',
        string='Líneas de Propiedades',
        help='Propiedades incluidas en este contrato multi-propiedad'
    )
    active_properties_count = fields.Integer(
        string='Propiedades Activas',
        compute='_compute_properties_count',
        store=False,
        help='Cantidad de propiedades activas en el contrato'
    )
    terminated_properties_count = fields.Integer(
        string='Propiedades Terminadas',
        compute='_compute_properties_count',
        store=False,
        help='Cantidad de propiedades terminadas en el contrato'
    )
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
        ('constant_periods', 'Períodos Constantes (360 días)'),
        ('daily_computation', 'Basado en Días Reales')
    ], string="Método de Prorrateo", required=True, default='daily_computation', tracking=True,
       help="""Método para calcular el prorrateo del primer y último período:

• Sin Prorrateo: Se cobra el valor completo del canon mensual sin importar los días del período.
  Ejemplo: Si inicia el 15, cobra el 100% del canon ese mes.

• Períodos Constantes (360 días): Usa el método bancario de 360 días (12 meses × 30 días).
  Ejemplo: Canon $1,000 del 15-30 = $1,000 × (16/30) = $533.33
  Ideal para cálculos financieros estandarizados.

• Basado en Días Reales: Calcula proporcionalmente según días calendario del mes.
  Ejemplo: Canon $1,000 en febrero (28 días) del 15-28 = $1,000 × (14/28) = $500.00
  Más preciso para contratos que inician/terminan a mitad de mes.""")

    # Campos computados para información del prorrateo
    prorate_info_first = fields.Char(
        string='Info Primer Período',
        compute='_compute_prorate_info',
        store=False,
        help='Información calculada del prorrateo del primer período'
    )
    prorate_info_last = fields.Char(
        string='Info Último Período',
        compute='_compute_prorate_info',
        store=False,
        help='Información calculada del prorrateo del último período'
    )

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
        "Prorratear Primer y Último Período",
        default=True,
        tracking=True,
        help="""Activar para calcular proporcionalmente el canon del primer y último período según los días reales del contrato.

Ejemplo con Canon de $1,000:
✓ Activado: Contrato del 15 al 30 = $1,000 × (16 días/30 días) = $533.33
✗ Desactivado: Contrato del 15 al 30 = $1,000 (monto completo)

Recomendado: ACTIVAR para contratos que no inician el día 1 del mes."""
    )
    billing_date = fields.Integer(
        "Día de Facturación",
        default=1,
        tracking=True,
        help="""Día del mes en que se generan las facturas automáticas (1-31).

Ejemplos:
• 1 = Facturas se generan el primer día de cada mes
• 15 = Facturas se generan el día 15 de cada mes
• 30 = Facturas se generan el día 30 (o último día si el mes tiene menos días)

Nota: Si el día no existe en el mes (ej: 31 en febrero), se usa el último día del mes."""
    )
    is_escenary_propiedad = fields.Boolean("Usar Escenario de Propiedad", default=False, tracking=True)
    
    
    maintenance = fields.Float(string="Mantenimiento", digits="Product Price")
    maintenance_type = fields.Selection([
        ("percentage", "Porcentaje"), 
        ("amount", "Monto")
    ], string="Tipo de Mantenimiento")
    
    
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

    # CONFIGURACIÓN DE PLANTILLA (TEMPORAL - USAR SELECTION)
    contract_template = fields.Selection([
        ('standard_local', 'Contrato Local Estándar'),
        ('commercial', 'Contrato Comercial'),
        ('residential', 'Contrato Residencial'),
        ('luxury', 'Contrato Premium'),
    ], string='Plantilla de Contrato', help='Plantilla predefinida con condiciones estándar')

    # CAMPOS DE COMISIÓN
    commission_percentage = fields.Float(
        'Comisión (%)',
        compute='_compute_commission_config',
        store=True,
        readonly=False,
        help='Porcentaje de comisión - toma por defecto de configuración empresarial'
    )
    commission_calculation_method = fields.Selection([
        ('gross_amount', 'Sobre Monto Bruto'),
        ('net_amount', 'Sobre Monto Neto'),
        ('rental_fee_only', 'Solo Canon')
    ], string='Base de Comisión',
       compute='_compute_commission_config',
       store=True,
       readonly=False)

    total_commission = fields.Float(
        'Comisión Total',
        compute='_compute_total_commission',
        store=True,
        digits='Account'
    )

    # Campo adicional para monto del próximo pago
    next_payment_amount = fields.Float(
        string='Monto Próximo Pago',
        compute='_compute_next_payment_info',
        help='Monto de la próxima cuota a pagar',
        digits='Account'
    )

    # RELACIONES CON PAGOS
    payment_ids = fields.Many2many(
        'account.payment',
        'payment_contract_rel',
        'contract_id', 'payment_id',
        string='Pagos Relacionados'
    )

    # RELACIÓN CON RESERVAS
    reservation_id = fields.Many2one(
        'property.reservation',
        string='Reserva Origen',
        help='Reserva desde la cual se creó este contrato'
    )

    # INTEGRACIÓN CON ODOO SIGN
    sign_request_id = fields.Many2one(
        'sign.request',
        string='Solicitud de Firma',
        help='Solicitud de firma electrónica vinculada',
        copy=False,
        tracking=True
    )
    sign_request_state = fields.Selection(
        related='sign_request_id.state',
        string='Estado Firma Sign',
        store=True,
        readonly=True
    )
    sign_completed_document = fields.Binary(
        related='sign_request_id.completed_document',
        string='Contrato Firmado',
        readonly=True
    )

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


    @api.depends("loan_line_ids.amount", "loan_line_ids.amount_residual", "loan_line_ids.payment_state")
    def _check_amounts(self):
        """
        Calcula los totales del contrato de manera consistente:
        - amount_total: Suma de TODOS los loan_line_ids.amount
        - paid: Suma de SOLO las líneas completamente pagadas (payment_state='paid')
        - balance: amount_total - paid
        """
        for rec in self:
            # Total del contrato: suma de todas las cuotas
            rec.amount_total = sum(rec.loan_line_ids.mapped('amount'))

            # Pagado: suma de cuotas completamente pagadas
            rec.paid = sum(rec.loan_line_ids.filtered(lambda x: x.payment_state == 'paid').mapped('amount'))

            # Saldo: total menos pagado
            rec.balance = rec.amount_total - rec.paid

    def _voucher_count(self):
        """Cuenta los pagos relacionados al contrato"""
        for rec in self:
            # Contar pagos usando search_count
            rec.voucher_count = self.env["account.payment"].search_count([
                ("contract_ids", "in", rec.id)
            ])

    def _entry_count(self):
        """Cuenta las facturas relacionadas al contrato"""
        for rec in self:
            # Contar facturas a través de loan.line
            loan_lines = self.env["loan.line"].search([
                ("contract_id", "=", rec.id),
                ("invoice_id", "!=", False)
            ])
            # Obtener facturas únicas
            rec.entry_count = len(loan_lines.mapped('invoice_id'))

    def auto_rental_invoice(self):
        """
        Crear facturas automáticas de alquiler.
        MEJORADO: Considera contratos multi-propiedad y multi-propietario.
        """
        try:
            # Buscar cuotas pendientes de facturar
            rental_line_ids = self.env["loan.line"].search([
                ("contract_id.state", "=", "confirmed"),
                ("date", "<=", fields.Date.today()),
                ("invoice_id", "=", False)  # Solo cuotas sin factura
            ])

            if not rental_line_ids:
                _logger.info("No hay cuotas pendientes de facturar")
                return True

            # Obtener diario de ventas
            journal = self.env["account.journal"].search([("type", "=", "sale")], limit=1)
            if not journal:
                raise UserError(_("No se encontró un diario de ventas configurado"))

            # Procesar cada línea de cuota
            invoices_created = 0
            for line in rental_line_ids:
                contract = line.contract_id

                if contract.is_multi_property and contract.contract_line_ids:
                    self._create_invoice_multi_property(line, contract, journal)
                    invoices_created += 1
                elif contract.property_id and contract.property_id.is_multi_owner and contract.owners_lines:
                    self._create_invoice_multi_owner(line, contract, journal)
                    invoices_created += 1
                else:
                    # Caso estándar: Un propietario
                    self._create_invoice_single_owner(line, contract, journal)
                    invoices_created += 1

            _logger.info(f"Se crearon {invoices_created} facturas automáticas")
            return True

        except UserError:
            raise
        except Exception as e:
            _logger.error(f"Error en auto_rental_invoice: {str(e)}", exc_info=True)
            raise UserError(_("Error al crear facturas automáticas: %s") % str(e))

    def _create_invoice_single_owner(self, line, contract, journal):
        """Crear factura estándar para un solo propietario"""
        # Generar código de codificación
        auto_code = self.env['account.move'].generate_auto_invoice_code(contract, line)

        inv_dict = {
            "journal_id": journal.id,
            "partner_id": contract.partner_id.id,
            "move_type": "out_invoice",
            "rental_line_id": line.id,
            "auto_invoice_code": auto_code,
            "invoice_date_due": line.date,
            "ref": f"{contract.name} - {line.name}",
        }

        vals = {
            "name": f"{contract.name} - {line.name}",
            "quantity": 1,
            "price_unit": line.amount,
        }

        if line.tax_status == 'per_installment':
            tax_ids = [(6, 0, self.env.company.account_sale_tax_id.ids)]
            vals.update({"tax_ids": tax_ids})

        inv_dict["invoice_line_ids"] = [(0, None, vals)]
        invoice = self.env["account.move"].create(inv_dict)
        invoice.action_post()
        line.invoice_id = invoice.id

    def _create_invoice_multi_owner(self, line, contract, journal):
        """
        Crear facturas separadas por propietario para una propiedad con múltiples owners.
        Cada propietario recibe su % del total.
        """
        for owner_line in contract.owners_lines:
            if owner_line.ownership_percentage <= 0:
                continue

            # Calcular monto proporcional
            owner_amount = line.amount * (owner_line.ownership_percentage / 100.0)

            # Generar código de codificación
            auto_code = self.env['account.move'].generate_auto_invoice_code(contract, line, owner=owner_line)

            inv_dict = {
                "journal_id": journal.id,
                "partner_id": owner_line.partner_id.id,  # Factura al propietario
                "move_type": "out_invoice",
                "rental_line_id": line.id,
                "auto_invoice_code": auto_code,
                "invoice_date_due": line.date,
                "ref": f"{contract.name} - {line.name} - Propietario: {owner_line.partner_id.name}",
            }

            vals = {
                "name": f"{contract.name} - {line.name} ({owner_line.ownership_percentage}% Propiedad)",
                "quantity": 1,
                "price_unit": owner_amount,
                "product_id": contract.property_id.id if hasattr(contract.property_id, 'product_variant_id') else False,
            }

            if line.tax_status == 'per_installment':
                tax_ids = [(6, 0, self.env.company.account_sale_tax_id.ids)]
                vals.update({"tax_ids": tax_ids})

            inv_dict["invoice_line_ids"] = [(0, None, vals)]

            try:
                invoice = self.env["account.move"].create(inv_dict)
                invoice.action_post()

                # Log en el contrato
                contract.message_post(
                    body=f"Factura creada para propietario {owner_line.partner_id.name}: "
                         f"{self.env.company.currency_id.format(owner_amount)} "
                         f"({owner_line.ownership_percentage}% de {self.env.company.currency_id.format(line.amount)})"
                )
            except Exception as e:
                _logger.error(f"Error creando factura para propietario {owner_line.partner_id.name}: {str(e)}")

        # Marcar la línea como facturada (vincula a la primera factura creada)
        if contract.owners_lines:
            first_invoice = self.env["account.move"].search([
                ("rental_line_id", "=", line.id)
            ], limit=1)
            if first_invoice:
                line.invoice_id = first_invoice.id

    def _create_invoice_multi_property(self, line, contract, journal):
        """
        Crear facturas para contrato multi-propiedad.
        Divide el monto de la cuota proporcionalmente entre las propiedades activas.
        Cada propiedad puede tener múltiples propietarios.
        """
        active_contract_lines = contract.contract_line_ids.filtered(lambda l: l.state == 'active')

        if not active_contract_lines:
            _logger.warning(f"No hay líneas activas para el contrato {contract.name}")
            return

        total_rental = sum(active_contract_lines.mapped('rental_fee'))

        if total_rental <= 0:
            _logger.warning(f"Canon total es 0 para contrato {contract.name}")
            return

        # Crear factura por cada línea de propiedad
        for contract_line in active_contract_lines:
            # Calcular monto proporcional de esta línea en la cuota
            line_percentage = (contract_line.rental_fee / total_rental) if total_rental > 0 else 0
            line_amount = line.amount * line_percentage

            property_obj = contract_line.property_id

            # Verificar si la propiedad tiene múltiples propietarios
            if property_obj.is_multi_owner and property_obj.owners_lines:
                # Multi-propietario: Crear factura por cada owner
                for owner_line in property_obj.owners_lines:
                    if owner_line.ownership_percentage <= 0:
                        continue

                    owner_amount = line_amount * (owner_line.ownership_percentage / 100.0)

                    # Generar código de codificación para multi-propiedad con multi-owner
                    auto_code = self.env['account.move'].generate_auto_invoice_code(
                        contract, line, property_line=contract_line
                    )

                    inv_dict = {
                        "journal_id": journal.id,
                        "partner_id": owner_line.partner_id.id,
                        "move_type": "out_invoice",
                        "rental_line_id": line.id,
                        "auto_invoice_code": auto_code,
                        "invoice_date_due": line.date,
                        "ref": f"{contract.name} - {property_obj.name} - {owner_line.partner_id.name}",
                    }

                    vals = {
                        "name": f"{contract.name} - {property_obj.name} ({owner_line.ownership_percentage}%)",
                        "quantity": 1,
                        "price_unit": owner_amount,
                        "product_id": property_obj.id if hasattr(property_obj, 'product_variant_id') else False,
                    }

                    if line.tax_status == 'per_installment':
                        tax_ids = [(6, 0, self.env.company.account_sale_tax_id.ids)]
                        vals.update({"tax_ids": tax_ids})

                    inv_dict["invoice_line_ids"] = [(0, None, vals)]

                    try:
                        invoice = self.env["account.move"].create(inv_dict)
                        invoice.action_post()

                        contract.message_post(
                            body=f"Factura creada - Propiedad: {property_obj.name}, "
                                 f"Propietario: {owner_line.partner_id.name}, "
                                 f"Monto: {self.env.company.currency_id.format(owner_amount)}"
                        )
                    except Exception as e:
                        _logger.error(f"Error creando factura multi-propiedad: {str(e)}")
            else:
                # Propiedad con un solo propietario
                owner_id = property_obj.partner_id

                if not owner_id:
                    _logger.warning(f"Propiedad {property_obj.name} no tiene propietario definido")
                    continue

                # Generar código de codificación para multi-propiedad con single-owner
                auto_code = self.env['account.move'].generate_auto_invoice_code(
                    contract, line, property_line=contract_line
                )

                inv_dict = {
                    "journal_id": journal.id,
                    "partner_id": owner_id.id,
                    "move_type": "out_invoice",
                    "rental_line_id": line.id,
                    "auto_invoice_code": auto_code,
                    "invoice_date_due": line.date,
                    "ref": f"{contract.name} - {property_obj.name}",
                }

                vals = {
                    "name": f"{contract.name} - {property_obj.name}",
                    "quantity": 1,
                    "price_unit": line_amount,
                    "product_id": property_obj.id if hasattr(property_obj, 'product_variant_id') else False,
                }

                if line.tax_status == 'per_installment':
                    tax_ids = [(6, 0, self.env.company.account_sale_tax_id.ids)]
                    vals.update({"tax_ids": tax_ids})

                inv_dict["invoice_line_ids"] = [(0, None, vals)]

                try:
                    invoice = self.env["account.move"].create(inv_dict)
                    invoice.action_post()

                    contract.message_post(
                        body=f"Factura creada - Propiedad: {property_obj.name}, "
                             f"Monto: {self.env.company.currency_id.format(line_amount)}"
                    )
                except Exception as e:
                    _logger.error(f"Error creando factura para propiedad única: {str(e)}")

        # Marcar la línea como facturada
        first_invoice = self.env["account.move"].search([
            ("rental_line_id", "=", line.id)
        ], limit=1)
        if first_invoice:
            line.invoice_id = first_invoice.id

    @api.depends("rent", "property_area", "property_id", "property_id.rent_value_from",
                 "rental_agreement", "is_multi_property",
                 "contract_line_ids.rental_fee", "contract_line_ids.state")
    def _compute_rental_fee(self):
        for rec in self:
            if rec.is_multi_property and rec.contract_line_ids:
                # Usar suma de líneas activas para contratos multi-propiedad
                active_lines = rec.contract_line_ids.filtered(lambda l: l.state == 'active')
                rec.rental_fee = sum(active_lines.mapped('rental_fee'))
            else:
                # Método original para contratos de una sola propiedad
                rec.rental_fee = rec.property_id.rent_value_from if rec.property_id else 0.0

    @api.depends('contract_line_ids.state')
    def _compute_properties_count(self):
        """Calcular cantidad de propiedades activas y terminadas"""
        for rec in self:
            if rec.is_multi_property and rec.contract_line_ids:
                rec.active_properties_count = len(rec.contract_line_ids.filtered(lambda l: l.state == 'active'))
                rec.terminated_properties_count = len(rec.contract_line_ids.filtered(lambda l: l.state == 'terminated'))
            else:
                rec.active_properties_count = 0
                rec.terminated_properties_count = 0

    @api.depends('date_to', 'state')
    def _compute_color(self):
        """
        Calcular color del contrato según días restantes hasta vencimiento:
        - Rojo (1): Menos de 30 días
        - Naranja (2): Entre 30 y 60 días
        - Amarillo (3): Entre 60 y 90 días
        - Verde (10): Más de 90 días o no confirmado
        """
        today = fields.Date.today()
        for rec in self:
            if rec.state != 'confirmed' or not rec.date_to:
                rec.color = 10  # Verde por defecto
            else:
                days_remaining = (rec.date_to - today).days
                if days_remaining < 0:
                    rec.color = 1  # Rojo - Vencido
                elif days_remaining < 30:
                    rec.color = 1  # Rojo - Menos de 30 días
                elif days_remaining < 60:
                    rec.color = 2  # Naranja - 30-60 días
                elif days_remaining < 90:
                    rec.color = 3  # Amarillo - 60-90 días
                else:
                    rec.color = 10  # Verde - Más de 90 días

    @api.depends('date_from', 'date_to', 'rental_fee', 'prorata_computation_type', 'prorate_first_period', 'periodicity')
    def _compute_prorate_info(self):
        """Calcula información del prorrateo para el primer y último período"""
        for contract in self:
            # Inicializar campos vacíos
            contract.prorate_info_first = ''
            contract.prorate_info_last = ''

            # Validar que existan los campos necesarios
            if not contract.date_from or not contract.date_to or not contract.rental_fee:
                continue

            # Si no hay prorrateo, indicarlo
            if not contract.prorate_first_period or contract.prorata_computation_type == 'none':
                contract.prorate_info_first = 'Sin prorrateo - Se cobra el valor completo'
                contract.prorate_info_last = 'Sin prorrateo - Se cobra el valor completo'
                continue

            # Calcular primer período
            period_months = int(contract.periodicity) if contract.periodicity else 1
            first_period_end = contract._get_period_end_date(contract.date_from, period_months, contract.date_to)

            # Información del primer período
            if contract.prorata_computation_type == 'daily_computation':
                # Basado en días reales
                days_in_period = (first_period_end - contract.date_from).days + 1
                total_days_in_month = monthrange(contract.date_from.year, contract.date_from.month)[1]
                prorated_amount = contract.rental_fee * (days_in_period / total_days_in_month)
                contract.prorate_info_first = (
                    f'Días reales: {days_in_period} días de {total_days_in_month} días del mes\n'
                    f'Cálculo: ${contract.rental_fee:,.2f} × ({days_in_period}/{total_days_in_month}) = '
                    f'${prorated_amount:,.2f}'
                )
            elif contract.prorata_computation_type == 'constant_periods':
                # Método 360 días
                days_360 = days360(contract.date_from, first_period_end)
                prorated_amount = (contract.rental_fee / 30) * days_360
                contract.prorate_info_first = (
                    f'Método 360 días: {days_360} días de 30 días\n'
                    f'Cálculo: (${contract.rental_fee:,.2f} / 30) × {days_360} = '
                    f'${prorated_amount:,.2f}'
                )

            # Calcular último período
            # Encontrar el inicio del último período
            current_date = contract.date_from
            last_period_start = contract.date_from

            while current_date < contract.date_to:
                period_end = contract._get_period_end_date(current_date, period_months, contract.date_to)
                if period_end >= contract.date_to:
                    last_period_start = current_date
                    break
                current_date = period_end + relativedelta(days=1)

            # Información del último período
            if contract.prorata_computation_type == 'daily_computation':
                # Basado en días reales
                days_in_period = (contract.date_to - last_period_start).days + 1
                total_days_in_month = monthrange(last_period_start.year, last_period_start.month)[1]
                prorated_amount = contract.rental_fee * (days_in_period / total_days_in_month)
                contract.prorate_info_last = (
                    f'Días reales: {days_in_period} días de {total_days_in_month} días del mes\n'
                    f'Cálculo: ${contract.rental_fee:,.2f} × ({days_in_period}/{total_days_in_month}) = '
                    f'${prorated_amount:,.2f}'
                )
            elif contract.prorata_computation_type == 'constant_periods':
                # Método 360 días
                days_360 = days360(last_period_start, contract.date_to)
                prorated_amount = (contract.rental_fee / 30) * days_360
                contract.prorate_info_last = (
                    f'Método 360 días: {days_360} días de 30 días\n'
                    f'Cálculo: (${contract.rental_fee:,.2f} / 30) × {days_360} = '
                    f'${prorated_amount:,.2f}'
                )

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
            if serial == 1 and self.prorate_first_period and period_start.day != 1:
                # Primer período con prorrateo (solo si NO inicia el día 1)
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


            # Fecha de facturación (día específico del mes siguiente o día de corte)
            invoice_date = self._get_invoice_date(period_end)

            # Calcular comisión para esta cuota
            commission_amount = self._calculate_commission(prorated_amount)

            rental_lines.append((0, 0, {
                "serial": serial,
                "amount": self.company_id.currency_id.round(prorated_amount),
                "date": invoice_date,
                "name": _("Canon período %s - %s") % (
                    period_start.strftime('%d/%m/%Y'),
                    period_end.strftime('%d/%m/%Y')
                ),
                "period_start": period_start,
                "period_end": period_end,
                "commission": self.company_id.currency_id.round(commission_amount),
                "commission_percentage": self.commission_percentage,
            }))

            # Avanzar al siguiente período
            # Si el primer período fue prorrateado (no empezó el día 1),
            # el siguiente debe empezar el día 1 del mes siguiente
            if serial == 1 and start_date.day != 1:
                current_date = (period_end + relativedelta(days=1)).replace(day=1)
            else:
                current_date = period_end + relativedelta(days=1)

            serial += 1

            # Prevenir loops infinitos
            if serial > 1000:
                raise ValidationError(_("Se excedió el límite de períodos (1000). Verifique las fechas del contrato."))

        self.write({"loan_line_ids": rental_lines})

    def _get_period_end_date(self, start_date, period_months, contract_end_date):
        """
        Calcula la fecha de fin del período MENSUAL CALENDARIO.

        Lógica:
        - Si es el primer día del mes: período va del 1 al último día del mes
        - Si NO es el primer día: período va hasta el último día del mes actual
        - Períodos posteriores van del 1 al último día del mes

        Ejemplos:
        - start_date=2025-01-15, period_months=1 -> 2025-01-31 (fin del mes actual)
        - start_date=2025-02-01, period_months=1 -> 2025-02-28 (mes completo)
        - start_date=2025-01-01, period_months=1 -> 2025-01-31 (mes calendario completo)
        """
        # Si el contrato inicia el día 1, cubrir el mes completo
        if start_date.day == 1:
            # Calcular último día del mes según period_months
            target_month = start_date + relativedelta(months=period_months - 1)
            period_end = target_month + relativedelta(day=31)  # Último día del mes
        else:
            # Si inicia en cualquier otro día, ir hasta el fin del mes actual
            period_end = start_date + relativedelta(day=31)  # Último día del mes de inicio

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

    def _calculate_commission(self, base_amount):
        """
        Calcula la comisión según el método configurado
        :param base_amount: Monto base (canon de la cuota)
        :return: Monto de comisión
        """
        self.ensure_one()

        if not self.commission_percentage:
            return 0.0

        # Aplicar porcentaje según el método
        if self.commission_calculation_method == 'rental_fee_only':
            # Solo sobre el canon
            commission = base_amount * (self.commission_percentage / 100.0)
        elif self.commission_calculation_method == 'net_amount':
            # Sobre monto neto (canon - descuentos, si aplicara)
            commission = base_amount * (self.commission_percentage / 100.0)
        else:  # 'gross_amount' (default)
            # Sobre monto bruto
            commission = base_amount * (self.commission_percentage / 100.0)

        return commission

    def days_between(self, start_date, end_date):
        s1, e1 = start_date, end_date + timedelta(days=1)
        s360 = (s1.year * 12 + s1.month) * 30 + s1.day
        e360 = (e1.year * 12 + e1.month) * 30 + e1.day
        res = divmod(e360 - s360, 30)
        return ((res[0] * 30) + res[1]) or 0





    @api.onchange('skip_signature')
    def _onchange_skip_signature(self):
        """Actualizar estado de firma cuando se marca/desmarca omitir firma"""
        if self.skip_signature:
            self.signature_state = 'not_required'
        else:
            if self.signature_state == 'not_required':
                self.signature_state = 'pending'

    def action_quotation_to_draft(self):
        """Convertir cotización a pre-contrato"""
        for contract in self:
            if contract.state != 'quotation':
                raise ValidationError(_("Solo se pueden convertir cotizaciones a pre-contrato"))

            # Validaciones básicas
            if not contract.partner_id:
                raise ValidationError(_("Debe especificar un cliente/inquilino"))
            if not contract.property_id and not contract.contract_line_ids:
                raise ValidationError(_("Debe especificar al menos una propiedad"))

            contract.write({'state': 'draft'})
            contract.message_post(body=_("Cotización convertida a pre-contrato"))

    def action_back_to_quotation(self):
        """Regresar a cotización"""
        for contract in self:
            if contract.state not in ('draft', 'pending_signature'):
                raise ValidationError(_("Solo se pueden regresar a cotización contratos en pre-contrato o pendientes de firma"))

            contract.write({'state': 'quotation'})
            contract.message_post(body=_("Contrato regresado a cotización"))

    def action_send_for_signature(self):
        """Enviar contrato para firma"""
        for contract in self:
            if contract.skip_signature:
                raise ValidationError(_("Este contrato está configurado para omitir la firma"))

            # Validaciones básicas
            if not contract.partner_id:
                raise ValidationError(_("Debe especificar un cliente/inquilino"))
            if not contract.property_id:
                raise ValidationError(_("Debe especificar una propiedad"))

            contract.write({
                'state': 'pending_signature',
                'signature_state': 'pending'
            })

            contract.message_post(
                body=_("Contrato enviado para firma al cliente %s") % contract.partner_id.name
            )

    def action_mark_signed(self):
        """Marcar contrato como firmado"""
        for contract in self:
            contract.write({'signature_state': 'signed'})
            contract.message_post(body=_("Contrato firmado correctamente"))

    def action_reject_signature(self):
        """Rechazar firma del contrato"""
        for contract in self:
            contract.write({
                'signature_state': 'rejected',
                'state': 'draft'
            })
            contract.message_post(body=_("Firma del contrato rechazada"))

    def action_confirm(self):
        for contract_id in self:
            # Validaciones antes de confirmar
            if not contract_id.loan_line_ids and not contract_id.debit_line_ids:
                raise ValidationError(_("Debe generar las líneas de pago antes de confirmar el contrato"))

            if not contract_id.partner_id:
                raise ValidationError(_("Debe especificar un cliente/inquilino"))

            if not contract_id.property_id:
                raise ValidationError(_("Debe especificar una propiedad"))

            # Validar firma si es requerida
            if not contract_id.skip_signature and contract_id.signature_state != 'signed':
                raise ValidationError(_(
                    "El contrato debe estar firmado antes de confirmarse. "
                    "Estado de firma actual: %s"
                ) % dict(contract_id._fields['signature_state'].selection).get(contract_id.signature_state))

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
        voucher_obj = self.env["account.payment"]
        voucher_ids = voucher_obj.search([("contract_ids", "in", self.id)])

        return {
            "name": _("Recibos"),
            "domain": [("id", "in", voucher_ids.ids)],
            "view_type": "form",
            "view_mode": "list,form",
            "res_model": "account.payment",
            "type": "ir.actions.act_window",
            "view_id": False,
            "target": "current",
        }

    def view_entries(self):
        # Obtener facturas a través de loan.line
        loan_lines = self.env["loan.line"].search([
            ("contract_id", "in", self.ids),
            ("invoice_id", "!=", False)
        ])
        invoice_ids = loan_lines.mapped('invoice_id.id')

        return {
            "name": _("Asientos Contables"),
            "domain": [("id", "in", invoice_ids)],
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

    # MÉTODOS COMPUTE AGREGADOS
    @api.depends('company_id')
    def _compute_commission_config(self):
        """Aplicar configuración por defecto de la empresa"""
        for contract in self:
            if not contract.commission_percentage:  # Solo si está vacío
                # Valores por defecto
                contract.commission_percentage = 8.0
                contract.commission_calculation_method = 'gross_amount'

    @api.depends('loan_line_ids.commission')
    def _compute_total_commission(self):
        """Calcular comisión total del contrato"""
        for contract in self:
            contract.total_commission = sum(contract.loan_line_ids.mapped('commission'))

    @api.depends('date_from', 'billing_date', 'first_invoice_date')
    def _compute_first_billing_date(self):
        """Calcular fecha real de primera factura"""
        for contract in self:
            if not (contract.date_from and contract.billing_date):
                contract.first_billing_date = contract.first_invoice_date
                continue

            start_date = contract.date_from
            billing_day = contract.billing_date

            # Si es el primer día o ya pasó el día de facturación del mes
            if start_date.day >= billing_day:
                # Próximo mes
                next_month = start_date + relativedelta(months=1)
                try:
                    contract.first_billing_date = next_month.replace(day=billing_day)
                except ValueError:
                    # Día no existe en el mes (ej: 31 Feb)
                    contract.first_billing_date = next_month.replace(day=monthrange(next_month.year, next_month.month)[1])
            else:
                # Mismo mes
                contract.first_billing_date = start_date.replace(day=billing_day)

    @api.depends('loan_line_ids.date', 'loan_line_ids.amount', 'loan_line_ids.payment_state')
    def _compute_next_payment_info(self):
        """Calcular información del próximo pago pendiente"""
        for contract in self:
            pending_lines = contract.loan_line_ids.filtered(
                lambda l: l.payment_state != 'paid' and l.date >= fields.Date.today()
            ).sorted('date')

            if pending_lines:
                next_line = pending_lines[0]
                contract.next_payment_amount = next_line.amount
                contract.next_payment_date = next_line.date
            else:
                contract.next_payment_amount = 0.0
                contract.next_payment_date = False

    @api.depends('loan_line_ids.date', 'loan_line_ids.payment_state')
    def _compute_last_payment_info(self):
        """Calcular fecha del último pago realizado"""
        for contract in self:
            paid_lines = contract.loan_line_ids.filtered(
                lambda l: l.payment_state == 'paid'
            ).sorted('date', reverse=True)

            contract.last_payment_date = paid_lines[0].date if paid_lines else False

    def action_modify_contract(self):
        """Abrir wizard de modificación unificado"""
        return {
            'name': 'Modificar Contrato',
            'type': 'ir.actions.act_window',
            'res_model': 'modify.contract.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_contract_id': self.id}
        }

    def compute_depreciation_board(self, date=False):
        """Recalcular líneas futuras (como Account Asset)"""
        for contract in self:
            if contract.state != 'confirmed':
                continue

            # Eliminar líneas futuras no pagadas
            future_lines = contract.loan_line_ids.filtered(
                lambda l: l.date >= (date or fields.Date.today()) and l.payment_state != 'paid'
            )
            future_lines.unlink()

            # Regenerar líneas
            contract.prepare_lines()

            contract.message_post(
                body=f"Líneas de pago recalculadas desde {(date or fields.Date.today()).strftime('%d/%m/%Y')}"
            )

    def _recalculate_future_installments_on_line_change(self):
        """Recalcular cuotas futuras cuando cambian las líneas de propiedades"""
        self.ensure_one()

        if self.state != 'confirmed' or not self.is_multi_property:
            return

        # Fecha de corte: primera cuota no pagada o hoy
        cutoff_date = fields.Date.today()
        first_unpaid = self.loan_line_ids.filtered(
            lambda l: l.payment_state != 'paid'
        ).sorted('date')

        if first_unpaid:
            cutoff_date = first_unpaid[0].date

        # Guardar cuotas ya pagadas
        paid_lines = self.loan_line_ids.filtered(lambda l: l.payment_state == 'paid')

        # Eliminar cuotas futuras no pagadas
        future_lines = self.loan_line_ids.filtered(
            lambda l: l.date >= cutoff_date and l.payment_state != 'paid'
        )
        future_lines.unlink()

        # Recalcular desde la fecha de corte usando el nuevo canon total
        self._prepare_lines_from_date(cutoff_date)

        # Log del cambio
        new_total = sum(self.contract_line_ids.filtered(lambda l: l.state == 'active').mapped('rental_fee'))
        self.message_post(
            body=_('Canon recalculado automáticamente. Nuevo total: %s (desde %s)') % (
                self.env.company.currency_id.format(new_total),
                cutoff_date.strftime('%d/%m/%Y')
            )
        )

    def _prepare_lines_from_date(self, start_date):
        """Preparar líneas de cobro desde una fecha específica"""
        self.ensure_one()

        if not (self.periodicity and self.date_to):
            return

        end_date = self.date_to
        current_rental_fee = self.rental_fee  # Ya incluye el total de líneas activas
        period_months = int(self.periodicity)

        if not current_rental_fee or current_rental_fee <= 0:
            _logger.warning(f"Canon total es cero para contrato {self.name}. No se generarán líneas.")
            return

        current_date = start_date
        # Obtener el último serial usado
        last_serial = max(self.loan_line_ids.mapped('serial') or [0])
        serial = last_serial + 1

        # Variables para incrementos
        last_increment_date = self.date_from

        # Calcular si ya se han aplicado incrementos
        months_since_start = self._get_months_between(self.date_from, current_date)
        if self.increment_recurring_interval and self.increment_percentage:
            increment_interval_months = self.increment_recurring_interval * (12 if self.increment_period == 'years' else 1)
            increments_applied = months_since_start // increment_interval_months

            # Aplicar incrementos acumulados
            for _ in range(increments_applied):
                current_rental_fee = current_rental_fee * (1 + self.increment_percentage / 100)

            last_increment_date = self.date_from + relativedelta(months=increments_applied * increment_interval_months)

        rental_lines = []

        while current_date <= end_date:
            # Calcular período
            period_start = current_date
            period_end = self._get_period_end_date(current_date, period_months, end_date)

            # Verificar si hay líneas activas en este período
            active_properties_in_period = self._get_active_properties_in_period(period_start, period_end)
            if not active_properties_in_period:
                # Si no hay propiedades activas, saltar este período
                current_date = period_end + relativedelta(days=1)
                continue

            # Calcular el canon proporcional según propiedades activas
            period_rental_fee = self._calculate_period_rental_fee(period_start, period_end, current_rental_fee)

            # Aplicar incremento si corresponde
            if self.increment_recurring_interval and self.increment_percentage:
                months_since_increment = self._get_months_between(last_increment_date, period_start)
                increment_interval_months = self.increment_recurring_interval * (12 if self.increment_period == 'years' else 1)

                if months_since_increment >= increment_interval_months:
                    current_rental_fee = current_rental_fee * (1 + self.increment_percentage / 100)
                    period_rental_fee = self._calculate_period_rental_fee(period_start, period_end, current_rental_fee)
                    last_increment_date = period_start

            # Fecha de facturación
            invoice_date = self._get_invoice_date(period_end)

            # Calcular comisión
            commission_amount = self._calculate_commission(period_rental_fee)

            rental_lines.append((0, 0, {
                "serial": serial,
                "amount": self.company_id.currency_id.round(period_rental_fee),
                "date": invoice_date,
                "name": _("Canon período %s - %s") % (
                    period_start.strftime('%d/%m/%Y'),
                    period_end.strftime('%d/%m/%Y')
                ),
                "period_start": period_start,
                "period_end": period_end,
                "commission": self.company_id.currency_id.round(commission_amount),
                "commission_percentage": self.commission_percentage,
            }))

            # Avanzar al siguiente período
            current_date = period_end + relativedelta(days=1)
            serial += 1

            # Prevenir loops infinitos
            if serial > 2000:
                raise ValidationError(_("Se excedió el límite de períodos (2000). Verifique las fechas del contrato."))

        # Agregar líneas (no sobreescribir las existentes)
        if rental_lines:
            existing_lines = [(6, 0, self.loan_line_ids.ids)]
            self.write({"loan_line_ids": existing_lines + rental_lines})

    def _get_active_properties_in_period(self, period_start, period_end):
        """Obtener propiedades activas en un período específico"""
        if not self.is_multi_property:
            return [self.property_id] if self.property_id else []

        active_lines = self.contract_line_ids.filtered(
            lambda l: l.state == 'active' and
                     l.date_from <= period_end and
                     (not l.date_end_real or l.date_end_real >= period_start)
        )
        return active_lines.mapped('property_id')

    def _calculate_period_rental_fee(self, period_start, period_end, base_rental_fee):
        """Calcular canon para un período considerando propiedades activas y terminaciones"""
        if not self.is_multi_property:
            return base_rental_fee

        # Obtener líneas que están activas durante todo el período
        period_duration = (period_end - period_start).days + 1
        total_rental_for_period = 0.0

        for line in self.contract_line_ids:
            if line.state not in ['active', 'terminated']:
                continue

            # Calcular días que esta línea está activa en el período
            line_start = max(line.date_from, period_start)
            line_end = min(line.date_end_real or line.date_to, period_end)

            if line_start <= line_end:
                active_days = (line_end - line_start).days + 1
                daily_rate = line.rental_fee / 30  # Aproximación diaria

                if self.prorate_first_period:
                    # Prorratear según días activos
                    total_rental_for_period += daily_rate * active_days
                else:
                    # Canon completo si está activa cualquier día del período
                    total_rental_for_period += line.rental_fee

        return total_rental_for_period

    def action_asset_modify(self):
        """Modificar contrato (como Account Asset)"""
        return self.action_modify_contract()

    @api.model
    def create_from_reservation(self, reservation_id):
        """Crear contrato desde reserva"""
        reservation = self.env['property.reservation'].browse(reservation_id)

        contract_vals = {
            'partner_id': reservation.partner_id.id,
            'property_id': reservation.property_id.id,
            'user_id': reservation.user_id.id,
            'reservation_id': reservation.id,
            'origin': f"Reserva: {reservation.name}",
            'date_from': reservation.date_from or fields.Date.today(),
            'date_to': reservation.date_to,
            'rental_fee': reservation.property_id.rent_value_from,
            'insurance_fee': reservation.property_id.insurance_fee,
            'deposit': reservation.amount,  # El monto de reserva como depósito
            # Configuración por defecto
            'commission_percentage': 8.0,
            'interest_rate': 1.5,
            'interest_days_grace': 5,
            'increment_percentage': 4.0,
            'apply_interest': True,
            'periodicity': '1',
        }

        contract = self.create(contract_vals)

        # Marcar reserva como convertida
        reservation.write({
            'conversion_state': 'converted',
            'contract_id': contract.id
        })

        return contract

    @api.onchange('contract_template')
    def _onchange_contract_template(self):
        """Aplicar plantilla predefinida"""
        if not self.contract_template:
            return

        # Configuraciones por tipo de plantilla
        template_configs = {
            'standard_local': {
                'commission_percentage': 8.0,
                'interest_rate': 1.5,
                'interest_days_grace': 5,
                'increment_percentage': 4.0,
                'apply_interest': True,
                'prorate_first_period': True,
                'billing_date': 1,
                'periodicity': '1'
            },
            'commercial': {
                'commission_percentage': 6.0,
                'interest_rate': 2.0,
                'interest_days_grace': 3,
                'increment_percentage': 6.0,
                'apply_interest': True,
                'prorate_first_period': False,
                'billing_date': 5,
                'periodicity': '1'
            },
            'residential': {
                'commission_percentage': 10.0,
                'interest_rate': 1.0,
                'interest_days_grace': 10,
                'increment_percentage': 3.5,
                'apply_interest': True,
                'prorate_first_period': True,
                'billing_date': 1,
                'periodicity': '1'
            },
            'luxury': {
                'commission_percentage': 5.0,
                'interest_rate': 1.5,
                'interest_days_grace': 15,
                'increment_percentage': 5.0,
                'apply_interest': True,
                'prorate_first_period': True,
                'billing_date': 1,
                'periodicity': '3'  # Trimestral
            }
        }

        config = template_configs.get(self.contract_template, {})

        # Solo aplicar valores si están vacíos
        for field, value in config.items():
            if not getattr(self, field, None):
                setattr(self, field, value)

    @api.onchange('property_id')
    def onchange_unit(self):
        """MEJORAR método existente - líneas 521-527"""
        if self.property_id:
            self.type = self.property_id.project_type
            self.project_id = self.property_id.project_worksite_id.id
            self.region_id = self.property_id.region_id.id

            # Traer valor de arriendo de la propiedad (COMO SOLICITASTE)
            if not self.rental_fee:  # Solo si está vacío
                self.rental_fee = self.property_id.rent_value_from

            if not self.insurance_fee:  # Solo si está vacío
                self.insurance_fee = self.property_id.insurance_fee

    def _compute_access_url(self):
        """URL de acceso al portal"""
        super()._compute_access_url()
        for contract in self:
            contract.access_url = f'/my/contract/{contract.id}'


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


# PropertyContractLine REMOVIDO - La definición completa está en property_contract_line.py
# Esta era una duplicación que causaba conflictos en la carga de modelos


# ==================================================================================
# EXTENSIONES MULTI-PROPIEDAD DE PROPERTY.CONTRACT
# Movidas desde property_contract_line.py para mantener UN ARCHIVO POR MODELO
# ==================================================================================

class PropertyContractMultiProperty(models.Model):
    """Extensiones para contratos multi-propiedad"""
    _inherit = 'property.contract'

    # Métodos específicos para multi-propiedad (ya están definidos en Contract arriba)
    # Los campos is_multi_property y contract_line_ids ya están definidos en Contract

    @api.onchange('is_multi_property')
    def _onchange_is_multi_property(self):
        if self.is_multi_property and not self.contract_line_ids:
            # Si se activa multi-propiedad y hay una propiedad principal, crear primera línea
            if self.property_id:
                self.contract_line_ids = [(0, 0, {
                    'property_id': self.property_id.id,
                    'date_from': self.date_from,
                    'date_to': self.date_to,
                    'rental_fee': self.rental_fee or self.property_id.rent_value_from,
                    'state': 'active' if self.state == 'confirmed' else 'draft',
                })]

    def action_add_property_line(self):
        """Agregar nueva línea de propiedad"""
        self.ensure_one()
        if not self.is_multi_property:
            raise UserError(_('Debe activar "Contrato Multi-Propiedad" primero'))

        return {
            'name': _('Agregar Propiedad al Contrato'),
            'type': 'ir.actions.act_window',
            'res_model': 'property.contract.add.line.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_contract_id': self.id,
                'default_date_from': self.date_from,
                'default_date_to': self.date_to,
            }
        }

    def action_terminate_property_line(self):
        """Terminar línea de propiedad específica"""
        self.ensure_one()
        return {
            'name': _('Terminar Propiedad del Contrato'),
            'type': 'ir.actions.act_window',
            'res_model': 'property.contract.terminate.line.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_contract_id': self.id}
        }


# ==================================================================================
# WIZARDS PARA CONTRATOS MULTI-PROPIEDAD
# Movidos desde property_contract_line.py para consolidación
# ==================================================================================

class PropertyContractAddLineWizard(models.TransientModel):
    _name = 'property.contract.add.line.wizard'
    _description = 'Wizard para Agregar Propiedad al Contrato'

    contract_id = fields.Many2one('property.contract', 'Contrato', required=True)
    property_id = fields.Many2one('product.template', 'Propiedad', required=True,
                                  domain=[("is_property", "=", True), ("state", "=", "free")])

    # FECHAS
    date_from = fields.Date('Fecha Inicio', required=True)
    date_to = fields.Date('Fecha Fin', required=True)

    # CONFIGURACIÓN DE CANON
    calculation_method = fields.Selection([
        ('property_default', 'Canon Sugerido de la Propiedad'),
        ('manual_amount', 'Monto Manual'),
        ('percentage_of_contract', 'Porcentaje del Contrato Principal')
    ], string='Método de Cálculo', default='property_default', required=True)

    manual_rental_fee = fields.Float('Canon Manual', digits='Product Price')
    percentage_of_contract = fields.Float('Porcentaje (%)', default=0.0,
                                         help='Porcentaje del canon del contrato principal')

    # CAMPOS CALCULADOS
    suggested_rental_fee = fields.Float('Canon Sugerido', compute='_compute_suggested_rental', readonly=True)
    final_rental_fee = fields.Float('Canon Final', compute='_compute_final_rental', readonly=True)

    @api.depends('property_id')
    def _compute_suggested_rental(self):
        for wizard in self:
            if wizard.property_id:
                wizard.suggested_rental_fee = wizard.property_id.rent_value_from or 0.0
            else:
                wizard.suggested_rental_fee = 0.0

    @api.depends('calculation_method', 'manual_rental_fee', 'percentage_of_contract',
                 'suggested_rental_fee', 'contract_id.rental_fee')
    def _compute_final_rental(self):
        for wizard in self:
            if wizard.calculation_method == 'property_default':
                wizard.final_rental_fee = wizard.suggested_rental_fee
            elif wizard.calculation_method == 'manual_amount':
                wizard.final_rental_fee = wizard.manual_rental_fee
            elif wizard.calculation_method == 'percentage_of_contract':
                base_rental = wizard.contract_id.rental_fee or 0.0
                wizard.final_rental_fee = base_rental * (wizard.percentage_of_contract / 100)
            else:
                wizard.final_rental_fee = 0.0

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for wizard in self:
            if wizard.date_from >= wizard.date_to:
                raise ValidationError(_('La fecha de inicio debe ser menor que la fecha de fin'))

    def action_add_line(self):
        """Agregar la línea al contrato"""
        self.ensure_one()

        # Validar que la propiedad esté disponible
        if self.property_id.state != 'free':
            raise UserError(_('La propiedad seleccionada no está disponible'))

        # Crear la línea
        line_vals = {
            'contract_id': self.contract_id.id,
            'property_id': self.property_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'rental_fee': self.final_rental_fee,
            'state': 'active' if self.contract_id.state == 'confirmed' else 'draft',
        }

        line = self.env['property.contract.line'].create(line_vals)

        # Marcar propiedad como ocupada
        if self.contract_id.state == 'confirmed':
            self.property_id.write({'state': 'on_lease'})

        # Recalcular cuotas del contrato si está confirmado
        if self.contract_id.state == 'confirmed':
            self.contract_id._recalculate_future_installments_on_line_change()

        # Log en el contrato
        self.contract_id.message_post(
            body=_('Nueva propiedad agregada: %s (Canon: %s)') % (
                self.property_id.name,
                self.env.company.currency_id.format(self.final_rental_fee)
            )
        )

        return {'type': 'ir.actions.act_window_close'}


class PropertyContractTerminateLineWizard(models.TransientModel):
    _name = 'property.contract.terminate.line.wizard'
    _description = 'Wizard para Terminar Línea Específica'

    contract_id = fields.Many2one('property.contract', 'Contrato', required=True)
    contract_line_id = fields.Many2one('property.contract.line', 'Línea a Terminar', required=True,
                                       domain="[('contract_id', '=', contract_id), ('state', '=', 'active')]")

    termination_date = fields.Date('Fecha de Terminación', required=True, default=fields.Date.today)
    termination_reason = fields.Selection([
        ('contract_end', 'Fin de Contrato'),
        ('early_termination', 'Terminación Anticipada'),
        ('non_payment', 'Falta de Pago'),
        ('property_sale', 'Venta de Propiedad'),
        ('other', 'Otro Motivo')
    ], string='Motivo', required=True)
    notes = fields.Text('Observaciones')

    # VISTA PREVIA DEL IMPACTO
    current_total_rental = fields.Float('Canon Total Actual', compute='_compute_impact', readonly=True)
    rental_after_termination = fields.Float('Canon Después de Terminación', compute='_compute_impact', readonly=True)
    impact_amount = fields.Float('Impacto en Canon', compute='_compute_impact', readonly=True)
    impact_percentage = fields.Float('% de Impacto', compute='_compute_impact', readonly=True)

    @api.depends('contract_line_id', 'contract_id')
    def _compute_impact(self):
        for wizard in self:
            if wizard.contract_id and wizard.contract_line_id:
                wizard.current_total_rental = wizard.contract_id.total_rental_fee
                wizard.impact_amount = wizard.contract_line_id.rental_fee
                wizard.rental_after_termination = wizard.current_total_rental - wizard.impact_amount

                if wizard.current_total_rental > 0:
                    wizard.impact_percentage = (wizard.impact_amount / wizard.current_total_rental) * 100
                else:
                    wizard.impact_percentage = 0.0
            else:
                wizard.current_total_rental = 0.0
                wizard.rental_after_termination = 0.0
                wizard.impact_amount = 0.0
                wizard.impact_percentage = 0.0

    def action_terminate_line(self):
        """Terminar la línea seleccionada"""
        self.ensure_one()

        # Ejecutar terminación
        self.contract_line_id.terminate_line(
            self.termination_date,
            self.termination_reason,
            self.notes
        )

        # Liberar la propiedad
        self.contract_line_id.property_id.write({'state': 'free'})

        return {'type': 'ir.actions.act_window_close'}
# 🔧 IMPLEMENTACIÓN COMPLETA: BILLING TYPE Y WIZARD DE FACTURACIÓN

---

## 📊 RESUMEN EJECUTIVO

Implementación completa de:
- ✅ Campo `billing_type` (mes vencido/anticipado)
- ✅ Wizard para generar facturas por período
- ✅ Generación automática de factura de comisiones
- ✅ Lógica de fechas ajustada según billing_type

---

## 1️⃣ MODIFICAR MODELO `property.contract`

### 📁 Archivo: `real_estate_bits/models/property_contract.py`

```python
# ==========================================
# AGREGAR CAMPO billing_type
# ==========================================

billing_type = fields.Selection([
    ('arrears', 'Mes Vencido'),      # Factura DESPUÉS del período consumido
    ('advance', 'Mes Anticipado'),   # Factura ANTES del período a consumir
], string='Tipo de Facturación',
   default='arrears',
   required=True,
   tracking=True,
   help="""Mes Vencido: La factura se genera después de consumir el período.
Mes Anticipado: La factura se genera antes de iniciar el período.""")


# ==========================================
# AGREGAR CAMPOS DE INFORMACIÓN
# ==========================================

prorate_info_first = fields.Char(
    string='Cálculo Primer Período',
    compute='_compute_prorate_info',
    help='Muestra el cálculo del prorrateo del primer período'
)

prorate_info_last = fields.Char(
    string='Cálculo Último Período',
    compute='_compute_prorate_info',
    help='Muestra el cálculo del prorrateo del último período'
)

billing_type_description = fields.Char(
    string='Descripción Facturación',
    compute='_compute_billing_type_description',
    help='Explica cómo funciona el tipo de facturación seleccionado'
)


# ==========================================
# MÉTODO COMPUTE: billing_type_description
# ==========================================

@api.depends('billing_type')
def _compute_billing_type_description(self):
    """Explica el tipo de facturación"""
    for contract in self:
        if contract.billing_type == 'arrears':
            contract.billing_type_description = (
                "📅 Mes Vencido: La factura se genera DESPUÉS de consumir el período. "
                "Ejemplo: Período Feb 1-28 → Factura Mar 1"
            )
        else:  # advance
            contract.billing_type_description = (
                "📅 Mes Anticipado: La factura se genera ANTES de iniciar el período. "
                "Ejemplo: Período Feb 1-28 → Factura Feb 1"
            )


# ==========================================
# MÉTODO COMPUTE: prorate_info
# ==========================================

@api.depends('date_from', 'date_to', 'rental_fee',
             'prorata_computation_type', 'prorate_first_period',
             'billing_type')
def _compute_prorate_info(self):
    """Calcula y muestra información del prorrateo"""
    for contract in self:
        if not (contract.prorate_first_period and contract.date_from and
                contract.date_to and contract.rental_fee):
            contract.prorate_info_first = "No aplica prorrateo"
            contract.prorate_info_last = "No aplica prorrateo"
            continue

        # ===== PRIMER PERÍODO =====
        if contract.date_from.day != 1:
            period_start = contract.date_from
            # Primer período hasta fin de mes
            period_end = period_start.replace(
                day=monthrange(period_start.year, period_start.month)[1]
            )

            if period_end > contract.date_to:
                period_end = contract.date_to

            days_in_period = (period_end - period_start).days + 1

            if contract.prorata_computation_type == 'daily_computation':
                total_days = monthrange(period_start.year, period_start.month)[1]
                prorated = contract.rental_fee * (days_in_period / total_days)

                contract.prorate_info_first = (
                    f"📊 {period_start.strftime('%d/%m/%Y')} - {period_end.strftime('%d/%m/%Y')} | "
                    f"Días: {days_in_period}/{total_days} | "
                    f"Monto: {contract.company_id.currency_id.symbol} "
                    f"{formatLang(self.env, prorated, currency_obj=contract.company_id.currency_id)}"
                )
            elif contract.prorata_computation_type == 'constant_periods':
                days_360 = days360(period_start, period_end)
                prorated = (contract.rental_fee / 30) * days_360

                contract.prorate_info_first = (
                    f"🏦 {period_start.strftime('%d/%m/%Y')} - {period_end.strftime('%d/%m/%Y')} | "
                    f"Días 360: {days_360}/30 | "
                    f"Monto: {contract.company_id.currency_id.symbol} "
                    f"{formatLang(self.env, prorated, currency_obj=contract.company_id.currency_id)}"
                )
            else:  # none
                contract.prorate_info_first = (
                    f"❌ Sin prorrateo | "
                    f"Monto: {contract.company_id.currency_id.symbol} "
                    f"{formatLang(self.env, contract.rental_fee, currency_obj=contract.company_id.currency_id)}"
                )
        else:
            contract.prorate_info_first = "✅ Inicia día 1 - No requiere prorrateo"

        # ===== ÚLTIMO PERÍODO =====
        last_day_of_month = monthrange(contract.date_to.year, contract.date_to.month)[1]

        if contract.date_to.day != last_day_of_month:
            period_end = contract.date_to
            period_start = period_end.replace(day=1)

            days_in_period = (period_end - period_start).days + 1

            if contract.prorata_computation_type == 'daily_computation':
                total_days = monthrange(period_end.year, period_end.month)[1]
                prorated = contract.rental_fee * (days_in_period / total_days)

                contract.prorate_info_last = (
                    f"📊 {period_start.strftime('%d/%m/%Y')} - {period_end.strftime('%d/%m/%Y')} | "
                    f"Días: {days_in_period}/{total_days} | "
                    f"Monto: {contract.company_id.currency_id.symbol} "
                    f"{formatLang(self.env, prorated, currency_obj=contract.company_id.currency_id)}"
                )
            elif contract.prorata_computation_type == 'constant_periods':
                days_360 = days360(period_start, period_end)
                prorated = (contract.rental_fee / 30) * days_360

                contract.prorate_info_last = (
                    f"🏦 {period_start.strftime('%d/%m/%Y')} - {period_end.strftime('%d/%m/%Y')} | "
                    f"Días 360: {days_360}/30 | "
                    f"Monto: {contract.company_id.currency_id.symbol} "
                    f"{formatLang(self.env, prorated, currency_obj=contract.company_id.currency_id)}"
                )
            else:  # none
                contract.prorate_info_last = (
                    f"❌ Sin prorrateo | "
                    f"Monto: {contract.company_id.currency_id.symbol} "
                    f"{formatLang(self.env, contract.rental_fee, currency_obj=contract.company_id.currency_id)}"
                )
        else:
            contract.prorate_info_last = "✅ Termina último día del mes - No requiere prorrateo"


# ==========================================
# MODIFICAR MÉTODO: _get_invoice_date
# ==========================================

def _get_invoice_date(self, period_start, period_end):
    """
    Calcula la fecha de facturación según billing_type y billing_date

    :param period_start: Fecha de inicio del período
    :param period_end: Fecha de fin del período
    :return: Fecha en que se debe generar/enviar la factura
    """
    self.ensure_one()

    if self.billing_type == 'advance':
        # ===== MES ANTICIPADO: Factura al INICIO del período =====
        if self.billing_date and self.billing_date > 0:
            try:
                # Usar el día específico de facturación en el mes de inicio
                invoice_date = period_start.replace(day=self.billing_date)

                # Si ya pasó ese día en el mes, facturar en la fecha de inicio
                if invoice_date < period_start:
                    invoice_date = period_start

                return invoice_date
            except ValueError:
                # El día no existe en este mes (ej: 31 en febrero)
                # Usar el último día del mes
                last_day = monthrange(period_start.year, period_start.month)[1]
                return period_start.replace(day=min(last_day, self.billing_date))
        else:
            # Sin día específico, facturar el primer día del período
            return period_start

    else:  # billing_type == 'arrears' (MES VENCIDO - DEFAULT)
        # ===== MES VENCIDO: Factura al TERMINAR el período =====
        if self.billing_date and self.billing_date > 0:
            try:
                # Calcular el primer día después del período
                day_after_period = period_end + relativedelta(days=1)

                # Intentar usar el día de facturación en ese mes
                invoice_date = day_after_period.replace(day=self.billing_date)

                # Si el día de facturación es antes del fin del período,
                # mover al siguiente mes
                if invoice_date <= period_end:
                    invoice_date = invoice_date + relativedelta(months=1)

                return invoice_date
            except ValueError:
                # El día no existe, usar el primer día del mes siguiente
                return period_end + relativedelta(months=1, day=1)
        else:
            # Sin día específico, facturar el día después del período
            return period_end + relativedelta(days=1)


# ==========================================
# MODIFICAR MÉTODO: prepare_lines
# ==========================================

def prepare_lines(self):
    """
    Genera las líneas de cobro de canon con lógica corregida:
    - Prorrateo SOLO hasta fin del mes de inicio
    - Respeta billing_type (vencido/anticipado)
    - Genera períodos mensuales completos después del prorrateo
    """
    self.ensure_one()
    self.loan_line_ids = False
    rental_lines = []

    # Validaciones básicas
    if not (self.periodicity and self.date_from and self.date_to):
        return

    start_date = self.date_from
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

    # ==========================================
    # PASO 1: PRORRATEO PRIMER PERÍODO (si aplica)
    # ==========================================
    if self.prorate_first_period and start_date.day != 1:
        # Primer período prorrateado: desde start_date hasta fin del mes
        period_start = start_date
        last_day_of_month = monthrange(start_date.year, start_date.month)[1]
        period_end = start_date.replace(day=last_day_of_month)

        # Si el contrato termina antes del fin del mes, ajustar
        if period_end > end_date:
            period_end = end_date

        # Calcular monto prorrateado
        prorated_amount = self._compute_prorated_amount(
            period_start, period_end, current_rental_fee
        )

        # Calcular fecha de facturación según billing_type
        invoice_date = self._get_invoice_date(period_start, period_end)

        rental_lines.append((0, 0, {
            "serial": serial,
            "amount": self.company_id.currency_id.round(prorated_amount),
            "date": invoice_date,
            "name": _("Canon período %s - %s (Prorrateo)") % (
                period_start.strftime('%d/%m/%Y'),
                period_end.strftime('%d/%m/%Y')
            ),
            "period_start": period_start,
            "period_end": period_end,
        }))

        # Mensaje en chatter
        self.message_post(
            body=_(
                "🔢 Línea %s (Prorrateo): %s - %s | Monto: %s"
            ) % (
                serial,
                period_start.strftime('%d/%m/%Y'),
                period_end.strftime('%d/%m/%Y'),
                formatLang(self.env, prorated_amount, currency_obj=self.company_id.currency_id)
            )
        )

        # Avanzar al primer día del mes siguiente
        current_date = period_end + relativedelta(days=1)
        serial += 1

    # ==========================================
    # PASO 2: PERÍODOS COMPLETOS
    # ==========================================
    iteration_count = 0
    max_iterations = 1000

    while current_date <= end_date and iteration_count < max_iterations:
        iteration_count += 1

        period_start = current_date

        # Calcular fin del período
        period_end = self._get_period_end_date(current_date, period_months, end_date)

        # Verificar si es el último período
        is_last_period = (period_end >= end_date)

        if is_last_period:
            period_end = end_date

        # Calcular monto del período
        if is_last_period and self.prorate_first_period:
            # Verificar si requiere prorrateo (no termina en último día del mes)
            last_day_of_month = monthrange(period_end.year, period_end.month)[1]

            if period_end.day != last_day_of_month:
                # Último período con prorrateo
                prorated_amount = self._compute_prorated_amount(
                    period_start, period_end, current_rental_fee
                )
            else:
                # Último período sin prorrateo (mes completo)
                prorated_amount = current_rental_fee
        else:
            # Período completo normal
            prorated_amount = current_rental_fee

        # ===== APLICAR INCREMENTO (si corresponde) =====
        if self.increment_recurring_interval and self.increment_percentage:
            months_since_increment = self._get_months_between(
                last_increment_date, period_start
            )

            increment_interval_months = self.increment_recurring_interval * (
                12 if self.increment_period == 'years' else 1
            )

            if months_since_increment >= increment_interval_months:
                # Aplicar incremento
                increment_factor = 1 + (self.increment_percentage / 100)
                current_rental_fee = current_rental_fee * increment_factor
                prorated_amount = current_rental_fee
                last_increment_date = period_start

                # Log del incremento
                _logger.info(
                    "Contrato %s: Incremento del %s%% aplicado en período %s",
                    self.name,
                    self.increment_percentage,
                    period_start.strftime('%d/%m/%Y')
                )

        # Calcular fecha de facturación
        invoice_date = self._get_invoice_date(period_start, period_end)

        # Crear línea
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
        }))

        # Avanzar al siguiente período
        current_date = period_end + relativedelta(days=1)
        serial += 1

    # Prevenir loops infinitos
    if iteration_count >= max_iterations:
        raise ValidationError(_(
            "Se excedió el límite de períodos (1000). "
            "Verifique las fechas del contrato."
        ))

    # Escribir todas las líneas
    self.write({"loan_line_ids": rental_lines})

    # Mensaje de confirmación
    self.message_post(
        body=_("✅ Se generaron %s líneas de pago") % (serial - 1)
    )


# ==========================================
# AGREGAR MÉTODO: action_open_invoice_wizard
# ==========================================

def action_open_invoice_wizard(self):
    """Abre el wizard para generar facturas por período"""
    self.ensure_one()

    return {
        'name': _('Generar Facturas'),
        'type': 'ir.actions.act_window',
        'res_model': 'contract.invoice.wizard',
        'view_mode': 'form',
        'target': 'new',
        'context': {
            'default_contract_id': self.id,
            'default_contract_ids': [(6, 0, [self.id])],
        }
    }


# ==========================================
# MÉTODO AUXILIAR: _compute_prorated_amount
# ==========================================

def _compute_prorated_amount(self, period_start, period_end, base_amount):
    """
    Calcula el monto prorrateado según el método configurado

    :param period_start: Fecha inicio del período
    :param period_end: Fecha fin del período
    :param base_amount: Monto base mensual
    :return: Monto prorrateado
    """
    self.ensure_one()

    if not self.prorate_first_period or self.prorata_computation_type == 'none':
        return base_amount

    if self.prorata_computation_type == 'daily_computation':
        # Método días reales
        days_in_period = (period_end - period_start).days + 1
        total_days_in_month = monthrange(period_start.year, period_start.month)[1]

        prorated = base_amount * (days_in_period / total_days_in_month)

    elif self.prorata_computation_type == 'constant_periods':
        # Método 360 días
        days_360 = days360(period_start, period_end)
        prorated = (base_amount / 30) * days_360

    else:
        # Sin prorrateo
        prorated = base_amount

    return prorated
```

---

## 2️⃣ CREAR WIZARD DE FACTURACIÓN

### 📁 Archivo: `real_estate_bits/wizards/contract_invoice_wizard.py`

```python
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta

class ContractInvoiceWizard(models.TransientModel):
    _name = 'contract.invoice.wizard'
    _description = 'Wizard para Generar Facturas de Contrato'

    # ==========================================
    # CAMPOS
    # ==========================================

    contract_id = fields.Many2one(
        'property.contract',
        string='Contrato',
        required=True
    )

    contract_ids = fields.Many2many(
        'property.contract',
        string='Contratos',
        help='Permitir selección múltiple para generación masiva'
    )

    invoice_date = fields.Date(
        string='Fecha de Factura',
        default=fields.Date.context_today,
        required=True,
        help='Fecha que aparecerá en la factura generada'
    )

    period_start = fields.Date(
        string='Inicio del Período',
        help='Fecha de inicio del período a facturar (opcional)'
    )

    period_end = fields.Date(
        string='Fin del Período',
        help='Fecha de fin del período a facturar (opcional)'
    )

    filter_type = fields.Selection([
        ('pending', 'Solo Cuotas Pendientes'),
        ('all_unpaid', 'Todas las Cuotas Sin Facturar'),
        ('by_period', 'Por Período Específico'),
        ('by_date', 'Por Fecha de Facturación'),
    ], string='Filtro', default='pending', required=True)

    include_commission = fields.Boolean(
        string='Generar Factura de Comisión',
        default=True,
        help='Generar factura de comisión junto con la factura de canon'
    )

    commission_percentage = fields.Float(
        string='Porcentaje Comisión',
        related='contract_id.commission_percentage',
        readonly=True
    )

    preview_lines = fields.One2many(
        'contract.invoice.wizard.line',
        'wizard_id',
        string='Vista Previa',
        compute='_compute_preview_lines'
    )

    total_amount = fields.Monetary(
        string='Total Canon',
        compute='_compute_totals',
        currency_field='currency_id'
    )

    total_commission = fields.Monetary(
        string='Total Comisión',
        compute='_compute_totals',
        currency_field='currency_id'
    )

    grand_total = fields.Monetary(
        string='Total General',
        compute='_compute_totals',
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='contract_id.currency_id',
        readonly=True
    )

    line_count = fields.Integer(
        string='Cantidad de Líneas',
        compute='_compute_preview_lines'
    )

    # ==========================================
    # COMPUTE METHODS
    # ==========================================

    @api.depends('contract_id', 'filter_type', 'period_start',
                 'period_end', 'invoice_date')
    def _compute_preview_lines(self):
        """Genera vista previa de las líneas a facturar"""
        for wizard in self:
            # Buscar cuotas según filtro
            domain = [('contract_id', '=', wizard.contract_id.id)]

            if wizard.filter_type == 'pending':
                # Solo cuotas pendientes con fecha <= hoy
                domain += [
                    ('invoice_id', '=', False),
                    ('date', '<=', fields.Date.context_today(self))
                ]
            elif wizard.filter_type == 'all_unpaid':
                # Todas las cuotas sin facturar
                domain += [('invoice_id', '=', False)]
            elif wizard.filter_type == 'by_period':
                # Por período específico
                if wizard.period_start and wizard.period_end:
                    domain += [
                        ('invoice_id', '=', False),
                        ('period_start', '>=', wizard.period_start),
                        ('period_end', '<=', wizard.period_end)
                    ]
            elif wizard.filter_type == 'by_date':
                # Por fecha de facturación
                domain += [
                    ('invoice_id', '=', False),
                    ('date', '<=', wizard.invoice_date)
                ]

            lines = self.env['loan.line'].search(domain, order='date, serial')
            wizard.line_count = len(lines)

            # Crear líneas de vista previa
            preview_lines = []
            for line in lines:
                preview_lines.append((0, 0, {
                    'loan_line_id': line.id,
                    'serial': line.serial,
                    'name': line.name,
                    'period_start': line.period_start,
                    'period_end': line.period_end,
                    'date': line.date,
                    'amount': line.amount,
                }))

            wizard.preview_lines = preview_lines

    @api.depends('preview_lines', 'include_commission', 'commission_percentage')
    def _compute_totals(self):
        """Calcula totales de canon y comisión"""
        for wizard in self:
            total_canon = sum(wizard.preview_lines.mapped('amount'))
            wizard.total_amount = total_canon

            if wizard.include_commission and wizard.commission_percentage:
                wizard.total_commission = total_canon * (wizard.commission_percentage / 100)
            else:
                wizard.total_commission = 0.0

            wizard.grand_total = total_canon + wizard.total_commission

    # ==========================================
    # ACCIONES
    # ==========================================

    def action_generate_invoices(self):
        """Genera las facturas de canon y comisión"""
        self.ensure_one()

        if not self.preview_lines:
            raise UserError(_("No hay líneas para facturar con los filtros seleccionados"))

        # Obtener líneas de loan
        loan_lines = self.preview_lines.mapped('loan_line_id')

        if not loan_lines:
            raise UserError(_("No se encontraron cuotas para facturar"))

        contract = self.contract_id

        # ===== GENERAR FACTURA DE CANON =====
        invoice_canon = self._create_canon_invoice(contract, loan_lines)

        # ===== GENERAR FACTURA DE COMISIÓN (si aplica) =====
        invoice_commission = False
        if self.include_commission and self.total_commission > 0:
            invoice_commission = self._create_commission_invoice(
                contract,
                self.total_commission,
                loan_lines
            )

        # Marcar líneas como facturadas
        loan_lines.write({'invoice_id': invoice_canon.id})

        # Mensaje de confirmación
        message = _("✅ Facturas generadas exitosamente:\n")
        message += _("- Factura Canon: %s (Monto: %s)\n") % (
            invoice_canon.name,
            invoice_canon.amount_total_signed
        )

        if invoice_commission:
            message += _("- Factura Comisión: %s (Monto: %s)\n") % (
                invoice_commission.name,
                invoice_commission.amount_total_signed
            )

        contract.message_post(body=message)

        # Retornar acción para abrir facturas generadas
        invoices = invoice_canon
        if invoice_commission:
            invoices |= invoice_commission

        return {
            'name': _('Facturas Generadas'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', invoices.ids)],
            'context': {'create': False}
        }

    def _create_canon_invoice(self, contract, loan_lines):
        """Crea la factura de canon"""
        # Determinar cliente
        partner = contract.partner_id

        # Preparar valores de factura
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_date': self.invoice_date,
            'invoice_origin': contract.name,
            'ref': _('Canon Contrato %s') % contract.name,
            'invoice_line_ids': [],
        }

        # Agregar líneas
        for line in loan_lines:
            invoice_line_vals = {
                'name': line.name,
                'quantity': 1,
                'price_unit': line.amount,
                'account_id': contract.account_income.id,
            }
            invoice_vals['invoice_line_ids'].append((0, 0, invoice_line_vals))

        # Crear factura
        invoice = self.env['account.move'].create(invoice_vals)

        return invoice

    def _create_commission_invoice(self, contract, commission_amount, loan_lines):
        """Crea la factura de comisión"""
        # Cliente de comisión (puede ser el propietario o la empresa)
        partner = contract.partner_is_owner_id or contract.company_id.partner_id

        # Preparar valores
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_date': self.invoice_date,
            'invoice_origin': contract.name,
            'ref': _('Comisión Contrato %s') % contract.name,
            'invoice_line_ids': [(0, 0, {
                'name': _('Comisión %s%% - Contrato %s') % (
                    contract.commission_percentage,
                    contract.name
                ),
                'quantity': 1,
                'price_unit': commission_amount,
                'account_id': contract.account_income.id,  # Ajustar cuenta según negocio
            })],
        }

        # Crear factura
        invoice = self.env['account.move'].create(invoice_vals)

        return invoice


# ==========================================
# LÍNEAS DE VISTA PREVIA
# ==========================================

class ContractInvoiceWizardLine(models.TransientModel):
    _name = 'contract.invoice.wizard.line'
    _description = 'Líneas de Vista Previa del Wizard'

    wizard_id = fields.Many2one(
        'contract.invoice.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )

    loan_line_id = fields.Many2one(
        'loan.line',
        string='Línea de Cuota',
        required=True
    )

    serial = fields.Integer(string='#')
    name = fields.Char(string='Descripción')
    period_start = fields.Date(string='Inicio Período')
    period_end = fields.Date(string='Fin Período')
    date = fields.Date(string='Fecha Factura')
    amount = fields.Monetary(string='Monto', currency_field='currency_id')

    currency_id = fields.Many2one(
        'res.currency',
        related='wizard_id.currency_id'
    )
```

---

## 3️⃣ MODIFICAR MODELO `loan.line`

### 📁 Archivo: `real_estate_bits/models/loan_line.py`

```python
# ==========================================
# AGREGAR CAMPO: due_date
# ==========================================

due_date = fields.Date(
    string='Fecha de Vencimiento',
    compute='_compute_due_date',
    store=True,
    help='Fecha límite de pago (normalmente 5 días después de facturación)'
)

payment_terms_days = fields.Integer(
    string='Días de Plazo',
    related='contract_id.payment_terms_days',
    help='Días de plazo para el pago'
)


# ==========================================
# MÉTODO COMPUTE: due_date
# ==========================================

@api.depends('date', 'contract_id.payment_terms_days')
def _compute_due_date(self):
    """Calcula la fecha de vencimiento del pago"""
    for line in self:
        if line.date:
            # Por defecto 5 días, o según configuración del contrato
            days = line.payment_terms_days or 5
            line.due_date = line.date + relativedelta(days=days)
        else:
            line.due_date = False
```

---

## 4️⃣ AGREGAR CAMPO `payment_terms_days` A CONTRACT

### 📁 Archivo: `real_estate_bits/models/property_contract.py`

```python
# ==========================================
# AGREGAR CAMPO: payment_terms_days
# ==========================================

payment_terms_days = fields.Integer(
    string='Días de Plazo para Pago',
    default=5,
    help='Días después de la facturación para el vencimiento del pago'
)
```

---

## 5️⃣ ACTUALIZAR `__manifest__.py`

### 📁 Archivo: `real_estate_bits/__manifest__.py`

```python
{
    'name': 'Real Estate Bits',
    # ... otros campos ...

    'data': [
        # ... otros archivos ...

        # Wizards
        'wizards/contract_invoice_wizard_views.xml',
        'security/ir.model.access.csv',

        # ... otros archivos ...
    ],
}
```

---

## 6️⃣ CREAR VISTA DEL WIZARD

### 📁 Archivo: `real_estate_bits/wizards/contract_invoice_wizard_views.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- ========================================== -->
    <!-- VISTA FORMULARIO DEL WIZARD -->
    <!-- ========================================== -->

    <record id="contract_invoice_wizard_form" model="ir.ui.view">
        <field name="name">contract.invoice.wizard.form</field>
        <field name="model">contract.invoice.wizard</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <group>
                        <group string="📋 Contrato">
                            <field name="contract_id" readonly="1"/>
                            <field name="currency_id" invisible="1"/>
                        </group>

                        <group string="🧾 Configuración de Factura">
                            <field name="invoice_date"/>
                            <field name="filter_type" widget="radio"/>
                        </group>
                    </group>

                    <group invisible="filter_type != 'by_period'">
                        <group string="📅 Período a Facturar">
                            <field name="period_start" required="filter_type == 'by_period'"/>
                            <field name="period_end" required="filter_type == 'by_period'"/>
                        </group>
                    </group>

                    <group>
                        <group string="💵 Comisión">
                            <field name="include_commission"/>
                            <field name="commission_percentage"
                                   invisible="not include_commission"/>
                        </group>

                        <group string="📊 Resumen">
                            <field name="line_count" readonly="1"/>
                            <field name="total_amount" widget="monetary"/>
                            <field name="total_commission" widget="monetary"
                                   invisible="not include_commission"/>
                            <field name="grand_total" widget="monetary"
                                   class="oe_subtotal_footer_separator"/>
                        </group>
                    </group>

                    <notebook>
                        <page string="📋 Vista Previa de Cuotas" name="preview">
                            <field name="preview_lines" readonly="1">
                                <list>
                                    <field name="serial"/>
                                    <field name="name"/>
                                    <field name="period_start"/>
                                    <field name="period_end"/>
                                    <field name="date"/>
                                    <field name="amount" widget="monetary" sum="Total"/>
                                </list>
                            </field>
                        </page>
                    </notebook>
                </sheet>

                <footer>
                    <button name="action_generate_invoices"
                            type="object"
                            string="Generar Facturas"
                            class="btn-primary"
                            invisible="line_count == 0"/>
                    <button string="Cancelar"
                            class="btn-secondary"
                            special="cancel"/>
                </footer>
            </form>
        </field>
    </record>

</odoo>
```

---

## 7️⃣ ACTUALIZAR VISTA DE CONTRATO

### 📁 Archivo: `real_estate_bits/views/property_contract_views.xml`

```xml
<!-- AGREGAR AL FORMULARIO DE CONTRATO -->

<header>
    <!-- ... botones existentes ... -->

    <!-- NUEVO BOTÓN -->
    <button name="action_open_invoice_wizard"
            type="object"
            string="🧾 Generar Facturas"
            invisible="state != 'confirmed'"
            class="oe_highlight"/>
</header>

<!-- DENTRO DEL NOTEBOOK, PESTAÑA DE FECHAS -->

<page string="📅 Fechas y Facturación" name="dates">
    <group>
        <group string="📆 Período del Contrato">
            <field name="date_from"/>
            <field name="date_to"/>
            <field name="date_end"/>
        </group>

        <group string="🧾 Configuración de Facturación">
            <!-- NUEVO CAMPO -->
            <field name="billing_type" widget="radio"/>
            <field name="billing_type_description"
                   readonly="1"
                   class="text-info"/>

            <field name="periodicity"/>
            <field name="recurring_interval"/>
            <field name="billing_date"/>
            <field name="payment_terms_days"/>
            <field name="first_invoice_date"/>
            <field name="first_billing_date" readonly="1"/>
        </group>
    </group>

    <!-- ... resto del código ... -->
</page>

<!-- PESTAÑA DE PRORRATEO -->

<page string="➗ Prorrateo" name="prorate">
    <group>
        <group string="⚙️ Configuración de Prorrateo">
            <field name="prorate_first_period"/>
            <field name="prorata_computation_type"/>
        </group>
    </group>

    <group string="📊 Cálculos de Prorrateo">
        <!-- NUEVOS CAMPOS -->
        <field name="prorate_info_first"
               readonly="1"
               class="alert alert-success"/>
        <field name="prorate_info_last"
               readonly="1"
               class="alert alert-info"/>
    </group>

    <!-- ... resto del código ... -->
</page>
```

---

## 8️⃣ AGREGAR SEGURIDAD

### 📁 Archivo: `real_estate_bits/security/ir.model.access.csv`

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_contract_invoice_wizard,contract.invoice.wizard,model_contract_invoice_wizard,base.group_user,1,1,1,1
access_contract_invoice_wizard_line,contract.invoice.wizard.line,model_contract_invoice_wizard_line,base.group_user,1,1,1,1
```

---

## 📊 EJEMPLO DE USO COMPLETO

### Escenario:

**Contrato:**
- Fecha inicio: 2025-01-15
- Fecha fin: 2025-04-30
- Canon: $1,000,000
- Periodicidad: Mensual
- Billing Type: **Mes Vencido**
- Prorrateo: Activado (Días reales)
- Comisión: 8%
- Días de plazo: 5

### Líneas Generadas con `prepare_lines()`:

```
Línea 1 (Prorrateo):
  📅 Período: 15/01/2025 → 31/01/2025 (17 días)
  💰 Monto: $548,387 (17/31 * $1,000,000)
  🧾 Fecha Factura: 01/02/2025 (mes vencido: después del período)
  ⏰ Vencimiento: 06/02/2025 (5 días después)

Línea 2:
  📅 Período: 01/02/2025 → 28/02/2025
  💰 Monto: $1,000,000
  🧾 Fecha Factura: 01/03/2025
  ⏰ Vencimiento: 06/03/2025

Línea 3:
  📅 Período: 01/03/2025 → 31/03/2025
  💰 Monto: $1,000,000
  🧾 Fecha Factura: 01/04/2025
  ⏰ Vencimiento: 06/04/2025

Línea 4:
  📅 Período: 01/04/2025 → 30/04/2025
  💰 Monto: $1,000,000
  🧾 Fecha Factura: 01/05/2025
  ⏰ Vencimiento: 06/05/2025
```

### Generar Facturas con Wizard:

1. Usuario abre contrato confirmado
2. Click en botón **"🧾 Generar Facturas"**
3. Wizard se abre con:
   - Filtro: "Solo Cuotas Pendientes"
   - Incluir comisión: ✅
   - Vista previa muestra líneas pendientes
4. Click **"Generar Facturas"**
5. Sistema crea:
   - **Factura Canon**: $548,387 (Línea 1)
   - **Factura Comisión**: $43,871 (8% de $548,387)

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [ ] Agregar campo `billing_type` a `property.contract`
- [ ] Agregar campos `prorate_info_first/last` a `property.contract`
- [ ] Agregar campo `payment_terms_days` a `property.contract`
- [ ] Modificar método `_get_invoice_date()`
- [ ] Modificar método `prepare_lines()`
- [ ] Agregar métodos compute para info de prorrateo
- [ ] Crear archivo `contract_invoice_wizard.py`
- [ ] Crear archivo `contract_invoice_wizard_views.xml`
- [ ] Agregar campo `due_date` a `loan.line`
- [ ] Actualizar `__manifest__.py`
- [ ] Agregar permisos en `security/ir.model.access.csv`
- [ ] Actualizar vistas de contrato
- [ ] Probar con datos de ejemplo
- [ ] Validar cálculos de prorrateo
- [ ] Validar generación de facturas

---

🔚 **FIN DE IMPLEMENTACIÓN COMPLETA**

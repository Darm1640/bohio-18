# ============================================================================
# PATCH PARA property_contract.py
# Aplicar mejoras de billing_type, prorrateo correcto y campos informativos
# ============================================================================

"""
INSTRUCCIONES DE APLICACIÓN:

1. Abrir c:\Program Files\Odoo 18.0.20250830\server\addons\real_estate_bits\models\property_contract.py
   con permisos de administrador

2. Aplicar los cambios en el orden indicado

3. Reiniciar Odoo

4. Actualizar el módulo real_estate_bits
"""

# ============================================================================
# PASO 1: AGREGAR CAMPOS NUEVOS (después de línea 258)
# ============================================================================

# BUSCAR ESTA LÍNEA (aproximadamente línea 252):
#     billing_date = fields.Integer(
#         "Día de Facturación",
#         default=1,
#         tracking=True,
#         help="Día del mes en que se genera la factura (1-31)"
#     )
#     is_escenary_propiedad = fields.Boolean("Usar Escenario de Propiedad", default=False, tracking=True)

# REEMPLAZAR CON:

CAMPOS_NUEVOS = '''
    billing_date = fields.Integer(
        "Día de Facturación",
        default=1,
        tracking=True,
        help="Día del mes en que se genera la factura (1-31)"
    )

    # ===== CAMPOS NUEVOS =====
    billing_type = fields.Selection([
        ('arrears', 'Mes Vencido'),      # Factura DESPUÉS del período consumido
        ('advance', 'Mes Anticipado'),   # Factura ANTES del período a consumir
    ], string='Tipo de Facturación',
       default='arrears',
       required=True,
       tracking=True,
       help="""Mes Vencido: La factura se genera después de consumir el período (ej: consumo Feb 1-28, factura Mar 1).
Mes Anticipado: La factura se genera antes de iniciar el período (ej: período Feb 1-28, factura Feb 1).""")

    payment_terms_days = fields.Integer(
        string='Días de Plazo para Pago',
        default=5,
        tracking=True,
        help='Días después de la facturación para el vencimiento del pago'
    )

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
    # ===== FIN CAMPOS NUEVOS =====

    is_escenary_propiedad = fields.Boolean("Usar Escenario de Propiedad", default=False, tracking=True)
'''

# ============================================================================
# PASO 2: AGREGAR MÉTODOS COMPUTE (después de _compute_last_payment_info)
# ============================================================================

# INSERTAR DESPUÉS DE LA LÍNEA 1210 (después del método _compute_last_payment_info)

METODOS_COMPUTE = '''
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
'''

# ============================================================================
# PASO 3: REEMPLAZAR MÉTODO _get_invoice_date (línea 954)
# ============================================================================

# BUSCAR:
#     def _get_invoice_date(self, period_end_date):
#         """Calcula la fecha de facturación basada en billing_date"""
#         ...

# REEMPLAZAR CON:

METODO_GET_INVOICE_DATE = '''
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
'''

# ============================================================================
# PASO 4: REEMPLAZAR MÉTODO prepare_lines (línea 868)
# ============================================================================

# BUSCAR:
#     def prepare_lines(self):
#         """Genera las líneas de cobro de canon usando lógica similar a account_asset"""
#         ...

# REEMPLAZAR MÉTODO COMPLETO CON:

METODO_PREPARE_LINES = '''
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
'''

# ============================================================================
# PASO 5: ACTUALIZAR _compute_prorated_amount (línea 970)
# ============================================================================

# BUSCAR:
#     def _compute_prorated_amount(self, period_start, period_end, base_amount, is_first=False, is_last=False):

# REEMPLAZAR CON:

METODO_COMPUTE_PRORATED_AMOUNT = '''
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
            days_in_period = days360(period_start, period_end)
            prorated = (base_amount / 30) * days_in_period

        else:
            # Sin prorrateo
            prorated = base_amount

        return prorated
'''

# ============================================================================
# PASO 6: ACTUALIZAR TODAS LAS LLAMADAS A _get_invoice_date
# ============================================================================

# BUSCAR todas las llamadas:
#     invoice_date = self._get_invoice_date(period_end)

# REEMPLAZAR CON:
#     invoice_date = self._get_invoice_date(period_start, period_end)

# Esto ocurre en aproximadamente 3 lugares:
# - Línea 925 (dentro de prepare_lines)
# - Línea 1342 (dentro de _prepare_lines_from_date)
# - Posiblemente otros métodos

EJEMPLO_CAMBIO = '''
# ANTES:
invoice_date = self._get_invoice_date(period_end)

# DESPUÉS:
invoice_date = self._get_invoice_date(period_start, period_end)
'''

print("✅ Archivo de parche creado exitosamente")
print("\n" + "="*80)
print("INSTRUCCIONES:")
print("="*80)
print("\n1. Ejecutar Odoo como Administrador")
print("2. Editar el archivo:")
print("   c:\\Program Files\\Odoo 18.0.20250830\\server\\addons\\real_estate_bits\\models\\property_contract.py")
print("\n3. Aplicar los cambios en el orden indicado")
print("\n4. Reiniciar Odoo")
print("\n5. Actualizar el módulo: Settings > Apps > real_estate_bits > Upgrade")
print("\n" + "="*80)

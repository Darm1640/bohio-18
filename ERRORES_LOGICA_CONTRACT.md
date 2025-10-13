# 🚨 ERRORES Y PROBLEMAS EN MODELO CONTRACT

---

## 📊 RESUMEN EJECUTIVO

Se identificaron **5 problemas críticos** en la lógica de contratos:

1. ❌ **Falta campo `billing_type`** (mes vencido/anticipado)
2. ❌ **Prorrateo mal implementado** - No completa el primer mes
3. ❌ **Falta campos informativos** (`prorate_info_first`, `prorate_info_last`)
4. ❌ **Flujo de fechas incorrecto** en las líneas
5. ❌ **Organización visual deficiente** en vistas

---

## 1️⃣ ❌ FALTA CAMPO `billing_type` (MES VENCIDO/ANTICIPADO)

### 📝 Descripción del Problema

El sistema **NO tiene forma de distinguir** entre:
- **Mes Vencido**: Factura se genera DESPUÉS del período consumido
- **Mes Anticipado**: Factura se genera ANTES del período a consumir

### 🎯 Ejemplo del Error

**Contrato:**
- Fecha inicio: 2025-01-15
- Canon: $1,000,000
- Periodicidad: Mensual

**Comportamiento ACTUAL (Incorrecto):**
```
Período 1: 2025-01-15 a 2025-02-14
  └─> Factura: 2025-03-01 (mes siguiente)
  └─> ❌ ERROR: Cliente ya consumió el período pero NO se le facturó a tiempo
```

**Comportamiento ESPERADO (Mes Vencido):**
```
Período 1: 2025-01-15 a 2025-02-14
  └─> Factura: 2025-02-15 (al terminar el período)
  └─> ✅ Factura inmediatamente al terminar el período
```

**Comportamiento ESPERADO (Mes Anticipado):**
```
Período 1: 2025-01-15 a 2025-02-14
  └─> Factura: 2025-01-15 (al INICIAR el período)
  └─> ✅ Cliente paga ANTES de consumir
```

### ✅ Solución Propuesta

```python
# AGREGAR AL MODELO property.contract

billing_type = fields.Selection([
    ('arrears', 'Mes Vencido'),      # Factura al terminar período
    ('advance', 'Mes Anticipado'),   # Factura al iniciar período
], string='Tipo de Facturación', default='arrears', required=True, tracking=True,
   help='Mes Vencido: Factura al finalizar el período. Mes Anticipado: Factura al iniciar.')
```

### 🔧 Modificación Requerida en `_get_invoice_date()`

**ANTES (Incorrecto):**
```python
def _get_invoice_date(self, period_end_date):
    """Calcula la fecha de facturación basada en billing_date"""
    if self.billing_date and self.billing_date > 0:
        try:
            invoice_date = period_end_date.replace(day=self.billing_date)
            if invoice_date < period_end_date:
                invoice_date = invoice_date + relativedelta(months=1)
            return invoice_date
        except ValueError:
            invoice_date = period_end_date + relativedelta(months=1, day=1)
            return invoice_date
    else:
        # Por defecto, primer día del mes siguiente
        return period_end_date + relativedelta(months=1, day=1)
```

**DESPUÉS (Correcto):**
```python
def _get_invoice_date(self, period_start, period_end_date):
    """
    Calcula la fecha de facturación basada en billing_type y billing_date

    :param period_start: Fecha de inicio del período
    :param period_end_date: Fecha de fin del período
    :return: Fecha de facturación
    """
    if self.billing_type == 'advance':
        # MES ANTICIPADO: Factura al INICIO del período
        if self.billing_date and self.billing_date > 0:
            try:
                # Intentar usar el día de facturación en el mes de inicio
                invoice_date = period_start.replace(day=self.billing_date)

                # Si el día de facturación ya pasó en el mes, usar ese día
                if invoice_date < period_start:
                    # Ya pasó, usar el mismo día en el mes actual
                    invoice_date = period_start.replace(day=self.billing_date)

                return invoice_date
            except ValueError:
                # Día no existe en el mes (ej: 31 en febrero)
                # Usar el último día del mes
                last_day = monthrange(period_start.year, period_start.month)[1]
                return period_start.replace(day=last_day)
        else:
            # Sin día específico, usar el primer día del período
            return period_start

    else:  # billing_type == 'arrears' (Mes Vencido - DEFAULT)
        # MES VENCIDO: Factura al TERMINAR el período
        if self.billing_date and self.billing_date > 0:
            try:
                # Intentar usar el día de facturación en el mes siguiente al fin
                next_month = period_end_date + relativedelta(days=1)
                invoice_date = next_month.replace(day=self.billing_date)

                # Si el día de facturación es antes del fin del período,
                # mover al mes siguiente
                if invoice_date <= period_end_date:
                    invoice_date = invoice_date + relativedelta(months=1)

                return invoice_date
            except ValueError:
                # Día no existe en el mes
                invoice_date = period_end_date + relativedelta(months=1, day=1)
                return invoice_date
        else:
            # Por defecto, primer día del mes siguiente al período
            return period_end_date + relativedelta(days=1)
```

### 🔧 Modificación Requerida en `prepare_lines()`

Cambiar la línea donde se llama `_get_invoice_date()`:

**ANTES:**
```python
invoice_date = self._get_invoice_date(period_end)
```

**DESPUÉS:**
```python
invoice_date = self._get_invoice_date(period_start, period_end)
```

---

## 2️⃣ ❌ PRORRATEO MAL IMPLEMENTADO

### 📝 Descripción del Problema

El prorrateo actual **NO completa el primer mes**, genera un problema de facturación:

**Ejemplo:**
- Fecha inicio: 2025-01-15
- Canon: $1,000,000
- Periodicidad: Mensual
- Prorrateo: Activado

**Comportamiento ACTUAL (Incorrecto):**
```
Línea 1: 2025-01-15 a 2025-02-14 (31 días) → $1,000,000 (prorr. 16 días = $516,129)
Línea 2: 2025-02-15 a 2025-03-14 (28 días) → $1,000,000
```

❌ **ERROR**: El cliente solo pagó por 16 días en enero, pero consumió hasta el 14 de febrero.

**Comportamiento ESPERADO (Correcto):**
```
Línea 1 (Prorrateo primer mes):
  Período: 2025-01-15 a 2025-01-31 (17 días de enero)
  Monto: $548,387 (17/31 * $1,000,000)

Línea 2 (Mes completo):
  Período: 2025-02-01 a 2025-02-28 (28 días - mes completo)
  Monto: $1,000,000

Línea 3 (Mes completo):
  Período: 2025-03-01 a 2025-03-31 (31 días - mes completo)
  Monto: $1,000,000
```

✅ **CORRECTO**: El primer período solo cubre los días restantes de enero (17 días), y luego se facturan meses completos.

### ✅ Solución Propuesta

Modificar el método `prepare_lines()` para que el prorrateo SOLO AFECTE el primer período hasta fin de mes:

```python
def prepare_lines(self):
    """Genera las líneas de cobro de canon con prorrateo correcto"""
    self.ensure_one()
    self.loan_line_ids = False
    rental_lines = []

    if not (self.periodicity and self.date_from and self.date_to and self.first_invoice_date):
        return

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

    # ✅ NUEVO: Si hay prorrateo Y el día de inicio NO es día 1
    # Generar PRIMER período prorrateado hasta fin de mes
    if self.prorate_first_period and start_date.day != 1:
        # Primer período: desde start_date hasta fin del mes
        period_start = start_date
        period_end = start_date.replace(day=monthrange(start_date.year, start_date.month)[1])

        # Si el período termina después del fin del contrato, ajustar
        if period_end > end_date:
            period_end = end_date

        # Calcular monto prorrateado
        prorated_amount = self._compute_prorated_amount(
            period_start, period_end, current_rental_fee, is_first=True
        )

        # Fecha de facturación
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

        # Avanzar al primer día del mes siguiente
        current_date = period_end + relativedelta(days=1)
        serial += 1

    # Generar períodos completos desde aquí
    while current_date <= end_date:
        period_start = current_date
        period_end = self._get_period_end_date(current_date, period_months, end_date)

        # Calcular monto
        if period_end >= end_date and self.prorate_first_period:
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

        # Fecha de facturación
        invoice_date = self._get_invoice_date(period_start, period_end)

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
        if serial > 1000:
            raise ValidationError(_("Se excedió el límite de períodos (1000). Verifique las fechas del contrato."))

    self.write({"loan_line_ids": rental_lines})
```

---

## 3️⃣ ❌ FALTAN CAMPOS INFORMATIVOS DE PRORRATEO

### 📝 Descripción del Problema

En la documentación mencioné estos campos pero **NO EXISTEN** en el código:
- `prorate_info_first` - Información del cálculo del primer período
- `prorate_info_last` - Información del cálculo del último período

### ✅ Solución Propuesta

**AGREGAR campos computed:**

```python
# AGREGAR AL MODELO property.contract

prorate_info_first = fields.Char(
    string='Info Prorrateo Primer Período',
    compute='_compute_prorate_info',
    help='Muestra el cálculo del prorrateo del primer período'
)

prorate_info_last = fields.Char(
    string='Info Prorrateo Último Período',
    compute='_compute_prorate_info',
    help='Muestra el cálculo del prorrateo del último período'
)

@api.depends('date_from', 'date_to', 'rental_fee',
             'prorata_computation_type', 'prorate_first_period')
def _compute_prorate_info(self):
    """Calcula y muestra información del prorrateo"""
    for contract in self:
        if not (contract.prorate_first_period and contract.date_from and
                contract.date_to and contract.rental_fee):
            contract.prorate_info_first = False
            contract.prorate_info_last = False
            continue

        # PRIMER PERÍODO
        if contract.date_from.day != 1:
            period_start = contract.date_from
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
                    f"Primer período: {period_start.strftime('%d/%m')} - {period_end.strftime('%d/%m')} "
                    f"({days_in_period}/{total_days} días) = "
                    f"{contract.company_id.currency_id.format(prorated)}"
                )
            elif contract.prorata_computation_type == 'constant_periods':
                days_360 = days360(period_start, period_end)
                prorated = (contract.rental_fee / 30) * days_360
                contract.prorate_info_first = (
                    f"Primer período: {period_start.strftime('%d/%m')} - {period_end.strftime('%d/%m')} "
                    f"({days_360}/30 días método 360) = "
                    f"{contract.company_id.currency_id.format(prorated)}"
                )
            else:
                contract.prorate_info_first = "Sin prorrateo"
        else:
            contract.prorate_info_first = "Inicia día 1 - No requiere prorrateo"

        # ÚLTIMO PERÍODO
        if contract.date_to.day != monthrange(contract.date_to.year, contract.date_to.month)[1]:
            period_end = contract.date_to
            period_start = period_end.replace(day=1)

            days_in_period = (period_end - period_start).days + 1

            if contract.prorata_computation_type == 'daily_computation':
                total_days = monthrange(period_end.year, period_end.month)[1]
                prorated = contract.rental_fee * (days_in_period / total_days)
                contract.prorate_info_last = (
                    f"Último período: {period_start.strftime('%d/%m')} - {period_end.strftime('%d/%m')} "
                    f"({days_in_period}/{total_days} días) = "
                    f"{contract.company_id.currency_id.format(prorated)}"
                )
            elif contract.prorata_computation_type == 'constant_periods':
                days_360 = days360(period_start, period_end)
                prorated = (contract.rental_fee / 30) * days_360
                contract.prorate_info_last = (
                    f"Último período: {period_start.strftime('%d/%m')} - {period_end.strftime('%d/%m')} "
                    f"({days_360}/30 días método 360) = "
                    f"{contract.company_id.currency_id.format(prorated)}"
                )
            else:
                contract.prorate_info_last = "Sin prorrateo"
        else:
            contract.prorate_info_last = "Termina último día del mes - No requiere prorrateo"
```

---

## 4️⃣ ❌ FLUJO DE FECHAS INCORRECTO EN LÍNEAS

### 📝 Descripción del Problema

Las líneas (`loan.line`) tienen **fechas inconsistentes**:

**Campos en loan.line:**
- `date` - ¿Fecha de qué? ¿Facturación? ¿Vencimiento?
- `period_start` - Inicio del período
- `period_end` - Fin del período

❌ **PROBLEMA**: No hay claridad sobre qué representa cada fecha.

### ✅ Solución Propuesta

**MODIFICAR modelo loan.line para agregar campos claros:**

```python
# EN MODELO loan.line (loan_line.py)

date = fields.Date(
    string='Fecha de Facturación',
    help='Fecha en que se genera la factura'
)

period_start = fields.Date(
    string='Inicio del Período',
    help='Fecha de inicio del período de consumo'
)

period_end = fields.Date(
    string='Fin del Período',
    help='Fecha de fin del período de consumo'
)

due_date = fields.Date(
    string='Fecha de Vencimiento',
    compute='_compute_due_date',
    store=True,
    help='Fecha límite de pago'
)

@api.depends('date', 'contract_id.payment_terms_id')
def _compute_due_date(self):
    """Calcular fecha de vencimiento según términos de pago"""
    for line in self:
        if line.date:
            # Por defecto: 5 días después de facturación
            # O según términos de pago del contrato
            line.due_date = line.date + relativedelta(days=5)
        else:
            line.due_date = False
```

---

## 5️⃣ ❌ ORGANIZACIÓN VISUAL DEFICIENTE

### 📝 Descripción del Problema

Las vistas del formulario de contrato están **desorganizadas**:

1. ❌ Campos críticos están ocultos o difíciles de encontrar
2. ❌ No hay separación visual clara entre secciones
3. ❌ Campos de prorrateo no muestran ejemplos de cálculo
4. ❌ No se muestra el flujo de fechas claramente

### ✅ Solución Propuesta

**MEJORAR vista de formulario contract:**

```xml
<!-- property_contract_view_form.xml -->
<record id="property_contract_view_form" model="ir.ui.view">
    <field name="name">property.contract.form</field>
    <field name="model">property.contract</field>
    <field name="arch" type="xml">
        <form>
            <header>
                <button name="action_confirm" type="object" string="Confirmar"
                        invisible="state != 'draft'" class="oe_highlight"/>
                <button name="action_cancel" type="object" string="Cancelar"
                        invisible="state != 'confirmed'"/>
                <button name="prepare_lines" type="object" string="Generar Cuotas"
                        invisible="state != 'draft'" class="oe_highlight"/>
                <field name="state" widget="statusbar"/>
            </header>

            <sheet>
                <!-- BANNER SUPERIOR CON INFORMACIÓN CLAVE -->
                <div class="oe_title">
                    <h1>
                        <field name="name" readonly="1"/>
                    </h1>
                </div>

                <group>
                    <group string="📋 Información Básica">
                        <field name="partner_id"/>
                        <field name="property_id"/>
                        <field name="user_id"/>
                        <field name="contract_type"/>
                    </group>

                    <group string="💰 Valores Financieros">
                        <field name="rental_fee" widget="monetary"/>
                        <field name="insurance_fee"/>
                        <field name="deposit"/>
                        <field name="maintenance"/>
                        <field name="maintenance_type"/>
                    </group>
                </group>

                <notebook>
                    <!-- PESTAÑA: FECHAS Y FACTURACIÓN -->
                    <page string="📅 Fechas y Facturación" name="dates">
                        <group>
                            <group string="📆 Período del Contrato">
                                <field name="date_from"/>
                                <field name="date_to"/>
                                <field name="date_end"/>
                            </group>

                            <group string="🧾 Configuración de Facturación">
                                <field name="billing_type" widget="radio"/>
                                <field name="periodicity"/>
                                <field name="recurring_interval"/>
                                <field name="billing_date"/>
                                <field name="first_invoice_date"/>
                                <field name="first_billing_date" readonly="1"/>
                            </group>
                        </group>

                        <group string="ℹ️ Información de Próximos Pagos">
                            <group>
                                <field name="next_payment_date" readonly="1"/>
                                <field name="next_payment_amount" widget="monetary" readonly="1"/>
                            </group>
                            <group>
                                <field name="last_payment_date" readonly="1"/>
                                <field name="color" invisible="1"/>
                            </group>
                        </group>
                    </page>

                    <!-- PESTAÑA: PRORRATEO -->
                    <page string="➗ Prorrateo" name="prorate">
                        <group>
                            <group string="⚙️ Configuración de Prorrateo">
                                <field name="prorate_first_period"/>
                                <field name="prorata_computation_type"/>
                            </group>
                        </group>

                        <group string="📊 Cálculos de Prorrateo">
                            <field name="prorate_info_first" readonly="1"
                                   class="text-success font-weight-bold"/>
                            <field name="prorate_info_last" readonly="1"
                                   class="text-info font-weight-bold"/>
                        </group>

                        <div class="alert alert-info" role="alert">
                            <strong>ℹ️ Información:</strong>
                            <ul>
                                <li><strong>Sin Prorrateo:</strong> Se factura el valor completo desde el primer día</li>
                                <li><strong>Períodos Constantes (360 días):</strong> Método bancario - todos los meses tienen 30 días</li>
                                <li><strong>Basado en Días:</strong> Cálculo preciso según días reales del mes</li>
                            </ul>
                        </div>
                    </page>

                    <!-- PESTAÑA: INCREMENTOS E INTERESES -->
                    <page string="📈 Incrementos e Intereses" name="adjustments">
                        <group>
                            <group string="📈 Incrementos Automáticos">
                                <field name="increment_recurring_interval"/>
                                <field name="increment_period"/>
                                <field name="increment_percentage"/>
                            </group>

                            <group string="⚠️ Intereses por Mora">
                                <field name="apply_interest"/>
                                <field name="interest_rate"
                                       invisible="not apply_interest"/>
                                <field name="interest_days_grace"
                                       invisible="not apply_interest"/>
                                <field name="interest_method"
                                       invisible="not apply_interest"/>
                            </group>
                        </group>
                    </page>

                    <!-- PESTAÑA: CUOTAS -->
                    <page string="💳 Cuotas de Pago" name="installments">
                        <field name="loan_line_ids" readonly="state == 'confirmed'">
                            <list editable="bottom">
                                <field name="serial"/>
                                <field name="name"/>
                                <field name="period_start"/>
                                <field name="period_end"/>
                                <field name="date" string="Fecha Factura"/>
                                <field name="due_date" string="Vencimiento"/>
                                <field name="amount" widget="monetary"/>
                                <field name="payment_state" widget="badge"/>
                                <field name="invoice_id"/>
                            </list>
                        </field>

                        <group class="oe_subtotal_footer">
                            <field name="amount_total" widget="monetary"/>
                            <field name="paid" widget="monetary"/>
                            <field name="balance" widget="monetary"/>
                        </group>
                    </page>

                    <!-- PESTAÑA: COMISIONES -->
                    <page string="💵 Comisiones" name="commissions">
                        <group>
                            <group>
                                <field name="commission_percentage"/>
                                <field name="commission_calculation_method"/>
                                <field name="total_commission" widget="monetary" readonly="1"/>
                            </group>
                        </group>
                    </page>

                    <!-- PESTAÑA: OTRAS CONFIGURACIONES -->
                    <page string="⚙️ Otras Configuraciones" name="other">
                        <group>
                            <group string="🎬 Escenario">
                                <field name="contract_scenery_id"/>
                                <field name="is_escenary_propiedad"/>
                            </group>

                            <group string="💼 Contabilidad">
                                <field name="account_income"/>
                                <field name="account_security_deposit"/>
                            </group>
                        </group>

                        <group>
                            <group string="🎨 Plantilla">
                                <field name="contract_template"/>
                            </group>

                            <group string="📋 Uso">
                                <field name="contract_use"/>
                                <field name="rental_agreement"/>
                            </group>
                        </group>

                        <group>
                            <field name="descripcion" colspan="2"/>
                        </group>
                    </page>
                </notebook>
            </sheet>

            <!-- CHATTER -->
            <chatter/>
        </form>
    </field>
</record>
```

---

## 📊 RESUMEN DE CAMBIOS REQUERIDOS

| 🔹 Archivo | 📝 Cambio | ⚠️ Prioridad |
|---|---|---|
| `property_contract.py` | Agregar campo `billing_type` | 🔴 CRÍTICO |
| `property_contract.py` | Modificar `_get_invoice_date()` | 🔴 CRÍTICO |
| `property_contract.py` | Modificar `prepare_lines()` | 🔴 CRÍTICO |
| `property_contract.py` | Agregar campos `prorate_info_*` | 🟠 ALTO |
| `property_contract.py` | Agregar método `_compute_prorate_info()` | 🟠 ALTO |
| `loan_line.py` | Agregar campo `due_date` | 🟡 MEDIO |
| `loan_line.py` | Agregar método `_compute_due_date()` | 🟡 MEDIO |
| `property_contract_view_form.xml` | Reorganizar vista completa | 🟢 BAJO |

---

## ✅ VALIDACIONES REQUERIDAS

Después de aplicar los cambios, verificar:

1. ✅ **Prorrateo correcto** - Primer período solo hasta fin de mes
2. ✅ **Facturación anticipada/vencida** funciona correctamente
3. ✅ **Campos informativos** muestran cálculos correctos
4. ✅ **Fechas en líneas** son claras y coherentes
5. ✅ **Vista de formulario** es intuitiva y organizada

---

## 🎯 EJEMPLO COMPLETO ESPERADO

**Contrato:**
- Fecha inicio: 2025-01-15
- Fecha fin: 2025-04-30
- Canon: $1,000,000
- Periodicidad: Mensual
- Prorrateo: Activado (Días reales)
- Tipo facturación: Mes Vencido

**Líneas Generadas (CORRECTO):**

```
Línea 1 - Prorrateo Primer Mes:
  📅 Período: 2025-01-15 → 2025-01-31 (17 días)
  💰 Monto: $548,387 (17/31 * $1,000,000)
  🧾 Fecha Factura: 2025-02-01 (mes vencido)
  ⏰ Vencimiento: 2025-02-06 (5 días después)

Línea 2 - Mes Completo:
  📅 Período: 2025-02-01 → 2025-02-28 (28 días)
  💰 Monto: $1,000,000
  🧾 Fecha Factura: 2025-03-01
  ⏰ Vencimiento: 2025-03-06

Línea 3 - Mes Completo:
  📅 Período: 2025-03-01 → 2025-03-31 (31 días)
  💰 Monto: $1,000,000
  🧾 Fecha Factura: 2025-04-01
  ⏰ Vencimiento: 2025-04-06

Línea 4 - Prorrateo Último Mes:
  📅 Período: 2025-04-01 → 2025-04-30 (30 días)
  💰 Monto: $1,000,000
  🧾 Fecha Factura: 2025-05-01
  ⏰ Vencimiento: 2025-05-06
```

---

🔚 **FIN DEL ANÁLISIS DE ERRORES**

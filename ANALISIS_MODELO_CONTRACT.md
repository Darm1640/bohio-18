# 📊 ANÁLISIS DEL MODELO CONTRACT - property.contract

---

## 🏗️ ► Información General

| 🔹 Propiedad | 📝 Valor |
|---|---|
| **📦 Modelo** | `property.contract` (Contract) |
| **🧬 Hereda de** | `mail.thread`, `mail.activity.mixin`, `portal.mixin` |
| **📁 Archivo** | `real_estate_bits/models/property_contract.py` |
| **📋 Descripción** | Gestión completa de contratos de arrendamiento |
| **📏 Total líneas** | ~1,830 |
| **🎯 Propósito** | Sistema integral de arrendamiento con facturación automática |

🔚 _Fin: Información General_

---

## 🔧 ► FUNCIONES AUXILIARES

### 1️⃣ 🧮 **Cálculo de Días (Método 360)**
```python
def days360(start_date, end_date, method_eu=True):
    """Método bancario de 360 días (12 meses × 30 días)"""
```
- ✅ Usado para prorrateo financiero estandarizado
- 📊 Considera todos los meses como 30 días
- 🏦 Método bancario europeo/americano

### 2️⃣ 📆 **Operaciones con Meses**
```python
def add_months(source_date, months)        # ➕ Suma meses a fecha
def subtract_month(date_a, year=0, month=0) # ➖ Resta meses
```

🔚 _Fin: Funciones Auxiliares_

---

## 📋 ► CAMPOS PRINCIPALES

### 1️⃣ 🏷️ **INFORMACIÓN BÁSICA**

| 🔹 Campo | 📦 Tipo | ⚙️ Default | 📝 Descripción |
|---|---|---|---|
| `name` | Char | 'New' | 🔢 Número de contrato (secuencia) |
| `origin` | Char | - | 📄 Documento fuente |
| `contract_type` | Selection | is_rental | 📋 Tipo de contrato |
| `type` | Selection | - | 🏠 Tipo de propiedad |
| `user_id` | Many2one | current user | 👤 Vendedor |
| `partner_id` | Many2one | - | 👥 Inquilino/Propietario ⚠️ **required** |
| `company_id` | Many2one | current company | 🏢 Compañía |
| `currency_id` | Many2one | company currency | 💱 Moneda |

🔚 _Fin: Información Básica_

---

### 2️⃣ 📅 **FECHAS PRINCIPALES**

#### 🗓️ Fechas Base
| 🔹 Campo | 📦 Tipo | ⚠️ Required | 🔍 Tracking | 📝 Descripción |
|---|---|---|---|---|
| `date_from` | Date | ✅ | ✅ | 🟢 Fecha de inicio |
| `date_to` | Date | ❌ | ✅ | 🔴 Fecha de fin |
| `date_end` | Date | ❌ | ❌ | ⏹️ Fecha real de terminación |
| `first_invoice_date` | Date | ❌ | ✅ | 🧾 Fecha primera factura |

#### 🔢 Fechas Calculadas (Computed)
| 🔹 Campo | 📦 Tipo | 🧮 Compute | 📝 Descripción |
|---|---|---|---|
| `first_billing_date` | Date | ✅ Stored | 📌 Primera factura calculada según billing_date |
| `next_payment_date` | Date | ✅ | ⏭️ Fecha próximo pago pendiente |
| `last_payment_date` | Date | ✅ | ⏮️ Fecha último pago realizado |

🔚 _Fin: Fechas Principales_

---

### 3️⃣ 🔄 **ESTADOS Y WORKFLOW**

#### 📊 Estado del Contrato
```python
state = [
    ("quotation", "💭 Cotización"),           # Etapa inicial
    ("draft", "📝 Pre-Contrato"),             # Borrador
    ("pending_signature", "✍️ Pendiente de Firma"), # Esperando firma
    ("confirmed", "✅ Confirmado"),           # Activo
    ("renew", "🔄 Renovado"),                # Renovación
    ("cancel", "❌ Cancelado")               # Cancelado
]
```

#### ✍️ Estado de Firma
```python
signature_state = [
    ("not_required", "⏭️ No Requerida"),     # Sin firma digital
    ("pending", "⏳ Pendiente"),             # Esperando
    ("signed", "✅ Firmado"),                # Completado
    ("rejected", "❌ Rechazado")             # Rechazado
]
```

#### ⚙️ Campos de Control
| 🔹 Campo | 📦 Tipo | ⚙️ Default | 📝 Descripción |
|---|---|---|---|
| `skip_signature` | Boolean | False | ⏭️ Omitir firma digital |
| `show_payment_schedule` | Boolean | False | 📋 Mostrar tabla de pagos en cotización |
| `color` | Integer | Computed | 🚦 Color según días restantes (semáforo) |

🔚 _Fin: Estados y Workflow_

---

### 4️⃣ 💰 **CONFIGURACIÓN FINANCIERA**

#### 💵 Valores Base
| 🔹 Campo | 📦 Tipo | 🎯 Precisión | 📝 Descripción |
|---|---|---|---|
| `rental_fee` | Float | (25, 2) | 💰 Canon de arrendamiento (computed) |
| `insurance_fee` | Integer | - | 🛡️ Tarifa de seguro ⚠️ **required** |
| `deposit` | Float | - | 💎 Depósito de garantía |
| `rent` | Integer | - | 📆 Renta en meses |
| `maintenance` | Float | Product Price | 🔧 Mantenimiento |

#### 🔧 Tipo de Mantenimiento
```python
maintenance_type = [
    ("percentage", "📊 Porcentaje"),    # % del canon
    ("amount", "💵 Monto")              # Valor fijo
]
```

#### 🧾 Impuestos
| 🔹 Campo | 📦 Tipo | ⚙️ Default | 📝 Descripción |
|---|---|---|---|
| `apply_tax` | Boolean | False | 💼 Aplicar impuesto |
| `tax_status` | Selection | per_installment | 📋 Estado de impuesto |

**🔖 Opciones:**
- `per_installment` - 📅 Por cuota
- `tax_base_amount` - 💵 Monto base

🔚 _Fin: Configuración Financiera_

---

### 5️⃣ 📆 **PERIODICIDAD Y FACTURACIÓN**

#### ⏰ Configuración de Períodos
| 🔹 Campo | 📦 Tipo | ⚙️ Default | ⚠️ Required | 📝 Descripción |
|---|---|---|---|---|
| `periodicity` | Selection | '1' | ✅ | 🔄 Período entre facturaciones |
| `recurring_interval` | Integer | 1 | ✅ | 🔢 Número de períodos |
| `billing_date` | Integer | 1 | ❌ | 📅 Día de facturación (1-31) |

**📊 Periodicidad:**
- `'1'` - 📅 Mensual (cada mes)
- `'3'` - 📆 Trimestral (cada 3 meses)
- `'6'` - 🗓️ Semestral (cada 6 meses)
- `'12'` - 📋 Anual (cada año)

#### ➗ Prorrateo
| 🔹 Campo | 📦 Tipo | ⚙️ Default | 📝 Descripción |
|---|---|---|---|
| `prorate_first_period` | Boolean | True | 🎯 Prorratear primer/último período |
| `prorata_computation_type` | Selection | daily_computation | 🧮 Método de prorrateo |

**🧮 Métodos de Prorrateo:**
1. **`none`** - 🚫 Sin prorrateo (cobra valor completo)
2. **`constant_periods`** - 🏦 360 días (método bancario)
3. **`daily_computation`** - 📅 Basado en días reales

#### ℹ️ Campos Informativos
| 🔹 Campo | 📦 Tipo | 📝 Descripción |
|---|---|---|
| `prorate_info_first` | Char | 📊 Info cálculo primer período (computed) |
| `prorate_info_last` | Char | 📊 Info cálculo último período (computed) |

🔚 _Fin: Periodicidad y Facturación_

---

### 6️⃣ 📈 **INCREMENTOS**

| 🔹 Campo | 📦 Tipo | ⚙️ Default | 📝 Descripción |
|---|---|---|---|
| `increment_recurring_interval` | Integer | - | 🔢 Intervalo de incremento |
| `increment_period` | Selection | years | 📆 Recurrencia (months/years) |
| `increment_percentage` | Float | - | 📊 % de incremento |

**💡 Ejemplo:**
- `increment_recurring_interval = 1` → 🔢 Cada 1 período
- `increment_period = 'years'` → 📅 En años
- `increment_percentage = 4.0` → 📈 4% de incremento
→ ✅ **Resultado:** Incremento del 4% cada año

🔚 _Fin: Incrementos_

---

### 7️⃣ ⚠️ **INTERESES POR MORA**

| 🔹 Campo | 📦 Tipo | ⚙️ Default | 📝 Descripción |
|---|---|---|---|
| `apply_interest` | Boolean | False | 💰 Aplicar intereses |
| `interest_rate` | Float | 0.0 | 📊 Tasa mensual (%) |
| `interest_days_grace` | Integer | 5 | 🕐 Días de gracia |
| `interest_method` | Selection | simple | 🧮 Método de cálculo |

**🧮 Métodos:**
- `simple` - 📐 Interés simple: **I = P × r × t**
- `compound` - 📈 Interés compuesto: **A = P × (1 + r)^t**

**💻 Método de Cálculo:**
```python
def compute_interest(self, base_amount, days_overdue):
    # 🚫 Sin interés si no está activado o dentro del período de gracia
    if not self.apply_interest or days_overdue <= self.interest_days_grace:
        return 0.0

    # ⏰ Días efectivos después del período de gracia
    effective_days = days_overdue - self.interest_days_grace

    if self.interest_method == 'simple':
        # 📐 Interés simple
        interest = base_amount * (self.interest_rate / 100) * (effective_days / 30)
    else:  # compound
        # 📈 Interés compuesto
        months = effective_days / 30
        interest = base_amount * ((1 + self.interest_rate / 100) ** months - 1)

    return interest  # 💰 Monto de interés calculado
```

🔚 _Fin: Intereses por Mora_

---

### 8️⃣ 💵 **COMISIONES**

| 🔹 Campo | 📦 Tipo | 🧮 Computed | 📝 Descripción |
|---|---|---|---|
| `commission_percentage` | Float | ✅ | 📊 % de comisión (default: 8%) |
| `commission_calculation_method` | Selection | ✅ | 🧮 Base de cálculo |
| `total_commission` | Float | ✅ | 💰 Comisión total |

**🧮 Métodos de Cálculo:**
- `gross_amount` - 💵 Sobre monto bruto (sin deducciones)
- `net_amount` - 💸 Sobre monto neto (con deducciones)
- `rental_fee_only` - 🏠 Solo canon (sin extras)

🔚 _Fin: Comisiones_

---

### 9️⃣ 🏠 **RELACIÓN CON PROPIEDAD**

| 🔹 Campo | 📦 Tipo | 🎯 Domain | 📝 Descripción |
|---|---|---|---|
| `property_id` | Many2one | is_property=True, state=free | 🏘️ Propiedad ⚠️ **required** |
| `partner_is_owner_id` | Many2one | Related | 👤 Propietario de la propiedad |
| `is_multi_propietario` | Boolean | Related | 👥 ¿Multi-propietario? |
| `owners_lines` | One2many | Related | 📋 Líneas de propietarios |
| `property_code` | Char | Related, Stored | 🔢 Código de propiedad |
| `property_area` | Float | Related, Stored | 📐 Área |
| `price_per_m` | Float | Related, Stored | 💰 Precio base |
| `floor` | Integer | Related, Stored | 🏢 Piso |
| `address` | Char | Related, Stored | 📍 Dirección |

🔚 _Fin: Relación con Propiedad_

---

### 🔟 🎯 **PROYECTO Y ESCENARIO**

| 🔹 Campo | 📦 Tipo | 📝 Descripción |
|---|---|---|
| `project_id` | Many2one | 🏗️ Proyecto (related de property) |
| `project_code` | Char | 🔢 Código proyecto |
| `region_id` | Many2one | 🗺️ Región |
| `contract_scenery_id` | Many2one | 🎬 Escenario ⚠️ **required** |
| `is_escenary_propiedad` | Boolean | 🔄 Usar escenario de propiedad |

🔚 _Fin: Proyecto y Escenario_

---

### 1️⃣1️⃣ 🔗 **RELACIONES Y CONTADORES**

#### 📋 Líneas del Contrato
| 🔹 Campo | 📦 Tipo | 📝 Descripción |
|---|---|---|
| `loan_line_ids` | One2many | 💳 Cuotas de pago (loan.line) |
| `debit_line_ids` | One2many | 📄 Notas de débito programadas |

#### 🔢 Contadores
| 🔹 Campo | 📦 Tipo | 📝 Descripción |
|---|---|---|
| `voucher_count` | Integer | 🧾 Cantidad de comprobantes |
| `entry_count` | Integer | 📜 Cantidad de facturas |

#### 🔗 Relaciones
| 🔹 Campo | 📦 Tipo | 📝 Descripción |
|---|---|---|
| `payment_ids` | Many2many | 💰 Pagos relacionados |
| `reservation_id` | Many2one | 📌 Reserva origen |

🔚 _Fin: Relaciones y Contadores_

---

### 1️⃣2️⃣ 💼 **CUENTAS CONTABLES**

| 🔹 Campo | 📦 Tipo | ⚙️ Default | 📝 Descripción |
|---|---|---|---|
| `account_income` | Many2one | Config param | 💵 Cuenta de ingresos |
| `account_security_deposit` | Many2one | Config param | 💎 Cuenta depósito |

🔚 _Fin: Cuentas Contables_

---

### 1️⃣3️⃣ 🔢 **CAMPOS CALCULADOS**

| 🔹 Campo | 📦 Tipo | 🧮 Compute | 📝 Descripción |
|---|---|---|---|
| `paid` | Float | ✅ | ✅ Monto pagado |
| `balance` | Float | ✅ | ⚖️ Saldo pendiente |
| `amount_total` | Float | ✅ | 💰 Monto total |
| `next_payment_amount` | Float | ✅ | ⏭️ Monto próximo pago |

🔚 _Fin: Campos Calculados_

🔚 _**FIN: CAMPOS PRINCIPALES**_

---

## 🔧 ► MÉTODOS PRINCIPALES

### 1️⃣ 📋 **GESTIÓN DE CUOTAS**

#### 🎯 `prepare_lines()` - Generar Cuotas
```python
def prepare_lines(self):
    """Genera líneas de cobro de canon"""
    # 1. ✅ Validar datos requeridos
    # 2. 📅 Calcular períodos desde date_from hasta date_to
    # 3. ➗ Aplicar prorrateo si corresponde
    # 4. 📈 Aplicar incrementos automáticos
    # 5. 📆 Calcular fecha de facturación según billing_date
    # 6. 💾 Crear líneas de loan.line
```

**✨ Características:**
- ✅ Prorrateo primer/último período
- 📈 Incrementos automáticos
- 📅 Día de facturación configurable
- 🛡️ Prevención de loops infinitos (max 1000 períodos)

#### 🔧 Métodos Auxiliares de Preparación
```python
📅 _get_period_end_date(start_date, period_months, contract_end_date)
🗓️ _get_invoice_date(period_end_date)
➗ _compute_prorated_amount(period_start, period_end, base_amount)
🧮 _get_months_between(start_date, end_date)
```

🔚 _Fin: Gestión de Cuotas_

---

### 2️⃣ 🧾 **FACTURACIÓN AUTOMÁTICA**

#### 🤖 `auto_rental_invoice()` - Crear Facturas
```python
def auto_rental_invoice(self):
    """Crear facturas automáticas de alquiler"""
    # 🔍 Buscar cuotas pendientes (loan.line sin invoice_id)
    # 🔀 Procesar según tipo:
    #   - 👤 Contrato simple → _create_invoice_single_owner()
    #   - 🏘️ Multi-propiedad → _create_invoice_multi_property()
    #   - 👥 Multi-propietario → _create_invoice_multi_owner()
```

**📊 Tipos de Facturación:**

1️⃣ **👤 Single Owner** (Estándar)
   - 📄 Una factura por cuota
   - 👥 Cliente = partner_id del contrato

2️⃣ **👥 Multi-Owner** (Multi-propietario)
   - 📋 Una factura por cada propietario
   - ➗ Monto proporcional según % de propiedad
   - 👤 Cliente = cada owner

3️⃣ **🏘️ Multi-Property** (Multi-propiedad)
   - 🔀 Divide monto entre propiedades activas
   - 👥 Cada propiedad puede tener multi-owner
   - 📊 Proporcional según rental_fee

🔚 _Fin: Facturación Automática_

---

### 3️⃣ 🔄 **WORKFLOW DE ESTADOS**

#### ⚡ Transiciones de Estado
```python
💭➡️📝  action_quotation_to_draft()   # Cotización → Pre-contrato
📝➡️💭  action_back_to_quotation()    # Pre-contrato/Pendiente → Cotización
📝➡️✍️  action_send_for_signature()  # Draft → Pendiente Firma
✍️➡️✅  action_mark_signed()          # Marcar como firmado
✍️➡️❌  action_reject_signature()     # Rechazar firma
📝➡️✅  action_confirm()              # Confirmar contrato
❌      action_cancel()               # Cancelar contrato
```

#### ✅ `action_confirm()` - Validaciones
```python
def action_confirm(self):
    # 1. 📋 Validar líneas de pago generadas
    # 2. 👥 Validar cliente/inquilino
    # 3. 🏠 Validar propiedad
    # 4. ✍️ Validar firma (si no está skip_signature)
    # 5. 🔍 Verificar contratos traslapados
    # 6. 🏘️ Cambiar estado de propiedad a "on_lease"
    # 7. 🔢 Generar número de contrato (secuencia)
    # 8. ✅ Cambiar estado a "confirmed"
```

🔚 _Fin: Workflow de Estados_

---

### 4️⃣ 📋 **PLANTILLAS Y CONFIGURACIÓN**

#### 🎨 `_onchange_contract_template()` - Aplicar Plantilla
```python
contract_template = [
    ('standard_local', '🏢 Contrato Local Estándar'),
    ('commercial', '💼 Contrato Comercial'),
    ('residential', '🏠 Contrato Residencial'),
    ('luxury', '💎 Contrato Premium'),
]
```

**⚙️ Configuraciones por Plantilla:**

| 📋 Template | 💵 Comisión | ⚠️ Interés | 🕐 Días Gracia | 📈 Incremento | 📆 Periodicidad |
|---|---|---|---|---|---|
| **🏢 standard_local** | 8% | 1.5% | 5 | 4% | Mensual |
| **💼 commercial** | 6% | 2.0% | 3 | 6% | Mensual |
| **🏠 residential** | 10% | 1.0% | 10 | 3.5% | Mensual |
| **💎 luxury** | 5% | 1.5% | 15 | 5% | Trimestral |

🔚 _Fin: Plantillas y Configuración_

---

### 5️⃣ 🔄 **RECALCULAR CUOTAS FUTURAS**

#### 🔁 `compute_depreciation_board()` - Similar a Account Asset
```python
def compute_depreciation_board(self, date=False):
    """Recalcular líneas futuras no pagadas"""
    # 1. 🗑️ Eliminar líneas futuras no pagadas
    # 2. 🔄 Regenerar líneas con prepare_lines()
    # 3. 📝 Log en chatter
```

#### 🏘️ Multi-Propiedad
```python
🔄 _recalculate_future_installments_on_line_change()
📅 _prepare_lines_from_date(start_date)
🏠 _get_active_properties_in_period(period_start, period_end)
💰 _calculate_period_rental_fee(period_start, period_end, base_rental_fee)
```

🔚 _Fin: Recalcular Cuotas Futuras_

---

### 6️⃣ 🔗 **INTEGRACIÓN CON RESERVAS**

#### 🎯 `create_from_reservation()` - Crear desde Reserva
```python
@api.model
def create_from_reservation(self, reservation_id):
    """Convierte reserva en contrato"""
    # 📋 Copia datos de la reserva
    # ⚙️ Aplica configuración por defecto
    # ✅ Marca reserva como convertida
```

**⚙️ Valores por Defecto:**
- 💵 commission_percentage: 8.0
- ⚠️ interest_rate: 1.5
- 🕐 interest_days_grace: 5
- 📈 increment_percentage: 4.0
- ✅ apply_interest: True
- 📅 periodicity: '1' (Mensual)

🔚 _Fin: Integración con Reservas_

🔚 _**FIN: MÉTODOS PRINCIPALES**_

---

## ⚙️ ► MÉTODOS COMPUTE IMPORTANTES

### 1️⃣ 🚦 **Color del Contrato (Semáforo)**
```python
@api.depends('date_to', 'state')
def _compute_color(self):
    # 🔴 Rojo (1): < 30 días o vencido
    # 🟠 Naranja (2): 30-60 días
    # 🟡 Amarillo (3): 60-90 días
    # 🟢 Verde (10): > 90 días o no confirmado
```

### 2️⃣ 💰 **Canon de Arrendamiento**
```python
@api.depends("rent", "property_area", "property_id", "rental_agreement",
             "is_multi_property", "contract_line_ids.rental_fee")
def _compute_rental_fee(self):
    if is_multi_property:
        # 🏘️ Suma de líneas activas
    else:
        # 🏠 Valor de la propiedad
```

### 3️⃣ ➗ **Información de Prorrateo**
```python
@api.depends('date_from', 'date_to', 'rental_fee',
             'prorata_computation_type', 'prorate_first_period')
def _compute_prorate_info(self):
    # 🧮 Calcula y muestra cálculo del prorrateo
    # 📅 Primer período y último período
```

### 4️⃣ 📅 **Fechas de Pago**
```python
@api.depends('loan_line_ids.date', 'loan_line_ids.payment_state')
def _compute_next_payment_info(self):
    # ⏭️ Próxima cuota pendiente

@api.depends('loan_line_ids.date', 'loan_line_ids.payment_state')
def _compute_last_payment_info(self):
    # ⏮️ Última cuota pagada
```

🔚 _Fin: Métodos Compute Importantes_

---

## ✅ ► VALIDACIONES (Constraints)

### 1️⃣ 📅 **Fechas**
```python
@api.constrains("date_from", "date_to")
def _check_dates(self):
    # ✅ date_from < date_to
    # ✅ first_invoice_date >= date_from
```

### 2️⃣ 🔢 **Valores Numéricos**
```python
@api.constrains('billing_date')
def _check_billing_date(self):
    # ✅ 1 <= billing_date <= 31

@api.constrains('rental_fee')
def _check_rental_fee(self):
    # ✅ rental_fee > 0 para contratos de arrendamiento

@api.constrains('increment_percentage', 'increment_recurring_interval')
def _check_increment(self):
    # ✅ increment_percentage >= 0
    # ✅ Si > 0, debe tener intervalo válido
```

### 3️⃣ ⚠️ **Intereses**
```python
@api.constrains('interest_rate', 'interest_days_grace')
def _check_interest_config(self):
    if apply_interest:
        # ✅ 0 <= interest_rate <= 50
        # ✅ interest_days_grace >= 0
```

### 4️⃣ 🔄 **Intervalo Recurrente**
```python
@api.constrains("recurring_interval")
def _check_recurring_interval(self):
    # ✅ recurring_interval > 0
```

🔚 _Fin: Validaciones (Constraints)_

---

## 🔗 ► INTEGRACIONES

### 1️⃣ 🌐 **Portal del Cliente**
```python
def _compute_access_url(self):
    # 🔗 URL: /my/contract/{id}
    # 👥 Vista del cliente
```

### 2️⃣ 🔧 **Wizard de Modificación**
```python
def action_modify_contract(self):
    # 📝 Abre wizard unificado: modify.contract.wizard
    # ✏️ Permite editar contrato confirmado
```

### 3️⃣ 💼 **Account Asset (Similitud)**
```python
def action_asset_modify(self):
    # 🔄 Alias para action_modify_contract()
    # 🔗 Compatibilidad con módulo contable
```

🔚 _Fin: Integraciones_

---

## 📊 ► MODELO RELACIONADO: account.debit.term.line

**📝 Descripción:** Líneas de notas de débito/intereses automáticos

| 🔹 Campo | 📦 Tipo | ⚙️ Default | 📝 Descripción |
|---|---|---|---|
| `sequence` | Integer | 10 | 🔢 Orden |
| `contract_id` | Many2one | - | 📄 Contrato (cascade) |
| `name` | Char | Nota de Débito | 📋 Descripción |
| `value_amount` | Float | 100.0 | 📊 Porcentaje (0-100) |
| `nb_days` | Integer | 0 | ⏰ Días después vencimiento |

**🔧 Método:**
```python
def _get_due_date(self, date_ref):
    """Calcula fecha de vencimiento"""
    # 📅 date_ref + nb_days
    return date_ref + relativedelta(days=self.nb_days)
```

🔚 _Fin: Modelo Relacionado_

---

## 🎯 ► CARACTERÍSTICAS DESTACADAS

### ✅ Ventajas del Diseño

1️⃣ **🔄 Workflow Completo**
   - 💭 Cotización → 📝 Pre-contrato → ✍️ Firma → ✅ Confirmación
   - 🔀 Estados de firma independientes
   - ✅ Validaciones en cada paso

2️⃣ **💰 Facturación Flexible**
   - 🏘️ Soporta multi-propiedad
   - 👥 Soporta multi-propietario
   - ➗ Prorrateo configurable (3 métodos)

3️⃣ **🤖 Automatización**
   - 📋 Generación automática de cuotas
   - 🧾 Facturación automática (`auto_rental_invoice`)
   - 📈 Incrementos automáticos

4️⃣ **⚠️ Gestión de Mora**
   - 💰 Intereses configurables (simple/compuesto)
   - 🕐 Días de gracia
   - 👁️ Vista previa de cálculos

5️⃣ **🎨 Plantillas Predefinidas**
   - 📋 4 plantillas con configuración completa
   - ⚙️ Aplicación automática de valores

6️⃣ **🔗 Integración**
   - 🌐 Portal del cliente
   - 📌 Reservas → Contratos
   - 🔧 Wizard de modificación

7️⃣ **📝 Auditoría**
   - 🔍 Tracking en campos clave
   - 💬 Herencia de mail.thread (chatter)
   - 📊 Logs automáticos de cambios

🔚 _Fin: Características Destacadas_

---

## 📝 ► FLUJO TÍPICO DE TRABAJO

```
1️⃣ 💭 CREAR COTIZACIÓN
   └─> 📊 state = 'quotation'
   └─> ⚙️ Configurar: cliente, propiedad, fechas, canon

2️⃣ 📋 GENERAR CUOTAS
   └─> 🎯 prepare_lines()
   └─> ➗ Aplica prorrateo, incrementos, día facturación

3️⃣ 📝 CONVERTIR A PRE-CONTRATO
   └─> 🔄 action_quotation_to_draft()
   └─> 📊 state = 'draft'

4️⃣ ✍️ ENVIAR PARA FIRMA (opcional)
   └─> 📤 action_send_for_signature()
   └─> 📊 state = 'pending_signature'
   └─> ✍️ signature_state = 'pending'

5️⃣ ✅ CONFIRMAR FIRMA
   └─> ✓ action_mark_signed()
   └─> ✍️ signature_state = 'signed'

6️⃣ ✅ CONFIRMAR CONTRATO
   └─> 🎯 action_confirm()
   └─> ✅ Validaciones
   └─> 🏠 Cambiar propiedad a 'on_lease'
   └─> 📊 state = 'confirmed'

7️⃣ 🧾 FACTURACIÓN AUTOMÁTICA
   └─> 🤖 Cron ejecuta auto_rental_invoice()
   └─> 📄 Crea facturas de cuotas vencidas

8️⃣ 🔧 MODIFICACIÓN (si es necesario)
   └─> 📝 action_modify_contract()
   └─> 🔧 Wizard de modificación
   └─> 🔄 Recalcula cuotas futuras
```

🔚 _Fin: Flujo Típico de Trabajo_

---

## 🔍 ► PUNTOS CLAVE DE IMPLEMENTACIÓN

1️⃣ **➗ Prorrateo Inteligente:**
   - 🏦 Método 360 días (financiero)
   - 📅 Días reales (preciso)
   - 🚫 Sin prorrateo (simple)

2️⃣ **📈 Incrementos Automáticos:**
   - 📆 Por meses o años
   - 📊 Porcentaje configurable
   - 🤖 Aplicación automática en cuotas

3️⃣ **👥 Multi-tenant:**
   - 🏘️ Multi-propiedad: Varias propiedades en un contrato
   - 👥 Multi-propietario: Varios dueños de una propiedad
   - ➗ Facturación proporcional

4️⃣ **💵 Comisiones:**
   - 🧮 3 métodos de cálculo
   - ⚙️ Configuración por defecto de empresa
   - 💰 Total calculado automáticamente

5️⃣ **⚠️ Mora:**
   - 📐 Interés simple o compuesto
   - 🕐 Días de gracia
   - 👁️ Vista previa de cálculos

🔚 _Fin: Puntos Clave de Implementación_

---

## 📊 RESUMEN ESTADÍSTICO

| 🔹 Métrica | 🔢 Valor |
|---|---|
| 📦 **Total de campos** | ~80+ |
| 🔧 **Total de métodos** | ~50+ |
| 📏 **Líneas de código** | ~1,830 |
| ✅ **Validaciones (constraints)** | 6 |
| 🧮 **Métodos compute** | 10+ |
| 🔄 **Estados de workflow** | 6 |
| 🎨 **Plantillas predefinidas** | 4 |
| ➗ **Métodos de prorrateo** | 3 |
| 💰 **Métodos de interés** | 2 |

---

## 🎯 CONCLUSIÓN

Este modelo es el **💎 corazón del sistema de arrendamiento**, con funcionalidades avanzadas de:

- 🧾 **Facturación automática**
- ➗ **Prorrateo inteligente**
- 📈 **Incrementos automáticos**
- ⚠️ **Gestión de mora**
- 👥 **Multi-propiedad y multi-propietario**
- 🔄 **Workflow completo con validaciones**
- 🎨 **Plantillas configurables**
- 📊 **Auditoría y tracking**

---

🔚 **FIN DEL ANÁLISIS - MODELO CONTRACT** 📊

---

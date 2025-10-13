# ============================================================================
# PATCH PARA loan_line.py
# Agregar campo due_date (fecha de vencimiento del pago)
# ============================================================================

"""
INSTRUCCIONES DE APLICACIÓN:

1. Abrir c:\Program Files\Odoo 18.0.20250830\server\addons\real_estate_bits\models\loan_line.py
   con permisos de administrador

2. Aplicar los cambios indicados

3. Reiniciar Odoo

4. Actualizar el módulo real_estate_bits
"""

# ============================================================================
# PASO 1: AGREGAR CAMPO due_date (después de línea 43)
# ============================================================================

# BUSCAR ESTAS LÍNEAS (aproximadamente línea 39-44):
#     commission = fields.Float("Comisión", digits=(16, 2))
#     commission_percentage = fields.Float("% Comisión", default=8.0)
#     commission_invoice_ids = fields.Many2many('account.move', string='Facturas de Comisión', copy=False)
#     period_start = fields.Date("Inicio del periodo")
#     period_end = fields.Date("Fin del periodo")

# AGREGAR DESPUÉS:

CAMPO_DUE_DATE = '''
    commission = fields.Float("Comisión", digits=(16, 2))
    commission_percentage = fields.Float("% Comisión", default=8.0)
    commission_invoice_ids = fields.Many2many('account.move', string='Facturas de Comisión', copy=False)
    period_start = fields.Date("Inicio del periodo")
    period_end = fields.Date("Fin del periodo")

    # ===== CAMPO NUEVO: Fecha de Vencimiento =====
    due_date = fields.Date(
        string='Fecha de Vencimiento',
        compute='_compute_due_date',
        store=True,
        help='Fecha límite de pago (normalmente 5 días después de facturación)'
    )

    payment_terms_days = fields.Integer(
        string='Días de Plazo',
        related='contract_id.payment_terms_days',
        readonly=True,
        help='Días de plazo para el pago desde la fecha de factura'
    )
'''

# ============================================================================
# PASO 2: AGREGAR MÉTODO _compute_due_date (antes de make_invoice)
# ============================================================================

# INSERTAR ANTES DE LA LÍNEA 66 (antes del método make_invoice):

METODO_COMPUTE_DUE_DATE = '''
    @api.depends('date', 'payment_terms_days')
    def _compute_due_date(self):
        """Calcula la fecha de vencimiento del pago"""
        for line in self:
            if line.date:
                # Usar días de plazo del contrato, o 5 por defecto
                days = line.payment_terms_days or 5
                line.due_date = line.date + relativedelta(days=days)
            else:
                line.due_date = False

    def make_invoice(self):
'''

# ============================================================================
# PASO 3: ACTUALIZAR MÉTODO _compute_overdue_info (línea 374)
# ============================================================================

# BUSCAR:
#     @api.depends('date', 'payment_state')
#     def _compute_overdue_info(self):
#         """Calcular información de mora"""
#         today = fields.Date.today()
#
#         for line in self:
#             if line.payment_state == 'paid' or not line.date:
#                 line.days_overdue = 0
#                 line.is_overdue = False
#                 continue
#
#             # Días desde vencimiento
#             days_since_due = (today - line.date).days

# REEMPLAZAR CON:

METODO_COMPUTE_OVERDUE_INFO_MEJORADO = '''
    @api.depends('due_date', 'payment_state')
    def _compute_overdue_info(self):
        """
        Calcular información de mora usando due_date (fecha de vencimiento)
        en lugar de date (fecha de factura)
        """
        today = fields.Date.today()

        for line in self:
            if line.payment_state == 'paid':
                line.days_overdue = 0
                line.is_overdue = False
                continue

            # Usar due_date si existe, si no usar date como fallback
            reference_date = line.due_date or line.date

            if not reference_date:
                line.days_overdue = 0
                line.is_overdue = False
                continue

            # Días desde vencimiento
            days_since_due = (today - reference_date).days

            if days_since_due > 0:
                line.days_overdue = days_since_due
                line.is_overdue = True
            else:
                line.days_overdue = 0
                line.is_overdue = False
'''

# ============================================================================
# DOCUMENTACIÓN DE FECHAS EN LOAN.LINE
# ============================================================================

DOCUMENTACION_FECHAS = '''
# ============================================================================
# DOCUMENTACIÓN: FLUJO DE FECHAS EN loan.line
# ============================================================================

Un registro de loan.line (cuota de pago) tiene 4 fechas importantes:

1. **period_start** (Inicio del Período)
   - Fecha de inicio del período de consumo
   - Ejemplo: 2025-01-15 (inicio del primer período)

2. **period_end** (Fin del Período)
   - Fecha de fin del período de consumo
   - Ejemplo: 2025-01-31 (fin del primer mes)

3. **date** (Fecha de Factura)
   - Fecha en que se genera/envía la factura
   - Depende del billing_type del contrato:
     * Mes Vencido: Después del período (ej: 2025-02-01)
     * Mes Anticipado: Al inicio del período (ej: 2025-01-15)
   - Se calcula con _get_invoice_date(period_start, period_end)

4. **due_date** (Fecha de Vencimiento) [NUEVO]
   - Fecha límite para pagar sin mora
   - Se calcula: date + payment_terms_days
   - Ejemplo: 2025-02-01 + 5 días = 2025-02-06

# ============================================================================
# EJEMPLO COMPLETO DE FLUJO
# ============================================================================

Contrato:
- Fecha inicio: 2025-01-15
- Canon: $1,000,000
- Billing type: Mes Vencido
- Payment terms: 5 días
- Prorrateo: Activado

Línea 1 (Prorrateo):
├─ period_start: 2025-01-15  (inicio del consumo)
├─ period_end:   2025-01-31  (fin del mes de enero)
├─ date:         2025-02-01  (factura al día siguiente - mes vencido)
└─ due_date:     2025-02-06  (vencimiento: 5 días después)

Línea 2 (Mes completo):
├─ period_start: 2025-02-01
├─ period_end:   2025-02-28
├─ date:         2025-03-01  (factura al día siguiente)
└─ due_date:     2025-03-06  (vencimiento: 5 días después)

# ============================================================================
# CÁLCULO DE MORA
# ============================================================================

La mora se calcula desde due_date (NO desde date):

Ejemplo:
- due_date: 2025-02-06
- Pago realizado: 2025-02-15
- Días de mora: 9 días (desde 06 hasta 15)

Si el contrato tiene:
- interest_days_grace: 5
- Días efectivos de mora: 9 - 5 = 4 días

# ============================================================================
'''

print("✅ Archivo de parche para loan_line.py creado exitosamente")
print("\n" + "="*80)
print("CAMBIOS EN loan_line.py:")
print("="*80)
print("\n✅ AGREGAR:")
print("  - Campo 'due_date' (fecha de vencimiento)")
print("  - Campo 'payment_terms_days' (related de contrato)")
print("  - Método '_compute_due_date()' para calcular vencimiento")
print("\n✅ MODIFICAR:")
print("  - Método '_compute_overdue_info()' para usar due_date en lugar de date")
print("\n📊 FLUJO DE FECHAS:")
print("  period_start → period_end → date (factura) → due_date (vencimiento)")
print("\n" + "="*80)
print("\nVer documentación completa en el código del parche")
print("="*80)

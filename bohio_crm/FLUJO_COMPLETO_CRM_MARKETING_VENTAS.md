# 🔄 FLUJO COMPLETO CRM: MARKETING → VENTAS → RESERVA → CONTRATO

## 📊 NUEVOS CAMPOS AGREGADOS

### **1. MARKETING (service_interested = 'marketing')**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `marketing_campaign_type` | Selection | social_media, google_ads, facebook_ads, instagram_ads, email_marketing, print_media, outdoor, radio_tv, property_portals, event |
| `marketing_quantity` | Integer | Cantidad de publicaciones/anuncios/impresiones |
| `marketing_schedule` | Selection | morning, afternoon, evening, full_day, weekend, business_hours |
| `marketing_estimated_reach` | Integer | Personas estimadas a alcanzar |
| `marketing_budget_allocated` | Monetary | Presupuesto asignado a la campaña |
| `marketing_start_date` | Date | Fecha inicio de campaña |
| `marketing_end_date` | Date | Fecha fin de campaña |
| `marketing_description` | Text | Descripción completa (objetivos, público, mensaje) |

---

### **2. CAPTACIÓN (service_interested = 'consign')**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `captured_by_id` | Many2one(res.users) | Vendedor que consiguió el inmueble |
| `capture_date` | Date | Fecha de captación |
| `capture_source` | Selection | referral, cold_call, door_to_door, website, social_media, advertising, existing_client |
| `capture_commission_rate` | Float | % Comisión (default: 2%) |
| `capture_commission_amount` | Monetary | Monto calculado automáticamente |

---

### **3. PRÉSTAMO/FINANCIACIÓN (Venta/Proyectos)**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `requires_financing` | Boolean | Requiere financiación |
| `loan_type` | Selection | bank_mortgage, developer_financing, leasing, subsidized, other |
| `loan_amount` | Monetary | Monto del préstamo |
| `loan_bank_id` | Many2one(res.partner) | Entidad financiera |
| `loan_approval_status` | Selection | not_applied, pending, pre_approved, approved, rejected |
| `loan_document_ids` | Many2many(ir.attachment) | Documentos (certificados, extractos, declaraciones) |

---

### **4. RESERVA (Todos los servicios inmobiliarios)**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `reservation_id` | Many2one(property.reservation) | Reserva asociada |
| `reservation_count` | Integer | # Reservas del cliente |
| `ideal_visit_date` | Datetime | Fecha ideal para visita |
| `visit_notes` | Text | Notas (preferencias, acompañantes) |
| `has_conflicting_visit` | Boolean | Hay otra visita programada |
| `conflicting_visit_info` | Char | Información del conflicto |

---

### **5. CONTRATO**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `contract_template_id` | Many2one(contract.template) | Template de contrato seleccionado |

---

## 🔄 FLUJO 1: MARKETING → VENTA

```
┌─────────────────────────────────────────────────────────────────┐
│  1. LEAD DE MARKETING                                           │
│  service_interested = 'marketing'                               │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │  Cliente solicita campaña publicitaria
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. CONFIGURACIÓN DE CAMPAÑA                                    │
│  - Tipo: Facebook Ads / Google Ads / Vallas, etc.             │
│  - Cantidad: 10 publicaciones                                  │
│  - Horario: Mañana (6am-12pm)                                  │
│  - Alcance estimado: 5,000 personas                            │
│  - Presupuesto: $2,000,000 COP                                 │
│  - Fechas: 2025-02-01 → 2025-02-28                            │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │  Se ejecuta la campaña
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. CONVERSIÓN A VENTA/ARRIENDO                                 │
│  - Se crea NUEVO LEAD desde los contactos generados            │
│  - service_interested = 'sale' o 'rent'                        │
│  - request_source = 'advertising'                              │
│  - Se vincula con campaña original (campo origin)              │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │  Cliente interesado
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. PROCESO DE VENTA NORMAL                                     │
│  (Ver FLUJO 2 o FLUJO 3)                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🏠 FLUJO 2: VENTA/ARRIENDO CON FINANCIACIÓN

```
┌─────────────────────────────────────────────────────────────────┐
│  1. LEAD DE VENTA                                               │
│  service_interested = 'sale' o 'rent'                           │
│  - Cliente busca propiedad                                      │
│  - Budget: $200M - $250M                                        │
│  - Ciudad: Bogotá │ Barrio: Chapinero                          │
│  - Habitaciones: 3-4 │ Baños: 2-3                              │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │  Requiere financiación
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. CONFIGURACIÓN DE FINANCIACIÓN                               │
│  - requires_financing = True                                    │
│  - loan_type = 'bank_mortgage'                                 │
│  - loan_bank_id = Banco Davivienda                             │
│  - loan_amount = $150,000,000                                  │
│  - loan_approval_status = 'pending'                            │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │  Subir documentos
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. CARGA DE DOCUMENTOS                                         │
│  Botón: "Subir Documento para Estudio"                         │
│  - Certificado laboral.pdf                                     │
│  - Extractos bancarios.pdf                                     │
│  - Declaración de renta.pdf                                    │
│  - Cédula.pdf                                                  │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │  Banco aprueba
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. APROBACIÓN DEL PRÉSTAMO                                     │
│  - loan_approval_status = 'approved'                           │
│  - Notificación automática al vendedor                         │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │  Programar visita
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. PROGRAMACIÓN DE VISITA                                      │
│  - ideal_visit_date = 2025-02-15 10:00 AM                     │
│  - visit_notes = "Cliente viene con esposa e hijos"           │
│  - Sistema valida si hay conflictos ⚠️                         │
│    has_conflicting_visit = True                                │
│    conflicting_visit_info = "Juan Pérez tiene visita 9:00 AM" │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │  Cliente decide
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. CREAR RESERVA                                               │
│  Botón: "Crear Reserva"                                        │
│  - Se crea property.reservation                                │
│  - booking_type = 'is_ownership' o 'is_rental'                │
│  - Propiedad cambia a estado 'reserved'                        │
│  - reservation_id vinculado al lead                            │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │  Pagar depósito
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. RESERVA CONFIRMADA                                          │
│  - Cliente paga depósito                                        │
│  - Reserva pasa a 'confirmed'                                  │
│  - Se selecciona contract_template_id                          │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │  Generar contrato
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  8. CREACIÓN DE CONTRATO                                        │
│  - Se crea property.contract desde reservation                 │
│  - Usa contract_template_id seleccionado                       │
│  - contract_type = 'is_ownership' o 'is_rental'               │
│  - Lead pasa a estado 'won'                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📝 FLUJO 3: CAPTACIÓN DE INMUEBLE

```
┌─────────────────────────────────────────────────────────────────┐
│  1. LEAD DE CONSIGNACIÓN                                        │
│  service_interested = 'consign'                                 │
│  - Cliente quiere vender/arrendar su inmueble                  │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │  Vendedor visita inmueble
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. REGISTRO DE CAPTACIÓN                                       │
│  - captured_by_id = Juan Vendedor                              │
│  - capture_date = 2025-02-01                                   │
│  - capture_source = 'referral'                                 │
│  - capture_commission_rate = 2.0%                              │
│  - expected_revenue = $300,000,000                             │
│  - capture_commission_amount = $6,000,000 (automático)         │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │  Llenar datos del inmueble
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. DATOS DEL INMUEBLE                                          │
│  - desired_city = "Montería"                                   │
│  - desired_neighborhood = "Buenavista"                         │
│  - desired_property_type_id = "Apartamento"                    │
│  - property_area_min = 85 m²                                   │
│  - num_bedrooms_min = 3                                        │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │  Crear ficha
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. BOTÓN "CREAR FICHA DE INMUEBLE"                             │
│  action_create_property_from_lead()                             │
│  - Crea product.template                                        │
│  - name = "[CAPTACIÓN] Venta apartamento Sr. López"           │
│  - owner_id = Cliente                                          │
│  - state = 'draft'                                             │
│  - Vincula property_ids al lead                                │
│  - Mensaje en chatter con comisión                             │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │  Propiedad lista
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. PROPIEDAD PUBLICADA                                         │
│  - Se aprueba la propiedad                                      │
│  - Propiedad visible en el sitio web                           │
│  - Se puede crear campaña de marketing (FLUJO 1)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ SISTEMA DE ALERTAS DE VISITAS

### **Cómo Funciona**

```python
@api.depends('ideal_visit_date', 'property_ids')
def _compute_conflicting_visit(self):
    """
    Busca otros leads con visita programada ±2 horas
    en las mismas propiedades
    """
    if not self.ideal_visit_date or not self.property_ids:
        self.has_conflicting_visit = False
        return

    date_start = self.ideal_visit_date - timedelta(hours=2)
    date_end = self.ideal_visit_date + timedelta(hours=2)

    conflicting_leads = self.search([
        ('id', '!=', self.id),
        ('ideal_visit_date', '>=', date_start),
        ('ideal_visit_date', '<=', date_end),
        ('property_ids', 'in', self.property_ids.ids),
    ], limit=1)

    if conflicting_leads:
        self.has_conflicting_visit = True
        self.conflicting_visit_info = f"⚠️ {conflicting_leads.user_id.name} tiene visita programada"
```

### **Notificación en Formulario**

```xml
<div class="alert alert-warning" invisible="not has_conflicting_visit">
    <i class="bi bi-exclamation-triangle"/>
    <field name="conflicting_visit_info"/>
</div>
```

---

## 📋 MÉTODOS DE ACCIÓN DISPONIBLES

| Método | Descripción | Cuándo Usar |
|--------|-------------|-------------|
| `action_create_property_from_lead()` | Crea ficha inmueble | service_interested = 'consign' |
| `action_create_reservation()` | Crea reserva | Cuando cliente decide |
| `action_view_reservations()` | Ver reservas del cliente | Botón smart |
| `action_view_loan_documents()` | Ver documentos préstamo | requires_financing = True |
| `action_upload_loan_document()` | Subir documento | Estudio de crédito |
| `action_schedule_visit()` | Programar visita | Con validación de conflictos |

---

## 🔢 CÁLCULOS AUTOMÁTICOS

### **1. Comisión de Captación**

```python
@api.depends('captured_by_id', 'expected_revenue', 'capture_commission_rate')
def _compute_capture_commission(self):
    if self.captured_by_id and self.expected_revenue:
        self.capture_commission_amount = self.expected_revenue * (self.capture_commission_rate / 100)
```

**Ejemplo:**
- expected_revenue = $300,000,000
- capture_commission_rate = 2.0%
- **capture_commission_amount = $6,000,000** ✅

---

### **2. Conteo de Reservas**

```python
def _compute_reservation_count(self):
    if self.partner_id:
        self.reservation_count = self.env['property.reservation'].search_count([
            ('partner_id', '=', self.partner_id.id)
        ])
```

---

## 📊 SMART BUTTONS SUGERIDOS

```xml
<div class="oe_button_box" name="button_box">
    <!-- Reservas -->
    <button name="action_view_reservations"
            type="object"
            class="oe_stat_button"
            icon="fa-calendar-check-o"
            invisible="not partner_id">
        <field name="reservation_count" widget="statinfo" string="Reservas"/>
    </button>

    <!-- Documentos de Préstamo -->
    <button name="action_view_loan_documents"
            type="object"
            class="oe_stat_button"
            icon="fa-file-text-o"
            invisible="not requires_financing">
        <div class="o_field_widget o_stat_info">
            <span class="o_stat_value">
                <field name="loan_document_ids" widget="statinfo" string="Documentos"/>
            </span>
        </div>
    </button>

    <!-- Comisión de Captación -->
    <button name="action_view_capture_commission"
            type="object"
            class="oe_stat_button"
            icon="fa-money"
            invisible="not captured_by_id or service_interested != 'consign'">
        <div class="o_field_widget o_stat_info">
            <span class="o_stat_value">
                <field name="capture_commission_amount" widget="monetary"/>
            </span>
            <span class="o_stat_text">Comisión Captación</span>
        </div>
    </button>
</div>
```

---

## 🎯 RESUMEN POR SERVICIO

| Servicio | Campos Clave | Flujo | Resultado |
|----------|--------------|-------|-----------|
| **Marketing** | marketing_campaign_type, marketing_quantity, marketing_schedule, marketing_estimated_reach | Campaña → Leads generados | Múltiples oportunidades |
| **Venta** | budget_min/max, desired_city, loan_type, ideal_visit_date | Lead → Visita → Reserva → Contrato | property.contract (is_ownership) |
| **Arriendo** | monthly_income, has_pets, requires_parking, ideal_visit_date | Lead → Visita → Reserva → Contrato | property.contract (is_rental) |
| **Consignación** | captured_by_id, capture_commission, desired_city, property_area_min | Captación → Ficha inmueble | product.template |
| **Proyectos** | project_id, property_purpose, budget_min | Lead → Reserva → Contrato | property.contract + sale.order |

---

## ✅ TODO LIST PARA COMPLETAR

- [x] Agregar campos de marketing
- [x] Agregar campos de captación
- [x] Agregar campos de préstamo
- [x] Agregar campos de reserva
- [x] Agregar template de contrato
- [x] Agregar validación de visitas conflictivas
- [x] Crear métodos de acción
- [ ] Actualizar vista quick_create con nuevos campos
- [ ] Crear vistas de templates de contrato
- [ ] Agregar smart buttons al formulario
- [ ] Crear reportes de comisiones
- [ ] Integrar con módulo de contabilidad

---

**Creado por:** Bohio Inmobiliaria
**Fecha:** 2025
**Versión:** 18.0.1.0.2

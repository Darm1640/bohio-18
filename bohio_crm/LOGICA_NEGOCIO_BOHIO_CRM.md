# LÓGICA DE NEGOCIO - BOHIO CRM

## 📋 INFORMACIÓN GENERAL

**Módulo:** BOHIO CRM
**Versión:** 18.0.1.0.1
**Propósito:** CRM especializado para gestión inmobiliaria
**Dependencias:** crm, real_estate_bits

## 🏗️ ARQUITECTURA DEL SISTEMA

### Modelos Principales

1. **crm.lead (Heredado)** - Gestión de oportunidades inmobiliarias
2. **crm.team (Heredado)** - Equipos de ventas con métricas de recaudo
3. **bohio.crm.dashboard** - Vista dashboard personalizada
4. **bohio.crm.analytics** - Análisis avanzado de datos

---

## 🔄 PROCESOS DE NEGOCIO PRINCIPALES

### 1. GESTIÓN DE OPORTUNIDADES INMOBILIARIAS

#### 1.1 Clasificación de Clientes
- **Tipos:** Propietario, Arrendatario, Comprador, Vendedor, Inversionista
- **Servicios:** Venta, Arriendo, Proyectos, Consignación, Legal, Marketing, Corporativo, Avalúos
- **Asignación automática** a equipos inmobiliarios según servicio

#### 1.2 Sistema de Recomendaciones Inteligentes
```python
# Algoritmo de scoring para propiedades
def _compute_recommended_properties(self):
    score = 0
    # Barrio coincidente: +50 puntos
    # Tipo de propiedad: +40 puntos
    # Precio dentro del rango: +30 puntos
    # Habitaciones adecuadas: +15 puntos
    # Zonas comunes: +10 puntos
```

**Criterios de Recomendación:**
- Ubicación (barrio, ciudad)
- Tipo de propiedad deseada
- Rango de presupuesto (min/max)
- Número de habitaciones y baños
- Área mínima/máxima
- Amenidades (piscina, gym, seguridad)
- Propósito (vivienda, oficina, vacacional, inversión)

#### 1.3 Comparador de Propiedades
- **Límite:** Máximo 4 propiedades simultáneas
- **Generación de reportes** comparativos automáticos
- **Validación:** Control de límites por constraints

### 2. GESTIÓN DE CONTRATOS

#### 2.1 Creación Automática de Contratos
```python
def action_close_lead_with_contract(self):
    # Validaciones
    if not self.compared_properties_ids:
        raise ValidationError('Debe seleccionar la propiedad')

    # Creación del contrato
    contract_vals = {
        'name': f'Contrato - {self.name}',
        'partner_id': self.partner_id.id,
        'property_id': property_selected.id,
        'contract_type': 'is_rental' if self.service_interested == 'rent' else 'is_ownership',
        'rental_fee': self.estimated_monthly_rent
    }
```

#### 2.2 Cálculos Automáticos
- **Estimación de cánones mensuales**
- **Cálculo de comisiones** (% configurable)
- **Duración de contratos** con fechas automáticas
- **Montos totales** proyectados

### 3. SISTEMA PQRS (Peticiones, Quejas, Reclamos, Sugerencias)

#### 3.1 Clasificación y Plazos
```python
deadlines = {
    'petition': 15,    # días
    'complaint': 15,   # días
    'claim': 15,       # días
    'suggestion': 30,  # días
}
```

#### 3.2 Integración con Helpdesk
- **Creación automática** de tickets
- **Priorización** según tipo de PQRS
- **Seguimiento** de estados y plazos

### 4. PORTAL DEL CLIENTE

#### 4.1 Visibilidad Controlada
```python
def _compute_show_in_portal(self):
    # Solo visible si:
    # - portal_visible = True (manual)
    # - stage_id.fold = False (etapa activa)
    # - not stage_id.is_won (no ganada)
```

#### 4.2 Métricas Financieras
- **Total facturado** al cliente
- **Notas de crédito** aplicadas
- **Saldos pendientes** de pago
- **Porcentaje de pagos** cumplidos

---

## 🔧 CARACTERÍSTICAS TÉCNICAS

### 1. CAMPOS PERSONALIZADOS

#### Información del Cliente
- `client_type` - Tipo de cliente (owner, tenant, buyer, etc.)
- `service_interested` - Servicio de interés
- `referred_by_partner_id` - Cliente que refirió
- `project_id` - Proyecto inmobiliario asociado

#### Preferencias de Búsqueda
- `budget_min/max` - Rango presupuestal
- `desired_neighborhood` - Barrio preferido
- `desired_property_type_id` - Tipo de propiedad
- `num_bedrooms_min/max` - Habitaciones
- `property_area_min/max` - Área m²
- `has_pets`, `pet_type` - Información mascotas
- `requires_*` - Amenidades requeridas

#### Información Contractual
- `contract_start_date` - Fecha inicio estimada
- `contract_duration_months` - Duración contrato
- `estimated_monthly_rent` - Canon estimado
- `commission_percentage` - % comisión

### 2. ESTADOS Y VALIDACIONES

#### Estados de Recomendaciones
- `pending` - Pendiente generación
- `generated` - Recomendaciones creadas
- `viewed` - Vistas por cliente
- `selected` - Cliente seleccionó

#### Validaciones Críticas
```python
@api.constrains('compared_properties_ids')
def _check_compared_properties_limit(self):
    if len(lead.compared_properties_ids) > 4:
        raise ValidationError('Solo puede comparar un máximo de 4 propiedades')
```

### 3. MÉTODOS DE NEGOCIO PRINCIPALES

#### Generación de Recomendaciones
- `action_view_recommended_properties()` - Ver propiedades recomendadas
- `action_generate_recommendations()` - Generar nuevas recomendaciones
- `_compute_recommended_properties()` - Algoritmo de cálculo

#### Gestión de Comparaciones
- `action_add_to_comparison()` - Agregar propiedad a comparar
- `action_view_compared_properties()` - Ver propiedades en comparación
- `action_print_comparison()` - Generar reporte comparativo

#### Creación de Contratos
- `action_close_lead_with_contract()` - Cerrar oportunidad con contrato
- `_compute_estimated_amounts()` - Cálculos automáticos

#### PQRS y Helpdesk
- `action_create_helpdesk_ticket()` - Crear ticket desde PQRS
- `_compute_response_deadline()` - Calcular fecha límite respuesta

---

## 📊 INTEGRACIONES

### 1. Con Módulo real_estate_bits
- **Propiedades:** Consulta y filtrado de product.template
- **Contratos:** Creación de property.contract
- **Estados:** Sincronización de estados de propiedades

### 2. Con Módulo account
- **Facturación:** Consulta de account.move
- **Pagos:** Gestión de account.payment
- **Métricas financieras** integradas

### 3. Con Módulo helpdesk
- **Tickets:** Creación automática desde PQRS
- **Seguimiento:** Estados y responsables

### 4. Con Módulo calendar
- **Citas:** Gestión de calendar.event
- **Actividades:** Seguimiento de mail.activity

---

## 🎯 REGLAS DE NEGOCIO CRÍTICAS

### 1. Asignación Automática de Equipos
```python
if vals.get('service_interested') in ['rent', 'sale', 'projects']:
    real_estate_team = self.env['crm.team'].search([
        '|',
        ('name', 'ilike', 'inmobiliaria'),
        ('name', 'ilike', 'real estate')
    ], limit=1)
```

### 2. Cálculo de Comisiones
- **Arriendo:** Comisión sobre valor total del contrato (canon × meses)
- **Venta:** Comisión sobre precio de venta
- **Porcentaje configurable** por oportunidad

### 3. Estados de Propiedades
- **free** - Disponible para mostrar
- **reserved** - Reservada, no mostrar
- **on_lease** - Arrendada
- **sold** - Vendida

### 4. Visibilidad en Portal
- Manual: Campo `portal_visible`
- Automática: Etapas activas no ganadas
- Control granular por oportunidad

### 5. Métricas de Rendimiento
- **Tasa de conversión** por vendedor
- **Tiempo promedio** de cierre
- **Valor promedio** de contratos
- **Tasa de ocupación** de propiedades

---

## 🚀 FLUJO COMPLETO DEL PROCESO

### 1. Captura de Lead
1. Cliente ingresa por web/teléfono/referido
2. **Clasificación automática** por tipo y servicio
3. **Asignación a equipo** inmobiliario correspondiente

### 2. Calificación y Búsqueda
1. Registro de **preferencias detalladas**
2. **Generación automática** de recomendaciones
3. **Comparación** de hasta 4 propiedades

### 3. Seguimiento Comercial
1. **Agendamiento** de citas y visitas
2. **Registro de actividades** y seguimiento
3. **Actualización** de probabilidades

### 4. Cierre y Contratación
1. **Selección final** de propiedad
2. **Generación automática** de contrato
3. **Cambio de estado** a ganado

### 5. Gestión Post-Venta
1. **Seguimiento** de pagos y cumplimiento
2. **Atención** de PQRS si aplica
3. **Métricas** de satisfacción

Este documento constituye la base técnica y funcional del módulo BOHIO CRM, diseñado específicamente para optimizar la gestión comercial en el sector inmobiliario.
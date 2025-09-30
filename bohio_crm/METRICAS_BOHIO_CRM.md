# MÉTRICAS Y ANÁLISIS - BOHIO CRM

## 📊 INFORMACIÓN GENERAL

**Módulo:** BOHIO CRM - Sistema de Métricas
**Versión:** 18.0.1.0.1
**Propósito:** Análisis y métricas avanzadas para negocio inmobiliario
**Dashboards:** 3 niveles de análisis (Operativo, Táctico, Estratégico)

---

## 🎯 MÉTRICAS PRINCIPALES (KPIs)

### 1. MÉTRICAS COMERCIALES

#### 1.1 Oportunidades
```python
# Nuevas oportunidades del período
new_opportunities = Lead.search_count([
    ('create_date', '>=', start_date),
    ('type', '=', 'opportunity')
])

# Crecimiento vs período anterior
opportunities_growth = _calculate_growth(current, previous)
```

#### 1.2 Conversión y Cierre
- **Tasa de Conversión:** `(won_opportunities / total_opportunities * 100)`
- **Tiempo Promedio de Cierre:** Días desde creación hasta cierre
- **Valor Promedio por Oportunidad:** `total_expected / total_opportunities`

#### 1.3 Pipeline de Ventas
- **Valor Total del Pipeline:** Suma de expected_revenue activo
- **Probabilidad Ponderada:** `sum(expected_revenue * probability)`
- **Distribución por Etapas:** Cantidad y valor por stage_id

### 2. MÉTRICAS DE PROPIEDADES

#### 2.1 Inventario
```python
properties_available = Product.search_count([
    ('is_property', '=', True),
    ('state', '=', 'free')
])

properties_rented = Product.search_count([
    ('state', '=', 'on_lease')
])

properties_sold = Product.search_count([
    ('state', '=', 'sold')
])
```

#### 2.2 Ocupación y Rendimiento
- **Tasa de Ocupación:** `(properties_rented / properties_total * 100)`
- **Rotación de Inventario:** Tiempo promedio de disponibilidad
- **Propiedades por Tipo:** Distribución del portafolio

#### 2.3 Área Total Gestionada
```python
properties_with_area = Product.search([
    ('is_property', '=', True),
    ('property_area', '>', 0)
])
total_area = sum(properties_with_area.mapped('property_area'))
```

### 3. MÉTRICAS FINANCIERAS

#### 3.1 Facturación
```python
# Facturación del mes
total_invoiced = sum(invoices where move_type = 'out_invoice')
total_credit_notes = sum(invoices where move_type = 'out_refund')
net_invoiced = total_invoiced - total_credit_notes
```

#### 3.2 Recaudo y Pagos
```python
# Recaudo del período
total_collected = sum(payments where payment_type = 'inbound')

# Pagos a propietarios
total_paid_owners = sum(payments where payment_type = 'outbound')

# Balance del recaudo
collection_balance = total_collected - total_paid_owners
```

#### 3.3 Ingresos Recurrentes
```python
# Contratos de arriendo activos
rental_contracts = PropertyContract.search([
    ('state', '=', 'active'),
    ('contract_type', '=', 'is_rental')
])
recurring_revenue = sum(rental_contracts.mapped('rental_fee'))
```

### 4. MÉTRICAS DE CONTRATOS

#### 4.1 Nuevos Contratos
- **Contratos Firmados:** Cantidad del período
- **Valor Promedio:** `total_revenue / contract_count`
- **Contratos por Tipo:** is_rental vs is_ownership

#### 4.2 Contratos Activos y Vencimientos
```python
# Contratos que vencen en 30 días
expiring_contracts = PropertyContract.search_count([
    ('date_to', '<=', today + timedelta(days=30)),
    ('date_to', '>=', today),
    ('state', '=', 'active')
])
```

---

## 📈 DASHBOARDS Y REPORTES

### 1. DASHBOARD OPERATIVO (Diario)

#### 1.1 KPI Cards
```python
metrics = {
    'active_contracts': active_contracts,
    'new_opportunities': new_opportunities,
    'pending_appointments': pending_appointments,
    'pending_activities': pending_activities,
    'properties_available': properties_available
}
```

#### 1.2 Actividades del Día
- **Citas Pendientes:** calendar.event próximas
- **Actividades Vencidas:** mail.activity overdue
- **Seguimientos:** Tareas del día

### 2. DASHBOARD TÁCTICO (Semanal/Mensual)

#### 2.1 Gráficos de Tendencias
```python
# Datos mensuales para gráficos de línea
monthly_data = [{
    'month': month_start.strftime('%b'),
    'opportunities': opportunities_created,
    'won': opportunities_won,
    'revenue': revenue_month
}]
```

#### 2.2 Análisis por Servicio
```python
service_breakdown = {
    'rent': count_rent_opportunities,
    'sale': count_sale_opportunities,
    'projects': count_project_opportunities,
    'consign': count_consign_opportunities
}
```

#### 2.3 Top Performers
- **Vendedores Top:** Por revenue y conversión
- **Propiedades Más Consultadas:** Por frecuencia
- **Proyectos Activos:** Estado y timeline

### 3. DASHBOARD ESTRATÉGICO (Trimestral/Anual)

#### 3.1 Análisis Avanzado
```python
def get_analytics_data(self):
    return {
        'monthly_data': monthly_revenue_trend,
        'weekly_data': weekly_completion_rate,
        'top_companies': top_clients_analysis,
        'category_data': breakdown_by_service
    }
```

#### 3.2 Proyecciones y Forecasting
- **Pipeline Ponderado:** expected_revenue × probability
- **Proyección Mensual:** Basada en tendencias históricas
- **Análisis de Estacionalidad:** Patrones por época del año

---

## 🔍 ANÁLISIS ESPECIALIZADOS

### 1. ANÁLISIS POR TIPO DE SERVICIO

#### 1.1 Revenue por Servicio (Gráfico Donut)
```python
services = ['sale', 'rent', 'projects', 'consign', 'legal', 'marketing']
revenue_by_service = {
    service: sum(leads.filtered(lambda l: l.service_interested == service).mapped('expected_revenue'))
    for service in services
}
```

#### 1.2 Breakdown por Cliente
```python
client_breakdown = {
    'owner': count_owner_leads,
    'tenant': count_tenant_leads,
    'buyer': count_buyer_leads,
    'seller': count_seller_leads,
    'investor': count_investor_leads
}
```

### 2. ANÁLISIS DE PROYECTOS

#### 2.1 Timeline de Proyectos
```python
def _get_projects_timeline_chart(self):
    # Proyectos activos vs completados por mes
    active_projects = ProjectWorksite.search_count([
        ('state', '=', 'active'),
        ('create_date', '<=', month_end)
    ])

    completed_projects = ProjectWorksite.search_count([
        ('state', '=', 'completed'),
        ('write_date', '>=', month_start)
    ])
```

#### 2.2 Revenue por Proyecto
- **Ingresos Estimados por Etapa**
- **Proyectos en Pipeline**
- **Completación vs Planificado**

### 3. ANÁLISIS DE PROPIEDADES

#### 3.1 Distribución por Tipo
```python
property_types = Product.read_group(
    domain=[('is_property', '=', True)],
    fields=['property_type_id'],
    groupby=['property_type_id']
)
```

#### 3.2 Revenue por Tipo de Propiedad
```python
# Separado por venta vs arriendo
data_sale = revenue_by_property_type(service='sale')
data_rent = revenue_by_property_type(service='rent')
```

### 4. ANÁLISIS FINANCIERO DETALLADO

#### 4.1 Métricas de Recaudo por Lead
```python
@api.depends('contract_id')
def _compute_rent_metrics(self):
    months_active = self._calculate_months_active(contract)
    expected_collection = contract.rental_fee * months_active

    payments = AccountPayment.search_read([
        ('ref', 'like', contract.name),
        ('state', '=', 'posted')
    ])

    collected = sum(p['amount'] for p in payments if p['payment_type'] == 'inbound')
    paid_owner = sum(p['amount'] for p in payments if p['payment_type'] == 'outbound')
```

#### 4.2 Métricas por Equipo
```python
class CrmTeam(models.Model):
    total_invoiced_month = fields.Monetary(compute='_compute_invoice_metrics')
    total_collected_month = fields.Monetary(compute='_compute_payment_metrics')
    collection_vs_expected = fields.Float(compute='_compute_payment_metrics')
    pending_owner_payments = fields.Monetary(compute='_compute_payment_metrics')
```

---

## 🎛️ CONFIGURACIÓN Y FILTROS

### 1. Filtros Temporales
- **Período:** Semana, Mes, Trimestre, Año
- **Fechas Específicas:** Rango personalizado
- **Comparación:** Período actual vs anterior

### 2. Filtros por Equipo
```python
if not has_all_teams_access:
    user_teams = self.env['crm.team'].search([('member_ids', 'in', user.id)])
    domain.append(('team_id', 'in', user_teams.ids))
```

### 3. Filtros por Servicio
- **Todos los Servicios**
- **Filtro Específico:** rent, sale, projects, etc.
- **Agrupación:** Por tipo de servicio

### 4. Seguridad y Permisos
- **Vendedores:** Solo sus datos
- **Managers:** Datos del equipo
- **Administradores:** Todos los datos

---

## 📊 FORMATOS DE VISUALIZACIÓN

### 1. Gráficos Implementados

#### 1.1 Chart.js Integration
```javascript
// Gráfico de línea para tendencias
{
    type: 'line',
    data: {
        labels: months,
        datasets: [{
            label: 'Oportunidades',
            data: opportunities_data,
            borderColor: '#36A2EB'
        }]
    }
}
```

#### 1.2 Gráficos Donut para Distribución
```javascript
{
    type: 'doughnut',
    data: {
        labels: service_labels,
        datasets: [{
            data: revenue_data,
            backgroundColor: color_palette
        }]
    }
}
```

#### 1.3 Gráficos de Barras para Comparación
```javascript
{
    type: 'bar',
    data: {
        labels: property_types,
        datasets: [{
            label: 'Venta',
            data: sale_data,
            backgroundColor: '#FF6384'
        }, {
            label: 'Arriendo',
            data: rent_data,
            backgroundColor: '#36A2EB'
        }]
    }
}
```

### 2. Tablas y Listas
- **Top Performers:** Avatar, nombre, revenue, count
- **Actividades Próximas:** Fecha, usuario, tipo, resumen
- **Contratos Venciendo:** Fecha, cliente, propiedad

---

## 🔧 MÉTODOS TÉCNICOS PRINCIPALES

### 1. Cálculo de Crecimiento
```python
def _calculate_growth(self, current, previous):
    if previous == 0:
        return '+100%' if current > 0 else '0%'
    growth = ((current - previous) / previous) * 100
    sign = '+' if growth > 0 else ''
    return f"{sign}{round(growth)}%"
```

### 2. Cálculo de Meses Activos
```python
def _calculate_months_active(self, contract):
    today = fields.Date.today()
    start = contract.date_from
    end = min(contract.date_to, today) if contract.date_to else today
    months = (end.year - start.year) * 12 + (end.month - start.month) + 1
    return max(months, 0)
```

### 3. Agregación de Datos
```python
# Read_group para análisis eficiente
performers = Lead.read_group(
    domain=domain + [('stage_id.is_won', '=', True)],
    fields=['user_id', 'expected_revenue'],
    groupby=['user_id'],
    orderby='expected_revenue desc'
)
```

---

## 📈 INDICADORES CLAVE DE RENDIMIENTO

### 1. Comerciales
- **Conversión Rate:** % leads → oportunidades → ganadas
- **Cycle Time:** Tiempo promedio de cierre
- **Win Rate:** % oportunidades ganadas
- **Average Deal Size:** Valor promedio por oportunidad

### 2. Operacionales
- **Ocupancy Rate:** % propiedades ocupadas
- **Inventory Turnover:** Rotación de propiedades
- **Response Time:** Tiempo de respuesta PQRS
- **Activity Completion:** % actividades completadas

### 3. Financieros
- **Revenue Growth:** Crecimiento de ingresos
- **Collection Rate:** % recaudo vs esperado
- **Owner Payment Ratio:** % pagado a propietarios
- **Commission Rate:** % comisión promedio

### 4. Cliente
- **Customer Satisfaction:** Índice satisfacción
- **Referral Rate:** % clientes que refieren
- **Retention Rate:** % retención de clientes
- **PQRS Resolution:** % PQRS resueltos en tiempo

Este documento constituye la guía completa del sistema de métricas y análisis del módulo BOHIO CRM, diseñado para proporcionar visibilidad total del negocio inmobiliario.
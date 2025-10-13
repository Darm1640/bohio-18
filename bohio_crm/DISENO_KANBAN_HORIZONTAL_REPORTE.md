# 📋 DISEÑO KANBAN HORIZONTAL TIPO REPORTE
## Vista Completa con 5 Cintas Horizontales

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│  CINTA 1: BOTONES DE ACCIÓN + ETAPAS + PRIORIDAD                                               │
│  ═══════════════════════════════════════════════════════════════════════════════════════════   │
│                                                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       ┌────────────────────────┐     │
│  │ 📧 ENVIAR│  │ ✅ ELEGIR│  │ 📊 MÉTRICAS│ │ 📝 EDITAR│       │ ETAPA: Calificación   │     │
│  │  EMAIL   │  │   ESTA   │  │ COMPLETAS│  │   TODO   │       │ PROBABILIDAD: 20%     │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       └────────────────────────┘     │
│                                                                                                 │
│  PRIORIDAD: ⭐⭐⭐  |  COLOR: 🔴                                                                 │
│                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│  CINTA 2: MÉTRICAS CLAVE DE COMISIONES Y TIEMPOS                                               │
│  ═══════════════════════════════════════════════════════════════════════════════════════════   │
│                                                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐     │
│  │ 💰 INGRESO       │  │ 💵 COMISIÓN EST. │  │ 📅 CIERRE        │  │ ⏱️ DÍAS ACTIVO   │     │
│  │                  │  │                  │  │                  │  │                  │     │
│  │ $ 350,000,000    │  │ $ 35,000,000     │  │ 2024-12-31       │  │ 45 días          │     │
│  │                  │  │ (10%)            │  │                  │  │                  │     │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘  └──────────────────┘     │
│                                                                                                 │
│  CAMPOS: expected_revenue | estimated_commission | date_deadline | create_date                 │
│                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│  CINTA 3: INFORMACIÓN DEL CONTRATO                                                             │
│  ═══════════════════════════════════════════════════════════════════════════════════════════   │
│                                                                                                 │
│  📄 TEMPLATE CONTRATO: Arrendamiento Residencial                                               │
│  ├─ Inicio: 2024-11-01                                                                         │
│  ├─ Duración: 12 meses                                                                         │
│  ├─ Fin Estimado: 2025-11-01                                                                   │
│  └─ % Comisión: 10%                                                                            │
│                                                                                                 │
│  🤝 RESERVA: RES-2024-001 (Si existe)                                                          │
│                                                                                                 │
│  CAMPOS: contract_template_id | contract_start_date | contract_duration_months |               │
│          contract_end_date | commission_percentage | reservation_id                            │
│                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│  CINTA 4: PRODUCTOS (IZQUIERDA) + DATOS DEL CLIENTE (DERECHA)                                  │
│  ═══════════════════════════════════════════════════════════════════════════════════════════   │
│                                                                                                 │
│  ┌────────────────────────────────────────────┐  │  ┌──────────────────────────────────────┐  │
│  │ 🏠 PROPIEDADES DE INTERÉS (CARDS)         │  │  │ 👤 INFORMACIÓN DEL CLIENTE          │  │
│  │                                            │  │  │                                      │  │
│  │ ┌──────────────────────────────────────┐  │  │  │ NOMBRE: Juan Pérez García           │  │
│  │ │ 🏢 Apartamento en El Poblado          │  │  │  │ TIPO: Comprador                     │  │
│  │ │ ────────────────────────────────────  │  │  │  │ SERVICIO: Venta                     │  │
│  │ │ 📍 Medellín, Antioquia               │  │  │  │                                      │  │
│  │ │ 💵 VENTA: $350,000,000               │  │  │  │ 📧 juan.perez@email.com            │  │
│  │ │ ARRIENDO: $2,500,000/mes             │  │  │  │ 📱 +57 300 123 4567                │  │
│  │ │                                       │  │  │  │ 💼 Ingeniero                        │  │
│  │ │ [3 HAB] [2 BAÑ] [120 m²]            │  │  │  │ 💰 $8,000,000/mes                  │  │
│  │ │ [🅿️ 2] [🏊 Sí] [🔒 24/7]            │  │  │  │                                      │  │
│  │ │                                       │  │  │  │ 🎯 ORIGEN: Sitio Web                │  │
│  │ │ ESTADO: Disponible ✅                │  │  │  │ 👥 RESPONSABLE: María López         │  │
│  │ └──────────────────────────────────────┘  │  │  │                                      │  │
│  │                                            │  │  │ PREFERENCIAS DE BÚSQUEDA:            │  │
│  │ ┌──────────────────────────────────────┐  │  │  │ ├─ 💵 Presupuesto: $300M - $400M    │  │
│  │ │ 🏠 Casa en Envigado                   │  │  │  │ ├─ 📍 Ciudad: Medellín              │  │
│  │ │ ────────────────────────────────────  │  │  │  │ ├─ 🏘️ Barrio: El Poblado           │  │
│  │ │ 📍 Envigado, Antioquia               │  │  │  │ ├─ 🏡 Tipo: Apartamento             │  │
│  │ │ 💵 VENTA: $480,000,000               │  │  │  │ ├─ 🛏️ Habitaciones: 3-4            │  │
│  │ │                                       │  │  │  │ ├─ 🚿 Baños: 2+                    │  │
│  │ │ [4 HAB] [3 BAÑ] [180 m²]            │  │  │  │ ├─ 📐 Área: 100-150 m²             │  │
│  │ │ [🅿️ 3] [🌳 Jardín] [🔒 Sí]          │  │  │  │ ├─ 🅿️ Parqueadero: Sí (2)          │  │
│  │ │                                       │  │  │  │ ├─ 🐕 Mascotas: Sí (Perro)         │  │
│  │ │ ESTADO: Disponible ✅                │  │  │  │ └─ 🏠 Propósito: Vivienda          │  │
│  │ └──────────────────────────────────────┘  │  │  │                                      │  │
│  │                                            │  │  │ AMENIDADES REQUERIDAS:               │  │
│  │ + 2 propiedades más...                    │  │  │ [✅ Zonas Comunes] [✅ Gimnasio]    │  │
│  │                                            │  │  │ [✅ Piscina] [✅ Seguridad 24/7]    │  │
│  └────────────────────────────────────────────┘  │  └──────────────────────────────────────┘  │
│                                                                                                 │
│  CAMPOS PRODUCTOS:                              │  CAMPOS CLIENTE:                             │
│  property_ids (many2many)                       │  name | partner_id | client_type |           │
│  ├─ name | street | city_id | state_id         │  service_interested | email_from | mobile |  │
│  ├─ list_price | monthly_rent                  │  phone | occupation | monthly_income |       │
│  ├─ num_bedrooms | num_bathrooms | total_area  │  request_source | user_id |                  │
│  ├─ parking_spaces | has_pool | has_security   │  budget_min | budget_max | desired_city |    │
│  └─ state (disponibilidad)                     │  desired_neighborhood | desired_property_    │
│                                                  │  type_id | num_bedrooms_min/max |           │
│                                                  │  num_bathrooms_min | property_area_min/max │
│                                                  │  requires_parking | parking_spots |         │
│                                                  │  has_pets | pet_type | property_purpose |   │
│                                                  │  requires_common_areas | requires_gym |     │
│                                                  │  requires_pool | requires_security |        │
│                                                  │  requires_elevator | num_occupants          │
│                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│  CINTA 5: SECCIÓN COLAPSABLE - INFORMACIÓN ADICIONAL DETALLADA                                 │
│  ═══════════════════════════════════════════════════════════════════════════════════════════   │
│                                                                                                 │
│  [▼ EXPANDIR PARA VER MÁS INFORMACIÓN]                                                         │
│                                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ 💰 FINANCIAMIENTO (Si requires_financing = TRUE)                                       │   │
│  │ ═══════════════════════════════════════════════════════════════════════════════════   │   │
│  │                                                                                         │   │
│  │ ├─ 🏦 Tipo de Préstamo: Hipoteca Bancaria                                              │   │
│  │ ├─ 💵 Monto Solicitado: $280,000,000                                                   │   │
│  │ ├─ 🏢 Entidad Financiera: Banco de Bogotá                                              │   │
│  │ ├─ 📊 Estado de Aprobación: Pre-aprobado ⏳                                            │   │
│  │ └─ 📎 Documentos Adjuntos: [3 archivos]                                                │   │
│  │                                                                                         │   │
│  │ CAMPOS: requires_financing | loan_type | loan_amount | loan_bank_id |                 │   │
│  │         loan_approval_status | loan_document_ids                                       │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ 📢 CAMPAÑA DE MARKETING (Si campaign_id O marketing_campaign_type existe)             │   │
│  │ ═══════════════════════════════════════════════════════════════════════════════════   │   │
│  │                                                                                         │   │
│  │ ├─ 🎯 Campaña: Black Friday Inmobiliario 2024                                          │   │
│  │ ├─ 📱 Fuente: Facebook Ads                                                             │   │
│  │ ├─ 📺 Medio: Redes Sociales                                                            │   │
│  │ ├─ 🎪 Tipo de Campaña: Facebook Ads                                                    │   │
│  │ ├─ 💰 Presupuesto Asignado: $5,000,000                                                 │   │
│  │ ├─ 👥 Alcance Estimado: 50,000 personas                                                │   │
│  │ ├─ 📊 Cantidad de Anuncios: 10                                                         │   │
│  │ ├─ ⏰ Horario Preferido: Todo el día                                                    │   │
│  │ ├─ 📅 Período: 2024-11-15 → 2024-12-15                                                 │   │
│  │ └─ 📝 Descripción: Campaña enfocada en propiedades premium...                          │   │
│  │                                                                                         │   │
│  │ ⚠️ ACCIÓN: Iniciar seguimiento de campaña                                              │   │
│  │                                                                                         │   │
│  │ CAMPOS: campaign_id | source_id | medium_id | marketing_campaign_type |               │   │
│  │         marketing_budget_allocated | marketing_estimated_reach | marketing_quantity |  │   │
│  │         marketing_schedule | marketing_start_date | marketing_end_date |              │   │
│  │         marketing_description                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ 🤝 CAPTACIÓN (Si service_interested = 'consign' Y captured_by_id existe)              │   │
│  │ ═══════════════════════════════════════════════════════════════════════════════════   │   │
│  │                                                                                         │   │
│  │ ├─ 👤 Captado Por: Carlos Rodríguez                                                    │   │
│  │ ├─ 📅 Fecha de Captación: 2024-10-15                                                   │   │
│  │ ├─ 📍 Fuente: Referido                                                                 │   │
│  │ ├─ 💵 % Comisión de Captación: 2.0%                                                    │   │
│  │ └─ 💰 Monto Comisión: $7,000,000                                                       │   │
│  │                                                                                         │   │
│  │ CAMPOS: captured_by_id | capture_date | capture_source |                              │   │
│  │         capture_commission_rate | capture_commission_amount                            │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ 🔄 PROPIEDADES EN COMPARACIÓN                                                          │   │
│  │ ═══════════════════════════════════════════════════════════════════════════════════   │   │
│  │                                                                                         │   │
│  │ [Apto A - $350M] vs [Apto B - $380M] vs [Casa C - $420M] vs [Casa D - $390M]         │   │
│  │                                                                                         │   │
│  │ 📊 [VER COMPARACIÓN DETALLADA] ← Botón para abrir reporte de comparación              │   │
│  │                                                                                         │   │
│  │ CAMPOS: compared_properties_ids (many2many, máx 4)                                     │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ 📅 VISITAS PROGRAMADAS                                                                 │   │
│  │ ═══════════════════════════════════════════════════════════════════════════════════   │   │
│  │                                                                                         │   │
│  │ ├─ 🗓️ Fecha Ideal: 2024-11-20 14:00                                                    │   │
│  │ ├─ 📝 Notas: Asistirán 3 personas, preferencia tarde                                   │   │
│  │ └─ ⚠️ Conflicto: Hay otra visita programada (Si existe)                                │   │
│  │                                                                                         │   │
│  │ CAMPOS: ideal_visit_date | visit_notes | has_conflicting_visit |                      │   │
│  │         conflicting_visit_info                                                         │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ 📋 ACTIVIDADES Y SEGUIMIENTO                                                           │   │
│  │ ═══════════════════════════════════════════════════════════════════════════════════   │   │
│  │                                                                                         │   │
│  │ [Widget de actividades de Odoo - kanban_activity]                                      │   │
│  │                                                                                         │   │
│  │ CAMPOS: activity_ids | activity_state                                                  │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ 🔗 OTRAS REFERENCIAS                                                                   │   │
│  │ ═══════════════════════════════════════════════════════════════════════════════════   │   │
│  │                                                                                         │   │
│  │ ├─ 👤 Referido Por: Ana María Torres                                                   │   │
│  │ └─ 🏗️ Proyecto: Torre Rialto Montería                                                  │   │
│  │                                                                                         │   │
│  │ CAMPOS: referred_by_partner_id | project_id                                            │   │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                                 │
│  [▲ COLAPSAR INFORMACIÓN ADICIONAL]                                                            │
│                                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 RESUMEN DE CAMPOS POR CINTA

### CINTA 1: Botones + Etapas + Prioridad (8 elementos)
```
┌─────────────────────────────────────────────────────────────┐
│ CAMPOS UTILIZADOS:                                          │
│ ├─ stage_id         → Etapa actual                          │
│ ├─ probability      → % Probabilidad                        │
│ ├─ priority         → Estrellas de prioridad                │
│ ├─ color            → Color picker                          │
│ ├─ id               → Para acciones (botones)               │
│ └─ BOTONES:                                                  │
│    ├─ Enviar por Email (action_send_email_report)           │
│    ├─ Elegir esta (action_select_for_opportunity)           │
│    ├─ Ver Métricas Completas (action_open_metrics)          │
│    └─ Editar Todo (action_edit_full)                        │
└─────────────────────────────────────────────────────────────┘
```

### CINTA 2: Métricas Clave (4 métricas)
```
┌─────────────────────────────────────────────────────────────┐
│ CAMPOS UTILIZADOS:                                          │
│ ├─ expected_revenue      → Ingreso esperado ($)             │
│ ├─ estimated_commission  → Comisión estimada ($)            │
│ ├─ commission_percentage → % de comisión                    │
│ ├─ date_deadline         → Fecha de cierre esperado         │
│ ├─ create_date          → Fecha de creación                 │
│ └─ COMPUTED:                                                 │
│    └─ Días activo (date.today - create_date)                │
└─────────────────────────────────────────────────────────────┘
```

### CINTA 3: Contrato (7 campos)
```
┌─────────────────────────────────────────────────────────────┐
│ CAMPOS UTILIZADOS:                                          │
│ ├─ contract_template_id       → Template de contrato        │
│ ├─ contract_start_date        → Fecha de inicio             │
│ ├─ contract_duration_months   → Duración en meses           │
│ ├─ contract_end_date          → Fecha fin (computed)        │
│ ├─ commission_percentage      → % Comisión                  │
│ ├─ reservation_id             → Reserva asociada            │
│ └─ reservation_count          → # de reservas               │
└─────────────────────────────────────────────────────────────┘
```

### CINTA 4 IZQUIERDA: Productos (15+ campos por producto)
```
┌─────────────────────────────────────────────────────────────┐
│ CAMPOS UTILIZADOS (property_ids - many2many):               │
│                                                              │
│ CADA PRODUCTO (product.template) MUESTRA:                   │
│ ├─ name              → Nombre de la propiedad               │
│ ├─ street            → Dirección                            │
│ ├─ city_id           → Ciudad                               │
│ ├─ state_id          → Departamento                         │
│ ├─ list_price        → Precio de venta                      │
│ ├─ monthly_rent      → Canon de arriendo (condicional)      │
│ ├─ num_bedrooms      → # Habitaciones                       │
│ ├─ num_bathrooms     → # Baños                              │
│ ├─ total_area        → Área en m²                           │
│ ├─ parking_spaces    → # Parqueaderos                       │
│ ├─ has_pool          → Tiene piscina (boolean)              │
│ ├─ has_gym           → Tiene gimnasio (boolean)             │
│ ├─ has_security      → Seguridad 24/7 (boolean)             │
│ ├─ has_elevator      → Tiene ascensor (boolean)             │
│ ├─ state             → Estado (disponible/reservado/etc)    │
│ └─ COMPUTED:                                                 │
│    └─ Tipo de precio (Venta/Arriendo según type_service)    │
│                                                              │
│ PASTILLAS/BADGES ADAPTATIVAS:                               │
│ ├─ Si es VENTA      → [💵 VENTA: $XXX]                     │
│ ├─ Si es ARRIENDO   → [💵 ARRIENDO: $XXX/mes]              │
│ ├─ Si es PROYECTO   → [💵 DESDE: $XXX]                     │
│ └─ Características  → [3 HAB] [2 BAÑ] [120m²] [🅿️ 2]      │
└─────────────────────────────────────────────────────────────┘
```

### CINTA 4 DERECHA: Cliente (35+ campos)
```
┌─────────────────────────────────────────────────────────────┐
│ CAMPOS UTILIZADOS:                                          │
│                                                              │
│ DATOS BÁSICOS:                                              │
│ ├─ name                  → Nombre del lead                  │
│ ├─ partner_id            → Cliente/Contacto                 │
│ ├─ client_type           → Tipo de cliente                  │
│ ├─ service_interested    → Servicio de interés              │
│ ├─ email_from            → Email                            │
│ ├─ mobile                → Celular                          │
│ ├─ phone                 → Teléfono fijo                    │
│ ├─ occupation            → Ocupación                        │
│ ├─ monthly_income        → Ingresos mensuales               │
│ ├─ request_source        → Origen de solicitud              │
│ └─ user_id               → Responsable                      │
│                                                              │
│ PREFERENCIAS DE BÚSQUEDA:                                   │
│ ├─ budget_min            → Presupuesto mínimo               │
│ ├─ budget_max            → Presupuesto máximo               │
│ ├─ desired_city          → Ciudad deseada                   │
│ ├─ desired_neighborhood  → Barrio deseado                   │
│ ├─ desired_property_type_id → Tipo de propiedad deseada     │
│ ├─ num_bedrooms_min      → Habitaciones mínimas             │
│ ├─ num_bedrooms_max      → Habitaciones máximas             │
│ ├─ num_bathrooms_min     → Baños mínimos                    │
│ ├─ property_area_min     → Área mínima                      │
│ ├─ property_area_max     → Área máxima                      │
│ ├─ requires_parking      → Requiere parqueadero             │
│ ├─ parking_spots         → # Parqueaderos necesarios        │
│ ├─ has_pets              → Tiene mascotas                   │
│ ├─ pet_type              → Tipo de mascota                  │
│ └─ property_purpose      → Propósito del inmueble           │
│                                                              │
│ AMENIDADES REQUERIDAS:                                      │
│ ├─ requires_common_areas → Zonas comunes                    │
│ ├─ requires_gym          → Gimnasio                         │
│ ├─ requires_pool         → Piscina                          │
│ ├─ requires_security     → Seguridad 24/7                   │
│ ├─ requires_elevator     → Ascensor                         │
│ └─ num_occupants         → # Personas que ocuparán          │
└─────────────────────────────────────────────────────────────┘
```

### CINTA 5: Colapsable (50+ campos adicionales en 7 secciones)
```
┌─────────────────────────────────────────────────────────────┐
│ SECCIÓN 1: FINANCIAMIENTO (6 campos)                       │
│ ├─ requires_financing     → Requiere financiación           │
│ ├─ loan_type              → Tipo de préstamo                │
│ ├─ loan_amount            → Monto del préstamo              │
│ ├─ loan_bank_id           → Entidad financiera              │
│ ├─ loan_approval_status   → Estado de aprobación            │
│ └─ loan_document_ids      → Documentos adjuntos             │
│                                                              │
│ SECCIÓN 2: MARKETING (12 campos)                            │
│ ├─ campaign_id                → Campaña                     │
│ ├─ source_id                  → Fuente                      │
│ ├─ medium_id                  → Medio                       │
│ ├─ marketing_campaign_type    → Tipo de campaña             │
│ ├─ marketing_budget_allocated → Presupuesto                 │
│ ├─ marketing_estimated_reach  → Alcance estimado            │
│ ├─ marketing_quantity         → # Anuncios                  │
│ ├─ marketing_schedule         → Horario preferido           │
│ ├─ marketing_start_date       → Fecha inicio                │
│ ├─ marketing_end_date         → Fecha fin                   │
│ ├─ marketing_description      → Descripción                 │
│ └─ COMPUTED:                                                 │
│    └─ Duración campaña (end - start)                        │
│                                                              │
│ SECCIÓN 3: CAPTACIÓN (5 campos)                             │
│ ├─ captured_by_id              → Captado por                │
│ ├─ capture_date                → Fecha de captación         │
│ ├─ capture_source              → Fuente de captación        │
│ ├─ capture_commission_rate     → % Comisión captación       │
│ └─ capture_commission_amount   → Monto comisión (computed)  │
│                                                              │
│ SECCIÓN 4: COMPARACIÓN (1 campo many2many)                  │
│ └─ compared_properties_ids     → Hasta 4 propiedades        │
│                                                              │
│ SECCIÓN 5: VISITAS (4 campos)                               │
│ ├─ ideal_visit_date            → Fecha ideal visita         │
│ ├─ visit_notes                 → Notas de visita            │
│ ├─ has_conflicting_visit       → Hay conflicto (computed)   │
│ └─ conflicting_visit_info      → Info del conflicto         │
│                                                              │
│ SECCIÓN 6: ACTIVIDADES (2 campos)                           │
│ ├─ activity_ids                → Actividades (widget)       │
│ └─ activity_state              → Estado de actividades      │
│                                                              │
│ SECCIÓN 7: REFERENCIAS (2 campos)                           │
│ ├─ referred_by_partner_id      → Referido por               │
│ └─ project_id                  → Proyecto inmobiliario      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📈 TOTAL DE CAMPOS MOSTRADOS

```
┌────────────────────────────────────────────────────────┐
│ RESUMEN GENERAL                                        │
├────────────────────────────────────────────────────────┤
│ CINTA 1: Botones + Etapas          │  8 elementos     │
│ CINTA 2: Métricas                  │  4 campos + 1    │
│ CINTA 3: Contrato                  │  7 campos        │
│ CINTA 4: Productos (izq)           │ 15 campos/prod   │
│ CINTA 4: Cliente (der)             │ 35 campos        │
│ CINTA 5: Colapsable                │ 50+ campos       │
├────────────────────────────────────────────────────────┤
│ TOTAL APROXIMADO                   │ 120+ CAMPOS      │
└────────────────────────────────────────────────────────┘
```

---

## 🎨 CARACTERÍSTICAS ESPECIALES

### 1. **CARDS DE PRODUCTOS ADAPTATIVOS**
```
SI type_service = 'sale':
   ┌──────────────────────────┐
   │ 💵 VENTA: $350,000,000   │
   └──────────────────────────┘

SI type_service = 'rent':
   ┌──────────────────────────┐
   │ 💵 ARRIENDO: $2,500,000  │
   │ /mes                     │
   └──────────────────────────┘

SI type_service = 'both':
   ┌──────────────────────────┐
   │ 💵 VENTA: $350,000,000   │
   │ 💵 ARRIENDO: $2,500,000  │
   │ /mes                     │
   └──────────────────────────┘
```

### 2. **PASTILLAS/BADGES PARA CARACTERÍSTICAS**
```
[3 HAB]  = num_bedrooms
[2 BAÑ]  = num_bathrooms
[120 m²] = total_area
[🅿️ 2]  = parking_spaces
[🏊 Sí]  = has_pool (si TRUE)
[🔒 24/7] = has_security (si TRUE)
[🏋️ Gym] = has_gym (si TRUE)
[🛗 Asc] = has_elevator (si TRUE)
```

### 3. **SECCIONES CONDICIONALES**
```
MOSTRAR FINANCIAMIENTO    → Solo si requires_financing = TRUE
MOSTRAR MARKETING         → Solo si campaign_id O marketing_campaign_type existe
MOSTRAR CAPTACIÓN        → Solo si service_interested = 'consign' Y captured_by_id existe
MOSTRAR COMPARACIÓN      → Solo si compared_properties_ids tiene elementos
MOSTRAR VISITAS          → Solo si ideal_visit_date existe
```

### 4. **BOTONES DE ACCIÓN**
```
📧 ENVIAR EMAIL      → Genera PDF y envía al cliente
✅ ELEGIR ESTA       → Marca esta oportunidad como seleccionada
📊 VER MÉTRICAS      → Abre dashboard de métricas completas
📝 EDITAR TODO       → Abre formulario completo
```

---

## 🎯 AGRUPACIÓN DE LA VISTA KANBAN

```
AGRUPAR POR: service_interested (Servicio de Interés)

┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│   VENTA     │  ARRIENDO   │  PROYECTOS  │  CONSIGNAR  │  MARKETING  │
├─────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│   [CARD 1]  │  [CARD 1]   │  [CARD 1]   │  [CARD 1]   │  [CARD 1]   │
│   [CARD 2]  │  [CARD 2]   │  [CARD 2]   │  [CARD 2]   │  [CARD 2]   │
│   [CARD 3]  │  [CARD 3]   │  [CARD 3]   │  [CARD 3]   │  [CARD 3]   │
│     ...     │     ...     │     ...     │     ...     │     ...     │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘

CADA COLUMNA CONTIENE LAS 5 CINTAS COMPLETAS
```

---

## ✉️ FUNCIÓN DE ENVÍO POR EMAIL

Al hacer clic en "📧 ENVIAR EMAIL":
1. Genera PDF con layout horizontal (5 cintas)
2. Incluye solo datos relevantes para el cliente
3. Oculta comisiones y datos internos
4. Adjunta PDF al email
5. Envía al email del cliente (email_from)

---

Este diseño permite:
✅ Ver toda la información en un formato horizontal tipo reporte
✅ Enviar por correo al cliente de forma profesional
✅ Seleccionar oportunidades específicas
✅ Expandir/colapsar secciones según necesidad
✅ Adaptar el precio mostrado según el tipo de producto
✅ Mostrar características en formato compacto con badges

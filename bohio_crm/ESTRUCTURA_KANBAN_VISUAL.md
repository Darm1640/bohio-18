# ESTRUCTURA VISUAL - KANBAN COMPLETA BOHIO CRM

## 📋 ORGANIZACIÓN DE CAMPOS

```
┌─────────────────────────────────────────────────────────────────────────┐
│ VISTA KANBAN AGRUPADA POR: service_interested (Tipo de Servicio)       │
│ ════════════════════════════════════════════════════════════════════    │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐   │
│  │   VENTA      │  │  ARRIENDO    │  │  PROYECTOS   │  │  CONSIGN │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🎴 ESTRUCTURA DE CADA TARJETA (CARD)

```
╔═══════════════════════════════════════════════════════════════════════╗
║                      TARJETA DE OPORTUNIDAD                           ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║  ┌─────────────────────────────────────────────────────────────────┐ ║
║  │ ⭐ SECCIÓN 1: DATOS BÁSICOS (SIEMPRE VISIBLE)                   │ ║
║  ├─────────────────────────────────────────────────────────────────┤ ║
║  │                                                                  │ ║
║  │  📌 NOMBRE DE LA OPORTUNIDAD                                    │ ║
║  │     └─ name (Lead/Opportunity Name)                             │ ║
║  │                                                                  │ ║
║  │  👤 CLIENTE                                (COLAPSADA POR DEFECTO)                           │ ║
║  │     ├─ partner_id (Cliente/Contacto)                            │ ║
║  │     └─ Si no hay: "Sin cliente"                                 │ ║
║  │                                                                  │ ║
║  │  📞 TELÉFONO                                                     │ ║
║  │     ├─ mobile (Celular) - PRIORIDAD                             │ ║
║  │     └─ phone (Fijo) - SI NO HAY MOBILE                          │ ║
║  │                                                                  │ ║
║  │  🏷️ BADGES DE CLASIFICACIÓN                                     │ ║
║  │     ├─ service_interested (Venta/Arriendo/Proyectos/etc)        │ ║
║  │     ├─ client_type (Comprador/Vendedor/Inversionista/etc)       │ ║
║  │     └─ stage_id (Etapa Actual)                                  │ ║
║  │                                                                  │ ║
║  │  💰 INGRESO ESPERADO                                            │ ║
║  │     ├─ expected_revenue (Valor monetario)                       │ ║
║  │     └─ probability (% de probabilidad)                          │ ║
║  │                                                                  │ ║
║  │  👨‍💼 RESPONSABLE                                                 │ ║
║  │     └─ user_id (Usuario asignado con avatar)                    │ ║
║  │                                                                  │ ║
║  └─────────────────────────────────────────────────────────────────┘ ║
║                                                                       ║
║  ┌─────────────────────────────────────────────────────────────────┐ ║
║  │ 🔽 BOTÓN: "Ver todos los datos" / "Ocultar datos"              │ ║
║  │    (Solo aparece si hay datos extras)                           │ ║
║  └─────────────────────────────────────────────────────────────────┘ ║
║                                                                       ║
║  ╔═══════════════════════════════════════════════════════════════╗  ║
║  ║ 📂 SECCIÓN EXPANDIBLE (COLAPSADA POR DEFECTO)                 ║  ║
║  ╠═══════════════════════════════════════════════════════════════╣  ║
║  ║                                                                ║  ║
║  ║  ┌────────────────────────────────────────────────────────┐   ║  ║
║  ║  │ 📇 SUBSECCIÓN 1: DATOS DE CONTACTO COMPLETOS           │   ║  ║
║  ║  ├────────────────────────────────────────────────────────┤   ║  ║
║  ║  │  ├─ email_from (Email)                                 │   ║  ║
║  ║  │  ├─ phone (Teléfono fijo completo)                     │   ║  ║
║  ║  │  ├─ mobile (Celular completo)                          │   ║  ║
║  ║  │  ├─ occupation (Ocupación)                             │   ║  ║
║  ║  │  ├─ monthly_income (Ingresos mensuales)                │   ║  ║
║  ║  │  └─ request_source (Origen: Web/WhatsApp/Teléfono)     │   ║  ║
║  ║  └────────────────────────────────────────────────────────┘   ║  ║
║  ║                                                                ║  ║
║  ║  ┌────────────────────────────────────────────────────────┐   ║  ║
║  ║  │ 📄 SUBSECCIÓN 2: DATOS DE CONTRATO (CONDICIONAL)      │   ║  ║
║  ║  │    ⚠️ Solo si: contract_template_id ≠ NULL            │   ║  ║
║  ║  ├────────────────────────────────────────────────────────┤   ║  ║
║  ║  │  ├─ contract_template_id (Template de contrato)        │   ║  ║
║  ║  │  ├─ reservation_id (Reserva asociada)                  │   ║  ║
║  ║  │  ├─ date_deadline (Fecha de cierre esperada)           │   ║  ║
║  ║  │  ├─ estimated_commission (Comisión estimada)           │   ║  ║
║  ║  │  └─ final_commission (Comisión final)                  │   ║  ║
║  ║  └────────────────────────────────────────────────────────┘   ║  ║
║  ║                                                                ║  ║
║  ║  ┌────────────────────────────────────────────────────────┐   ║  ║
║  ║  │ 📢 SUBSECCIÓN 3: CAMPAÑA DE MARKETING (CONDICIONAL)   │   ║  ║
║  ║  │    ⚠️ Solo si: campaign_id ≠ NULL                     │   ║  ║
║  ║  ├────────────────────────────────────────────────────────┤   ║  ║
║  ║  │  ├─ campaign_id (Campaña UTM)                          │   ║  ║
║  ║  │  ├─ source_id (Fuente UTM)                             │   ║  ║
║  ║  │  ├─ medium_id (Medio UTM)                              │   ║  ║
║  ║  │  ├─ marketing_campaign_type (Tipo: Social/Ads/Email)   │   ║  ║
║  ║  │  ├─ marketing_quantity (Cantidad de publicaciones)     │   ║  ║
║  ║  │  ├─ marketing_schedule (Horario: Mañana/Tarde/Noche)   │   ║  ║
║  ║  │  ├─ marketing_estimated_reach (Personas a alcanzar)    │   ║  ║
║  ║  │  ├─ marketing_budget_allocated (Presupuesto asignado)  │   ║  ║
║  ║  │  ├─ marketing_start_date (Fecha inicio)                │   ║  ║
║  ║  │  ├─ marketing_end_date (Fecha fin)                     │   ║  ║
║  ║  │  └─ marketing_description (Descripción campaña)        │   ║  ║
║  ║  │                                                         │   ║  ║
║  ║  │  ⚡ ALERTA: "Iniciar campaña de seguimiento"           │   ║  ║
║  ║  └────────────────────────────────────────────────────────┘   ║  ║
║  ║                                                                ║  ║
║  ║  ┌────────────────────────────────────────────────────────┐   ║  ║
║  ║  │ 🏠 SUBSECCIÓN 4: PROPIEDADES DE INTERÉS               │   ║  ║
║  ║  │    ⚠️ Solo si: property_ids ≠ EMPTY                   │   ║  ║
║  ║  ├────────────────────────────────────────────────────────┤   ║  ║
║  ║  │  ├─ property_ids (Tags de propiedades)                 │   ║  ║
║  ║  │  ├─ desired_city (Ciudad deseada)                      │   ║  ║
║  ║  │  ├─ desired_neighborhood (Barrio deseado)              │   ║  ║
║  ║  │  ├─ desired_property_type_id (Tipo de propiedad)       │   ║  ║
║  ║  │  ├─ budget_min / budget_max (Presupuesto)              │   ║  ║
║  ║  │  ├─ num_bedrooms_min / max (Habitaciones)              │   ║  ║
║  ║  │  ├─ num_bathrooms_min (Baños)                          │   ║  ║
║  ║  │  ├─ property_area_min / max (Área m²)                  │   ║  ║
║  ║  │  ├─ has_pets (Tiene mascotas)                          │   ║  ║
║  ║  │  ├─ pet_type (Tipo de mascota: Perro/Gato)            │   ║  ║
║  ║  │  ├─ requires_parking (Requiere parqueadero)            │   ║  ║
║  ║  │  ├─ parking_spots (# de parqueaderos)                  │   ║  ║
║  ║  │  ├─ num_occupants (# de ocupantes)                     │   ║  ║
║  ║  │  ├─ property_purpose (Propósito: Vivienda/Oficina)     │   ║  ║
║  ║  │  └─ AMENIDADES:                                        │   ║  ║
║  ║  │     ├─ requires_common_areas (Zonas comunes)           │   ║  ║
║  ║  │     ├─ requires_gym (Gimnasio)                         │   ║  ║
║  ║  │     ├─ requires_pool (Piscina)                         │   ║  ║
║  ║  │     ├─ requires_security (Seguridad 24/7)              │   ║  ║
║  ║  │     └─ requires_elevator (Ascensor)                    │   ║  ║
║  ║  └────────────────────────────────────────────────────────┘   ║  ║
║  ║                                                                ║  ║
║  ║  ┌────────────────────────────────────────────────────────┐   ║  ║
║  ║  │ 🏦 SUBSECCIÓN 5: FINANCIAMIENTO (CONDICIONAL)         │   ║  ║
║  ║  │    ⚠️ Solo si: requires_financing = TRUE              │   ║  ║
║  ║  ├────────────────────────────────────────────────────────┤   ║  ║
║  ║  │  ├─ loan_type (Hipoteca/Leasing/Subsidiada)            │   ║  ║
║  ║  │  ├─ loan_amount (Monto solicitado)                     │   ║  ║
║  ║  │  ├─ loan_bank_id (Entidad financiera)                  │   ║  ║
║  ║  │  ├─ loan_approval_status (Estado: Aprobado/Pendiente)  │   ║  ║
║  ║  │  └─ loan_document_ids (Documentos adjuntos)            │   ║  ║
║  ║  └────────────────────────────────────────────────────────┘   ║  ║
║  ║                                                                ║  ║
║  ║  ┌────────────────────────────────────────────────────────┐   ║  ║
║  ║  │ 🤝 SUBSECCIÓN 6: CAPTACIÓN (CONDICIONAL)              │   ║  ║
║  ║  │    ⚠️ Solo si: service_interested = 'consign'         │   ║  ║
║  ║  ├────────────────────────────────────────────────────────┤   ║  ║
║  ║  │  ├─ captured_by_id (Captado por)                       │   ║  ║
║  ║  │  ├─ capture_date (Fecha de captación)                  │   ║  ║
║  ║  │  ├─ capture_source (Fuente: Referido/Cold Call/etc)    │   ║  ║
║  ║  │  ├─ capture_commission_rate (% de comisión)            │   ║  ║
║  ║  │  └─ capture_commission_amount (Monto comisión)         │   ║  ║
║  ║  └────────────────────────────────────────────────────────┘   ║  ║
║  ║                                                                ║  ║
║  ║  ┌────────────────────────────────────────────────────────┐   ║  ║
║  ║  │ ✅ SUBSECCIÓN 7: ACTIVIDADES                          │   ║  ║
║  ║  ├────────────────────────────────────────────────────────┤   ║  ║
║  ║  │  └─ activity_ids (Widget kanban_activity)              │   ║  ║
║  ║  └────────────────────────────────────────────────────────┘   ║  ║
║  ║                                                                ║  ║
║  ╚═══════════════════════════════════════════════════════════════╝  ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

## 🎨 AGRUPACIONES DISPONIBLES

```
OPCIÓN 1: Agrupar por TIPO DE SERVICIO (service_interested)
┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│  VENTA   │ ARRIENDO │PROYECTOS │ CONSIGN  │ LEGAL    │ MARKETING│CORPORATE │ AVALÚOS  │
│  (sale)  │  (rent)  │(projects)│(consign) │ (legal)  │(marketing│(corporate│(valuation│
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘

OPCIÓN 2: Agrupar por TIPO DE CLIENTE (client_type)
┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│PROPIETARIO│ARRENDATARIO│COMPRADOR│VENDEDOR │INVERSIONISTA│  OTRO  │
│  (owner)  │ (tenant)  │ (buyer) │(seller) │ (investor)  │(other) │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘

OPCIÓN 3: Agrupar por ETAPA (stage_id)
┌──────────┬──────────┬──────────┬──────────┬──────────┐
│  NUEVA   │CALIFICADA│PROPUESTA │NEGOCIACIÓN│  GANADA  │
└──────────┴──────────┴──────────┴──────────┴──────────┘

OPCIÓN 4: Agrupar por USUARIO (user_id)
┌──────────┬──────────┬──────────┬──────────┐
│ JUAN P.  │ MARÍA G. │ CARLOS R.│  ADMIN   │
└──────────┴──────────┴──────────┴──────────┘
```

---

## 📊 TOTAL DE CAMPOS INCLUIDOS

```
┌─────────────────────────────────────────────────────┐
│ CATEGORÍA                    │ # CAMPOS │ VISIBLE  │
├──────────────────────────────┼──────────┼──────────┤
│ DATOS BÁSICOS (Siempre)     │    8     │ SIEMPRE  │
│ Contacto Completo            │    6     │ Expandir │
│ Contrato                     │    5     │ Condicional (si existe contrato) │
│ Marketing                    │   12     │ Condicional (si viene de campaña)│
│ Propiedades                  │   15     │ Condicional (si hay propiedades) │
│ Financiamiento               │    5     │ Condicional (si requiere) │
│ Captación                    │    5     │ Condicional (si es consignación)│
│ Actividades                  │    1     │ Expandir │
├──────────────────────────────┼──────────┼──────────┤
│ TOTAL                        │   57     │          │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 LÓGICA DE VISUALIZACIÓN

```
SI tarjeta.collapsed = TRUE (por defecto):
    MOSTRAR:
    ├─ Nombre
    ├─ Cliente
    ├─ Teléfono
    ├─ Badges (servicio, cliente, etapa)
    ├─ Ingreso esperado
    ├─ Responsable
    └─ Botón "Ver todos los datos"

SI usuario HACE CLIC en "Ver todos los datos":
    tarjeta.collapsed = FALSE
    MOSTRAR TAMBIÉN:
    ├─ Datos de contacto completos
    ├─ SI contract_template_id != NULL → Datos de contrato
    ├─ SI campaign_id != NULL → Datos de marketing
    ├─ SI property_ids != EMPTY → Propiedades de interés
    ├─ SI requires_financing = TRUE → Financiamiento
    ├─ SI service = 'consign' → Captación
    └─ Actividades

SI usuario HACE CLIC en "Ocultar datos":
    tarjeta.collapsed = TRUE
    OCULTAR sección expandible
```

---

## 🔄 FLUJO DE INTERACCIÓN

```
Usuario entra a la vista
         │
         ▼
┌────────────────────┐
│ VISTA KANBAN       │
│ Agrupada por       │
│ service_interested │
└────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Columnas automáticas:                  │
│ • Venta                                │
│ • Arriendo                             │
│ • Proyectos                            │
│ • Consignación                         │
│ • etc.                                 │
└────────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│ Cada columna muestra tarjetas:         │
│                                        │
│ ┌──────────────┐                       │
│ │ Tarjeta 1    │ ← Datos básicos       │
│ │ [Compacta]   │   siempre visibles    │
│ └──────────────┘                       │
│                                        │
│ ┌──────────────┐                       │
│ │ Tarjeta 2    │                       │
│ │ [Compacta]   │                       │
│ └──────────────┘                       │
└────────────────────────────────────────┘
         │
         ▼
Usuario HACE CLIC en "Ver todos los datos"
         │
         ▼
┌────────────────────────────────────────┐
│ Tarjeta se EXPANDE                     │
│                                        │
│ ┌──────────────────────────────────┐   │
│ │ Datos básicos                    │   │
│ ├──────────────────────────────────┤   │
│ │ ▼ SECCIÓN EXPANDIDA              │   │
│ │   • Contacto completo            │   │
│ │   • Contrato (si existe)         │   │
│ │   • Marketing (si viene campaña) │   │
│ │   • Propiedades                  │   │
│ │   • Financiamiento               │   │
│ │   • Captación                    │   │
│ │   • Actividades                  │   │
│ └──────────────────────────────────┘   │
└────────────────────────────────────────┘
```

---

## ✨ CARACTERÍSTICAS ESPECIALES

### 1. BADGES DINÁMICOS CON COLORES

```
service_interested:
├─ 'sale'      → 🔵 Azul (primary)
├─ 'rent'      → 🔷 Cyan (info)
├─ 'projects'  → 🟢 Verde (success)
├─ 'consign'   → 🟡 Amarillo (warning)
├─ 'marketing' → 🔴 Rojo (danger)
└─ 'legal'     → ⚫ Gris (secondary)
```

### 2. SECCIONES CONDICIONALES

```
┌─────────────────────────────────────────────┐
│ SUBSECCIÓN               │ SE MUESTRA SI:  │
├──────────────────────────┼─────────────────┤
│ Datos de Contrato        │ contract_template_id != NULL │
│ Campaña de Marketing     │ campaign_id != NULL          │
│ Propiedades de Interés   │ property_ids != EMPTY        │
│ Financiamiento           │ requires_financing = TRUE    │
│ Captación                │ service = 'consign'          │
└─────────────────────────────────────────────┘
```

### 3. ALERTAS INTELIGENTES

```
SI campaign_id != NULL:
    MOSTRAR alerta:
    ┌──────────────────────────────────────┐
    │ ⚠️ ACCIÓN SUGERIDA:                  │
    │ Iniciar campaña de seguimiento       │
    └──────────────────────────────────────┘
```

---

## 📱 RESPONSIVE

```
DESKTOP (> 1200px):
┌──────┬──────┬──────┬──────┐
│Card 1│Card 2│Card 3│Card 4│
└──────┴──────┴──────┴──────┘

TABLET (768px - 1200px):
┌──────┬──────┬──────┐
│Card 1│Card 2│Card 3│
└──────┴──────┴──────┘

MOBILE (< 768px):
┌──────┐
│Card 1│
├──────┤
│Card 2│
└──────┘
```

---

**¿Te parece bien esta estructura? ¿Quieres que ajuste algo?**

Confirma y creo la vista con este diseño exacto.

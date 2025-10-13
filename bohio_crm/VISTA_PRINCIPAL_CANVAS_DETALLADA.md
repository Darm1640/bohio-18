# 📋 VISTA PRINCIPAL KANBAN CANVAS - DETALLE COMPLETO

## 🎯 VISIÓN GENERAL

Esta es la **ÚNICA vista kanban** del módulo CRM, diseñada con estilo canvas elegante, agrupada por etapas y mostrando 4 columnas a la vez.

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                            🔍 BARRA DE BÚSQUEDA                                          │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ 🔍 [Buscar oportunidades...]  [📁 Filtros] [⚙️ Agrupación] [➕ Crear Nueva]       │ │
│  └────────────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                         📊 COLUMNAS DE ETAPAS (4 EN 4)                                   │
│  ═══════════════════════════════════════════════════════════════════════════════════    │
│                                                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │
│  │ NUEVA  [5]  │  │ CALIFICADA  │  │ PROPUESTA   │  │ NEGOCIACIÓN │  ◀ Scroll →        │
│  │             │  │     [8]     │  │     [3]     │  │     [2]     │                    │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤  ├─────────────┤                   │
│  │             │  │             │  │             │  │             │                    │
│  │  [CARD 1]   │  │  [CARD 1]   │  │  [CARD 1]   │  │  [CARD 1]   │                    │
│  │             │  │             │  │             │  │             │                    │
│  │  [CARD 2]   │  │  [CARD 2]   │  │  [CARD 2]   │  │  [CARD 2]   │                    │
│  │             │  │             │  │             │  │             │                    │
│  │  [CARD 3]   │  │  [CARD 3]   │  │  [CARD 3]   │  │             │                    │
│  │             │  │             │  │             │  │  [+ CREAR]  │                    │
│  │  [CARD 4]   │  │  [CARD 4]   │  │  [+ CREAR]  │  │   RÁPIDA    │                    │
│  │             │  │             │  │   RÁPIDA    │  │             │                    │
│  │  [CARD 5]   │  │  [CARD 5]   │  │             │  └─────────────┘                   │
│  │             │  │             │  └─────────────┘                                      │
│  │  [+ CREAR]  │  │  [CARD 6]   │                                                       │
│  │   RÁPIDA    │  │             │  ◀─────────── DRAGGABLE ───────────▶                 │
│  │             │  │  [CARD 7]   │                                                       │
│  └─────────────┘  │             │                                                       │
│                   │  [CARD 8]   │                                                       │
│                   │             │                                                       │
│                   │  [+ CREAR]  │                                                       │
│                   │   RÁPIDA    │                                                       │
│                   │             │                                                       │
│                   └─────────────┘                                                       │
│                                                                                           │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📱 DETALLE DE UN CARD (TARJETA)

Cada card muestra información compacta y elegante:

```
┌─────────────────────────────────────────────────────────────────────┐
│  ⭐⭐⭐                                                    🔴 [Color] │ ← Aside (Prioridad + Color)
├─────────────────────────────────────────────────────────────────────┤
│  📋 HEADER                                                          │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ Casa en El Poblado - Cliente Nuevo           [VENTA]          │ │ ← Título + Badge Servicio
│  └───────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│  👤 CLIENTE                                                         │
│  👤 Juan Pérez García                                              │
│  📱 +57 300 123 4567                                               │
├─────────────────────────────────────────────────────────────────────┤
│  💰 MÉTRICAS                                                        │
│  ┌──────────────────────┬──────────────────────────────────────┐  │
│  │ 💵 $350,000,000      │ 💸 $35,000,000                       │  │
│  │    Ingreso Esperado  │    Comisión Est.                     │  │
│  └──────────────────────┴──────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│  🏠 PROPIEDADES                                                     │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ 🏡 3 Propiedades de Interés                                   │ │
│  └───────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│  🔍 PREFERENCIAS (BADGES)                                           │
│  [📍 Medellín] [$300M] [3 HAB]                                     │
├─────────────────────────────────────────────────────────────────────┤
│  🗺️ MAPA (COMPRIMIDO POR DEFECTO)                                  │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ [▼ Ver Mapa]                                                   │ │ ← Botón colapsar/expandir
│  └───────────────────────────────────────────────────────────────┘ │
│  │                                                                 │ │
│  │ (Cuando se expande)                                            │ │
│  │ ┌───────────────────────────────────────────────────────────┐ │ │
│  │ │                                                             │ │ │
│  │ │         🗺️  MAPA INTERACTIVO LEAFLET                       │ │ │
│  │ │           Ubicación basada en propiedades                  │ │ │
│  │ │                                                             │ │ │
│  │ └───────────────────────────────────────────────────────────┘ │ │
│  │ [▲ Ocultar Mapa]                                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│  ℹ️ DETALLES ADICIONALES (COMPRIMIDO POR DEFECTO)                  │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │ [▼ Ver Más Detalles]                                           │ │ ← Botón colapsar/expandir
│  └───────────────────────────────────────────────────────────────┘ │
│  │                                                                 │ │
│  │ (Cuando se expande)                                            │ │
│  │ ┌───────────────────────────────────────────────────────────┐ │ │
│  │ │ 📧 juan.perez@email.com                                    │ │ │
│  │ │ ☎️ 604 123 4567                                            │ │ │
│  │ │ 🏷️ Tipo: Comprador                                        │ │ │
│  │ │ 🎯 Origen: Sitio Web                                       │ │ │
│  │ │ 📄 Contrato: Arrendamiento Residencial                    │ │ │
│  │ │ 📅 Cierre: 2024-12-31                                      │ │ │
│  │ │                                                             │ │ │
│  │ │ [📢 Marketing] [🏦 Financiamiento] [📌 Reservado]          │ │ │
│  │ └───────────────────────────────────────────────────────────┘ │ │
│  │ [▲ Ocultar Detalles]                                           │ │
│  └───────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│  👔 FOOTER                                                          │
│  ┌────────────────────┬────────────────────────────────────────┐  │
│  │ 👤 María López     │              🟢 ⏰ 🔔                 │  │
│  │    Responsable     │         Actividades                     │  │
│  └────────────────────┴────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎨 CARACTERÍSTICAS DE LA VISTA

### 1. **AGRUPACIÓN POR ETAPAS**
```
┌──────────────────────────────────────────────────────────────────┐
│ ETAPAS DISPONIBLES (stage_id):                                  │
├──────────────────────────────────────────────────────────────────┤
│ 1. Nueva                  → Oportunidades recién creadas         │
│ 2. Calificada             → Oportunidades validadas              │
│ 3. Propuesta              → Propuesta enviada al cliente         │
│ 4. Negociación            → En proceso de negociación            │
│ 5. Ganada                 → Cierre exitoso                       │
│ 6. Perdida                → Oportunidad perdida                  │
└──────────────────────────────────────────────────────────────────┘

VISUALIZACIÓN: 4 columnas visibles a la vez
NAVEGACIÓN: Scroll horizontal para ver más etapas
ARRASTRE: Las cards se pueden arrastrar entre columnas
```

### 2. **BARRA DE BÚSQUEDA SUPERIOR**
```
┌──────────────────────────────────────────────────────────────────┐
│ FUNCIONES DE LA BARRA:                                          │
├──────────────────────────────────────────────────────────────────┤
│ 🔍 Campo de búsqueda    → Buscar por nombre, cliente, ciudad    │
│ 📁 Filtros              → Filtros predefinidos (Mis oportun.)   │
│ ⚙️ Agrupación           → Cambiar agrupación (Etapa, Usuario)   │
│ 📊 Vista                → Cambiar a List, Form, Calendar, etc.  │
│ ➕ Crear Nueva          → Crear oportunidad (Quick Create)      │
└──────────────────────────────────────────────────────────────────┘
```

### 3. **CREAR RÁPIDA (QUICK CREATE)**
```
┌──────────────────────────────────────────────────────────────────┐
│ AL HACER CLIC EN "+ CREAR RÁPIDA" EN CUALQUIER COLUMNA:         │
├──────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ ➕ Crear Nueva Oportunidad                                 │ │
│  │ ┌──────────────────────────────────────────────────────────┤ │
│  │ │ Nombre: [__________________________________]             │ │
│  │ │ Cliente: [__________________________________]            │ │
│  │ │ Email: [__________________________________]              │ │
│  │ │ Teléfono: [__________________________________]           │ │
│  │ │ Servicio: [▼ Venta]                                     │ │
│  │ │                                                          │ │
│  │ │ [✓ Crear]  [✗ Cancelar]  [📝 Editar Completo]         │ │
│  │ └──────────────────────────────────────────────────────────┤ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ CAMPOS VISIBLES:                                                 │
│ - Nombre de la oportunidad (obligatorio)                        │
│ - Cliente/Contacto                                              │
│ - Email                                                          │
│ - Teléfono/Móvil                                                │
│ - Servicio de Interés                                           │
│                                                                  │
│ Se crea directamente en la ETAPA donde se hizo clic             │
└──────────────────────────────────────────────────────────────────┘
```

### 4. **DRAG & DROP (ARRASTRAR Y SOLTAR)**
```
┌──────────────────────────────────────────────────────────────────┐
│ FUNCIONALIDAD:                                                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [NUEVA] ──────────▶ [CALIFICADA] ──────────▶ [PROPUESTA]       │
│     ↑                    ↑                         ↑             │
│     └────────────────────┴─────────────────────────┘             │
│                                                                  │
│ • Arrastra cualquier card a otra columna                        │
│ • La etapa se actualiza automáticamente                         │
│ • Animación visual al arrastrar                                 │
│ • No se puede arrastrar a "Ganada" sin propiedades              │
└──────────────────────────────────────────────────────────────────┘
```

### 5. **MAPA INTERACTIVO (COMPRIMIDO)**
```
┌──────────────────────────────────────────────────────────────────┐
│ CARACTERÍSTICAS DEL MAPA:                                        │
├──────────────────────────────────────────────────────────────────┤
│ • COMPRIMIDO POR DEFECTO (no ocupa espacio)                     │
│ • Se expande al hacer clic en "Ver Mapa"                        │
│ • Usa Leaflet.js para renderizar                                │
│ • Muestra ubicación promedio de propiedades de interés          │
│ • Marcadores para cada propiedad                                │
│ • Tooltip con información al pasar el mouse                     │
│                                                                  │
│ UBICACIÓN CALCULADA:                                             │
│ - Si tiene propiedades → Promedio de lat/lng propiedades        │
│ - Si no tiene → Ubicación del cliente (partner)                 │
│ - Si ninguno → "Sin ubicación disponible"                       │
└──────────────────────────────────────────────────────────────────┘
```

### 6. **DETALLES ADICIONALES (COMPRIMIDOS)**
```
┌──────────────────────────────────────────────────────────────────┐
│ INFORMACIÓN EXPANDIBLE:                                          │
├──────────────────────────────────────────────────────────────────┤
│ • Email adicional                                                │
│ • Teléfono fijo                                                  │
│ • Tipo de cliente (Owner, Tenant, Buyer, etc.)                  │
│ • Origen de la solicitud (Web, WhatsApp, Phone, etc.)           │
│ • Template de contrato (si existe)                              │
│ • Fecha de cierre estimada                                      │
│ • Badges de estado:                                             │
│   - 📢 Campaña de Marketing activa                             │
│   - 🏦 Requiere Financiamiento                                 │
│   - 📌 Tiene Reserva                                            │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📏 DIMENSIONES Y RESPONSIVE

### ESCRITORIO GRANDE (> 1600px)
```
┌─────────────────────────────────────────────────────────────────┐
│  [COLUMNA 1]  [COLUMNA 2]  [COLUMNA 3]  [COLUMNA 4]  → Scroll  │
│      25%          25%          25%          25%                  │
│   Min 280px   Min 280px   Min 280px   Min 280px                │
│   Max 350px   Max 350px   Max 350px   Max 350px                │
└─────────────────────────────────────────────────────────────────┘
```

### ESCRITORIO MEDIANO (1200px - 1600px)
```
┌─────────────────────────────────────────────────────────────────┐
│  [COLUMNA 1]  [COLUMNA 2]  [COLUMNA 3]  → Scroll               │
│     33.33%       33.33%       33.33%                            │
└─────────────────────────────────────────────────────────────────┘
```

### TABLET (768px - 1200px)
```
┌─────────────────────────────────────────────────────────────────┐
│  [COLUMNA 1]      [COLUMNA 2]      → Scroll                    │
│       50%              50%                                       │
└─────────────────────────────────────────────────────────────────┘
```

### MÓVIL (< 768px)
```
┌─────────────────────────────────────────────────────────────────┐
│  [COLUMNA 1]                                                    │
│       100%                                                       │
│       ↓                                                          │
│  [COLUMNA 2]                                                    │
│       100%                                                       │
│       ↓                                                          │
│  [COLUMNA 3]                                                    │
│       100%                                                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎨 PALETA DE COLORES

### BADGES DE SERVICIO
```
┌───────────────────────────────────────────────────────────────┐
│ VENTA         → Azul (bg-primary)     #0d6efd                │
│ ARRIENDO      → Celeste (bg-info)     #0dcaf0                │
│ PROYECTOS     → Verde (bg-success)    #198754                │
│ CONSIGNAR     → Amarillo (bg-warning) #ffc107                │
│ MARKETING     → Rojo (bg-danger)      #dc3545                │
│ OTROS         → Gris (bg-secondary)   #6c757d                │
└───────────────────────────────────────────────────────────────┘
```

### HEADER DE COLUMNAS
```
┌───────────────────────────────────────────────────────────────┐
│ Gradiente Morado → De #667eea a #764ba2                      │
│ Texto → Blanco                                                │
│ Contador → Fondo blanco semi-transparente                    │
└───────────────────────────────────────────────────────────────┘
```

### MÉTRICAS
```
┌───────────────────────────────────────────────────────────────┐
│ Fondo → Gradiente gris claro (#f8f9fa → #e9ecef)            │
│ Ingreso → Verde (#198754)                                     │
│ Comisión → Azul (#0d6efd)                                    │
│ Íconos → Colores específicos según función                   │
└───────────────────────────────────────────────────────────────┘
```

---

## 🔄 INTERACCIONES DEL USUARIO

### 1. HACER CLIC EN UNA CARD
```
┌───────────────────────────────────────────────────────────────┐
│ ACCIÓN: Click en cualquier parte del card                    │
│ RESULTADO: Abre el formulario completo en modo edición      │
└───────────────────────────────────────────────────────────────┘
```

### 2. EXPANDIR MAPA
```
┌───────────────────────────────────────────────────────────────┐
│ ACCIÓN: Click en "Ver Mapa"                                  │
│ RESULTADO:                                                    │
│ • Animación de expansión suave (0.3s)                        │
│ • Mapa se renderiza con Leaflet                              │
│ • Botón cambia a "Ocultar Mapa"                             │
│ • Íco no rota 180°                                            │
└───────────────────────────────────────────────────────────────┘
```

### 3. EXPANDIR DETALLES
```
┌───────────────────────────────────────────────────────────────┐
│ ACCIÓN: Click en "Ver Más Detalles"                          │
│ RESULTADO:                                                    │
│ • Animación de expansión suave (0.3s)                        │
│ • Se muestran todos los campos adicionales                   │
│ • Botón cambia a "Ocultar Detalles"                         │
│ • Ícono rota 180°                                             │
└───────────────────────────────────────────────────────────────┘
```

### 4. ARRASTRAR CARD
```
┌───────────────────────────────────────────────────────────────┐
│ ACCIÓN: Arrastrar card a otra columna                        │
│ RESULTADO:                                                    │
│ • Card se eleva con sombra                                   │
│ • Card rota ligeramente (3°)                                 │
│ • Columna destino se resalta                                 │
│ • Al soltar: actualiza etapa automáticamente                │
└───────────────────────────────────────────────────────────────┘
```

### 5. HOVER SOBRE CARD
```
┌───────────────────────────────────────────────────────────────┐
│ ACCIÓN: Pasar mouse sobre card                               │
│ RESULTADO:                                                    │
│ • Sombra más pronunciada                                     │
│ • Card se eleva 2px                                          │
│ • Borde cambia a color morado (#667eea)                     │
│ • Transición suave (0.3s)                                    │
└───────────────────────────────────────────────────────────────┘
```

---

## 📊 CAMPOS MOSTRADOS EN CADA SECCIÓN

### HEADER (SIEMPRE VISIBLE)
```
✓ name              → Nombre de la oportunidad
✓ service_interested → Badge de servicio (Venta, Arriendo, etc.)
✓ priority          → Estrellas (1-3)
✓ color             → Color picker
```

### CLIENTE (SIEMPRE VISIBLE)
```
✓ partner_id → Nombre del cliente/contacto
✓ mobile     → Teléfono móvil (link clicable)
```

### MÉTRICAS (SIEMPRE VISIBLE)
```
✓ expected_revenue      → Ingreso esperado
✓ estimated_commission  → Comisión estimada
✓ company_currency      → Moneda
```

### PROPIEDADES (SI TIENE)
```
✓ property_ids → Cantidad de propiedades de interés
```

### PREFERENCIAS (SI TIENE)
```
✓ desired_city      → Ciudad deseada
✓ budget_min        → Presupuesto mínimo
✓ num_bedrooms_min  → Habitaciones mínimas
```

### MAPA (COLAPSABLE - COMPRIMIDO POR DEFECTO)
```
✓ partner_latitude  → Latitud calculada
✓ partner_longitude → Longitud calculada
✓ property_ids      → Propiedades para marcar en mapa
```

### DETALLES (COLAPSABLE - COMPRIMIDO POR DEFECTO)
```
✓ email_from            → Email
✓ phone                 → Teléfono fijo
✓ client_type           → Tipo de cliente
✓ request_source        → Origen de solicitud
✓ contract_template_id  → Template de contrato
✓ date_deadline         → Fecha de cierre
✓ campaign_id           → Campaña de marketing (badge)
✓ requires_financing    → Financiamiento (badge)
✓ reservation_id        → Reserva (badge)
```

### FOOTER (SIEMPRE VISIBLE)
```
✓ user_id       → Responsable (avatar + nombre)
✓ activity_ids  → Widget de actividades
✓ activity_state → Estado de actividad (color)
```

---

## 🚀 RENDIMIENTO

### OPTIMIZACIONES
```
┌───────────────────────────────────────────────────────────────┐
│ • Solo 4 columnas visibles a la vez                          │
│ • Mapa NO se renderiza hasta que se expande                  │
│ • Detalles adicionales NO se cargan hasta expandir           │
│ • Imágenes lazy loading (si se agregan fotos)                │
│ • Transiciones CSS (no JavaScript)                           │
│ • Scroll virtual para listas largas                          │
└───────────────────────────────────────────────────────────────┘
```

---

## 📝 RESUMEN FINAL

```
┌──────────────────────────────────────────────────────────────────┐
│ VISTA KANBAN CANVAS - CARACTERÍSTICAS PRINCIPALES               │
├──────────────────────────────────────────────────────────────────┤
│ ✅ Una sola vista kanban (se eliminaron las demás)              │
│ ✅ Agrupada por etapas (stage_id)                               │
│ ✅ 4 columnas visibles a la vez                                 │
│ ✅ Scroll horizontal para más etapas                            │
│ ✅ Barra de búsqueda superior                                   │
│ ✅ Quick Create (crear rápida) en cada columna                  │
│ ✅ Drag & Drop entre columnas                                   │
│ ✅ Mapa comprimido por defecto                                  │
│ ✅ Detalles adicionales comprimidos por defecto                 │
│ ✅ Diseño elegante estilo canvas/portal                         │
│ ✅ Responsive (4/3/2/1 columnas según pantalla)                 │
│ ✅ Animaciones suaves                                           │
│ ✅ CSS optimizado sin errores                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

**ARCHIVOS RELACIONADOS:**
- Vista XML: `bohio_crm/views/crm_lead_kanban_canvas.xml`
- CSS: `bohio_crm/static/src/css/crm_kanban_canvas.css`
- Manifest: `bohio_crm/__manifest__.py` (ya actualizado)

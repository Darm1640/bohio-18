# 🚀 BOHIO CRM - Quick Create Inteligente

## 📋 Descripción

Vista de creación rápida condicional para CRM inspirada en el widget de conciliación bancaria de Odoo 18.

### ✨ Características Principales

1. **Campos Condicionales Dinámicos**
   - Los campos cambian según el `service_interested` seleccionado
   - Validaciones contextuales
   - Ocultamiento automático de campos irrelevantes

2. **Badges de Estado por Etapa**
   - Nueva Oportunidad
   - Seguimiento Requerido
   - En Negociación
   - Propuesta Enviada
   - Ganada

3. **Sistema de Sugerencias Inteligentes**
   - Aprende de tus elecciones frecuentes
   - Sugiere valores basados en estadísticas
   - Autocompletado inteligente
   - Notificaciones contextuales

4. **Creación de Producto desde Captación**
   - Botón especial para crear ficha de inmueble
   - Pre-rellena datos desde la oportunidad
   - Vinculación automática

5. **Seguimiento con `request_source`**
   - Origen de la solicitud rastreado
   - Estadísticas de fuentes más efectivas

---

## 🎯 Campos Condicionales por Servicio

### **🏠 VENTA (`sale`)**
Campos mostrados:
- Rango de Presupuesto (Min - Max)
- Tipo de Inmueble Deseado
- Ciudad y Barrio Deseado
- Propósito de la Propiedad
- Características (habitaciones, baños, área)
- Amenidades requeridas

**Sugerencias automáticas:**
- Client Type → `buyer`
- Tags → `['Compra', 'Inversión', 'Primera Vivienda']`
- Probabilidad inicial → 30%

---

### **🏡 ARRIENDO (`rent`)**
Campos mostrados:
- Presupuesto Mensual (Min - Max)
- Ingresos Mensuales del Cliente
- Número de Ocupantes
- Mascotas (Sí/No + Tipo)
- Parqueadero requerido (Sí/No + Cantidad)
- Características y amenidades

**Sugerencias automáticas:**
- Client Type → `tenant`
- Tags → `['Arriendo', 'Temporal', 'Largo Plazo']`
- Probabilidad inicial → 40%

---

### **🏗️ PROYECTOS (`projects`)**
Campos mostrados:
- Proyecto Inmobiliario (Many2one)
- Propósito de la Inversión
- Presupuesto de Inversión

**Sugerencias automáticas:**
- Client Type → `investor`
- Tags → `['Proyecto Nuevo', 'Preventa', 'Inversión']`
- Carga proyectos activos disponibles

---

### **📝 CONSIGNACIÓN (`consign`)**
Campos mostrados:
- Ubicación del Inmueble (Ciudad + Barrio)
- Tipo de Inmueble
- Valor Estimado
- Área (m²)

**Funcionalidad especial:**
- **Botón "Crear Ficha de Inmueble"** → Crea `product.template` con:
  - Nombre: `[CAPTACIÓN] {nombre_oportunidad}`
  - Estado: `draft`
  - Propietario vinculado
  - Datos pre-llenados
  - Vinculación automática con el lead

**Sugerencias automáticas:**
- Client Type → `owner`
- Tags → `['Captación', 'Exclusiva', 'Avalúo Pendiente']`
- Notificación recordatorio

---

### **🛠️ SERVICIOS (`legal`, `marketing`, `corporate`, `valuation`)**
Campos mostrados:
- Valor Estimado del Servicio
- Descripción del Requerimiento

**Sugerencias automáticas:**
- Tags → `['Servicio', 'Consultoría']`

---

## 🧠 Sistema de Sugerencias Inteligentes

### **Cómo Funciona**

1. **Aprendizaje Local (localStorage)**
   - Guarda tus últimas 10 elecciones por campo
   - Almacenado en `bohio_crm_recent_choices`

2. **Estadísticas del Backend**
   - Analiza tus últimos 30 días de actividad
   - Método: `crm.lead.get_smart_suggestions()`

3. **Sugerencias Contextuales**
   ```javascript
   // Ejemplo: Cuando seleccionas "Venta"
   ✨ Tipo de cliente sugerido: Comprador
   🏘️ Encontradas 15 propiedades en tu rango de presupuesto
   ```

### **Notificaciones Inteligentes**

- **Rango de presupuesto:** Busca propiedades disponibles
- **Mascotas:** Filtra propiedades que aceptan mascotas
- **Proyectos:** Muestra cantidad de proyectos activos
- **Captación:** Recuerda crear la ficha del inmueble

---

## 🎨 Diseño Inspirado en Bank Widget

### **Similitudes con el Widget Bancario**

| Característica | Bank Widget | Bohio CRM Quick Create |
|---------------|-------------|------------------------|
| **Badges de Estado** | `To check`, `Matched` | `Nueva`, `Seguimiento`, `Negociación`, `Propuesta`, `Ganada` |
| **Separador Condicional** | Botón "Statement" si falta extracto | Botón "Crear Ficha" si es captación |
| **Colores Dinámicos** | Rojo para montos negativos | Gradientes según probabilidad |
| **Quick Create** | Vista rápida con campos esenciales | Vista adaptativa según servicio |
| **JS Class Personalizada** | `bank_rec_widget_kanban` | `bohio_crm_quick_create_form` |

### **Paleta de Colores**

```scss
$bohio-red: #ff1d25;     // Color principal
$bohio-black: #000000;   // Color secundario

// Gradientes
$gradient-blue: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
$gradient-green: linear-gradient(135deg, #50c878 0%, #3fa463 100%);
$gradient-yellow: linear-gradient(135deg, #f39c12 0%, #d68910 100%);
$gradient-red: linear-gradient(135deg, #ff1d25 0%, #cc0000 100%);
```

---

## 🔧 Uso

### **1. Desde la Vista Kanban**

```xml
<kanban quick_create_view="bohio_crm.view_crm_lead_quick_create_form_bohio">
    <!-- Habilita el botón "+" en cada columna -->
</kanban>
```

### **2. Desde el Menú**

```python
# views/bohio_crm_actions.xml
<menuitem id="menu_crm_quick_create"
          name="Nueva Oportunidad Rápida"
          action="action_crm_lead_quick_create_bohio"
          sequence="5"/>
```

### **3. Desde JavaScript**

```javascript
this.action.doAction({
    type: 'ir.actions.act_window',
    name: 'Nueva Oportunidad',
    res_model: 'crm.lead',
    view_mode: 'form',
    views: [[false, 'bohio_crm_quick_create_form']],
    target: 'new',
});
```

---

## 📊 Método Python: `get_smart_suggestions()`

```python
@api.model
def get_smart_suggestions(self):
    """
    Obtener sugerencias basadas en estadísticas del usuario
    """
    return {
        'most_used_services': [
            {'value': 'sale', 'count': 15},
            {'value': 'rent', 'count': 10},
        ],
        'most_used_client_types': [...],
        'most_used_sources': [...],
        'frequent_projects': [...],
        'suggested_tags': [...],
    }
```

---

## 🎓 Validaciones Condicionales

### **Reglas Automáticas**

1. **Si `has_pets` = True**
   - Mostrar campo `pet_type`
   - Agregar tag "Con Mascotas"
   - Filtrar propiedades que aceptan mascotas

2. **Si `requires_parking` = True**
   - Mostrar campo `parking_spots`
   - Valor por defecto: 1

3. **Si `service_interested` = 'consign'**
   - Mostrar separador amarillo con botón
   - Validar que tenga `desired_city` y `desired_property_type_id`

---

## 📱 Responsive

- **Desktop:** Vista completa con todos los grupos
- **Mobile:**
  - Badges centrados
  - Selectores de servicio en 100% width
  - Grupos compactos

---

## 🚀 Instalación

1. **Actualizar el módulo:**
   ```bash
   odoo-bin -u bohio_crm -d tu_base_datos
   ```

2. **Verificar assets:**
   - CSS: `bohio_crm/static/src/css/crm_quick_create_smart.css`
   - JS: `bohio_crm/static/src/js/crm_quick_create_smart.js`
   - XML: `bohio_crm/views/crm_lead_quick_create_form.xml`

3. **Limpiar caché del navegador:**
   ```bash
   Ctrl + Shift + R
   ```

---

## 🐛 Troubleshooting

### **Campos no se muestran/ocultan**

Verificar que el atributo `invisible` esté correctamente escrito:
```xml
<!-- CORRECTO -->
<group invisible="service_interested != 'sale'">

<!-- INCORRECTO -->
<group invisible="service_interested == 'rent'">  <!-- Esto solo oculta en rent -->
```

### **Sugerencias no funcionan**

1. Verificar que el método `get_smart_suggestions()` esté en `crm_models.py`
2. Comprobar logs del navegador (F12 → Console)
3. Verificar permisos del usuario actual

### **Botón "Crear Ficha" no aparece**

Verificar:
```xml
<div invisible="service_interested != 'consign'" name="consign_action_section">
```

---

## 📚 Recursos

- **Odoo 18 Bank Reconciliation:** Inspiración para el diseño
- **OWL Framework:** Para componentes JavaScript
- **QWeb:** Para templates XML

---

## 🎉 Resultado Final

Una vista de creación rápida que:
- ✅ Adapta campos según el contexto
- ✅ Aprende de tus hábitos
- ✅ Acelera la captura de leads
- ✅ Mantiene consistencia de datos
- ✅ Facilita la captación de inmuebles
- ✅ Mejora la experiencia del usuario

---

**Creado por:** Bohio Inmobiliaria
**Versión:** 18.0.1.0.0
**Fecha:** 2025

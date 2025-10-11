# 🎯 CONDICIONES DE LA VISTA QUICK CREATE

## 📋 Tabla Completa de Condiciones

### **1. BADGES DE ESTADO (Header)**

| Badge | Condición `invisible` | Cuándo se Muestra |
|-------|----------------------|-------------------|
| 🆕 **Nueva Oportunidad** | `stage_id` | Cuando NO tiene etapa asignada |
| ⚠️ **Seguimiento Requerido** | `not stage_id or stage_id.probability >= 20` | Probabilidad < 20% |
| 🤝 **En Negociación** | `not stage_id or stage_id.probability < 20 or >= 70` | Probabilidad entre 20-69% |
| 📊 **Propuesta Enviada** | `not stage_id or stage_id.probability < 70 or is_won` | Probabilidad 70-99% |
| ✅ **Ganada** | `not stage_id or not stage_id.is_won` | `is_won = True` |
| 📝 **Captación** | `service_interested != 'consign'` | Servicio = Consignación |

---

### **2. CAMPOS DE CLASIFICACIÓN (Sección 1)**

| Campo | `required` | `invisible` | `readonly` |
|-------|-----------|------------|-----------|
| **service_interested** | ✅ `1` | ❌ | ❌ |
| **client_type** | ✅ `not in ['legal','marketing','corporate']` | ❌ | ❌ |
| **request_source** | ✅ `1` | ❌ | ❌ |
| **user_id** | ✅ `1` | ❌ | ❌ |

---

### **3. SEPARADOR CONDICIONAL: BOTÓN "CREAR FICHA"**

```xml
invisible="service_interested != 'consign'"
```

**Se muestra solo cuando:** `service_interested = 'consign'`

**Acción:** `action_create_property_from_lead()`

---

### **4. INFORMACIÓN DEL CLIENTE (Sección 2)**

| Campo | `required` | Condición |
|-------|-----------|-----------|
| **partner_id** | ✅ `type == 'opportunity'` | Si es oportunidad (no lead) |
| **email_from** | ✅ `not partner_id` | Si NO tiene contacto vinculado |
| **phone** | ✅ `not partner_id` | Si NO tiene contacto vinculado |
| **referred_by_partner_id** | ❌ | Opcional |

---

### **5. SECCIÓN VENTA (Sección 3)**

**Visible cuando:** `service_interested in ['sale', 'projects']`

| Campo | `required` | `invisible` |
|-------|-----------|------------|
| **budget_min** | ✅ `in ['sale', 'projects']` | ❌ |
| **budget_max** | ❌ | ❌ |
| **desired_property_type_id** | ✅ `== 'sale'` | ❌ |
| **property_purpose** | ❌ | ❌ |
| **desired_city** | ✅ `== 'sale'` | ❌ |
| **desired_neighborhood** | ❌ | ❌ |
| **num_bedrooms_min** | ❌ | ❌ |

---

### **6. SECCIÓN ARRIENDO (Sección 4)**

**Visible cuando:** `service_interested == 'rent'`

| Campo | `required` | `invisible` | Trigger |
|-------|-----------|------------|---------|
| **budget_min** | ✅ `== 'rent'` | ❌ | - |
| **budget_max** | ❌ | ❌ | - |
| **monthly_income** | ✅ `== 'rent'` | ❌ | - |
| **number_of_occupants** | ❌ | ❌ | - |
| **has_pets** | ❌ | ❌ | ⚡ Muestra `pet_type` |
| **pet_type** | ✅ `has_pets` | ✅ `not has_pets` | - |
| **requires_parking** | ❌ | ❌ | ⚡ Muestra `parking_spots` |
| **parking_spots** | ✅ `requires_parking` | ✅ `not requires_parking` | - |

**Lógica Condicional:**
```python
if has_pets:
    pet_type.visible = True
    pet_type.required = True

if requires_parking:
    parking_spots.visible = True
    parking_spots.required = True
```

---

### **7. SECCIÓN PROYECTOS (Sección 5)**

**Visible cuando:** `service_interested == 'projects'`

| Campo | `required` | `domain` |
|-------|-----------|----------|
| **project_id** | ✅ `== 'projects'` | `[('is_enabled', '=', True)]` |
| **property_purpose** | ✅ `== 'projects'` | - |

---

### **8. SECCIÓN CONSIGNACIÓN (Sección 6)**

**Visible cuando:** `service_interested == 'consign'`

| Campo | `required` | Descripción |
|-------|-----------|-------------|
| **desired_city** | ✅ `== 'consign'` | Ciudad del inmueble |
| **desired_neighborhood** | ✅ `== 'consign'` | Barrio |
| **desired_property_type_id** | ✅ `== 'consign'` | Tipo de inmueble |
| **expected_revenue** | ✅ `== 'consign'` | Valor estimado |
| **property_area_min** | ❌ | Área (m²) |
| **num_bedrooms_min** | ❌ | Habitaciones |

---

### **9. SECCIÓN SERVICIOS (Sección 7)**

**Visible cuando:** `service_interested in ['legal', 'marketing', 'corporate', 'valuation']`

| Campo | `required` |
|-------|-----------|
| **expected_revenue** | ✅ `in ['legal','marketing','corporate','valuation']` |
| **description** | ✅ `in ['legal','marketing','corporate','valuation']` |

---

### **10. CARACTERÍSTICAS DESEADAS (Sección 8)**

**Visible cuando:** `service_interested in ['sale', 'rent']`

| Campo | `required` |
|-------|-----------|
| **num_bedrooms_min** | ❌ |
| **num_bedrooms_max** | ❌ |
| **num_bathrooms_min** | ❌ |
| **property_area_min** | ❌ |
| **property_area_max** | ❌ |

---

### **11. AMENIDADES (Sección 9)**

**Visible cuando:** `service_interested in ['sale', 'rent']`

| Campo | Widget | Descripción |
|-------|--------|-------------|
| **requires_gym** | `boolean_toggle` | Gimnasio |
| **requires_pool** | `boolean_toggle` | Piscina |
| **requires_elevator** | `boolean_toggle` | Ascensor |
| **requires_security** | `boolean_toggle` | Seguridad 24/7 |
| **requires_common_areas** | `boolean_toggle` | Zonas comunes |

---

### **12. PROPIEDADES DE INTERÉS (Sección 10)**

**Visible cuando:** `service_interested NOT IN ['consign', 'legal', 'marketing', 'corporate', 'valuation']`

**Domain Dinámico:**
```python
domain = [
    ('is_property', '=', True),
    ('state', '=', 'free'),
    ('type_service', '=', service_interested if service_interested in ['sale', 'rent'] else False)
]
```

---

### **13. INFORMACIÓN FINANCIERA (Sección 11)**

| Campo | `required` | `readonly` | `invisible` |
|-------|-----------|------------|------------|
| **expected_revenue** | ✅ `in ['legal','marketing','corporate','valuation']` | ✅ `in ['sale','rent','projects','consign']` | ✅ `in ['legal','marketing','corporate','valuation']` |
| **probability** | ❌ | ❌ | ❌ |
| **date_deadline** | ❌ | ❌ | ❌ |
| **estimated_commission** | ❌ | ✅ `1` (calculado) | ❌ |

**Lógica:**
- **Venta/Arriendo/Proyectos/Consignación:** `expected_revenue` es READONLY (se calcula desde propiedades)
- **Servicios:** `expected_revenue` es REQUIRED y editable

---

### **14. NOTAS ADICIONALES (Sección 12)**

**Visible cuando:** `service_interested NOT IN ['legal', 'marketing', 'corporate', 'valuation']`

| Campo | `required` |
|-------|-----------|
| **description** | ❌ (excepto en servicios) |

---

### **15. ETIQUETAS (Sección 13)**

| Campo | `required` | Opciones |
|-------|-----------|----------|
| **tag_ids** | ❌ | `{'color_field': 'color', 'no_create_edit': True}` |

---

## 🔄 **FLUJO CONDICIONAL COMPLETO**

### **Escenario 1: VENTA**
```
1. Seleccionar service_interested = 'sale'
2. Se muestra sección "Preferencias de Compra"
3. Campos REQUERIDOS:
   - budget_min ✅
   - desired_property_type_id ✅
   - desired_city ✅
4. Se muestra sección "Características Deseadas"
5. Se muestra sección "Amenidades"
6. Se muestra "Propiedades de Interés" (filtradas por type_service='sale')
```

### **Escenario 2: ARRIENDO**
```
1. Seleccionar service_interested = 'rent'
2. Se muestra sección "Información de Arriendo"
3. Campos REQUERIDOS:
   - budget_min ✅
   - monthly_income ✅
4. Si marca has_pets = True:
   → pet_type se hace visible y REQUERIDO
5. Si marca requires_parking = True:
   → parking_spots se hace visible y REQUERIDO
6. Se muestra "Características" y "Amenidades"
7. Propiedades filtradas por type_service='rent'
```

### **Escenario 3: CONSIGNACIÓN**
```
1. Seleccionar service_interested = 'consign'
2. Se muestra SEPARADOR con botón "Crear Ficha de Inmueble"
3. Se muestra sección "Información del Inmueble a Consignar"
4. Campos REQUERIDOS:
   - desired_city ✅
   - desired_neighborhood ✅
   - desired_property_type_id ✅
   - expected_revenue ✅
5. Al hacer clic en "Crear Ficha":
   → Ejecuta action_create_property_from_lead()
   → Crea product.template
   → Vincula automáticamente
```

### **Escenario 4: PROYECTOS**
```
1. Seleccionar service_interested = 'projects'
2. Se muestra sección "Información de Proyecto"
3. Campos REQUERIDOS:
   - budget_min ✅
   - project_id ✅ (domain: is_enabled=True)
   - property_purpose ✅
4. Se muestra "Preferencias de Compra" (comparte con venta)
```

### **Escenario 5: SERVICIOS**
```
1. Seleccionar service_interested in ['legal', 'marketing', 'corporate', 'valuation']
2. Se muestra SOLO sección "Detalles del Servicio"
3. Campos REQUERIDOS:
   - expected_revenue ✅ (editable)
   - description ✅
4. client_type NO es requerido
5. NO se muestran: características, amenidades, propiedades
```

---

## 🎨 **WIDGETS CONDICIONALES**

| Widget | Campos | Comportamiento |
|--------|--------|---------------|
| **badge** | `client_type`, `request_source` | Colorea según valor con `decoration-*` |
| **many2one_avatar_user** | `user_id` | Muestra foto del usuario |
| **monetary** | Todos los campos de dinero | Usa `company_currency` |
| **progressbar** | `probability` | Barra visual de 0-100% |
| **many2many_tags** | `property_ids`, `tag_ids` | Tags con colores |
| **boolean_toggle** | Amenidades | Switch on/off |
| **email** | `email_from` | Validación de email |
| **phone** | `phone` | Formato de teléfono |
| **radio** | `service_interested`, `pet_type` | Botones radio |

---

## 🔍 **VALIDACIONES AUTOMÁTICAS**

### **1. Cliente vs Email/Phone**
```python
if partner_id:
    email_from.required = False
    phone.required = False
else:
    email_from.required = True
    phone.required = True
```

### **2. Mascotas**
```python
if has_pets == True:
    pet_type.visible = True
    pet_type.required = True
```

### **3. Parqueadero**
```python
if requires_parking == True:
    parking_spots.visible = True
    parking_spots.required = True
```

### **4. Expected Revenue**
```python
if service_interested in ['sale', 'rent', 'projects', 'consign']:
    expected_revenue.readonly = True  # Calculado desde propiedades
elif service_interested in ['legal', 'marketing', 'corporate', 'valuation']:
    expected_revenue.required = True
    expected_revenue.readonly = False
```

---

## 📊 **RESUMEN RÁPIDO**

| Servicio | Secciones Visibles | Campos Requeridos |
|----------|-------------------|-------------------|
| **Venta** | Preferencias, Características, Amenidades, Propiedades | budget_min, desired_property_type_id, desired_city |
| **Arriendo** | Arriendo, Características, Amenidades, Propiedades | budget_min, monthly_income, pet_type (si has_pets), parking_spots (si requires_parking) |
| **Proyectos** | Proyecto, Preferencias, Propiedades | budget_min, project_id, property_purpose |
| **Consignación** | Inmueble a Consignar | desired_city, desired_neighborhood, desired_property_type_id, expected_revenue |
| **Servicios** | Detalles del Servicio | expected_revenue, description |

---

## ✅ **VENTAJAS DE ESTA ESTRUCTURA**

1. ✅ **Formulario Dinámico:** Solo muestra campos relevantes
2. ✅ **Validación Inteligente:** Campos requeridos según contexto
3. ✅ **Menos Errores:** No se pueden llenar campos incorrectos
4. ✅ **Experiencia Guiada:** El usuario sabe qué llenar
5. ✅ **Datos Consistentes:** Domain filters aseguran coherencia
6. ✅ **Separador de Acción:** Botón especial para captación
7. ✅ **Badges Visuales:** Estado visible de un vistazo

---

**Inspirado en:** Odoo 18 Bank Reconciliation Widget
**Creado por:** Bohio Inmobiliaria
**Versión:** 18.0.1.0.0

# 📖 GUÍA COMPLETA: Property Dynamic Snippet

## 🎯 VISIÓN GENERAL

Este snippet personalizado extiende el sistema de snippets dinámicos de Odoo 18 para soportar propiedades inmobiliarias con filtros avanzados y múltiples plantillas de diseño.

---

## 📂 ESTRUCTURA DE ARCHIVOS

```
theme_bohio_real_estate/
├── models/
│   ├── __init__.py
│   └── website_snippet_filter.py          # Lógica Python del snippet
├── views/
│   └── snippets/
│       ├── property_snippet_templates.xml  # 4 plantillas de diseño
│       └── s_dynamic_snippet_properties.xml # Definición y opciones
├── static/src/
│   ├── css/
│   │   └── property_snippets.css          # Estilos del snippet
│   └── snippets/s_dynamic_snippet_properties/
│       ├── 000.js                          # Lógica frontend
│       └── options.js                      # Opciones del editor
```

---

## 🎨 4 PLANTILLAS DISPONIBLES

### 1️⃣ **Property Card** (Tarjeta Estándar)
**ID:** `dynamic_filter_template_property_card`

**Características:**
- Imagen + Badge de tipo servicio
- Ubicación (región, ciudad)
- Tipo de propiedad
- Características (hab, baños, garajes, área)
- Precio + botón "Ver Más"

**Uso ideal:** Listado general de propiedades

**Preview:**
```xml
<t t-call="theme_bohio_real_estate.dynamic_filter_template_property_card"/>
```

---

### 2️⃣ **Property Banner** (Banner Grande)
**ID:** `dynamic_filter_template_property_banner`

**Características:**
- Layout horizontal (imagen + contenido)
- Descripción corta
- Iconos grandes de características
- Solo 1 elemento por slide
- Ideal para destacar

**Uso ideal:** Hero section, propiedad destacada

**Preview:**
```xml
<t t-call="theme_bohio_real_estate.dynamic_filter_template_property_banner"/>
```

---

### 3️⃣ **Property Compact** (Compacta)
**ID:** `dynamic_filter_template_property_compact`

**Características:**
- Solo imagen + precio overlay
- 4 elementos por defecto
- Minimalista
- Badge de tipo servicio

**Uso ideal:** Galerías, secciones compactas

**Preview:**
```xml
<t t-call="theme_bohio_real_estate.dynamic_filter_template_property_compact"/>
```

---

### 4️⃣ **Property List** (Lista Horizontal)
**ID:** `dynamic_filter_template_property_list`

**Características:**
- Layout horizontal
- 2 filas por slide
- Imagen pequeña + info
- Características compactas

**Uso ideal:** Listados tipo tabla, comparación

**Preview:**
```xml
<t t-call="theme_bohio_real_estate.dynamic_filter_template_property_list"/>
```

---

## ⚙️ FILTROS DISPONIBLES

### **Tipo de Servicio** (`typeService`)
```python
'all'        # Todas las propiedades
'rent'       # En arriendo
'sale'       # En venta
'sale_used'  # Venta usadas (sin proyecto)
'projects'   # Proyectos nuevos (con proyecto)
```

### **Tipo de Propiedad** (`propertyType`)
```python
'all', 'apartment', 'house', 'office', 'warehouse',
'land', 'commercial_premises', 'building', 'farm',
'cabin', 'hotel', 'parking', 'room', 'other'
```

### **Ubicación**
```python
cityId      # ID de res.city
regionId    # ID de property.region
```

### **Rangos de Precio**
```python
priceMin    # Precio mínimo en pesos
priceMax    # Precio máximo en pesos
```

### **Características Mínimas**
```python
minBedrooms   # Habitaciones mínimas
minBathrooms  # Baños mínimos
minArea       # Área mínima en m²
```

---

## 🚀 CÓMO USAR

### **Opción 1: Website Builder (Arrastrar y Soltar)**

1. **Abrir el editor de website:**
   ```
   Website → Editar
   ```

2. **Arrastrar snippet "Properties":**
   - Ir a pestaña "Content Blocks"
   - Buscar "Properties"
   - Arrastrar a la página

3. **Configurar opciones:**
   - Click en el snippet
   - Panel derecho → Opciones
   - Seleccionar filtros:
     - Tipo de Servicio
     - Tipo de Propiedad
     - Ciudad/Barrio
     - Rangos de precio
     - Características

4. **Elegir plantilla:**
   - En opciones → Template
   - Elegir entre 4 diseños

---

### **Opción 2: Código Directo en Template**

```xml
<template id="mi_pagina_custom">
    <t t-call="website.layout">
        <div id="wrap">
            <!-- Propiedades en Arriendo -->
            <section class="py-5">
                <div class="container">
                    <h2>Propiedades en Arriendo</h2>
                    <div class="s_dynamic_snippet_properties"
                         data-filter-id="my_filter_rent"
                         data-type-service="rent"
                         data-template-key="theme_bohio_real_estate.dynamic_filter_template_property_card"
                         data-limit="12">
                        <!-- Se carga dinámicamente -->
                    </div>
                </div>
            </section>

            <!-- Propiedades en Venta -->
            <section class="py-5 bg-light">
                <div class="container">
                    <h2>Propiedades en Venta</h2>
                    <div class="s_dynamic_snippet_properties"
                         data-filter-id="my_filter_sale"
                         data-type-service="sale_used"
                         data-template-key="theme_bohio_real_estate.dynamic_filter_template_property_card"
                         data-limit="12">
                        <!-- Se carga dinámicamente -->
                    </div>
                </div>
            </section>

            <!-- Proyectos -->
            <section class="py-5">
                <div class="container">
                    <h2>Proyectos Nuevos</h2>
                    <div class="s_dynamic_snippet_properties"
                         data-filter-id="my_filter_projects"
                         data-type-service="projects"
                         data-template-key="theme_bohio_real_estate.dynamic_filter_template_property_banner"
                         data-limit="6">
                        <!-- Se carga dinámicamente -->
                    </div>
                </div>
            </section>
        </div>
    </t>
</template>
```

---

### **Opción 3: Crear Filtro Personalizado**

```xml
<record id="dynamic_filter_properties_featured" model="website.snippet.filter">
    <field name="name">Propiedades Destacadas</field>
    <field name="model_id" ref="product.model_product_template"/>
    <field name="limit">8</field>
    <field name="filter_domain">[
        ('is_property', '=', True),
        ('active', '=', True),
        ('state', '=', 'free')
    ]</field>
</record>
```

Luego úsalo:
```xml
<div class="s_dynamic_snippet_properties"
     data-filter-id="dynamic_filter_properties_featured"
     data-template-key="theme_bohio_real_estate.dynamic_filter_template_property_card">
</div>
```

---

## 🔧 MÉTODOS PYTHON DISPONIBLES

### **En website_snippet_filter.py:**

```python
# Obtener propiedades por modo
_get_properties(mode, **kwargs)

# Modos disponibles:
_get_properties_rent()           # En arriendo
_get_properties_sale_used()      # Usadas en venta
_get_properties_projects()       # Proyectos
_get_properties_featured()       # Destacadas
_get_properties_latest()         # Últimas agregadas
_get_properties_by_type()        # Por tipo
_get_properties_by_city()        # Por ciudad
_get_properties_by_region()      # Por región
```

---

## 🎨 PERSONALIZAR PLANTILLA

### **Crear nueva plantilla:**

```xml
<template id="mi_plantilla_custom" name="Mi Plantilla">
    <t t-foreach="records" t-as="data">
        <t t-set="record" t-value="data['_record']"/>
        <div class="mi-clase-custom">
            <!-- Tu diseño aquí -->
            <h3 t-field="record.name"/>
            <p t-esc="data.get('city_name')"/>
            <span t-esc="data.get('list_price_formatted')"
                  t-options="{'widget': 'monetary', 'display_currency': record.currency_id}"/>
        </div>
    </t>
</template>
```

### **Campos disponibles en `data`:**

```python
{
    '_record': record_object,        # Objeto completo
    'image_512': url,                # Imagen 512x512
    'property_type_label': str,      # "Apartamento", "Casa", etc.
    'type_service_label': str,       # "Arriendo", "Venta"
    'has_project': bool,             # Tiene proyecto
    'project_name': str,             # Nombre del proyecto
    'city_name': str,                # Ciudad
    'region_name': str,              # Barrio/Región
    'state_name': str,               # Departamento
    'bedrooms': int,                 # Habitaciones
    'bathrooms': int,                # Baños
    'garages': int,                  # Garajes
    'area': float,                   # Área m²
    'list_price_formatted': float,   # Precio
    'currency_name': str,            # Moneda
}
```

---

## 🔗 INTEGRACIÓN CON CARRUSELES EXISTENTES

### **Reemplazar carruseles actuales:**

**ANTES** (property_carousels_snippet.xml):
```xml
<div id="carousel-rent" class="property-carousel-loading">
    <div class="spinner-border"></div>
</div>
```

**AHORA** (con snippet dinámico):
```xml
<div class="s_dynamic_snippet_properties"
     data-type-service="rent"
     data-template-key="theme_bohio_real_estate.dynamic_filter_template_property_card"
     data-limit="12">
</div>
```

**VENTAJAS:**
✅ Editable desde Website Builder
✅ Sin JavaScript personalizado
✅ Cacheable
✅ Más rápido

---

## 📊 EJEMPLOS DE USO

### **Ejemplo 1: Homepage con 3 Secciones**

```xml
<template id="homepage_bohio">
    <!-- Arriendo -->
    <section class="py-5">
        <div class="container">
            <h2>Propiedades en Arriendo</h2>
            <div class="s_dynamic_snippet_properties"
                 data-type-service="rent"
                 data-limit="8">
            </div>
        </div>
    </section>

    <!-- Venta Usadas -->
    <section class="py-5 bg-light">
        <div class="container">
            <h2>Venta de Inmuebles</h2>
            <div class="s_dynamic_snippet_properties"
                 data-type-service="sale_used"
                 data-limit="8">
            </div>
        </div>
    </section>

    <!-- Proyectos -->
    <section class="py-5">
        <div class="container">
            <h2>Proyectos Nuevos</h2>
            <div class="s_dynamic_snippet_properties"
                 data-type-service="projects"
                 data-template-key="theme_bohio_real_estate.dynamic_filter_template_property_banner"
                 data-limit="3">
            </div>
        </div>
    </section>
</template>
```

---

### **Ejemplo 2: Página de Ciudad**

```xml
<template id="city_page">
    <t t-set="city_id" t-value="12"/>  <!-- ID de Medellín -->

    <div class="container py-5">
        <h1>Propiedades en Medellín</h1>

        <div class="s_dynamic_snippet_properties"
             t-att-data-city-id="city_id"
             data-limit="20">
        </div>
    </div>
</template>
```

---

### **Ejemplo 3: Filtros Combinados**

```xml
<div class="s_dynamic_snippet_properties"
     data-type-service="rent"
     data-property-type="apartment"
     data-city-id="12"
     data-price-min="500000"
     data-price-max="2000000"
     data-min-bedrooms="2"
     data-limit="12">
</div>
```

Esto mostrará:
- ✅ Apartamentos
- ✅ En arriendo
- ✅ En Medellín
- ✅ Entre $500,000 - $2,000,000
- ✅ Mínimo 2 habitaciones

---

## 🐛 TROUBLESHOOTING

### **No aparece el snippet en el editor**

1. Verificar que el módulo esté actualizado:
   ```bash
   odoo-bin -u theme_bohio_real_estate -d bohio_db
   ```

2. Verificar que los archivos XML estén en `__manifest__.py`

3. Limpiar cache del navegador

---

### **Las propiedades no se cargan**

1. Verificar en consola del navegador errores JavaScript

2. Verificar que existan propiedades:
   ```python
   # En shell de Odoo
   env['product.template'].search([
       ('is_property', '=', True),
       ('state', '=', 'free')
   ])
   ```

3. Verificar permisos del usuario

---

### **Los filtros no funcionan**

1. Verificar `data-` attributes en HTML

2. Verificar en `options.js` que los filtros estén registrados

3. Ver errores en consola del navegador

---

## 📚 REFERENCIA RÁPIDA

### **Atributos data- disponibles:**

```html
data-filter-id=""           <!-- ID del filtro -->
data-template-key=""        <!-- Template a usar -->
data-limit=""               <!-- Límite de resultados -->
data-type-service=""        <!-- rent/sale/sale_used/projects -->
data-property-type=""       <!-- apartment/house/office/etc -->
data-city-id=""            <!-- ID de ciudad -->
data-region-id=""          <!-- ID de región -->
data-price-min=""          <!-- Precio mínimo -->
data-price-max=""          <!-- Precio máximo -->
data-min-bedrooms=""       <!-- Habitaciones mínimas -->
data-min-bathrooms=""      <!-- Baños mínimos -->
data-min-area=""           <!-- Área mínima -->
```

---

## 🎓 PRÓXIMOS PASOS

1. **Crear filtros predefinidos** para diferentes páginas
2. **Agregar más plantillas** de diseño
3. **Integrar con búsqueda avanzada**
4. **Agregar animaciones** de transición
5. **Implementar lazy loading** de imágenes

---

## 📞 SOPORTE

Para más información, ver:
- [Documentación Odoo Snippets](https://www.odoo.com/documentation/18.0/developer/reference/frontend/snippets.html)
- Código fuente: `theme_bohio_real_estate/`
- Ejemplos: Ver archivos en `views/snippets/`

---

**Última actualización:** 2025-10-12
**Versión:** 1.0
**Autor:** BOHIO Real Estate Development Team

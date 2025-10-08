# Sistema de Búsqueda de Propiedades con Comparación
## Documentación Técnica Completa

---

## 📋 TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Sistema de Contextos](#sistema-de-contextos)
4. [Autocompletado Inteligente](#autocompletado-inteligente)
5. [Sistema de Comparación](#sistema-de-comparación)
6. [Guía de Implementación](#guía-de-implementación)
7. [API Reference](#api-reference)
8. [Ejemplos de Uso](#ejemplos-de-uso)
9. [Troubleshooting](#troubleshooting)

---

## 1. RESUMEN EJECUTIVO

### ¿Qué es este sistema?

Un controlador avanzado para Odoo 18.0 que proporciona:

✅ **Búsqueda contextual** de propiedades inmobiliarias
✅ **Autocompletado inteligente** con subdivisión por tipo
✅ **Sistema de comparación** de hasta 4 propiedades simultáneas
✅ **Modal dinámico** que muestra diferencias entre propiedades
✅ **Filtros avanzados** por ubicación, precio, características
✅ **Soporte multi-contexto** para diferentes casos de uso

### Casos de Uso Principales

1. **Búsqueda pública**: Clientes finales buscando propiedades disponibles
2. **Portal administrativo**: Agentes inmobiliarios gestionando propiedades
3. **Búsqueda por proyecto**: Visualización de propiedades de un proyecto específico
4. **Búsqueda rápida**: Widget embebido para otras vistas

---

## 2. ARQUITECTURA DEL SISTEMA

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────┐
│                   FRONTEND (Templates + JS)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Templates   │  │  JavaScript  │  │     CSS      │     │
│  │   (QWeb)     │  │   Widget     │  │   Estilos    │     │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘     │
│         │                  │                                │
└─────────┼──────────────────┼────────────────────────────────┘
          │                  │
          │                  │ JSON-RPC
          │                  │
┌─────────┼──────────────────┼────────────────────────────────┐
│         │                  │         BACKEND                │
│  ┌──────▼──────────────────▼───────┐                        │
│  │  PropertySearchController       │                        │
│  │  ┌───────────────────────────┐  │                        │
│  │  │  Contextos Configurables  │  │                        │
│  │  │  - public / admin / etc.  │  │                        │
│  │  └───────────────────────────┘  │                        │
│  │                                  │                        │
│  │  ┌───────────────────────────┐  │                        │
│  │  │  Autocompletado con       │  │                        │
│  │  │  Subdivisión              │  │                        │
│  │  └───────────────────────────┘  │                        │
│  │                                  │                        │
│  │  ┌───────────────────────────┐  │                        │
│  │  │  Sistema de Comparación   │  │                        │
│  │  │  - Sesión                 │  │                        │
│  │  │  - Detección Diferencias  │  │                        │
│  │  └───────────────────────────┘  │                        │
│  └──────────────────────────────────┘                        │
└───────────────────────────────────────────────────────────────┘
```

### Archivos del Sistema

```
real_estate_bits/
├── controllers/
│   └── property_search_controller.py  [Controlador principal]
├── static/
│   ├── src/
│   │   ├── js/
│   │   │   └── property_search.js     [Widget JavaScript]
│   │   └── css/
│   │       └── property_search.css     [Estilos]
├── views/
│   └── property_search_templates.xml   [Templates QWeb]
└── __manifest__.py
```

---

## 3. SISTEMA DE CONTEXTOS

### ¿Qué son los Contextos?

Los contextos permiten configurar el comportamiento de la búsqueda según el caso de uso.

### Contextos Predefinidos

#### 1. `public` (Búsqueda Pública)

```python
'public': {
    'name': 'Búsqueda Pública',
    'allowed_states': ['free'],  # Solo propiedades disponibles
    'show_price': True,
    'show_contact': True,
    'allow_comparison': True,
}
```

**Uso típico**: Portal web para clientes

#### 2. `admin` (Búsqueda Administrativa)

```python
'admin': {
    'name': 'Búsqueda Administrativa',
    'allowed_states': ['free', 'reserved', 'sold', 'on_lease'],
    'show_price': True,
    'show_contact': True,
    'allow_comparison': True,
}
```

**Uso típico**: Backend para agentes inmobiliarios

#### 3. `project` (Búsqueda por Proyecto)

```python
'project': {
    'name': 'Búsqueda por Proyecto',
    'allowed_states': ['free'],
    'filter_by_project': True,
    'show_price': True,
    'show_contact': False,
    'allow_comparison': True,
}
```

**Uso típico**: Páginas de proyectos específicos

#### 4. `quick` (Búsqueda Rápida)

```python
'quick': {
    'name': 'Búsqueda Rápida',
    'allowed_states': ['free'],
    'show_price': False,
    'show_contact': False,
    'allow_comparison': False,
    'max_results': 10,
}
```

**Uso típico**: Widgets embebidos en otras páginas

### Cómo Usar Contextos

#### En URLs

```python
# Búsqueda pública (contexto por defecto)
/property/search

# Búsqueda con contexto explícito
/property/search/admin
/property/search/project
/property/search/quick
```

#### En Código Python

```python
# Llamar a la búsqueda con contexto
self.property_search(context='admin', property_type='apartment')
```

#### En Templates

```xml
<a t-att-href="'/property/search/admin'">
    Búsqueda Administrativa
</a>
```

### Crear Contextos Personalizados

```python
# En property_search_controller.py

SEARCH_CONTEXTS = {
    # ... contextos existentes ...
    
    'my_custom_context': {
        'name': 'Mi Contexto Personalizado',
        'allowed_states': ['free', 'reserved'],
        'show_price': True,
        'show_contact': True,
        'allow_comparison': True,
        'filter_by_project': True,
        'max_results': 50,
        # Agregar propiedades personalizadas
        'custom_filter': 'my_value',
    }
}
```

---

## 4. AUTOCOMPLETADO INTELIGENTE

### Características

- **Búsqueda en tiempo real** con debounce de 300ms
- **Subdivisión por tipo**: ciudades, barrios, proyectos, propiedades
- **Priorización inteligente**: resultados más relevantes primero
- **Conteo de propiedades**: muestra cuántas propiedades hay en cada resultado

### Subdivisiones Disponibles

#### 1. `all` (Búsqueda Total)

Busca en todos los tipos simultáneamente:
- Ciudades
- Barrios/Regiones
- Proyectos
- Propiedades individuales

#### 2. `cities` (Solo Ciudades)

```javascript
{
    subdivision: 'cities',
    results: [
        {
            type: 'city',
            name: 'Bogotá',
            property_count: 145
        }
    ]
}
```

#### 3. `regions` (Solo Barrios)

```javascript
{
    subdivision: 'regions',
    results: [
        {
            type: 'region',
            name: 'Chapinero',
            property_count: 23
        }
    ]
}
```

#### 4. `projects` (Solo Proyectos)

```javascript
{
    subdivision: 'projects',
    results: [
        {
            type: 'project',
            name: 'Torres del Parque',
            property_count: 12
        }
    ]
}
```

#### 5. `properties` (Solo Propiedades)

```javascript
{
    subdivision: 'properties',
    results: [
        {
            type: 'property',
            name: 'APT-001 - Apartamento en Chapinero',
            property_count: 1
        }
    ]
}
```

### API de Autocompletado

#### Endpoint

```
POST /property/search/autocomplete/<context>
```

#### Parámetros

```javascript
{
    term: 'chapinero',      // Término de búsqueda
    context: 'public',      // Contexto de búsqueda
    subdivision: 'all',     // Tipo de subdivisión
    limit: 10               // Número máximo de resultados
}
```

#### Respuesta

```javascript
{
    results: [
        {
            id: 'region_15',
            type: 'region',
            name: 'Chapinero',
            full_name: 'Chapinero, Bogotá, Cundinamarca',
            label: '<i class="fa fa-home"></i> Chapinero <small>(Bogotá)</small>',
            property_count: 23,
            priority: 2,
            region_id: 15,
            city_id: 5
        }
    ],
    subdivision: 'all',
    total: 1
}
```

### Integración en Templates

```xml
<div class="input-group">
    <input type="text" 
           class="form-control property-search-input" 
           placeholder="Buscar..."/>
    
    <select class="form-control subdivision-filter">
        <option value="all">Buscar todo</option>
        <option value="cities">Solo ciudades</option>
        <option value="regions">Solo barrios</option>
        <option value="projects">Solo proyectos</option>
        <option value="properties">Solo propiedades</option>
    </select>
</div>

<div class="autocomplete-container" style="display: none;"/>
```

---

## 5. SISTEMA DE COMPARACIÓN

### Flujo de Comparación

```
1. Usuario agrega propiedades (máx. 4)
   ↓
2. Propiedades se guardan en sesión
   ↓
3. Usuario hace clic en "Comparar"
   ↓
4. Sistema obtiene datos completos
   ↓
5. Se detectan diferencias automáticamente
   ↓
6. Modal muestra tabla comparativa
```

### Métodos del Sistema

#### 1. Agregar a Comparación

```javascript
// Endpoint
POST /property/comparison/add

// Parámetros
{
    property_id: 123,
    context: 'public'
}

// Respuesta
{
    success: true,
    total: 2,
    property_ids: [123, 456]
}
```

#### 2. Eliminar de Comparación

```javascript
// Endpoint
POST /property/comparison/remove

// Parámetros
{
    property_id: 123
}

// Respuesta
{
    success: true,
    total: 1,
    property_ids: [456]
}
```

#### 3. Limpiar Comparación

```javascript
// Endpoint
POST /property/comparison/clear

// Respuesta
{
    success: true,
    total: 0
}
```

#### 4. Obtener Datos de Comparación

```javascript
// Endpoint
POST /property/comparison/get

// Parámetros
{
    context: 'public'
}

// Respuesta
{
    properties: [...],      // Datos de propiedades
    fields: [...],          // Campos a comparar
    differences: [...],     // Diferencias detectadas
    total: 3
}
```

### Campos de Comparación

El sistema compara automáticamente:

**Campos comunes**:
- Precio
- Área (m²)
- Habitaciones
- Baños
- Estrato
- Estado

**Campos específicos por tipo**:

Para **Apartamentos** y **Oficinas**:
- Piso
- Ascensor

Para **Casas** y **Lotes**:
- Jardín
- Frente (metros)

**Campos adicionales**:
- Garaje
- Piscina
- Parqueadero cubierto

### Detección de Diferencias

El sistema detecta automáticamente campos con valores diferentes:

```javascript
differences: [
    {
        field: 'num_bedrooms',
        label: 'Habitaciones',
        values: [3, 2, 3],  // Valores diferentes
        type: 'integer'
    },
    {
        field: 'elevator',
        label: 'Ascensor',
        values: ['Sí', 'No', 'Sí'],
        type: 'boolean'
    }
]
```

### Modal de Comparación

El modal muestra:

1. **Tabla comparativa** con todas las características
2. **Resaltado de diferencias** en color amarillo
3. **Resumen de diferencias** al final
4. **Botones de acción**:
   - Quitar propiedad individual
   - Limpiar comparación completa
   - Imprimir comparación
   - Cerrar modal

---

## 6. GUÍA DE IMPLEMENTACIÓN

### Paso 1: Instalar el Módulo

```bash
# 1. Copiar archivos al módulo
cp property_search_controller.py /path/to/odoo/addons/real_estate_bits/controllers/
cp property_search.js /path/to/odoo/addons/real_estate_bits/static/src/js/
cp property_search.css /path/to/odoo/addons/real_estate_bits/static/src/css/
cp property_search_templates.xml /path/to/odoo/addons/real_estate_bits/views/

# 2. Actualizar __manifest__.py
# Agregar los archivos en las secciones correspondientes

# 3. Actualizar módulo en Odoo
odoo-bin -u real_estate_bits -d your_database
```

### Paso 2: Configurar el __manifest__.py

```python
{
    'name': 'Real Estate Bits',
    # ... otras configuraciones ...
    
    'data': [
        # ... otros archivos ...
        'views/property_search_templates.xml',
    ],
    
    'assets': {
        'web.assets_frontend': [
            'real_estate_bits/static/src/js/property_search.js',
            'real_estate_bits/static/src/css/property_search.css',
        ],
    },
    
    'depends': [
        'website',
        'website_sale',
        'product',
    ],
}
```

### Paso 3: Agregar __init__.py en Controllers

```python
# controllers/__init__.py
from . import property_search_controller
```

### Paso 4: Configurar Permisos

```xml
<!-- security/ir.model.access.csv -->
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_product_template_public,product.template.public,product.model_product_template,base.group_public,1,0,0,0
```

### Paso 5: Agregar al Menú del Website

```xml
<record id="menu_property_search" model="website.menu">
    <field name="name">Buscar Propiedades</field>
    <field name="url">/property/search</field>
    <field name="parent_id" ref="website.main_menu"/>
    <field name="sequence">50</field>
</record>
```

---

## 7. API REFERENCE

### Rutas HTTP

#### Búsqueda Principal

```
GET /property/search/<context>?<params>

Parámetros:
- context: 'public', 'admin', 'project', 'quick' (default: 'public')
- search: término de búsqueda
- property_type: tipo de propiedad
- city_id: ID de ciudad
- state_id: ID de departamento
- region_id: ID de barrio
- project_id: ID de proyecto
- min_price, max_price: rango de precio
- min_area, max_area: rango de área
- bedrooms, bathrooms: número mínimo
- garage, garden, pool, elevator: filtros booleanos
- order: ordenamiento ('relevance', 'price_asc', 'price_desc', etc.)
- page: número de página
- ppg: propiedades por página
```

#### Propiedad Individual

```
GET /property/get/<property_id>/<context>

Parámetros:
- property_id: ID de la propiedad
- context: contexto de visualización
```

### Rutas JSON-RPC

#### Autocompletado

```python
@http.route(['/property/search/autocomplete/<context>'], type='json')
def property_search_autocomplete(term, context, subdivision, limit):
    """
    Búsqueda con autocompletado
    
    Returns:
        {
            'results': [...],
            'subdivision': 'all',
            'total': 10
        }
    """
```

#### Sistema de Comparación

```python
@http.route(['/property/comparison/add'], type='json')
def add_to_comparison(property_id, context):
    """Agrega propiedad a comparación"""

@http.route(['/property/comparison/remove'], type='json')
def remove_from_comparison(property_id):
    """Elimina propiedad de comparación"""

@http.route(['/property/comparison/clear'], type='json')
def clear_comparison():
    """Limpia todas las propiedades"""

@http.route(['/property/comparison/get'], type='json')
def get_comparison_data(context):
    """Obtiene datos para el modal"""
```

---

## 8. EJEMPLOS DE USO

### Ejemplo 1: Widget Simple en Otra Página

```xml
<template id="my_custom_page">
    <div class="container">
        <h2>Propiedades Destacadas</h2>
        
        <!-- Widget de búsqueda rápida -->
        <iframe src="/property/search/quick?property_type=apartment&amp;max_results=6" 
                style="width:100%; height:600px; border:none;"/>
    </div>
</template>
```

### Ejemplo 2: Búsqueda Embebida con JavaScript

```javascript
// En tu JavaScript personalizado
$(document).ready(function() {
    // Cargar resultados de búsqueda vía AJAX
    $.ajax({
        url: '/property/search/quick',
        data: {
            property_type: 'house',
            city_id: 5,
            max_results: 10
        },
        success: function(html) {
            $('#property-results').html(html);
        }
    });
});
```

### Ejemplo 3: Comparación Programática

```javascript
// Agregar propiedades a comparación desde código
async function addPropertiesToCompare(propertyIds) {
    for (let id of propertyIds) {
        await jsonrpc('/property/comparison/add', {
            property_id: id,
            context: 'public'
        });
    }
    
    // Mostrar modal
    const data = await jsonrpc('/property/comparison/get', {
        context: 'public'
    });
    
    renderComparisonModal(data);
}

// Uso
addPropertiesToCompare([123, 456, 789]);
```

### Ejemplo 4: Contexto Personalizado en Acción

```python
# En un controlador personalizado
class MyCustomController(http.Controller):
    
    @http.route(['/my/properties'], type='http', auth='user', website=True)
    def my_properties(self, **kwargs):
        # Llamar al controlador de búsqueda con contexto personalizado
        return request.env['PropertySearchController'].property_search(
            context='admin',
            search_term='',
            **kwargs
        )
```

---

## 9. TROUBLESHOOTING

### Problema: Autocompletado no funciona

**Solución**:
1. Verificar que el JavaScript esté cargado:
```javascript
console.log(typeof PropertySearchWidget);  // Debe ser 'function'
```

2. Revisar errores en consola del navegador

3. Verificar que la ruta JSON-RPC esté accesible:
```bash
curl -X POST http://localhost:8069/property/search/autocomplete/public \
    -H "Content-Type: application/json" \
    -d '{"term": "test", "subdivision": "all"}'
```

### Problema: Comparación no guarda en sesión

**Solución**:
1. Verificar que las sesiones estén habilitadas
2. Verificar localStorage en el navegador:
```javascript
localStorage.getItem('property_comparison');
```

3. Limpiar localStorage si hay datos corruptos:
```javascript
localStorage.removeItem('property_comparison');
```

### Problema: Modal no muestra diferencias

**Solución**:
1. Verificar que haya al menos 2 propiedades
2. Revisar la consola para errores de renderizado
3. Verificar que los campos de comparación estén definidos:
```python
def _get_comparison_fields(self, properties):
    # Debe retornar lista de campos
    return [{'name': 'field', 'label': 'Label', 'type': 'type'}]
```

### Problema: Contexto no aplica filtros

**Solución**:
1. Verificar que el contexto esté en `SEARCH_CONTEXTS`
2. Revisar el dominio generado:
```python
_logger.info("Domain: %s", domain)
```

3. Verificar estados permitidos:
```python
allowed_states = search_context.get('allowed_states', ['free'])
```

---

## 📞 SOPORTE Y CONTACTO

Para preguntas o problemas:
- Revisar la documentación en `/docs`
- Consultar logs de Odoo: `/var/log/odoo/odoo.log`
- Habilitar modo debug en Odoo para más detalles

---

## 🔄 ACTUALIZACIONES Y MEJORAS FUTURAS

### En Desarrollo
- [ ] Cache de resultados de búsqueda
- [ ] Búsqueda por voz
- [ ] Mapas interactivos
- [ ] Comparación con gráficos
- [ ] Export a PDF de comparaciones
- [ ] Historial de búsquedas del usuario
- [ ] Sugerencias basadas en IA

### Solicitado por Usuarios
- [ ] Filtro por rango de distancia
- [ ] Búsqueda por características premium
- [ ] Integración con WhatsApp
- [ ] Tours virtuales 360°

---

**Versión**: 1.0.0  
**Última actualización**: Octubre 2025  
**Compatible con**: Odoo 18.0  
**Licencia**: LGPL-3

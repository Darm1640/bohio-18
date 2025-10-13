# Sistema de Autocompletado Inteligente - BOHIO Real Estate

## 📋 Resumen

Sistema de autocompletado en tiempo real para la barra de búsqueda del homepage, con normalización sin acentos, resultados agrupados y navegación por teclado.

## ✅ Características Implementadas

### 1. **Búsqueda Inteligente**
- ✅ Normalización sin acentos (buscar "bogota" encuentra "Bogotá")
- ✅ Debounce de 300ms para evitar sobrecarga
- ✅ Mínimo 2 caracteres para activar
- ✅ Búsqueda en múltiples categorías simultáneamente

### 2. **Resultados Agrupados**
- **Ciudades** 🗺️ - Con contador de propiedades disponibles
- **Barrios/Regiones** 🏠 - Filtrado por ciudad si está seleccionada
- **Proyectos** 🏢 - Solo en modo público/proyecto
- **Propiedades** 🔑 - Por código, nombre o barcode

### 3. **Navegación por Teclado**
- `↑` - Seleccionar resultado anterior
- `↓` - Seleccionar resultado siguiente
- `Enter` - Confirmar selección
- `Escape` - Cerrar resultados

### 4. **Interacción Visual**
- Hover effect en items
- Resaltado de términos buscados en **rojo**
- Badges con contadores de propiedades
- Animación fade-in al mostrar
- Loading spinner durante búsqueda

## 📁 Archivos Creados

### 1. `homepage_autocomplete.js` (420 líneas)
```javascript
/** @odoo-module **/
import { jsonrpc } from "@web/core/network/rpc_service";

class BohioAutocomplete {
    constructor(inputElement, options = {}) {
        // Configuración
        this.options = {
            minChars: 2,
            debounceMs: 300,
            maxResults: 10,
            context: 'public',
            subdivision: 'all',
            onSelect: null,
            ...options
        };
        // ...
    }
}
```

**Métodos principales**:
- `init()` - Inicialización de eventos y contenedor
- `search(term)` - Llamada RPC al servidor
- `renderResults(results, term)` - Renderizado agrupado
- `selectResult(result)` - Redirección según tipo
- `handleKeydown(e)` - Navegación con teclado

### 2. `homepage_autocomplete.css` (140 líneas)
Estilos para:
- Contenedor de resultados con scrollbar personalizado
- Grupos con títulos sticky
- Items con hover y estados
- Animaciones y responsive

## 🔌 API Endpoint

### `/property/search/autocomplete` (JSON-RPC)

**Parámetros**:
```javascript
{
    term: 'bogo',              // Término de búsqueda (min 2 chars)
    context: 'public',         // Contexto: 'public', 'admin', 'project', 'quick'
    subdivision: 'all',        // 'all', 'cities', 'regions', 'projects', 'properties'
    limit: 10                  // Máximo de resultados
}
```

**Respuesta**:
```json
{
    "success": true,
    "results": [
        {
            "id": "city_1",
            "type": "city",
            "name": "Bogotá",
            "full_name": "Bogotá, Cundinamarca",
            "label": "<i class='bi bi-geo-alt-fill'></i> <b>Bogotá</b>, Cundinamarca",
            "property_count": 45,
            "priority": 3,
            "city_id": 1,
            "state_id": 25
        },
        {
            "id": "region_15",
            "type": "region",
            "name": "Chapinero",
            "full_name": "Chapinero, Bogotá",
            "label": "<i class='bi bi-house-fill'></i> Chapinero <small>(Bogotá)</small>",
            "property_count": 12,
            "priority": 2,
            "region_id": 15,
            "city_id": 1
        }
    ],
    "subdivision": "all",
    "total": 2,
    "term": "bogo"
}
```

## 🎯 Integración con Homepage

### Antes (Select estático)
```html
<select name="search" class="form-select">
    <option value="">¿Dónde quieres vivir?</option>
    <option value="Bogotá">Bogotá</option>
    <option value="Medellín">Medellín</option>
    <!-- ... -->
</select>
```

### Después (Input con autocompletado)
```html
<input type="text"
       name="search_autocomplete"
       class="form-control"
       placeholder="¿Dónde quieres vivir?">
```

El JavaScript automáticamente:
1. Detecta el `<select name="search">`
2. Lo reemplaza por un `<input>`
3. Inicializa el autocompletado con callback personalizado
4. Al seleccionar, redirige a `/properties?city_id=X` o similar

## 🔧 Controlador Backend

### `property_search.py` - Métodos Clave

#### `_autocomplete_cities(term, context, limit)`
```python
def _autocomplete_cities(self, term, search_context, limit):
    """Autocompletado de ciudades con normalización"""
    normalized_term = self._normalize_search_term(term)

    cities = request.env['res.city'].sudo().search([
        '|',
        ('name', 'ilike', term),
        ('name', 'ilike', normalized_term),
        ('country_id', '=', request.env.company.country_id.id)
    ], limit=limit * 2)

    results = []
    for city in cities:
        domain = [
            ('is_property', '=', True),
            ('city_id', '=', city.id),
            ('state', 'in', search_context.get('allowed_states', ['free']))
        ]
        property_count = request.env['product.template'].sudo().search_count(domain)

        if property_count > 0:
            results.append({
                'id': f'city_{city.id}',
                'type': 'city',
                'name': city.name,
                'full_name': f'{city.name}, {city.state_id.name}',
                'property_count': property_count,
                'priority': 3,
                'city_id': city.id,
                'state_id': city.state_id.id,
            })

    return results
```

#### `_normalize_search_term(term)`
```python
def _normalize_search_term(self, term):
    """Normaliza término quitando acentos"""
    import unicodedata
    normalized = ''.join(
        c for c in unicodedata.normalize('NFD', term)
        if unicodedata.category(c) != 'Mn'
    )
    return normalized.lower().strip()
```

Similar para:
- `_autocomplete_regions()` - Barrios/Regiones
- `_autocomplete_projects()` - Proyectos inmobiliarios
- `_autocomplete_properties()` - Propiedades por código

## 🎨 Estilos Principales

### Contenedor de resultados
```css
.bohio-autocomplete-results {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    max-height: 400px;
    overflow-y: auto;
    z-index: 1050;
}
```

### Items con hover
```css
.autocomplete-item:hover {
    background-color: #f8f9fa;
}

.autocomplete-item.selected {
    background-color: #fff3f3;
    border-left: 3px solid #E31E24;
}
```

### Términos resaltados
```css
.item-name strong {
    color: #E31E24;
    font-weight: 600;
}
```

## 🚀 Flujo de Funcionamiento

### 1. Usuario escribe en el input
```
Usuario: "bog"
↓
Debounce 300ms
↓
if (term.length >= 2) → API Call
```

### 2. Llamada al servidor
```javascript
await jsonrpc('/property/search/autocomplete', {
    term: 'bog',
    context: 'public',
    subdivision: 'all',
    limit: 10
});
```

### 3. Backend procesa
```python
# Normalización
'bog' → ['bog', 'bog']  # Ya sin acento
'Bogotá' → match con 'ilike'

# Búsqueda en modelos
- res.city: Bogotá (45 props)
- region.region: Bosa (8 props)
- project.worksite: Bogotá Plaza (3 props)

# Contar propiedades libres por cada resultado
```

### 4. Frontend renderiza
```html
<div class="autocomplete-group">
    <div class="group-title">Ciudades</div>
    <div class="autocomplete-item" data-index="0">
        <div class="item-name">
            <strong>Bog</strong>otá
        </div>
        <small>Bogotá, Cundinamarca</small>
        <span class="badge">45</span>
    </div>
</div>
```

### 5. Usuario selecciona (click o Enter)
```javascript
selectResult(result) {
    if (result.type === 'city') {
        window.location.href = `/properties?city_id=${result.city_id}`;
    } else if (result.type === 'property') {
        window.location.href = `/property/${result.property_id}`;
    }
}
```

## 📊 Prioridades de Resultados

El sistema ordena resultados por:
1. **Priority** (descendente)
   - Cities: 3
   - Regions/Projects: 2
   - Properties: 1

2. **Property Count** (descendente)
   - Más propiedades disponibles = mayor relevancia

Ejemplo de orden:
```
1. Bogotá (Ciudad, 45 props)      - priority:3, count:45
2. Medellín (Ciudad, 32 props)    - priority:3, count:32
3. Chapinero (Barrio, 12 props)   - priority:2, count:12
4. BOH-2024-001 (Propiedad, 1)    - priority:1, count:1
```

## 🔍 Casos de Uso

### Búsqueda por ciudad
```
Usuario: "medellin" → Encuentra "Medellín"
Click → /properties?city_id=2
```

### Búsqueda por barrio
```
Usuario: "chapinero" → Encuentra "Chapinero, Bogotá"
Click → /properties?region_id=15
```

### Búsqueda por código
```
Usuario: "BOH-2024" → Encuentra "BOH-2024-001 - Apartamento..."
Click → /property/123
```

### Búsqueda con acento omitido
```
Usuario: "bogota" (sin tilde)
Backend normaliza: "Bogotá" → "bogota"
Match: ✅ Encuentra resultados
```

## 🐛 Debugging

### Verificar carga
```javascript
console.log(typeof BohioAutocomplete);  // "function"
console.log(typeof window.BohioAutocomplete);  // "function"
```

### Ver requests en Network
```
POST /property/search/autocomplete
Payload: {"term":"bog","context":"public",...}
Response: {"success":true,"results":[...],...}
```

### Logs en consola
```javascript
// En homepage_autocomplete.js
console.log('BOHIO Autocomplete inicializado en:', this.input.placeholder);
console.log('Resultados recibidos:', result.results.length);
```

## 🎯 Próximas Mejoras Sugeridas

### 1. **Historial de búsquedas**
```javascript
localStorage.setItem('bohio_search_history', JSON.stringify(searches));
// Mostrar últimas 3 búsquedas al hacer focus sin escribir
```

### 2. **Búsquedas populares**
```python
# En property_search.py
@http.route('/property/search/popular', type='json')
def get_popular_searches(self):
    # Obtener ciudades con más propiedades
    # Obtener barrios trending
    # Retornar top 5
```

### 3. **Thumbnails en resultados de propiedades**
```html
<div class="autocomplete-item">
    <img src="/web/image/product.template/123/image_128">
    <div>BOH-2024-001 - Apartamento...</div>
</div>
```

### 4. **Filtros contextuales**
```javascript
// Si el usuario ya seleccionó "Arrendar", buscar solo en arriendos
const serviceType = document.getElementById('selectedServiceType').value;
await jsonrpc('/property/search/autocomplete', {
    term: term,
    filters: { type_service: serviceType }
});
```

## 📚 Referencias

- [Odoo 18 JSON-RPC](https://www.odoo.com/documentation/18.0/developer/reference/frontend/javascript_reference.html#rpc)
- [Debounce Pattern](https://davidwalsh.name/javascript-debounce-function)
- [Keyboard Navigation](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/)

---

**Fecha de Implementación**: 2025-01-10
**Versión de Odoo**: 18.0
**Desarrollador**: Claude Code Assistant

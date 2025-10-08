# 🏠 Sistema Avanzado de Búsqueda de Propiedades para Odoo 18.0

Sistema completo de búsqueda, filtrado y comparación de propiedades inmobiliarias con soporte multi-contexto, autocompletado inteligente y comparación visual de hasta 4 propiedades.

[![Odoo Version](https://img.shields.io/badge/Odoo-18.0-blue.svg)](https://www.odoo.com/)
[![License](https://img.shields.io/badge/License-LGPL--3-green.svg)](https://www.gnu.org/licenses/lgpl-3.0.html)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)](https://www.python.org/)

---

## ✨ Características Principales

### 🔍 Búsqueda Contextual Inteligente
- **4 contextos predefinidos**: Public, Admin, Project, Quick
- **Filtros dinámicos** por ubicación, precio, área, características
- **Búsqueda jerárquica**: Ciudad → Departamento → Barrio → Proyecto
- **Resultados en tiempo real** con paginación

### 🎯 Autocompletado con Subdivisión
- **5 tipos de búsqueda**: Todo, Ciudades, Barrios, Proyectos, Propiedades
- **Priorización inteligente** de resultados
- **Contador de propiedades** por cada resultado
- **Debounce optimizado** para reducir llamadas al servidor

### ⚖️ Sistema de Comparación Avanzado
- **Comparar hasta 4 propiedades** simultáneamente
- **Detección automática de diferencias**
- **Modal interactivo** con tabla comparativa
- **Persistencia en sesión** y localStorage
- **Opción de impresión** de comparaciones

### 🎨 UI/UX Optimizada
- **Diseño responsive** para móviles y tablets
- **Animaciones fluidas** y transiciones suaves
- **Notificaciones en tiempo real**
- **Tarjetas de propiedad** con hover effects
- **Badges visuales** para estados y tipos

---

## 📦 Instalación Rápida

### Prerrequisitos

```bash
Odoo 18.0
Python 3.10+
PostgreSQL 12+
```

### Paso 1: Copiar Archivos

```bash
# Clonar o descargar los archivos
cd /path/to/odoo/addons/real_estate_bits/

# Estructura de carpetas
mkdir -p controllers static/src/js static/src/css views
```

### Paso 2: Ubicar Archivos

```
real_estate_bits/
├── controllers/
│   ├── __init__.py
│   └── property_search_controller.py
├── static/src/
│   ├── js/
│   │   └── property_search.js
│   └── css/
│       └── property_search.css
└── views/
    └── property_search_templates.xml
```

### Paso 3: Actualizar __manifest__.py

```python
{
    'name': 'Real Estate Bits',
    'version': '18.0.1.0.0',
    'category': 'Real Estate',
    'depends': ['website', 'website_sale', 'product'],
    
    'data': [
        'views/property_search_templates.xml',
    ],
    
    'assets': {
        'web.assets_frontend': [
            'real_estate_bits/static/src/js/property_search.js',
            'real_estate_bits/static/src/css/property_search.css',
        ],
    },
    
    'installable': True,
    'application': True,
    'auto_install': False,
}
```

### Paso 4: Actualizar Odoo

```bash
# Reiniciar Odoo con actualización
odoo-bin -u real_estate_bits -d your_database --dev all

# O desde la interfaz web:
# Apps → Real Estate Bits → Upgrade
```

---

## 🚀 Uso Rápido

### Búsqueda Pública (Contexto por Defecto)

```
URL: http://your-domain.com/property/search
```

**Características**:
- Solo muestra propiedades disponibles (estado: `free`)
- Precio visible
- Contacto visible
- Comparación habilitada

### Búsqueda Administrativa

```
URL: http://your-domain.com/property/search/admin
```

**Características**:
- Muestra todas las propiedades (todos los estados)
- Ideal para agentes inmobiliarios
- Todas las funcionalidades activas

### Widget de Búsqueda Rápida

```xml
<!-- Embeber en cualquier página -->
<iframe src="/property/search/quick?property_type=apartment" 
        style="width:100%; height:600px; border:none;">
</iframe>
```

---

## 📖 Ejemplos de Uso

### Ejemplo 1: Búsqueda con Filtros

```python
# Búsqueda de apartamentos en Bogotá con 3+ habitaciones
/property/search/public?property_type=apartment&city_id=5&bedrooms=3
```

### Ejemplo 2: Autocompletado en JavaScript

```javascript
import { jsonrpc } from "@web/core/network/rpc_service";

// Buscar ciudades que contengan "bogo"
const results = await jsonrpc('/property/search/autocomplete/public', {
    term: 'bogo',
    subdivision: 'cities',
    limit: 10
});

console.log(results.results);
// [{type: 'city', name: 'Bogotá', property_count: 145, ...}]
```

### Ejemplo 3: Agregar a Comparación

```javascript
// Agregar propiedad ID 123 a comparación
await jsonrpc('/property/comparison/add', {
    property_id: 123,
    context: 'public'
});

// Obtener datos de comparación
const data = await jsonrpc('/property/comparison/get', {
    context: 'public'
});

console.log(`Comparando ${data.total} propiedades`);
```

### Ejemplo 4: Contexto Personalizado

```python
# En property_search_controller.py, agregar:

SEARCH_CONTEXTS = {
    # ... contextos existentes ...
    
    'vip': {
        'name': 'Búsqueda VIP',
        'allowed_states': ['free'],
        'show_price': True,
        'show_contact': True,
        'allow_comparison': True,
        'min_price': 500000000,  # Filtro automático
    }
}

# Usar: /property/search/vip
```

---

## 🎯 Características Avanzadas

### Sistema de Contextos

Los contextos permiten adaptar la búsqueda a diferentes casos de uso:

| Contexto | Estados Permitidos | Mostrar Precio | Comparación | Uso Típico |
|----------|-------------------|----------------|-------------|------------|
| `public` | `free` | ✅ | ✅ | Portal web |
| `admin` | Todos | ✅ | ✅ | BackOffice |
| `project` | `free` | ✅ | ✅ | Páginas de proyectos |
| `quick` | `free` | ❌ | ❌ | Widgets |

### Subdivisión de Autocompletado

| Subdivisión | Busca en | Ejemplo |
|-------------|----------|---------|
| `all` | Todo | Ciudades, barrios, proyectos, propiedades |
| `cities` | Solo ciudades | Bogotá, Medellín, Cali |
| `regions` | Solo barrios | Chapinero, Poblado, Granada |
| `projects` | Solo proyectos | Torres del Parque |
| `properties` | Solo propiedades | APT-001, Casa en... |

### Comparación de Propiedades

**Flujo de trabajo**:

1. Usuario navega propiedades
2. Click en "Comparar" en cada tarjeta (máx. 4)
3. Click en botón "Ver Comparación"
4. Modal muestra tabla comparativa
5. Diferencias resaltadas en amarillo
6. Opciones: Quitar, Limpiar, Imprimir

---

## 🔧 Configuración Avanzada

### Personalizar Campos de Comparación

```python
# En property_search_controller.py

def _get_comparison_fields(self, properties):
    # Campos base
    fields = [
        {'name': 'net_price', 'label': _('Precio'), 'type': 'monetary'},
        {'name': 'property_area', 'label': _('Área'), 'type': 'float', 'unit': 'm²'},
        # ... más campos ...
    ]
    
    # Agregar campos personalizados
    if any(p.property_type == 'apartment' for p in properties):
        fields.append({
            'name': 'balcony_area',
            'label': _('Área Balcón'),
            'type': 'float',
            'unit': 'm²'
        })
    
    return fields
```

### Agregar Filtros Personalizados

```python
# En el método property_search()

# Filtro personalizado: Solo propiedades con piscina olímpica
if post.get('olympic_pool'):
    domain.append(('pool_length', '>=', 25))
```

### Personalizar Rangos de Precio

```python
def _get_price_ranges_by_type(self, property_type, type_service):
    # Rangos personalizados por tipo
    if property_type == 'luxury':
        return [
            {'min': 1000000000, 'max': 2000000000, 'label': '$1,000M - $2,000M'},
            {'min': 2000000000, 'max': 5000000000, 'label': '$2,000M - $5,000M'},
            {'min': 5000000000, 'max': 0, 'label': 'Más de $5,000M'},
        ]
    
    return super()._get_price_ranges_by_type(property_type, type_service)
```

---

## 📊 Rendimiento y Optimización

### Cache de Resultados (Recomendado)

```python
from werkzeug.contrib.cache import SimpleCache
cache = SimpleCache()

def property_search_autocomplete(self, term='', context='public', **kwargs):
    cache_key = f'autocomplete_{term}_{context}'
    results = cache.get(cache_key)
    
    if results is None:
        results = self._perform_autocomplete(term, context)
        cache.set(cache_key, results, timeout=300)  # 5 minutos
    
    return {'results': results}
```

### Índices de Base de Datos

```sql
-- Agregar índices para mejorar rendimiento
CREATE INDEX idx_property_search ON product_template(is_property, active, state);
CREATE INDEX idx_property_location ON product_template(city_id, state_id, region_id);
CREATE INDEX idx_property_type_service ON product_template(property_type, type_service);
```

### Lazy Loading de Imágenes

```xml
<!-- En la tarjeta de propiedad -->
<img t-att-data-src="'data:image/png;base64,' + prop.image_1920" 
     class="card-img-top lazyload" 
     loading="lazy"/>
```

---

## 🐛 Troubleshooting

### Problema: "Module not found"

```bash
# Verificar que el módulo esté en addons_path
grep addons_path /etc/odoo/odoo.conf

# Agregar si falta
addons_path = /path/to/odoo/addons,/path/to/real_estate_bits
```

### Problema: JavaScript no carga

```javascript
// En consola del navegador
console.log(odoo.__DEBUG__.services);  // Ver servicios disponibles

// Verificar que el archivo esté en assets
// Ir a: Configuración → Técnico → Vistas → Assets
```

### Problema: Sesión no guarda comparación

```python
# Verificar configuración de sesiones en odoo.conf
session_store = filesystem

# O usar Redis (recomendado)
session_store = redis
session_redis_host = localhost
session_redis_port = 6379
```

### Problema: Autocompletado lento

```python
# Agregar límite de caracteres mínimos
if len(term) < 3:  # Cambiar de 2 a 3
    return {'results': []}

# Reducir límite de resultados
limit = min(int(limit), 5)  # Máximo 5 resultados
```

---

## 📚 Documentación Completa

Para documentación detallada, ver:
- **[DOCUMENTATION.md](./DOCUMENTATION.md)** - Documentación técnica completa
- **[API Reference](./DOCUMENTATION.md#7-api-reference)** - Referencia de API
- **[Examples](./DOCUMENTATION.md#8-ejemplos-de-uso)** - Ejemplos prácticos

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📝 Changelog

### Version 1.0.0 (Octubre 2025)
- ✨ Sistema de contextos configurables
- ✨ Autocompletado con subdivisión
- ✨ Comparación de propiedades con modal
- ✨ Detección automática de diferencias
- ✨ Filtros avanzados dinámicos
- 🎨 UI responsive y animaciones
- 📱 Soporte móvil completo

---

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Documentación**: [Ver docs](./DOCUMENTATION.md)
- **Email**: support@example.com

---

## 📄 Licencia

Este proyecto está bajo la licencia LGPL-3. Ver el archivo `LICENSE` para más detalles.

---

## 🙏 Agradecimientos

- Equipo de Odoo por el framework
- Comunidad de desarrolladores
- Todos los contribuidores

---

**Hecho con ❤️ para la comunidad Odoo**

*Compatible con Odoo 18.0 | Última actualización: Octubre 2025*

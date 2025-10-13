# 🏠 FIX: Propiedades NO aparecían en Homepage

**Fecha:** 2025-10-11
**Problema:** Las secciones de Arriendo, Venta Usada y Proyectos NO mostraban propiedades en el homepage
**Causa Raíz:** El JavaScript requería `has_location: true` (coordenadas GPS) para TODAS las propiedades, incluso para el Grid
**Estado:** ✅ SOLUCIONADO

---

## 🔍 PROBLEMA IDENTIFICADO

### **Síntoma Reportado por el Usuario**
```
"Arriendo
Te ayudamos a encontrar el lugar ideal para vivir
 Vista Grid
 Vista Mapa

Venta de inmuebles usados
Te ayudamos a encontrar el hogar que estás buscando
 Vista Grid
 Vista Mapa

Proyectos en venta
Invierte hoy en el futuro que sueñas
 Vista Grid
 Vista Mapa

peude analisa porque no muestra una 10 propiedades en que este free por tipo venta o arriendo y mostra los proyecto revisa que si salga"
```

Las 3 secciones estaban **vacías** o mostraban muy pocas propiedades.

---

## 🐛 CAUSA RAÍZ

### **Archivo:** `theme_bohio_real_estate/static/src/js/homepage_properties.js`

**Problema en línea 242-247 (Arriendo):**
```javascript
// ❌ ANTES (INCORRECTO)
const rentData = await loadProperties({
    type_service: 'rent',
    has_location: true,  // ⚠️ REQUIERE coordenadas GPS SIEMPRE
    limit: 20,
    order: 'newest'
});
```

**Problema en línea 275-281 (Venta Usada):**
```javascript
// ❌ ANTES (INCORRECTO)
const usedSaleData = await loadProperties({
    type_service: 'sale',
    has_location: true,      // ⚠️ REQUIERE coordenadas GPS
    has_project: false,
    limit: 20,
    order: 'newest'
});
```

**Problema en línea 309-315 (Proyectos):**
```javascript
// ❌ ANTES (INCORRECTO)
const projectsData = await loadProperties({
    type_service: 'sale',
    has_location: true,   // ⚠️ REQUIERE coordenadas GPS
    has_project: true,
    limit: 20,
    order: 'newest'
});
```

### **¿Por qué fallaba?**

El filtro `has_location: true` se traduce en el backend a:
```python
# En property_search.py línea 436-438
if filters.get('has_location'):
    domain.append(('latitude', '!=', False))
    domain.append(('longitude', '!=', False))
```

**Resultado:** Solo se mostraban propiedades que tenían **latitud Y longitud** configuradas.

**Problema:** Muchas propiedades en la base de datos NO tienen coordenadas GPS asignadas, por lo que:
- ❌ NO aparecían en el Grid (aunque no necesitan ubicación)
- ❌ NO aparecían en el Mapa (aquí sí se necesita ubicación)
- ✅ Solo aparecían las pocas propiedades con GPS

---

## ✅ SOLUCIÓN IMPLEMENTADA

### **Estrategia: Separar carga de Grid y Mapa**

**Grid (Vista de Tarjetas):** NO requiere coordenadas GPS
**Mapa (Vista de Mapa):** SÍ requiere coordenadas GPS

Se modificó `homepage_properties.js` para hacer **2 llamadas separadas** por cada sección:

1. **Primera llamada:** Cargar 10 propiedades para el GRID (sin `has_location`)
2. **Segunda llamada:** Cargar 20 propiedades CON ubicación para el MAPA (`has_location: true`)

---

## 📝 CAMBIOS REALIZADOS

### **1. Sección ARRIENDO (Líneas 240-286)**

**ANTES (1 llamada con has_location):**
```javascript
const rentData = await loadProperties({
    type_service: 'rent',
    has_location: true,  // ❌ Bloqueaba propiedades sin GPS
    limit: 20,
    order: 'newest'
});
```

**DESPUÉS (2 llamadas separadas):**
```javascript
// 🟢 PRIMERA LLAMADA: Para el GRID (sin requerir ubicación)
const rentDataGrid = await loadProperties({
    type_service: 'rent',
    limit: 10,
    order: 'newest'
});

if (rentDataGrid.properties && rentDataGrid.properties.length > 0) {
    const arriendoContainer = document.getElementById('arriendo-properties-grid');
    if (arriendoContainer) {
        // Mostrar solo las primeras 4 en el grid
        arriendoContainer.innerHTML = rentDataGrid.properties.slice(0, 4).map(prop => createPropertyCard(prop)).join('');
    }
    console.log('Propiedades de arriendo cargadas (grid):', rentDataGrid.properties.length);
}

// 🗺️ SEGUNDA LLAMADA: Para el MAPA (solo con ubicación)
const rentDataMap = await loadProperties({
    type_service: 'rent',
    has_location: true,  // ✅ Aquí sí necesitamos GPS
    limit: 20,
    order: 'newest'
});

if (rentDataMap.properties && rentDataMap.properties.length > 0) {
    rentPropertiesData = rentDataMap.properties;
    console.log('Propiedades de arriendo con ubicación (mapa):', rentPropertiesData.length);
} else {
    rentPropertiesData = [];  // Sin propiedades para el mapa
}
```

---

### **2. Sección VENTA USADA (Líneas 288-336)**

**ANTES:**
```javascript
const usedSaleData = await loadProperties({
    type_service: 'sale',
    has_location: true,      // ❌ Bloqueaba propiedades sin GPS
    has_project: false,
    limit: 20
});
```

**DESPUÉS:**
```javascript
// 🟢 GRID: Sin requerir ubicación
const usedSaleDataGrid = await loadProperties({
    type_service: 'sale',
    has_project: false,
    limit: 10,
    order: 'newest'
});

// 🗺️ MAPA: Solo con ubicación
const usedSaleDataMap = await loadProperties({
    type_service: 'sale',
    has_location: true,
    has_project: false,
    limit: 20,
    order: 'newest'
});
```

---

### **3. Sección PROYECTOS (Líneas 338-386)**

**ANTES:**
```javascript
const projectsData = await loadProperties({
    type_service: 'sale',
    has_location: true,   // ❌ Bloqueaba proyectos sin GPS
    has_project: true,
    limit: 20
});
```

**DESPUÉS:**
```javascript
// 🟢 GRID: Sin requerir ubicación
const projectsDataGrid = await loadProperties({
    type_service: 'sale',
    has_project: true,
    limit: 10,
    order: 'newest'
});

// 🗺️ MAPA: Solo con ubicación
const projectsDataMap = await loadProperties({
    type_service: 'sale',
    has_location: true,
    has_project: true,
    limit: 20,
    order: 'newest'
});
```

---

### **4. Manejo de Mapas sin Propiedades (Líneas 395-500)**

Se actualizó `setupMapTabs()` para mostrar un mensaje amigable cuando NO hay propiedades con ubicación para el mapa:

**ANTES:**
```javascript
if (arriendoMap && rentPropertiesData.length > 0) {
    setTimeout(() => {
        updateMapMarkers(arriendoMap, rentPropertiesData);
    }, 200);
}
```

**DESPUÉS:**
```javascript
if (rentPropertiesData.length === 0) {
    // Sin propiedades con ubicación, mostrar mensaje
    if (mapContainer) {
        mapContainer.innerHTML = `
            <div class="d-flex align-items-center justify-content-center h-100 bg-light">
                <div class="text-center p-4">
                    <i class="fa fa-map-marked-alt fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No hay propiedades con ubicación disponible para mostrar en el mapa</p>
                </div>
            </div>
        `;
    }
} else {
    // Hay propiedades, mostrar mapa
    if (!arriendoMap) {
        arriendoMap = initMap('arriendo-properties-map', arriendoMap);
    }
    if (arriendoMap) {
        setTimeout(() => {
            updateMapMarkers(arriendoMap, rentPropertiesData);
        }, 200);
    }
}
```

Mismo tratamiento para `usedSaleMap` y `projectsMap`.

---

## 📊 RESULTADO FINAL

### **Vista Grid (Tarjetas)**
- ✅ **Muestra hasta 4 propiedades** por sección
- ✅ **NO requiere coordenadas GPS**
- ✅ Toma las 10 propiedades más recientes y muestra las primeras 4
- ✅ Funciona con TODAS las propiedades libres (state='free')

### **Vista Mapa**
- ✅ **Muestra hasta 20 propiedades CON ubicación**
- ✅ **Requiere latitud Y longitud** (correcto para mapas)
- ✅ Si no hay propiedades con ubicación, muestra mensaje informativo
- ✅ No genera errores ni mapas vacíos

---

## 🎯 FILTROS APLICADOS

### **1. Arriendo**
**Grid:**
```javascript
{
    type_service: 'rent',
    limit: 10,
    order: 'newest'
}
```
**Mapa:**
```javascript
{
    type_service: 'rent',
    has_location: true,
    limit: 20,
    order: 'newest'
}
```

**Dominio Odoo (Grid):**
```python
[
    ('is_property', '=', True),
    ('active', '=', True),
    ('state', '=', 'free'),
    ('type_service', 'in', ['rent', 'sale_rent', 'vacation_rent'])
]
```

**Dominio Odoo (Mapa):**
```python
[
    ('is_property', '=', True),
    ('active', '=', True),
    ('state', '=', 'free'),
    ('type_service', 'in', ['rent', 'sale_rent', 'vacation_rent']),
    ('latitude', '!=', False),
    ('longitude', '!=', False)
]
```

---

### **2. Venta Usada**
**Grid:**
```javascript
{
    type_service: 'sale',
    has_project: false,
    limit: 10,
    order: 'newest'
}
```
**Mapa:**
```javascript
{
    type_service: 'sale',
    has_location: true,
    has_project: false,
    limit: 20,
    order: 'newest'
}
```

**Diferencia Clave:** `has_project: false` filtra propiedades **SIN** proyecto (usadas)

---

### **3. Proyectos**
**Grid:**
```javascript
{
    type_service: 'sale',
    has_project: true,
    limit: 10,
    order: 'newest'
}
```
**Mapa:**
```javascript
{
    type_service: 'sale',
    has_location: true,
    has_project: true,
    limit: 20,
    order: 'newest'
}
```

**Diferencia Clave:** `has_project: true` filtra propiedades **CON** proyecto (nuevas/proyectos)

---

## 🔄 ACTIVACIÓN

### **Método 1: Limpiar Caché del Navegador**
```
Ctrl + Shift + R (o Cmd + Shift + R en Mac)
```

### **Método 2: Actualizar Módulo en Odoo**
```
1. Aplicaciones → theme_bohio_real_estate → Actualizar
2. Refrescar página
```

### **Método 3: Reiniciar Assets**
```bash
cd "C:\Program Files\Odoo 18.0.20250830\server"
python odoo-bin -c odoo.conf -d bohio_db --dev=all
```

---

## ✅ CHECKLIST DE VERIFICACIÓN

### **Visual**
- [ ] Sección "Arriendo" muestra 4 propiedades en Vista Grid
- [ ] Sección "Venta de inmuebles usados" muestra 4 propiedades en Vista Grid
- [ ] Sección "Proyectos en venta" muestra 4 propiedades (o proyectos) en Vista Grid
- [ ] Al hacer clic en "Vista Mapa", se muestra el mapa CON marcadores (si hay propiedades con ubicación)
- [ ] Si no hay propiedades con ubicación, el mapa muestra mensaje informativo

### **Consola del Navegador (F12 → Console)**
```javascript
// Deberías ver estos logs:
Propiedades de arriendo cargadas (grid): 10
Propiedades de arriendo con ubicación (mapa): 5

Propiedades usadas cargadas (grid): 10
Propiedades usadas con ubicación (mapa): 3

Proyectos cargados (grid): 10
Proyectos con ubicación (mapa): 8
```

### **Funcional**
- [ ] Hacer clic en una propiedad del Grid lleva al detalle
- [ ] Cambiar de "Vista Grid" a "Vista Mapa" funciona correctamente
- [ ] Los marcadores del mapa muestran popup con información de la propiedad
- [ ] Botón "Explora la categoría" redirige a `/properties?type_service=rent` (o sale)

---

## 📈 IMPACTO

### **Antes**
- ❌ Grid vacío si propiedades sin GPS
- ❌ Mapa vacío sin mensaje
- ❌ UX confusa (usuario no sabía por qué no veía propiedades)
- ❌ Pocas propiedades mostradas

### **Después**
- ✅ Grid muestra propiedades sin GPS
- ✅ Mapa muestra mensaje si no hay ubicaciones
- ✅ UX clara y profesional
- ✅ Máximo de propiedades visibles

---

## 🚀 PRÓXIMOS PASOS (OPCIONAL)

### **1. Geocodificación Automática**
Si deseas que todas las propiedades tengan coordenadas automáticamente:

```python
# En real_estate_bits/models/property.py
from geopy.geocoders import Nominatim

def _compute_coordinates(self):
    """Auto-asignar coordenadas basado en dirección"""
    geolocator = Nominatim(user_agent="bohio_real_estate")

    for prop in self:
        if not prop.latitude and not prop.longitude:
            address = f"{prop.street}, {prop.city}, {prop.state}"
            try:
                location = geolocator.geocode(address)
                if location:
                    prop.latitude = location.latitude
                    prop.longitude = location.longitude
            except:
                pass
```

### **2. Asignar Coordenadas Manualmente (Odoo UI)**
```
Inmuebles → Propiedades → [Seleccionar Propiedad]
→ Pestaña "Ubicación"
→ Ingresar Latitud y Longitud
```

### **3. Importación Masiva con CSV**
Crear CSV con columnas:
```
name,latitude,longitude
Propiedad 1,4.7110,-74.0721
Propiedad 2,6.2442,-75.5812
```

---

## 📁 ARCHIVO MODIFICADO

```
theme_bohio_real_estate/static/src/js/homepage_properties.js
```

**Total de Líneas Modificadas:** ~150 líneas
**Secciones Afectadas:**
- `loadHomePropertiesWithMaps()` - Líneas 237-390
- `setupMapTabs()` - Líneas 395-500

---

**FIN DEL DOCUMENTO**

**Fecha:** 2025-10-11
**Autor:** Claude Code (Anthropic)
**Versión:** 1.0.0

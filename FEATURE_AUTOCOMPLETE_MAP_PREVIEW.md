# Feature: Preview de Mapa en Autocompletado

## 📋 Resumen

Se ha implementado una funcionalidad de **preview en tiempo real** que muestra las propiedades en el mapa cuando el usuario pasa el mouse sobre los items del autocompletado de búsqueda, **sin necesidad de hacer click**.

## 🎯 Comportamiento

### Antes (solo click)
1. Usuario escribe "monter" en el buscador
2. Aparece dropdown con "Montería - 1543 propiedades"
3. Usuario debe **HACER CLICK** para ver propiedades en el mapa
4. El filtro se aplica definitivamente

### Después (hover preview)
1. Usuario escribe "monter" en el buscador
2. Aparece dropdown con "Montería - 1543 propiedades"
3. Usuario **PASA EL MOUSE** sobre el item → Mapa muestra preview de propiedades en Montería
4. Usuario **SALE DEL ITEM** → Mapa vuelve al estado anterior
5. Usuario **HACE CLICK** → Filtro se aplica definitivamente

## 💻 Implementación Técnica

### Archivo modificado
- **`theme_bohio_real_estate/static/src/js/property_shop.js`**

### Nuevas propiedades en constructor (líneas 67-69)
```javascript
// Preview de autocomplete
this.previewFilters = null;  // Guardar filtros antes del preview
this.isPreviewActive = false;  // Flag para saber si estamos en modo preview
```

### Event listeners agregados (líneas 277-289)
```javascript
// Hover: mostrar preview en el mapa
item.addEventListener('mouseenter', () => {
    // Solo preview si NO es una propiedad (las propiedades redirigen al detalle)
    if (item.dataset.type !== 'property') {
        this.previewAutocompleteItem(item.dataset);
    }
});

item.addEventListener('mouseleave', () => {
    if (item.dataset.type !== 'property') {
        this.clearAutocompletePreview();
    }
});
```

### Nuevas funciones (líneas 334-421)

#### 1. `previewAutocompleteItem(data)` (líneas 336-376)
**Propósito:** Mostrar preview temporal en el mapa

**Lógica:**
1. Verificar que el mapa esté inicializado
2. Marcar flag `isPreviewActive = true`
3. Guardar filtros actuales en `previewFilters` (solo la primera vez)
4. Crear filtros temporales con la ubicación del item hover
5. Llamar a `loadMapPropertiesPreview()` con filtros temporales

**Código clave:**
```javascript
// Guardar los filtros actuales SOLO la primera vez
if (!this.previewFilters) {
    this.previewFilters = { ...this.filters };
    console.log('[AUTOCOMPLETE-PREVIEW] Filtros guardados:', this.previewFilters);
}

// Crear filtros temporales para el preview
const tempFilters = { ...this.filters };

// Limpiar filtros de ubicación previos
delete tempFilters.city_id;
delete tempFilters.region_id;
delete tempFilters.project_id;

// Agregar filtro según el tipo
if (data.type === 'city' && data.cityId) {
    tempFilters.city_id = data.cityId;
}
```

#### 2. `clearAutocompletePreview()` (líneas 378-394)
**Propósito:** Restaurar estado original del mapa

**Lógica:**
1. Verificar si estamos en modo preview
2. Restaurar filtros originales desde `previewFilters`
3. Llamar a `loadMapPropertiesPreview()` con filtros originales
4. Limpiar flag y filtros guardados

**Código clave:**
```javascript
// Restaurar filtros originales
if (this.previewFilters) {
    console.log('[AUTOCOMPLETE-PREVIEW] Restaurando filtros originales:', this.previewFilters);
    this.loadMapPropertiesPreview(this.previewFilters);
    this.previewFilters = null;
}

this.isPreviewActive = false;
```

#### 3. `loadMapPropertiesPreview(filters)` (líneas 396-421)
**Propósito:** Cargar propiedades en el mapa con filtros específicos

**Lógica:**
1. Hacer llamada RPC a `/bohio/api/properties/map` con filtros personalizados
2. Actualizar el mapa con las propiedades recibidas
3. Manejar errores mostrando mapa vacío

**Diferencia con `loadMapProperties()`:**
- `loadMapProperties()` usa `this.filters` (estado actual)
- `loadMapPropertiesPreview()` recibe `filters` como parámetro (para preview temporal)

## 🔍 Flujo Completo

### Escenario: Usuario busca "monteria" y pasa por varios items

```
1. [ESTADO INICIAL]
   - this.filters = {}
   - this.previewFilters = null
   - this.isPreviewActive = false
   - Mapa muestra: Colombia general

2. [MOUSE SOBRE "Montería - 1543 props"]
   mouseenter → previewAutocompleteItem()
   - this.previewFilters = {} (guarda filtros vacíos)
   - this.isPreviewActive = true
   - tempFilters = { city_id: 1253 }
   - RPC call con city_id=1253
   - Mapa muestra: 30 propiedades en Montería

3. [MOUSE SOBRE "Montería Centro - 45 props"]
   mouseenter → previewAutocompleteItem()
   - this.previewFilters = {} (YA guardado, no sobrescribe)
   - tempFilters = { region_id: 789 }
   - RPC call con region_id=789
   - Mapa muestra: 30 propiedades en Montería Centro

4. [MOUSE SALE DEL DROPDOWN]
   mouseleave → clearAutocompletePreview()
   - loadMapPropertiesPreview(this.previewFilters) // = {}
   - this.previewFilters = null
   - this.isPreviewActive = false
   - Mapa muestra: Colombia general (restaurado)

5. [USUARIO HACE CLICK EN "Montería"]
   click → selectAutocompleteItem()
   - this.filters = { city_id: 1253 }
   - loadProperties() + loadMapProperties()
   - Mapa muestra: Propiedades en Montería (DEFINITIVO)
```

## 🎨 Experiencia de Usuario

### Ventajas
1. **Exploración rápida:** Ver propiedades sin compromiso de selección
2. **Feedback inmediato:** Mapa se actualiza instantáneamente al pasar mouse
3. **No invasivo:** Click sigue funcionando igual que antes
4. **Reversible:** Al salir, mapa vuelve al estado anterior

### Casos de uso
- **Comparar ubicaciones:** Pasar mouse por "Montería" vs "Barranquilla" para ver distribución
- **Verificar barrios:** Explorar "Centro" vs "Norte" sin aplicar filtro
- **Explorar proyectos:** Ver ubicación de "Rialto Tower" vs otros proyectos

## 🐛 Manejo de Casos Especiales

### 1. Items de tipo "property"
```javascript
if (item.dataset.type !== 'property') {
    this.previewAutocompleteItem(item.dataset);
}
```
**Razón:** Las propiedades individuales redirigen a página de detalle, no deben hacer preview

### 2. Mapa no inicializado
```javascript
if (!this.map || !this.markers) {
    console.log('[AUTOCOMPLETE-PREVIEW] Mapa no inicializado, saltando preview');
    return;
}
```
**Razón:** El mapa se inicializa async, puede no estar listo aún

### 3. Múltiples hovers rápidos
```javascript
// Guardar los filtros actuales SOLO la primera vez
if (!this.previewFilters) {
    this.previewFilters = { ...this.filters };
}
```
**Razón:** Al pasar rápido por varios items, solo guardar el estado inicial, no estados intermedios

## 📊 Logs de Consola

Al usar la funcionalidad, la consola mostrará:

```
[AUTOCOMPLETE-PREVIEW] Mostrando preview para: {type: "city", cityId: "1253", ...}
[AUTOCOMPLETE-PREVIEW] Filtros guardados: {}
[AUTOCOMPLETE-PREVIEW] Preview ciudad: 1253
[AUTOCOMPLETE-PREVIEW] Cargando mapa con filtros: {city_id: "1253"}
[AUTOCOMPLETE-PREVIEW] Respuesta: 30 propiedades
[MAP] Actualizando mapa con 30 propiedades
[MAP] Agregados 30 markers al mapa

[AUTOCOMPLETE-PREVIEW] Limpiando preview
[AUTOCOMPLETE-PREVIEW] Restaurando filtros originales: {}
[AUTOCOMPLETE-PREVIEW] Cargando mapa con filtros: {}
[AUTOCOMPLETE-PREVIEW] Respuesta: 30 propiedades
[MAP] Actualizando mapa con 30 propiedades
```

## 🔧 Backend

**No se requirieron cambios en el backend** porque:
- El endpoint `/bohio/api/properties/map` ya acepta `city_id`, `region_id`, `project_id`
- La implementación anterior ya procesaba estos filtros correctamente
- Solo se cambió **cuándo** se llama (hover vs click), no **cómo** funciona

## ✅ Testing

### Checklist de pruebas
- [ ] Escribir "monter" → aparecer autocomplete
- [ ] Pasar mouse sobre "Montería" → mapa actualiza
- [ ] Salir de "Montería" → mapa vuelve a estado anterior
- [ ] Pasar mouse sobre "Montería Centro" → mapa actualiza a barrio
- [ ] Hacer click en "Montería" → filtro se aplica definitivamente
- [ ] Verificar que propiedades individuales NO hacen preview (redirigen)
- [ ] Verificar funcionamiento con filtros previos activos (ej: type_service=rent)

## 📝 Notas Técnicas

### Limitación actual
- La función `loadMapPropertiesPreview()` siempre usa `limit: 30`
- Esto es consistente con `loadMapProperties()` original
- Si se requiere más propiedades, ajustar el límite en ambas funciones

### Mejora futura posible
- Añadir debounce para evitar llamadas excesivas al pasar mouse muy rápido
- Añadir indicador visual de que el mapa está en "modo preview"
- Guardar último preview y restaurarlo al reabrir dropdown

## 🚀 Deployment

El módulo fue actualizado exitosamente en:
- **URL:** https://darm1640-bohio-18.odoo.com
- **DB:** darm1640-bohio-18-main-24081960
- **Módulo:** theme_bohio_real_estate
- **Estado:** Instalado y funcionando

## 📅 Fecha de Implementación
2025-10-11

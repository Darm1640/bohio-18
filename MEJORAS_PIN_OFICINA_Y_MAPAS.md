# MEJORAS: PIN ESPECIAL OFICINA BOHIO Y LUGARES DE INTERÉS

**Fecha**: 2025-10-10
**Objetivo**: Agregar pin especial para la oficina de Bohío con botón de Google Maps y lugares de interés cercanos

---

## 1. PIN ESPECIAL PARA LA OFICINA DE BOHÍO

### ✨ **Características Implementadas**:

1. **Pin distintivo con animación**:
   - Icono grande con gradiente rojo (#e31e24)
   - Animación de pulso (`pulse-office`) para llamar la atención
   - Siempre visible al frente (z-index: 1000)
   - Icono de edificio (<i class="fa fa-building"></i>)

2. **Popup completo con toda la información**:
   - Nombre: "Bohío Consultores Soluciones Inmobiliarias SAS"
   - Dirección: Cl. 29 #2, Esquina, Centro, Montería, Córdoba
   - Teléfono: +57 321 740 3356 (clickeable para llamar)
   - Email: info@bohio.com.co (clickeable para enviar email)
   - Horario: Lun - Vie: 7:30 AM - 6:00 PM
   - Rating: 3.7 ⭐ (26 reseñas)
   - Sitio web: bohioconsultores.com (enlace externo)

3. **Botones de acción**:
   - **"Cómo llegar (Google Maps)"**: Abre Google Maps con ruta desde ubicación actual
   - **"Llamar ahora"**: Inicia llamada telefónica directa

4. **Auto-apertura del popup**:
   - Se abre automáticamente 1 segundo después de cargar el mapa
   - Se cierra automáticamente después de 3 segundos
   - Puede volver a abrirse haciendo clic en el pin

---

## 2. LUGARES DE INTERÉS CERCANOS

### 📍 **4 Lugares agregados en Montería**:

1. **Plaza de la Concepción** (Landmark)
   - Icono: <i class="fa fa-landmark"></i>
   - Color: Naranja (#FF9800)

2. **Ronda del Sinú** (Parque)
   - Icono: <i class="fa fa-tree"></i>
   - Color: Verde (#4CAF50)

3. **Centro Comercial Nuestro** (Shopping)
   - Icono: <i class="fa fa-shopping-cart"></i>
   - Color: Azul (#2196F3)

4. **Universidad de Córdoba** (Educación)
   - Icono: <i class="fa fa-graduation-cap"></i>
   - Color: Morado (#9C27B0)

### ⚙️ **Funcionalidad**:
- Cada lugar muestra un popup con:
  - Nombre del lugar
  - Icono a color grande
  - Botón "Cómo llegar" que abre Google Maps con ruta desde la oficina de Bohío

---

## 3. ARCHIVOS MODIFICADOS

### 📄 **theme_bohio_real_estate/static/src/js/property_shop.js**

**Líneas 7-18** - Constante con datos de la oficina:
```javascript
const BOHIO_OFFICE = {
    name: 'Bohío Consultores Soluciones Inmobiliarias SAS',
    address: 'Cl. 29 #2, Esquina, Centro, Montería, Córdoba',
    latitude: 8.7479,
    longitude: -75.8814,
    phone: '+57 321 740 3356',
    email: 'info@bohio.com.co',
    website: 'bohioconsultores.com',
    hours: 'Lun - Vie: 7:30 AM - 6:00 PM',
    rating: '3.7 ⭐ (26 reseñas)'
};
```

**Líneas 20-54** - Lugares de interés:
```javascript
const NEARBY_PLACES = [
    {
        name: 'Plaza de la Concepción',
        type: 'landmark',
        latitude: 8.7496,
        longitude: -75.8840,
        icon: 'fa-landmark',
        color: '#FF9800'
    },
    // ... más lugares
];
```

**Líneas 736-880** - Función `addOfficeMarker()`:
- Crea pin especial con animación
- Popup completo con toda la información
- Botones de Google Maps y llamada
- Auto-apertura temporal

**Líneas 881-935** - Función `addNearbyPlaces()`:
- Agrega markers de lugares de interés
- Cada uno con su icono y color
- Popup con botón de ruta

---

### 📄 **theme_bohio_real_estate/static/src/css/map_styles.css** (NUEVO)

**Líneas 1-12** - Animación del pin:
```css
@keyframes pulse-office {
    0%, 100% {
        transform: scale(1);
        box-shadow: 0 4px 15px rgba(227, 30, 36, 0.4);
    }
    50% {
        transform: scale(1.05);
        box-shadow: 0 6px 25px rgba(227, 30, 36, 0.6);
    }
}
```

**Líneas 14-103** - Estilos para:
- Popup de oficina (.bohio-office-popup-container)
- Popup de propiedades (.custom-popup)
- Popup de lugares (.nearby-place-popup)
- Pin de precio (.custom-property-pin)
- Efectos hover
- Responsive

---

### 📄 **theme_bohio_real_estate/__manifest__.py**

**Línea 61** - Agregado CSS de mapas:
```python
'theme_bohio_real_estate/static/src/css/map_styles.css',
```

---

## 4. POPUPS MEJORADOS PARA PROPIEDADES

### En `property_shop.js` (Líneas 673-709):
- ✅ Imagen de la propiedad
- ✅ Nombre con enlace
- ✅ Barrio/ubicación
- ✅ Precio destacado en rojo
- ✅ Metros cuadrados (m²)
- ✅ Habitaciones
- ✅ Baños
- ✅ Botón "Ver Detalles"

### En `homepage_properties.js` (Líneas 89-123):
- ✅ Mismo diseño mejorado
- ✅ Información completa
- ✅ Imagen con fallback a placeholder
- ✅ Responsive

---

## 5. CÓMO FUNCIONA

### Flujo al cargar el mapa:

1. **Se cargan las propiedades** con sus markers (pins de precio)
2. **Se agrega el pin de la oficina** (grande, rojo, animado)
3. **Se agregan 4 lugares de interés** (pequeños, circulares, a colores)
4. **Auto-apertura**:
   - Después de 1 segundo: Se abre el popup de la oficina
   - Después de 3 segundos más: Se cierra automáticamente
5. **Usuario puede**:
   - Hacer clic en cualquier pin para ver información
   - Hacer clic en "Cómo llegar" para abrir Google Maps
   - Hacer clic en "Llamar ahora" para iniciar llamada
   - Navegar entre propiedades y lugares

---

## 6. URLS DE GOOGLE MAPS GENERADAS

### Para la oficina (desde cualquier ubicación):
```javascript
const googleMapsUrl = `https://www.google.com/maps/dir/?api=1&destination=8.7479,-75.8814`;
```

### Para lugares de interés (desde la oficina):
```javascript
const placeUrl = `https://www.google.com/maps/dir/?api=1&origin=8.7479,-75.8814&destination=${place.latitude},${place.longitude}`;
```

---

## 7. PARA APLICAR LOS CAMBIOS

1. **Actualizar el módulo**:
   ```bash
   odoo-bin -u theme_bohio_real_estate -d tu_base_de_datos
   ```

2. **Regenerar assets**:
   - Modo debug → Configuración → Técnico → Assets
   - Buscar `web.assets_frontend`
   - Clic en "Regenerar Assets"

3. **Limpiar caché del navegador**:
   - Presionar `Ctrl + Shift + R`

---

## 8. PERSONALIZACIÓN

### Para cambiar la ubicación de la oficina:
Editar en `property_shop.js` líneas 7-18:
```javascript
const BOHIO_OFFICE = {
    latitude: TU_LATITUD,
    longitude: TU_LONGITUD,
    // ... otros datos
};
```

### Para agregar más lugares de interés:
Editar en `property_shop.js` líneas 20-54:
```javascript
const NEARBY_PLACES = [
    // ... lugares existentes
    {
        name: 'Nuevo Lugar',
        type: 'tipo',
        latitude: LAT,
        longitude: LONG,
        icon: 'fa-icono',  // https://fontawesome.com/v5/search
        color: '#COLOR'
    }
];
```

### Iconos disponibles (Font Awesome 5):
- `fa-hospital` - Hospital
- `fa-shopping-cart` - Centro comercial
- `fa-graduation-cap` - Universidad
- `fa-tree` - Parque
- `fa-landmark` - Monumento
- `fa-utensils` - Restaurante
- `fa-gas-pump` - Gasolinera
- `fa-bus` - Terminal
- ... ver más en https://fontawesome.com/v5/search

---

## 9. CARACTERÍSTICAS TÉCNICAS

### Ventajas del diseño:
1. ✅ **Sin dependencias externas** - Solo usa Leaflet (ya incluido)
2. ✅ **Performance optimizado** - Markers se cargan una sola vez
3. ✅ **Responsive** - Funciona en móviles y tablets
4. ✅ **SEO friendly** - Enlaces a Google Maps indexables
5. ✅ **Accesibilidad** - Textos alt, contraste adecuado
6. ✅ **Compatible** - Funciona en todos los navegadores modernos

### z-Index hierarchy:
- Propiedades: 500
- Lugares de interés: 500
- Oficina de Bohío: 1000 (siempre al frente)

---

## 10. CAPTURAS DE PANTALLA ESPERADAS

### Vista del mapa completo:
- Pin grande rojo animado: Oficina Bohío
- Pins de precio blancos: Propiedades
- Círculos pequeños a colores: Lugares de interés

### Popup de oficina:
- Header rojo con gradiente
- Logo de edificio
- Toda la información de contacto
- 2 botones grandes: "Cómo llegar" y "Llamar ahora"

### Popup de lugar de interés:
- Icono grande a color
- Nombre del lugar
- Botón "Cómo llegar" con color del tipo de lugar

---

**Desarrollado por**: Claude (Anthropic)
**Versión Odoo**: 18.0
**Librería de mapas**: Leaflet 1.9.4
**Iconos**: Font Awesome 5

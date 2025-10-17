# PLAN DE IMPLEMENTACIÓN - MARCA BOHIO

**Objetivo:** Aplicar correctamente la imagen de marca BOHIO según el Manual de Identidad Corporativa
**Fecha:** 2025-10-17
**Prioridad:** ALTA

---

## RESUMEN EJECUTIVO

### Cambios Principales Requeridos

| Elemento | Estado Actual | Debe Ser | Impacto |
|----------|---------------|----------|---------|
| **Color Rojo Principal** | `#E31E24` | `#FF1D25` (Pantone 485C) | ALTO |
| **Logos** | Versiones antiguas | Logos del manual oficial | ALTO |
| **Tipografías** | Mixtas | Montserrat + Oswald | MEDIO |
| **Área de protección** | No definida | 1x alrededor del logo | MEDIO |

---

## FASE 1: ACTUALIZACIÓN DE COLORES

### 1.1 Archivo: `_variables.scss`

**Ubicación:** `theme_bohio_real_estate/static/src/scss/_variables.scss`

**Acción:** Reemplazar variables de color

**Código Actual:**
```scss
$bohio-red-primary: #E31E24;
$bohio-red-secondary: #c91920;
$bohio-red-light: #ef4444;
$bohio-red-dark: #991b1b;
```

**Código Nuevo:**
```scss
// ============================================
// COLORES CORPORATIVOS BOHIO - MANUAL OFICIAL
// Pantone 485C: #FF1D25 | RGB(255, 29, 37)
// ============================================

$bohio-red-primary: #FF1D25 !default;        // Pantone 485C (Principal)
$bohio-red-primary-rgb: 255, 29, 37 !default;

$bohio-red-dark: #CC1720 !default;           // Hover/Active states
$bohio-red-light: #FF4D54 !default;          // Backgrounds suaves
$bohio-red-lighter: #FF7A7F !default;        // Alerts/Notificaciones

$bohio-black: #000000 !default;              // Pantone 1788C
$bohio-white: #FFFFFF !default;
```

**Comando:**
```bash
# Backup del archivo original
cp theme_bohio_real_estate/static/src/scss/_variables.scss theme_bohio_real_estate/static/src/scss/_variables.scss.backup

# Editar el archivo con los nuevos valores
```

---

### 1.2 Buscar y Reemplazar en Todos los Archivos

**Archivos afectados:** SCSS, CSS, XML, JS

**Buscar:** `#E31E24`
**Reemplazar:** `#FF1D25`

**Buscar:** `rgb(227, 30, 36)`
**Reemplazar:** `rgb(255, 29, 37)`

**Buscar:** `rgba(227, 30, 36,`
**Reemplazar:** `rgba(255, 29, 37,`

**Comando búsqueda global:**
```bash
cd c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18

# Buscar todas las ocurrencias
grep -r "#E31E24" theme_bohio_real_estate/ bohio_crm/ real_estate_bits/
grep -r "227, 30, 36" theme_bohio_real_estate/ bohio_crm/ real_estate_bits/
```

---

### 1.3 Archivos Prioritarios a Actualizar

**SCSS:**
- `theme_bohio_real_estate/static/src/scss/_variables.scss`
- `theme_bohio_real_estate/static/src/scss/_mixins.scss`
- `theme_bohio_real_estate/static/src/scss/header.scss`
- `theme_bohio_real_estate/static/src/scss/footer.scss`
- `theme_bohio_real_estate/static/src/scss/homepage.scss`
- `theme_bohio_real_estate/static/src/scss/property_cards.scss`

**CSS:**
- `theme_bohio_real_estate/static/src/css/style.css`
- `theme_bohio_real_estate/static/src/css/homepage_autocomplete.css`
- `theme_bohio_real_estate/static/src/css/property_snippets.css`

**XML:**
- `theme_bohio_real_estate/views/homepage_new.xml`
- `theme_bohio_real_estate/views/headers/header_template.xml`
- `theme_bohio_real_estate/views/footers/footer_template.xml`

---

## FASE 2: ACTUALIZACIÓN DE LOGOS

### 2.1 Copiar Logos del Manual de Marca

**Origen:**
```
C:\Users\darm1\Downloads\PAGINA WEB BOHIO-20250925T171508Z-1-003\PAGINA WEB BOHIO\MANUAL DE MARCA\
```

**Destino:**
```
c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\theme_bohio_real_estate\static\src\img\logos\
```

**Archivos a copiar:**

| Archivo Origen | Archivo Destino | Uso |
|----------------|-----------------|-----|
| `Bohio_Principal_Rojo_485C_sobreBlanco.png` | `logo-bohio-principal.png` | Logo principal (fondos claros) |
| `Bohio_Negativo_Blanco_sobreNegro.png` | `logo-bohio-blanco.png` | Fondos oscuros/negros |
| `Transparente_Rojo_485C.png` | `logo-bohio-rojo-transparente.png` | Fondos mixtos/overlays |
| `Transparente_Blanco.png` | `logo-bohio-blanco-transparente.png` | Overlays oscuros |
| `Logo-horizontal-bohio.png` | `logo-bohio-horizontal.png` | Headers/footers |

**Comandos:**
```powershell
# Crear directorio de logos
mkdir "c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\theme_bohio_real_estate\static\src\img\logos"

# Copiar archivos
Copy-Item "C:\Users\darm1\Downloads\PAGINA WEB BOHIO-20250925T171508Z-1-003\PAGINA WEB BOHIO\MANUAL DE MARCA\Bohio_Principal_Rojo_485C_sobreBlanco.png" "c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\theme_bohio_real_estate\static\src\img\logos\logo-bohio-principal.png"

Copy-Item "C:\Users\darm1\Downloads\PAGINA WEB BOHIO-20250925T171508Z-1-003\PAGINA WEB BOHIO\MANUAL DE MARCA\Bohio_Negativo_Blanco_sobreNegro.png" "c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\theme_bohio_real_estate\static\src\img\logos\logo-bohio-blanco.png"

Copy-Item "C:\Users\darm1\Downloads\PAGINA WEB BOHIO-20250925T171508Z-1-003\PAGINA WEB BOHIO\MANUAL DE MARCA\Transparente_Rojo_485C.png" "c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\theme_bohio_real_estate\static\src\img\logos\logo-bohio-rojo-transparente.png"

Copy-Item "C:\Users\darm1\Downloads\PAGINA WEB BOHIO-20250925T171508Z-1-003\PAGINA WEB BOHIO\MANUAL DE MARCA\Transparente_Blanco.png" "c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\theme_bohio_real_estate\static\src\img\logos\logo-bohio-blanco-transparente.png"

Copy-Item "C:\Users\darm1\Downloads\PAGINA WEB BOHIO-20250925T171508Z-1-003\PAGINA WEB BOHIO\MANUAL DE MARCA\Logo-horizontal-bohio.png" "c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\theme_bohio_real_estate\static\src\img\logos\logo-bohio-horizontal.png"
```

---

### 2.2 Actualizar Referencias en Header

**Archivo:** `theme_bohio_real_estate/views/headers/header_template.xml`

**Buscar:**
```xml
<img src="/theme_bohio_real_estate/static/src/img/logo-bohio.png" alt="BOHIO" />
```

**Reemplazar con:**
```xml
<img src="/theme_bohio_real_estate/static/src/img/logos/logo-bohio-principal.png"
     alt="BOHIO Consultores - Soluciones Inmobiliarias"
     style="max-height: 60px; width: auto;" />
```

---

### 2.3 Actualizar Referencias en Footer

**Archivo:** `theme_bohio_real_estate/views/footers/footer_template.xml`

**Buscar:**
```xml
<img src="/theme_bohio_real_estate/static/src/img/logo-blanco.png" alt="BOHIO" />
```

**Reemplazar con:**
```xml
<img src="/theme_bohio_real_estate/static/src/img/logos/logo-bohio-blanco.png"
     alt="BOHIO Consultores - Soluciones Inmobiliarias"
     style="max-height: 80px; width: auto;" />
```

---

### 2.4 Actualizar Favicon

**Crear favicon desde el isotipo:**

1. Tomar el archivo `Transparente_Rojo_485C.png`
2. Redimensionar a 512x512px
3. Convertir a favicon.ico con múltiples tamaños (16x16, 32x32, 48x48, 64x64, 128x128, 256x256)

**Herramienta online:** https://favicon.io/favicon-converter/

**Ubicación final:**
```
theme_bohio_real_estate/static/description/icon.png (512x512)
theme_bohio_real_estate/static/favicon.ico
```

---

## FASE 3: ACTUALIZACIÓN DE TIPOGRAFÍAS

### 3.1 Cargar Tipografías desde Google Fonts

**Archivo:** `theme_bohio_real_estate/__manifest__.py`

**En la sección de `assets`**, agregar antes de otros CSS:

```python
'assets': {
    'web.assets_frontend': [
        # Google Fonts (alternativas a Arista Pro y Bebas Neue Pro)
        'https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&family=Oswald:wght@400;600;700&display=swap',

        # ... resto de assets
    ]
}
```

---

### 3.2 Actualizar Variables de Tipografía

**Archivo:** `theme_bohio_real_estate/static/src/scss/_variables.scss`

**Agregar:**
```scss
// ============================================
// TIPOGRAFÍAS CORPORATIVAS
// ============================================

// Tipografía Principal (Arista Pro alternativa)
$font-family-bohio-primary: 'Montserrat', -apple-system, BlinkMacSystemFont, sans-serif !default;

// Tipografía Secundaria (Bebas Neue Pro alternativa)
$font-family-bohio-secondary: 'Oswald', 'Arial Narrow', sans-serif !default;

// Tipografía de Cuerpo
$font-family-bohio-body: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !default;

// Pesos
$font-weight-bohio-bold: 700 !default;
$font-weight-bohio-semibold: 600 !default;
$font-weight-bohio-regular: 400 !default;
```

---

### 3.3 Aplicar Tipografías

**Archivo:** `theme_bohio_real_estate/static/src/scss/_mixins.scss`

**Agregar mixins:**
```scss
// Mixin para tipografía principal (Logotipo "bohío")
@mixin font-bohio-primary {
  font-family: $font-family-bohio-primary;
  font-weight: $font-weight-bohio-bold;
}

// Mixin para tipografía secundaria (CONSULTORES)
@mixin font-bohio-secondary {
  font-family: $font-family-bohio-secondary;
  font-weight: $font-weight-bohio-bold;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

// Mixin para cuerpo de texto
@mixin font-bohio-body {
  font-family: $font-family-bohio-body;
  font-weight: $font-weight-bohio-regular;
}
```

---

## FASE 4: ÁREA DE PROTECCIÓN DEL LOGO

### 4.1 Agregar Estilos de Protección

**Archivo:** `theme_bohio_real_estate/static/src/scss/header.scss`

**Agregar:**
```scss
.bohio-logo-container {
  padding: 1rem; // Área de protección mínima

  img {
    display: block;
    max-height: 60px;
    width: auto;

    // Asegurar espacio alrededor
    margin: 0.5rem;
  }
}
```

**Aplicar en XML:**
```xml
<div class="bohio-logo-container">
  <img src="/theme_bohio_real_estate/static/src/img/logos/logo-bohio-principal.png"
       alt="BOHIO Consultores - Soluciones Inmobiliarias" />
</div>
```

---

## FASE 5: COMPILACIÓN Y TESTING

### 5.1 Recompilar Assets

```bash
cd c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18

# Si usas compilador SCSS
sass theme_bohio_real_estate/static/src/scss:theme_bohio_real_estate/static/src/css

# O en Odoo 18
# Los assets se compilan automáticamente al actualizar el módulo
```

---

### 5.2 Actualizar Módulo en Odoo

```python
# En Odoo, ir a:
# Apps > Theme Bohio Real Estate > Actualizar

# O desde línea de comandos:
python odoo-bin -u theme_bohio_real_estate -d bohio --stop-after-init
```

---

### 5.3 Testing Checklist

**Visuales:**
- [ ] Logo se ve correctamente en header (fondo blanco)
- [ ] Logo se ve correctamente en footer (fondo negro)
- [ ] Color rojo es el correcto (`#FF1D25`)
- [ ] Tipografías se cargan correctamente
- [ ] Área de protección respetada (mín 1rem)
- [ ] Tamaño mínimo respetado (100px web)

**Responsive:**
- [ ] Logo se adapta en mobile (mín 100px)
- [ ] Logo se adapta en tablet
- [ ] Logo se adapta en desktop
- [ ] No se distorsiona en ninguna resolución

**Contraste:**
- [ ] Logo rojo sobre blanco: contraste WCAG AA ✓
- [ ] Logo blanco sobre negro: contraste WCAG AA ✓
- [ ] Logo blanco sobre rojo: contraste WCAG AA ✓

**Cross-browser:**
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge

---

## FASE 6: DOCUMENTACIÓN

### 6.1 Actualizar README del Módulo

**Archivo:** `theme_bohio_real_estate/README.md`

**Agregar sección:**
```markdown
## Identidad Visual

Este tema sigue estrictamente el Manual de Identidad Corporativa de BOHIO.

### Colores Corporativos
- **Rojo Principal:** `#FF1D25` (Pantone 485C)
- **Negro:** `#000000` (Pantone 1788C)
- **Blanco:** `#FFFFFF`

### Tipografías
- **Principal:** Montserrat Bold (Alternativa a Arista Pro)
- **Secundaria:** Oswald Bold (Alternativa a Bebas Neue Pro)

### Logos
Ubicación: `static/src/img/logos/`

Consultar `MANUAL_MARCA_BOHIO_ESPECIFICACIONES.md` para más detalles.
```

---

### 6.2 Crear CHANGELOG

**Archivo:** `theme_bohio_real_estate/CHANGELOG.md`

**Agregar entrada:**
```markdown
## [18.0.3.0.2] - 2025-10-17

### Changed
- **BREAKING:** Actualizado color rojo corporativo de `#E31E24` a `#FF1D25` (Pantone 485C) según Manual de Identidad Corporativa oficial
- Reemplazados logos con versiones oficiales del manual de marca
- Actualizadas tipografías a Montserrat y Oswald (alternativas web)
- Implementada área de protección del logo (mín 1rem)
- Asegurados tamaños mínimos de reproducción (100px web)

### Added
- Nuevos archivos de logo en `/static/src/img/logos/`
- Variables CSS para colores corporativos
- Mixins SCSS para tipografías corporativas
- Documentación completa en `MANUAL_MARCA_BOHIO_ESPECIFICACIONES.md`

### Fixed
- Contraste de colores cumple WCAG AA
- Proporciones de logo respetadas (2:3)
- Logo responsive en todos los dispositivos
```

---

## RESUMEN DE ARCHIVOS A MODIFICAR

### Críticos (ALTA PRIORIDAD)

1. `theme_bohio_real_estate/static/src/scss/_variables.scss` - Colores
2. `theme_bohio_real_estate/views/headers/header_template.xml` - Logo header
3. `theme_bohio_real_estate/views/footers/footer_template.xml` - Logo footer
4. `theme_bohio_real_estate/__manifest__.py` - Tipografías Google Fonts
5. Copiar logos del manual de marca

### Importantes (MEDIA PRIORIDAD)

6. `theme_bohio_real_estate/static/src/scss/_mixins.scss` - Mixins tipografías
7. `theme_bohio_real_estate/static/src/scss/header.scss` - Área protección
8. `theme_bohio_real_estate/views/homepage_new.xml` - Colores homepage
9. `theme_bohio_real_estate/static/src/css/style.css` - Colores CSS
10. `theme_bohio_real_estate/README.md` - Documentación

### Opcionales (BAJA PRIORIDAD)

11. `theme_bohio_real_estate/CHANGELOG.md` - Registro de cambios
12. Favicon actualizado
13. Compilar SCSS a CSS
14. Testing exhaustivo

---

## CRONOGRAMA ESTIMADO

| Fase | Tarea | Tiempo | Responsable |
|------|-------|--------|-------------|
| 1 | Actualizar colores en variables | 30 min | Dev |
| 1 | Buscar/reemplazar colores global | 45 min | Dev |
| 2 | Copiar logos del manual | 15 min | Dev |
| 2 | Actualizar referencias de logos | 30 min | Dev |
| 2 | Crear favicon | 20 min | Dev |
| 3 | Cargar tipografías Google Fonts | 15 min | Dev |
| 3 | Actualizar variables tipografías | 20 min | Dev |
| 3 | Aplicar tipografías en código | 30 min | Dev |
| 4 | Implementar área de protección | 20 min | Dev |
| 5 | Compilar y actualizar módulo | 15 min | Dev |
| 5 | Testing visual | 45 min | QA |
| 5 | Testing responsive | 30 min | QA |
| 5 | Testing cross-browser | 30 min | QA |
| 6 | Documentación | 30 min | Dev |
| **TOTAL** | | **6 horas** | |

---

## RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Colores no coinciden exactamente | Media | Alto | Usar valores exactos del manual |
| Logos no se ven bien en mobile | Baja | Medio | Testing exhaustivo responsive |
| Tipografías no cargan | Baja | Medio | Tener fallbacks definidos |
| Breaking changes en sitio live | Alta | Alto | Deploy en staging primero |
| Assets no se recompilan | Media | Alto | Limpiar cache y rebuild |

---

## APROBACIONES REQUERIDAS

- [ ] **Cliente:** Revisar y aprobar cambios visuales
- [ ] **Diseñador:** Validar correcta aplicación del manual de marca
- [ ] **QA:** Validar testing en todos los navegadores
- [ ] **Product Owner:** Aprobar deploy a producción

---

## COMANDOS RÁPIDOS

### Backup antes de cambios
```bash
cd c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18
git checkout -b feature/manual-marca-bohio
git add .
git commit -m "Backup antes de aplicar manual de marca"
```

### Buscar todas las referencias al color antiguo
```bash
grep -rn "#E31E24" theme_bohio_real_estate/
grep -rn "227, 30, 36" theme_bohio_real_estate/
grep -rn "E31E24" theme_bohio_real_estate/
```

### Reemplazar color globalmente (cuidado!)
```bash
# Usar con precaución, hacer backup primero
find theme_bohio_real_estate/ -type f -exec sed -i 's/#E31E24/#FF1D25/g' {} +
find theme_bohio_real_estate/ -type f -exec sed -i 's/227, 30, 36/255, 29, 37/g' {} +
```

---

**Documento creado:** 2025-10-17
**Última actualización:** 2025-10-17
**Responsable:** Equipo de Desarrollo BOHIO

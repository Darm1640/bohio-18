# Theme Bohio Real Estate

Tema profesional para inmobiliarias desarrollado para Bohio Real Estate en Odoo 18.

## Características

### 🏠 Homepage
- **Banner Hero** con imagen de familia y búsqueda de propiedades
- **Barra de Búsqueda Avanzada** con filtros por:
  - Barrio/Ubicación
  - Habitaciones
  - Baños
  - Área mínima (m²)
  - Tipo de servicio (Venta/Arriendo)
  - Filtros avanzados (precio, tipo de propiedad, estrato, estado)
- **Propiedades Destacadas** con grid responsivo
- **Sección de Servicios** (Venta, Arriendo, Consigna, Legal, Marketing, Corporativos)
- **Call to Action** con botones de contacto

### 🎨 Diseño
- **Fuentes personalizadas**:
  - Arista Pro (títulos)
  - Ciutadella (cuerpo de texto)
- **Colores de marca**:
  - Azul oscuro primario: `#1E3A8A`
  - Azul claro secundario: `#0EA5E9`
  - Dorado acento: `#F59E0B`
- **Componentes modernos**:
  - Cards con efectos hover
  - Iconos Remix Icon
  - Sombras y transiciones suaves
  - Diseño 100% responsivo

### 📱 Portal de Clientes
- Diseño personalizado del portal
- Estilos mejorados para tarjetas y enlaces
- Integración con bohio_real_estate

### 🔍 Componentes

#### Property Search Bar
Componente reutilizable de búsqueda que incluye:
- Búsqueda básica en una sola línea
- Panel de filtros avanzados colapsable
- Autocompletado de barrios (preparado para implementar)
- Validación de formularios

#### Property Card
Tarjeta de propiedad con:
- Imagen con badge de tipo (Venta/Arriendo)
- Título y ubicación
- Características (habitaciones, baños, área)
- Precio y botón de acción

## Instalación

1. Copiar el módulo a la carpeta de addons de Odoo
2. Actualizar lista de aplicaciones
3. Instalar "Theme Bohio Real Estate"

## Dependencias

- `website` - Website Builder de Odoo
- `portal` - Portal de clientes
- `bohio_real_estate` - Módulo de bienes raíces de Bohio

## Estructura de Archivos

```
theme_bohio_real_estate/
├── static/
│   └── src/
│       ├── css/
│       ├── scss/
│       │   ├── color_variables.scss      # Variables de color
│       │   ├── theme_variables.scss      # Variables de tema
│       │   ├── common.scss               # Estilos comunes
│       │   ├── header.scss               # Estilos del header
│       │   ├── footer.scss               # Estilos del footer
│       │   ├── homepage.scss             # Estilos del home
│       │   ├── property_search.scss      # Estilos de búsqueda
│       │   └── portal.scss               # Estilos del portal
│       ├── js/
│       │   ├── common.js                 # JavaScript común
│       │   ├── property_search.js        # JS de búsqueda
│       │   └── portal.js                 # JS del portal
│       ├── fonts/
│       │   ├── arista-pro-bold.ttf
│       │   ├── Ciutadella Light.ttf
│       │   └── Ciutadella SemiBold.ttf
│       └── img/
│           ├── home-banner.jpg
│           └── logo.png
└── views/
    ├── assets.xml
    ├── homepage_template.xml
    ├── property_search_template.xml
    ├── portal_template.xml
    ├── headers/
    │   └── header_template.xml
    └── footers/
        └── footer_template.xml
```

## Uso

### Homepage
La homepage se carga automáticamente en la ruta raíz `/`.

### Búsqueda de Propiedades
El componente de búsqueda se puede incluir en cualquier página con:
```xml
<t t-call="theme_bohio_real_estate.property_search_bar"/>
```

### Property Card
Para mostrar una tarjeta de propiedad:
```xml
<t t-call="theme_bohio_real_estate.property_card">
    <t t-set="property" t-value="property_record"/>
</t>
```

## Personalización

### Colores
Modificar `static/src/scss/color_variables.scss`

### Fuentes
Modificar `static/src/scss/theme_variables.scss`

### Estilos
Los estilos están modularizados por componente en archivos SCSS separados.

## Soporte

Para soporte técnico, contactar al equipo de desarrollo de Bohio.

## Licencia

LGPL-3

## Versión

18.0.1.0.0

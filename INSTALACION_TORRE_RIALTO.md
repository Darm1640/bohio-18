# Instalación del Proyecto Torre Rialto

## ✅ Archivos Creados

### 1. **Archivo de Datos XML** (Recomendado)
📁 `real_estate_bits/data/proyecto_torre_rialto.xml`

Este archivo crea automáticamente:
- ✅ Proyecto "Torre Rialto" usando el modelo `project.worksite`
- ✅ Barrio "Milla de Oro" (si no existe)
- ✅ Toda la información del proyecto
- ✅ Descripción con tabla HTML de apartamentos
- ✅ Características técnicas del proyecto

### 2. **Archivo CSV** (Alternativa)
📁 `data/proyecto_rialto_monteria.csv`

Contiene 10 apartamentos de ejemplo listos para importar.

### 3. **Documentación Completa**
📁 `PROYECTO_RIALTO_MONTERIA.md`

---

## 🚀 Instalación Paso a Paso

### Método 1: Actualizar Módulo (RECOMENDADO)

Este método instala el proyecto automáticamente usando el archivo XML.

#### Paso 1: Reiniciar Odoo con actualización

```bash
# Windows
cd "C:\Program Files\Odoo 18.0.20250830\server"
python odoo-bin -c odoo.conf -u real_estate_bits -d nombre_base_datos

# Linux
./odoo-bin -c /etc/odoo/odoo.conf -u real_estate_bits -d nombre_base_datos
```

**¿Qué hace?**
- Lee el archivo `data/proyecto_torre_rialto.xml`
- Crea el registro del proyecto en la base de datos
- Crea el barrio "Milla de Oro" si no existe

#### Paso 2: Verificar que se creó

1. Ir a **Inmobiliaria → Proyectos**
2. Buscar "**Torre Rialto**"
3. Verificar que aparece con:
   - ✅ Nombre: Torre Rialto
   - ✅ Código: RIALTO
   - ✅ Tipo: Torre
   - ✅ 18 pisos
   - ✅ Descripción completa con tabla HTML

---

### Método 2: Importar CSV (Alternativa)

Si prefieres crear solo las propiedades sin el proyecto:

#### Paso 1: Crear Proyecto Manualmente

1. Ir a **Inmobiliaria → Proyectos → Crear**
2. Llenar:
   - **Nombre**: Torre Rialto
   - **Código**: RIALTO
   - **Tipo de Proyecto**: Torre
   - **Barrio**: Milla de Oro (crear si no existe)
   - **Dirección**: Milla de Oro, Montería, Córdoba
   - **# Pisos**: 18
   - **# Torres**: 1
   - **# Total de Propiedades**: 70

#### Paso 2: Importar Apartamentos

1. Ir a **Inventario → Productos → Productos**
2. Clic en **"⚙️ Favoritos" → "Importar registros"**
3. Cargar: `data/proyecto_rialto_monteria.csv`
4. Mapear columnas (automático si los nombres coinciden)
5. **Importante**: En la columna `project_name`, mapear al campo `project_worksite_id` y buscar "Torre Rialto"
6. Importar

---

## 🗺️ Configurar Barrio con Coordenadas GPS

El barrio "Milla de Oro" necesita coordenadas para que aparezca en el mapa.

### Opción A: Desde la Interfaz

1. Ir a **Configuración → Técnico → Regiones (region.region)**
2. Buscar "**Milla de Oro**"
3. Editar y agregar:
   - **Ciudad**: Montería
   - **Departamento**: Córdoba
   - **País**: Colombia

### Opción B: Actualizar XML

Editar `real_estate_bits/data/proyecto_torre_rialto.xml`:

```xml
<!-- Descomentar estas líneas después de encontrar los IDs correctos -->
<record id="region_milla_de_oro" model="region.region">
    <field name="name">Milla de Oro</field>
    <field name="city_id" ref="base.city_monteria"/>  <!-- Si existe -->
    <field name="state_id" ref="base.state_co_23"/>  <!-- ID de Córdoba -->
    <field name="country_id" ref="base.co"/>  <!-- Colombia -->
</record>
```

---

## 📊 Verificación del Proyecto

### 1. En Backend (Odoo Admin)

**Ir a**: Inmobiliaria → Proyectos → Torre Rialto

Verificar:
- ✅ **General**: Nombre, código, tipo
- ✅ **Ubicación**: Barrio Milla de Oro
- ✅ **Características**: 18 pisos, 1 torre
- ✅ **Descripción**: Tabla HTML con tipos de apartamentos
- ✅ **Notas**: Amenidades y desarrolladores

### 2. En Propiedades

**Ir a**: Inventario → Productos → Productos

**Filtrar por**: Proyecto = "Torre Rialto"

Deberías ver:
- 10 apartamentos (si importaste el CSV)
- Todos con coordenadas: `8.7523, -75.8792`
- Todos con amenidades (piscina, gym, etc.)
- Precios desde $550M hasta $1,200M

### 3. En el Mapa (Frontend)

**Ir a**: https://tu-dominio.com/properties/shop

1. **Buscar**: "Torre Rialto" o "Milla de Oro" en el autocomplete
2. **Mapa**: Debería aparecer un pin en Montería
3. **Click en pin**: Ver las propiedades del proyecto
4. **Filtros**: Filtrar por Montería → Ver Torre Rialto

---

## 🎨 Landing Page del Proyecto

Para crear una página dedicada al proyecto:

### Opción 1: Página QWeb

Crear archivo: `real_estate_bits/views/proyecto_torre_rialto_landing.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <template id="torre_rialto_landing" name="Torre Rialto Landing">
        <t t-call="website.layout">
            <div id="wrap">
                <!-- Hero Section -->
                <section class="s_cover parallax s_parallax_no_overflow_hidden pt160 pb160" style="background-image: url('/theme_bohio_real_estate/static/src/img/torre-rialto-hero.jpg');">
                    <span class="s_parallax_bg oe_img_bg" style="background-image: url('/theme_bohio_real_estate/static/src/img/torre-rialto-hero.jpg'); background-position: 50% 0;"></span>
                    <div class="container">
                        <div class="row">
                            <div class="col-lg-7">
                                <h1 class="text-white display-2 fw-bold">Torre Rialto</h1>
                                <p class="lead text-white">Vive a la altura de tus sueños en la Milla de Oro de Montería</p>
                                <a href="#apartamentos" class="btn btn-lg" style="background: #E31E24; color: white;">
                                    Ver Apartamentos Disponibles
                                </a>
                            </div>
                        </div>
                    </div>
                </section>

                <!-- Apartamentos Section -->
                <section id="apartamentos" class="pt96 pb96">
                    <div class="container">
                        <h2 class="text-center mb-5">Tipos de Apartamentos</h2>
                        <div class="row">
                            <!-- Aquí cargar dinámicamente las propiedades del proyecto -->
                            <t t-foreach="properties" t-as="prop">
                                <div class="col-lg-4 col-md-6 mb-4">
                                    <!-- Tarjeta de propiedad -->
                                </div>
                            </t>
                        </div>
                    </div>
                </section>

                <!-- Amenidades Section -->
                <section class="bg-light pt96 pb96">
                    <div class="container">
                        <h2 class="text-center mb-5">Amenidades</h2>
                        <div class="row">
                            <div class="col-md-3 text-center mb-4">
                                <i class="fa fa-swimming-pool fa-3x text-primary mb-3"></i>
                                <h5>Piscina</h5>
                            </div>
                            <!-- Más amenidades -->
                        </div>
                    </div>
                </section>
            </div>
        </t>
    </template>
</odoo>
```

### Opción 2: Página en Website Builder

1. Ir a **Website → Sitio Web**
2. Click en **+ Nuevo** → **Nueva Página**
3. Nombre: "Torre Rialto"
4. URL: `/proyecto/torre-rialto`
5. Usar el editor visual para agregar:
   - Hero con imagen
   - Sección de apartamentos
   - Galería
   - Contacto

---

## 🔗 Integración con el Sitio Web Original

El sitio original (https://www.rialto-monteria.com/) puede:

1. **Redireccionar** a tu página de Odoo
2. **Iframe**: Embeber tu página en su sitio
3. **API**: Consultar disponibilidad desde tu Odoo

---

## 📋 Checklist Post-Instalación

- [ ] Proyecto "Torre Rialto" creado
- [ ] Barrio "Milla de Oro" asociado a Montería
- [ ] 10 apartamentos importados (o más)
- [ ] Todas las propiedades tienen coordenadas GPS
- [ ] Propiedades aparecen en el mapa
- [ ] Autocomplete muestra "Torre Rialto" al buscar
- [ ] Página landing creada (opcional)
- [ ] Imágenes reales agregadas
- [ ] Formulario de contacto configurado

---

## 🐛 Troubleshooting

### Error: "El barrio Milla de Oro no existe"

**Solución**: Crear manualmente en **Configuración → Técnico → Regiones**

### Error: "No aparece en el mapa"

**Verificar**:
1. Las propiedades tienen `latitude` y `longitude` no vacíos
2. El campo `is_property = True`
3. El estado es `state = 'free'`

### Error: "No aparece en autocomplete"

**Verificar**:
1. El endpoint está activo: [main.py:313](controllers/main.py#L313)
2. El proyecto tiene `is_enabled = True`
3. Hay propiedades asociadas al proyecto

---

## 📞 Soporte

Para dudas sobre la instalación:
- Revisar logs de Odoo: `Configuración → Técnico → Logs`
- Verificar permisos del usuario
- Asegurarse de que el módulo `real_estate_bits` esté actualizado

---

**Última actualización**: 2025-10-10
**Versión de Odoo**: 18.0
**Módulo**: real_estate_bits

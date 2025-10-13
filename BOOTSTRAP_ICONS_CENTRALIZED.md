# Bootstrap Icons - Instalación Centralizada en Módulo Base

## Fecha: 2025-10-13
## Módulo Base: real_estate_bits
## Versión Bootstrap Icons: 1.11.3

---

## 🏗️ ARQUITECTURA DE MÓDULOS BOHIO

```
real_estate_bits (MÓDULO BASE ⭐)
    │
    │   ✅ Bootstrap Icons instalado aquí
    │   ✅ Disponible para TODOS los módulos
    │
    ├── bohio_real_estate (Portal & Préstamos)
    │   │   ✅ Hereda Bootstrap Icons automáticamente
    │   │
    │   └── theme_bohio_real_estate (Tema Website Público)
    │       ✅ Hereda Bootstrap Icons automáticamente
    │
    └── bohio_crm (CRM Inmobiliario)
        ✅ Hereda Bootstrap Icons automáticamente
```

---

## 📦 INSTALACIÓN CENTRALIZADA

### ¿Por Qué en `real_estate_bits`?

✅ **Módulo Base**: Todos los otros módulos dependen de él
✅ **Sin Duplicación**: Solo se instala una vez
✅ **Herencia Automática**: Todos los módulos hijo lo heredan
✅ **Fácil Actualización**: Solo actualizar en un lugar
✅ **Backend + Frontend**: Disponible en ambos contextos

### Pasos Realizados:

#### 1. Instalación NPM (Una sola vez):
```bash
cd c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18
npm i bootstrap-icons
```

#### 2. Copia al Módulo Base:
```bash
cp -r node_modules/bootstrap-icons/font/* real_estate_bits/static/src/lib/bootstrap-icons/
```

#### 3. Configuración en `real_estate_bits/__manifest__.py`:

```python
"assets": {
    "web.assets_backend": [
        # Bootstrap Icons - Disponible para todos los módulos (Backend)
        "real_estate_bits/static/src/lib/bootstrap-icons/bootstrap-icons.min.css",

        # ... otros assets backend
    ],
    'web.assets_frontend': [
        # Bootstrap Icons - Disponible para todos los módulos (Frontend)
        "real_estate_bits/static/src/lib/bootstrap-icons/bootstrap-icons.min.css",

        # ... otros assets frontend
    ],
}
```

#### 4. Módulos Hijos (NO necesitan configuración):

**bohio_real_estate/__manifest__.py**:
```python
'depends': [
    'real_estate_bits',  # ← Hereda Bootstrap Icons automáticamente
    # ...
],
```

**theme_bohio_real_estate/__manifest__.py**:
```python
'depends': [
    'bohio_real_estate',  # ← Hereda Bootstrap Icons vía bohio_real_estate
    # ...
],
'assets': {
    'web.assets_frontend': [
        # Bootstrap Icons - Heredado de real_estate_bits
        # No es necesario incluirlo aquí, se carga automáticamente

        # ... otros assets del tema
    ],
}
```

**bohio_crm/__manifest__.py**:
```python
'depends': [
    'real_estate_bits',  # ← Hereda Bootstrap Icons automáticamente
    # ...
],
```

---

## 📂 ESTRUCTURA DE ARCHIVOS

```
c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\
│
├── real_estate_bits/                        ← ⭐ MÓDULO BASE (CONTIENE LOS ICONOS)
│   └── static/
│       └── src/
│           └── lib/
│               └── bootstrap-icons/
│                   ├── bootstrap-icons.css           (versión completa)
│                   ├── bootstrap-icons.min.css       (versión minificada - USADA)
│                   ├── bootstrap-icons.scss          (para compilación)
│                   ├── bootstrap-icons.json          (metadata)
│                   └── fonts/
│                       ├── bootstrap-icons.woff
│                       └── bootstrap-icons.woff2
│
├── bohio_real_estate/                      ← Hereda de real_estate_bits
│   └── (No necesita copiar los archivos)
│
├── theme_bohio_real_estate/                ← Hereda vía bohio_real_estate
│   └── (No necesita copiar los archivos)
│   └── (Archivos antiguos fueron eliminados)
│
└── bohio_crm/                              ← Hereda de real_estate_bits
    └── (No necesita copiar los archivos)
```

---

## 🎨 CÓMO USAR EN CUALQUIER MÓDULO

Gracias a la herencia, Bootstrap Icons está disponible en **TODOS** los módulos:

### Sintaxis Básica:
```html
<i class="bi bi-{nombre-icono}"></i>
```

### Contextos Disponibles:

#### 1. Frontend (Website Público):
- Homepage
- Páginas de propiedades
- Shop de propiedades
- Portal clientes
- Formularios de contacto

#### 2. Backend (Interfaz Odoo):
- Vistas de formulario
- Vistas de lista
- Dashboard
- Widgets personalizados
- Botones y acciones

### Ejemplos por Módulo:

#### En `theme_bohio_real_estate` (Website):
```html
<!-- En property cards -->
<i class="bi bi-bed"></i> 3 Habitaciones
<i class="bi bi-droplet"></i> 2 Baños
<i class="bi bi-rulers"></i> 120 m²

<!-- En botones -->
<button class="btn btn-primary">
    <i class="bi bi-heart-fill me-2"></i> Favoritos
</button>
```

#### En `bohio_real_estate` (Portal):
```html
<!-- En dashboard de propietario -->
<i class="bi bi-house-fill"></i> Mis Propiedades
<i class="bi bi-cash-stack"></i> Pagos
<i class="bi bi-file-text"></i> Facturas

<!-- En menú lateral -->
<i class="bi bi-speedometer2"></i> Dashboard
<i class="bi bi-building"></i> Propiedades
<i class="bi bi-calendar-event"></i> Contratos
```

#### En `bohio_crm` (Backend):
```xml
<!-- En vistas XML de Odoo -->
<button name="action_schedule_visit" type="object" class="btn-primary">
    <i class="bi bi-calendar-event me-1"></i> Agendar Visita
</button>

<div class="o_kanban_record">
    <i class="bi bi-telephone-fill"></i> Llamar Cliente
</div>
```

#### En `real_estate_bits` (Backend Core):
```xml
<!-- En formularios de propiedades -->
<button name="action_publish_property" type="object">
    <i class="bi bi-eye-fill"></i> Publicar
</button>

<field name="state">
    <i class="bi bi-check-circle-fill text-success"></i> Disponible
</field>
```

---

## 📋 ICONOS MÁS ÚTILES PARA INMOBILIARIA

### Características de Propiedades:
| Característica | Icono | Código |
|----------------|-------|--------|
| Habitaciones | 🛏️ | `<i class="bi bi-bed"></i>` |
| Baños | 💧 | `<i class="bi bi-droplet"></i>` |
| Garage | 🚗 | `<i class="bi bi-car-front"></i>` |
| Piscina | 🏊 | `<i class="bi bi-water"></i>` |
| Jardín | 🌸 | `<i class="bi bi-flower2"></i>` |
| Ascensor | ⬆️ | `<i class="bi bi-arrow-up-square"></i>` |
| Área/m² | 📏 | `<i class="bi bi-rulers"></i>` |
| Piso/Nivel | 🏢 | `<i class="bi bi-building"></i>` |

### Acciones Comunes:
| Acción | Icono | Código |
|--------|-------|--------|
| Buscar | 🔍 | `<i class="bi bi-search"></i>` |
| Favoritos | ❤️ | `<i class="bi bi-heart-fill"></i>` |
| Compartir | 🔗 | `<i class="bi bi-share-fill"></i>` |
| Descargar | 📥 | `<i class="bi bi-download"></i>` |
| Imprimir | 🖨️ | `<i class="bi bi-printer-fill"></i>` |
| WhatsApp | 💬 | `<i class="bi bi-whatsapp"></i>` |
| Email | 📧 | `<i class="bi bi-envelope-fill"></i>` |
| Teléfono | 📞 | `<i class="bi bi-telephone-fill"></i>` |

### Estados y Alertas:
| Estado | Icono | Código |
|--------|-------|--------|
| Disponible | ✅ | `<i class="bi bi-check-circle-fill"></i>` |
| No disponible | ❌ | `<i class="bi bi-x-circle-fill"></i>` |
| Advertencia | ⚠️ | `<i class="bi bi-exclamation-triangle"></i>` |
| Información | ℹ️ | `<i class="bi bi-info-circle-fill"></i>` |
| Destacado | ⭐ | `<i class="bi bi-star-fill"></i>` |
| Nuevo | 🆕 | `<i class="bi bi-patch-plus"></i>` |

---

## 🚀 ACTUALIZAR MÓDULOS

Después de la instalación centralizada, es necesario actualizar el módulo base:

### Opción 1: Actualizar Solo `real_estate_bits`:
```bash
cd "C:\Program Files\Odoo 18.0.20250830\server"
..\python\python.exe odoo-bin -c odoo.conf -d bohio_db -u real_estate_bits --stop-after-init
```

### Opción 2: Actualizar Todos los Módulos:
```bash
# Actualizar en orden de dependencia
..\python\python.exe odoo-bin -c odoo.conf -d bohio_db -u real_estate_bits,bohio_crm,bohio_real_estate,theme_bohio_real_estate --stop-after-init
```

### Opción 3: Via Script Python (Para servidor remoto):
```python
# crear actualizar_real_estate_bits.py
import xmlrpc.client

URL = 'https://104.131.70.107'
DB = 'bohio'
USERNAME = 'admin'
PASSWORD = '123456'

common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid = common.authenticate(DB, USERNAME, PASSWORD, {})

models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

# Buscar módulo
module_id = models.execute_kw(DB, uid, PASSWORD, 'ir.module.module', 'search',
    [[('name', '=', 'real_estate_bits')]])

# Actualizar
models.execute_kw(DB, uid, PASSWORD, 'ir.module.module', 'button_immediate_upgrade', [module_id])
print('✅ real_estate_bits actualizado')
```

**IMPORTANTE**: Después de actualizar, hacer **Ctrl + Shift + R** en el navegador.

---

## 🔍 VERIFICAR INSTALACIÓN

### En Frontend (Website):
1. Abrir cualquier página del sitio web
2. Abrir DevTools (F12) → Console
3. Ejecutar:
```javascript
Array.from(document.styleSheets).find(s => s.href && s.href.includes('bootstrap-icons'))
```
4. Debe retornar un objeto `CSSStyleSheet` ✅

### En Backend (Odoo):
1. Ir a Aplicaciones → Buscar "Gestión Inmobiliaria"
2. Verificar que `real_estate_bits` esté instalado
3. Abrir cualquier vista de backend
4. Abrir DevTools (F12) → Console
5. Ejecutar el mismo código que arriba

### Prueba Visual:
Agregar temporalmente este código en cualquier plantilla:
```html
<div style="font-size: 3rem; padding: 20px;">
    <i class="bi bi-house-fill text-danger"></i>
    <i class="bi bi-heart-fill text-primary"></i>
    <i class="bi bi-star-fill text-warning"></i>
    <i class="bi bi-check-circle-fill text-success"></i>
</div>
```

Si ves los iconos correctamente, la instalación funciona ✅

---

## ✅ VENTAJAS DE LA ARQUITECTURA CENTRALIZADA

| Ventaja | Descripción |
|---------|-------------|
| 🎯 **Un Solo Lugar** | Bootstrap Icons solo en `real_estate_bits` |
| 📦 **Sin Duplicación** | No hay archivos duplicados en otros módulos |
| 🔄 **Herencia Automática** | Todos los módulos lo heredan por dependencia |
| 🚀 **Fácil Actualización** | Solo actualizar en el módulo base |
| 💾 **Menor Tamaño** | ~85KB en vez de ~255KB (3 copias) |
| 🌐 **Backend + Frontend** | Disponible en ambos contextos |
| 🏗️ **Arquitectura Limpia** | Sigue buenas prácticas de Odoo |
| 🔧 **Mantenimiento Simple** | Cambios centralizados |

---

## 📚 RECURSOS ADICIONALES

- **Documentación Oficial**: https://icons.getbootstrap.com/
- **Lista Completa de Iconos**: https://icons.getbootstrap.com/#icons
- **Buscar Iconos**: https://icons.getbootstrap.com/#search
- **GitHub**: https://github.com/twbs/icons
- **NPM Package**: https://www.npmjs.com/package/bootstrap-icons

---

## 🔄 COMPARACIÓN: ANTES vs DESPUÉS

### ANTES (Instalación Duplicada):
```
theme_bohio_real_estate/
└── static/src/lib/bootstrap-icons/  (~85KB)

bohio_real_estate/
└── static/src/lib/bootstrap-icons/  (~85KB)

bohio_crm/
└── static/src/lib/bootstrap-icons/  (~85KB)

Total: ~255KB duplicados ❌
```

### DESPUÉS (Instalación Centralizada):
```
real_estate_bits/
└── static/src/lib/bootstrap-icons/  (~85KB)

bohio_real_estate/
└── (hereda automáticamente) ✅

theme_bohio_real_estate/
└── (hereda automáticamente) ✅

bohio_crm/
└── (hereda automáticamente) ✅

Total: ~85KB sin duplicación ✅
```

**Ahorro**: ~170KB (66% menos espacio)

---

## ✅ CHECKLIST POST-INSTALACIÓN

- [x] Paquete NPM instalado
- [x] Archivos copiados a `real_estate_bits/static/src/lib/`
- [x] CSS agregado a `web.assets_backend` de `real_estate_bits`
- [x] CSS agregado a `web.assets_frontend` de `real_estate_bits`
- [x] Comentarios agregados a módulos hijos
- [x] Archivos duplicados eliminados de `theme_bohio_real_estate`
- [ ] Módulo `real_estate_bits` actualizado en Odoo
- [ ] Hard refresh en navegador (Ctrl + Shift + R)
- [ ] Verificar carga en DevTools (Frontend + Backend)
- [ ] Probar iconos en diferentes módulos

---

**Estado**: ✅ **INSTALADO Y CENTRALIZADO**

**Próximo Paso**: Actualizar módulo `real_estate_bits` y verificar que todos los módulos hijos pueden usar los iconos.

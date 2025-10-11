# IMÁGENES DE PROPIEDADES DESCARGADAS

## 📁 ESTRUCTURA DE CARPETAS

Cada carpeta representa una propiedad única identificada por su **código**.

```
property_images/
├── 8747/     (3 imágenes)  - Apartamento en Venta
├── 8935/     (26 imágenes) - Apartamento en Venta
└── [más propiedades...]
```

---

## 🏠 PROPIEDADES DESCARGADAS

### Propiedad 8747
- **Carpeta:** `8747/`
- **Total Imágenes:** 3
- **Tamaño Total:** 344.9 KB
- **Imagen Principal:** `800x600_347_GOPR4359.JPG` ⭐
- **URL Original:** https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8747

**Archivos:**
```
800x600_347_GOPR4359.JPG  (156.1 KB) ⭐ PRINCIPAL
800x600_GOPR4337.JPG      (106.7 KB)
800x600_GOPR4339.JPG      ( 82.1 KB)
```

---

### Propiedad 8935
- **Carpeta:** `8935/`
- **Total Imágenes:** 26
- **Tamaño Total:** 2.74 MB
- **Imagen Principal:** `800x600_GOPR6519.JPG` ⭐
- **URL Original:** https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8935

**Archivos:**
```
800x600_GOPR6519.JPG  (170.0 KB) ⭐ PRINCIPAL
800x600_GOPR6515.JPG  ( 97.8 KB)
800x600_GOPR6516.JPG  ( 85.6 KB)
... (23 imágenes más)
```

---

## 📊 ESTADÍSTICAS GENERALES

| Propiedad | Código | Imágenes | Tamaño Total | Imagen Principal |
|-----------|--------|----------|--------------|------------------|
| 8747      | 8747   | 3        | 344.9 KB     | 800x600_347_GOPR4359.JPG |
| 8935      | 8935   | 26       | 2.74 MB      | 800x600_GOPR6519.JPG |
| **TOTAL** | **2**  | **29**   | **3.08 MB**  | - |

---

## 🔍 CLASIFICACIÓN DE IMÁGENES

### Imagen Principal (⭐)
La **primera imagen** de cada carpeta es la imagen principal de la propiedad.

- `8747/800x600_347_GOPR4359.JPG` ⭐
- `8935/800x600_GOPR6519.JPG` ⭐

### Imágenes Secundarias
Todas las demás imágenes en orden de aparición en la página original.

---

## 📝 ORIGEN DE LAS IMÁGENES

Todas las imágenes fueron descargadas desde:
```
https://bohio.arrendasoft.co/img/big/
```

**Características:**
- Tamaño: 800x600 pixels
- Formato: JPG
- Nombres originales preservados

---

## 🚀 CÓMO USAR ESTAS IMÁGENES

### 1. Ver Imágenes Localmente

```bash
# Windows
start property_images\8747

# Linux/Mac
open property_images/8747
```

### 2. Subir a Odoo 18

```python
import os
import base64

property_code = "8747"
folder = f"property_images/{property_code}"

for filename in sorted(os.listdir(folder)):
    filepath = os.path.join(folder, filename)
    with open(filepath, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
        # Crear en property.image en Odoo
```

### 3. Copiar a Otro Destino

```bash
# Copiar carpeta completa
xcopy property_images D:\Backup\propiedades /E /I

# Copiar solo una propiedad
xcopy property_images\8747 D:\Propiedades\8747 /E /I
```

---

## 📋 NOTAS IMPORTANTES

### ⭐ Imagen Principal
- La primera imagen de cada carpeta es la **imagen principal**
- Se muestra primero en el listado
- Debe usarse como portada en Odoo (`is_cover=True`)

### 📁 Nombres de Archivo
- Se preservan nombres originales de arrendasoft.co
- Formato: `800x600_[NOMBRE].JPG`
- Algunos tienen prefijo hash: `800x600_[HASH]_[NOMBRE].JPG`

### 🔄 Re-descarga
- Si vuelves a ejecutar el script, sobrescribe las imágenes existentes
- Útil para actualizar si cambian en la web

---

## 🛠️ MANTENIMIENTO

### Agregar Más Propiedades

```bash
python download_property_images.py "URL_NUEVA_PROPIEDAD"
```

### Verificar Integridad

```bash
# Contar archivos por carpeta
find property_images -type f | wc -l

# Ver tamaño total
du -sh property_images/
```

### Limpiar Carpeta

```bash
# Eliminar una propiedad
rm -rf property_images/8747

# Eliminar todo
rm -rf property_images/*
```

---

## 📞 SOPORTE

Para descargar más propiedades, usar el script:

```bash
python download_property_images.py "URL_COMPLETA"
```

Consultar la guía completa en: [GUIA_DESCARGA_IMAGENES.md](../GUIA_DESCARGA_IMAGENES.md)

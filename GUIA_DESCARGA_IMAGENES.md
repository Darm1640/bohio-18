# GUÍA DE DESCARGA DE IMÁGENES POR CÓDIGO DE PROPIEDAD

## ✅ SISTEMA IMPLEMENTADO

Script automático que descarga imágenes de propiedades desde `bohioconsultores.com` y las organiza en carpetas locales clasificadas por **código de propiedad**.

---

## 📁 ESTRUCTURA DE CARPETAS

```
property_images/
├── 8747/
│   ├── 800x600_347_GOPR4359.JPG  ⭐ (PRINCIPAL)
│   ├── 800x600_GOPR4337.JPG
│   └── 800x600_GOPR4339.JPG
├── 8935/
│   ├── 800x600_GOPR6519.JPG  ⭐ (PRINCIPAL)
│   ├── 800x600_GOPR6515.JPG
│   └── ... (26 imágenes)
└── 8933/
    ├── 800x600_GOPR7041.JPG  ⭐ (PRINCIPAL)
    └── ... (23 imágenes)
```

**Lógica de Clasificación:**
- Cada propiedad tiene su carpeta con el **código extraído de la URL**
- La **primera imagen** se marca como PRINCIPAL ⭐
- Los archivos mantienen sus nombres originales de `bohio.arrendasoft.co`

---

## 🚀 USO DEL SCRIPT

### Sintaxis Básica

```bash
python download_property_images.py "URL_DE_LA_PROPIEDAD"
```

### Ejemplo Real - Propiedad 8747

```bash
python download_property_images.py "https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8747"
```

**Resultado:**
```
================================================================================
🏠 DESCARGADOR DE IMÁGENES DE PROPIEDADES
================================================================================

✅ Código de Propiedad: 8747

📥 Obteniendo página: https://bohioconsultores.com/detalle-propiedad/?...

📸 Total imágenes encontradas: 3

📁 Carpeta de descarga: C:\...\property_images\8747
📥 Descargando 3 imágenes...

    1. ⭐ PRINCIPAL 800x600_347_GOPR4359.JPG     (156.1 KB)
    2.             800x600_GOPR4337.JPG          (106.7 KB)
    3.             800x600_GOPR4339.JPG          ( 82.1 KB)

✅ 3 de 3 imágenes descargadas exitosamente

📊 RESUMEN:
   Código Propiedad: 8747
   Total Imágenes: 3
   Carpeta Local: C:\...\property_images\8747
   Tamaño Total: 344.9 KB (0.34 MB)
   Imagen Principal: 800x600_347_GOPR4359.JPG
```

---

## 🔍 CÓMO FUNCIONA LA EXTRACCIÓN DEL CÓDIGO

### Patrón de URLs

El script detecta automáticamente el código desde diferentes formatos:

```
✅ https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8747
   → Código: 8747

✅ https://bohioconsultores.com/detalle-propiedad/?Casa-en-Arriendo-9123
   → Código: 9123

✅ https://bohioconsultores.com/detalle-propiedad/?Lote-en-Venta%20y%20Arriendo-7856
   → Código: 7856
```

**Lógica:** Busca el número después del **último guion** en la URL.

---

## 📥 EJEMPLOS DE USO

### 1. Descargar Una Propiedad

```bash
python download_property_images.py "https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8747"
```

### 2. Verificar Imágenes Descargadas

```bash
# Windows
dir property_images\8747

# Linux/Mac
ls -lh property_images/8747
```

### 3. Procesar Múltiples Propiedades (Batch)

Crear archivo `descargar_multiples.bat`:

```batch
@echo off
python download_property_images.py "https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8747"
python download_property_images.py "https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8935"
python download_property_images.py "https://bohioconsultores.com/detalle-propiedad/?Casa-en-Venta-8933"
pause
```

Ejecutar:
```bash
descargar_multiples.bat
```

---

## 📋 CARACTERÍSTICAS DEL SISTEMA

### ✅ Clasificación Automática

| Característica | Descripción |
|----------------|-------------|
| **Código de Propiedad** | Extraído automáticamente desde URL |
| **Carpeta Individual** | Una carpeta por propiedad: `property_images/[CODIGO]/` |
| **Imagen Principal** | Primera imagen marcada con ⭐ |
| **Nombres Originales** | Se preservan nombres de `bohio.arrendasoft.co` |
| **Secuencia Ordenada** | Imágenes numeradas en orden de aparición |

### ✅ Información Detallada

- **Tamaño de cada archivo** en KB
- **Tamaño total** de la descarga
- **Contador de progreso** (1/10, 2/10, etc.)
- **Ruta absoluta** de la carpeta creada
- **Manejo de errores** individual por imagen

### ✅ Validaciones

- ✅ Verifica que la URL sea válida
- ✅ Verifica que el código se pueda extraer
- ✅ Crea carpetas automáticamente si no existen
- ✅ Maneja errores de descarga sin detener el proceso
- ✅ Reporta estadísticas finales

---

## 🔧 CASOS DE USO AVANZADOS

### 1. Cambiar Carpeta de Descarga

Editar el script `download_property_images.py`:

```python
# Línea 297 - Cambiar directorio de descarga
downloader = PropertyImageDownloader(download_dir="C:\\MisImagenes")
```

### 2. Integrar con Odoo

Después de descargar, usar el script de migración:

```python
# Las imágenes ya están locales en property_images/8747/
# Puedes leerlas desde allí para subirlas a Odoo

import os
import base64

property_id = "8747"
image_folder = f"property_images/{property_id}"

for filename in os.listdir(image_folder):
    filepath = os.path.join(image_folder, filename)
    with open(filepath, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
        # Subir a Odoo...
```

### 3. Verificar Calidad de Imágenes

```bash
# Ver tamaño de todas las imágenes de una propiedad
cd property_images/8747
ls -lh  # Linux/Mac
dir     # Windows
```

### 4. Script de Respaldo

```bash
# Copiar todas las carpetas descargadas
xcopy property_images D:\Respaldo\propiedades /E /I
```

---

## 🎯 VENTAJAS DE ESTE SISTEMA

### 1. **Organización Automática**
- ✅ No necesitas crear carpetas manualmente
- ✅ Código de propiedad como nombre de carpeta
- ✅ Fácil de encontrar imágenes por código

### 2. **Trazabilidad**
- ✅ Cada carpeta representa una propiedad única
- ✅ Primera imagen siempre identificada como PRINCIPAL
- ✅ Nombres originales preservados

### 3. **Escalabilidad**
- ✅ Puede procesar 1 o 1000 propiedades
- ✅ No hay límite de imágenes por propiedad
- ✅ Descarga paralela posible con modificaciones

### 4. **Flexibilidad**
- ✅ Funciona con cualquier URL de bohioconsultores.com
- ✅ Detecta código automáticamente
- ✅ Fácil de integrar con otros sistemas

---

## 📊 EJEMPLO COMPLETO PASO A PASO

### Escenario: Descargar imágenes de 3 propiedades

**Códigos:** 8747, 8935, 8933

#### Paso 1: Preparar URLs

```
https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8747
https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8935
https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8933
```

#### Paso 2: Ejecutar Script

```bash
python download_property_images.py "https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8747"
```

#### Paso 3: Verificar Resultado

```
property_images/
└── 8747/
    ├── 800x600_347_GOPR4359.JPG  ⭐
    ├── 800x600_GOPR4337.JPG
    └── 800x600_GOPR4339.JPG
```

#### Paso 4: Repetir para otras propiedades

```bash
python download_property_images.py "https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8935"
python download_property_images.py "https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8933"
```

#### Resultado Final

```
property_images/
├── 8747/ (3 imágenes)
├── 8935/ (26 imágenes)
└── 8933/ (23 imágenes)

Total: 3 propiedades, 52 imágenes
```

---

## 🛠️ TROUBLESHOOTING

### Error: No se pudo extraer código

```
❌ No se pudo extraer ID de propiedad desde: [URL]
```

**Solución:** Verificar que la URL tenga el formato correcto:
- Debe terminar en `-[NUMERO]`
- Ejemplo correcto: `?Apartamento-en-Venta-8747`

### Error: No se pueden descargar imágenes

```
❌ Error descargando 800x600_XXXX.JPG: HTTPError 404
```

**Soluciones:**
1. Verificar que la URL de la propiedad sea válida
2. Verificar conexión a internet
3. La imagen puede haber sido eliminada de arrendasoft.co

### Error: Carpeta no se crea

```
❌ Permission denied: property_images/8747
```

**Solución:** Ejecutar desde una carpeta con permisos de escritura

---

## 📝 NOTAS IMPORTANTES

### ⚠️ Consideraciones

1. **Conexión a Internet:** Necesaria para descargar
2. **Espacio en Disco:** Calcular ~100-200 KB por imagen
3. **Tiempo de Descarga:** Depende de cantidad de imágenes
4. **URLs Duplicadas:** Si ejecutas 2 veces, sobrescribe imágenes

### 💡 Recomendaciones

1. **Verificar URL:** Copiar y pegar desde navegador
2. **Usar comillas:** Siempre encerrar URL entre comillas `"..."`
3. **Revisar resultado:** Verificar carpeta creada después de descarga
4. **Backup regular:** Respaldar carpeta `property_images/` periódicamente

---

## 🔄 INTEGRACIÓN CON ODOO 18

Una vez descargadas las imágenes localmente, puedes:

### 1. Subir manualmente a Odoo
- Ir a la propiedad en Odoo
- Usar el modelo `property.image`
- Subir desde `property_images/[CODIGO]/`

### 2. Usar script de migración automática
```python
# Ver: migrate_property_8747_images.py (se genera automáticamente)
# Adaptado para leer desde carpeta local
```

### 3. Crear batch de migración
```python
# migrate_from_local.py
import os
import base64

for property_code in os.listdir('property_images'):
    folder = f'property_images/{property_code}'
    # Procesar cada imagen...
```

---

## ✅ CONCLUSIÓN

Este sistema permite:

- ✅ **Descargar automáticamente** imágenes desde bohioconsultores.com
- ✅ **Clasificar por código** de propiedad extraído de URL
- ✅ **Organizar localmente** en carpetas individuales
- ✅ **Identificar imagen principal** automáticamente
- ✅ **Preparar para migración** a Odoo 18

**Comando Principal:**
```bash
python download_property_images.py "URL_COMPLETA_DE_PROPIEDAD"
```

**Resultado:** Carpeta `property_images/[CODIGO]/` con todas las imágenes descargadas y organizadas.

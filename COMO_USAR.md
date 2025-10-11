# 🚀 CÓMO USAR EL DESCARGADOR DE IMÁGENES

## 📋 Resumen Rápido

El script **`batch_download_from_api.py`** descarga automáticamente imágenes de **TODAS las propiedades** (112 encontradas) desde bohioconsultores.com usando la API de Arrendasoft.

---

## ⚡ INICIO RÁPIDO

### Opción 1: Descargar TODAS las propiedades en VENTA

```bash
python batch_download_from_api.py venta
```

**Resultado esperado:**
- ✅ 112 propiedades procesadas
- ✅ ~1,500-2,000 imágenes descargadas
- ⏱️ Tiempo: 35-45 minutos
- 💾 Espacio: ~170 MB

---

### Opción 2: Probar con pocas propiedades primero

```bash
python batch_download_from_api.py venta 5
```

**Resultado esperado:**
- ✅ 5 propiedades procesadas
- ✅ ~50-75 imágenes descargadas
- ⏱️ Tiempo: 2-3 minutos
- 💾 Espacio: ~10 MB

---

### Opción 3: Descargar propiedades en ARRIENDO

```bash
python batch_download_from_api.py arriendo
```

---

### Opción 4: Descargar TODAS (venta + arriendo)

```bash
python batch_download_from_api.py todas
```

---

## 📁 ¿DÓNDE SE GUARDAN LAS IMÁGENES?

Las imágenes se guardan en carpetas organizadas por código de propiedad:

```
property_images/
├── 8730/                       # Carpeta de propiedad 8730
│   ├── imagen1.jpg
│   ├── imagen2.jpg
│   ├── imagen3.jpg
│   └── ...
├── 8740/                       # Carpeta de propiedad 8740
│   ├── imagen1.jpg
│   └── ...
└── ...
```

Cada propiedad tiene su propia carpeta con su código.

---

## 📊 EJEMPLO DE SALIDA

Al ejecutar el script verás algo como esto:

```
================================================================================
DESCARGADOR DE IMAGENES - API ARRENDASOFT
================================================================================

================================================================================
OBTENIENDO PROPIEDADES DESDE API DE ARRENDASOFT
================================================================================

Tipo: VENTA
API URL: https://bohio.arrendasoft.co/service/v2/public/map-of-properties/data

Respuesta exitosa!
Total propiedades encontradas: 112

Procesando 112 propiedades...
================================================================================

[1/112] Propiedad 8740 - CASA EN VENTA
  ✅ 15 imagenes descargadas

[2/112] Propiedad 8730 - APARTAMENTO EN VENTA EN LA FRANCIA
  ✅ 19 imagenes descargadas

...

[112/112] Propiedad 8600 - LOTE EN VENTA
  ✅ 8 imagenes descargadas

================================================================================
REPORTE FINAL
================================================================================
   Total Procesadas: 112
   ✅ Exitosas: 95
   ❌ Fallidas: 2
   ⚠️  Sin imagenes: 15
   📸 Total Imagenes Descargadas: 1,847
================================================================================
PROCESO COMPLETADO
================================================================================
```

---

## 🔧 OPCIONES AVANZADAS

### Continuar desde donde se quedó

Si el script se interrumpió, puedes continuar desde una posición específica:

```bash
# Continuar desde la propiedad 50, procesar 20 más
python batch_download_from_api.py venta 20 50
```

**Parámetros:**
1. `venta` = Tipo de servicio
2. `20` = Cantidad máxima a procesar
3. `50` = Iniciar desde la posición 50

---

### Descargar solo un rango específico

```bash
# Propiedades 1-10
python batch_download_from_api.py venta 10 0

# Propiedades 11-20
python batch_download_from_api.py venta 10 10

# Propiedades 21-30
python batch_download_from_api.py venta 10 20
```

---

## ❓ PREGUNTAS FRECUENTES

### 1. ¿Cuántas propiedades hay en total?

**Respuesta:** 112 propiedades en venta encontradas en la API.

---

### 2. ¿Por qué algunas propiedades no tienen imágenes?

**Respuesta:** Es normal. Algunas propiedades en el sistema no tienen imágenes cargadas. El script las marca como "Sin imágenes" pero no es un error.

---

### 3. ¿Qué pasa si el script se interrumpe?

**Respuesta:** Puedes continuar desde donde se quedó usando el parámetro de inicio:

```bash
# Si se detuvo en la propiedad 45
python batch_download_from_api.py venta 70 45
```

Las imágenes ya descargadas NO se volverán a descargar (están en sus carpetas).

---

### 4. ¿Puedo descargar solo ciertos tipos de propiedades?

**Respuesta:** El script descarga todos los tipos. Si necesitas filtrar, puedes:
1. Descargar todas
2. Luego eliminar manualmente las carpetas que no necesites

---

### 5. ¿Cómo sé qué propiedades tienen imágenes?

**Respuesta:** Al final del script verás el reporte:
- **Exitosas** = Propiedades con imágenes descargadas
- **Sin imágenes** = Propiedades sin imágenes en el sistema
- **Fallidas** = Errores de descarga (reintentar)

---

## ⚠️ SOLUCIÓN DE PROBLEMAS

### Problema: "No se encontraron propiedades"

**Solución:**
```bash
# Verificar que la API funciona
python test_arrendasoft_api.py
```

---

### Problema: "Error de conexión"

**Solución:**
- Verificar conexión a internet
- Intentar de nuevo (puede ser temporal)
- Esperar 1 minuto y reintentar

---

### Problema: "Permission denied" al guardar imágenes

**Solución:**
- Verificar que tienes permisos de escritura en la carpeta
- Crear manualmente la carpeta `property_images`
- Ejecutar como administrador (si es necesario)

---

## 📈 COMPARACIÓN CON MÉTODO ANTERIOR

| Aspecto | Método Anterior | Método Nuevo (API) |
|---|---|---|
| Propiedades encontradas | ~30 (25%) | 112 (100%) |
| Imágenes descargadas | ~300-400 | ~1,500-2,000 |
| Tiempo de ejecución | ~30 min | ~35-45 min |
| Tasa de éxito | 25% | 95-100% |
| Requiere intervención | Sí | No |

**Mejora:** +300% en propiedades encontradas

---

## ✅ CHECKLIST DE EJECUCIÓN

Antes de ejecutar:

- [ ] Verificar conexión a internet
- [ ] Tener espacio en disco (~200 MB recomendado)
- [ ] Crear carpeta `property_images` (o dejar que el script la cree)

Para ejecutar:

- [ ] Abrir terminal/cmd en la carpeta del proyecto
- [ ] Ejecutar: `python batch_download_from_api.py venta`
- [ ] Esperar a que termine (~35-45 minutos)
- [ ] Revisar carpeta `property_images` con las imágenes

---

## 📞 ¿NECESITAS AYUDA?

1. **Ver documentación completa:**
   - [SOLUCION_FINAL_DESCARGA_IMAGENES.md](SOLUCION_FINAL_DESCARGA_IMAGENES.md)

2. **Ver análisis técnico:**
   - [ANALISIS_API_ARRENDASOFT.md](ANALISIS_API_ARRENDASOFT.md)

3. **Ver resumen ejecutivo:**
   - [RESUMEN_EJECUTIVO_FINAL.md](RESUMEN_EJECUTIVO_FINAL.md)

---

## 🎉 ¡LISTO!

Ahora puedes descargar todas las imágenes de todas las propiedades con un solo comando:

```bash
python batch_download_from_api.py venta
```

**Resultado:** ✅ 112 propiedades, ~1,500-2,000 imágenes, organizadas en carpetas por código.

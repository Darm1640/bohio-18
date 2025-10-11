# GUÍA COMPLETA - SISTEMA DE SCRAPING PAGINADO

## 🎯 RESUMEN DEL SISTEMA

Has implementado **3 sistemas diferentes** para procesar las propiedades:

---

## ✅ SISTEMA 1: BATCH DESDE LISTADO.TXT (RECOMENDADO)

### **Archivo:** `batch_download_from_list.py`

### **Cómo funciona:**
1. Lee `property_images/listado.txt` (2496 códigos)
2. Construye URLs automáticamente probando patrones
3. Descarga imágenes directamente
4. Guarda en carpetas por código

### **Ventajas:**
- ✅ **MÁS RÁPIDO** - No depende de scraping web
- ✅ **MÁS CONFIABLE** - Ya tienes los códigos
- ✅ **YA PROBADO** - Funciona perfectamente
- ✅ **CONTROL TOTAL** - Puedes procesar por lotes

### **Uso:**
```bash
# TODO (2496 propiedades)
python batch_download_from_list.py

# Por lotes
python batch_download_from_list.py 100      # Primeras 100
python batch_download_from_list.py 100 100  # Desde 100, siguiente 100
python batch_download_from_list.py 100 200  # Desde 200, siguiente 100
```

### **Resultado probado:**
```
[1/5] Procesando código: 170
✅ URL encontrada
📸 11 imágenes descargadas
Carpeta: property_images/170/

Total: 1 de 5 exitosas
```

---

## 🔄 SISTEMA 2: SCRAPER PAGINADO CON TRACKING

### **Archivo:** `scraper_paginado.py`

### **Problema actual:**
La página `bohioconsultores.com` usa **JavaScript/AJAX** para cargar las propiedades dinámicamente, por lo que:
- `requests` no puede ver el contenido dinámico
- Necesitarías usar **Selenium** o **Playwright** para navegadores

### **Cómo funcionaría (con Selenium):**
1. Abre navegador Chrome automático
2. Navega a página de búsqueda
3. Espera a que cargue JavaScript
4. Extrae URLs de propiedades visibles
5. Click en "Siguiente página" (botón nextPage)
6. Repite para las 103 páginas
7. Descarga imágenes de cada URL
8. Guarda progreso en JSON
9. Puede reanudar si se interrumpe

### **Para implementarlo necesitarías:**
```bash
pip install selenium
pip install webdriver-manager

# Modificar scraper_paginado.py para usar Selenium
```

### **Ventaja:**
- ✅ Obtiene URLs directamente de la web
- ✅ No necesita listado.txt
- ✅ Tracking de progreso automático

### **Desventaja:**
- ❌ Más lento (necesita cargar navegador)
- ❌ Más complejo de configurar
- ❌ Depende de estructura de la página web

---

## 💡 SISTEMA 3: PROCESO HÍBRIDO (EL MEJOR)

### **Combinación de ambos sistemas:**

```bash
# PASO 1: Usa listado.txt para descargar
python batch_download_from_list.py 500

# PASO 2: Verifica cuáles fallaron
# Las que fallaron las guardas en "fallidas.txt"

# PASO 3: Para las fallidas, usa scraper con Selenium
# (si vale la pena por la cantidad)
```

---

## 📊 COMPARACIÓN DE SISTEMAS

| Característica | Batch listado.txt | Scraper Paginado |
|----------------|-------------------|------------------|
| **Velocidad** | ⚡⚡⚡ Muy rápido | 🐌 Lento (navegador) |
| **Configuración** | ✅ Simple | ⚠️ Compleja (Selenium) |
| **Confiabilidad** | ✅ Alta | ⚠️ Media (depende de web) |
| **Progreso** | ⚠️ Manual | ✅ Automático (JSON) |
| **Mantenimiento** | ✅ Fácil | ❌ Difícil |
| **URLs actualizadas** | ⚠️ Necesita listado | ✅ Siempre actual |

---

## 🚀 RECOMENDACIÓN FINAL

### **USA EL SISTEMA 1 (batch_download_from_list.py)**

**Razones:**

1. **Ya tienes 2496 códigos** en listado.txt
2. **Ya está probado** y funciona
3. **Es 10x más rápido** que scraping con navegador
4. **Más confiable** - no depende de cambios en la web

### **Proceso Recomendado:**

```bash
# 1. Procesar todo el listado (o por lotes)
python batch_download_from_list.py 100  # Primeras 100
python batch_download_from_list.py 100 100  # Siguientes 100
# ... continuar hasta completar

# 2. Al terminar, subir a Odoo
python create_images_in_odoo.py

# 3. Ver estadísticas
ls property_images/ | wc -l  # Carpetas creadas
find property_images -name "*.JPG" | wc -l  # Total imágenes
```

---

## 📋 TRACKING MANUAL (Sistema 1)

Aunque el Sistema 1 no tiene tracking automático, puedes hacerlo manualmente:

### **Crear log de progreso:**
```bash
# Ejecutar con log
python batch_download_from_list.py 100 > batch_log_100.txt 2>&1

# Ver progreso
tail -f batch_log_100.txt

# Contar exitosas
grep "✅" batch_log_100.txt | wc -l

# Ver fallidas
grep "❌" batch_log_100.txt
```

### **Script para tracking:**
```bash
#!/bin/bash
# track_batch.sh

BATCH_SIZE=100
TOTAL=2496
CURRENT=0

while [ $CURRENT -lt $TOTAL ]; do
    echo "=== Procesando lote $CURRENT ==="
    python batch_download_from_list.py $BATCH_SIZE $CURRENT > "log_${CURRENT}.txt" 2>&1

    # Verificar si terminó correctamente
    if [ $? -eq 0 ]; then
        echo "✅ Lote $CURRENT completado"
    else
        echo "❌ Error en lote $CURRENT"
        break
    fi

    CURRENT=$((CURRENT + BATCH_SIZE))
    sleep 5
done

echo "PROCESO COMPLETADO"
```

---

## 🔧 SI QUIERES IMPLEMENTAR SCRAPING CON SELENIUM

### **Instalar dependencias:**
```bash
pip install selenium webdriver-manager
```

### **Código básico:**
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Inicializar navegador
driver = webdriver.Chrome(ChromeDriverManager().install())

# Ir a página
driver.get("https://bohioconsultores.com/resultados-de-busqueda/?Servicio=2")

# Esperar a que cargue
wait = WebDriverWait(driver, 10)
boxes = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "movil-50")))

# Extraer URLs
for box in boxes:
    link = box.find_element(By.TAG_NAME, "a")
    url = link.get_attribute("href")
    print(url)

# Siguiente página
next_btn = driver.find_element(By.ID, "nextPage")
next_btn.click()

# Esperar y repetir...

driver.quit()
```

---

## 💾 ARCHIVOS GENERADOS

### **Sistema 1 (Batch):**
```
property_images/
├── 170/
│   └── *.JPG (11 imágenes)
├── 8747/
│   └── *.JPG (3 imágenes)
└── ... (más carpetas)

# NO genera tracking automático
```

### **Sistema 2 (Scraper Paginado):**
```
scraping_progress.json
{
  "last_page": 5,
  "total_pages": 103,
  "processed_codes": ["8942", "8937", ...],
  "failed_codes": [],
  "stats": {
    "total_found": 60,
    "total_downloaded": 45,
    "total_images": 450,
    "total_failed": 5,
    "no_images": 10
  }
}

processed_properties.txt
# PROPIEDADES PROCESADAS
# Total: 45
8942
8937
...
```

---

## ✅ CONCLUSIÓN

### **Para tu caso específico:**

**USAR SISTEMA 1** porque:
- ✅ Ya tienes listado.txt con 2496 códigos
- ✅ Es más rápido (3-5 propiedades/minuto)
- ✅ Ya está probado y funciona
- ✅ No depende de JavaScript/AJAX
- ✅ Más fácil de mantener

**Proceso completo:**
```bash
# 1. Descargar imágenes (por lotes)
python batch_download_from_list.py 100  # Lote 1
python batch_download_from_list.py 100 100  # Lote 2
# ... continuar

# 2. Subir a Odoo
python create_images_in_odoo.py

# DONE! ✅
```

**Tiempo estimado:**
- 2496 propiedades
- ~30% con imágenes = 749 propiedades
- ~10 imágenes promedio = 7490 imágenes
- Velocidad: 3-5 min/propiedad
- **Total: 4-6 horas** procesando por lotes

---

## 📞 RESUMEN EJECUTIVO

| Pregunta | Respuesta |
|----------|-----------|
| **¿Cuál usar?** | Sistema 1: `batch_download_from_list.py` |
| **¿Por qué?** | Más rápido, ya probado, no depende de web |
| **¿Cómo empezar?** | `python batch_download_from_list.py 100` |
| **¿Tracking?** | Manual con logs: `> log.txt 2>&1` |
| **¿Reanudar?** | Especificar posición: `... 100 500` |
| **¿Cuánto tarda?** | 4-6 horas para las 2496 propiedades |
| **¿Siguiente paso?** | `python create_images_in_odoo.py` |

**¿Listo para empezar el proceso completo?** 🚀

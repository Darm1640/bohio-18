# ✅ SISTEMA LISTO - COMANDOS PARA EJECUTAR

## 📦 DEPENDENCIAS INSTALADAS

```
✅ Selenium 4.36.0
✅ webdriver-manager 4.0.2
✅ beautifulsoup4
✅ requests
```

---

## 🎯 PRUEBA EXITOSA (10 PROPIEDADES)

```
Total Procesadas: 10
✅ Exitosas: 3 (códigos: 170, 195, 197)
📸 Total Imágenes: 16
⚠️  Sin imágenes: 7

Carpetas creadas:
- property_images/170/ (11 imágenes)
- property_images/195/ (2 imágenes)
- property_images/197/ (3 imágenes)
```

---

## 🚀 COMANDOS PARA PROCESO COMPLETO

### OPCIÓN 1: Todo de una vez (4-6 horas)

```bash
cd "C:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18"
python batch_download_from_list.py
```

### OPCIÓN 2: Por lotes de 100 (RECOMENDADO)

```bash
cd "C:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18"

# Lote 1: Propiedades 0-99
python batch_download_from_list.py 100

# Lote 2: Propiedades 100-199
python batch_download_from_list.py 100 100

# Lote 3: Propiedades 200-299
python batch_download_from_list.py 100 200

# Lote 4: Propiedades 300-399
python batch_download_from_list.py 100 300

# ... continuar hasta 2496
```

### OPCIÓN 3: Lotes grandes (500)

```bash
# Lote 1
python batch_download_from_list.py 500

# Lote 2
python batch_download_from_list.py 500 500

# Lote 3
python batch_download_from_list.py 500 1000

# Lote 4
python batch_download_from_list.py 500 1500

# Lote 5
python batch_download_from_list.py 496 2000
```

---

## 📊 VERIFICAR PROGRESO

### Ver carpetas creadas
```bash
ls property_images/ | grep -E '^[0-9]+$' | wc -l
```

### Contar imágenes totales
```bash
find property_images -type f \( -iname "*.jpg" -o -iname "*.png" \) | wc -l
```

### Ver tamaño total
```bash
du -sh property_images/
```

### Carpetas con más imágenes
```bash
for dir in property_images/*/; do
    count=$(ls -1 "$dir" 2>/dev/null | wc -l)
    echo "$count $dir"
done | sort -rn | head -20
```

---

## 🎯 DESPUÉS DE DESCARGAR: SUBIR A ODOO

```bash
python create_images_in_odoo.py
```

**El script:**
- Lee carpetas en `property_images/`
- Busca cada propiedad en Odoo por código
- Sube todas las imágenes
- Marca primera como PRINCIPAL ⭐
- Clasifica automáticamente

---

## 📝 CREAR LOGS DEL PROCESO

### Con log en archivo
```bash
python batch_download_from_list.py 100 > batch_log_0-100.txt 2>&1
```

### Ver log en tiempo real
```bash
# Terminal 1
python batch_download_from_list.py 100 | tee batch_log.txt

# Terminal 2
tail -f batch_log.txt
```

---

## 🔄 SCRIPT AUTOMATIZADO (OPCIONAL)

### Windows (batch_all.bat)
```batch
@echo off
echo ========================================
echo DESCARGA AUTOMATICA EN LOTES
echo ========================================

set BATCH_SIZE=100
set START=0

:loop
if %START% GEQ 2496 goto end

echo.
echo === Lote desde %START% ===
python batch_download_from_list.py %BATCH_SIZE% %START% > "log_%START%.txt" 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo ERROR en lote %START%
    pause
    goto end
)

set /a START=%START%+%BATCH_SIZE%
timeout /t 5
goto loop

:end
echo.
echo ========================================
echo PROCESO COMPLETADO
echo ========================================
pause
```

**Ejecutar:**
```bash
batch_all.bat
```

---

## ⚙️ CONFIGURACIÓN ODOO

Antes de ejecutar `create_images_in_odoo.py`, verificar configuración en el archivo (líneas 276-279):

```python
ODOO_URL = 'http://localhost:8069'  # ← Cambiar si necesario
ODOO_DB = 'bohio_db'                 # ← Tu base de datos
ODOO_USER = 'admin'                  # ← Tu usuario
ODOO_PASS = 'admin'                  # ← Tu contraseña
```

---

## 📊 ESTIMACIONES

### Basado en prueba de 10 propiedades:

| Métrica | Valor |
|---------|-------|
| **Propiedades con imágenes** | 30% (3 de 10) |
| **Promedio imágenes/propiedad** | 5.3 (16 ÷ 3) |
| **Velocidad** | ~30 seg/propiedad |

### Para 2496 propiedades:

| Métrica | Estimado |
|---------|----------|
| **Con imágenes** | ~749 propiedades (30%) |
| **Total imágenes** | ~3,970 imágenes |
| **Tiempo descarga** | 3-4 horas |
| **Espacio disco** | ~400-800 MB |
| **Tiempo subida Odoo** | 2-3 horas |
| **TOTAL** | **5-7 horas** |

---

## 🎯 PLAN DE EJECUCIÓN RECOMENDADO

### DÍA 1: Descarga por lotes

```bash
# Mañana: Lotes 1-5 (500 propiedades)
python batch_download_from_list.py 100
python batch_download_from_list.py 100 100
python batch_download_from_list.py 100 200
python batch_download_from_list.py 100 300
python batch_download_from_list.py 100 400

# Tarde: Lotes 6-10 (500 propiedades)
python batch_download_from_list.py 100 500
python batch_download_from_list.py 100 600
python batch_download_from_list.py 100 700
python batch_download_from_list.py 100 800
python batch_download_from_list.py 100 900
```

### DÍA 2: Continuar descarga

```bash
# Completar hasta 2496
python batch_download_from_list.py 100 1000
python batch_download_from_list.py 100 1100
# ... continuar
python batch_download_from_list.py 96 2400  # Últimas 96
```

### DÍA 3: Subir a Odoo

```bash
python create_images_in_odoo.py
```

---

## 🛠️ TROUBLESHOOTING

### Error: "No module named 'selenium'"
```bash
python -m pip install --user selenium webdriver-manager
```

### Error: "Connection timeout"
```bash
# Aumentar timeout en download_property_images.py línea 53
response = requests.get(url, timeout=30)  # Cambiar a 60
```

### Error: "Propiedad no encontrada en Odoo"
```bash
# Verificar códigos en Odoo
# Ajustar búsqueda en create_images_in_odoo.py
```

### Verificar progreso si se interrumpe
```bash
# Ver últimas carpetas creadas
ls -lt property_images/ | head -20

# Ver último código procesado
ls property_images/ | grep -E '^[0-9]+$' | sort -n | tail -1

# Continuar desde ahí
python batch_download_from_list.py 100 [ULTIMO_CODIGO]
```

---

## ✅ CHECKLIST PRE-EJECUCIÓN

- [ ] Python 3.x instalado
- [ ] Dependencias instaladas (selenium, requests, beautifulsoup4)
- [ ] Archivo `property_images/listado.txt` existe (2496 códigos)
- [ ] Conexión a internet estable
- [ ] Espacio en disco suficiente (~1 GB libre)
- [ ] Odoo corriendo si vas a subir después
- [ ] Configuración de Odoo verificada

---

## 🎉 COMANDO RÁPIDO PARA EMPEZAR

```bash
# Ve al directorio
cd "C:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18"

# Ejecuta primer lote de 100
python batch_download_from_list.py 100

# Espera resultado (~30-40 minutos)
# Luego continúa con siguiente lote
```

---

## 📞 COMANDOS DE AYUDA

```bash
# Ver ayuda del script
python batch_download_from_list.py --help

# Ver versión de Python
python --version

# Ver paquetes instalados
pip list | grep -i selenium

# Ver estructura de archivos
tree property_images -L 2
```

---

## ✅ ESTADO ACTUAL

```
✅ Dependencias instaladas
✅ Sistema probado (10 propiedades, 3 exitosas)
✅ Estructura funcionando correctamente
✅ Listo para proceso completo de 2496 propiedades

SIGUIENTE COMANDO:
  python batch_download_from_list.py 100
```

**¿Listo para empezar?** 🚀

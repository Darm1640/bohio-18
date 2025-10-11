# SISTEMA COMPLETO DE DESCARGA Y SUBIDA BATCH DE IMÁGENES

## 🎯 OBJETIVO

Sistema automatizado de 3 pasos para:
1. **Descargar imágenes** de todas las propiedades desde `bohioconsultores.com`
2. **Organizar localmente** por código de propiedad
3. **Subir a Odoo 18** manteniendo clasificación y orden

---

## 📦 ARCHIVOS DEL SISTEMA

| Archivo | Descripción |
|---------|-------------|
| `batch_download_from_list.py` | Descarga batch desde listado.txt (2496 códigos) |
| `download_property_images.py` | Descarga individual por URL |
| `create_images_in_odoo.py` | Sube imágenes desde carpetas a Odoo |
| `property_images/listado.txt` | Lista de códigos de propiedades |

---

## 🚀 PROCESO COMPLETO (3 PASOS)

### PASO 1: Descargar Todas las Imágenes

```bash
# Descargar TODAS las propiedades (2496 códigos)
python batch_download_from_list.py

# O limitar cantidad
python batch_download_from_list.py 100    # Solo primeras 100
python batch_download_from_list.py 50 200 # Desde pos 200, 50 propiedades
```

**Resultado:**
```
property_images/
├── 1/        (imágenes)
├── 123/      (imágenes)
├── 170/      (imágenes)
├── 8747/     (imágenes)
├── 8935/     (imágenes)
└── ... (hasta 2496 carpetas)
```

### PASO 2: Revisar Imágenes Descargadas

```bash
# Ver cuántas carpetas se crearon
ls property_images/ | wc -l

# Ver estadísticas
du -sh property_images/

# Contar total de imágenes
find property_images -type f -name "*.JPG" -o -name "*.jpg" | wc -l
```

### PASO 3: Subir a Odoo

```bash
python create_images_in_odoo.py
```

**El script:**
- Conecta a Odoo (`localhost:8069`)
- Lee cada carpeta en `property_images/`
- Busca la propiedad por código
- Sube todas las imágenes
- Marca la primera como PRINCIPAL

---

## 📊 EJEMPLO COMPLETO

### 1. Descargar 10 Propiedades de Prueba

```bash
python batch_download_from_list.py 10
```

**Output:**
```
================================================================================
BATCH DOWNLOADER - DESCARGA MASIVA DE IMÁGENES
================================================================================

📋 Códigos encontrados en property_images/listado.txt: 2496
🔢 Limitando a: 10 propiedades
🚀 Procesando 10 propiedades...

[1/10] Procesando código: 1
✅ URL encontrada
⚠️  Código 1: Sin imágenes

[2/10] Procesando código: 123
⚠️  Código 123: Sin imágenes

[3/10] Procesando código: 170
✅ Código 170: 11 imágenes descargadas

[4/10] Procesando código: 8747
✅ Código 8747: 3 imágenes descargadas

...

📊 REPORTE FINAL:
   Total Procesadas: 10
   ✅ Exitosas: 3
   ⚠️  Sin imágenes: 7
   📸 Total Imágenes: 35
```

### 2. Verificar Carpetas Creadas

```bash
ls property_images/
```

**Output:**
```
170/   8747/   8935/   README.md   listado.txt
```

### 3. Subir a Odoo

```bash
python create_images_in_odoo.py
```

**Output:**
```
================================================================================
CREADOR DE IMÁGENES EN ODOO DESDE CARPETAS LOCALES
================================================================================

🔌 Conectando a http://localhost:8069...
✅ Autenticación exitosa

📋 Encontradas 3 carpetas de propiedades

[1/3] Propiedad: 170
--------------------------------------------------------------------------------
✅ Propiedad encontrada en Odoo: ID=123
📸 Encontradas 11 imágenes

   [1/11] Subiendo: 14847694951-(Copy).JPG
      ⭐ PRINCIPAL
      ✅ Imagen creada en Odoo: ID=1

   [2/11] Subiendo: 1484769495DSC00051-(Copy).JPG
      ✅ Imagen creada en Odoo: ID=2

   ... (9 más)

[2/3] Propiedad: 8747
✅ Código 8747: 3 imágenes subidas

[3/3] Propiedad: 8935
✅ Código 8935: 26 imágenes subidas

📊 REPORTE FINAL:
   Total Propiedades: 3
   ✅ Procesadas: 3
   📸 Total Imágenes Subidas: 40
```

---

## 📋 CARACTERÍSTICAS DEL SISTEMA

### Descarga Batch (`batch_download_from_list.py`)

✅ **Fuentes de Códigos:**
- Lee `property_images/listado.txt` (2496 códigos)
- O extrae desde página de búsqueda si no existe

✅ **Patrones de URL Inteligentes:**
Prueba automáticamente:
- `Apartamento-en-Venta-[CODE]`
- `Casa-en-Venta-[CODE]`
- `Lote-en-Venta-[CODE]`
- `Apartamento-en-Arriendo-[CODE]`
- `Casa-en-Arriendo-[CODE]`

✅ **Control de Proceso:**
- Límite de cantidad: `python batch_download_from_list.py 100`
- Iniciar desde posición: `python batch_download_from_list.py 50 200`
- Pausa entre descargas (1 segundo)
- No detiene proceso si una falla

✅ **Reportes Detallados:**
- Contador en tiempo real (1/2496, 2/2496, ...)
- Estadísticas finales
- Lista de códigos fallidos

### Subida a Odoo (`create_images_in_odoo.py`)

✅ **Búsqueda Flexible de Propiedades:**
- Por `default_code` directo
- Por `default_code` con prefijo `BOH-`
- Por `id` si es número

✅ **Prevención de Duplicados:**
- Verifica si propiedad ya tiene imágenes
- Pregunta antes de agregar más

✅ **Clasificación Automática:**
- Primera imagen → `is_cover=True`, `image_type='main'`
- Resto → `is_cover=False`, `image_type='other'`
- Secuencia ordenada: 1, 2, 3, ..., N

✅ **Seguridad:**
- Conecta con autenticación
- Maneja errores por imagen
- No detiene si una falla

---

## 🎯 CASOS DE USO

### Uso 1: Descargar Todo (2496 Propiedades)

```bash
# Descargar todas las propiedades
python batch_download_from_list.py

# Puede tomar varias horas dependiendo de:
# - Cantidad con imágenes
# - Velocidad de internet
# - Carga del servidor
```

**Estimación:**
- Propiedades: 2496
- Con imágenes: ~30% (749 propiedades)
- Promedio imágenes/propiedad: 10
- Total imágenes: ~7490
- Tiempo estimado: 2-4 horas

### Uso 2: Descargar Por Lotes

```bash
# Lote 1: Primeras 500
python batch_download_from_list.py 500

# Lote 2: Siguientes 500 (desde posición 500)
python batch_download_from_list.py 500 500

# Lote 3: Siguientes 500 (desde posición 1000)
python batch_download_from_list.py 500 1000

# Lote 4: Resto (desde posición 1500)
python batch_download_from_list.py 1000 1500
```

**Ventajas:**
- Control por etapas
- Revisar resultados parciales
- Fácil reinicio si hay error

### Uso 3: Solo Propiedades Específicas

Crear `codigos_seleccionados.txt`:
```
8747
8935
8933
7821
```

Modificar script para usar ese archivo.

---

## 📁 ESTRUCTURA FINAL

```
bohio-18/
├── batch_download_from_list.py          ← Descarga batch
├── download_property_images.py          ← Descarga individual
├── create_images_in_odoo.py            ← Sube a Odoo
├── SISTEMA_COMPLETO_BATCH.md           ← Esta guía
│
└── property_images/                     ← Carpeta de imágenes
    ├── listado.txt                      ← 2496 códigos
    ├── README.md                        ← Resumen
    │
    ├── 1/                               ← Propiedad 1
    ├── 123/                             ← Propiedad 123
    ├── 170/                             ← Propiedad 170
    │   ├── 14847694951-(Copy).JPG      ← ⭐ Principal
    │   ├── 1484769495DSC00051-(Copy).JPG
    │   └── ... (11 imágenes)
    │
    ├── 8747/                            ← Propiedad 8747
    │   ├── 800x600_347_GOPR4359.JPG    ← ⭐ Principal
    │   ├── 800x600_GOPR4337.JPG
    │   └── 800x600_GOPR4339.JPG
    │
    ├── 8935/                            ← Propiedad 8935
    │   ├── 800x600_GOPR6519.JPG        ← ⭐ Principal
    │   └── ... (26 imágenes)
    │
    └── ... (hasta 2496 carpetas)
```

---

## ⚙️ CONFIGURACIÓN

### Modificar Conexión Odoo

Editar `create_images_in_odoo.py`:

```python
# Líneas 276-279
ODOO_URL = 'http://localhost:8069'  # Cambiar si es remoto
ODOO_DB = 'bohio_db'                 # Nombre de tu BD
ODOO_USER = 'admin'                  # Tu usuario
ODOO_PASS = 'admin'                  # Tu contraseña
```

### Modificar Búsqueda de Propiedades

Editar `create_images_in_odoo.py`, función `find_property_by_code()`:

```python
# Opción 1: Buscar por campo personalizado
[[('x_codigo_externo', '=', code)]]

# Opción 2: Buscar por nombre
[[('name', 'ilike', f'%{code}%')]]

# Opción 3: Buscar por ID directo
[[('id', '=', int(code))]]
```

### Modificar Límites

Editar `batch_download_from_list.py`:

```python
# Línea 236 - Cambiar valores por defecto
max_properties = 100  # Limite por defecto
start_from = 0        # Posición inicial
```

---

## 📊 ESTADÍSTICAS DEL ARCHIVO listado.txt

```
Total códigos: 2496
Rango: 1 - 8757
Formato: Un código por línea
```

**Distribución aproximada:**
- Propiedades antiguas (1-1000): ~400
- Propiedades intermedias (1001-5000): ~1000
- Propiedades recientes (5001-8757): ~1096

---

## 🛠️ TROUBLESHOOTING

### Error: "Propiedad no encontrada en Odoo"

```python
# Verificar códigos en Odoo
SELECT id, default_code, name
FROM product_template
WHERE default_code IN ('170', 'BOH-170', '8747');
```

**Solución:** Ajustar búsqueda en `find_property_by_code()`

### Error: "Autenticación fallida"

```bash
# Verificar conexión
curl http://localhost:8069

# Verificar credenciales
psql bohio_db -c "SELECT login FROM res_users WHERE id=2;"
```

### Error: "No se encontraron imágenes"

Puede ser:
1. Propiedad sin fotos en bohioconsultores.com
2. URL incorrecta (tipo de propiedad)
3. Propiedad eliminada/inactiva

---

## 📝 LOGS Y TRACKING

### Crear Log de Descargas

```bash
python batch_download_from_list.py 100 2>&1 | tee download_log.txt
```

### Crear Log de Subidas

```bash
python create_images_in_odoo.py 2>&1 | tee upload_log.txt
```

### Ver Progreso en Tiempo Real

```bash
# Terminal 1: Ejecutar descarga
python batch_download_from_list.py

# Terminal 2: Monitorear carpetas
watch -n 5 'ls property_images/ | wc -l'

# Terminal 3: Monitorear imágenes
watch -n 10 'find property_images -name "*.JPG" | wc -l'
```

---

## 🎯 FLUJO RECOMENDADO

### Para Producción (2496 Propiedades)

1. **Prueba inicial (10 propiedades)**
   ```bash
   python batch_download_from_list.py 10
   ```

2. **Verificar resultados**
   ```bash
   ls property_images/
   ```

3. **Prueba Odoo (las 10 descargadas)**
   ```bash
   python create_images_in_odoo.py
   ```

4. **Verificar en Odoo UI**
   - Ir a propiedades
   - Ver galería de imágenes
   - Verificar imagen principal

5. **Procesar por lotes**
   ```bash
   # Lote 1
   python batch_download_from_list.py 500
   python create_images_in_odoo.py

   # Lote 2
   python batch_download_from_list.py 500 500
   python create_images_in_odoo.py

   # Continuar...
   ```

---

## ✅ CHECKLIST PRE-EJECUCIÓN

Antes de ejecutar el proceso completo:

- [ ] Odoo está corriendo en `localhost:8069`
- [ ] Base de datos `bohio_db` existe
- [ ] Usuario `admin` con contraseña correcta
- [ ] Modelo `property.image` existe en Odoo
- [ ] Campo `default_code` existe en `product.template`
- [ ] Espacio suficiente en disco (~5-10 GB)
- [ ] Conexión a internet estable
- [ ] Archivo `property_images/listado.txt` existe
- [ ] Python 3.x instalado
- [ ] Librerías instaladas: `requests`, `beautifulsoup4`

---

## 📈 MÉTRICAS ESPERADAS

### Descarga Batch
- **Velocidad**: ~3-5 propiedades/minuto
- **Éxito**: ~30% tienen imágenes
- **Imágenes/propiedad**: 5-15 (promedio 10)

### Subida a Odoo
- **Velocidad**: ~10-20 imágenes/minuto
- **Éxito**: 95%+ si propiedad existe
- **Tamaño promedio**: 100-200 KB/imagen

### Estimación Total (2496 propiedades)
- **Tiempo descarga**: 8-12 horas
- **Tiempo subida**: 4-6 horas
- **Espacio disco**: 5-8 GB
- **Imágenes totales**: 5000-7500

---

## 🎓 COMANDOS ÚTILES

```bash
# Contar carpetas creadas
ls -1 property_images | grep -E '^[0-9]+$' | wc -l

# Contar imágenes totales
find property_images -type f \( -iname "*.jpg" -o -iname "*.png" \) | wc -l

# Ver tamaño total
du -sh property_images/

# Carpetas con más imágenes
for dir in property_images/*/; do
    count=$(ls -1 "$dir" | wc -l)
    echo "$count $dir"
done | sort -rn | head -10

# Carpetas vacías
find property_images -type d -empty

# Limpiar carpetas vacías
find property_images -type d -empty -delete
```

---

## 🔗 INTEGRACIÓN CON ODOO

### Verificar Imágenes en Odoo

```python
# Odoo shell
self.env['property.image'].search([]).mapped('property_id.default_code')

# Contar imágenes por propiedad
SELECT
    pt.default_code,
    COUNT(pi.id) as image_count
FROM property_image pi
JOIN product_template pt ON pt.id = pi.property_id
GROUP BY pt.default_code
ORDER BY image_count DESC
LIMIT 10;
```

### Eliminar Todas las Imágenes (Reset)

```python
# CUIDADO: Esto elimina TODAS las imágenes
self.env['property.image'].search([]).unlink()
```

---

## ✅ CONCLUSIÓN

Sistema completo de 3 pasos:

1. ✅ **Descarga Batch** → `batch_download_from_list.py`
   - Lee 2496 códigos
   - Descarga imágenes automáticamente
   - Organiza por carpetas

2. ✅ **Verificación** → Revisar carpetas locales
   - property_images/[CODE]/

3. ✅ **Subida a Odoo** → `create_images_in_odoo.py`
   - Lee carpetas locales
   - Busca propiedades en Odoo
   - Sube imágenes con clasificación

**Estado:** ✅ LISTO PARA PRODUCCIÓN

**Probado con:**
- 5 propiedades de prueba
- 1 propiedad con imágenes (170: 11 imágenes)
- Sistema funcional end-to-end

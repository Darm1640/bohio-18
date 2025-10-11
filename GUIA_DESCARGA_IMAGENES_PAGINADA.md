# GUÍA DE DESCARGA DE IMÁGENES - NAVEGACIÓN PAGINADA

## 📋 Resumen

Se han mejorado los scripts de descarga de imágenes para navegar página por página en los resultados de búsqueda de bohioconsultores.com y extraer automáticamente los enlaces de todas las propiedades, sin necesidad de construir URLs manualmente.

## 🆕 Mejoras Implementadas

### 1. **batch_download_from_list.py** (MEJORADO)

El script original ahora incluye funcionalidad de navegación paginada:

#### Características nuevas:
- ✅ **Navegación automática por páginas**: Recorre automáticamente múltiples páginas de resultados
- ✅ **Extracción inteligente de URLs**: Extrae enlaces reales de propiedades desde el HTML
- ✅ **Detección de fin de resultados**: Detecta automáticamente cuando no hay más páginas
- ✅ **Evita duplicados**: Filtra URLs duplicadas entre páginas
- ✅ **Soporte para códigos de listado.txt**: Mantiene compatibilidad con el método anterior

#### Uso:

```bash
# Descargar todas las propiedades (navega hasta 10 páginas por defecto)
python batch_download_from_list.py

# Limitar a 20 propiedades
python batch_download_from_list.py 20

# Limitar a 20 propiedades, iniciar desde la posición 10, navegar 5 páginas
python batch_download_from_list.py 20 10 5
```

#### Parámetros:
1. **max_properties**: Cantidad máxima de propiedades a procesar (None = todas)
2. **start_from**: Índice desde donde empezar (0 = desde el inicio)
3. **max_pages**: Número máximo de páginas de búsqueda a navegar (default: 10)

---

### 2. **batch_download_paginated.py** (NUEVO)

Script completamente nuevo diseñado específicamente para navegación paginada avanzada.

#### Características:
- 🔍 **Navegación completa**: Navega todas las páginas de resultados automáticamente
- 📊 **Estadísticas detalladas**: Muestra progreso página por página
- 💾 **Guarda enlaces**: Guarda todos los enlaces encontrados en archivo de texto
- 🎯 **Múltiples tipos de búsqueda**: Soporta búsquedas de venta, arriendo o todas
- ⏱️ **Control de delays**: Configuración de pausas entre páginas y descargas

#### Uso:

```bash
# Descargar todas las propiedades en venta
python batch_download_paginated.py venta

# Limitar a 5 páginas de búsqueda, 20 propiedades
python batch_download_paginated.py venta 5 20

# Buscar propiedades en arriendo, máximo 10 páginas
python batch_download_paginated.py arriendo 10

# Todas las propiedades (venta + arriendo)
python batch_download_paginated.py todas
```

#### Parámetros:
1. **search_type**: Tipo de búsqueda ('venta', 'arriendo', 'todas')
2. **max_pages**: Número máximo de páginas a navegar (None = todas)
3. **max_properties**: Número máximo de propiedades a procesar (None = todas)

---

## 🔧 Cómo Funcionan

### Flujo de Navegación Paginada

```
1. Obtener página de resultados
   ↓
2. Extraer todos los enlaces de propiedades
   ↓
3. Filtrar duplicados
   ↓
4. Detectar si hay siguiente página
   ↓
5. Repetir hasta max_pages o fin de resultados
   ↓
6. Descargar imágenes de cada propiedad
```

### Estrategias de Extracción

El script usa múltiples estrategias para encontrar propiedades:

#### A. Extracción de enlaces:
```python
# Busca todos los <a href="..."> que contengan "detalle-propiedad"
for link in soup.find_all('a', href=True):
    if 'detalle-propiedad' in href:
        urls.append(href)
```

#### B. Detección de siguiente página:
```python
# Busca botones "Siguiente", "Next", "›", etc.
# O incrementa parámetro de página: ?page=2, ?page=3...
```

#### C. Detección de fin de resultados:
```python
# Si no hay enlaces nuevos o la página está vacía
# Automáticamente detiene la navegación
```

---

## 📊 Ejemplos de Uso Real

### Caso 1: Descargar Primeras 50 Propiedades en Venta

```bash
python batch_download_paginated.py venta 5 50
```

**Resultado esperado:**
- Navega hasta 5 páginas de resultados de búsqueda
- Extrae enlaces de propiedades
- Descarga imágenes de las primeras 50 propiedades
- Guarda enlaces en `property_images/property_links_venta.txt`

---

### Caso 2: Continuar desde donde se Quedó

```bash
# Primera ejecución (procesa propiedades 0-49)
python batch_download_from_list.py 50

# Segunda ejecución (procesa propiedades 50-99)
python batch_download_from_list.py 50 50

# Tercera ejecución (procesa propiedades 100-149)
python batch_download_from_list.py 50 100
```

---

### Caso 3: Navegar Todas las Páginas, Descargar Todo

```bash
python batch_download_paginated.py venta
```

**Resultado esperado:**
- Navega TODAS las páginas de resultados (sin límite)
- Extrae todas las URLs de propiedades
- Descarga todas las imágenes
- Puede tomar mucho tiempo (pausas de 2s entre páginas, 1s entre descargas)

---

## 📁 Estructura de Salida

```
property_images/
├── listado.txt                      # Lista de códigos (entrada opcional)
├── property_links_venta.txt         # URLs extraídas (venta)
├── property_links_arriendo.txt      # URLs extraídas (arriendo)
├── 8935/                            # Carpeta por propiedad
│   ├── foto1.jpg
│   ├── foto2.jpg
│   └── foto3.jpg
├── 8936/
│   ├── foto1.jpg
│   └── foto2.jpg
└── ...
```

---

## ⚙️ Configuración Avanzada

### Ajustar Delays

Editar en `batch_download_paginated.py`:

```python
scraper.run_full_process(
    search_type='venta',
    page_delay=2,      # Segundos entre páginas (default: 2)
    download_delay=1   # Segundos entre descargas (default: 1)
)
```

### Ajustar Formato de Paginación

Si el sitio usa un formato diferente de paginación, editar:

```python
def fetch_search_page(self, page_number=1):
    url = self.base_search_url
    if page_number > 1:
        # Cambiar formato aquí
        url = f"{url}&page={page_number}"  # o ?p=, ?pag=, etc.
```

---

## 🐛 Solución de Problemas

### Problema: No encuentra propiedades en la primera página

**Solución:**
1. Verificar que la URL de búsqueda sea correcta
2. Comprobar que el sitio responda correctamente
3. Intentar acceder manualmente a la URL en el navegador

```python
# Verificar URL
self.base_search_url = "https://bohioconsultores.com/resultados-de-busqueda/?Servicio=2"
```

---

### Problema: Se detiene después de pocas páginas

**Causa:** El script detecta que no hay enlaces nuevos o la página está vacía

**Solución:**
- Verificar si realmente hay más páginas en el sitio
- Ajustar la lógica de detección de fin de resultados

---

### Problema: URLs duplicadas

**Solución:** El script ya filtra duplicados automáticamente:

```python
# Filtrar URLs nuevas
new_urls = [url for url in urls if url not in all_urls]
```

---

## 📈 Estadísticas de Rendimiento

### Tiempos Estimados:

- **Navegación por página**: ~2-3 segundos por página
- **Descarga por propiedad**: ~1-5 segundos (dependiendo de cantidad de imágenes)

**Ejemplo:**
- 10 páginas × 20 propiedades/página × 3 segundos/propiedad = **~10 minutos**

---

## 🔄 Comparación de Scripts

| Característica | batch_download_from_list.py | batch_download_paginated.py |
|---|---|---|
| Navegación paginada | ✅ (nueva) | ✅ (diseñado para esto) |
| Lee listado.txt | ✅ | ❌ |
| Construye URLs manualmente | ✅ | ❌ |
| Guarda enlaces extraídos | ❌ | ✅ |
| Tipos de búsqueda | Solo venta | Venta, arriendo, todas |
| Estadísticas por página | ✅ | ✅ (más detalladas) |

---

## 🚀 Recomendaciones

1. **Para descarga rápida**: Usar `batch_download_from_list.py` con límite de propiedades
2. **Para navegación completa**: Usar `batch_download_paginated.py` con tipo de búsqueda
3. **Para reintentos**: Usar `start_from` para continuar desde donde se quedó
4. **Para depuración**: Limitar a pocas páginas primero (ej: `max_pages=2`)

---

## ✅ Ventajas de la Navegación Paginada

1. ✅ **No necesita construir URLs manualmente**: Extrae enlaces reales del HTML
2. ✅ **Encuentra todas las propiedades**: No se salta ninguna por URL incorrecta
3. ✅ **Detecta automáticamente fin de resultados**: No intenta páginas vacías
4. ✅ **Evita duplicados**: Filtra propiedades ya procesadas
5. ✅ **Más robusto**: No depende de patrones específicos de URL

---

## 📝 Notas Finales

- Ambos scripts mantienen **compatibilidad con listado.txt**
- Si existe `listado.txt`, lo usa primero
- Si no existe, navega páginas de búsqueda automáticamente
- Todas las imágenes se guardan en carpetas por código de propiedad
- Los enlaces extraídos se guardan para referencia futura

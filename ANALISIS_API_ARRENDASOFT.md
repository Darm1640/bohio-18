# ANÁLISIS - API ARRENDASOFT Y CARGA DINÁMICA DE PROPIEDADES

## 🔍 Hallazgos

El sitio web **bohioconsultores.com** NO muestra las propiedades directamente en el HTML estático. En su lugar, utiliza **JavaScript y una API de Arrendasoft** para cargar las propiedades dinámicamente.

### API Detectada:

```javascript
var arrendasoft_web_components = {
    "site_url": "https://bohioconsultores.com",
    "api_url": "https://bohio.arrendasoft.co",
    "url_map_data": "https://bohio.arrendasoft.co/service/v2/public/map-of-properties/data",
    // ... otros endpoints
};
```

## ❌ Problema con el Enfoque Actual

El script `batch_download_paginated.py` busca enlaces en el HTML:

```python
def extract_property_links_from_page(self, html):
    soup = BeautifulSoup(html, 'html.parser')
    for link in soup.find_all('a', href=True):
        if 'detalle-propiedad' in href:
            # ...
```

**Resultado:**
- ❌ 0 propiedades encontradas
- ❌ El HTML no contiene los enlaces
- ❌ Los enlaces se generan dinámicamente con JavaScript

## ✅ Soluciones Posibles

### Solución 1: Usar la API de Arrendasoft Directamente

**Ventajas:**
- ✅ Acceso directo a todas las propiedades
- ✅ Datos estructurados (JSON)
- ✅ Más rápido y eficiente
- ✅ No necesita parsear HTML

**Endpoint detectado:**
```
https://bohio.arrendasoft.co/service/v2/public/map-of-properties/data
```

**Implementación:**
```python
import requests

# Obtener propiedades desde API
response = requests.get(
    "https://bohio.arrendasoft.co/service/v2/public/map-of-properties/data",
    params={'Servicio': 2}  # 2 = Venta
)
properties = response.json()

# Procesar cada propiedad
for prop in properties:
    property_id = prop['codigo']
    # Construir URL
    url = f"https://bohioconsultores.com/detalle-propiedad/?{prop['tipo']}-en-Venta-{property_id}"
    # Descargar imágenes...
```

---

### Solución 2: Usar Selenium/Playwright (Headless Browser)

**Ventajas:**
- ✅ Simula navegador real
- ✅ JavaScript se ejecuta automáticamente
- ✅ Ve exactamente lo que ve el usuario

**Desventajas:**
- ❌ Más lento
- ❌ Requiere instalar dependencias (ChromeDriver, etc.)
- ❌ Más recursos (CPU, memoria)

**Implementación:**
```python
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("https://bohioconsultores.com/resultados-de-busqueda/?Servicio=2")

# Esperar a que JavaScript cargue las propiedades
time.sleep(5)

# Extraer enlaces
links = driver.find_elements(By.CSS_SELECTOR, "a[href*='detalle-propiedad']")
for link in links:
    url = link.get_attribute('href')
    # Descargar imágenes...
```

---

### Solución 3: Scraping del Sitemap.xml

**Ventajas:**
- ✅ Archivo XML con todas las URLs
- ✅ Fácil de parsear
- ✅ No necesita JavaScript

**Implementación:**
```python
import requests
from xml.etree import ElementTree

# Obtener sitemap
response = requests.get("https://bohioconsultores.com/sitemap.xml")
root = ElementTree.fromstring(response.content)

# Extraer URLs de propiedades
for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
    if 'detalle-propiedad' in url.text:
        # Descargar imágenes...
```

---

## 🚀 Recomendación: **Solución 1 (API)**

La mejor solución es usar la API de Arrendasoft directamente porque:

1. ✅ **Más rápida**: No necesita cargar/parsear HTML
2. ✅ **Datos estructurados**: JSON con toda la información
3. ✅ **Completa**: Acceso a todas las propiedades
4. ✅ **Eficiente**: Una sola llamada puede traer múltiples propiedades

---

## 📝 Implementación Propuesta

Voy a crear un nuevo script que:
1. Llame a la API de Arrendasoft
2. Obtenga todas las propiedades (venta, arriendo)
3. Construya las URLs correctas
4. Descargue las imágenes

### Script: `batch_download_from_api.py`

```python
import requests
from download_property_images import PropertyImageDownloader

class ArrendasoftAPIDownloader:
    def __init__(self):
        self.api_url = "https://bohio.arrendasoft.co"
        self.downloader = PropertyImageDownloader()

    def get_all_properties(self, servicio=2):
        """
        Obtiene todas las propiedades desde la API
        servicio: 1=Arriendo, 2=Venta
        """
        endpoint = f"{self.api_url}/service/v2/public/map-of-properties/data"
        response = requests.get(endpoint, params={'Servicio': servicio})
        return response.json()

    def construct_property_url(self, property_data):
        """
        Construye URL desde datos de la API
        """
        tipo = property_data.get('tipo', 'Propiedad')
        servicio = property_data.get('servicio', 'Venta')
        codigo = property_data.get('codigo')

        return f"https://bohioconsultores.com/detalle-propiedad/?{tipo}-en-{servicio}-{codigo}"

    def download_all(self):
        # Obtener propiedades
        properties = self.get_all_properties()

        # Descargar cada una
        for prop in properties:
            url = self.construct_property_url(prop)
            self.downloader.process_property_url(url, download_locally=True)
```

---

## 🔍 Endpoints de API Detectados

```
Base URL: https://bohio.arrendasoft.co/service/v2/public/

Endpoints:
- /map-of-properties/data         - Obtener propiedades para mapa
- /property-detail/add-comment     - Añadir comentario
- /property-detail/send-adviser    - Enviar a asesor
- /property-detail/add-solicitud   - Añadir solicitud de cita
- /requirements/save-data          - Guardar requerimiento
- /property-register/save-data     - Registrar propiedad
- /contact-adviser/send-adviser    - Contactar asesor
```

**Endpoint clave para nuestro caso:**
```
GET https://bohio.arrendasoft.co/service/v2/public/map-of-properties/data?Servicio=2
```

---

## 📊 Próximos Pasos

1. **Probar el endpoint de API** para ver qué datos retorna
2. **Crear script adaptado** que use la API en lugar de scraping HTML
3. **Mantener compatibilidad** con el sistema actual de descarga de imágenes

---

## 🎯 Ventajas del Nuevo Enfoque

| Característica | Scraping HTML | API Arrendasoft |
|---|---|---|
| Velocidad | 🐌 Lenta | ⚡ Rápida |
| Confiabilidad | ❌ Baja (depende de HTML) | ✅ Alta (JSON estructurado) |
| Cobertura | ❌ Incompleta (JS dinámico) | ✅ Completa |
| Mantenimiento | ❌ Frágil (cambia HTML) | ✅ Estable (API versionada) |
| Eficiencia | ❌ Una página = ~20 props | ✅ Una llamada = todas |

---

## ⚠️ Consideraciones

1. **Rate Limiting**: La API puede tener límites de requests
2. **Autenticación**: Verificar si necesita tokens/keys
3. **Parámetros**: Explorar qué filtros y parámetros acepta
4. **Paginación**: Ver si la API pagina resultados o trae todo

---

## 🧪 Test del Endpoint

Voy a crear un script de prueba para el endpoint de la API.

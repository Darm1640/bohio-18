# Scripts de Carga Masiva - Real Estate Bits

Scripts para carga masiva y gestión de propiedades mediante XML-RPC en Odoo 18.

## 📋 Índice

1. [Requisitos](#requisitos)
2. [Configuración](#configuración)
3. [Scripts Disponibles](#scripts-disponibles)
4. [Uso](#uso)
5. [Ejemplos](#ejemplos)
6. [Estructura de Datos](#estructura-de-datos)
7. [Solución de Problemas](#solución-de-problemas)

---

## 🔧 Requisitos

- Python 3.8 o superior
- Acceso a servidor Odoo 18 (local o cloud)
- Credenciales de administrador

### Dependencias Python

```bash
# No requiere instalación adicional, usa librerías estándar de Python
# xmlrpc.client, json, csv, logging, datetime
```

---

## ⚙️ Configuración

### 1. Configurar Conexión

Editar la sección de configuración en cada script:

```python
MODE = 'cloud'  # 'local' o 'cloud'

CONNECTIONS = {
    'local': {
        'url': 'http://localhost:8069',
        'db': 'david_test',
        'username': 'admin',
        'password': 'admin'
    },
    'cloud': {
        'url': 'https://darm1640-bohio-18.odoo.com',
        'db': 'darm1640-bohio-18-main-24081960',
        'username': 'admin',
        'password': 'admin'
    }
}
```

### 2. Permisos Requeridos

El usuario debe tener:
- Acceso de administrador
- Permisos de creación/escritura en:
  - `product.template` (propiedades)
  - `res.partner` (terceros/propietarios)
  - `region.region` (barrios)
  - `property.type` (tipos de propiedad)
  - `contract.owner.partner` (propietarios adicionales)

---

## 📦 Scripts Disponibles

### 1. `bulk_property_loader_xmlrpc.py`

**Función:** Carga masiva de propiedades como servicios en Odoo.

**Características:**
- ✅ Crea propiedades completas con todos sus campos
- ✅ Crea/actualiza propietarios automáticamente
- ✅ Crea/actualiza ubicaciones (barrios, ciudades)
- ✅ Genera direcciones de facturación
- ✅ Soporta propietarios múltiples
- ✅ Procesamiento por lotes
- ✅ Caché de registros frecuentes
- ✅ Estadísticas detalladas

**Uso:**
```bash
python bulk_property_loader_xmlrpc.py
```

### 2. `update_property_owners_xmlrpc.py`

**Función:** Actualiza todos los terceros que tienen propiedades marcándolos como propietarios.

**Características:**
- ✅ Identifica propietarios principales
- ✅ Identifica propietarios en contratos
- ✅ Actualiza ranking de proveedor/cliente
- ✅ Genera reporte detallado
- ✅ Top propietarios por cantidad de propiedades

**Uso:**
```bash
python update_property_owners_xmlrpc.py
```

---

## 🚀 Uso

### Carga Masiva de Propiedades

#### Opción 1: Usar Datos de Ejemplo

El script incluye 3 propiedades de ejemplo listas para cargar:

```python
# En main() del script bulk_property_loader_xmlrpc.py
properties = get_sample_properties()
```

Ejecutar:
```bash
python bulk_property_loader_xmlrpc.py
```

#### Opción 2: Cargar desde CSV

1. Crear archivo `properties.csv`:

```csv
name,street,city_name,state_name,region_name,property_area,num_bedrooms,num_bathrooms,net_rental_price,admin_value,owner_name,owner_vat,owner_phone,owner_email
Apartamento Centro,Calle 10 #5-20,Bogotá,Bogotá D.C.,Centro,80,3,2,2000000,300000,Juan Pérez,123456789,3001234567,juan@email.com
Casa Cedritos,Carrera 15 #140-20,Bogotá,Bogotá D.C.,Cedritos,150,4,3,3500000,450000,María López,987654321,3109876543,maria@email.com
```

2. Modificar `main()`:

```python
def main():
    loader = OdooPropertyLoader(...)

    # Cargar desde CSV
    properties = load_from_csv('properties.csv')

    stats = loader.bulk_create_properties(properties)
```

#### Opción 3: Cargar desde JSON

1. Crear archivo `properties.json`:

```json
[
    {
        "name": "Apartamento Moderno",
        "street": "Carrera 43A #5-33",
        "state_name": "Antioquia",
        "city_name": "Medellín",
        "region_name": "El Poblado",
        "property_area": 85.0,
        "num_bedrooms": 3,
        "num_bathrooms": 2,
        "net_rental_price": 2500000.0,
        "partner_data": {
            "name": "Juan Pérez García",
            "vat": "1234567890",
            "phone": "+57 301 234 5678",
            "email": "juan.perez@example.com"
        }
    }
]
```

2. Modificar `main()`:

```python
properties = load_from_json('properties.json')
```

### Actualizar Propietarios

Simplemente ejecutar:

```bash
python update_property_owners_xmlrpc.py
```

El script:
1. Analiza todas las propiedades
2. Identifica propietarios
3. Muestra top 20 propietarios
4. Pide confirmación
5. Actualiza registros
6. Genera reporte

---

## 📊 Estructura de Datos

### Estructura Completa de una Propiedad

```python
property_data = {
    # === IDENTIFICACIÓN ===
    'name': 'Apartamento Moderno en El Poblado',
    'state': 'free',  # free, reserved, on_lease, sold, blocked
    'sequence': 10,

    # === PROPIETARIO ===
    'partner_data': {
        'name': 'Juan Pérez García',
        'vat': '1234567890',
        'phone': '+57 301 234 5678',
        'email': 'juan.perez@example.com',
        'is_company': False,
        'street': 'Calle 123',
        'city': 'Medellín',
    },

    # === UBICACIÓN ===
    'state_name': 'Antioquia',
    'city_name': 'Medellín',
    'region_name': 'El Poblado',
    'street': 'Carrera 43A #5-33',
    'street2': 'Edificio Torre Central, Apto 802',
    'neighborhood': 'El Poblado',
    'zip': '050021',

    # === GEOLOCALIZACIÓN ===
    'latitude': 6.208889,
    'longitude': -75.566667,
    'geocoding_status': 'manual',  # pending, success, failed, manual

    # === TIPO DE PROPIEDAD ===
    'property_type_name': 'Apartamento',
    'property_type': 'apartment',  # apartment, house, land, office, etc.

    # === CARACTERÍSTICAS ===
    'stratum': '6',  # 1-6, commercial, no_stratified
    'type_service': 'rent',  # sale, rent, sale_rent, vacation_rent
    'property_status': 'new',  # new, used, remodeled
    'property_area': 85.0,
    'unit_of_measure': 'm',  # m, yard, hectare
    'num_bedrooms': 3,
    'num_bathrooms': 2,
    'property_age': 2,
    'floor_number': 8,
    'number_of_levels': 1,

    # === ESPACIOS INTERIORES ===
    'living_room': True,
    'main_dining_room': True,
    'study': False,
    'integral_kitchen': True,
    'american_kitchen': False,
    'service_room': True,
    'service_bathroom': True,
    'closet': True,
    'n_closet': 3,
    'walk_in_closet': False,
    'warehouse': False,

    # === ESPACIOS EXTERIORES ===
    'balcony': True,
    'terrace': False,
    'garden': False,
    'patio': False,
    'laundry_area': True,

    # === PARQUEADERO ===
    'garage': True,
    'n_garage': 1,
    'covered_parking': 1,
    'uncovered_parking': 0,
    'visitors_parking': True,

    # === SERVICIOS PÚBLICOS ===
    'gas_installation': True,
    'has_water': True,
    'hot_water': True,
    'electric_heating': False,
    'air_conditioning': False,
    'n_air_conditioning': 0,
    'phone_lines': 1,
    'intercom': True,

    # === AMENIDADES DEL EDIFICIO ===
    'doorman': '24_hours',  # 24_hours, daytime, virtual, none
    'elevator': True,
    'social_room': True,
    'gym': True,
    'pools': True,
    'n_pools': 1,
    'sauna': False,
    'jacuzzi': False,
    'green_areas': True,
    'sports_area': False,
    'has_playground': True,

    # === SEGURIDAD ===
    'has_security': True,
    'security_cameras': True,
    'alarm': False,
    'security_door': True,

    # === ACABADOS ===
    'floor_type': 'porcelain',  # tile, wood, ceramic, porcelain, marble, carpet
    'door_type': 'wood',  # wood, metal, glass, aluminum
    'marble_floor': False,

    # === CARACTERÍSTICAS ADICIONALES ===
    'furnished': False,
    'fireplace': False,
    'mezzanine': False,
    'apartment_type': False,  # duplex, loft, penthouse

    # === PRECIOS DE VENTA ===
    'property_price_type': 'sft',  # fix, sft
    'price_per_unit': 0.0,
    'net_price': 0.0,
    'discount_type': False,  # percentage, amount
    'discount': 0.0,
    'sale_value_from': 0.0,
    'sale_value_to': 0.0,

    # === PRECIOS DE ARRIENDO ===
    'rental_price_type': 'fix',  # fix, sft
    'rental_price_per_unit': 0.0,
    'net_rental_price': 2500000.0,
    'rental_discount_type': False,
    'rental_discount': 0.0,
    'rent_value_from': 2500000.0,
    'rent_value_to': 0.0,

    # === ADMINISTRACIÓN ===
    'admin_value': 350000.0,
    'cadastral_valuation': 0.0,
    'property_tax': 480000.0,
    'maintenance_type': 'fix',  # fix, sft
    'maintenance_charges': 0.0,

    # === INFORMACIÓN LEGAL ===
    'license_code': False,
    'registration_number': False,
    'cadastral_reference': False,
    'liens': False,

    # === CONSIGNACIÓN ===
    'consignment_date': '2025-09-30',
    'property_consignee': False,  # owner, tenant, agent
    'keys_location': False,  # office, property, doorman, owner, other
    'key_note': False,

    # === DESCRIPCIONES ===
    'urbanization_description': False,
    'property_description': 'Hermoso apartamento moderno en una de las mejores zonas de Medellín',
    'observations': 'Disponible inmediato',

    # === INFORMACIÓN DE CONTACTO ===
    'contact_name': False,
    'email_from': False,
    'phone': False,
    'mobile': False,
    'website': False,

    # === PROYECTO ===
    'building_unit': False,  # urbanizacion, edificio, conjunto_cerrado, etc.
    'is_vis': False,
    'is_vip': False,
    'has_subsidy': False,

    # === CONTROL ===
    'create_billing_address': True,  # Crear dirección de facturación automáticamente

    # === PROPIETARIOS ADICIONALES (OPCIONAL) ===
    'additional_owners': [
        {
            'partner_data': {
                'name': 'María Rodríguez',
                'vat': '9876543210',
            },
            'ownership_percentage': 50.0,
            'is_main_owner': False,
            'notes': 'Copropietario'
        }
    ]
}
```

### Campos Mínimos Requeridos

```python
property_data = {
    'name': 'Nombre de la Propiedad',  # REQUERIDO
    'state_name': 'Antioquia',
    'city_name': 'Medellín',
    'region_name': 'El Poblado',
}
```

---

## 📈 Ejemplos de Uso

### Ejemplo 1: Apartamento en Arriendo

```python
property_data = {
    'name': 'Apartamento 3 Habitaciones - Poblado',
    'state_name': 'Antioquia',
    'city_name': 'Medellín',
    'region_name': 'El Poblado',
    'street': 'Carrera 43A #5-33',
    'property_type_name': 'Apartamento',
    'type_service': 'rent',
    'property_area': 85.0,
    'num_bedrooms': 3,
    'num_bathrooms': 2,
    'stratum': '6',
    'net_rental_price': 2500000.0,
    'admin_value': 350000.0,
    'garage': True,
    'elevator': True,
    'pools': True,
    'gym': True,
    'partner_data': {
        'name': 'Juan Pérez',
        'vat': '1234567890',
        'phone': '+57 301 234 5678',
    }
}
```

### Ejemplo 2: Casa en Venta

```python
property_data = {
    'name': 'Casa Campestre - Llanogrande',
    'state_name': 'Antioquia',
    'city_name': 'Rionegro',
    'region_name': 'Llanogrande',
    'street': 'Vereda Llanogrande Km 2.5',
    'property_type_name': 'Casa',
    'type_service': 'sale',
    'property_area': 250.0,
    'num_bedrooms': 4,
    'num_bathrooms': 3,
    'stratum': '5',
    'net_price': 650000000.0,
    'sale_value_from': 650000000.0,
    'garden': True,
    'fireplace': True,
    'partner_data': {
        'name': 'María Rodríguez',
        'vat': '9876543210',
        'phone': '+57 304 987 6543',
    }
}
```

### Ejemplo 3: Oficina en Arriendo

```python
property_data = {
    'name': 'Oficina Centro Empresarial',
    'state_name': 'Antioquia',
    'city_name': 'Medellín',
    'region_name': 'Centro',
    'street': 'Calle 50 #50-25',
    'property_type_name': 'Oficina',
    'type_service': 'rent',
    'property_area': 65.0,
    'num_bathrooms': 1,
    'stratum': 'commercial',
    'net_rental_price': 1800000.0,
    'admin_value': 180000.0,
    'air_conditioning': True,
    'elevator': True,
    'partner_data': {
        'name': 'Inversiones XYZ S.A.S.',
        'vat': '900123456',
        'is_company': True,
    }
}
```

---

## 🔍 Solución de Problemas

### Error: "Autenticación fallida"

**Causa:** Credenciales incorrectas o base de datos no existe.

**Solución:**
```python
# Verificar configuración
CONFIG = {
    'url': 'https://...',  # Sin barra al final
    'db': 'nombre-exacto-base-datos',
    'username': 'admin',
    'password': 'contraseña-correcta'
}
```

### Error: "No se pudo crear la propiedad"

**Causas comunes:**
1. Faltan campos requeridos
2. Relaciones inválidas (ciudad, departamento no existen)
3. Restricciones SQL (códigos duplicados)

**Solución:**
```python
# Verificar logs detallados
logger.setLevel(logging.DEBUG)

# Verificar que existan registros base
# - País Colombia
# - Departamento
# - Ciudad
```

### Error: "No se encontró región/barrio"

**Causa:** La región no existe en la base de datos.

**Solución:** El script creará automáticamente la región si no existe. Verificar que `state_name` y `city_name` sean correctos.

### Advertencia: "No se pudo crear dirección de facturación"

**Causa:** Normalmente no crítico. El partner principal no tiene ID válido.

**Solución:** Verificar que `partner_data` tenga `name` mínimo.

### Performance Lento

**Causa:** Muchas propiedades, conexión lenta.

**Soluciones:**
1. Reducir cantidad de propiedades por lote
2. Usar conexión local si es posible
3. Comentar logs DEBUG:
   ```python
   logger.setLevel(logging.INFO)
   ```

---

## 📝 Logs y Reportes

### Logs del Sistema

Los logs se muestran en consola con formato:
```
2025-09-30 10:30:15 - INFO - ✓ Conectado a https://...
2025-09-30 10:30:16 - INFO - [1/10] Procesando: Apartamento...
2025-09-30 10:30:17 - INFO - ✓ Propiedad creada: ... (ID: 123)
```

### Reportes Generados

#### `property_owners_update_report_[db].txt`

Generado por `update_property_owners_xmlrpc.py`:

```
╔════════════════════════════════════════════════════════════╗
║         REPORTE DE ACTUALIZACIÓN DE PROPIETARIOS          ║
╠════════════════════════════════════════════════════════════╣
║  Total de propietarios procesados:                   45   ║
║  Actualizados exitosamente:                          43   ║
║  Fallidos:                                            2    ║
║  Total de propiedades:                               128   ║
║  Tasa de éxito:  95.6%                                    ║
╚════════════════════════════════════════════════════════════╝
```

---

## 🎯 Casos de Uso

### 1. Migración Desde Otro Sistema

```python
# 1. Exportar propiedades del sistema anterior a CSV
# 2. Mapear columnas a estructura de Odoo
# 3. Ejecutar carga masiva
properties = load_from_csv('migracion_propiedades.csv')
stats = loader.bulk_create_properties(properties)
```

### 2. Carga Periódica desde API Externa

```python
# 1. Obtener propiedades de API externa
import requests
response = requests.get('https://api-externa.com/properties')
external_properties = response.json()

# 2. Transformar a formato Odoo
odoo_properties = []
for ext_prop in external_properties:
    odoo_prop = {
        'name': ext_prop['title'],
        'street': ext_prop['address'],
        # ... mapear campos
    }
    odoo_properties.append(odoo_prop)

# 3. Cargar en Odoo
stats = loader.bulk_create_properties(odoo_properties)
```

### 3. Actualización Masiva de Propietarios

```bash
# Ejecutar después de:
# - Importar nuevas propiedades
# - Asignar propietarios manualmente
# - Migración de datos

python update_property_owners_xmlrpc.py
```

---

## 🔒 Seguridad

### Credenciales

**NO** subir archivos con credenciales a repositorios públicos.

Usar variables de entorno:

```python
import os

CONFIG = {
    'url': os.getenv('ODOO_URL'),
    'db': os.getenv('ODOO_DB'),
    'username': os.getenv('ODOO_USER'),
    'password': os.getenv('ODOO_PASSWORD')
}
```

Ejecutar:
```bash
export ODOO_URL="https://..."
export ODOO_DB="database"
export ODOO_USER="admin"
export ODOO_PASSWORD="password"

python bulk_property_loader_xmlrpc.py
```

### Backups

**IMPORTANTE:** Hacer backup de la base de datos antes de:
- Carga masiva inicial
- Actualizaciones masivas
- Pruebas de migración

```bash
# Backup desde Odoo Cloud
# Ir a: Base de Datos > Administrar > Backup

# Backup local
pg_dump nombre_base > backup_$(date +%Y%m%d).sql
```

---

## 📞 Soporte

Para soporte técnico:
1. Revisar logs detallados
2. Verificar estructura de datos
3. Consultar documentación de Odoo 18

---

## 📄 Licencia

Scripts creados para uso interno de Real Estate Bits / Bohio CRM.

---

**Última actualización:** 2025-09-30
**Versión:** 1.0.0
**Autor:** Claude Code
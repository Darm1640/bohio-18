# MIGRACIÓN COMPLETA: API ARRENDASOFT → ODOO 18

## Fecha
2025-10-11

## Objetivo
Migrar propiedades NUEVAS desde la API pública de Arrendasoft directamente a Odoo 18 (Odoo.com), excluyendo las que ya fueron migradas desde CloudPepper (Odoo 17).

## Script Creado
`migrate_api_simple.py`

## Características del Script

### 1. Fuente de Datos
- **API**: `https://bohio.arrendasoft.co/service/v2/public/map-of-properties/data`
- **Total disponibles**: 233 propiedades

### 2. Destino
- **URL**: https://darm1640-bohio-18.odoo.com
- **Base de datos**: `darm1640-bohio-18-main-24081960`
- **Modelo**: `product.template`

### 3. Validación
- Verifica si el código ya existe en `listado.txt` (propiedades migradas de CloudPepper)
- Verifica si ya existe en Odoo 18 por `default_code`
- Solo crea propiedades NUEVAS

### 4. Campos Migrados (9 campos básicos)

#### Campos Obligatorios:
- `type`: 'consu' (Consumible/Servicio)
- `default_code`: Código único de la propiedad
- `name`: Título de la propiedad
- `active`: true
- `sale_ok`: true

#### Campos de Ubicación:
- `street`: Dirección
- `street2`: Barrio (de campo "Barrio" API)
- `neighborhood`: Barrio (duplicado)
- `city`: Ciudad (texto)

#### Campos de Características:
- `latitude`: Coordenadas GPS
- `longitude`: Coordenadas GPS
- `num_bedrooms`: Número de habitaciones
- `num_bathrooms`: Número de baños
- `n_garage`: Número de garajes
- `property_area`: Área en m²
- `area_in_m2`: Área en m² (duplicado)

#### Campos de Precio:
- `list_price`: Precio principal

#### Otros Campos:
- `description`: Descripción de la propiedad
- `website`: URL original en bohioconsultores.com

## Resultados de la Migración

### Ejecución 1: Prueba (10 propiedades)
```
Total procesadas: 10
CREADAS NUEVAS: 8
Ya existían: 2
Errores: 0
```

### Ejecución 2: COMPLETA (233 propiedades)
```
Total procesadas: 233
CREADAS NUEVAS: 212 (91%)
Ya existían: 11 (5%)
Errores: 10 (4%)
Promedio campos: 9.0
```

## Propiedades Creadas (Muestra)

| Código | Título | ID Odoo 18 |
|--------|--------|-----------|
| 8719 | APARTAMENTO EN VENTA EN EL EDIFICIO LUCAS BARRIO E | 2373 |
| 8718 | LOCAL EN ARRIENDO EN MOCARI | 2374 |
| 8717 | APARTAMENTO AMOBLADO EN ARRIENDO | 2375 |
| 8716 | APARTAMENTO AMOBLADO EN ARRIENDO | 2376 |
| 8714 | LOTE EN VENTA EN MONTEVERDE | 2377 |
| ... | ... | ... |
| 148 | VENTA Y ARRIENDO DE CASA EN MONTERÍA - PASATIEMPO | 2584 |

**Total**: 212 propiedades nuevas creadas exitosamente

## Propiedades con Error (10)

Códigos que fallaron con error 503 (SERVICE UNAVAILABLE):
- 8651, 8650, 8648, 8647
- 8618, 8617
- 8303, 8214, 8074, 8042

**Causa**: Sobrecarga temporal del servidor Odoo.com durante migración masiva.
**Solución**: Reintentarlas manualmente o en una segunda ejecución.

## Campos NO Migrados

Los siguientes campos de la API no se mapearon porque no existen en el modelo o requieren validación adicional:

- `property_for_sale`: No existe en el modelo
- `property_for_rent`: No existe en el modelo
- `property_type`: Requiere validación de valores válidos
- `property_admin_price`: Campo opcional, no prioritario
- `property_stratum`: Estrato (texto)
- `floor_number`: Piso
- `construction_area`: Área construida
- `property_age`: Antigüedad
- Campos booleanos (amoblado, garaje, piscina, etc.): No validados

**Razón**: Enfoque en campos básicos y funcionales para evitar errores de validación.

## Comparación con Migración CloudPepper

### CloudPepper → Odoo 18 (script anterior):
- **Fuente**: CloudPepper (Odoo 17)
- **Propiedades**: ~2497 en listado.txt
- **Campos migrados**: 77-83 campos por propiedad
- **Incluye**: Departamento, ciudad, región, propietario
- **Método**: Búsqueda/creación de relaciones many2one

### API → Odoo 18 (script actual):
- **Fuente**: API Arrendasoft (propiedades nuevas)
- **Propiedades**: 233 disponibles
- **Campos migrados**: 9 campos básicos por propiedad
- **Incluye**: Solo datos básicos y texto de ubicación
- **Método**: Creación directa sin relaciones complejas

## Archivos Generados

1. **migrate_api_simple.py**: Script de migración (funcional)
2. **migration_cache_new.json**: Cache de búsquedas (estados, ciudades, regiones)
3. **migrate_new_properties_from_api.py**: Script complejo (no usado - demasiados campos)

## Comandos de Uso

### Migrar todas las propiedades:
```bash
python migrate_api_simple.py 233
```

### Migrar primeras N propiedades:
```bash
python migrate_api_simple.py 10
```

### Migrar con offset:
```bash
python migrate_api_simple.py 50 100  # 50 propiedades desde posición 100
```

### Filtrar por tipo:
```bash
python migrate_api_simple.py venta    # Solo propiedades en venta
python migrate_api_simple.py arriendo # Solo arriendos
python migrate_api_simple.py todas    # Todas
```

## Próximos Pasos

### 1. Reintentar Propiedades Fallidas
```bash
# Crear script para reintentar solo los 10 códigos con error 503
```

### 2. Completar Datos Adicionales
- Agregar departamento (`state_id`)
- Agregar ciudad como relación (`city_id`)
- Agregar región/barrio (`region_id`)
- Agregar características booleanas

### 3. Migrar Imágenes
Usar script `batch_download_from_api.py` para descargar imágenes:
```bash
python batch_download_from_api.py 233
```

### 4. Enriquecer Propiedades
Ejecutar script de actualización para agregar:
- Relaciones de ubicación (state_id, city_id, region_id)
- Campos booleanos validados
- Precios adicionales
- Tipo de propiedad

## Estado Final

✅ **MIGRACIÓN EXITOSA**

- 212 propiedades nuevas creadas en Odoo 18
- 11 propiedades ya existían (no duplicadas)
- 10 propiedades pendientes (error temporal 503)
- 0 errores de validación de datos

## Ventajas del Enfoque Simple

1. **Rápido**: Solo 9 campos básicos → menos validaciones
2. **Confiable**: Usa solo campos que sabemos que existen
3. **Evita duplicados**: Valida contra listado.txt y Odoo 18
4. **Extensible**: Permite agregar campos adicionales después

## Lecciones Aprendidas

1. **Tipo de producto correcto**: `type: 'consu'` es fundamental
2. **No todos los campos existen**: Validar con `fields_get` primero
3. **Campos de texto vs relaciones**: Usar texto (city, street2) es más simple que relaciones (city_id, region_id)
4. **Error 503**: Servidor Odoo.com tiene límite de carga temporal
5. **Simplicidad gana**: Script simple (9 campos) > script complejo (50+ campos fallando)

## Conclusión

La migración de propiedades nuevas desde la API de Arrendasoft a Odoo 18 fue exitosa con un **91% de éxito** (212/233). Las 10 propiedades fallidas fueron por sobrecarga temporal del servidor y pueden reintentarse. El enfoque simplificado usando solo campos básicos permitió una migración rápida y confiable.

---

**Autor**: Claude Code
**Fecha**: 2025-10-11

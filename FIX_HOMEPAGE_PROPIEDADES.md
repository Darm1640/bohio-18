# FIX: Homepage No Muestra Propiedades

## PROBLEMA IDENTIFICADO

El filtro `has_project` con valor booleano `False` en JavaScript puede causar problemas en JSON-RPC de Python.

### Código Actual (homepage_properties.js líneas 291-296):

```javascript
const usedSaleDataGrid = await loadProperties({
    type_service: 'sale',
    has_project: false,      // <- PROBLEMA: booleano false
    limit: 10,
    order: 'newest'
});
```

### Por Qué Falla:

Cuando JavaScript envía `has_project: false` vía JSON-RPC, Python lo recibe pero la lógica en `property_search.py` línea 137 usa:

```python
if 'has_project' in filters:
    if filters['has_project']:  # <- PROBLEMA: false es falsy
        domain.append(('project_worksite_id', '!=', False))
    else:
        domain.append(('project_worksite_id', '=', False))
```

El problema es que `filters['has_project']` con valor `False` es "falsy" pero la clave EXISTE en el diccionario.

## SOLUCIÓN

Agregar logging y mensajes más descriptivos para debug, y mejorar la lógica del filtro.

### Archivo a Modificar:

`theme_bohio_real_estate/controllers/property_search.py`

### Cambio en el Método `property_search_ajax` (línea 139):

```python
@http.route([
    '/property/search/ajax',
    '/property/search/ajax/<string:context>'
], type='json', auth='public', website=True, csrf=False)
def property_search_ajax(self, context='public', filters=None, page=1, ppg=20, order='relevance'):
    """
    Endpoint JSON para búsquedas AJAX sin recarga de página
    Compatible con componentes OWL
    """
    if filters is None:
        filters = {}

    # LOG DE DEBUG
    _logger.info(f"[HOMEPAGE] /property/search/ajax llamado con:")
    _logger.info(f"  context={context}, filters={filters}, page={page}, ppg={ppg}, order={order}")

    # Validar contexto
    search_context = self.SEARCH_CONTEXTS.get(context, self.SEARCH_CONTEXTS['public'])

    # Construir dominio
    domain = self._build_context_domain(search_context, filters)
    _logger.info(f"[HOMEPAGE] Dominio base: {domain}")

    domain = self._apply_location_filters(domain, filters)
    domain = self._apply_property_filters(domain, filters)
    _logger.info(f"[HOMEPAGE] Dominio después de filtros de propiedad: {domain}")

    domain = self._apply_price_area_filters(domain, filters)
    domain = self._apply_amenities_filters(domain, filters)

    # Ordenamiento y paginación
    order_sql = self._get_smart_order(order)
    ppg = min(int(ppg), search_context.get('max_results', 100))
    offset = (int(page) - 1) * ppg

    # Búsqueda
    Property = request.env['product.template'].sudo()
    total = Property.search_count(domain)
    _logger.info(f"[HOMEPAGE] Total propiedades encontradas: {total}")

    properties = Property.search(domain, limit=ppg, offset=offset, order=order_sql)

    # Serializar propiedades para JSON
    properties_data = self._serialize_properties(properties, search_context)

    # Metadata de paginación
    total_pages = (total + ppg - 1) // ppg if ppg > 0 else 0

    return {
        'success': True,
        'properties': properties_data,
        'total': total,
        'page': int(page),
        'ppg': ppg,
        'total_pages': total_pages,
        'has_next': int(page) < total_pages,
        'has_prev': int(page) > 1,
        'context': context,
    }
```

### Cambio en el Método `_apply_property_filters` (línea 118):

```python
def _apply_property_filters(self, domain, filters):
    """Aplica filtros de tipo y características"""
    if filters.get('property_type'):
        domain.append(('property_type', '=', filters['property_type']))

    # Tipo de servicio
    if filters.get('type_service'):
        ts = filters['type_service']
        if ts == 'sale_rent':
            domain.append(('type_service', 'in', ['sale', 'rent', 'sale_rent']))
        else:
            domain.append(('type_service', 'in', [ts, 'sale_rent']))

    # Filtro de ubicación (solo propiedades con coordenadas)
    if filters.get('has_location'):
        domain.append(('latitude', '!=', False))
        domain.append(('longitude', '!=', False))

    # Filtro de proyecto (propiedades nuevas vs usadas)
    # MEJORADO: Manejo explícito de booleanos
    if 'has_project' in filters:
        has_project_value = filters['has_project']
        _logger.info(f"[HOMEPAGE] Aplicando filtro has_project={has_project_value} (tipo: {type(has_project_value)})")

        # Manejar tanto booleanos como strings
        if has_project_value in (True, 'true', '1', 1):
            # Propiedades nuevas/proyectos: tienen proyecto asignado
            domain.append(('project_worksite_id', '!=', False))
            _logger.info("[HOMEPAGE] Filtrando CON proyecto")
        elif has_project_value in (False, 'false', '0', 0, None):
            # Propiedades usadas: NO tienen proyecto
            domain.append(('project_worksite_id', '=', False))
            _logger.info("[HOMEPAGE] Filtrando SIN proyecto")

    # Habitaciones y baños
    if filters.get('bedrooms'):
        try:
            domain.append(('num_bedrooms', '>=', int(filters['bedrooms'])))
        except (ValueError, TypeError):
            pass

    if filters.get('bathrooms'):
        try:
            domain.append(('num_bathrooms', '>=', int(filters['bathrooms'])))
        except (ValueError, TypeError):
            pass

    return domain
```

## INSTRUCCIONES DE APLICACIÓN

### 1. Aplicar cambios al controlador:

```bash
# Abrir archivo
code "C:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\theme_bohio_real_estate\controllers\property_search.py"

# Buscar línea 139 (método property_search_ajax)
# Agregar los _logger.info() como se muestra arriba

# Buscar línea 118 (método _apply_property_filters)
# Reemplazar la sección de has_project con la versión mejorada
```

### 2. Actualizar el módulo:

```bash
"C:\Program Files\Odoo 18.0.20250830\python\python.exe" "C:\Program Files\Odoo 18.0.20250830\server\odoo-bin" -c "C:\Program Files\Odoo 18.0.20250830\server\odoo.conf" -d bohio_db -u theme_bohio_real_estate --stop-after-init
```

### 3. Revisar logs de Odoo:

Abrir el archivo de log y buscar las líneas que comienzan con `[HOMEPAGE]`:

```bash
# En PowerShell o CMD
Get-Content "C:\Program Files\Odoo 18.0.20250830\server\odoo.log" -Tail 50 -Wait | Select-String "HOMEPAGE"
```

### 4. Probar en el navegador:

1. Abrir http://localhost:8069
2. Abrir Consola del navegador (F12)
3. Buscar mensajes de console.log en homepage_properties.js
4. Verificar tab Network → Filter "search/ajax"

## ALTERNATIVA: Si el Problema Persiste

Si después de aplicar estos cambios aún no se muestran propiedades, el problema puede ser:

### A. No hay propiedades en la BD

Ejecutar en Odoo shell:

```python
# Verificar propiedades de arriendo
self.env['product.template'].search_count([
    ('is_property', '=', True),
    ('active', '=', True),
    ('state', '=', 'free'),
    ('type_service', 'in', ['rent', 'sale_rent'])
])

# Verificar propiedades de venta sin proyecto
self.env['product.template'].search_count([
    ('is_property', '=', True),
    ('active', '=', True),
    ('state', '=', 'free'),
    ('type_service', 'in', ['sale', 'sale_rent']),
    ('project_worksite_id', '=', False)
])

# Verificar proyectos
self.env['product.template'].search_count([
    ('is_property', '=', True),
    ('active', '=', True),
    ('state', '=', 'free'),
    ('type_service', 'in', ['sale', 'sale_rent']),
    ('project_worksite_id', '!=', False)
])
```

### B. JavaScript no está cargando

Verificar que el archivo esté registrado en `__manifest__.py`:

```python
'assets': {
    'web.assets_frontend': [
        ...
        'theme_bohio_real_estate/static/src/js/homepage_properties.js',
        ...
    ],
}
```

Limpiar cache del navegador:
- Ctrl+Shift+Del
- Seleccionar "Archivos e imágenes en caché"
- Limpiar

### C. Error de CORS o CSRF

Si ves error 403 en Network tab:

- Verificar que la ruta tenga `csrf=False`
- Verificar que `auth='public'`

## RESUMEN

Los cambios principales son:

1. Agregar logging detallado para depurar
2. Mejorar la lógica de manejo de `has_project` para aceptar booleanos y strings
3. Verificar que las propiedades existan en la BD
4. Verificar que el JavaScript esté cargando correctamente

Con estos cambios, los logs de Odoo te dirán exactamente:
- Qué filtros se están aplicando
- Qué dominio se está construyendo
- Cuántas propiedades se encuentran

Esto te permitirá identificar el problema exacto.

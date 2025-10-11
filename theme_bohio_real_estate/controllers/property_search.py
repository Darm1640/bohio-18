# -*- coding: utf-8 -*-
# Part of Odoo Real Estate Module - Sistema Avanzado de Búsqueda Odoo 18

from odoo import http, fields, _
from odoo.http import request
from odoo.osv import expression
from datetime import datetime, timedelta
import json
import logging

try:
    from odoo.addons.website.controllers.main import QueryURL
except ImportError:
    # Fallback si no está disponible QueryURL
    QueryURL = None

_logger = logging.getLogger(__name__)


class PropertySearchController(http.Controller):
    """
    Controlador Avanzado de Búsqueda de Propiedades - Odoo 18

    Características:
    - Sistema de contextos configurables (público, admin, proyecto, quick)
    - Filtros avanzados con contadores dinámicos (read_group)
    - Autocompletado inteligente con normalización sin acentos
    - Sistema de comparación de propiedades (hasta 4)
    - Búsqueda JSON-RPC para actualizaciones AJAX sin recarga
    - Paginación optimizada con QueryURL
    - Compatible con componentes OWL
    - Cache inteligente según contexto
    """

    # =================== CONFIGURACIÓN DE CONTEXTOS ===================

    SEARCH_CONTEXTS = {
        'public': {
            'name': _('Búsqueda Pública'),
            'allowed_states': ['free'],
            'show_price': True,
            'show_contact': True,
            'allow_comparison': True,
            'cache_ttl': 300,  # 5 minutos
        },
        'admin': {
            'name': _('Búsqueda Administrativa'),
            'allowed_states': ['free', 'reserved', 'sold', 'on_lease'],
            'show_price': True,
            'show_contact': True,
            'allow_comparison': True,
            'cache_ttl': 0,  # Sin cache
        },
        'project': {
            'name': _('Búsqueda por Proyecto'),
            'allowed_states': ['free'],
            'filter_by_project': True,
            'show_price': True,
            'show_contact': False,
            'allow_comparison': True,
            'cache_ttl': 600,  # 10 minutos
        },
        'quick': {
            'name': _('Búsqueda Rápida'),
            'allowed_states': ['free'],
            'show_price': False,
            'show_contact': False,
            'allow_comparison': False,
            'max_results': 10,
            'cache_ttl': 300,
        },
    }

    # =================== BÚSQUEDA PRINCIPAL HTTP ===================

    @http.route([
        '/shop/property/search',
        '/shop/property/search/<string:context>',
        '/property/search',
        '/property/search/<string:context>'
    ], type='http', auth='public', website=True, sitemap=False)
    def property_search(self, context='public', **post):
        """
        Página principal de búsqueda con contextos configurables

        Args:
            context (str): Tipo de contexto (public, admin, project, quick)
            **post: Parámetros de filtros

        Returns:
            Rendered template con propiedades filtradas
        """
        # Validar contexto
        search_context = self.SEARCH_CONTEXTS.get(context, self.SEARCH_CONTEXTS['public'])

        # Extraer parámetros de búsqueda
        filters = self._extract_search_filters(post)

        # Construir dominio base
        domain = self._build_context_domain(search_context, filters)

        # Aplicar filtros jerárquicos
        domain = self._apply_location_filters(domain, filters)
        domain = self._apply_property_filters(domain, filters)
        domain = self._apply_price_area_filters(domain, filters)
        domain = self._apply_amenities_filters(domain, filters)

        # Ordenamiento y paginación
        order = self._get_smart_order(filters.get('order', 'relevance'))
        page = int(filters.get('page', 1))
        ppg = min(int(filters.get('ppg', 20)), search_context.get('max_results', 100))
        offset = (page - 1) * ppg

        # Búsqueda optimizada
        Property = request.env['product.template'].sudo()
        total_properties = Property.search_count(domain)
        properties = Property.search(domain, limit=ppg, offset=offset, order=order)

        # Marcar propiedades nuevas (últimos 30 días)
        self._mark_new_properties(properties)

        # QueryURL para preservar filtros en paginación
        keep = self._build_query_url('/property/search/' + context, filters)

        # Preparar valores para renderizado
        values = self._prepare_search_values(
            properties, total_properties, filters, search_context,
            context, page, ppg, domain, keep
        )

        return request.render('theme_bohio_real_estate.properties_shop', values)

    # =================== BÚSQUEDA JSON-RPC PARA AJAX ===================

    @http.route([
        '/property/search/ajax',
        '/property/search/ajax/<string:context>'
    ], type='json', auth='public', website=True, csrf=False)
    def property_search_ajax(self, context='public', filters=None, page=1, ppg=20, order='relevance'):
        """
        Endpoint JSON para búsquedas AJAX sin recarga de página
        Compatible con componentes OWL

        Args:
            context (str): Contexto de búsqueda
            filters (dict): Diccionario de filtros
            page (int): Página actual
            ppg (int): Propiedades por página
            order (str): Criterio de ordenamiento

        Returns:
            dict: Propiedades + metadata
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
        _logger.info(f"[HOMEPAGE] Dominio después de filtros: {domain}")

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

    # =================== FILTROS DINÁMICOS JSON ===================

    @http.route([
        '/property/filters/options',
        '/property/filters/options/<string:context>'
    ], type='json', auth='public', website=True, csrf=False)
    def get_filter_options(self, context='public', filters=None):
        """
        Obtiene opciones de filtros con contadores dinámicos
        Usado por componentes OWL para actualizar filtros según selección

        Args:
            context (str): Contexto de búsqueda
            filters (dict): Filtros actuales aplicados

        Returns:
            dict: Opciones de filtros con contadores
        """
        if filters is None:
            filters = {}

        search_context = self.SEARCH_CONTEXTS.get(context, self.SEARCH_CONTEXTS['public'])

        # Dominio base con filtros actuales
        base_domain = self._build_context_domain(search_context, filters)

        return {
            'success': True,
            'property_types': self._get_property_types_with_counts(base_domain),
            'cities': self._get_cities_with_counts(base_domain),
            'states': self._get_states_with_counts(base_domain),
            'regions': self._get_regions_with_counts(base_domain, filters.get('city_id'), filters.get('state_id')),
            'projects': self._get_projects_with_counts(base_domain, filters.get('city_id'), filters.get('state_id'), filters.get('region_id')),
            'price_ranges': self._get_price_ranges_by_type(filters.get('property_type'), filters.get('type_service')),
            'area_ranges': self._get_area_ranges(),
            'bedroom_options': [1, 2, 3, 4, 5, 6],
            'bathroom_options': [1, 2, 3, 4, 5],
            'service_types': [
                {'value': 'sale', 'label': _('Venta')},
                {'value': 'rent', 'label': _('Arriendo')},
                {'value': 'vacation_rent', 'label': _('Arriendo Vacacional')},
            ],
            'property_states': [
                {'value': 'free', 'label': _('Disponible')},
                {'value': 'reserved', 'label': _('Reservada')},
                {'value': 'sold', 'label': _('Vendida')},
                {'value': 'on_lease', 'label': _('En Arriendo')},
            ] if context == 'admin' else [],
        }

    # =================== AUTOCOMPLETADO INTELIGENTE ===================

    @http.route([
        '/property/search/autocomplete',
        '/property/search/autocomplete/<string:context>'
    ], type='json', auth='public', website=True, csrf=False)
    def property_search_autocomplete(self, term='', context='public', subdivision='all', limit=10):
        """
        Autocompletado inteligente con normalización sin acentos

        Args:
            term (str): Término de búsqueda (mínimo 2 caracteres)
            context (str): Contexto de búsqueda
            subdivision (str): 'all', 'cities', 'regions', 'projects', 'properties'
            limit (int): Máximo de resultados

        Returns:
            dict: Resultados ordenados por prioridad
        """
        if not term or len(term) < 2:
            return {'success': True, 'results': [], 'subdivision': subdivision, 'total': 0}

        search_context = self.SEARCH_CONTEXTS.get(context, self.SEARCH_CONTEXTS['public'])
        results = []

        # Buscar según subdivisión
        if subdivision in ['all', 'cities']:
            results.extend(self._autocomplete_cities(term, search_context, limit))

        if subdivision in ['all', 'regions']:
            results.extend(self._autocomplete_regions(term, search_context, limit))

        if subdivision in ['all', 'projects'] and search_context.get('filter_by_project', True):
            results.extend(self._autocomplete_projects(term, search_context, limit))

        if subdivision in ['all', 'properties']:
            results.extend(self._autocomplete_properties(term, search_context, limit))

        # Ordenar por prioridad y contador
        results.sort(key=lambda x: (x.get('priority', 0), x.get('property_count', 0)), reverse=True)

        return {
            'success': True,
            'results': results[:limit],
            'subdivision': subdivision,
            'total': len(results),
            'term': term
        }

    # =================== SISTEMA DE COMPARACIÓN ===================

    @http.route(['/property/comparison/add'], type='json', auth='public', website=True, csrf=False)
    def add_to_comparison(self, property_id, context='public'):
        """Agregar propiedad a comparación (máximo 4)"""
        search_context = self.SEARCH_CONTEXTS.get(context, self.SEARCH_CONTEXTS['public'])

        if not search_context.get('allow_comparison', False):
            return {'success': False, 'message': _('Comparación no permitida en este contexto')}

        comparison_list = request.session.get('property_comparison', [])

        # Validar límite
        if len(comparison_list) >= 4:
            return {'success': False, 'message': _('Máximo 4 propiedades para comparar')}

        # Validar existencia
        Property = request.env['product.template'].sudo()
        domain = [
            ('id', '=', int(property_id)),
            ('is_property', '=', True),
            ('state', 'in', search_context.get('allowed_states', ['free']))
        ]

        if not Property.search_count(domain):
            return {'success': False, 'message': _('Propiedad no válida')}

        # Agregar
        if property_id not in comparison_list:
            comparison_list.append(property_id)
            request.session['property_comparison'] = comparison_list

        return {'success': True, 'total': len(comparison_list), 'property_ids': comparison_list}

    @http.route(['/property/comparison/remove'], type='json', auth='public', website=True, csrf=False)
    def remove_from_comparison(self, property_id):
        """Eliminar propiedad de comparación"""
        comparison_list = request.session.get('property_comparison', [])

        if property_id in comparison_list:
            comparison_list.remove(property_id)
            request.session['property_comparison'] = comparison_list

        return {'success': True, 'total': len(comparison_list), 'property_ids': comparison_list}

    @http.route(['/property/comparison/clear'], type='json', auth='public', website=True, csrf=False)
    def clear_comparison(self):
        """Limpiar todas las propiedades de comparación"""
        request.session['property_comparison'] = []
        return {'success': True, 'total': 0, 'property_ids': []}

    @http.route(['/property/comparison/list'], type='json', auth='public', website=True, csrf=False)
    def get_comparison_list(self):
        """Obtener IDs de propiedades en comparación"""
        comparison_list = request.session.get('property_comparison', [])
        return {'success': True, 'property_ids': comparison_list, 'total': len(comparison_list)}

    # =================== MÉTODOS AUXILIARES - FILTROS ===================

    def _extract_search_filters(self, post):
        """Extrae y normaliza todos los parámetros de filtros"""
        return {
            'search': post.get('search', '').strip(),
            'property_type': post.get('property_type', ''),
            'city_id': post.get('city_id', ''),
            'state_id': post.get('state_id', ''),
            'region_id': post.get('region_id', ''),
            'project_id': post.get('project_id', ''),
            'min_price': post.get('min_price', ''),
            'max_price': post.get('max_price', ''),
            'min_area': post.get('min_area', ''),
            'max_area': post.get('max_area', ''),
            'bedrooms': post.get('bedrooms', ''),
            'bathrooms': post.get('bathrooms', ''),
            'type_service': post.get('type_service', ''),
            'property_state': post.get('property_state', ''),
            'garage': post.get('garage', ''),
            'garden': post.get('garden', ''),
            'pool': post.get('pool', ''),
            'elevator': post.get('elevator', ''),
            'order': post.get('order', 'relevance'),
            'page': post.get('page', 1),
            'ppg': post.get('ppg', 20),
        }

    def _build_context_domain(self, search_context, filters):
        """Construye dominio base según contexto"""
        domain = [('is_property', '=', True), ('active', '=', True)]

        # Estados permitidos según contexto
        allowed_states = search_context.get('allowed_states', ['free'])
        domain.append(('state', 'in', allowed_states))

        return domain

    def _apply_location_filters(self, domain, filters):
        """Aplica filtros jerárquicos de ubicación"""
        location_domain = []

        # Prioridad: región > ciudad > estado
        if filters.get('region_id'):
            try:
                location_domain.append(('region_id', '=', int(filters['region_id'])))
            except (ValueError, TypeError):
                pass
        elif filters.get('city_id'):
            try:
                location_domain.append(('city_id', '=', int(filters['city_id'])))
            except (ValueError, TypeError):
                pass
        elif filters.get('state_id'):
            try:
                location_domain.append(('state_id', '=', int(filters['state_id'])))
            except (ValueError, TypeError):
                pass

        # Filtro por proyecto
        if filters.get('project_id'):
            try:
                location_domain.append(('project_worksite_id', '=', int(filters['project_id'])))
            except (ValueError, TypeError):
                pass

        if location_domain:
            domain = expression.AND([domain, location_domain])

        return domain

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
        # MEJORADO: Manejo explícito de booleanos y strings
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

    def _apply_price_area_filters(self, domain, filters):
        """Aplica filtros de precio y área"""
        # Precio (según tipo de servicio)
        price_field = self._get_price_field_by_context(filters.get('type_service', ''))

        if filters.get('min_price'):
            try:
                domain.append((price_field, '>=', float(filters['min_price'])))
            except (ValueError, TypeError):
                pass

        if filters.get('max_price'):
            try:
                domain.append((price_field, '<=', float(filters['max_price'])))
            except (ValueError, TypeError):
                pass

        # Área
        if filters.get('min_area'):
            try:
                domain.append(('property_area', '>=', float(filters['min_area'])))
            except (ValueError, TypeError):
                pass

        if filters.get('max_area'):
            try:
                domain.append(('property_area', '<=', float(filters['max_area'])))
            except (ValueError, TypeError):
                pass

        return domain

    def _apply_amenities_filters(self, domain, filters):
        """Aplica filtros de amenidades booleanas"""
        if filters.get('garage'):
            domain.append(('garage', '=', True))
        if filters.get('garden'):
            domain.append(('garden', '=', True))
        if filters.get('pool'):
            domain.append(('pools', '=', True))
        if filters.get('elevator'):
            domain.append(('elevator', '=', True))

        return domain

    def _get_price_field_by_context(self, type_service):
        """Retorna campo de precio según tipo de servicio"""
        if type_service in ['rent', 'vacation_rent']:
            return 'net_rental_price'
        return 'net_price'

    def _get_smart_order(self, order_param):
        """Traduce parámetros de ordenamiento a SQL"""
        order_map = {
            'relevance': 'sequence ASC, id DESC',
            'price_asc': 'net_price ASC NULLS LAST, id DESC',
            'price_desc': 'net_price DESC NULLS LAST, id DESC',
            'area_asc': 'property_area ASC NULLS LAST, id DESC',
            'area_desc': 'property_area DESC NULLS LAST, id DESC',
            'newest': 'create_date DESC NULLS LAST, id DESC',
            'oldest': 'create_date ASC NULLS LAST, id DESC',
            'name': 'name ASC, id DESC',
        }
        return order_map.get(order_param, 'sequence ASC, id DESC')

    def _mark_new_properties(self, properties):
        """Marca propiedades creadas en los últimos 30 días"""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        for prop in properties:
            prop.is_new = prop.create_date >= thirty_days_ago if prop.create_date else False

    def _build_query_url(self, base_url, filters):
        """Construye QueryURL para preservar filtros en paginación"""
        if QueryURL:
            return QueryURL(base_url, **filters)
        # Fallback manual si QueryURL no está disponible
        return type('QueryURL', (), {'__call__': lambda *args, **kw: base_url})()

    def _prepare_search_values(self, properties, total, filters, search_context, context, page, ppg, domain, keep):
        """Prepara diccionario de valores para el template"""
        return {
            'properties': properties,
            'total_properties': total,
            'search_context': context,
            'context_config': search_context,
            'page': page,
            'ppg': ppg,
            'pager': self._get_pager(total, page, ppg, f'/property/search/{context}', filters),
            'keep': keep,
            **filters,  # Incluir todos los filtros
            # Datos para filtros con contadores
            'property_types': self._get_property_types_with_counts(domain),
            'cities': self._get_cities_with_counts(domain),
            'states': self._get_states_with_counts(domain),
            'regions': self._get_regions_with_counts(domain, filters.get('city_id'), filters.get('state_id')),
            'projects': self._get_projects_with_counts(domain, filters.get('city_id'), filters.get('state_id'), filters.get('region_id')),
            'price_ranges': self._get_price_ranges_by_type(filters.get('property_type'), filters.get('type_service')),
            'area_ranges': self._get_area_ranges(),
            'bedroom_options': [1, 2, 3, 4, 5, 6],
            'bathroom_options': [1, 2, 3, 4, 5],
            'service_types': [
                {'value': 'sale', 'label': _('Venta')},
                {'value': 'rent', 'label': _('Arriendo')},
                {'value': 'vacation_rent', 'label': _('Arriendo Vacacional')},
            ],
        }

    def _serialize_properties(self, properties, search_context):
        """Serializa propiedades para respuesta JSON"""
        # Obtener website una sola vez (optimización)
        website = request.env['website'].get_current_website()

        data = []
        for prop in properties:
            # Determinar precio según tipo de servicio
            if prop.type_service in ('rent', 'vacation_rent'):
                price = prop.net_rental_price or 0
            else:
                price = prop.net_price or 0

            # Información del proyecto si existe
            project_id = prop.project_worksite_id.id if prop.project_worksite_id else None
            project_name = prop.project_worksite_id.name if prop.project_worksite_id else None

            # Obtener URL de imagen optimizada usando website.image_url
            # Esto maneja CDN, cache, lazy loading y tamaños optimizados automáticamente
            image_url = website.image_url(prop, 'image_512') if prop.image_512 else '/theme_bohio_real_estate/static/src/img/placeholder.jpg'

            # Obtener valores de selection fields correctamente
            property_type_label = ''
            if prop.property_type:
                selection_field = prop._fields['property_type']
                if callable(selection_field.selection):
                    selection_list = selection_field.selection(prop.env)
                else:
                    selection_list = selection_field.selection
                property_type_label = dict(selection_list).get(prop.property_type, '')

            type_service_label = ''
            if prop.type_service:
                selection_field = prop._fields['type_service']
                if callable(selection_field.selection):
                    selection_list = selection_field.selection(prop.env)
                else:
                    selection_list = selection_field.selection
                type_service_label = dict(selection_list).get(prop.type_service, '')

            data.append({
                'id': prop.id,
                'name': prop.name,
                'default_code': prop.default_code or '',
                'property_type': property_type_label,
                'type_service': type_service_label,
                'price': price,
                'currency_symbol': prop.currency_id.symbol or '$',
                'bedrooms': int(prop.num_bedrooms) if prop.num_bedrooms else 0,
                'bathrooms': int(prop.num_bathrooms) if prop.num_bathrooms else 0,
                'area': float(prop.property_area) if prop.property_area else 0,
                'city': prop.city_id.name if prop.city_id else prop.city or '',
                'state': prop.state_id.name if prop.state_id else '',
                'neighborhood': prop.neighborhood or '',
                'latitude': float(prop.latitude) if prop.latitude else None,
                'longitude': float(prop.longitude) if prop.longitude else None,
                'project_id': project_id,
                'project_name': project_name,
                'image_url': image_url,
                'url': f'/property/{prop.id}',
                'show_price': search_context.get('show_price', True),
            })
        return data

    # =================== MÉTODOS AUXILIARES - AUTOCOMPLETADO ===================

    def _normalize_search_term(self, term):
        """
        Normaliza término de búsqueda sin acentos.

        NOTA: Este método NO es necesario cuando se usa 'ilike' en PostgreSQL,
        ya que Odoo automáticamente aplica unaccent() de PostgreSQL.
        Se mantiene solo por compatibilidad con búsquedas en Python.
        """
        import unicodedata
        normalized = ''.join(
            c for c in unicodedata.normalize('NFD', term)
            if unicodedata.category(c) != 'Mn'
        )
        return normalized.lower().strip()

    def _autocomplete_cities(self, term, search_context, limit):
        """
        Autocompletado de ciudades con búsqueda optimizada.

        OPTIMIZACIÓN: PostgreSQL's ilike automáticamente usa unaccent()
        por lo que no necesitamos normalizar manualmente el término.
        La búsqueda 'ilike' es case-insensitive y accent-insensitive.
        """
        results = []

        # Construir dominio con búsqueda flexible
        # ilike ya incluye unaccent() de PostgreSQL automáticamente
        # Solo necesitamos buscar con y sin wildcards para mayor flexibilidad
        domain = [
            '|',
            ('name', 'ilike', term),           # Encuentra: "monter" en "Montería"
            ('name', 'ilike', f'%{term}%'),    # Encuentra: "onter" en "Montería"
        ]

        # Agregar filtro de país si está configurado
        if request.env.company.country_id:
            domain.append(('country_id', '=', request.env.company.country_id.id))

        cities = request.env['res.city'].sudo().search(domain, limit=limit * 2)

        _logger.debug(f'[AUTOCOMPLETE] Ciudades encontradas para "{term}": {len(cities)} ({[c.name for c in cities[:5]]})')

        for city in cities:
            domain = [
                ('is_property', '=', True),
                ('city_id', '=', city.id),
                ('state', 'in', search_context.get('allowed_states', ['free']))
            ]
            property_count = request.env['product.template'].sudo().search_count(domain)

            # Siempre incluir la ciudad aunque no tenga propiedades (para mejor UX)
            results.append({
                'id': f'city_{city.id}',
                'type': 'city',
                'name': city.name,
                'full_name': f'{city.name}, {city.state_id.name if city.state_id else ""}',
                'label': f'<i class="fa fa-map-marker text-primary"></i> <b>{city.name}</b>, {city.state_id.name if city.state_id else ""}',
                'property_count': property_count,
                'priority': 3 if property_count > 0 else 1,
                'city_id': city.id,
                'state_id': city.state_id.id if city.state_id else None,
            })

        return results

    def _autocomplete_regions(self, term, search_context, limit):
        """
        Autocompletado de regiones/barrios con búsqueda optimizada.

        OPTIMIZACIÓN: Usa ilike de PostgreSQL con unaccent() automático.
        """
        results = []
        Region = request.env['region.region'].sudo()

        if 'region.region' not in request.env:
            return results

        # Búsqueda optimizada con ilike (incluye unaccent automático)
        domain = [
            '|',
            ('name', 'ilike', term),
            ('name', 'ilike', f'%{term}%'),
        ]

        regions = Region.search(domain, limit=limit * 2)

        _logger.debug(f'[AUTOCOMPLETE] Regiones encontradas para "{term}": {len(regions)} ({[r.name for r in regions[:5]]})')

        for region in regions:
            domain = [
                ('is_property', '=', True),
                ('region_id', '=', region.id),
                ('state', 'in', search_context.get('allowed_states', ['free']))
            ]
            property_count = request.env['product.template'].sudo().search_count(domain)

            # Siempre incluir la región aunque no tenga propiedades
            results.append({
                'id': f'region_{region.id}',
                'type': 'region',
                'name': region.name,
                'full_name': f'{region.name}, {region.city_id.name if region.city_id else ""}',
                'label': f'<i class="fa fa-home text-success"></i> {region.name} <small class="text-muted">({region.city_id.name if region.city_id else ""})</small>',
                'property_count': property_count,
                'priority': 2 if property_count > 0 else 1,
                'region_id': region.id,
                'city_id': region.city_id.id if region.city_id else None,
            })

        return results

    def _autocomplete_projects(self, term, search_context, limit):
        """
        Autocompletado de proyectos con búsqueda optimizada.

        OPTIMIZACIÓN: Usa ilike de PostgreSQL con unaccent() automático.
        """
        results = []
        Project = request.env['project.worksite'].sudo()

        if 'project.worksite' not in request.env:
            return results

        # Búsqueda optimizada con ilike (incluye unaccent automático)
        projects = Project.search([
            '|',
            ('name', 'ilike', term),
            ('name', 'ilike', f'%{term}%'),
        ], limit=limit * 2)

        for project in projects:
            domain = [
                ('is_property', '=', True),
                ('project_worksite_id', '=', project.id),
                ('state', 'in', search_context.get('allowed_states', ['free']))
            ]
            property_count = request.env['product.template'].sudo().search_count(domain)

            if property_count > 0:
                results.append({
                    'id': f'project_{project.id}',
                    'type': 'project',
                    'name': project.name,
                    'full_name': f'{project.name} (Proyecto)',
                    'label': f'<i class="fa fa-building text-warning"></i> {project.name} <small class="text-muted">(Proyecto)</small>',
                    'property_count': property_count,
                    'priority': 2,
                    'project_id': project.id,
                })

        return results

    def _autocomplete_properties(self, term, search_context, limit):
        """
        Autocompletado de propiedades por código o nombre.

        OPTIMIZACIÓN: Usa ilike de PostgreSQL con unaccent() automático.
        Búsqueda optimizada en nombre, código y barcode.
        """
        results = []

        # Búsqueda optimizada con ilike (incluye unaccent automático)
        domain = [
            ('is_property', '=', True),
            ('state', 'in', search_context.get('allowed_states', ['free'])),
            '|', '|', '|', '|', '|',
            ('name', 'ilike', term),
            ('name', 'ilike', f'%{term}%'),
            ('default_code', 'ilike', term),
            ('default_code', 'ilike', f'%{term}%'),
            ('barcode', 'ilike', term),
            ('barcode', 'ilike', f'%{term}%'),
        ]

        properties = request.env['product.template'].sudo().search(domain, limit=limit)

        for prop in properties:
            results.append({
                'id': f'property_{prop.id}',
                'type': 'property',
                'name': prop.name,
                'full_name': f'{prop.default_code or ""} - {prop.name}',
                'label': f'<i class="fa fa-key text-info"></i> {prop.default_code or ""} - {prop.name}',
                'property_count': 1,
                'priority': 1,
                'property_id': prop.id,
            })

        return results

    # =================== MÉTODOS AUXILIARES - CONTADORES ===================

    def _get_property_types_with_counts(self, base_domain):
        """Obtiene tipos de propiedad con contadores usando read_group"""
        Property = request.env['product.template'].sudo()
        type_data = Property.read_group(base_domain, ['property_type'], ['property_type'])
        type_labels = dict(Property._fields['property_type'].selection)

        return [
            {
                'value': item['property_type'],
                'label': type_labels.get(item['property_type'], item['property_type']),
                'count': item['property_type_count']
            }
            for item in type_data if item['property_type']
        ]

    def _get_cities_with_counts(self, base_domain):
        """Obtiene ciudades con contadores"""
        Property = request.env['product.template'].sudo()
        city_data = Property.read_group(base_domain, ['city_id'], ['city_id'])

        return [
            {
                'id': item['city_id'][0],
                'name': item['city_id'][1],
                'count': item['city_id_count']
            }
            for item in city_data if item['city_id']
        ]

    def _get_states_with_counts(self, base_domain):
        """Obtiene departamentos/estados con contadores"""
        Property = request.env['product.template'].sudo()
        state_data = Property.read_group(base_domain, ['state_id'], ['state_id'])

        return [
            {
                'id': item['state_id'][0],
                'name': item['state_id'][1],
                'count': item['state_id_count']
            }
            for item in state_data if item['state_id']
        ]

    def _get_regions_with_counts(self, base_domain, city_id, state_id):
        """Obtiene regiones con contadores (dependientes de ciudad/estado)"""
        Property = request.env['product.template'].sudo()
        region_domain = list(base_domain)

        # Filtrar por ciudad o estado si están seleccionados
        if city_id:
            try:
                region_domain.append(('city_id', '=', int(city_id)))
            except (ValueError, TypeError):
                pass
        elif state_id:
            try:
                region_domain.append(('state_id', '=', int(state_id)))
            except (ValueError, TypeError):
                pass

        region_data = Property.read_group(region_domain, ['region_id'], ['region_id'])

        return [
            {
                'id': item['region_id'][0],
                'name': item['region_id'][1],
                'count': item['region_id_count']
            }
            for item in region_data if item['region_id']
        ]

    def _get_projects_with_counts(self, base_domain, city_id, state_id, region_id):
        """Obtiene proyectos con contadores (dependientes de ubicación)"""
        Property = request.env['product.template'].sudo()

        if 'project.worksite' not in request.env:
            return []

        project_domain = list(base_domain)

        # Filtrar por ubicación si está seleccionada
        if region_id:
            try:
                project_domain.append(('region_id', '=', int(region_id)))
            except (ValueError, TypeError):
                pass
        elif city_id:
            try:
                project_domain.append(('city_id', '=', int(city_id)))
            except (ValueError, TypeError):
                pass
        elif state_id:
            try:
                project_domain.append(('state_id', '=', int(state_id)))
            except (ValueError, TypeError):
                pass

        project_data = Property.read_group(project_domain, ['project_worksite_id'], ['project_worksite_id'])

        return [
            {
                'id': item['project_worksite_id'][0],
                'name': item['project_worksite_id'][1],
                'count': item['project_worksite_id_count']
            }
            for item in project_data if item['project_worksite_id']
        ]

    def _get_price_ranges_by_type(self, property_type, type_service):
        """Define rangos de precio según tipo de propiedad y servicio
        Args:
            property_type: Tipo de propiedad (usado para rangos personalizados futuros)
            type_service: Tipo de servicio (rent, sale, vacation_rent)
        """
        is_rental = type_service in ['rent', 'vacation_rent']

        if is_rental:
            return [
                {'min': 0, 'max': 1000000, 'label': 'Hasta $1M'},
                {'min': 1000000, 'max': 2000000, 'label': '$1M - $2M'},
                {'min': 2000000, 'max': 3000000, 'label': '$2M - $3M'},
                {'min': 3000000, 'max': 5000000, 'label': '$3M - $5M'},
                {'min': 5000000, 'max': 10000000, 'label': '$5M - $10M'},
                {'min': 10000000, 'max': 0, 'label': 'Más de $10M'},
            ]
        else:
            return [
                {'min': 0, 'max': 100000000, 'label': 'Hasta $100M'},
                {'min': 100000000, 'max': 200000000, 'label': '$100M - $200M'},
                {'min': 200000000, 'max': 300000000, 'label': '$200M - $300M'},
                {'min': 300000000, 'max': 500000000, 'label': '$300M - $500M'},
                {'min': 500000000, 'max': 1000000000, 'label': '$500M - $1,000M'},
                {'min': 1000000000, 'max': 0, 'label': 'Más de $1,000M'},
            ]

    def _get_area_ranges(self):
        """Define rangos de área"""
        return [
            {'min': 0, 'max': 50, 'label': 'Hasta 50 m²'},
            {'min': 50, 'max': 100, 'label': '50 - 100 m²'},
            {'min': 100, 'max': 150, 'label': '100 - 150 m²'},
            {'min': 150, 'max': 200, 'label': '150 - 200 m²'},
            {'min': 200, 'max': 300, 'label': '200 - 300 m²'},
            {'min': 300, 'max': 500, 'label': '300 - 500 m²'},
            {'min': 500, 'max': 0, 'label': 'Más de 500 m²'},
        ]

    def _get_pager(self, total, page, ppg, url, params):
        """Genera datos de paginación"""
        total_pages = (total + ppg - 1) // ppg if ppg > 0 else 0

        return {
            'page': page,
            'total_pages': total_pages,
            'total': total,
            'ppg': ppg,
            'prev_url': f"{url}?page={page-1}" if page > 1 else None,
            'next_url': f"{url}?page={page+1}" if page < total_pages else None,
        }

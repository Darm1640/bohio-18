# -*- coding: utf-8 -*-
from odoo import http, fields, _
from odoo.http import request
from odoo.osv import expression
from datetime import datetime, timedelta
import json
import logging

# Helpers de Odoo para URLs (mismo patrón que website_sale)
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.portal.controllers.portal import _build_url_w_params

_logger = logging.getLogger(__name__)


class BohioRealEstateController(http.Controller):

    def _safe_stratum_to_int(self, stratum_value):
        """
        Convierte stratum a int de forma segura.
        Si es 'commercial', 'no_stratified' u otro string, retorna 0.
        Si es un número o string numérico, lo convierte a int.
        """
        if not stratum_value:
            return 0

        # Si ya es un int, retornar directamente
        if isinstance(stratum_value, int):
            return stratum_value

        # Si es string, intentar convertir
        if isinstance(stratum_value, str):
            # Si es 'commercial', 'no_stratified', etc., retornar 0
            if not stratum_value.isdigit():
                return 0
            try:
                return int(stratum_value)
            except ValueError:
                return 0

        # Para cualquier otro tipo, retornar 0
        return 0

    def _serialize_properties_fast(self, properties_data, context_type='public'):
        """
        Serializa propiedades desde search_read para respuestas JSON rápidas.
        Usa datos ya cargados por search_read (evita N+1 queries).

        Args:
            properties_data: Lista de dicts desde search_read
            context_type: 'public', 'admin', o 'portal'

        Returns:
            Lista de dicts serializados para frontend
        """
        base_url = request.httprequest.url_root.rstrip('/')
        serialized = []

        for prop in properties_data:
            # Determinar precio según tipo de servicio
            price = 0
            type_service = prop.get('type_service', '')
            if 'rent' in type_service or 'Arriendo' in type_service:
                price = prop.get('net_rental_price', 0)
            else:
                price = prop.get('net_price', 0)

            # Obtener nombres de relaciones (Many2one viene como [id, name])
            city_id = prop.get('city_id')
            city_name = city_id[1] if city_id and isinstance(city_id, (list, tuple)) else prop.get('city', '')

            state_id = prop.get('state_id')
            state_name = state_id[1] if state_id and isinstance(state_id, (list, tuple)) else ''

            project_id = prop.get('project_worksite_id')
            project_name = project_id[1] if project_id and isinstance(project_id, (list, tuple)) else ''
            project_id_int = project_id[0] if project_id and isinstance(project_id, (list, tuple)) else None

            # Imagen - search_read devuelve el campo directamente
            image_data = prop.get('image_512')
            if image_data:
                image_url = f"{base_url}/web/image/product.template/{prop['id']}/image_512"
            else:
                image_url = f"{base_url}/theme_bohio_real_estate/static/src/img/placeholder.jpg"

            serialized.append({
                'id': prop['id'],
                'name': prop.get('name', 'Sin nombre'),
                'code': prop.get('default_code', ''),
                'property_type': prop.get('property_type', ''),
                'type_service': type_service,
                'price': price,
                'area': prop.get('property_area', 0),
                'bedrooms': prop.get('num_bedrooms', 0),
                'bathrooms': prop.get('num_bathrooms', 0),
                'city': city_name,
                'state': state_name,
                'neighborhood': prop.get('neighborhood', ''),
                'latitude': prop.get('latitude', 0.0),
                'longitude': prop.get('longitude', 0.0),
                'project_id': project_id_int,
                'project_name': project_name,
                'image_url': image_url,
                'url': f"/propiedad/{prop['id']}/{prop.get('name', '').replace(' ', '-').lower()}",
            })

        return serialized

    @http.route('/sobre-nosotros', type='http', auth='public', website=True)
    def sobre_nosotros(self, **kwargs):
        """Página Sobre Nosotros BOHIO"""
        return request.render('theme_bohio_real_estate.bohio_sobre_nosotros_page', {})

    @http.route('/servicios', type='http', auth='public', website=True)
    def servicios(self, **kwargs):
        """Página de Servicios BOHIO"""
        return request.render('theme_bohio_real_estate.bohio_servicios_page', {})

    @http.route('/privacy', type='http', auth='public', website=True)
    def privacy(self, **kwargs):
        """Política de Privacidad"""
        return request.render('theme_bohio_real_estate.privacy_page', {})

    @http.route('/terms', type='http', auth='public', website=True)
    def terms(self, **kwargs):
        """Términos y Condiciones"""
        return request.render('theme_bohio_real_estate.terms_page', {})

    @http.route('/properties', type='http', auth='public', website=True)
    def properties_shop(self, **post):
        """Tienda de Propiedades - Vista Avanzada con Filtros Completos"""
        search_term = post.get('search', '').strip()
        property_type = post.get('property_type', '')
        city_id = post.get('city_id', '')
        state_id = post.get('state_id', '')
        region_id = post.get('region_id', '')
        project_id = post.get('project_id', '')

        # Filtros adicionales
        min_price = post.get('min_price', 0)
        max_price = post.get('max_price', 0)
        min_area = post.get('min_area', 0)
        max_area = post.get('max_area', 0)
        bedrooms = post.get('bedrooms', '')
        bathrooms = post.get('bathrooms', '')
        type_service = post.get('type_service', '')

        # Filtro por estado de propiedad (solo disponibles por defecto)
        property_state = post.get('property_state', 'free')

        # Filtros booleanos
        garage = post.get('garage', '')
        garden = post.get('garden', '')
        pool = post.get('pool', '')
        elevator = post.get('elevator', '')

        # Construir dominio de búsqueda
        domain = [('is_property', '=', True), ('active', '=', True)]

        # Filtro de estado (solo mostrar disponibles por defecto)
        if property_state and property_state != 'all':
            domain.append(('state', '=', property_state))
        elif not property_state:
            domain.append(('state', '=', 'free'))

        # Aplicar filtros de ubicación jerárquica
        location_domain = self._build_location_domain(search_term, city_id, state_id, region_id)
        if location_domain:
            domain = expression.AND([domain, location_domain])

        # Filtro por proyecto
        if project_id:
            try:
                domain.append(('project_worksite_id', '=', int(project_id)))
            except ValueError:
                pass

        # Aplicar filtros de tipo de propiedad
        if property_type:
            domain.append(('property_type', '=', property_type))

        # Filtros booleanos
        if garage:
            domain.append(('garage', '=', True))
        if garden:
            domain.append(('garden', '=', True))
        if pool:
            domain.append(('pools', '=', True))
        if elevator:
            domain.append(('elevator', '=', True))

        # Filtros de precio adaptados por tipo de servicio
        price_field = self._get_price_field_by_context(type_service)
        if min_price:
            try:
                domain.append((price_field, '>=', float(min_price)))
            except ValueError:
                pass
        if max_price:
            try:
                domain.append((price_field, '<=', float(max_price)))
            except ValueError:
                pass

        # Filtros de área
        if min_area:
            try:
                domain.append(('property_area', '>=', float(min_area)))
            except ValueError:
                pass
        if max_area:
            try:
                domain.append(('property_area', '<=', float(max_area)))
            except ValueError:
                pass

        # Filtros de habitaciones y baños
        if bedrooms:
            try:
                domain.append(('num_bedrooms', '>=', int(bedrooms)))
            except ValueError:
                pass
        if bathrooms:
            try:
                domain.append(('num_bathrooms', '>=', int(bathrooms)))
            except ValueError:
                pass

        # Filtro de tipo de servicio
        if type_service:
            if type_service == 'sale_rent':
                domain.append(('type_service', 'in', ['sale', 'rent', 'sale_rent']))
            else:
                domain.append(('type_service', 'in', [type_service, 'sale_rent']))

        # Ordenamiento inteligente
        order = self._get_smart_order(post.get('order', 'relevance'))

        # Paginación
        page = int(post.get('page', 1))
        ppg = int(post.get('ppg', 20))
        offset = (page - 1) * ppg

        # Búsqueda de propiedades
        Property = request.env['product.template'].sudo()
        total_properties = Property.search_count(domain)
        properties = Property.search(domain, limit=ppg, offset=offset, order=order)

        # Marcar propiedades nuevas (creadas en los últimos 30 días)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        for prop in properties:
            prop.is_new = prop.create_date >= thirty_days_ago if prop.create_date else False

        # QueryURL helper (mismo patrón que website_sale) para mantener filtros en URLs
        keep = QueryURL('/properties',
            search=search_term,
            property_type=property_type,
            city_id=city_id,
            state_id=state_id,
            region_id=region_id,
            project_id=project_id,
            property_state=property_state,
            min_price=min_price,
            max_price=max_price,
            min_area=min_area,
            max_area=max_area,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            type_service=type_service,
            garage=garage,
            garden=garden,
            pool=pool,
            elevator=elevator,
            order=post.get('order', 'relevance')
        )

        # Preparar valores para renderizado
        values = {
            'properties': properties,
            'total_properties': total_properties,
            'search_term': search_term,
            'property_type': property_type,
            'city_id': city_id,
            'state_id': state_id,
            'region_id': region_id,
            'project_id': project_id,
            'property_state': property_state,
            'min_price': min_price,
            'max_price': max_price,
            'min_area': min_area,
            'max_area': max_area,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'type_service': type_service,
            'garage': garage,
            'garden': garden,
            'pool': pool,
            'elevator': elevator,
            'order': post.get('order', 'relevance'),
            'page': page,
            'ppg': ppg,
            'pager': self._get_pager(total_properties, page, ppg, '/properties', post),
            'keep': keep,  # Helper para construir URLs con filtros preservados

            # Datos para filtros con contadores
            'property_types': self._get_property_types_with_counts(domain),
            'cities': self._get_cities_with_counts(domain),
            'states': self._get_states_with_counts(domain),
            'regions': self._get_regions_with_counts(domain, city_id, state_id),
            'projects': self._get_projects_with_counts(domain, city_id, state_id, region_id),
            'price_ranges': self._get_price_ranges_by_type(property_type, type_service),
            'area_ranges': self._get_area_ranges(),
            'bedroom_options': [1, 2, 3, 4, 5],
            'bathroom_options': [1, 2, 3, 4],
            'property_states': [
                {'value': 'free', 'label': _('Disponible')},
                {'value': 'reserved', 'label': _('Reservada')},
                {'value': 'sold', 'label': _('Vendida')},
                {'value': 'on_lease', 'label': _('En Arriendo')},
                {'value': 'all', 'label': _('Todas')},
            ],
            'service_types': [
                {'value': 'sale', 'label': _('Venta')},
                {'value': 'rent', 'label': _('Arriendo')},
                {'value': 'vacation_rent', 'label': _('Arriendo Vacacional')},
            ],
        }

        return request.render('theme_bohio_real_estate.properties_shop', values)

    @http.route('/properties/map', type='http', auth='public', website=True)
    def properties_map(self, **kwargs):
        """Mapa de Propiedades con Filtros"""
        # Obtener ciudades para los filtros
        cities = request.env['res.city'].sudo().search([], order='name')

        # Obtener estados/departamentos
        states = request.env['res.country.state'].sudo().search([
            ('country_id.code', '=', 'CO')
        ], order='name')

        # Obtener propiedades activas con ubicación
        properties = request.env['product.template'].sudo().search([
            ('is_property', '=', True),
            ('website_published', '=', True),
            ('latitude', '!=', False),
            ('longitude', '!=', False),
        ])

        # Preparar datos para el mapa
        properties_data = []
        for prop in properties:
            properties_data.append({
                'id': prop.id,
                'name': prop.name,
                'lat': prop.latitude,
                'lng': prop.longitude,
                'price': prop.list_price,
                'currency_symbol': prop.currency_id.symbol or '$',
                'property_type': dict(prop._fields['property_type'].selection).get(prop.property_type, ''),
                'type_service': dict(prop._fields['type_service'].selection).get(prop.type_service, ''),
                'bedrooms': prop.num_bedrooms,
                'bathrooms': prop.num_bathrooms,
                'area': prop.property_area,
                'city': prop.city,
                'image': f'/web/image/product.template/{prop.id}/image_1920',
            })

        return request.render('theme_bohio_real_estate.properties_list_map_page', {
            'cities': cities,
            'states': states,
            'properties_json': properties_data,
        })

    # =================== AUTOCOMPLETADO AVANZADO ===================

    # DESHABILITADO - Usar endpoint en property_search.py con búsqueda aproximada sin acentos
    @http.route(['/property/search/autocomplete'], type='json', auth='public', website=True)
    def property_search_autocomplete(self, term='', limit=10, context='public', subdivision='all'):
        """Autocompletado inteligente con jerarquía y proyectos"""
        if not term or len(term) < 2:
            return {'results': []}

        results = []

        # 1. Buscar ciudades
        cities = request.env['res.city'].sudo().search([
            ('name', 'ilike', term),
            ('country_id', '=', request.env.company.country_id.id)
        ], limit=limit)

        for city in cities:
            property_count = request.env['product.template'].sudo().search_count([
                ('is_property', '=', True),
                ('city_id', '=', city.id),
                ('state', 'in', ['free', 'on_lease'])
            ])

            if property_count > 0:
                results.append({
                    'id': f'city_{city.id}',
                    'type': 'city',
                    'name': city.name,
                    'full_name': f'{city.name}, {city.state_id.name}',
                    'label': f'<i class="fa fa-map-marker text-primary"></i> <b>{city.name}</b>, {city.state_id.name}',
                    'property_count': property_count,
                    'priority': 3,
                    'city_id': city.id,
                    'state_id': city.state_id.id,
                })

        # 2. Buscar departamentos
        states = request.env['res.country.state'].sudo().search([
            ('name', 'ilike', term),
            ('country_id', '=', request.env.company.country_id.id)
        ], limit=limit)

        for state in states:
            property_count = request.env['product.template'].sudo().search_count([
                ('is_property', '=', True),
                ('state_id', '=', state.id),
                ('state', 'in', ['free', 'on_lease'])
            ])

            if property_count > 0:
                results.append({
                    'id': f'state_{state.id}',
                    'type': 'state',
                    'name': state.name,
                    'full_name': f'{state.name} (Departamento)',
                    'label': f'<i class="fa fa-globe text-info"></i> {state.name} <small class="text-muted">(Departamento)</small>',
                    'property_count': property_count,
                    'priority': 2,
                    'state_id': state.id,
                })

        # 3. Buscar barrios
        Region = request.env['region.region'].sudo()
        if Region._name in request.env:
            regions = Region.search([('name', 'ilike', term)], limit=limit)

            for region in regions:
                property_count = request.env['product.template'].sudo().search_count([
                    ('is_property', '=', True),
                    ('region_id', '=', region.id),
                    ('state', 'in', ['free', 'on_lease'])
                ])

                if property_count > 0:
                    results.append({
                        'id': f'region_{region.id}',
                        'type': 'region',
                        'name': region.name,
                        'full_name': f'{region.name}, {region.city_id.name}, {region.state_id.name}',
                        'label': f'<i class="fa fa-home text-success"></i> {region.name} <small class="text-muted">({region.city_id.name})</small>',
                        'property_count': property_count,
                        'priority': 1,
                        'region_id': region.id,
                        'city_id': region.city_id.id,
                        'state_id': region.state_id.id,
                    })

        # 4. Buscar proyectos
        Project = request.env['project.worksite'].sudo()
        if Project._name in request.env:
            projects = Project.search([
                ('name', 'ilike', term),
                ('is_enabled', '=', True)
            ], limit=limit)

            for project in projects:
                property_count = request.env['product.template'].sudo().search_count([
                    ('project_worksite_id', '=', project.id),
                    ('is_property', '=', True),
                    ('state', 'in', ['free', 'on_lease'])
                ])

                if property_count > 0:
                    location_parts = []
                    if project.region_id:
                        location_parts.append(project.region_id.name)
                    if project.region_id and project.region_id.city_id:
                        location_parts.append(project.region_id.city_id.name)

                    location_text = ', '.join(location_parts) if location_parts else ''

                    results.append({
                        'id': f'project_{project.id}',
                        'type': 'project',
                        'name': project.name,
                        'full_name': f'{project.name} - {location_text}',
                        'label': f'<i class="fa fa-building text-warning"></i> <b>{project.name}</b> <small class="text-muted">({location_text})</small>',
                        'property_count': property_count,
                        'priority': 2,
                        'project_id': project.id,
                        'region_id': project.region_id.id if project.region_id else '',
                        'city_id': project.region_id.city_id.id if project.region_id and project.region_id.city_id else '',
                        'state_id': project.region_id.state_id.id if project.region_id and project.region_id.state_id else '',
                    })

        # Ordenar por prioridad y cantidad
        results.sort(key=lambda x: (x['priority'], x['property_count']), reverse=True)

        return {
            'success': True,
            'results': results[:limit]
        }

    @http.route(['/property/characteristics/by_type'], type='json', auth='public', website=True)
    def get_characteristics_by_type(self, property_type=None, **kwargs):
        """Obtiene características completas agrupadas por tipo de propiedad"""
        characteristics_map = {
            'apartment': {
                'basicas': {
                    'label': _('Características Básicas'),
                    'icon': 'fa-home',
                    'fields': [
                        {'name': 'num_bedrooms', 'label': _('Habitaciones'), 'icon': 'fa-bed'},
                        {'name': 'num_bathrooms', 'label': _('Baños'), 'icon': 'fa-bath'},
                        {'name': 'property_area', 'label': _('Área'), 'icon': 'fa-arrows-alt', 'unit': 'm²'},
                        {'name': 'floor_number', 'label': _('Piso'), 'icon': 'fa-building'},
                        {'name': 'balcony', 'label': _('Balcón'), 'icon': 'fa-square', 'type': 'boolean'},
                    ]
                },
                'parqueadero': {
                    'label': _('Parqueadero'),
                    'icon': 'fa-car',
                    'fields': [
                        {'name': 'covered_parking', 'label': _('Cubiertos'), 'icon': 'fa-car'},
                        {'name': 'uncovered_parking', 'label': _('Descubiertos'), 'icon': 'fa-car'},
                        {'name': 'visitors_parking', 'label': _('Visitantes'), 'icon': 'fa-users', 'type': 'boolean'},
                    ]
                },
                'comodidades': {
                    'label': _('Comodidades'),
                    'icon': 'fa-star',
                    'fields': [
                        {'name': 'elevator', 'label': _('Ascensor'), 'icon': 'fa-arrows-v', 'type': 'boolean'},
                        {'name': 'air_conditioning', 'label': _('Aire Acondicionado'), 'icon': 'fa-snowflake', 'type': 'boolean'},
                        {'name': 'furnished', 'label': _('Amoblado'), 'icon': 'fa-couch', 'type': 'boolean'},
                    ]
                },
            },
            'house': {
                'basicas': {
                    'label': _('Características Básicas'),
                    'icon': 'fa-home',
                    'fields': [
                        {'name': 'num_bedrooms', 'label': _('Habitaciones'), 'icon': 'fa-bed'},
                        {'name': 'num_bathrooms', 'label': _('Baños'), 'icon': 'fa-bath'},
                        {'name': 'property_area', 'label': _('Área'), 'icon': 'fa-arrows-alt', 'unit': 'm²'},
                        {'name': 'number_of_levels', 'label': _('Niveles'), 'icon': 'fa-layer-group'},
                    ]
                },
                'exteriores': {
                    'label': _('Áreas Exteriores'),
                    'icon': 'fa-tree',
                    'fields': [
                        {'name': 'garden', 'label': _('Jardín'), 'icon': 'fa-leaf', 'type': 'boolean'},
                        {'name': 'patio', 'label': _('Patio'), 'icon': 'fa-home', 'type': 'boolean'},
                        {'name': 'terrace', 'label': _('Terraza'), 'icon': 'fa-square', 'type': 'boolean'},
                        {'name': 'pools', 'label': _('Piscina'), 'icon': 'fa-swimming-pool', 'type': 'boolean'},
                    ]
                },
                'parqueadero': {
                    'label': _('Parqueadero y Garaje'),
                    'icon': 'fa-car',
                    'fields': [
                        {'name': 'garage', 'label': _('Garaje'), 'icon': 'fa-warehouse', 'type': 'boolean'},
                        {'name': 'n_garage', 'label': _('N° Garajes'), 'icon': 'fa-car'},
                    ]
                },
            },
        }

        if not property_type:
            return {'characteristics': characteristics_map}

        return {'characteristics': characteristics_map.get(property_type, {})}

    # =================== MÉTODOS AUXILIARES ===================

    def _get_price_field_by_context(self, type_service):
        """Determina qué campo de precio usar según el contexto"""
        if type_service in ['rent', 'vacation_rent']:
            return 'net_rental_price'
        else:
            return 'net_price'

    def _build_location_domain(self, search_term, city_id, state_id, region_id):
        """Construye dominio de búsqueda por ubicación"""
        domain = []

        if region_id:
            try:
                domain.append(('region_id', '=', int(region_id)))
            except ValueError:
                pass
        elif city_id:
            try:
                domain.append(('city_id', '=', int(city_id)))
            except ValueError:
                pass
        elif state_id:
            try:
                domain.append(('state_id', '=', int(state_id)))
            except ValueError:
                pass
        elif search_term:
            search_domain = [
                '|', '|', '|', '|', '|',
                ('search_text', 'ilike', search_term),
                ('address', 'ilike', search_term),
                ('neighborhood', 'ilike', search_term),
                ('city', 'ilike', search_term),
                ('municipality', 'ilike', search_term),
                ('department', 'ilike', search_term),
            ]
            domain = expression.AND([domain, search_domain]) if domain else search_domain

        return domain

    def _get_smart_order(self, order_param):
        """Traduce ordenamiento"""
        order_map = {
            'relevance': 'sequence ASC, id DESC',
            'price_asc': 'net_price ASC, id DESC',
            'price_desc': 'net_price DESC, id DESC',
            'area_asc': 'property_area ASC, id DESC',
            'area_desc': 'property_area DESC, id DESC',
            'newest': 'create_date DESC, id DESC',
            'oldest': 'create_date ASC, id DESC',
        }
        return order_map.get(order_param, 'sequence ASC, id DESC')

    def _get_property_types_with_counts(self, base_domain):
        """Tipos de propiedad con cantidades"""
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
        """Ciudades con cantidades"""
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
        """Departamentos con cantidades"""
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
        """Barrios con cantidades"""
        Property = request.env['product.template'].sudo()
        region_domain = list(base_domain)

        if city_id:
            try:
                region_domain.append(('city_id', '=', int(city_id)))
            except ValueError:
                pass
        elif state_id:
            try:
                region_domain.append(('state_id', '=', int(state_id)))
            except ValueError:
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
        """Proyectos con cantidad de propiedades disponibles"""
        Property = request.env['product.template'].sudo()
        Project = request.env['project.worksite'].sudo()

        if Project._name not in request.env:
            return []

        project_domain = [('is_enabled', '=', True)]

        if region_id:
            try:
                project_domain.append(('region_id', '=', int(region_id)))
            except ValueError:
                pass
        elif city_id:
            Region = request.env['region.region'].sudo()
            if Region._name in request.env:
                regions = Region.search([('city_id', '=', int(city_id))])
                if regions:
                    project_domain.append(('region_id', 'in', regions.ids))
        elif state_id:
            Region = request.env['region.region'].sudo()
            if Region._name in request.env:
                regions = Region.search([('state_id', '=', int(state_id))])
                if regions:
                    project_domain.append(('region_id', 'in', regions.ids))

        projects = Project.search(project_domain, order='name ASC')

        result = []
        for project in projects:
            property_count = Property.search_count([
                ('project_worksite_id', '=', project.id),
                ('is_property', '=', True),
                ('state', 'in', ['free', 'on_lease'])
            ])

            if property_count > 0:
                location_parts = []
                if project.address:
                    location_parts.append(project.address)
                if project.region_id:
                    location_parts.append(project.region_id.name)
                if project.region_id and project.region_id.city_id:
                    location_parts.append(project.region_id.city_id.name)
                if project.region_id and project.region_id.state_id:
                    location_parts.append(project.region_id.state_id.name)

                result.append({
                    'id': project.id,
                    'name': project.name,
                    'count': property_count,
                    'full_location': ', '.join(location_parts) if location_parts else '',
                    'region': project.region_id.name if project.region_id else '',
                    'city': project.region_id.city_id.name if project.region_id and project.region_id.city_id else '',
                    'state': project.region_id.state_id.name if project.region_id and project.region_id.state_id else '',
                    'address': project.address or '',
                })

        return result

    def _get_price_ranges_by_type(self, property_type, type_service):
        """Rangos de precio adaptados al tipo de propiedad y servicio"""
        is_rental = type_service in ['rent', 'vacation_rent']

        if is_rental:
            if property_type == 'apartment':
                return [
                    {'min': 0, 'max': 1000000, 'label': 'Hasta $1M'},
                    {'min': 1000000, 'max': 2000000, 'label': '$1M - $2M'},
                    {'min': 2000000, 'max': 3000000, 'label': '$2M - $3M'},
                    {'min': 3000000, 'max': 5000000, 'label': '$3M - $5M'},
                    {'min': 5000000, 'max': 0, 'label': 'Más de $5M'},
                ]
            elif property_type == 'house':
                return [
                    {'min': 0, 'max': 2000000, 'label': 'Hasta $2M'},
                    {'min': 2000000, 'max': 4000000, 'label': '$2M - $4M'},
                    {'min': 4000000, 'max': 6000000, 'label': '$4M - $6M'},
                    {'min': 6000000, 'max': 10000000, 'label': '$6M - $10M'},
                    {'min': 10000000, 'max': 0, 'label': 'Más de $10M'},
                ]
            else:
                return [
                    {'min': 0, 'max': 2000000, 'label': 'Hasta $2M'},
                    {'min': 2000000, 'max': 5000000, 'label': '$2M - $5M'},
                    {'min': 5000000, 'max': 0, 'label': 'Más de $5M'},
                ]
        else:
            if property_type == 'apartment':
                return [
                    {'min': 0, 'max': 100000000, 'label': 'Hasta $100M'},
                    {'min': 100000000, 'max': 200000000, 'label': '$100M - $200M'},
                    {'min': 200000000, 'max': 300000000, 'label': '$200M - $300M'},
                    {'min': 300000000, 'max': 500000000, 'label': '$300M - $500M'},
                    {'min': 500000000, 'max': 1000000000, 'label': '$500M - $1,000M'},
                    {'min': 1000000000, 'max': 0, 'label': 'Más de $1,000M'},
                ]
            elif property_type == 'house':
                return [
                    {'min': 0, 'max': 200000000, 'label': 'Hasta $200M'},
                    {'min': 200000000, 'max': 400000000, 'label': '$200M - $400M'},
                    {'min': 400000000, 'max': 600000000, 'label': '$400M - $600M'},
                    {'min': 600000000, 'max': 1000000000, 'label': '$600M - $1,000M'},
                    {'min': 1000000000, 'max': 2000000000, 'label': '$1,000M - $2,000M'},
                    {'min': 2000000000, 'max': 0, 'label': 'Más de $2,000M'},
                ]
            else:
                return [
                    {'min': 0, 'max': 100000000, 'label': 'Hasta $100M'},
                    {'min': 100000000, 'max': 300000000, 'label': '$100M - $300M'},
                    {'min': 300000000, 'max': 500000000, 'label': '$300M - $500M'},
                    {'min': 500000000, 'max': 1000000000, 'label': '$500M - $1,000M'},
                    {'min': 1000000000, 'max': 0, 'label': 'Más de $1,000M'},
                ]

    def _get_area_ranges(self):
        """Rangos de área"""
        return [
            {'min': 0, 'max': 50, 'label': 'Hasta 50 m²'},
            {'min': 50, 'max': 100, 'label': '50 - 100 m²'},
            {'min': 100, 'max': 150, 'label': '100 - 150 m²'},
            {'min': 150, 'max': 200, 'label': '150 - 200 m²'},
            {'min': 200, 'max': 300, 'label': '200 - 300 m²'},
            {'min': 300, 'max': 0, 'label': 'Más de 300 m²'},
        ]

    def _get_pager(self, total, page, ppg, url, params):
        """Paginación"""
        total_pages = (total + ppg - 1) // ppg

        return {
            'page': page,
            'total_pages': total_pages,
            'total': total,
            'ppg': ppg,
            'prev_url': f"{url}?page={page-1}" if page > 1 else None,
            'next_url': f"{url}?page={page+1}" if page < total_pages else None,
        }

    # =================== NEW HOMEPAGE API ===================

    @http.route(['/'], type='http', auth='public', website=True, sitemap=False)
    def index_redirect(self, **kwargs):
        """Redirige / a /home para evitar conflictos con otros módulos"""
        return request.redirect('/home')

    @http.route(['/home', '/homepage'], type='http', auth='public', website=True)
    def homepage_bohio(self, **kwargs):
        """Homepage BOHIO Real Estate con propiedades dinámicas"""
        _logger.info("[HOMEPAGE] Renderizando homepage_bohio")
        return request.render('theme_bohio_real_estate.bohio_homepage_new', {
            'page_name': 'homepage_bohio',
        })

    # =================== ENDPOINTS ESPECÍFICOS POR SECCIÓN ===================

    @http.route(['/api/properties/arriendo'], type='json', auth='public', website=True, csrf=False)
    def api_properties_arriendo(self, limit=4, **kwargs):
        """
        Endpoint específico para propiedades de arriendo en homepage
        OPTIMIZADO: Usa search_read para cargar todos los campos en 1 query SQL
        FILTRO: Solo propiedades con imagen
        """
        _logger.info(f"[HOMEPAGE] Cargando {limit} propiedades de arriendo con imagen")

        Property = request.env['product.template'].sudo()

        domain = [
            ('is_property', '=', True),
            ('active', '=', True),
            ('state', '=', 'free'),
            ('type_service', 'in', ['rent', 'sale_rent']),
            ('image_512', '!=', False)  # Solo propiedades con imagen
        ]

        # OPTIMIZACIÓN: search_count para total
        total = Property.search_count(domain)

        # OPTIMIZACIÓN: search_read carga todos los campos en 1 query
        properties_data = Property.search_read(
            domain,
            fields=[
                'id', 'name', 'default_code',
                'property_type', 'type_service',
                'net_rental_price', 'net_price', 'currency_id',
                'num_bedrooms', 'num_bathrooms', 'property_area',
                'city_id', 'city', 'state_id', 'neighborhood',
                'latitude', 'longitude',
                'project_worksite_id',
                'image_512',
                'state'
            ],
            limit=int(limit),
            order='write_date desc'
        )

        _logger.info(f"[HOMEPAGE] Encontradas {len(properties_data)} de {total} propiedades de arriendo")

        return {
            'success': True,
            'properties': self._serialize_properties_fast(properties_data, 'public'),
            'total': total
        }

    @http.route(['/api/properties/venta-usada'], type='json', auth='public', website=True, csrf=False)
    def api_properties_venta_usada(self, limit=4, **kwargs):
        """
        Endpoint específico para propiedades de venta usadas
        OPTIMIZADO: Usa search_read para cargar todos los campos en 1 query SQL
        MEJORA: Si propiedad no tiene imagen, usa imagen del proyecto (si tiene proyecto)
        """
        _logger.info(f"[HOMEPAGE] Cargando {limit} propiedades de venta usada")

        Property = request.env['product.template'].sudo()
        Project = request.env['project.project'].sudo()

        domain = [
            ('is_property', '=', True),
            ('active', '=', True),
            ('state', '=', 'free'),
            ('type_service', 'in', ['sale', 'sale_rent']),
            ('project_worksite_id', '=', False)  # Sin proyecto (usadas)
        ]

        # OPTIMIZACIÓN: search_count para total
        total = Property.search_count(domain)

        # OPTIMIZACIÓN: search_read carga todos los campos en 1 query
        properties_data = Property.search_read(
            domain,
            fields=[
                'id', 'name', 'default_code',
                'property_type', 'type_service',
                'net_rental_price', 'net_price', 'currency_id',
                'num_bedrooms', 'num_bathrooms', 'property_area',
                'city_id', 'city', 'state_id', 'neighborhood',
                'latitude', 'longitude',
                'project_worksite_id',
                'image_512',
                'state'
            ],
            limit=int(limit),
            order='write_date desc'
        )

        # Filtrar solo propiedades con imagen (las usadas normalmente no tienen proyecto)
        properties_data = [p for p in properties_data if p.get('image_512')]

        _logger.info(f"[HOMEPAGE] Encontradas {len(properties_data)} de {total} propiedades usadas con imagen")

        return {
            'success': True,
            'properties': self._serialize_properties_fast(properties_data, 'public'),
            'total': total
        }

    @http.route(['/api/properties/proyectos'], type='json', auth='public', website=True, csrf=False)
    def api_properties_proyectos(self, limit=4, **kwargs):
        """
        Endpoint específico para propiedades en proyectos
        OPTIMIZADO: Usa search_read para cargar todos los campos en 1 query SQL
        MEJORA: Si propiedad no tiene imagen, usa imagen del proyecto
        """
        _logger.info(f"[HOMEPAGE] Cargando {limit} propiedades en proyectos")

        Property = request.env['product.template'].sudo()
        Project = request.env['project.project'].sudo()

        domain = [
            ('is_property', '=', True),
            ('active', '=', True),
            ('state', '=', 'free'),
            ('type_service', 'in', ['sale', 'sale_rent']),
            ('project_worksite_id', '!=', False)
        ]

        # OPTIMIZACIÓN: search_count para total
        total = Property.search_count(domain)

        # OPTIMIZACIÓN: search_read carga todos los campos en 1 query
        properties_data = Property.search_read(
            domain,
            fields=[
                'id', 'name', 'default_code',
                'property_type', 'type_service',
                'net_rental_price', 'net_price', 'currency_id',
                'num_bedrooms', 'num_bathrooms', 'property_area',
                'city_id', 'city', 'state_id', 'neighborhood',
                'latitude', 'longitude',
                'project_worksite_id',
                'image_512',
                'state'
            ],
            limit=int(limit),
            order='write_date desc'
        )

        # MEJORA: Para propiedades sin imagen, cargar imagen del proyecto
        project_ids_to_fetch = []
        for prop in properties_data:
            if not prop.get('image_512'):
                project_id = prop.get('project_worksite_id')
                if project_id and isinstance(project_id, (list, tuple)):
                    project_ids_to_fetch.append(project_id[0])

        # Cargar imágenes de proyectos en 1 query batch
        project_images = {}
        if project_ids_to_fetch:
            projects_data = Project.search_read(
                [('id', 'in', project_ids_to_fetch)],
                fields=['id', 'image_1920']
            )
            project_images = {p['id']: p.get('image_1920') for p in projects_data}

        # Asignar imágenes de proyecto a propiedades sin imagen
        for prop in properties_data:
            if not prop.get('image_512'):
                project_id = prop.get('project_worksite_id')
                if project_id and isinstance(project_id, (list, tuple)):
                    proj_id = project_id[0]
                    if proj_id in project_images:
                        prop['image_512'] = project_images[proj_id]
                        prop['_using_project_image'] = True

        _logger.info(f"[HOMEPAGE] Encontradas {len(properties_data)} de {total} propiedades en proyectos")

        return {
            'success': True,
            'properties': self._serialize_properties_fast(properties_data, 'public'),
            'total': total
        }

    @http.route(['/bohio/api/properties/map'], type='json', auth='public', website=True)
    def api_get_properties_for_map(self, **params):
        """
        API para obtener propiedades solo con coordenadas GPS para el mapa
        Calcula distancia desde punto de referencia (oficina BOHIO)
        """
        # Coordenadas de la oficina BOHIO en Montería
        office_lat = params.get('ref_lat', 8.7479)
        office_lng = params.get('ref_lng', -75.8814)
        limit = params.get('limit', 30)  # Default 30 propiedades para mejor rendimiento

        # Extraer filtros
        type_service = params.get('type_service')
        property_type = params.get('property_type')
        bedrooms = params.get('bedrooms')
        bathrooms = params.get('bathrooms')
        min_price = params.get('min_price')
        max_price = params.get('max_price')

        # FILTROS DE UBICACIÓN (agregados para filtrado dinámico del mapa)
        city_id = params.get('city_id')
        region_id = params.get('region_id')
        project_id = params.get('project_id')

        _logger.info(f"API /bohio/api/properties/map - Filtros recibidos:")
        _logger.info(f"  type_service={type_service}, property_type={property_type}")
        _logger.info(f"  city_id={city_id}, region_id={region_id}, project_id={project_id}")
        _logger.info(f"  bedrooms={bedrooms}, bathrooms={bathrooms}")
        _logger.info(f"  min_price={min_price}, max_price={max_price}")

        domain = [
            ('is_property', '=', True),
            ('active', '=', True),
            ('state', '=', 'free'),
            ('latitude', '!=', False),
            ('longitude', '!=', False),
            ('latitude', '!=', 0),
            ('longitude', '!=', 0),
            # Excluir productos que no son propiedades reales
            ('name', 'not ilike', 'COMISION'),
            ('name', 'not ilike', 'PAGO'),
            ('name', 'not ilike', 'Pago'),
        ]

        # Aplicar filtros si existen
        if type_service:
            if type_service == 'sale_rent':
                domain.append(('type_service', 'in', ['sale', 'rent', 'sale_rent']))
            else:
                domain.append(('type_service', 'in', [type_service, 'sale_rent']))

        if property_type:
            domain.append(('property_type', '=', property_type))

        if bedrooms:
            try:
                domain.append(('num_bedrooms', '>=', int(bedrooms)))
            except ValueError:
                pass

        if bathrooms:
            try:
                domain.append(('num_bathrooms', '>=', int(bathrooms)))
            except ValueError:
                pass

        # Precio
        price_field = 'net_rental_price' if type_service in ['rent', 'vacation_rent'] else 'net_price'
        if min_price:
            try:
                domain.append((price_field, '>=', float(min_price)))
            except ValueError:
                pass
        if max_price:
            try:
                domain.append((price_field, '<=', float(max_price)))
            except ValueError:
                pass

        # FILTROS DE UBICACIÓN JERÁRQUICOS (mismo patrón que /bohio/api/properties)
        # Orden de prioridad: proyecto > barrio > ciudad
        if project_id:
            try:
                domain.append(('project_worksite_id', '=', int(project_id)))
                _logger.info(f"[MAPA] Filtro project_id aplicado: {project_id}")
            except (ValueError, TypeError):
                _logger.warning(f"[MAPA] project_id inválido: {project_id}")
        elif region_id:
            try:
                domain.append(('region_id', '=', int(region_id)))
                _logger.info(f"[MAPA] Filtro region_id aplicado: {region_id}")
            except (ValueError, TypeError):
                _logger.warning(f"[MAPA] region_id inválido: {region_id}")
        elif city_id:
            try:
                domain.append(('city_id', '=', int(city_id)))
                _logger.info(f"[MAPA] Filtro city_id aplicado: {city_id}")
            except (ValueError, TypeError):
                _logger.warning(f"[MAPA] city_id inválido: {city_id}")

        try:
            Property = request.env['product.template'].sudo()
            properties = Property.search(domain, limit=int(limit))

            _logger.info(f"Propiedades con coordenadas encontradas: {len(properties)}")

            properties_data = []
            for prop in properties:
                # Calcular distancia aproximada (en km)
                import math
                if prop.latitude and prop.longitude:
                    lat1, lon1 = math.radians(office_lat), math.radians(office_lng)
                    lat2, lon2 = math.radians(prop.latitude), math.radians(prop.longitude)

                    dlat = lat2 - lat1
                    dlon = lon2 - lon1

                    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                    c = 2 * math.asin(math.sqrt(a))
                    distance_km = 6371 * c  # Radio de la Tierra en km

                    # Determinar precio
                    price = 0
                    if prop.type_service == 'sale':
                        price = float(prop.net_price) if prop.net_price else float(prop.list_price)
                    elif prop.type_service == 'rent':
                        price = float(prop.net_rental_price) if prop.net_rental_price else float(prop.list_price)
                    else:
                        price = float(prop.list_price) if prop.list_price else 0

                    # Obtener imagen
                    website = request.website
                    image_url = website.image_url(prop, 'image_512') if prop.image_512 else None

                    properties_data.append({
                        'id': prop.id,
                        'name': prop.name or '',
                        'default_code': prop.default_code or '',
                        'list_price': price,
                        'property_type': prop.property_type or '',
                        'type_service': prop.type_service or '',
                        'bedrooms': int(prop.num_bedrooms) if prop.num_bedrooms else 0,
                        'bathrooms': int(prop.num_bathrooms) if prop.num_bathrooms else 0,
                        'area_constructed': float(prop.property_area) if prop.property_area else 0,
                        'total_area': float(prop.property_area) if prop.property_area else 0,
                        'built_area': float(prop.property_area) if prop.property_area else 0,
                        'city': prop.city_id.name if prop.city_id else prop.city or '',
                        'region': prop.neighborhood or '',
                        'neighborhood': prop.neighborhood or '',
                        'image_url': image_url,
                        'latitude': float(prop.latitude),
                        'longitude': float(prop.longitude),
                        'distance_km': round(distance_km, 2),
                    })

            # Ordenar por distancia (más cercanas primero)
            properties_data.sort(key=lambda x: x['distance_km'])

            return {
                'success': True,
                'properties': properties_data,
                'count': len(properties_data),
                'reference_point': {
                    'lat': office_lat,
                    'lng': office_lng,
                    'name': 'Oficina BOHIO'
                }
            }

        except Exception as e:
            _logger.error(f"Error en /bohio/api/properties/map: {str(e)}")
            return {
                'success': False,
                'properties': [],
                'error': str(e)
            }

    @http.route(['/bohio/api/properties'], type='json', auth='public', website=True)
    def api_get_properties(self, **params):
        """API para obtener propiedades con paginación (40 por página) - compatible con homepage y shop"""
        # Extraer parámetros del JSON body
        type_service = params.get('type_service')
        state = params.get('state')
        is_project = params.get('is_project', False)
        limit = params.get('limit', 40)
        offset = params.get('offset', 0)
        property_type = params.get('property_type')
        bedrooms = params.get('bedrooms')
        bathrooms = params.get('bathrooms')
        min_price = params.get('min_price')
        max_price = params.get('max_price')
        garage = params.get('garage')
        pool = params.get('pool')
        garden = params.get('garden')
        elevator = params.get('elevator')
        order = params.get('order')
        context = params.get('context', 'public')

        # FILTROS DE UBICACIÓN (agregados para property_shop)
        city_id = params.get('city_id')
        region_id = params.get('region_id')
        project_id = params.get('project_id')

        _logger.info(f"API /bohio/api/properties LLAMADO - Parámetros recibidos:")
        _logger.info(f"  type_service={type_service}, property_type={property_type}")
        _logger.info(f"  bedrooms={bedrooms}, bathrooms={bathrooms}")
        _logger.info(f"  min_price={min_price}, max_price={max_price}")
        _logger.info(f"  garage={garage}, pool={pool}, garden={garden}, elevator={elevator}")
        _logger.info(f"  city_id={city_id}, region_id={region_id}, project_id={project_id}")
        _logger.info(f"  order={order}, limit={limit}, offset={offset}")

        domain = [
            ('is_property', '=', True),
            ('active', '=', True),
        ]

        # Filtrar por estado de propiedad (solo disponibles si no se especifica)
        if context == 'public' or not state:
            domain.append(('state', '=', 'free'))

        # Tipo de servicio
        if type_service:
            _logger.info(f"Filtro type_service recibido: {type_service}")
            if type_service == 'sale_rent':
                filter_clause = ('type_service', 'in', ['sale', 'rent', 'sale_rent'])
                domain.append(filter_clause)
                _logger.info(f"Filtro aplicado (sale_rent): {filter_clause}")
            else:
                filter_clause = ('type_service', 'in', [type_service, 'sale_rent'])
                domain.append(filter_clause)
                _logger.info(f"Filtro aplicado ({type_service}): {filter_clause}")

        # Estado del producto (nuevo/usado)
        if state:
            if state == 'used':
                domain.append(('product_state', '=', 'used'))
            elif state == 'new':
                domain.append(('product_state', '=', 'new'))

        # Proyectos
        if is_project:
            domain.append(('project_worksite_id', '!=', False))

        # NUEVOS FILTROS PARA PROPERTY SHOP

        # Tipo de propiedad
        if property_type:
            domain.append(('property_type', '=', property_type))

        # Habitaciones
        if bedrooms:
            try:
                domain.append(('num_bedrooms', '>=', int(bedrooms)))
            except ValueError:
                pass

        # Baños
        if bathrooms:
            try:
                domain.append(('num_bathrooms', '>=', int(bathrooms)))
            except ValueError:
                pass

        # Precio
        price_field = 'net_rental_price' if type_service in ['rent', 'vacation_rent'] else 'net_price'
        if min_price:
            try:
                domain.append((price_field, '>=', float(min_price)))
            except ValueError:
                pass
        if max_price:
            try:
                domain.append((price_field, '<=', float(max_price)))
            except ValueError:
                pass

        # Características booleanas
        if garage:
            domain.append(('garage', '=', True))
        if pool:
            domain.append(('pools', '=', True))
        if garden:
            domain.append(('garden', '=', True))
        if elevator:
            domain.append(('elevator', '=', True))

        # FILTROS DE UBICACIÓN JERÁRQUICOS
        # Orden de prioridad: proyecto > barrio > ciudad
        if project_id:
            try:
                domain.append(('project_worksite_id', '=', int(project_id)))
                _logger.info(f"Filtro project_id aplicado: {project_id}")
            except (ValueError, TypeError):
                _logger.warning(f"project_id inválido: {project_id}")
        elif region_id:
            try:
                domain.append(('region_id', '=', int(region_id)))
                _logger.info(f"Filtro region_id aplicado: {region_id}")
            except (ValueError, TypeError):
                _logger.warning(f"region_id inválido: {region_id}")
        elif city_id:
            try:
                domain.append(('city_id', '=', int(city_id)))
                _logger.info(f"Filtro city_id aplicado: {city_id}")
            except (ValueError, TypeError):
                _logger.warning(f"city_id inválido: {city_id}")

        try:
            Property = request.env['product.template'].sudo()

            # Log del domain completo antes de la búsqueda
            _logger.info(f"Domain final para búsqueda: {domain}")

            # Obtener total count para paginación
            total_count = Property.search_count(domain)

            # Limitar búsqueda para evitar timeouts
            search_limit = min(int(limit), 100)  # Máximo 100 propiedades por página
            search_offset = int(offset)

            properties = Property.search(
                domain,
                limit=search_limit,
                offset=search_offset,
                order='sequence ASC, create_date DESC'
            )

            _logger.info(f"API properties: Total={total_count}, Devolviendo={len(properties)}, Offset={search_offset}, Limit={search_limit}")

        except Exception as e:
            _logger.error(f"Error en búsqueda de propiedades: {str(e)}")
            return {
                'items': [],
                'properties': [],
                'count': 0,
                'total': 0,
                'error': str(e)
            }

        # Preparar datos para JSON - Optimizado
        properties_data = []
        thirty_days_ago = datetime.now() - timedelta(days=30)

        try:
            for prop in properties:
                try:
                    # Determinar precio correcto según tipo de servicio
                    price = 0
                    if prop.type_service == 'sale':
                        price = float(prop.net_price) if prop.net_price else float(prop.list_price)
                    elif prop.type_service == 'rent':
                        price = float(prop.net_rental_price) if prop.net_rental_price else float(prop.list_price)
                    else:
                        price = float(prop.list_price) if prop.list_price else 0

                    # Obtener URL de imagen optimizada usando website.image_url (mismo patrón que website_sale)
                    website = request.website
                    image_url = website.image_url(prop, 'image_512') if prop.image_512 else None

                    # Obtener solo los campos necesarios de forma eficiente
                    properties_data.append({
                        'id': prop.id,
                        'name': prop.name or '',
                        'default_code': prop.default_code or '',
                        'list_price': price,
                        'net_price': float(prop.net_price) if prop.net_price else 0,
                        'net_rental_price': float(prop.net_rental_price) if prop.net_rental_price else 0,
                        'property_type': prop.property_type or '',
                        'property_type_name': prop.property_type_id.name if prop.property_type_id else '',
                        'type_service': prop.type_service or '',
                        'bedrooms': int(prop.num_bedrooms) if prop.num_bedrooms else 0,
                        'bathrooms': int(prop.num_bathrooms) if prop.num_bathrooms else 0,
                        'area_constructed': float(prop.property_area) if prop.property_area else 0,
                        'area_total': float(prop.property_area) if prop.property_area else 0,
                        'city': prop.city_id.name if prop.city_id else prop.city or '',
                        'state': prop.state_id.name if prop.state_id else '',
                        'region': prop.neighborhood or '',
                        'address': prop.address or '',
                        'description': prop.description or '',
                        'image_url': image_url,
                        'create_date': prop.create_date.isoformat() if prop.create_date else None,
                        'is_new': bool(prop.create_date and prop.create_date >= thirty_days_ago),
                        'latitude': float(prop.latitude) if prop.latitude else None,
                        'longitude': float(prop.longitude) if prop.longitude else None,
                        # Características básicas
                        'garage': bool(prop.garage),
                        'elevator': bool(prop.elevator),
                        'pools': bool(prop.pools),
                        'stratum': self._safe_stratum_to_int(prop.stratum),
                        'parking': (prop.covered_parking or 0) + (prop.uncovered_parking or 0),
                        'covered_parking': int(prop.covered_parking) if prop.covered_parking else 0,
                        'uncovered_parking': int(prop.uncovered_parking) if prop.uncovered_parking else 0,
                        # Características adicionales agrupadas
                        'furnished': bool(prop.furnished),
                        'balcony': bool(prop.balcony),
                        'terrace': bool(prop.terrace),
                        'patio': bool(prop.patio),
                        'garden': bool(prop.garden),
                        'gym': bool(prop.gym),
                        'social_room': bool(prop.social_room),
                        'green_areas': bool(prop.green_areas),
                        'has_playground': bool(prop.has_playground),
                        'sports_area': bool(prop.sports_area),
                        'air_conditioning': bool(prop.air_conditioning),
                        'hot_water': bool(prop.hot_water),
                        'has_security': bool(prop.has_security),
                        'security_cameras': bool(prop.security_cameras),
                        'alarm': bool(prop.alarm),
                        'intercom': bool(prop.intercom),
                        'doorman': prop.doorman or False,
                        'laundry_area': bool(prop.laundry_area),
                        'warehouse': bool(prop.warehouse),
                        'fireplace': bool(prop.fireplace),
                        'mezzanine': bool(prop.mezzanine),
                        'apartment_type': prop.apartment_type or False,
                    })
                except Exception as e:
                    _logger.warning(f"Error procesando propiedad {prop.id}: {str(e)}")
                    continue

        except Exception as e:
            _logger.error(f"Error preparando datos de propiedades: {str(e)}")

        result = {
            'items': properties_data,
            'properties': properties_data,  # Mantener compatibilidad
            'count': len(properties_data),
            'total': total_count,
            'offset': search_offset,
            'limit': search_limit
        }

        _logger.info(f"API properties: Devolviendo {len(properties_data)} de {total_count} propiedades totales")

        return result

    @http.route(['/bohio/api/cities/autocomplete'], type='json', auth='public', website=True)
    def api_cities_autocomplete(self, query='', limit=10, **kwargs):
        """API para autocompletar ciudades"""
        if not query or len(query) < 2:
            return {'cities': []}

        City = request.env['res.city'].sudo()
        cities = City.search([
            ('name', 'ilike', query),
        ], limit=limit, order='name ASC')

        cities_data = []
        for city in cities:
            # Contar propiedades disponibles
            property_count = request.env['product.template'].sudo().search_count([
                ('is_property', '=', True),
                ('city_id', '=', city.id),
                ('state', '=', 'free'),
            ])

            if property_count > 0:
                cities_data.append({
                    'id': city.id,
                    'name': city.name,
                    'region': city.state_id.name if city.state_id else '',
                    'property_count': property_count,
                })

        return {'cities': cities_data}

    @http.route(['/contacto'], type='http', auth='public', website=True)
    def contacto(self, **kwargs):
        """Página de Contacto BOHIO"""
        return request.render('theme_bohio_real_estate.bohio_contacto_page', {})

    @http.route(['/contacto/submit'], type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def contacto_submit(self, **post):
        """Procesar formulario de contacto"""
        # Crear lead en CRM
        Lead = request.env['crm.lead'].sudo()

        # Obtener source_id buscando por nombre 'Website'
        UtmSource = request.env['utm.source'].sudo()
        website_source = UtmSource.search([('name', '=', 'Website')], limit=1)
        source_id = website_source.id if website_source else False

        lead_vals = {
            'name': post.get('asunto', 'Contacto desde Web'),
            'contact_name': post.get('nombre', ''),
            'email_from': post.get('email', ''),
            'phone': post.get('telefono', ''),
            'description': post.get('mensaje', ''),
            'type': 'opportunity',
            'source_id': source_id,
        }

        try:
            lead = Lead.create(lead_vals)
            return request.render('theme_bohio_real_estate.contacto_gracias', {})
        except Exception as e:
            _logger.error(f"Error creating lead from contact form: {e}")
            return request.render('theme_bohio_real_estate.contacto_error', {})

    @http.route(['/proyectos'], type='http', auth='public', website=True)
    def proyectos(self, **kwargs):
        """Página de Proyectos BOHIO"""
        return request.render('theme_bohio_real_estate.bohio_proyectos_page', {})

    @http.route(['/bohio/api/proyectos'], type='json', auth='public', website=True)
    def api_get_proyectos(self, **kwargs):
        """API para obtener proyectos"""
        Project = request.env['project.worksite'].sudo()

        domain = [('is_enabled', '=', True)]

        proyectos = Project.search(domain, order='name ASC')

        proyectos_data = []
        for proyecto in proyectos:
            # Contar unidades disponibles
            unidades_totales = request.env['product.template'].sudo().search_count([
                ('project_worksite_id', '=', proyecto.id),
                ('is_property', '=', True),
            ])

            unidades_disponibles = request.env['product.template'].sudo().search_count([
                ('project_worksite_id', '=', proyecto.id),
                ('is_property', '=', True),
                ('state', '=', 'free'),
            ])

            # Ubicación completa
            ubicacion_parts = []
            if proyecto.region_id:
                ubicacion_parts.append(proyecto.region_id.name)
            if proyecto.region_id and proyecto.region_id.city_id:
                ubicacion_parts.append(proyecto.region_id.city_id.name)
            if proyecto.region_id and proyecto.region_id.state_id:
                ubicacion_parts.append(proyecto.region_id.state_id.name)

            ubicacion = ', '.join(ubicacion_parts) if ubicacion_parts else 'Sin ubicación'

            # Imagen del proyecto
            image_url = None
            if proyecto.image_1920:
                image_url = f'/web/image/project.worksite/{proyecto.id}/image_1920'

            proyectos_data.append({
                'id': proyecto.id,
                'name': proyecto.name,
                'descripcion': proyecto.description or '',
                'ubicacion': ubicacion,
                'estado': 'construccion',  # Por defecto
                'unidades': unidades_totales,
                'disponibles': unidades_disponibles,
                'image_url': image_url,
            })

        return {'proyectos': proyectos_data}

    @http.route(['/bohio/crm/create_lead_whatsapp'], type='json', auth='public', website=True, csrf=False)
    def create_lead_whatsapp(self, **post):
        """Crear oportunidad desde formulario de WhatsApp"""
        try:
            # Extraer datos del formulario
            property_id = post.get('property_id')
            property_name = post.get('property_name', '')
            property_code = post.get('property_code', '')
            property_url = post.get('property_url', '')
            customer_name = post.get('customer_name', '')
            customer_phone = post.get('customer_phone', '')
            customer_email = post.get('customer_email', '')
            customer_message = post.get('customer_message', '')

            # Obtener propiedad
            property_obj = request.env['product.template'].sudo().browse(int(property_id))

            # Buscar o crear partner
            Partner = request.env['res.partner'].sudo()
            partner_domain = []

            if customer_email:
                partner_domain.append(('email', '=', customer_email))
            elif customer_phone:
                partner_domain.append(('phone', '=', customer_phone))

            partner = Partner.search(partner_domain, limit=1) if partner_domain else False

            if not partner:
                # Crear nuevo partner
                partner_vals = {
                    'name': customer_name,
                    'phone': customer_phone,
                    'email': customer_email or False,
                    'customer_rank': 1,
                }
                partner = Partner.create(partner_vals)

            # Crear oportunidad en CRM
            Lead = request.env['crm.lead'].sudo()

            # Preparar descripción con toda la información
            description = f"""
**Consulta desde WhatsApp - Detalle de Propiedad**

**Propiedad:**
- Nombre: {property_name}
- Código: {property_code}
- URL: {property_url}

**Cliente:**
- Nombre: {customer_name}
- Teléfono: {customer_phone}
- Email: {customer_email or 'No proporcionado'}

**Mensaje del Cliente:**
{customer_message or 'Sin mensaje adicional'}

**Origen:** Botón WhatsApp desde página de detalle
**Fecha:** {fields.Datetime.now()}
            """

            lead_vals = {
                'name': f'WhatsApp - {property_code} - {customer_name}',
                'partner_id': partner.id,
                'contact_name': customer_name,
                'phone': customer_phone,
                'email_from': customer_email or False,
                'description': description.strip(),
                'type': 'opportunity',
                'user_id': False,  # Sin asignar, para que el equipo lo asigne
                'team_id': request.env['crm.team'].sudo().search([], limit=1).id if request.env['crm.team'].sudo().search([], limit=1) else False,
                'source_id': request.env.ref('utm.utm_source_website').id if request.env.ref('utm.utm_source_website', False) else False,
                'medium_id': request.env.ref('utm.utm_medium_website').id if request.env.ref('utm.utm_medium_website', False) else False,
                'tag_ids': [(6, 0, [])],
            }

            # Vincular propiedad si existe el campo
            if hasattr(Lead, 'property_id'):
                lead_vals['property_id'] = property_id

            lead = Lead.create(lead_vals)

            # Obtener número de WhatsApp de la compañía
            company = request.env.company
            whatsapp_number = company.phone or '573001234567'  # Número por defecto

            # Limpiar número (quitar espacios, guiones, paréntesis)
            whatsapp_number = ''.join(filter(str.isdigit, whatsapp_number))

            _logger.info(f"Oportunidad creada desde WhatsApp: Lead ID {lead.id}, Cliente: {customer_name}, Propiedad: {property_code}")

            return {
                'success': True,
                'lead_id': lead.id,
                'partner_id': partner.id,
                'whatsapp_number': whatsapp_number,
                'message': 'Oportunidad creada exitosamente'
            }

        except Exception as e:
            _logger.error(f"Error creando oportunidad desde WhatsApp: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @http.route(['/bohio/api/crm/add_property'], type='json', auth='public', website=True, csrf=False)
    def add_property_to_crm(self, **post):
        """Agregar propiedad al CRM como oportunidad"""
        try:
            property_id = post.get('property_id')
            property_name = post.get('property_name', '')

            if not property_id:
                return {
                    'success': False,
                    'message': 'ID de propiedad requerido'
                }

            # Obtener propiedad
            property_obj = request.env['product.template'].sudo().browse(int(property_id))

            if not property_obj.exists():
                return {
                    'success': False,
                    'message': 'Propiedad no encontrada'
                }

            # Obtener usuario actual o crear partner genérico
            Partner = request.env['res.partner'].sudo()

            if request.env.user._is_public():
                # Usuario público - crear partner genérico o usar uno existente
                partner = Partner.search([('name', '=', 'Cliente Web Interesado')], limit=1)
                if not partner:
                    partner = Partner.create({
                        'name': 'Cliente Web Interesado',
                        'customer_rank': 1,
                    })
            else:
                # Usuario logueado
                partner = request.env.user.partner_id

            # Crear oportunidad en CRM
            Lead = request.env['crm.lead'].sudo()

            # Preparar descripción
            property_code = property_obj.default_code or property_obj.name
            property_url = f"{request.httprequest.host_url}property/{property_id}"

            description = f"""
**Propiedad de Interés desde la Web**

**Propiedad:**
- Nombre: {property_name}
- Código: {property_code}
- Tipo: {property_obj.property_type_id.name if property_obj.property_type_id else 'N/A'}
- URL: {property_url}

**Origen:** Botón "Agregar al CRM" desde tienda de propiedades
**Fecha:** {fields.Datetime.now()}
            """

            lead_vals = {
                'name': f'Interés Web - {property_code}',
                'partner_id': partner.id,
                'description': description.strip(),
                'type': 'opportunity',
                'user_id': False,  # Sin asignar
                'team_id': request.env['crm.team'].sudo().search([], limit=1).id if request.env['crm.team'].sudo().search([], limit=1) else False,
                'source_id': request.env.ref('utm.utm_source_website').id if request.env.ref('utm.utm_source_website', False) else False,
                'medium_id': request.env.ref('utm.utm_medium_website').id if request.env.ref('utm.utm_medium_website', False) else False,
            }

            # Vincular propiedad si existe el campo
            if hasattr(Lead, 'property_id'):
                lead_vals['property_id'] = property_id

            lead = Lead.create(lead_vals)

            _logger.info(f"Propiedad agregada al CRM: Lead ID {lead.id}, Propiedad: {property_code}")

            return {
                'success': True,
                'lead_id': lead.id,
                'message': 'Propiedad agregada al CRM exitosamente'
            }

        except Exception as e:
            _logger.error(f"Error agregando propiedad al CRM: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Error: {str(e)}'
            }

    @http.route(['/property/comparison/get'], type='json', auth='public', website=True, csrf=False)
    def get_property_comparison(self, **post):
        """Obtener propiedades para comparación"""
        try:
            _logger.info(f"Comparación de propiedades - POST recibido: {post}")
            property_ids = post.get('property_ids', [])
            _logger.info(f"Property IDs extraídos: {property_ids}")

            if not property_ids or not isinstance(property_ids, list):
                _logger.warning(f"Property IDs inválidos o vacíos: {property_ids}")
                return {
                    'success': False,
                    'properties': []
                }

            # Buscar propiedades
            Product = request.env['product.template'].sudo()
            properties = Product.browse([int(pid) for pid in property_ids if pid])

            properties_data = []
            for prop in properties:
                if not prop.exists():
                    continue

                # Determinar precio correcto
                price = 0
                if prop.type_service == 'sale':
                    price = float(prop.net_price) if prop.net_price else float(prop.list_price)
                elif prop.type_service == 'rent':
                    price = float(prop.net_rental_price) if prop.net_rental_price else float(prop.list_price)
                else:
                    price = float(prop.list_price) if prop.list_price else 0

                # Obtener URL de imagen optimizada (mismo patrón que website_sale)
                website = request.website
                image_url = website.image_url(prop, 'image_512') if prop.image_512 else None

                properties_data.append({
                    'id': prop.id,
                    'name': prop.name or '',
                    'default_code': prop.default_code or '',
                    'list_price': price,
                    'property_type': prop.property_type or '',
                    'property_type_name': prop.property_type_id.name if prop.property_type_id else '',
                    'type_service': prop.type_service or '',
                    'bedrooms': int(prop.num_bedrooms) if prop.num_bedrooms else 0,
                    'bathrooms': int(prop.num_bathrooms) if prop.num_bathrooms else 0,
                    'area_constructed': float(prop.property_area) if prop.property_area else 0,
                    'city': prop.city_id.name if prop.city_id else prop.city or '',
                    'state': prop.state_id.name if prop.state_id else '',
                    'region': prop.neighborhood or '',
                    'stratum': self._safe_stratum_to_int(prop.stratum),
                    'image_url': image_url,
                    'garage': bool(prop.garage),
                    'elevator': bool(prop.elevator),
                    'pools': bool(prop.pools),
                    'furnished': bool(prop.furnished),
                })

            _logger.info(f"Comparación exitosa - Devolviendo {len(properties_data)} propiedades")
            return {
                'success': True,
                'properties': properties_data
            }

        except Exception as e:
            _logger.error(f"Error en comparación de propiedades: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'properties': []
            }

    @http.route(['/property/<int:property_id>/similar'], type='json', auth='public', website=True, csrf=False)
    def get_similar_properties(self, property_id):
        """Buscar propiedades similares basadas en ubicación y características"""
        try:
            Product = request.env['product.template'].sudo()

            # Obtener propiedad actual
            current_property = Product.browse(property_id)
            if not current_property.exists():
                _logger.warning(f"Propiedad {property_id} no existe")
                return {'success': False, 'properties': []}

            _logger.info(f"Buscando propiedades similares a: {current_property.name} (ID: {property_id})")
            _logger.info(f"Tipo servicio: {current_property.type_service}, Ciudad: {current_property.city}, Precio: {current_property.list_price}")

            # BÚSQUEDA NIVEL 1: Mismo tipo y ciudad (MUY FLEXIBLE)
            domain = [
                ('id', '!=', property_id),
                ('active', '=', True),
            ]

            # Mismo tipo de servicio (solo si existe)
            if current_property.type_service:
                domain.append(('type_service', '=', current_property.type_service))

            # Misma ciudad (intentar ambos campos)
            if current_property.city_id:
                domain.append(('city_id', '=', current_property.city_id.id))
            elif current_property.city:
                domain.append(('city', '=', current_property.city))

            _logger.info(f"Dominio búsqueda nivel 1 (flexible): {domain}")
            similar_properties = Product.search(domain, limit=6, order='create_date DESC')
            _logger.info(f"Nivel 1: Encontradas {len(similar_properties)} propiedades")

            # BÚSQUEDA NIVEL 2: Solo mismo tipo de servicio (MUY AMPLIO)
            if len(similar_properties) < 3:
                _logger.info("Relajando criterios a nivel 2 (solo tipo servicio)...")
                domain = [
                    ('id', '!=', property_id),
                    ('active', '=', True),
                ]

                if current_property.type_service:
                    domain.append(('type_service', '=', current_property.type_service))

                _logger.info(f"Dominio búsqueda nivel 2: {domain}")
                similar_properties = Product.search(domain, limit=6, order='create_date DESC')
                _logger.info(f"Nivel 2: Encontradas {len(similar_properties)} propiedades")

            # BÚSQUEDA NIVEL 3: Cualquier propiedad activa (ULTRA AMPLIO)
            if len(similar_properties) < 2:
                _logger.info("Relajando criterios a nivel 3 (cualquier activa)...")
                domain = [
                    ('id', '!=', property_id),
                    ('active', '=', True),
                ]

                _logger.info(f"Dominio búsqueda nivel 3: {domain}")
                similar_properties = Product.search(domain, limit=6, order='create_date DESC')
                _logger.info(f"Nivel 3: Encontradas {len(similar_properties)} propiedades")

            # Formatear datos
            properties_data = []
            for prop in similar_properties:
                # Determinar precio correcto
                price = 0
                if prop.type_service == 'sale':
                    price = float(prop.net_price) if prop.net_price else float(prop.list_price)
                elif prop.type_service == 'rent':
                    price = float(prop.net_rental_price) if prop.net_rental_price else float(prop.list_price)
                else:
                    price = float(prop.list_price) if prop.list_price else 0

                properties_data.append({
                    'id': prop.id,
                    'name': prop.name or '',
                    'default_code': prop.default_code or '',
                    'list_price': price,
                    'type_service': prop.type_service or '',
                    'bedrooms': int(prop.num_bedrooms) if prop.num_bedrooms else 0,
                    'bathrooms': int(prop.num_bathrooms) if prop.num_bathrooms else 0,
                    'area_constructed': float(prop.property_area) if prop.property_area else 0,
                    'city': prop.city_id.name if prop.city_id else prop.city or '',
                    'region': prop.neighborhood or '',
                    'image_url': f'/web/image/product.template/{prop.id}/image_512' if prop.image_512 else None,
                })

            return {
                'success': True,
                'properties': properties_data
            }

        except Exception as e:
            _logger.error(f"Error buscando propiedades similares: {str(e)}")
            return {
                'success': False,
                'properties': []
            }

    @http.route('/properties/api/list', type='json', auth='public', website=True, csrf=False)
    def properties_api_list(self, type_service=None, is_project=None, limit=4):
        """
        API REST para listar propiedades (para homepage)
        """
        try:
            domain = [
                ('is_property', '=', True),  # Es una propiedad
                ('active', '=', True),  # Está activa
                ('state', '=', 'free'),  # Solo propiedades disponibles
                ('latitude', '!=', False),  # Debe tener latitud
                ('longitude', '!=', False),  # Debe tener longitud
            ]

            # Filtro por tipo de servicio
            if type_service:
                domain.append(('type_service', '=', type_service))

            # Filtro por proyectos (usar project_worksite_id en lugar de is_project)
            if is_project is not None:
                is_proj_bool = str(is_project).lower() in ('true', '1', 'yes')
                if is_proj_bool:
                    # Tiene proyecto
                    domain.append(('project_worksite_id', '!=', False))
                else:
                    # NO tiene proyecto (propiedades usadas)
                    domain.append(('project_worksite_id', '=', False))

            # Buscar propiedades
            properties = request.env['product.template'].sudo().search(
                domain,
                limit=int(limit),
                order='create_date desc'
            )

            # Construir respuesta
            properties_data = []
            for prop in properties:
      

                # Determinar tipo de servicio
                type_service = prop.type_service or 'sale'

                # Precio según tipo de servicio
                if type_service in ('rent', 'vacation_rent'):
                    # Para arriendo, usar net_rental_price
                    price = float(prop.net_rental_price) if prop.net_rental_price else 0
                elif type_service == 'sale_rent':
                    # Si tiene ambos servicios, priorizar venta
                    price = float(prop.net_price) if prop.net_price else 0
                else:
                    # Para venta, usar net_price (Precio Final de Venta)
                    price = float(prop.net_price) if prop.net_price else 0

                properties_data.append({
                    'id': prop.id,
                    'name': prop.name,
                    'description': prop.description or prop.note or '',
                    'price': price,
                    'type_service': type_service,
                    'bedrooms': int(prop.num_bedrooms) if prop.num_bedrooms else 0,
                    'bathrooms': int(prop.num_bathrooms) if prop.num_bathrooms else 0,
                    'area': float(prop.property_area) if prop.property_area else 0,
                    'city': prop.city_id.name if prop.city_id else prop.city or '',
                    'state': prop.state_id.name if prop.state_id else '',
                    'neighborhood': prop.neighborhood or '',
                    'default_code': prop.default_code or '',
                    'latitude': float(prop.latitude) if prop.latitude else None,
                    'longitude': float(prop.longitude) if prop.longitude else None,
                    'image_url': request.env['website'].image_url(prop, 'image_512') if prop.image_512 else None,
                })

            return {
                'success': True,
                'properties': properties_data
            }

        except Exception as e:
            _logger.error(f"Error en API /properties/api/list: {str(e)}")
            return {
                'success': False,
                'properties': [],
                'error': str(e)
            }

    @http.route(['/proyecto/<int:project_id>', '/proyecto/<string:project_slug>'], type='http', auth='public', website=True, sitemap=True)
    def proyecto_detalle(self, project_id=None, project_slug=None, **kwargs):
        """Pagina generica de detalle de proyecto"""
        # Buscar proyecto por ID o por slug/default_code
        if project_id:
            project = request.env['project.worksite'].sudo().browse(project_id)
        elif project_slug:
            # Buscar por default_code o slug
            project = request.env['project.worksite'].sudo().search([
                '|',
                ('default_code', '=ilike', project_slug),
                ('name', '=ilike', project_slug.replace('-', ' '))
            ], limit=1)
        else:
            return request.render('website.404')

        if not project or not project.exists():
            return request.render('website.404')

        # Obtener todas las propiedades del proyecto
        properties = request.env['product.template'].sudo().search([
            ('project_worksite_id', '=', project.id),
            ('is_property', '=', True),
            ('active', '=', True)
        ], order='floor_number ASC, name ASC')

        # Agrupar apartamentos por tipo
        apartments_by_type = {}
        for prop in properties:
            # Extraer tipo del nombre (ej: "Torre Rialto - Apartamento Tipo A Piso 3" -> "A")
            if 'Tipo' in prop.name:
                tipo = prop.name.split('Tipo')[1].strip().split()[0]
                if tipo not in apartments_by_type:
                    apartments_by_type[tipo] = []
                apartments_by_type[tipo].append(prop)

        # Si no hay agrupacion por tipo, agrupar todas
        if not apartments_by_type and properties:
            apartments_by_type = {'General': list(properties)}

        # Obtener imagen del proyecto (si existe)
        project_image = request.env['website'].image_url(project, 'image_1920') if project.image_1920 else '/theme_bohio_real_estate/static/src/img/banner1.jpg'

        # Obtener coordenadas para el mapa
        # 1. Primero intentar desde el proyecto mismo (si tiene campos de ubicacion)
        map_lat = None
        map_lng = None
        map_address = project.address or project.name

        # 2. Si el proyecto no tiene coordenadas, buscar en las propiedades
        if properties:
            for prop in properties:
                if prop.latitude and prop.longitude:
                    map_lat = float(prop.latitude)
                    map_lng = float(prop.longitude)
                    if not project.address and prop.city_id:
                        map_address = f"{prop.city_id.name}, {prop.state_id.name if prop.state_id else ''}"
                    break

        return request.render('theme_bohio_real_estate.proyecto_detalle_page', {
            'project': project,
            'properties': properties,
            'apartments_by_type': apartments_by_type,
            'property_count': len(properties),
            'project_image': project_image,
            'map_lat': map_lat,
            'map_lng': map_lng,
            'map_address': map_address
        })

    # Mantener ruta antigua para compatibilidad
    @http.route('/proyecto/torre-rialto', type='http', auth='public', website=True)
    def proyecto_torre_rialto_legacy(self, **kwargs):
        """Redireccion para compatibilidad"""
        return request.redirect('/proyecto/torre-rialto')

    # =================== CARRUSELES DINÁMICOS ===================

    @http.route(['/carousel/properties'], type='json', auth='public', website=True, csrf=False)
    def carousel_properties(self, carousel_type='sale', limit=12, **kwargs):
        """
        Endpoint para cargar propiedades dinámicamente en carruseles

        Args:
            carousel_type (str): 'sale', 'rent', 'projects'
            limit (int): Número máximo de propiedades a retornar

        Returns:
            dict: Lista de propiedades serializadas para el carrusel
        """
        try:
            Property = request.env['product.template'].sudo()

            # Dominio base
            domain = [
                ('is_property', '=', True),
                ('active', '=', True),
                ('state', '=', 'free'),
                ('latitude', '!=', False),
                ('longitude', '!=', False)
            ]

            # Filtrar según tipo de carrusel
            if carousel_type == 'rent':
                # Propiedades en arriendo
                domain.append(('type_service', 'in', ['rent', 'sale_rent']))
            elif carousel_type == 'sale':
                # Propiedades usadas en venta (sin proyecto)
                domain.append(('type_service', 'in', ['sale', 'sale_rent']))
                domain.append(('project_worksite_id', '=', False))
            elif carousel_type == 'projects':
                # Propiedades nuevas/proyectos (con proyecto)
                domain.append(('type_service', 'in', ['sale', 'sale_rent']))
                domain.append(('project_worksite_id', '!=', False))

            # Buscar propiedades más recientes
            properties = Property.search(domain, limit=limit, order='create_date DESC')

            # Obtener website una sola vez fuera del loop (optimización)
            website = request.env['website'].get_current_website()

            # Serializar datos
            properties_data = []
            for prop in properties:
                # Determinar precio
                if prop.type_service in ('rent', 'vacation_rent'):
                    price = prop.net_rental_price or 0
                    price_label = 'Arriendo/mes'
                else:
                    price = prop.net_price or 0
                    price_label = 'Venta'

                # Formatear precio
                price_formatted = f"${price:,.0f}" if price > 0 else "Consultar"

                # Información del proyecto
                project_name = prop.project_worksite_id.name if prop.project_worksite_id else None
                project_id = prop.project_worksite_id.id if prop.project_worksite_id else None

                # Obtener URL de imagen optimizada usando website.image_url
                image_url = website.image_url(prop, 'image_512') if prop.image_512 else '/theme_bohio_real_estate/static/src/img/placeholder.jpg'

                properties_data.append({
                    'id': prop.id,
                    'name': prop.name,
                    'code': prop.default_code or '',
                    'price': price,
                    'price_formatted': price_formatted,
                    'price_label': price_label,
                    'bedrooms': int(prop.num_bedrooms) if prop.num_bedrooms else 0,
                    'bathrooms': int(prop.num_bathrooms) if prop.num_bathrooms else 0,
                    'area': float(prop.property_area) if prop.property_area else 0,
                    'city': prop.city_id.name if prop.city_id else prop.city or '',
                    'state': prop.state_id.name if prop.state_id else '',
                    'neighborhood': prop.neighborhood or '',
                    'property_type': dict(prop._fields['property_type'].selection).get(prop.property_type, ''),
                    'image_url': image_url,
                    'url': f'/property/{prop.id}',
                    'project_id': project_id,
                    'project_name': project_name,
                    'latitude': float(prop.latitude) if prop.latitude else None,
                    'longitude': float(prop.longitude) if prop.longitude else None,
                })

            return {
                'success': True,
                'properties': properties_data,
                'total': len(properties_data),
                'carousel_type': carousel_type
            }

        except Exception as e:
            _logger.error(f"Error cargando carrusel de propiedades ({carousel_type}): {str(e)}")
            return {
                'success': False,
                'properties': [],
                'error': str(e)
            }

    @http.route('/contact/property', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def contact_property(self, **post):
        """
        Endpoint para formulario de contacto desde detalle de propiedad.
        Crea una oportunidad en CRM con los datos del formulario.
        """
        try:
            property_id = post.get('property_id')
            name = post.get('name', '').strip()
            email = post.get('email', '').strip()
            phone = post.get('phone', '').strip()
            client_type = post.get('client_type', 'buyer')
            message = post.get('message', '').strip()
            ideal_visit_date = post.get('ideal_visit_date')  # Nueva fecha de visita

            # Validaciones básicas
            if not property_id or not name or not email or not phone:
                return request.render('theme_bohio_real_estate.property_contact_error', {
                    'error': 'Por favor complete todos los campos obligatorios.'
                })

            # Obtener la propiedad
            property_obj = request.env['product.template'].sudo().browse(int(property_id))
            if not property_obj.exists():
                return request.render('theme_bohio_real_estate.property_contact_error', {
                    'error': 'Propiedad no encontrada.'
                })

            # Buscar o crear partner
            partner = request.env['res.partner'].sudo().search([
                '|', ('email', '=', email), ('phone', '=', phone)
            ], limit=1)

            if not partner:
                partner = request.env['res.partner'].sudo().create({
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'customer_rank': 1,
                })

            # Determinar servicio de interés según tipo de propiedad
            service_interested = 'sale' if property_obj.type_service == 'sale' else 'rent'

            # Preparar fecha de visita
            visit_date = False
            if ideal_visit_date:
                try:
                    visit_date = datetime.strptime(ideal_visit_date, '%Y-%m-%dT%H:%M')
                except:
                    _logger.warning(f"Formato de fecha inválido: {ideal_visit_date}")

            # Crear oportunidad en CRM
            lead_vals = {
                'name': f"Interés en {property_obj.name}",
                'partner_id': partner.id,
                'email_from': email,
                'phone': phone,
                'type': 'opportunity',
                'client_type': client_type,
                'service_interested': service_interested,
                'request_source': 'property_inquiry',
                'property_ids': [(6, 0, [property_obj.id])],
                'description': message or f"Cliente interesado en {property_obj.name}",
                'ideal_visit_date': visit_date,
            }

            # Agregar campos específicos según tipo de servicio
            if service_interested == 'sale' and property_obj.net_price:
                lead_vals['expected_revenue'] = property_obj.net_price
                lead_vals['budget_min'] = property_obj.net_price * 0.9
                lead_vals['budget_max'] = property_obj.net_price * 1.1
            elif service_interested == 'rent' and property_obj.net_rental_price:
                lead_vals['budget_min'] = property_obj.net_rental_price

            # Agregar ubicación y características
            if property_obj.city:
                lead_vals['desired_city'] = property_obj.city
            if property_obj.region_id:
                lead_vals['desired_neighborhood'] = property_obj.region_id.name
            if property_obj.property_type_id:
                lead_vals['desired_property_type_id'] = property_obj.property_type_id.id
            if property_obj.num_bedrooms:
                lead_vals['num_bedrooms_min'] = property_obj.num_bedrooms
            if property_obj.num_bathrooms:
                lead_vals['num_bathrooms_min'] = property_obj.num_bathrooms
            if property_obj.property_area:
                lead_vals['property_area_min'] = property_obj.property_area

            lead = request.env['crm.lead'].sudo().create(lead_vals)

            # Si hay fecha de visita, crear actividad
            if visit_date:
                request.env['mail.activity'].sudo().create({
                    'res_model_id': request.env['ir.model'].sudo().search([('model', '=', 'crm.lead')], limit=1).id,
                    'res_id': lead.id,
                    'activity_type_id': request.env.ref('mail.mail_activity_data_meeting').id,
                    'summary': f'Visita programada a {property_obj.name}',
                    'date_deadline': visit_date.date(),
                    'user_id': lead.user_id.id if lead.user_id else request.env.user.id,
                    'note': f'El cliente {name} solicitó visita para {visit_date.strftime("%d/%m/%Y %H:%M")}',
                })

            # Enviar notificación al equipo de ventas
            lead.message_post(
                body=f"""
                <p><strong>Nueva consulta desde página web</strong></p>
                <ul>
                    <li><strong>Cliente:</strong> {name}</li>
                    <li><strong>Email:</strong> {email}</li>
                    <li><strong>Teléfono:</strong> {phone}</li>
                    <li><strong>Propiedad:</strong> {property_obj.name} ({property_obj.default_code or 'Sin código'})</li>
                    <li><strong>Tipo de cliente:</strong> {dict(request.env['crm.lead']._fields['client_type'].selection).get(client_type, client_type)}</li>
                    {f'<li><strong>Fecha visita solicitada:</strong> {visit_date.strftime("%d/%m/%Y %H:%M")}</li>' if visit_date else ''}
                    {f'<li><strong>Mensaje:</strong> {message}</li>' if message else ''}
                </ul>
                """,
                subject='Nueva Consulta desde Web',
                message_type='comment'
            )

            # Redirigir a página de éxito
            return request.render('theme_bohio_real_estate.property_contact_success', {
                'property': property_obj,
                'lead': lead,
            })

        except Exception as e:
            _logger.error(f"Error procesando formulario de contacto: {str(e)}")
            return request.render('theme_bohio_real_estate.property_contact_error', {
                'error': 'Ocurrió un error al procesar su solicitud. Por favor intente nuevamente.'
            })

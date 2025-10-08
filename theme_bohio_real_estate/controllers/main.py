# -*- coding: utf-8 -*-
from odoo import http, fields, _
from odoo.http import request
from odoo.osv import expression
from datetime import datetime, timedelta
import json
import logging

_logger = logging.getLogger(__name__)


class BohioRealEstateController(http.Controller):

    @http.route('/aboutus', type='http', auth='public', website=True)
    def about_us(self, **kwargs):
        """Página Sobre Nosotros"""
        return request.render('theme_bohio_real_estate.about_us_page', {})

    @http.route('/services', type='http', auth='public', website=True)
    def services(self, **kwargs):
        """Página de Servicios"""
        return request.render('theme_bohio_real_estate.services_page', {})

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

    @http.route(['/property/search/autocomplete'], type='json', auth='public', website=True)
    def property_search_autocomplete(self, term='', limit=10):
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

        return {'results': results[:limit]}

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

    @http.route(['/'], type='http', auth='public', website=True)
    def homepage_new(self, **kwargs):
        """Nueva Homepage BOHIO Real Estate"""
        return request.render('theme_bohio_real_estate.bohio_homepage_new', {})

    @http.route(['/bohio/api/properties'], type='json', auth='public', website=True)
    def api_get_properties(self, type_service=None, state=None, is_project=False, limit=6, **kwargs):
        """API para obtener propiedades para la homepage"""
        domain = [
            ('is_property', '=', True),
            ('active', '=', True),
            ('state', '=', 'free'),
        ]

        if type_service:
            if type_service == 'sale_rent':
                domain.append(('type_service', 'in', ['sale', 'rent', 'sale_rent']))
            else:
                domain.append(('type_service', 'in', [type_service, 'sale_rent']))

        if state:
            if state == 'used':
                domain.append(('product_state', '=', 'used'))
            elif state == 'new':
                domain.append(('product_state', '=', 'new'))

        if is_project:
            domain.append(('project_worksite_id', '!=', False))

        Property = request.env['product.template'].sudo()
        properties = Property.search(domain, limit=limit, order='sequence ASC, create_date DESC')

        # Preparar datos para JSON
        properties_data = []
        for prop in properties:
            # Determinar si es nueva (< 30 días)
            is_new = False
            if prop.create_date:
                thirty_days_ago = datetime.now() - timedelta(days=30)
                is_new = prop.create_date >= thirty_days_ago

            # Obtener URL de imagen
            image_url = f'/web/image/product.template/{prop.id}/image_1920' if prop.image_1920 else None

            properties_data.append({
                'id': prop.id,
                'name': prop.name,
                'default_code': prop.default_code or '',
                'list_price': prop.list_price,
                'property_type': prop.property_type,
                'type_service': prop.type_service,
                'bedrooms': prop.num_bedrooms if hasattr(prop, 'num_bedrooms') else 0,
                'bathrooms': prop.num_bathrooms if hasattr(prop, 'num_bathrooms') else 0,
                'area_constructed': prop.property_area if hasattr(prop, 'property_area') else 0,
                'area_total': prop.property_area if hasattr(prop, 'property_area') else 0,
                'city': prop.city if hasattr(prop, 'city') else '',
                'region': prop.neighborhood if hasattr(prop, 'neighborhood') else '',
                'image_url': image_url,
                'create_date': prop.create_date.isoformat() if prop.create_date else None,
                'is_new': is_new,
                'latitude': prop.latitude if hasattr(prop, 'latitude') else None,
                'longitude': prop.longitude if hasattr(prop, 'longitude') else None,
            })

        return {
            'properties': properties_data,
            'count': len(properties_data)
        }

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

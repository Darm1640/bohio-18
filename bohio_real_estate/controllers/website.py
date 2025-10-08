# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
import base64


class BohioWebsiteController(http.Controller):
    """Controlador para website público - Bohío Real Estate"""

    @http.route('/', type='http', auth='public', website=True)
    def bohio_home(self, **kw):
        """Homepage landing con secciones de arriendo, venta y proyectos"""
        Product = request.env['product.template'].sudo()
        City = request.env['res.city'].sudo()
        Contract = request.env['property.contract'].sudo()

        # Propiedades en arriendo
        rent_properties = Product.search([
            ('is_property', '=', True),
            ('website_published', '=', True),
            ('state', '=', 'free'),
            ('net_rental_price', '>', 0)
        ], limit=4, order='create_date desc')

        # Propiedades en venta (usados)
        sale_properties = Product.search([
            ('is_property', '=', True),
            ('website_published', '=', True),
            ('state', '=', 'free'),
            ('net_price', '>', 0)
        ], limit=4, order='create_date desc')

        # Proyectos en venta (por ahora mostramos propiedades)
        projects = Product.search([
            ('is_property', '=', True),
            ('website_published', '=', True),
            ('net_price', '>', 0)
        ], limit=3, order='create_date desc')

        # Ciudades para el buscador
        cities = City.search([
            ('state_id.country_id.code', '=', 'CO')
        ], order='name', limit=50)

        # Stats
        total_properties = Product.search_count([
            ('is_property', '=', True),
            ('website_published', '=', True)
        ])

        active_contracts = Contract.search_count([
            ('state', 'in', ['active', 'running'])
        ])

        # Clientes satisfechos (estimado)
        happy_clients = 150

        stats = {
            'total_properties': total_properties,
            'active_contracts': active_contracts,
            'happy_clients': happy_clients
        }

        return request.render('theme_bohio_real_estate.bohio_homepage_new', {
            'rent_properties': rent_properties,
            'sale_properties': sale_properties,
            'projects': projects,
            'cities': cities,
            'stats': stats
        })

    @http.route('/properties/map', type='http', auth='public', website=True)
    def properties_map(self, **kw):
        """Vista de lista/mapa de propiedades con OpenStreetMap"""
        City = request.env['res.city']

        # Obtener ciudades para filtro
        cities = City.sudo().search([
            ('state_id.country_id.code', '=', 'CO')
        ], order='name', limit=100)

        return request.render('theme_bohio_real_estate.properties_list_map_page', {
            'cities': cities
        })

    @http.route('/api/properties/map', type='json', auth='public', website=True)
    def api_properties_map(self, **kw):
        domain = [
            ('is_property', '=', True),
            ('state', '=', 'free'),
            ('website_published', '=', True)
        ]

        if kw.get('type_service'):
            domain.append(('type_service', '=', kw['type_service']))
        if kw.get('property_type'):
            domain.append(('property_type', '=', kw['property_type']))
        if kw.get('price_min'):
            domain.append(('list_price', '>=', float(kw['price_min'])))
        if kw.get('price_max'):
            domain.append(('list_price', '<=', float(kw['price_max'])))
        if kw.get('bedrooms'):
            domain.append(('num_bedrooms', '>=', int(kw['bedrooms'])))
        if kw.get('bathrooms'):
            domain.append(('num_bathrooms', '>=', int(kw['bathrooms'])))
        if kw.get('area_min'):
            domain.append(('property_area', '>=', float(kw['area_min'])))
        if kw.get('area_max'):
            domain.append(('property_area', '<=', float(kw['area_max'])))

        properties = request.env['product.template'].sudo().search(domain, limit=100)

        result = []
        for prop in properties:
            result.append({
                'id': prop.id,
                'name': prop.name,
                'default_code': prop.default_code,
                'address': prop.address or f"{prop.street}, {prop.city}",
                'latitude': prop.latitude,
                'longitude': prop.longitude,
                'price': prop.list_price,
                'type_service': prop.type_service,
                'property_type': prop.property_type,
                'bedrooms': prop.num_bedrooms,
                'bathrooms': prop.num_bathrooms,
                'area': prop.property_area,
                'image': f"/web/image/product.template/{prop.id}/image_1920",
                'url': f"/property/{prop.id}"
            })

        return {'properties': result}

    # TODO: Crear vista property_compare_view en theme_bohio_real_estate
    # @http.route('/properties/compare', type='http', auth='public', website=True)
    # def properties_compare(self, ids='', **kw):
    #     if not ids:
    #         return request.redirect('/properties')
    #
    #     property_ids = [int(x) for x in ids.split(',') if x.isdigit()]
    #     if len(property_ids) < 2:
    #         return request.redirect('/properties')
    #
    #     property_ids = property_ids[:4]
    #
    #     properties = request.env['product.template'].sudo().browse(property_ids)
    #
    #     return request.render('theme_bohio_real_estate.property_compare_view', {
    #         'properties': properties
    #     })

    @http.route('/contact/property/<int:property_id>', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def contact_property(self, property_id, **post):
        property_obj = request.env['product.template'].sudo().browse(property_id)

        if not property_obj.exists():
            return request.redirect('/properties')

        lead_vals = {
            'name': f"Consulta - {property_obj.name}",
            'contact_name': post.get('name'),
            'email_from': post.get('email'),
            'phone': post.get('phone'),
            'description': post.get('message'),
            'request_source': 'property_inquiry',
            'client_type': post.get('client_type', 'buyer'),
            'service_interested': property_obj.type_service,
            'property_ids': [(4, property_id)],
            'type': 'opportunity',
            'expected_revenue': property_obj.list_price,
        }

        real_estate_team = request.env['crm.team'].sudo().search([
            '|',
            ('name', 'ilike', 'inmobiliaria'),
            ('name', 'ilike', 'real estate')
        ], limit=1)

        if real_estate_team:
            lead_vals['team_id'] = real_estate_team.id

        request.env['crm.lead'].sudo().create(lead_vals)

        return request.render('bohio_real_estate.contact_thanks', {
            'property': property_obj
        })

    @http.route('/pqrs', type='http', auth='public', website=True)
    def pqrs_form(self, **kw):
        return request.render('bohio_real_estate.pqrs_form')

    @http.route('/pqrs/submit', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def pqrs_submit(self, **post):
        pqrs_type = post.get('pqrs_type', 'petition')
        pqrs_type_labels = {
            'petition': 'Petición',
            'complaint': 'Queja',
            'claim': 'Reclamo',
            'suggestion': 'Sugerencia'
        }

        partner = None
        if request.env.user and request.env.user != request.env.ref('base.public_user'):
            partner = request.env.user.partner_id

        pqrs_team = request.env['helpdesk.team'].sudo().search([
            '|',
            ('name', 'ilike', 'pqrs'),
            ('name', 'ilike', 'servicio')
        ], limit=1)

        if not pqrs_team:
            pqrs_team = request.env['helpdesk.team'].sudo().search([], limit=1)

        ticket_vals = {
            'name': f"{pqrs_type_labels.get(pqrs_type, 'Solicitud')} - {post.get('name', 'Cliente')}",
            'partner_id': partner.id if partner else False,
            'partner_name': post.get('name'),
            'partner_email': post.get('email'),
            'partner_phone': post.get('phone'),
            'description': post.get('message'),
            'team_id': pqrs_team.id if pqrs_team else False,
            'ticket_type_id': False,
        }

        ticket = request.env['helpdesk.ticket'].sudo().create(ticket_vals)

        if post.get('attachment'):
            attachment_vals = {
                'name': post.get('attachment').filename,
                'datas': base64.b64encode(post.get('attachment').read()),
                'res_model': 'helpdesk.ticket',
                'res_id': ticket.id,
            }
            request.env['ir.attachment'].sudo().create(attachment_vals)

        return request.render('bohio_real_estate.pqrs_thanks', {
            'ticket': ticket
        })

    @http.route('/property/<int:property_id>', type='http', auth='public', website=True)
    def property_detail(self, property_id, **kw):
        prop = request.env['product.template'].sudo().search([
            ('id', '=', property_id),
            ('is_property', '=', True),
            ('website_published', '=', True)
        ], limit=1)

        if not prop:
            return request.redirect('/properties')

        return request.render('theme_bohio_real_estate.property_detail', {
            'property': prop
        })

    @http.route([
        '/properties',
        '/properties/page/<int:page>'
    ], type='http', auth='public', website=True)
    def properties_shop(self, page=1, search='', property_type=None, type_service=None,
                       state_id=None, city_id=None, region_id=None,
                       bedrooms=None, bathrooms=None,
                       price_min=0.0, price_max=0.0,
                       area_min=0.0, area_max=0.0,
                       garage=None, parking=None,
                       ppg=12, **post):

        Product = request.env['product.template']
        Region = request.env['region.region']
        State = request.env['res.country.state']
        City = request.env['res.city']

        domain = [
            ('is_property', '=', True),
            ('website_published', '=', True)
        ]

        if search:
            domain.append('|')
            domain.append(('name', 'ilike', search))
            domain.append('|')
            domain.append(('default_code', 'ilike', search))
            domain.append(('description', 'ilike', search))

        if property_type:
            domain.append(('property_type', '=', property_type))

        if type_service:
            domain.append(('type_service', '=', type_service))

        if state_id:
            try:
                domain.append(('state_id', '=', int(state_id)))
            except (ValueError, TypeError):
                pass

        if city_id:
            try:
                domain.append(('city_id', '=', int(city_id)))
            except (ValueError, TypeError):
                pass

        if region_id:
            try:
                domain.append(('region_id', '=', int(region_id)))
            except (ValueError, TypeError):
                pass

        if bedrooms:
            try:
                domain.append(('num_bedrooms', '>=', int(bedrooms)))
            except (ValueError, TypeError):
                pass

        if bathrooms:
            try:
                domain.append(('num_bathrooms', '>=', int(bathrooms)))
            except (ValueError, TypeError):
                pass

        try:
            price_min = float(price_min or 0)
            price_max = float(price_max or 0)
        except ValueError:
            price_min = price_max = 0

        if price_min > 0:
            domain.append(('list_price', '>=', price_min))
        if price_max > 0:
            domain.append(('list_price', '<=', price_max))

        try:
            area_min = float(area_min or 0)
            area_max = float(area_max or 0)
        except ValueError:
            area_min = area_max = 0

        if area_min > 0:
            domain.append(('property_area', '>=', area_min))
        if area_max > 0:
            domain.append(('property_area', '<=', area_max))

        if garage:
            domain.append(('garage', '=', True))

        if parking:
            try:
                total_parking = int(parking)
                domain.append('|')
                domain.append(('covered_parking', '>=', total_parking))
                domain.append(('uncovered_parking', '>=', total_parking))
            except (ValueError, TypeError):
                pass

        product_count = Product.sudo().search_count(domain)

        pager = request.website.pager(
            url='/properties',
            total=product_count,
            page=page,
            step=ppg,
            url_args=post
        )

        properties = Product.sudo().search(
            domain,
            limit=ppg,
            offset=pager['offset'],
            order='sequence, property_date desc, id desc'
        )

        keep = QueryURL('/properties',
                       search=search,
                       property_type=property_type,
                       type_service=type_service,
                       state_id=state_id,
                       city_id=city_id,
                       region_id=region_id,
                       bedrooms=bedrooms,
                       bathrooms=bathrooms,
                       price_min=price_min,
                       price_max=price_max,
                       area_min=area_min,
                       area_max=area_max,
                       garage=garage,
                       parking=parking)

        states = State.sudo().search([('country_id.code', '=', 'CO')], order='name')
        cities = City.sudo().search([], order='name', limit=1000)
        regions = Region.sudo().search([], order='name')

        property_types = Product.sudo().read_group(
            [('is_property', '=', True), ('property_type', '!=', False)],
            ['property_type'],
            ['property_type']
        )

        values = {
            'properties': properties,
            'pager': pager,
            'keep': keep,
            'search': search,
            'property_type': property_type,
            'type_service': type_service,
            'state_id': int(state_id) if state_id else None,
            'city_id': int(city_id) if city_id else None,
            'region_id': int(region_id) if region_id else None,
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'price_min': price_min,
            'price_max': price_max,
            'area_min': area_min,
            'area_max': area_max,
            'garage': garage,
            'parking': parking,
            'states': states,
            'cities': cities,
            'regions': regions,
            'property_types': property_types,
            'product_count': product_count,
        }

        return request.render('theme_bohio_real_estate.properties_shop', values)

    @http.route('/api/properties/search_by_code', type='json', auth='public', website=True)
    def search_by_code(self, code='', **kw):
        if not code:
            return {'error': 'Código requerido'}

        code_clean = code.strip().upper()

        prop = request.env['product.template'].sudo().search([
            ('is_property', '=', True),
            ('default_code', 'ilike', code_clean),
            ('website_published', '=', True)
        ], limit=1)

        if not prop:
            prop = request.env['product.template'].sudo().search([
                ('is_property', '=', True),
                ('default_code', 'ilike', f'%{code_clean}%'),
            ], limit=1)

        if prop:
            return {
                'found': True,
                'id': prop.id,
                'name': prop.name,
                'code': prop.default_code,
                'url': f'/property/{prop.id}',
                'published': prop.website_published
            }

        return {'found': False, 'error': f'No se encontró ninguna propiedad con el código "{code}"'}

    @http.route('/api/cities_by_state', type='json', auth='public', website=True)
    def cities_by_state(self, state_id=None, **kw):
        if not state_id:
            return {'cities': []}

        cities = request.env['res.city'].sudo().search([
            ('state_id', '=', int(state_id))
        ], order='name')

        return {
            'cities': [{'id': c.id, 'name': c.name} for c in cities]
        }

    @http.route('/api/regions_by_city', type='json', auth='public', website=True)
    def regions_by_city(self, city_name='', **kw):
        if not city_name:
            return {'regions': []}

        regions = request.env['region.region'].sudo().search([
            ('city_id.name', '=ilike', city_name)
        ], order='name')

        return {
            'regions': [{'id': r.id, 'name': r.name} for r in regions]
        }

    def _get_property_characteristics_map(self):
        """Mapeo de características relevantes por tipo de propiedad"""
        return {
            'apartment': {
                'basic': ['num_bedrooms', 'num_bathrooms', 'property_area', 'floor_number', 'apartment_type'],
                'price': ['net_price', 'net_rental_price', 'price_per_unit'],
                'amenities': ['elevator', 'balcony', 'doorman', 'parking', 'furnished'],
                'building': ['pools', 'gym', 'social_room', 'green_areas']
            },
            'house': {
                'basic': ['num_bedrooms', 'num_bathrooms', 'property_area', 'number_of_levels', 'property_age'],
                'price': ['net_price', 'net_rental_price', 'price_per_unit'],
                'amenities': ['garage', 'patio', 'garden', 'terrace', 'furnished'],
                'features': ['service_room', 'study', 'fireplace']
            },
            'studio': {
                'basic': ['num_bathrooms', 'property_area', 'floor_number'],
                'price': ['net_price', 'net_rental_price', 'price_per_unit'],
                'amenities': ['elevator', 'balcony', 'furnished'],
                'building': ['doorman', 'parking']
            },
            'office': {
                'basic': ['property_area', 'floor_number', 'number_of_levels'],
                'price': ['net_price', 'net_rental_price', 'price_per_unit'],
                'amenities': ['elevator', 'air_conditioning', 'parking'],
                'features': ['electrical_capacity', 'phone_lines']
            },
            'bodega': {
                'basic': ['property_area', 'front_meters', 'depth_meters'],
                'price': ['net_price', 'net_rental_price', 'price_per_unit'],
                'features': ['truck_door', 'electric_plant', 'electrical_capacity'],
                'security': ['has_security', 'security_cameras']
            },
            'local': {
                'basic': ['property_area', 'front_meters', 'floor_number'],
                'price': ['net_price', 'net_rental_price', 'price_per_unit'],
                'amenities': ['air_conditioning', 'bathroom'],
                'features': ['electrical_capacity', 'water_nearby']
            },
            'finca': {
                'basic': ['property_area', 'unit_of_measure'],
                'price': ['net_price', 'net_rental_price'],
                'features': ['has_water', 'water_nearby', 'aqueduct_access'],
                'amenities': ['num_bedrooms', 'num_bathrooms', 'pools']
            },
            'lot': {
                'basic': ['property_area', 'front_meters', 'depth_meters', 'unit_of_measure'],
                'price': ['net_price', 'price_per_unit'],
                'features': ['water_nearby', 'aqueduct_access', 'urban_space'],
                'location': ['stratum', 'state_id', 'city_id']
            },
            'country_lot': {
                'basic': ['property_area', 'unit_of_measure', 'front_meters', 'depth_meters'],
                'price': ['net_price', 'price_per_unit'],
                'features': ['water_nearby', 'aqueduct_access'],
                'location': ['state_id', 'city_id']
            },
            'hotel': {
                'basic': ['property_area', 'num_bedrooms', 'number_of_levels'],
                'price': ['net_price', 'net_rental_price'],
                'amenities': ['pools', 'gym', 'social_room', 'parking'],
                'features': ['elevator', 'restaurant']
            },
            'building': {
                'basic': ['property_area', 'number_of_levels'],
                'price': ['net_price', 'net_rental_price'],
                'features': ['elevator', 'parking', 'electrical_capacity'],
                'location': ['state_id', 'city_id', 'stratum']
            }
        }

    def _get_property_fields(self, prop):
        """Obtiene campos relevantes según tipo de propiedad"""
        characteristics_map = self._get_property_characteristics_map()
        property_type = prop.property_type or 'apartment'

        char_config = characteristics_map.get(property_type, characteristics_map['apartment'])

        result = {
            'id': prop.id,
            'name': prop.name,
            'default_code': prop.default_code,
            'type_service': prop.type_service,
            'property_type': prop.property_type,
            'property_type_name': prop.property_type_id.name if prop.property_type_id else '',
            'currency': prop.currency_id.symbol if prop.currency_id else '$',
            'address': prop.address or '',
            'city': prop.city_id.name if prop.city_id else '',
            'state': prop.state_id.name if prop.state_id else '',
            'region': prop.region_id.name if prop.region_id else '',
            'image_url': f'/web/image/product.template/{prop.id}/image_1920',
            'url': f'/property/{prop.id}',
            'latitude': prop.latitude,
            'longitude': prop.longitude,
        }

        all_fields = []
        for category in char_config.values():
            all_fields.extend(category)

        field_mapping = {
            'num_bedrooms': ('bedrooms', lambda p: p.num_bedrooms),
            'num_bathrooms': ('bathrooms', lambda p: p.num_bathrooms),
            'property_area': ('area', lambda p: p.property_area),
            'unit_of_measure': ('area_unit', lambda p: p.unit_of_measure),
            'floor_number': ('floor', lambda p: p.floor_number),
            'number_of_levels': ('levels', lambda p: p.number_of_levels),
            'property_age': ('age', lambda p: p.property_age),
            'apartment_type': ('apartment_type', lambda p: p.apartment_type),
            'front_meters': ('front_meters', lambda p: p.front_meters),
            'depth_meters': ('depth_meters', lambda p: p.depth_meters),
            'net_price': ('sale_price', lambda p: p.net_price),
            'net_rental_price': ('rental_price', lambda p: p.net_rental_price),
            'price_per_unit': ('price_per_unit', lambda p: p.price_per_unit),
            'stratum': ('stratum', lambda p: p.stratum),
            'parking': ('parking', lambda p: (prop.covered_parking or 0) + (prop.uncovered_parking or 0)),
            'garage': ('has_garage', lambda p: p.garage),
            'elevator': ('has_elevator', lambda p: p.elevator),
            'pools': ('has_pool', lambda p: p.pools),
            'gym': ('has_gym', lambda p: p.gym),
            'furnished': ('is_furnished', lambda p: p.furnished),
            'balcony': ('has_balcony', lambda p: p.balcony),
            'terrace': ('has_terrace', lambda p: p.terrace),
            'patio': ('has_patio', lambda p: p.patio),
            'garden': ('has_garden', lambda p: p.garden),
        }

        for field in all_fields:
            if field in field_mapping:
                key, getter = field_mapping[field]
                result[key] = getter(prop)

        return result

    @http.route('/api/properties/search', type='json', auth='public', website=True)
    def api_properties_search(self, filters=None, page=1, limit=12, **kw):
        Product = request.env['product.template']

        domain = [
            ('is_property', '=', True),
            ('website_published', '=', True)
        ]

        if not filters:
            filters = {}

        if filters.get('search'):
            search_term = filters['search']
            domain.append('|')
            domain.append(('name', 'ilike', search_term))
            domain.append('|')
            domain.append(('default_code', 'ilike', search_term))
            domain.append(('description', 'ilike', search_term))

        if filters.get('property_type'):
            domain.append(('property_type', '=', filters['property_type']))

        if filters.get('type_service'):
            domain.append(('type_service', '=', filters['type_service']))

        if filters.get('state_id'):
            domain.append(('state_id', '=', int(filters['state_id'])))

        if filters.get('city_id'):
            domain.append(('city_id', '=', int(filters['city_id'])))

        if filters.get('region_id'):
            domain.append(('region_id', '=', int(filters['region_id'])))

        if filters.get('bedrooms'):
            domain.append(('num_bedrooms', '>=', int(filters['bedrooms'])))

        if filters.get('bathrooms'):
            domain.append(('num_bathrooms', '>=', int(filters['bathrooms'])))

        if filters.get('price_min'):
            domain.append('|')
            domain.append(('net_price', '>=', float(filters['price_min'])))
            domain.append(('net_rental_price', '>=', float(filters['price_min'])))

        if filters.get('price_max'):
            domain.append('|')
            domain.append(('net_price', '<=', float(filters['price_max'])))
            domain.append(('net_rental_price', '<=', float(filters['price_max'])))

        if filters.get('area_min'):
            domain.append(('property_area', '>=', float(filters['area_min'])))

        if filters.get('area_max'):
            domain.append(('property_area', '<=', float(filters['area_max'])))

        if filters.get('garage'):
            domain.append(('garage', '=', True))

        if filters.get('parking'):
            total_parking = int(filters['parking'])
            domain.append('|')
            domain.append(('covered_parking', '>=', total_parking))
            domain.append(('uncovered_parking', '>=', total_parking))

        total_count = Product.sudo().search_count(domain)

        offset = (page - 1) * limit
        properties = Product.sudo().search(
            domain,
            limit=limit,
            offset=offset,
            order='sequence, property_date desc, id desc'
        )

        results = []
        for prop in properties:
            results.append(self._get_property_fields(prop))

        return {
            'properties': results,
            'total': total_count,
            'page': page,
            'pages': (total_count + limit - 1) // limit,
            'limit': limit
        }

    @http.route('/api/location/autocomplete', type='json', auth='public', website=True)
    def location_autocomplete(self, term='', **kw):
        """Autocomplete para ubicaciones: departamentos, ciudades y barrios"""
        if not term or len(term) < 2:
            return {'results': []}

        term = term.strip()
        results = []

        State = request.env['res.country.state'].sudo()
        City = request.env['res.city'].sudo()
        Region = request.env['region.region'].sudo()

        states = State.search([
            ('country_id.code', '=', 'CO'),
            ('name', 'ilike', term)
        ], limit=5, order='name')

        for state in states:
            city_count = City.search_count([('state_id', '=', state.id)])
            results.append({
                'type': 'state',
                'id': state.id,
                'name': state.name,
                'display': f"{state.name} (Departamento)",
                'subtitle': f"{city_count} ciudades",
                'level': 1
            })

        cities = City.search([
            ('name', 'ilike', term)
        ], limit=8, order='name')

        for city in cities:
            region_count = Region.search_count([('city_id', '=', city.id)])
            results.append({
                'type': 'city',
                'id': city.id,
                'name': city.name,
                'state_id': city.state_id.id,
                'state_name': city.state_id.name,
                'display': f"{city.name}, {city.state_id.name}",
                'subtitle': f"{region_count} barrios",
                'level': 2
            })

        regions = Region.search([
            ('name', 'ilike', term)
        ], limit=10, order='name')

        for region in regions:
            results.append({
                'type': 'region',
                'id': region.id,
                'name': region.name,
                'city_id': region.city_id.id,
                'city_name': region.city_id.name,
                'state_id': region.city_id.state_id.id,
                'state_name': region.city_id.state_id.name,
                'display': f"{region.name}",
                'subtitle': f"{region.city_id.name}, {region.city_id.state_id.name}",
                'level': 3
            })

        results.sort(key=lambda x: (x['level'], x['name']))

        return {'results': results}

    # TODO: Crear vistas de servicios y páginas informativas en theme_bohio_real_estate
    # @http.route('/servicios/venta', type='http', auth='public', website=True)
    # def servicio_venta(self, **kw):
    #     return request.render('theme_bohio_real_estate.servicio_venta')
    #
    # @http.route('/servicios/arriendo', type='http', auth='public', website=True)
    # def servicio_arriendo(self, **kw):
    #     return request.render('theme_bohio_real_estate.servicio_arriendo')
    #
    # @http.route('/servicios/juridico', type='http', auth='public', website=True)
    # def servicio_juridico(self, **kw):
    #     return request.render('theme_bohio_real_estate.servicio_juridico')
    #
    # @http.route('/servicios/marketing', type='http', auth='public', website=True)
    # def servicio_marketing(self, **kw):
    #     return request.render('theme_bohio_real_estate.servicio_marketing')
    #
    # @http.route('/clientes/propietarios', type='http', auth='public', website=True)
    # def clientes_propietarios(self, **kw):
    #     return request.render('theme_bohio_real_estate.clientes_propietarios')
    #
    # @http.route('/clientes/arrendatarios', type='http', auth='public', website=True)
    # def clientes_arrendatarios(self, **kw):
    #     return request.render('theme_bohio_real_estate.clientes_arrendatarios')
    #
    # @http.route('/contacto', type='http', auth='public', website=True)
    # def contacto(self, **kw):
    #     return request.render('theme_bohio_real_estate.contacto_page')

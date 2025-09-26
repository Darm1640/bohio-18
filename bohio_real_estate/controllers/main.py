from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
import json


class BohioRealEstateController(http.Controller):

    @http.route('/properties/map', type='http', auth='public', website=True)
    def properties_map(self, **kw):
        return request.render('bohio_real_estate.property_map_view')

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

    @http.route('/properties/compare', type='http', auth='public', website=True)
    def properties_compare(self, ids='', **kw):
        if not ids:
            return request.redirect('/properties')

        property_ids = [int(x) for x in ids.split(',') if x.isdigit()]
        if len(property_ids) < 2:
            return request.redirect('/properties')

        property_ids = property_ids[:4]

        properties = request.env['product.template'].sudo().browse(property_ids)

        return request.render('bohio_real_estate.property_compare_view', {
            'properties': properties
        })

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
        lead_vals = {
            'name': f"PQRS - {post.get('pqrs_type', 'Solicitud')}",
            'contact_name': post.get('name'),
            'email_from': post.get('email'),
            'phone': post.get('phone'),
            'description': post.get('message'),
            'request_source': 'pqrs',
            'client_type': post.get('client_type'),
            'pqrs_type': post.get('pqrs_type'),
            'type': 'lead',
        }

        service_team = request.env['crm.team'].sudo().search([
            '|',
            ('name', 'ilike', 'servicio'),
            ('name', 'ilike', 'service')
        ], limit=1)

        if service_team:
            lead_vals['team_id'] = service_team.id

        request.env['crm.lead'].sudo().create(lead_vals)

        return request.render('bohio_real_estate.pqrs_thanks')

    @http.route('/property/<int:property_id>', type='http', auth='public', website=True)
    def property_detail(self, property_id, **kw):
        prop = request.env['product.template'].sudo().search([
            ('id', '=', property_id),
            ('is_property', '=', True),
            ('website_published', '=', True)
        ], limit=1)

        if not prop:
            return request.redirect('/properties')

        return request.render('bohio_real_estate.property_detail', {
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

        return request.render('bohio_real_estate.properties_shop', values)

    @http.route('/api/properties/search_by_code', type='json', auth='public', website=True)
    def search_by_code(self, code='', **kw):
        if not code:
            return {'error': 'Código requerido'}

        prop = request.env['product.template'].sudo().search([
            ('is_property', '=', True),
            ('default_code', '=ilike', code.strip()),
            ('website_published', '=', True)
        ], limit=1)

        if prop:
            return {
                'found': True,
                'id': prop.id,
                'name': prop.name,
                'code': prop.default_code,
                'url': f'/property/{prop.id}'
            }

        return {'found': False, 'error': 'Propiedad no encontrada'}

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

    @http.route('/servicios/venta', type='http', auth='public', website=True)
    def servicio_venta(self, **kw):
        return request.render('bohio_real_estate.servicio_venta')

    @http.route('/servicios/arriendo', type='http', auth='public', website=True)
    def servicio_arriendo(self, **kw):
        return request.render('bohio_real_estate.servicio_arriendo')

    @http.route('/servicios/juridico', type='http', auth='public', website=True)
    def servicio_juridico(self, **kw):
        return request.render('bohio_real_estate.servicio_juridico')

    @http.route('/servicios/marketing', type='http', auth='public', website=True)
    def servicio_marketing(self, **kw):
        return request.render('bohio_real_estate.servicio_marketing')

    @http.route('/clientes/propietarios', type='http', auth='public', website=True)
    def clientes_propietarios(self, **kw):
        return request.render('bohio_real_estate.clientes_propietarios')

    @http.route('/clientes/arrendatarios', type='http', auth='public', website=True)
    def clientes_arrendatarios(self, **kw):
        return request.render('bohio_real_estate.clientes_arrendatarios')

    @http.route('/contacto', type='http', auth='public', website=True)
    def contacto(self, **kw):
        return request.render('bohio_real_estate.contacto_page')

    @http.route('/my/opportunities', type='http', auth='user', website=True)
    def portal_my_opportunities(self, **kw):
        partner = request.env.user.partner_id
        
        opportunities = request.env['crm.lead'].search([
            ('partner_id', '=', partner.id),
            ('show_in_portal', '=', True),
            ('type', '=', 'opportunity')
        ], order='create_date desc')
        
        return request.render('bohio_real_estate.portal_my_opportunities', {
            'opportunities': opportunities,
            'page_name': 'opportunities',
        })

    @http.route('/my/opportunity/<int:opportunity_id>', type='http', auth='user', website=True)
    def portal_opportunity_detail(self, opportunity_id, **kw):
        opportunity = request.env['crm.lead'].search([
            ('id', '=', opportunity_id),
            ('partner_id', '=', request.env.user.partner_id.id),
            ('show_in_portal', '=', True)
        ], limit=1)

        if not opportunity:
            return request.redirect('/my/opportunities')

        return request.render('bohio_real_estate.portal_opportunity_detail', {
            'opportunity': opportunity,
            'page_name': 'opportunity_detail',
        })

    @http.route('/my/properties', type='http', auth='user', website=True)
    def portal_my_properties(self, **kw):
        partner = request.env.user.partner_id

        properties = request.env['product.template'].sudo().search([
            ('is_property', '=', True),
            '|',
            ('partner_id', '=', partner.id),
            ('owners_lines.partner_id', '=', partner.id)
        ], order='create_date desc')

        contracts = request.env['property.contract'].search([
            ('partner_id', '=', partner.id),
            ('state', '!=', 'cancel')
        ], order='date_from desc')

        tenant_properties = contracts.mapped('property_id')

        return request.render('bohio_real_estate.portal_my_properties', {
            'properties': properties,
            'tenant_properties': tenant_properties,
            'page_name': 'my_properties',
        })

    @http.route('/my/contracts', type='http', auth='user', website=True)
    def portal_my_contracts(self, **kw):
        partner = request.env.user.partner_id

        contracts = request.env['property.contract'].search([
            ('partner_id', '=', partner.id)
        ], order='date_from desc')

        return request.render('bohio_real_estate.portal_my_contracts', {
            'contracts': contracts,
            'page_name': 'contracts',
        })

    @http.route('/my/contract/<int:contract_id>', type='http', auth='user', website=True)
    def portal_contract_detail(self, contract_id, **kw):
        contract = request.env['property.contract'].search([
            ('id', '=', contract_id),
            ('partner_id', '=', request.env.user.partner_id.id)
        ], limit=1)

        if not contract:
            return request.redirect('/my/contracts')

        return request.render('bohio_real_estate.portal_contract_detail', {
            'contract': contract,
            'page_name': 'contract_detail',
        })

    @http.route('/my/payments', type='http', auth='user', website=True)
    def portal_my_payments(self, **kw):
        partner = request.env.user.partner_id

        payments = request.env['recaudo.news.payment'].search([
            ('partner_id', '=', partner.id)
        ], order='create_date desc')

        return request.render('bohio_real_estate.portal_my_payments', {
            'payments': payments,
            'page_name': 'payments',
        })
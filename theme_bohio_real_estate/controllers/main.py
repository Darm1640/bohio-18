# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


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

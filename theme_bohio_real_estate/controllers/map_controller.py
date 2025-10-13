# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

# Coordenadas de Montería, Córdoba
DEFAULT_LAT = 8.7479
DEFAULT_LNG = -75.8814
DEFAULT_ZOOM = 12
ZOOM_WITH_USER = 13
RADIUS_KM = 50

class BohioMapController(http.Controller):

    @http.route('/mapa-propiedades', type='http', auth='public', website=True)
    def mapa_propiedades(self, **kw):
        """Vista principal del mapa"""
        return request.render('theme_bohio_real_estate.mapa_propiedades_view')

    @http.route('/api/properties/mapa', type='json', auth='public', website=True, csrf=False)
    def get_properties_mapa(self, **kw):
        """Obtener propiedades para el mapa con geolocalización"""

        user_lat = kw.get('user_lat')
        user_lng = kw.get('user_lng')

        # Dominio base
        domain = [
            ('is_property', '=', True),
            ('active', '=', True),
            ('state', '=', 'free'),
            ('latitude', '!=', False),
            ('longitude', '!=', False)
        ]

        # Filtro por proximidad si hay ubicación del usuario
        if user_lat and user_lng:
            try:
                bbox = self._get_bounding_box(float(user_lat), float(user_lng), RADIUS_KM)
                domain.extend([
                    ('latitude', '>=', bbox['lat_min']),
                    ('latitude', '<=', bbox['lat_max']),
                    ('longitude', '>=', bbox['lng_min']),
                    ('longitude', '<=', bbox['lng_max'])
                ])
                _logger.info(f"Filtering properties within {RADIUS_KM}km of user location")
            except (ValueError, TypeError) as e:
                _logger.warning(f"Invalid user coordinates: {e}")

        # Buscar propiedades
        properties = request.env['product.template'].sudo().search_read(
            domain,
            ['id', 'name', 'latitude', 'longitude', 'list_price',
             'type_service', 'num_bedrooms', 'num_bathrooms',
             'property_area', 'street', 'city_id', 'image_1920'],
            limit=200
        )

        # Formatear datos para el mapa
        property_data = []
        for prop in properties:
            # Determinar precio
            price_text = f"${prop['list_price']:,.0f}"
            if prop['type_service'] == 'rent':
                price_text += "/mes"
            elif prop['type_service'] == 'sale_rent':
                price_text += " (V/A)"

            # URL de la propiedad
            prop_slug = prop['name'].replace(' ', '-').lower()
            prop_url = f"/shop/product/{prop['id']}"

            property_data.append({
                'id': prop['id'],
                'name': prop['name'],
                'lat': prop['latitude'],
                'lng': prop['longitude'],
                'price': price_text,
                'url': prop_url,
                'bedrooms': int(prop['num_bedrooms'] or 0),
                'bathrooms': int(prop['num_bathrooms'] or 0),
                'area': prop['property_area'] or 0,
                'city': prop['city_id'][1] if prop['city_id'] else '',
                'address': prop['street'] or '',
                'type': prop['type_service']
            })

        # Determinar centro del mapa
        if property_data:
            center_lat = property_data[0]['lat']
            center_lng = property_data[0]['lng']
            zoom = ZOOM_WITH_USER if user_lat and user_lng else DEFAULT_ZOOM
        elif user_lat and user_lng:
            center_lat = float(user_lat)
            center_lng = float(user_lng)
            zoom = ZOOM_WITH_USER
        else:
            center_lat = DEFAULT_LAT
            center_lng = DEFAULT_LNG
            zoom = DEFAULT_ZOOM

        return {
            'properties': property_data,
            'center': {'lat': center_lat, 'lng': center_lng},
            'zoom': zoom,
            'has_user_location': bool(user_lat and user_lng),
            'property_count': len(property_data)
        }

    def _get_bounding_box(self, lat, lng, radius_km):
        """Calcular bounding box para búsqueda por proximidad"""
        # Aproximación: 1 grado de latitud ≈ 111 km
        lat_delta = radius_km / 111.0
        # Ajustar longitud según latitud
        lng_delta = radius_km / (111.0 * abs(lat) * 0.0175)

        return {
            'lat_min': lat - lat_delta,
            'lat_max': lat + lat_delta,
            'lng_min': lng - lng_delta,
            'lng_max': lng + lng_delta
        }

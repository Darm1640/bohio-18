# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class PropertyFiltersAPI(http.Controller):
    """API para filtros avanzados de propiedades con características agrupadas"""

    @http.route('/api/property/filters/grouped', type='json', auth='public', methods=['POST'], csrf=False)
    def get_grouped_filters(self, property_type=None, **kwargs):
        """
        Retorna filtros agrupados por características según tipo de inmueble

        Args:
            property_type: Tipo de inmueble para filtros específicos

        Returns:
            dict: Estructura con filtros agrupados y opciones
        """
        try:
            # Obtener características según tipo de inmueble
            characteristics = request.env['property.characteristic.item'].sudo().search([
                ('active', '=', True)
            ], order='category, sequence')

            # Agrupar por categoría
            filters_by_category = {}
            for char in characteristics:
                if char.category not in filters_by_category:
                    filters_by_category[char.category] = []

                filters_by_category[char.category].append({
                    'id': char.id,
                    'name': char.name,
                    'field_name': char.field_name,
                    'field_type': char.field_type,
                    'icon': char.icon,
                })

            # Obtener grupos de filtros específicos del tipo
            filter_groups = []
            if property_type:
                groups = request.env['property.filter.characteristics'].sudo().search([
                    '|',
                    ('property_type', '=', property_type),
                    ('property_type', '=', 'all'),
                    ('active', '=', True)
                ], order='sequence')

                for group in groups:
                    filter_groups.append({
                        'id': group.id,
                        'name': group.name,
                        'property_type': group.property_type,
                        'characteristics': [{
                            'id': c.id,
                            'name': c.name,
                            'field_name': c.field_name,
                            'field_type': c.field_type,
                            'icon': c.icon,
                        } for c in group.characteristic_ids]
                    })

            return {
                'success': True,
                'filters_by_category': filters_by_category,
                'filter_groups': filter_groups,
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/property/filters/ranges', type='json', auth='public', methods=['POST'], csrf=False)
    def get_filter_ranges(self, **kwargs):
        """
        Retorna rangos disponibles para filtros (precio, área, habitaciones, etc.)
        Con contadores de propiedades por rango

        Returns:
            dict: Estructura con rangos y contadores
        """
        try:
            Property = request.env['product.template'].sudo()

            # Contar propiedades por rango de precio
            price_ranges = {}
            for range_value in ['0-50m', '50-100m', '100-200m', '200-300m', '300-500m', '500-1000m', '1000m+']:
                count = Property.search_count([
                    ('price_range', '=', range_value),
                    ('property_type_id', '!=', False),
                    ('state', '=', 'free')  # Solo disponibles
                ])
                price_ranges[range_value] = count

            # Contar propiedades por rango de arriendo
            rental_ranges = {}
            for range_value in ['0-500k', '500k-1m', '1-2m', '2-3m', '3-5m', '5m+']:
                count = Property.search_count([
                    ('rental_price_range', '=', range_value),
                    ('property_type_id', '!=', False),
                    ('state', '=', 'free')
                ])
                rental_ranges[range_value] = count

            # Contar propiedades por habitaciones
            bedroom_ranges = {}
            for range_value in ['studio', '1', '2', '3', '4', '5+']:
                count = Property.search_count([
                    ('bedrooms_range', '=', range_value),
                    ('property_type_id', '!=', False),
                    ('state', '=', 'free')
                ])
                bedroom_ranges[range_value] = count

            # Contar propiedades por baños
            bathroom_ranges = {}
            for range_value in ['1', '2', '3', '4+']:
                count = Property.search_count([
                    ('bathrooms_range', '=', range_value),
                    ('property_type_id', '!=', False),
                    ('state', '=', 'free')
                ])
                bathroom_ranges[range_value] = count

            # Contar propiedades por parqueaderos
            parking_ranges = {}
            for range_value in ['0', '1', '2', '3+']:
                count = Property.search_count([
                    ('parking_range', '=', range_value),
                    ('property_type_id', '!=', False),
                    ('state', '=', 'free')
                ])
                parking_ranges[range_value] = count

            # Contar propiedades por área
            area_ranges = {}
            for range_value in ['0-50', '50-80', '80-120', '120-200', '200-500', '500+']:
                count = Property.search_count([
                    ('area_range', '=', range_value),
                    ('property_type_id', '!=', False),
                    ('state', '=', 'free')
                ])
                area_ranges[range_value] = count

            # Contar propiedades por características agrupadas
            grouped_characteristics = {
                'has_outdoor_areas': Property.search_count([
                    ('has_outdoor_areas', '=', True),
                    ('property_type_id', '!=', False),
                    ('state', '=', 'free')
                ]),
                'has_building_amenities': Property.search_count([
                    ('has_building_amenities', '=', True),
                    ('property_type_id', '!=', False),
                    ('state', '=', 'free')
                ]),
                'has_luxury_amenities': Property.search_count([
                    ('has_luxury_amenities', '=', True),
                    ('property_type_id', '!=', False),
                    ('state', '=', 'free')
                ]),
                'has_full_security': Property.search_count([
                    ('has_full_security', '=', True),
                    ('property_type_id', '!=', False),
                    ('state', '=', 'free')
                ]),
            }

            return {
                'success': True,
                'price_ranges': price_ranges,
                'rental_ranges': rental_ranges,
                'bedroom_ranges': bedroom_ranges,
                'bathroom_ranges': bathroom_ranges,
                'parking_ranges': parking_ranges,
                'area_ranges': area_ranges,
                'grouped_characteristics': grouped_characteristics,
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    @http.route('/api/property/search/advanced', type='json', auth='public', methods=['POST'], csrf=False)
    def search_properties_advanced(self, filters=None, limit=20, offset=0, order='id desc', **kwargs):
        """
        Búsqueda avanzada de propiedades usando filtros agrupados

        Args:
            filters: Dict con filtros aplicados
            limit: Número de resultados
            offset: Offset para paginación
            order: Ordenamiento

        Returns:
            dict: Propiedades encontradas con metadata
        """
        try:
            Property = request.env['product.template'].sudo()

            # Construir dominio base
            domain = [
                ('property_type_id', '!=', False),
                ('state', '=', 'free')  # Solo disponibles
            ]

            if not filters:
                filters = {}

            # Aplicar filtros de rangos
            if filters.get('price_range'):
                domain.append(('price_range', '=', filters['price_range']))

            if filters.get('rental_price_range'):
                domain.append(('rental_price_range', '=', filters['rental_price_range']))

            if filters.get('bedrooms_range'):
                domain.append(('bedrooms_range', '=', filters['bedrooms_range']))

            if filters.get('bathrooms_range'):
                domain.append(('bathrooms_range', '=', filters['bathrooms_range']))

            if filters.get('parking_range'):
                domain.append(('parking_range', '=', filters['parking_range']))

            if filters.get('area_range'):
                domain.append(('area_range', '=', filters['area_range']))

            # Filtros de tipo
            if filters.get('property_type'):
                domain.append(('property_type', '=', filters['property_type']))

            if filters.get('type_service'):
                domain.append(('type_service', '=', filters['type_service']))

            # Filtros de ubicación
            if filters.get('state_id'):
                domain.append(('state_id', '=', int(filters['state_id'])))

            if filters.get('city'):
                domain.append(('city', 'ilike', filters['city']))

            if filters.get('region_id'):
                domain.append(('region_id', '=', int(filters['region_id'])))

            # Filtros de características agrupadas
            if filters.get('has_outdoor_areas'):
                domain.append(('has_outdoor_areas', '=', True))

            if filters.get('has_building_amenities'):
                domain.append(('has_building_amenities', '=', True))

            if filters.get('has_luxury_amenities'):
                domain.append(('has_luxury_amenities', '=', True))

            if filters.get('has_full_security'):
                domain.append(('has_full_security', '=', True))

            # Filtros booleanos individuales
            boolean_filters = [
                'balcony', 'terrace', 'garden', 'patio', 'pools', 'gym',
                'social_room', 'green_areas', 'elevator', 'furnished',
                'air_conditioning', 'garage', 'security_cameras', 'alarm'
            ]

            for field in boolean_filters:
                if filters.get(field):
                    domain.append((field, '=', True))

            # Contar total
            total = Property.search_count(domain)

            # Buscar propiedades
            properties = Property.search(domain, limit=limit, offset=offset, order=order)

            # Formatear resultados
            results = []
            for prop in properties:
                # Obtener primera imagen
                image_url = f'/web/image/product.template/{prop.id}/image_1920'

                results.append({
                    'id': prop.id,
                    'name': prop.name,
                    'default_code': prop.default_code,
                    'property_type': dict(prop._fields['property_type'].selection).get(prop.property_type) if prop.property_type else '',
                    'type_service': prop.type_service,
                    'state': prop.state,
                    'city': prop.city,
                    'region': prop.region_id.name if prop.region_id else '',
                    'address': prop.street or '',
                    'net_price': prop.net_price,
                    'rental_price': prop.rental_price,
                    'currency': prop.currency_id.symbol or prop.currency_id.name,
                    'property_area': prop.property_area,
                    'unit_of_measure': prop.unit_of_measure,
                    'area_in_m2': prop.area_in_m2,
                    'num_bedrooms': prop.num_bedrooms,
                    'num_bathrooms': prop.num_bathrooms,
                    'stratum': prop.stratum,
                    'image_url': image_url,
                    # Geolocalización
                    'latitude': prop.latitude,
                    'longitude': prop.longitude,
                    # Rangos calculados
                    'price_range': prop.price_range,
                    'bedrooms_range': prop.bedrooms_range,
                    'area_range': prop.area_range,
                    # Características agrupadas
                    'has_outdoor_areas': prop.has_outdoor_areas,
                    'has_building_amenities': prop.has_building_amenities,
                    'has_luxury_amenities': prop.has_luxury_amenities,
                    'has_full_security': prop.has_full_security,
                    # URL de detalle
                    'url': f'/property/{prop.id}'
                })

            return {
                'success': True,
                'properties': results,
                'total': total,
                'limit': limit,
                'offset': offset,
                'page': (offset // limit) + 1 if limit > 0 else 1,
                'total_pages': (total + limit - 1) // limit if limit > 0 else 1,
            }

        except Exception as e:
            import traceback
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }

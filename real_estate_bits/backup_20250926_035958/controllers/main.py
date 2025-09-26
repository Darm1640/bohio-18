# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.osv import expression
from odoo.addons.website_sale.controllers.main import QueryURL, WebsiteSale
import logging

_logger = logging.getLogger(__name__)

# Filtros booleanos (amenidades)
BOOLEAN_FILTERS = [
    'pools', 'gym', 'elevator', 'furnished', 'garden', 'terrace',
    'social_room', 'sauna', 'turkish_bath', 'jacuzzi', 'playground',
    'green_areas', 'sports_area', 'court', 'bar'
]

# Filtros de rango numérico
RANGE_FILTERS = {
    'area': ('property_area', float),
    'bedrooms': ('num_bedrooms', int),
    'bathrooms': ('num_bathrooms', int),
    'floor': ('floor_number', int),
}

class WebsiteSaleRealEstate(WebsiteSale):
    
    def _get_search_options(
        self,
        category=None,
        attrib_values=None,
        tags=None,
        min_price=0.0,
        max_price=0.0,
        conversion_rate=1,
        **post,
    ):
        """
        Extender las opciones de búsqueda para incluir filtros de bienes raíces
        """
        res = super()._get_search_options(
            category=category,
            attrib_values=attrib_values,
            tags=tags,
            min_price=min_price,
            max_price=max_price,
            conversion_rate=conversion_rate,
            **post,
        )

        # Agregar filtros específicos de bienes raíces
        res.update({
            "location": request.context.get("location"),
            "type_service": request.context.get("type_service"),
            "property_type_id": request.context.get("property_type_id"),  # Corregido para Many2one
        })

        # Agregar filtros de rango
        for filter_name, (field_name, field_type) in RANGE_FILTERS.items():
            res[f"{filter_name}_min"] = request.context.get(f"{filter_name}_min")
            res[f"{filter_name}_max"] = request.context.get(f"{filter_name}_max")

        # Agregar filtros booleanos (amenidades)
        for amenity in BOOLEAN_FILTERS:
            res[amenity] = bool(request.context.get(amenity))

        return res

    def _get_shop_domain(self, search, category, attrib_values, search_in_description=True):
        """
        Construir el dominio de búsqueda incluyendo filtros de bienes raíces
        """
        domain = super()._get_shop_domain(search, category, attrib_values, search_in_description)
        
        try:
            # Filtro de ubicación (busca en ciudad, estado y barrio)
            if "location" in request.context and request.context["location"]:
                location_search = request.context["location"].strip()
                if location_search:
                    location_domain = expression.OR([
                        [("city", "ilike", location_search)],
                        [("state_id.name", "ilike", location_search)],
                        [("neighborhood", "ilike", location_search)],
                        [("partner_id.street", "ilike", location_search)],  # Buscar también en dirección
                    ])
                    domain = expression.AND([domain, location_domain])
            
            # Filtro de tipo de servicio (venta/alquiler)
            if "type_service" in request.context and request.context["type_service"]:
                domain = expression.AND([
                    domain, 
                    [("type_service", "=", request.context["type_service"])]
                ])
            
            # CORREGIDO: Filtro de tipo de propiedad (Many2one)
            if "property_type_id" in request.context and request.context["property_type_id"]:
                try:
                    property_type_id = int(request.context["property_type_id"])
                    domain = expression.AND([
                        domain, 
                        [("property_type_id", "=", property_type_id)]
                    ])
                except (ValueError, TypeError):
                    _logger.warning(f"Invalid property_type_id: {request.context['property_type_id']}")

            # Filtros de rango numérico
            for filter_name, (field_name, field_type) in RANGE_FILTERS.items():
                # Filtro mínimo
                min_key = f"{filter_name}_min"
                if min_key in request.context and request.context[min_key]:
                    try:
                        min_value = field_type(request.context[min_key])
                        domain = expression.AND([
                            domain, 
                            [(field_name, ">=", min_value)]
                        ])
                    except (ValueError, TypeError):
                        _logger.warning(f"Invalid {min_key}: {request.context[min_key]}")
                
                # Filtro máximo
                max_key = f"{filter_name}_max"
                if max_key in request.context and request.context[max_key]:
                    try:
                        max_value = field_type(request.context[max_key])
                        domain = expression.AND([
                            domain, 
                            [(field_name, "<=", max_value)]
                        ])
                    except (ValueError, TypeError):
                        _logger.warning(f"Invalid {max_key}: {request.context[max_key]}")

            # Filtros booleanos (amenidades)
            for bool_filter in BOOLEAN_FILTERS:
                if bool_filter in request.context and request.context[bool_filter]:
                    domain = expression.AND([
                        domain, 
                        [(bool_filter, "=", True)]
                    ])

        except Exception as e:
            _logger.error(f"Error building shop domain: {e}")
            # En caso de error, devolver el dominio base sin filtros adicionales

        return domain

    def _get_property_types(self):
        """
        Obtener tipos de propiedad disponibles para el formulario
        """
        try:
            PropertyType = request.env['property.type']
            return PropertyType.search([('active', '=', True)], order='name')
        except Exception as e:
            _logger.error(f"Error fetching property types: {e}")
            return request.env['property.type']

    def _get_filter_options(self):
        """
        Obtener opciones para filtros select
        """
        return {
            'property_types': self._get_property_types(),
            'type_services': [
                ('sale', 'Venta'),
                ('rent', 'Alquiler'),
                ('both', 'Venta y Alquiler'),
            ],
            'boolean_filters': BOOLEAN_FILTERS,
            'range_filters': list(RANGE_FILTERS.keys()),
        }

    @http.route([
        "/shop",
        "/shop/page/<int:page>",
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>',
    ], type="http", auth="public", website=True)
    def shop(
        self,
        page=0,
        category=None,
        search="",
        min_price=0.0,
        max_price=0.0,
        ppg=False,
        **post,
    ):
        """
        Página principal de la tienda con filtros de bienes raíces
        """
        # Obtener contexto actual
        ctx = dict(request.context)

        try:
            # Filtros simples (texto y selección)
            SIMPLE_FILTERS = [
                'location', 'type_service', 'property_type_id'
            ]
            
            for f in SIMPLE_FILTERS:
                if f in post and post.get(f):
                    ctx[f] = post.get(f).strip() if isinstance(post.get(f), str) else post.get(f)

            # Filtros de rango numérico
            for filter_name in RANGE_FILTERS.keys():
                for suffix in ['_min', '_max']:
                    key = f"{filter_name}{suffix}"
                    if key in post and post.get(key):
                        try:
                            # Limpiar valor (remover espacios y caracteres especiales)
                            value = str(post.get(key)).strip().replace(',', '')
                            if value and value != '0':
                                ctx[key] = value
                        except (ValueError, TypeError):
                            pass

            # Filtros booleanos (amenidades)
            for amenity in BOOLEAN_FILTERS:
                if amenity in post:
                    # Convertir a booleano de manera segura
                    value = str(post.get(amenity)).lower()
                    ctx[amenity] = value not in ['false', '0', 'off', '', 'none', 'null']
                else:
                    # Si no está en post, remover del contexto para que no persista
                    ctx.pop(amenity, None)

            # Actualizar el contexto de la petición
            request.update_context(**ctx)

        except Exception as e:
            _logger.error(f"Error processing shop filters: {e}")
            # Continuar sin filtros en caso de error

        # Llamar al método padre
        response = super(WebsiteSaleRealEstate, self).shop(
            page=page,
            category=category,
            search=search,
            min_price=min_price,
            max_price=max_price,
            ppg=ppg,
            **post,
        )

        # Agregar opciones de filtros al contexto de la respuesta
        if hasattr(response, 'qcontext'):
            response.qcontext.update({
                'filter_options': self._get_filter_options(),
                'current_filters': {
                    'location': ctx.get('location', ''),
                    'type_service': ctx.get('type_service', ''),
                    'property_type_id': ctx.get('property_type_id', ''),
                    **{f: ctx.get(f, '') for f in [f"{name}_{suffix}" 
                                                  for name in RANGE_FILTERS.keys() 
                                                  for suffix in ['min', 'max']]},
                    **{amenity: ctx.get(amenity, False) for amenity in BOOLEAN_FILTERS}
                },
                'active_filters_count': self._count_active_filters(ctx),
            })

        return response

    def _count_active_filters(self, ctx):
        """
        Contar filtros activos para mostrar en la UI
        """
        count = 0
        
        # Filtros de texto
        text_filters = ['location', 'type_service', 'property_type_id']
        for f in text_filters:
            if ctx.get(f):
                count += 1
        
        # Filtros de rango
        for filter_name in RANGE_FILTERS.keys():
            if ctx.get(f"{filter_name}_min") or ctx.get(f"{filter_name}_max"):
                count += 1
        
        # Filtros booleanos
        for amenity in BOOLEAN_FILTERS:
            if ctx.get(amenity):
                count += 1
        
        return count

    @http.route('/shop/filters/clear', type='http', auth='public', website=True)
    def clear_filters(self, **post):
        """
        Limpiar todos los filtros y redirigir a la tienda
        """
        return request.redirect('/shop')

    @http.route('/shop/get_property_types', type='json', auth='public', website=True)
    def get_property_types_ajax(self):
        """
        Endpoint AJAX para obtener tipos de propiedad
        """
        try:
            property_types = self._get_property_types()
            return {
                'success': True,
                'data': [{'id': pt.id, 'name': pt.name} for pt in property_types]
            }
        except Exception as e:
            _logger.error(f"Error in get_property_types_ajax: {e}")
            return {
                'success': False,
                'error': 'Error loading property types'
            }
# -*- coding: utf-8 -*-
"""
PROPERTY BANNER SNIPPET - Controladores optimizados con search_read
Sistema de snippet editable para Website Builder similar a theme_snazzy
"""

from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class PropertyBannerController(http.Controller):
    """
    Controlador para Property Banner Snippet
    Endpoints optimizados con search_read para máxima performance
    """

    @http.route(['/bohio/property_banner/select_list'], type='json', auth='public', website=True)
    def bohio_property_select_list(self, **kwargs):
        """
        Retorna lista de propiedades disponibles para seleccionar en el snippet.
        OPTIMIZADO: Usa search_read en lugar de search + acceso a campos
        """
        try:
            Property = request.env['product.template'].sudo()

            # Buscar propiedades activas y disponibles
            domain = [
                ('is_property', '=', True),
                ('active', '=', True),
                ('state', 'in', ['free', 'reserved']),
            ]

            # OPTIMIZACIÓN: search_read carga solo los campos necesarios en 1 query
            properties = Property.search_read(
                domain,
                fields=['id', 'name', 'default_code', 'city_id'],
                order='name asc',
                limit=100
            )

            # Formato para el select dropdown
            result = []
            for prop in properties:
                # Información básica para mostrar en el selector
                label = prop['name']
                if prop.get('default_code'):
                    label = f"[{prop['default_code']}] {label}"
                if prop.get('city_id'):
                    # city_id viene como tupla (id, name) en search_read
                    city_name = prop['city_id'][1] if isinstance(prop['city_id'], (list, tuple)) else ''
                    if city_name:
                        label = f"{label} - {city_name}"

                result.append({
                    'id': prop['id'],
                    'name': label,
                })

            _logger.info(f"[PROPERTY BANNER] Lista de propiedades: {len(result)} encontradas")
            return result

        except Exception as e:
            _logger.error(f"[PROPERTY BANNER] Error en select_list: {str(e)}")
            return []

    @http.route(['/bohio/property_banner/details_js'], type='json', auth='public', website=True)
    def bohio_property_banner_details_js(self, **post):
        """
        Retorna datos básicos de la propiedad para modo de edición (preview).
        OPTIMIZADO: Usa search_read para cargar campos en 1 query
        """
        try:
            property_id = int(post.get('property_id', 0))
            if not property_id:
                return {}

            Property = request.env['product.template'].sudo()

            # OPTIMIZACIÓN: search_read carga solo campos necesarios
            properties = Property.search_read(
                [('id', '=', property_id)],
                fields=['id', 'name', 'description_sale', 'default_code', 'city_id', 'region_id'],
                limit=1
            )

            if not properties:
                return {}

            prop = properties[0]

            values = {
                'property_id': prop['id'],
                'property_name': prop['name'],
                'property_description': prop.get('description_sale') or 'No description available',
                'property_code': prop.get('default_code') or '',
                'city': prop['city_id'][1] if prop.get('city_id') else '',
                'region': prop['region_id'][1] if prop.get('region_id') else '',
            }

            _logger.info(f"[PROPERTY BANNER] Detalles JS: Propiedad {property_id} - {prop['name']}")
            return values

        except Exception as e:
            _logger.error(f"[PROPERTY BANNER] Error en details_js: {str(e)}")
            return {}

    @http.route(['/bohio/property_banner/details_xml'], type='http', auth='public', website=True, sitemap=False)
    def bohio_property_banner_details_xml(self, **post):
        """
        Renderiza el template completo con datos de la propiedad para modo público.

        NOTA: Este endpoint usa browse() normal porque necesita renderizar un template QWeb
        que accede a campos relacionados (city_id.name, project_worksite_id.name, etc.)
        El template espera objetos de modelo, no diccionarios.
        """
        try:
            property_id = post.get('property_id')

            if not property_id:
                return ''

            property_obj = request.env['product.template'].sudo().browse(int(property_id))

            if not property_obj.exists():
                return ''

            values = {
                'property': property_obj,
                'add_qty': 1,
            }

            _logger.info(f"[PROPERTY BANNER] Detalles XML: Renderizando propiedad {property_id} - {property_obj.name}")
            return request.render("theme_bohio_real_estate.property_banner_dynamic_data", values)

        except Exception as e:
            _logger.error(f"[PROPERTY BANNER] Error en details_xml: {str(e)}")
            return ''

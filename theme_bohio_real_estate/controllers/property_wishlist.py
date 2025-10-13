# -*- coding: utf-8 -*-
"""
BOHIO Real Estate - Property Wishlist Controller
================================================
Controlador para manejar favoritos/wishlist de propiedades.
Extiende la funcionalidad de website_sale_wishlist para propiedades inmobiliarias.

Autor: BOHIO Inmobiliaria
Fecha: 2025
"""

from odoo import http, _
from odoo.http import request
from odoo.addons.website_sale_wishlist.controllers.main import WebsiteSaleWishlist
import logging

_logger = logging.getLogger(__name__)


class BohioPropertyWishlist(WebsiteSaleWishlist):
    """
    Controlador extendido para wishlist de propiedades.
    Compatible con product.wishlist de Odoo pero adaptado para real estate.
    """

    @http.route('/property/wishlist/add', type='json', auth='public', website=True, csrf=False)
    def add_property_to_wishlist(self, property_id, **kw):
        """
        Agregar una propiedad al wishlist.

        Args:
            property_id (int): ID de la propiedad (product.template)
            **kw: Argumentos adicionales

        Returns:
            dict: {
                'success': bool,
                'message': str,
                'new_count': int,
                'is_in_wishlist': bool
            }
        """
        try:
            # Validar que la propiedad existe
            property_rec = request.env['product.template'].sudo().browse(int(property_id))

            if not property_rec.exists():
                return {
                    'success': False,
                    'message': _('Propiedad no encontrada'),
                    'new_count': 0,
                    'is_in_wishlist': False
                }

            # Verificar si ya está en el wishlist
            wishlist = request.env['product.wishlist'].sudo()
            existing = wishlist.search([
                ('product_id', '=', property_rec.product_variant_id.id),
                '|',
                ('partner_id', '=', request.env.user.partner_id.id if request.env.user != request.env.ref('base.public_user') else False),
                ('session_id', '=', request.session.sid if request.env.user == request.env.ref('base.public_user') else False)
            ], limit=1)

            if existing:
                return {
                    'success': True,
                    'message': _('Esta propiedad ya está en tus favoritos'),
                    'new_count': len(wishlist.current()),
                    'is_in_wishlist': True
                }

            # Usar el método padre para agregar
            result = super(BohioPropertyWishlist, self).add_to_wishlist(
                product_id=property_rec.product_variant_id.id,
                **kw
            )

            # Obtener contador actualizado
            new_count = len(wishlist.current())

            _logger.info(f'✅ Propiedad {property_id} agregada al wishlist. Total: {new_count}')

            return {
                'success': True,
                'message': _('Propiedad agregada a favoritos'),
                'new_count': new_count,
                'is_in_wishlist': True
            }

        except Exception as e:
            _logger.error(f'❌ Error agregando propiedad {property_id} al wishlist: {e}')
            return {
                'success': False,
                'message': _('Error al agregar a favoritos'),
                'new_count': 0,
                'is_in_wishlist': False
            }

    @http.route('/property/wishlist/remove', type='json', auth='public', website=True, csrf=False)
    def remove_property_from_wishlist(self, property_id, **kw):
        """
        Remover una propiedad del wishlist.

        Args:
            property_id (int): ID de la propiedad (product.template)

        Returns:
            dict: {
                'success': bool,
                'message': str,
                'new_count': int,
                'is_in_wishlist': bool
            }
        """
        try:
            property_rec = request.env['product.template'].sudo().browse(int(property_id))

            if not property_rec.exists():
                return {
                    'success': False,
                    'message': _('Propiedad no encontrada'),
                    'new_count': 0,
                    'is_in_wishlist': False
                }

            # Buscar en el wishlist
            wishlist = request.env['product.wishlist'].sudo()
            wish_item = wishlist.search([
                ('product_id', '=', property_rec.product_variant_id.id),
                '|',
                ('partner_id', '=', request.env.user.partner_id.id if request.env.user != request.env.ref('base.public_user') else False),
                ('session_id', '=', request.session.sid if request.env.user == request.env.ref('base.public_user') else False)
            ], limit=1)

            if wish_item:
                wish_item.unlink()
                new_count = len(wishlist.current())

                _logger.info(f'✅ Propiedad {property_id} removida del wishlist. Total: {new_count}')

                return {
                    'success': True,
                    'message': _('Propiedad removida de favoritos'),
                    'new_count': new_count,
                    'is_in_wishlist': False
                }
            else:
                return {
                    'success': True,
                    'message': _('La propiedad no estaba en favoritos'),
                    'new_count': len(wishlist.current()),
                    'is_in_wishlist': False
                }

        except Exception as e:
            _logger.error(f'❌ Error removiendo propiedad {property_id} del wishlist: {e}')
            return {
                'success': False,
                'message': _('Error al remover de favoritos'),
                'new_count': 0,
                'is_in_wishlist': False
            }

    @http.route('/property/wishlist/toggle', type='json', auth='public', website=True, csrf=False)
    def toggle_property_wishlist(self, property_id, **kw):
        """
        Toggle (agregar/remover) una propiedad del wishlist.
        Método más conveniente que combina add y remove.

        Args:
            property_id (int): ID de la propiedad (product.template)

        Returns:
            dict: {
                'success': bool,
                'message': str,
                'new_count': int,
                'is_in_wishlist': bool,
                'action': str  # 'added' o 'removed'
            }
        """
        try:
            property_rec = request.env['product.template'].sudo().browse(int(property_id))

            if not property_rec.exists():
                return {
                    'success': False,
                    'message': _('Propiedad no encontrada'),
                    'new_count': 0,
                    'is_in_wishlist': False,
                    'action': 'error'
                }

            # Verificar si ya está en wishlist
            wishlist = request.env['product.wishlist'].sudo()
            wish_item = wishlist.search([
                ('product_id', '=', property_rec.product_variant_id.id),
                '|',
                ('partner_id', '=', request.env.user.partner_id.id if request.env.user != request.env.ref('base.public_user') else False),
                ('session_id', '=', request.session.sid if request.env.user == request.env.ref('base.public_user') else False)
            ], limit=1)

            if wish_item:
                # Ya está en wishlist, remover
                wish_item.unlink()
                new_count = len(wishlist.current())

                _logger.info(f'🔄 Propiedad {property_id} removida del wishlist (toggle). Total: {new_count}')

                return {
                    'success': True,
                    'message': _('Propiedad removida de favoritos'),
                    'new_count': new_count,
                    'is_in_wishlist': False,
                    'action': 'removed'
                }
            else:
                # No está en wishlist, agregar
                result = super(BohioPropertyWishlist, self).add_to_wishlist(
                    product_id=property_rec.product_variant_id.id,
                    **kw
                )

                new_count = len(wishlist.current())

                _logger.info(f'🔄 Propiedad {property_id} agregada al wishlist (toggle). Total: {new_count}')

                return {
                    'success': True,
                    'message': _('Propiedad agregada a favoritos'),
                    'new_count': new_count,
                    'is_in_wishlist': True,
                    'action': 'added'
                }

        except Exception as e:
            _logger.error(f'❌ Error en toggle wishlist para propiedad {property_id}: {e}')
            return {
                'success': False,
                'message': _('Error al actualizar favoritos'),
                'new_count': 0,
                'is_in_wishlist': False,
                'action': 'error'
            }

    @http.route('/property/wishlist/check', type='json', auth='public', website=True, csrf=False)
    def check_property_in_wishlist(self, property_id, **kw):
        """
        Verificar si una propiedad está en el wishlist.

        Args:
            property_id (int): ID de la propiedad (product.template)

        Returns:
            dict: {
                'is_in_wishlist': bool,
                'total_count': int
            }
        """
        try:
            property_rec = request.env['product.template'].sudo().browse(int(property_id))

            if not property_rec.exists():
                return {
                    'is_in_wishlist': False,
                    'total_count': 0
                }

            wishlist = request.env['product.wishlist'].sudo()
            wish_item = wishlist.search([
                ('product_id', '=', property_rec.product_variant_id.id),
                '|',
                ('partner_id', '=', request.env.user.partner_id.id if request.env.user != request.env.ref('base.public_user') else False),
                ('session_id', '=', request.session.sid if request.env.user == request.env.ref('base.public_user') else False)
            ], limit=1)

            return {
                'is_in_wishlist': bool(wish_item),
                'total_count': len(wishlist.current())
            }

        except Exception as e:
            _logger.error(f'❌ Error verificando wishlist para propiedad {property_id}: {e}')
            return {
                'is_in_wishlist': False,
                'total_count': 0
            }

    @http.route('/property/wishlist/count', type='json', auth='public', website=True, csrf=False)
    def get_wishlist_count(self, **kw):
        """
        Obtener el contador total del wishlist.

        Returns:
            dict: {
                'count': int
            }
        """
        try:
            wishlist = request.env['product.wishlist'].sudo()
            count = len(wishlist.current())

            return {
                'count': count
            }

        except Exception as e:
            _logger.error(f'❌ Error obteniendo contador de wishlist: {e}')
            return {
                'count': 0
            }

    @http.route('/property/wishlist/list', type='json', auth='public', website=True, csrf=False)
    def get_wishlist_properties(self, **kw):
        """
        Obtener lista de propiedades en el wishlist.

        Returns:
            dict: {
                'properties': [{id, name, code, price, image_url, ...}],
                'count': int
            }
        """
        try:
            wishlist = request.env['product.wishlist'].sudo().current()
            website = request.env['website'].get_current_website()

            properties_data = []

            for wish in wishlist:
                prop = wish.product_id.product_tmpl_id

                # Solo incluir propiedades (is_property = True)
                if not prop.is_property:
                    continue

                # Obtener imagen optimizada
                image_url = website.image_url(prop, 'image_512') if prop.image_512 else '/theme_bohio_real_estate/static/src/img/placeholder.jpg'

                # Determinar precio según tipo
                price = 0
                if prop.type_service in ['rent', 'Arriendo']:
                    price = prop.net_rental_price or 0
                else:
                    price = prop.net_price or 0

                properties_data.append({
                    'id': prop.id,
                    'name': prop.name,
                    'code': prop.default_code or '',
                    'property_type': prop.property_type or '',
                    'type_service': prop.type_service or '',
                    'price': price,
                    'area': prop.property_area or 0,
                    'bedrooms': prop.num_bedrooms or 0,
                    'bathrooms': prop.num_bathrooms or 0,
                    'city': prop.city or '',
                    'image_url': image_url,
                    'url': f'/property/{prop.id}'
                })

            _logger.info(f'📋 Lista de wishlist: {len(properties_data)} propiedades')

            return {
                'properties': properties_data,
                'count': len(properties_data)
            }

        except Exception as e:
            _logger.error(f'❌ Error obteniendo lista de wishlist: {e}')
            return {
                'properties': [],
                'count': 0
            }

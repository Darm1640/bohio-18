# -*- coding: utf-8 -*-
"""
BOHIO Real Estate - Property Interactions Controller
====================================================
Controlador consolidado para interacciones del usuario con propiedades:
- Wishlist/Favoritos
- Mapas individuales de propiedades
- Direcciones y navegación

Autor: BOHIO Inmobiliaria
Fecha: 2025
"""

from odoo import http, _
from odoo.http import request
from odoo.addons.website_sale_wishlist.controllers.main import WebsiteSaleWishlist
import logging

_logger = logging.getLogger(__name__)


class BohioPropertyInteractions(WebsiteSaleWishlist):
    """
    Controlador consolidado para interacciones del usuario.

    FUSIONA:
    - property_wishlist.py: Wishlist/favoritos (6 rutas)
    - property_map_controller.py: Mapas individuales (2 rutas)
    - Reportes de problemas (1 ruta)

    Total: 9 rutas
    """

    # ========================================================================
    # SECCIÓN 1: WISHLIST / FAVORITOS
    # ========================================================================

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

            # Construir dominio según usuario autenticado o público
            if request.env.user != request.env.ref('base.public_user'):
                # Usuario autenticado
                domain = [
                    ('product_id', '=', property_rec.product_variant_id.id),
                    ('partner_id', '=', request.env.user.partner_id.id)
                ]
            else:
                # Usuario público (usar sesión)
                domain = [
                    ('product_id', '=', property_rec.product_variant_id.id),
                    ('session_id', '=', request.session.sid)
                ]

            existing = wishlist.search(domain, limit=1)

            if existing:
                return {
                    'success': True,
                    'message': _('Esta propiedad ya está en tus favoritos'),
                    'new_count': len(wishlist.current()),
                    'is_in_wishlist': True
                }

            # Usar el método padre para agregar
            result = super(BohioPropertyInteractions, self).add_to_wishlist(
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

            # Construir dominio según usuario autenticado o público
            if request.env.user != request.env.ref('base.public_user'):
                domain = [
                    ('product_id', '=', property_rec.product_variant_id.id),
                    ('partner_id', '=', request.env.user.partner_id.id)
                ]
            else:
                domain = [
                    ('product_id', '=', property_rec.product_variant_id.id),
                    ('session_id', '=', request.session.sid)
                ]

            wish_item = wishlist.search(domain, limit=1)

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

            # Construir dominio según usuario autenticado o público
            if request.env.user != request.env.ref('base.public_user'):
                domain = [
                    ('product_id', '=', property_rec.product_variant_id.id),
                    ('partner_id', '=', request.env.user.partner_id.id)
                ]
            else:
                domain = [
                    ('product_id', '=', property_rec.product_variant_id.id),
                    ('session_id', '=', request.session.sid)
                ]

            wish_item = wishlist.search(domain, limit=1)

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
                result = super(BohioPropertyInteractions, self).add_to_wishlist(
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

            # Construir dominio según usuario autenticado o público
            if request.env.user != request.env.ref('base.public_user'):
                domain = [
                    ('product_id', '=', property_rec.product_variant_id.id),
                    ('partner_id', '=', request.env.user.partner_id.id)
                ]
            else:
                domain = [
                    ('product_id', '=', property_rec.product_variant_id.id),
                    ('session_id', '=', request.session.sid)
                ]

            wish_item = wishlist.search(domain, limit=1)

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

    # ========================================================================
    # SECCIÓN 2: MAPAS INDIVIDUALES DE PROPIEDADES
    # Fusionados desde property_map_controller.py
    # ========================================================================

    @http.route('/property/<int:property_id>/map', type='http', auth='public', website=True)
    def property_map_fullpage(self, property_id, **kwargs):
        """
        Página dedicada para mostrar el mapa de una propiedad

        Args:
            property_id: ID de la propiedad (product.template)

        Returns:
            Renderiza el template property_map_fullpage
        """
        # Buscar la propiedad
        property_obj = request.env['product.template'].sudo().browse(property_id)

        # Verificar que existe y es una propiedad
        if not property_obj.exists() or not property_obj.is_property:
            return request.not_found()

        # Verificar que tiene coordenadas
        if not property_obj.latitude or not property_obj.longitude:
            return request.render('theme_bohio_real_estate.property_map_no_coordinates', {
                'property': property_obj
            })

        # Renderizar template del mapa
        return request.render('theme_bohio_real_estate.property_map_fullpage', {
            'property': property_obj
        })

    @http.route('/property/<int:property_id>/directions', type='http', auth='public', website=True)
    def property_directions(self, property_id, **kwargs):
        """
        Redirige a Google Maps con direcciones hacia la propiedad

        Args:
            property_id: ID de la propiedad

        Returns:
            Redirección a Google Maps
        """
        property_obj = request.env['product.template'].sudo().browse(property_id)

        if not property_obj.exists() or not property_obj.latitude or not property_obj.longitude:
            return request.not_found()

        # URL de Google Maps con direcciones
        google_maps_url = f"https://www.google.com/maps/dir/?api=1&destination={property_obj.latitude},{property_obj.longitude}"

        return request.redirect(google_maps_url)

    # ========================================================================
    # SECCIÓN 3: REPORTES DE PROBLEMAS CON PROPIEDADES
    # ========================================================================

    @http.route('/property/report', type='json', auth='public', website=True, csrf=False)
    def property_report(self, **post):
        """
        Recibir reportes de problemas con propiedades y crear tickets de helpdesk.

        Datos esperados en POST:
            - property_id: ID de la propiedad
            - property_name: Nombre de la propiedad
            - property_code: Código de la propiedad
            - property_url: URL de la propiedad
            - problem_type: Tipo de problema
            - reporter_name: Nombre del reportante
            - reporter_email: Email del reportante
            - description: Descripción del problema

        Returns:
            dict: {'success': bool, 'message': str, 'ticket_id': int}
        """
        try:
            # Validar datos requeridos
            required_fields = ['property_id', 'problem_type', 'reporter_email', 'description']
            for field in required_fields:
                if not post.get(field):
                    return {
                        'success': False,
                        'message': f'Campo requerido faltante: {field}'
                    }

            # Obtener o crear el partner del reportante
            reporter_email = post.get('reporter_email')
            reporter_name = post.get('reporter_name', 'Usuario Web')

            partner = request.env['res.partner'].sudo().search([
                ('email', '=', reporter_email)
            ], limit=1)

            if not partner:
                # Crear partner temporal para el reportante
                partner = request.env['res.partner'].sudo().create({
                    'name': reporter_name,
                    'email': reporter_email,
                    'is_company': False,
                })

            # Obtener la propiedad
            property_id = int(post.get('property_id'))
            property_obj = request.env['product.template'].sudo().browse(property_id)

            if not property_obj.exists():
                return {
                    'success': False,
                    'message': 'Propiedad no encontrada'
                }

            # Mapear tipos de problemas a etiquetas legibles
            problem_types = {
                'incorrect_info': 'Información Incorrecta',
                'outdated': 'Información Desactualizada',
                'unavailable': 'Propiedad No Disponible',
                'photos': 'Problema con Fotos',
                'price': 'Problema con Precio',
                'location': 'Ubicación Incorrecta',
                'other': 'Otro Problema'
            }

            problem_type_label = problem_types.get(
                post.get('problem_type'),
                'Problema General'
            )

            # Buscar equipo de helpdesk
            helpdesk_team = request.env['helpdesk.team'].sudo().search([], limit=1)

            # Crear ticket de helpdesk
            ticket_vals = {
                'name': f'[Reporte Web] {problem_type_label} - {property_obj.name}',
                'partner_id': partner.id,
                'partner_email': reporter_email,
                'team_id': helpdesk_team.id if helpdesk_team else False,
                'description': f"""
REPORTE DE PROBLEMA CON PROPIEDAD
=================================

Propiedad: {post.get('property_name', property_obj.name)}
Código: {post.get('property_code', property_obj.default_code or 'N/A')}
URL: {post.get('property_url', '')}

Tipo de Problema: {problem_type_label}

Reportado por: {reporter_name} ({reporter_email})

Descripción:
{post.get('description', '')}
                """.strip(),
                'priority': '2',  # Media prioridad
            }

            ticket = request.env['helpdesk.ticket'].sudo().create(ticket_vals)

            # Vincular la propiedad al ticket usando message_post
            if property_obj:
                ticket.message_post(
                    body=f'Propiedad reportada: <a href="/property/{property_obj.id}">{property_obj.name}</a>',
                    message_type='notification'
                )

            _logger.info(
                f'✅ Reporte creado: Ticket #{ticket.id} para propiedad {property_id} '
                f'por {reporter_email}'
            )

            return {
                'success': True,
                'message': 'Reporte enviado exitosamente. Gracias por ayudarnos a mejorar.',
                'ticket_id': ticket.id
            }

        except Exception as e:
            _logger.error(f'❌ Error creando reporte de propiedad: {e}', exc_info=True)
            return {
                'success': False,
                'message': 'Error al enviar el reporte. Por favor intenta de nuevo.'
            }

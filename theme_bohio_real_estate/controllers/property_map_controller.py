# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class PropertyMapController(http.Controller):
    
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

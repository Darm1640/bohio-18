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

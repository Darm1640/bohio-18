# -*- coding: utf-8 -*-
# Part of Bohio Real Estate. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.osv import expression


class WebsiteSnippetFilter(models.Model):
    """
    Extiende website.snippet.filter para soportar filtros dinámicos de propiedades.

    Basado en website_sale.WebsiteSnippetFilter pero adaptado para product.template
    (propiedades) en lugar de product.product.
    """
    _inherit = 'website.snippet.filter'

    def _prepare_values(self, limit=None, **kwargs):
        """Override para manejar propiedades (product.template)"""
        website = self.env['website'].get_current_website()

        # Si es un filtro de propiedades, procesar especialmente
        if self.model_name == 'product.template':
            search_domain = kwargs.get('search_domain', [])

            # Asegurar que solo sean propiedades
            if ('is_property', '=', True) not in search_domain:
                search_domain.append(('is_property', '=', True))

            kwargs['search_domain'] = search_domain

        return super()._prepare_values(limit=limit, **kwargs)

    def _filter_records_to_values(self, records, is_sample=False):
        """Override para agregar información específica de propiedades"""
        res_properties = super()._filter_records_to_values(records, is_sample)

        if self.model_name == 'product.template' and not is_sample:
            for res_property in res_properties:
                property_obj = res_property.get('_record')

                if property_obj and hasattr(property_obj, 'is_property') and property_obj.is_property:
                    # Agregar información específica de propiedades
                    res_property.update({
                        'property_type_label': dict(property_obj._fields['property_type'].selection).get(
                            property_obj.property_type, ''
                        ) if property_obj.property_type else '',
                        'type_service_label': dict(property_obj._fields['type_service'].selection).get(
                            property_obj.type_service, ''
                        ) if property_obj.type_service else '',
                        'has_project': bool(property_obj.project_worksite_id),
                        'project_name': property_obj.project_worksite_id.name if property_obj.project_worksite_id else '',
                        # Ubicación
                        'city_name': property_obj.city_id.name if property_obj.city_id else '',
                        'region_name': property_obj.region_id.name if property_obj.region_id else '',
                        'state_name': property_obj.state_id.name if property_obj.state_id else '',
                        # Características principales
                        'bedrooms': property_obj.bedrooms or 0,
                        'bathrooms': property_obj.bathrooms or 0,
                        'garages': property_obj.garages or 0,
                        'area': property_obj.area or 0.0,
                        # Precios
                        'list_price_formatted': property_obj.list_price,
                        'currency_name': property_obj.currency_id.name if property_obj.currency_id else 'COP',
                    })

        return res_properties

    @api.model
    def _get_properties(self, mode, **kwargs):
        """
        Método principal para obtener propiedades dinámicamente.
        Similar a _get_products pero para propiedades.

        Modos disponibles:
        - rent: Propiedades en arriendo
        - sale_used: Propiedades usadas en venta
        - projects: Propiedades de proyectos
        - featured: Propiedades destacadas
        - latest: Últimas propiedades agregadas
        """
        dynamic_filter = self.env.context.get('dynamic_filter')
        handler = getattr(self, f'_get_properties_{mode}', self._get_properties_latest)

        website = self.env['website'].get_current_website()
        search_domain = self.env.context.get('search_domain', [])
        limit = self.env.context.get('limit', 12)

        # Dominio base para propiedades
        domain = expression.AND([
            [('is_property', '=', True)],
            [('active', '=', True)],
            [('state', '=', 'free')],  # Solo propiedades libres
            website.website_domain(),
            search_domain,
        ])

        properties = handler(website, limit, domain, **kwargs)

        return dynamic_filter._filter_records_to_values(properties, is_sample=False)

    def _get_properties_rent(self, website, limit, domain, **kwargs):
        """Obtener propiedades en arriendo"""
        domain = expression.AND([
            domain,
            [('type_service', 'in', ['rent', 'sale_rent'])],
        ])

        return self.env['product.template'].search(
            domain,
            limit=limit,
            order='create_date DESC'
        )

    def _get_properties_sale_used(self, website, limit, domain, **kwargs):
        """Obtener propiedades usadas en venta (sin proyecto)"""
        domain = expression.AND([
            domain,
            [('type_service', 'in', ['sale', 'sale_rent'])],
            [('project_worksite_id', '=', False)],  # Sin proyecto = usada
        ])

        return self.env['product.template'].search(
            domain,
            limit=limit,
            order='create_date DESC'
        )

    def _get_properties_projects(self, website, limit, domain, **kwargs):
        """Obtener propiedades de proyectos (en venta con proyecto)"""
        domain = expression.AND([
            domain,
            [('type_service', 'in', ['sale', 'sale_rent'])],
            [('project_worksite_id', '!=', False)],  # Con proyecto = nueva
        ])

        return self.env['product.template'].search(
            domain,
            limit=limit,
            order='project_worksite_id, create_date DESC'
        )

    def _get_properties_featured(self, website, limit, domain, **kwargs):
        """Obtener propiedades destacadas"""
        # Asumiendo que tienes un campo 'is_featured' o similar
        # Si no, puedes usar otro criterio
        domain = expression.AND([
            domain,
            # [('is_featured', '=', True)],  # Descomentar si tienes este campo
        ])

        return self.env['product.template'].search(
            domain,
            limit=limit,
            order='create_date DESC'
        )

    def _get_properties_latest(self, website, limit, domain, **kwargs):
        """Obtener últimas propiedades agregadas"""
        return self.env['product.template'].search(
            domain,
            limit=limit,
            order='create_date DESC'
        )

    def _get_properties_by_type(self, website, limit, domain, property_type=None, **kwargs):
        """Obtener propiedades por tipo (apartment, house, office, etc.)"""
        if property_type:
            domain = expression.AND([
                domain,
                [('property_type', '=', property_type)],
            ])

        return self.env['product.template'].search(
            domain,
            limit=limit,
            order='create_date DESC'
        )

    def _get_properties_by_city(self, website, limit, domain, city_id=None, **kwargs):
        """Obtener propiedades por ciudad"""
        if city_id:
            domain = expression.AND([
                domain,
                [('city_id', '=', int(city_id))],
            ])

        return self.env['product.template'].search(
            domain,
            limit=limit,
            order='create_date DESC'
        )

    def _get_properties_by_region(self, website, limit, domain, region_id=None, **kwargs):
        """Obtener propiedades por región/barrio"""
        if region_id:
            domain = expression.AND([
                domain,
                [('region_id', '=', int(region_id))],
            ])

        return self.env['product.template'].search(
            domain,
            limit=limit,
            order='create_date DESC'
        )

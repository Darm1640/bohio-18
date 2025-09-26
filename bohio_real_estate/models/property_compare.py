from odoo import models, fields, api


class PropertyCompare(models.TransientModel):
    _name = 'property.compare'
    _description = 'Comparador de Propiedades'

    property_ids = fields.Many2many(
        'product.template',
        string='Propiedades a Comparar',
        domain=[('is_property', '=', True)]
    )

    @api.model
    def get_comparison_data(self, property_ids):
        """Obtener datos estructurados para comparación"""
        properties = self.env['product.template'].browse(property_ids)

        comparison_data = {
            'properties': [],
            'features': {
                'basic': ['default_code', 'type_service', 'property_type', 'state'],
                'location': ['address', 'city', 'neighborhood', 'stratum'],
                'characteristics': ['property_area', 'num_bedrooms', 'num_bathrooms', 'n_garage', 'property_age'],
                'amenities': ['pool', 'gym', 'garden', 'terrace', 'air_conditioning'],
                'prices': ['list_price', 'administration_fee']
            }
        }

        for prop in properties:
            prop_data = {
                'id': prop.id,
                'name': prop.name,
                'image': prop.image_1920,
                'data': {}
            }

            # Recopilar todos los datos
            for category, fields_list in comparison_data['features'].items():
                for field in fields_list:
                    if hasattr(prop, field):
                        value = getattr(prop, field)
                        prop_data['data'][field] = value

            comparison_data['properties'].append(prop_data)

        return comparison_data
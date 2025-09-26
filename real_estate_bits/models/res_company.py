from odoo import models, fields, api, _
# from odoo.exceptions import Warning


class ResCompany(models.Model):
    _inherit = 'res.company'

    commission_based_on = fields.Selection([('sales_team', 'Sales Team'),
                                            ('product_category', 'Product Category'),
                                            ('product_template', 'Product')], string="Calculation Based On",
                                           default='sales_team')
    when_to_pay = fields.Selection([('invoice_validate', 'Invoice Validate'), ('invoice_payment', 'Customer Payment')],
                                   string="When To Pay", default='invoice_payment')



    def create_property_types_and_categories(self):
        """Crear tipos de propiedades y categorías automáticamente"""
        
        main_category = self.env['product.category'].search([
            ('name', '=', 'Tipos de Propiedades'),
            ('parent_id', '=', False)
        ])
        if not main_category:
            main_category = self.env['product.category'].create({
                'name': 'Tipos de Propiedades'
            })

        property_types_structure = {
            'Casa': {
                'property_type': 'house',
                'subtypes': [
                    'Casa',  # Categoría general 
                    'Casa Finca',
                    'Casa Arquitectónica',
                    'Casa Campestre',
                    'Casa Hotel',
                    'Casa Lote',
                    'Casa Residencial',
                    'Casa de Campo'
                ]
            },
            'Apartamento': {
                'property_type': 'apartment',
                'subtypes': [
                    'Apartamento',  # Categoría general
                    'Apartamento Arrendado',
                    'Penthouse',
                    'Dúplex',
                    'Loft',
                    'Apartamento Amoblado',
                    'Apartamento Ejecutivo'
                ]
            },
            'Apartaestudio': {
                'property_type': 'studio',
                'subtypes': [
                    'Apartaestudio',
                    'Apartaestudio Amoblado',
                    'Studio Loft',
                    'Micro Apartamento'
                ]
            },
            'Oficina': {
                'property_type': 'office',
                'subtypes': [
                    'Oficina',  # Categoría general
                    'Oficina Comercial',
                    'Consultorio',
                    'Oficina Ejecutiva',
                    'Coworking',
                    'Centro de Negocios',
                ]
            },
            'Local': {
                'property_type': 'local',
                'subtypes': [
                    'Local',  # Categoría general
                    'Local Comercial',
                    'Local en Centro Comercial',
                    'Local en Galería',
                    'Local Esquinero',
                    'Showroom',
                    'Restaurante',
                    'Tienda',
                    'Café',
                    'Farmacia',
                    'Supermercado'
                ]
            },
            'Bodega': {
                'property_type': 'bodega',
                'subtypes': [
                    'Bodega',
                    'Bodega Industrial',
                    'Bodega Comercial',
                    'Bodega de Almacenamiento',
                    'Centro Logístico',
                    'Depósito',
                    'Almacén'
                ]
            },
            'Lote': {
                'property_type': 'lot',
                'subtypes': [
                    'Lote',
                    'Lote 122',  # Tipo específico de tu tabla
                    'Lote Urbano',
                    'Lote Industrial',
                    'Lote Comercial',
                    'Terreno',
                    'Solar'
                ]
            },
            'Lote Campestre': {
                'property_type': 'country_lot',
                'subtypes': [
                    'Lote Campestre',
                    'Lote Rural',
                    'Lote de Recreo',
                ]
            },
            'Parcela': {
                'property_type': 'plot',
                'subtypes': [
                    'Parcela',
                    'Parcela Rural',
                    'Parcela Urbana',
                    'Parcela Agrícola'
                ]
            },
            'Finca': {
                'property_type': 'finca',
                'subtypes': [
                    'Finca',
                    'Finca Recreativa',
                    'Finca Productiva',
                    'Finca Ganadera',
                    'Finca Agrícola',
                    'Hacienda',
                    'Estancia',
                    'Finca Cafetera',
                    'Finca Avícola'
                ]
            },
            'Hotel': {
                'property_type': 'hotel',
                'subtypes': [
                    'Hotel',
                    'Hotel Boutique',
                    'Hostal',
                    'Apart Hotel',
                    'Posada',
                    'Motel',
                    'Resort'
                ]
            },
            'Cabaña': {
                'property_type': 'cabin',
                'subtypes': [
                    'Cabaña',
                    'Cabaña de Recreo',
                    'Cabaña Campestre',
                    'Glamping',
                    'Cabaña Ecológica'
                ]
            },
            'Edificio': {
                'property_type': 'building',
                'subtypes': [
                    'Edificio',
                    'Edificio Completo',
                    'Edificio Residencial',
                    'Edificio Comercial',
                    'Edificio de Oficinas',
                    'Centro Comercial',
                    'Conjunto Residencial',
                    'Torre',
                    'Complejo'
                ]
            },
            'Sobre Plano': {
                'property_type': 'blueprint',
                'subtypes': [
                    'Sobre Plano',
                    'Apartamento Sobre Plano',
                    'Casa Sobre Plano',
                    'Proyecto Nuevo',
                    'Preventa'
                ]
            },
            'Espacios Especiales': {
                'property_type': 'building',  # Usamos building como tipo base
                'subtypes': [
                    'Gimnasio',
                    'Clínica',
                    'Hospital',
                    'Colegio',
                    'Universidad',
                    'Iglesia',
                    'Teatro',
                    'Auditorio',
                    'Salón de Eventos',
                    'Centro de Convenciones',
                    'Parqueadero',
                    'Garaje',
                    'Laboratorio',
                    'Taller',
                    'Estudio de Grabación',
                    'Galería de Arte',
                    'Museo',
                    'Biblioteca',
                    'Guardería',
                    'Spa',
                    'Centro de Estética',
                    'Veterinaria',
                    'Centro Deportivo',
                    'Discoteca',
                    'Bar',
                    'Panadería'
                ]
            }
        }

        created_types = []
        
        for main_type, type_info in property_types_structure.items():
            # Crear tipo principal
            main_property_type = self.env['property.type'].search([
                ('name', '=', main_type),
                ('parent_id', '=', False)
            ])
            
            if not main_property_type:
                main_property_type = self.env['property.type'].create({
                    'name': main_type,
                    'property_type': type_info['property_type']
                })
                created_types.append(main_property_type)
            
            # Crear subtipos
            for subtype in type_info['subtypes']:
                existing_subtype = self.env['property.type'].search([
                    ('name', '=', subtype),
                    ('parent_id', '=', main_property_type.id)
                ])
                
                if not existing_subtype:
                    subtype_record = self.env['property.type'].create({
                        'name': subtype,
                        'parent_id': main_property_type.id,
                        'property_type': type_info['property_type']
                    })
                    created_types.append(subtype_record)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Tipos de Propiedades Creados',
                'message': f'Se crearon {len(created_types)} tipos de propiedades exitosamente.',
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def create_property_sequence(self):
        """Crear secuencia para códigos de propiedades"""
        sequence = self.env['ir.sequence'].search([('code', '=', 'property.code')])
        if not sequence:
            self.env['ir.sequence'].create({
                'name': 'Secuencia de Propiedades',
                'code': 'property.code',
                'prefix': '',
                'suffix': '',
                'padding': 3,
                'number_next': 1,
                'number_increment': 1,
                'implementation': 'standard'
            })
            return True
        return False
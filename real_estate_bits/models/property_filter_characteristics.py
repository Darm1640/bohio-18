# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class PropertyFilterCharacteristics(models.Model):
    """Modelo para agrupar características potenciales de filtrado por tipo de inmueble"""
    _name = 'property.filter.characteristics'
    _description = 'Características de Filtrado por Tipo de Inmueble'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre del Grupo', required=True, translate=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    active = fields.Boolean(string='Activo', default=True)

    property_type = fields.Selection([
        ('bodega', 'Bodega'),
        ('local', 'Local'),
        ('apartment', 'Apartamento'),
        ('house', 'Casa'),
        ('studio', 'Apartaestudio'),
        ('office', 'Oficina'),
        ('finca', 'Finca'),
        ('lot', 'Lote'),
        ('hotel', 'Hotel'),
        ('cabin', 'Cabaña'),
        ('building', 'Edificio'),
        ('country_lot', 'Lote Campestre'),
        ('blueprint', 'Sobre Plano'),
        ('plot', 'Parcela'),
        ('project', 'Proyecto'),
        ('all', 'Todos los Tipos')
    ], string='Tipo de Inmueble', required=True, default='all')

    characteristic_ids = fields.Many2many(
        'property.characteristic.item',
        'property_filter_characteristic_rel',
        'filter_id',
        'characteristic_id',
        string='Características'
    )

    description = fields.Text(string='Descripción')


class PropertyCharacteristicItem(models.Model):
    """Items individuales de características para filtros"""
    _name = 'property.characteristic.item'
    _description = 'Item de Característica'
    _order = 'category, sequence, name'

    name = fields.Char(string='Nombre', required=True, translate=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    active = fields.Boolean(string='Activo', default=True)

    category = fields.Selection([
        ('basic', 'Características Básicas'),
        ('rooms', 'Habitaciones y Espacios'),
        ('outdoor', 'Áreas Exteriores'),
        ('parking', 'Parqueadero'),
        ('amenities', 'Amenidades del Edificio'),
        ('recreational', 'Áreas Recreativas'),
        ('security', 'Seguridad'),
        ('utilities', 'Servicios Públicos'),
        ('finishes', 'Acabados'),
        ('special', 'Características Especiales')
    ], string='Categoría', required=True, default='basic')

    field_name = fields.Char(
        string='Campo Técnico',
        required=True,
        help='Nombre del campo en el modelo product.template'
    )

    field_type = fields.Selection([
        ('boolean', 'Sí/No'),
        ('integer', 'Número'),
        ('selection', 'Selección'),
        ('many2one', 'Relación')
    ], string='Tipo de Campo', required=True, default='boolean')

    icon = fields.Char(string='Icono FontAwesome', help='ej: fa-bed, fa-car, fa-shield')

    filter_ids = fields.Many2many(
        'property.filter.characteristics',
        'property_filter_characteristic_rel',
        'characteristic_id',
        'filter_id',
        string='Grupos de Filtros'
    )


class PropertyTemplate(models.Model):
    """Extensión del modelo de propiedades con mejoras de filtrado y conversión"""
    _inherit = 'product.template'

    # =================== UNIDADES DE MEDIDA MEJORADAS ===================
    unit_of_measure = fields.Selection(
        selection_add=[
            ('ft2', 'Pies²'),
            ('vara2', 'Vara²'),
            ('acre', 'Acre'),
            ('fanegada', 'Fanegada')
        ],
        ondelete={
            'ft2': 'cascade',
            'vara2': 'cascade',
            'acre': 'cascade',
            'fanegada': 'cascade'
        }
    )

    # Conversiones de área
    area_in_ft2 = fields.Float(
        string='Área en Pies²',
        compute='_compute_area_conversions',
        store=True,
        digits=(16, 2),
        help='Área convertida a pies cuadrados (1 m² = 10.764 ft²)'
    )

    area_in_vara2 = fields.Float(
        string='Área en Varas²',
        compute='_compute_area_conversions',
        store=True,
        digits=(16, 2),
        help='Área convertida a varas cuadradas (1 m² = 1.4301 vara²)'
    )

    area_in_hectares = fields.Float(
        string='Área en Hectáreas',
        compute='_compute_area_conversions',
        store=True,
        digits=(16, 4),
        help='Área convertida a hectáreas (1 ha = 10,000 m²)'
    )

    # =================== MULTI-MONEDA MEJORADO ===================
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    # Precios en diferentes monedas (conversión automática)
    net_price_usd = fields.Monetary(
        string='Precio en USD',
        compute='_compute_multi_currency_prices',
        store=True,
        currency_field='usd_currency_id'
    )

    rental_price_usd = fields.Monetary(
        string='Arriendo en USD',
        compute='_compute_multi_currency_prices',
        store=True,
        currency_field='usd_currency_id'
    )

    usd_currency_id = fields.Many2one(
        'res.currency',
        string='USD Currency',
        compute='_compute_usd_currency',
        store=True
    )

    # =================== RANGOS DE PRECIO PARA FILTROS ===================
    price_range = fields.Selection([
        ('0-50m', 'Menos de $50 millones'),
        ('50-100m', '$50M - $100M'),
        ('100-200m', '$100M - $200M'),
        ('200-300m', '$200M - $300M'),
        ('300-500m', '$300M - $500M'),
        ('500-1000m', '$500M - $1.000M'),
        ('1000m+', 'Más de $1.000 millones')
    ], string='Rango de Precio', compute='_compute_price_range', store=True, index=True)

    rental_price_range = fields.Selection([
        ('0-500k', 'Menos de $500 mil'),
        ('500k-1m', '$500K - $1M'),
        ('1-2m', '$1M - $2M'),
        ('2-3m', '$2M - $3M'),
        ('3-5m', '$3M - $5M'),
        ('5m+', 'Más de $5M')
    ], string='Rango Arriendo', compute='_compute_rental_price_range', store=True, index=True)

    # =================== FILTROS AGRUPADOS POR CARACTERÍSTICAS ===================
    # Habitaciones agrupadas
    bedrooms_range = fields.Selection([
        ('studio', 'Apartaestudio'),
        ('1', '1 Habitación'),
        ('2', '2 Habitaciones'),
        ('3', '3 Habitaciones'),
        ('4', '4 Habitaciones'),
        ('5+', '5+ Habitaciones')
    ], string='Habitaciones', compute='_compute_bedrooms_range', store=True, index=True)

    bathrooms_range = fields.Selection([
        ('1', '1 Baño'),
        ('2', '2 Baños'),
        ('3', '3 Baños'),
        ('4+', '4+ Baños')
    ], string='Baños', compute='_compute_bathrooms_range', store=True, index=True)

    parking_range = fields.Selection([
        ('0', 'Sin Parqueadero'),
        ('1', '1 Parqueadero'),
        ('2', '2 Parqueaderos'),
        ('3+', '3+ Parqueaderos')
    ], string='Parqueaderos', compute='_compute_parking_range', store=True, index=True)

    # Área agrupada
    area_range = fields.Selection([
        ('0-50', 'Menos de 50 m²'),
        ('50-80', '50-80 m²'),
        ('80-120', '80-120 m²'),
        ('120-200', '120-200 m²'),
        ('200-500', '200-500 m²'),
        ('500+', 'Más de 500 m²')
    ], string='Rango de Área', compute='_compute_area_range', store=True, index=True)

    # =================== CARACTERÍSTICAS AGRUPADAS PARA FILTROS ===================
    has_outdoor_areas = fields.Boolean(
        string='Tiene Áreas Exteriores',
        compute='_compute_grouped_characteristics',
        store=True,
        help='Tiene patio, jardín, balcón o terraza'
    )

    has_luxury_amenities = fields.Boolean(
        string='Amenidades de Lujo',
        compute='_compute_grouped_characteristics',
        store=True,
        help='Jacuzzi, sauna, turco, piscina privada'
    )

    has_building_amenities = fields.Boolean(
        string='Amenidades del Conjunto',
        compute='_compute_grouped_characteristics',
        store=True,
        help='Piscina, gimnasio, salón social, zonas verdes'
    )

    has_full_security = fields.Boolean(
        string='Seguridad Completa',
        compute='_compute_grouped_characteristics',
        store=True,
        help='Portería 24h, cámaras, alarma'
    )

    # =================== MÉTODOS COMPUTE ===================

    @api.depends('area_in_m2')
    def _compute_area_conversions(self):
        """Convertir área a diferentes unidades de medida"""
        # Factores de conversión desde m²
        CONVERSION_FACTORS = {
            'ft2': 10.764,      # 1 m² = 10.764 ft²
            'vara2': 1.4301,    # 1 m² = 1.4301 vara² (vara colombiana)
            'hectare': 0.0001,  # 1 m² = 0.0001 ha
        }

        for record in self:
            if record.area_in_m2:
                record.area_in_ft2 = record.area_in_m2 * CONVERSION_FACTORS['ft2']
                record.area_in_vara2 = record.area_in_m2 * CONVERSION_FACTORS['vara2']
                record.area_in_hectares = record.area_in_m2 * CONVERSION_FACTORS['hectare']
            else:
                record.area_in_ft2 = 0.0
                record.area_in_vara2 = 0.0
                record.area_in_hectares = 0.0

    @api.depends('company_id')
    def _compute_usd_currency(self):
        """Obtener moneda USD"""
        usd = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        for record in self:
            record.usd_currency_id = usd.id

    @api.depends('net_price', 'net_rental_price', 'currency_id')
    def _compute_multi_currency_prices(self):
        """Convertir precios a diferentes monedas"""
        for record in self:
            if record.currency_id and record.usd_currency_id:
                # Convertir precio de venta
                if record.net_price:
                    record.net_price_usd = record.currency_id._convert(
                        record.net_price,
                        record.usd_currency_id,
                        record.company_id or self.env.company,
                        fields.Date.today()
                    )
                else:
                    record.net_price_usd = 0.0

                # Convertir precio de arriendo
                if record.net_rental_price:
                    record.rental_price_usd = record.currency_id._convert(
                        record.net_rental_price,
                        record.usd_currency_id,
                        record.company_id or self.env.company,
                        fields.Date.today()
                    )
                else:
                    record.rental_price_usd = 0.0
            else:
                record.net_price_usd = 0.0
                record.rental_price_usd = 0.0

    @api.depends('net_price')
    def _compute_price_range(self):
        """Calcular rango de precio para filtros"""
        for record in self:
            price = record.net_price or 0
            if price < 50000000:
                record.price_range = '0-50m'
            elif price < 100000000:
                record.price_range = '50-100m'
            elif price < 200000000:
                record.price_range = '100-200m'
            elif price < 300000000:
                record.price_range = '200-300m'
            elif price < 500000000:
                record.price_range = '300-500m'
            elif price < 1000000000:
                record.price_range = '500-1000m'
            else:
                record.price_range = '1000m+'

    @api.depends('rental_price')
    def _compute_rental_price_range(self):
        """Calcular rango de arriendo para filtros"""
        for record in self:
            price = record.rental_price or 0
            if price < 500000:
                record.rental_price_range = '0-500k'
            elif price < 1000000:
                record.rental_price_range = '500k-1m'
            elif price < 2000000:
                record.rental_price_range = '1-2m'
            elif price < 3000000:
                record.rental_price_range = '2-3m'
            elif price < 5000000:
                record.rental_price_range = '3-5m'
            else:
                record.rental_price_range = '5m+'

    @api.depends('num_bedrooms')
    def _compute_bedrooms_range(self):
        """Calcular rango de habitaciones"""
        for record in self:
            bedrooms = record.num_bedrooms or 0
            if record.property_type == 'studio':
                record.bedrooms_range = 'studio'
            elif bedrooms == 1:
                record.bedrooms_range = '1'
            elif bedrooms == 2:
                record.bedrooms_range = '2'
            elif bedrooms == 3:
                record.bedrooms_range = '3'
            elif bedrooms == 4:
                record.bedrooms_range = '4'
            elif bedrooms >= 5:
                record.bedrooms_range = '5+'
            else:
                record.bedrooms_range = False

    @api.depends('num_bathrooms')
    def _compute_bathrooms_range(self):
        """Calcular rango de baños"""
        for record in self:
            bathrooms = record.num_bathrooms or 0
            if bathrooms == 1:
                record.bathrooms_range = '1'
            elif bathrooms == 2:
                record.bathrooms_range = '2'
            elif bathrooms == 3:
                record.bathrooms_range = '3'
            elif bathrooms >= 4:
                record.bathrooms_range = '4+'
            else:
                record.bathrooms_range = False

    @api.depends('n_garage', 'covered_parking', 'uncovered_parking')
    def _compute_parking_range(self):
        """Calcular total de parqueaderos"""
        for record in self:
            total = (record.n_garage or 0) + (record.covered_parking or 0) + (record.uncovered_parking or 0)
            if total == 0:
                record.parking_range = '0'
            elif total == 1:
                record.parking_range = '1'
            elif total == 2:
                record.parking_range = '2'
            else:
                record.parking_range = '3+'

    @api.depends('area_in_m2')
    def _compute_area_range(self):
        """Calcular rango de área"""
        for record in self:
            area = record.area_in_m2 or 0
            if area < 50:
                record.area_range = '0-50'
            elif area < 80:
                record.area_range = '50-80'
            elif area < 120:
                record.area_range = '80-120'
            elif area < 200:
                record.area_range = '120-200'
            elif area < 500:
                record.area_range = '200-500'
            else:
                record.area_range = '500+'

    @api.depends('patio', 'garden', 'balcony', 'terrace', 'pools', 'gym',
                 'social_room', 'green_areas', 'jacuzzi', 'sauna', 'turkish_bath',
                 'has_security', 'security_cameras', 'alarm', 'doorman')
    def _compute_grouped_characteristics(self):
        """Agrupar características relacionadas para facilitar filtros"""
        for record in self:
            # Áreas exteriores
            record.has_outdoor_areas = any([
                record.patio,
                record.garden,
                record.balcony,
                record.terrace
            ])

            # Amenidades de lujo
            record.has_luxury_amenities = any([
                record.jacuzzi,
                record.sauna,
                record.turkish_bath
            ])

            # Amenidades del conjunto/edificio
            record.has_building_amenities = any([
                record.pools,
                record.gym,
                record.social_room,
                record.green_areas,
                record.sports_area,
                record.court
            ])

            # Seguridad completa
            record.has_full_security = any([
                record.has_security,
                record.security_cameras,
                record.alarm,
                record.doorman in ['24_hours', 'daytime']
            ])

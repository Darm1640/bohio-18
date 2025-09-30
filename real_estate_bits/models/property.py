from odoo import _, api, fields, models, tools
from .project_worksite import PROJECT_WORKSITE_TYPE
import logging
import requests
import json
import pytz
import threading
from ast import literal_eval
from collections import OrderedDict, defaultdict
from datetime import date, datetime, timedelta
from markupsafe import Markup
from psycopg2 import sql
from decimal import Decimal, ROUND_HALF_UP
from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.addons.iap.tools import iap_tools
from odoo.addons.mail.tools import mail_validation
from odoo.addons.phone_validation.tools import phone_validation
from odoo.exceptions import UserError, AccessError,ValidationError
from odoo.osv import expression
from odoo.tools.translate import _
from odoo.tools import date_utils, email_split, is_html_empty, groupby, parse_contact_from_email
from odoo.tools.misc import get_lang

_logger = logging.getLogger(__name__)


class Property(models.Model):
    _inherit = ["product.template"]
    _description = "Propiedad"
    _order = "sequence, id"


    # =================== BASIC INFO ===================
    state = fields.Selection([
        ("free", "Disponible"), 
        ("reserved", "Reservada"), 
        ("on_lease", "Arriendo"),
        ("sold", "Vendida"), 
        ("blocked", "Bloqueada")
    ], "Estado", default="free", tracking=True, index=True)

    sequence = fields.Integer("Secuencia", tracking=True, index=True)
    
    # Código interno automático
    default_code = fields.Char("Código Interno", compute="_compute_default_code", store=True, readonly=False, tracking=True, index='trigram')
    
    @api.depends('property_type_id')
    def _compute_default_code(self):
        """Generar código automático BOH-XXX"""
        for rec in self:
            if not rec.default_code and rec.id:
                sequence = self.env['ir.sequence'].next_by_code('property.code') or str(rec.id).zfill(3)
                rec.default_code = f"BOH-{sequence}"

    partner_id = fields.Many2one("res.partner", "Propietario Principal", tracking=True, index=True)
    region_id = fields.Many2one("region.region", "Barrio", tracking=True, index=True)
    property_date = fields.Date("Fecha", default=fields.Date.context_today, tracking=True, index=True)
    country_code = fields.Char(related="country_id.code", string="Código País", store=True)

    note = fields.Html("Notas", tracking=True)
    description = fields.Text("Descripción", tracking=True)

    # =================== PROPERTY TYPES ===================
    property_type_id = fields.Many2one("property.type", "Tipo de Propiedad", tracking=True, index=True)
    property_type = fields.Selection(
        related='property_type_id.property_type', 
        string='Tipo de Inmueble', 
        store=True, 
        readonly=True,
        tracking=True,
        index=True
    )
    
    # =================== LOCATION ===================
    address = fields.Char(string='Dirección', tracking=True, index='trigram')
    department = fields.Char(string='Departamento', tracking=True, index='trigram')
    municipality = fields.Char(string='Municipio', tracking=True, index='trigram')
    neighborhood = fields.Char(string='Barrio', tracking=True, index='trigram')
    
    street = fields.Char('Dirección Principal', readonly=False, store=True, tracking=True, index='trigram')
    street2 = fields.Char('Dirección Secundaria', readonly=False, store=True, tracking=True, index='trigram')
    zip = fields.Char('Código Postal', change_default=True, readonly=False, store=True, tracking=True, index=True)
    city = fields.Char('Ciudad', readonly=False, store=True, tracking=True, index='trigram')
    city_id = fields.Many2one(comodel_name='res.city', string='Ciudad', readonly=False, store=True, 
                             domain="[('country_id', '=?', country_id)]", tracking=True, index=True)
    state_id = fields.Many2one("res.country.state", string='Departamento', readonly=False, store=True, 
                              domain="[('country_id', '=?', country_id)]", tracking=True, index=True)
    country_id = fields.Many2one('res.country', string='País', readonly=False, store=True, 
                                default=lambda self: self.env.company.country_id.id, tracking=True, index=True)
    
    # =================== GEOLOCALIZACIÓN AUTOMÁTICA ===================
    # Campos de geolocalización con cálculo automático desde dirección
    latitude = fields.Float(
        string='Latitud',
        digits=(10, 8),
        tracking=True,
        index=True,
        store=True,
        help='Latitud GPS calculada automáticamente desde la dirección'
    )

    longitude = fields.Float(
        string='Longitud',
        digits=(11, 8),
        tracking=True,
        index=True,
        readonly=False,
        help='Longitud GPS calculada automáticamente desde la dirección'
    )

    geocoding_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('success', 'Exitoso'),
        ('failed', 'Fallido'),
        ('manual', 'Manual')
    ], string='Estado Geocodificación', default='pending', readonly=True)

    full_computed_address = fields.Char(
        string='Dirección Completa para Geocodificación',
        compute='_compute_full_address_geo',
        store=True
    )

    # =================== PROPERTY DETAILS ===================
    stratum = fields.Selection([
        ('1', 'Estrato 1'),
        ('2', 'Estrato 2'),
        ('3', 'Estrato 3'),
        ('4', 'Estrato 4'),
        ('5', 'Estrato 5'),
        ('6', 'Estrato 6'),
        ('commercial', 'Comercial'),
        ('no_stratified', 'No Estratificada'),
    ], string='Estrato', tracking=True, index=True)

    type_service = fields.Selection([
        ('sale', 'Venta'),
        ('rent', 'Arriendo'),
        ('sale_rent', 'Venta y Arriendo'),
        ('vacation_rent', 'Arriendo Vacacional')
    ], string='Tipo De Servicios', tracking=True, index=True)

    property_status = fields.Selection([
        ('new', 'Nuevo'),
        ('used', 'Usado'),
        ('remodeled', 'Remodelado')
    ], string='Estado del Inmueble', tracking=True, index=True)

    # =================== MEASUREMENTS ===================
    property_area = fields.Float("Área de la Propiedad", digits=(16, 8), tracking=True, index=True,
                                 help="Área de la propiedad en la unidad seleccionada")
    
    unit_of_measure = fields.Selection([
        ("m", "m²"), 
        ("yard", "Yarda²"),
        ("hectare", "Hectárea")
    ], default="m", string="Unidad de Medida", tracking=True, index=True)
    
    unit_label = fields.Char("Etiqueta Unidad", compute="_compute_unit_label", store=True)
    
    area_in_m2 = fields.Float("Área en M² (Interno)", compute="_compute_area_in_m2", store=True, digits=(16, 8))
    
    unit_iso_code = fields.Char("Código ISO", compute="_compute_unit_iso_info", store=True)
    unit_display_name = fields.Char("Nombre Unidad", compute="_compute_unit_iso_info", store=True)
    
    front_meters = fields.Float("Frente (metros)", digits=(10, 2), tracking=True, index=True)
    depth_meters = fields.Float("Fondo (metros)", digits=(10, 2), tracking=True, index=True)

    # =================== BASIC CHARACTERISTICS ===================
    num_bedrooms = fields.Integer(string='N° De Habitaciones', tracking=True, index=True)
    num_bathrooms = fields.Integer(string='N° De Baños', tracking=True, index=True)
    property_age = fields.Integer(string='Antigüedad del Inmueble', tracking=True, index=True)
    num_living_room = fields.Integer(string='N° De Sala', tracking=True, index=True)
    floor_number = fields.Integer(string='N° De Piso', tracking=True, index=True)
    number_of_levels = fields.Integer(string='Número de Niveles', tracking=True, index=True)

    # =================== ROOMS AND SPACES ===================
    # Salas y comedores
    living_room = fields.Boolean(string='¿Tiene Sala?', tracking=True)
    living_dining_room = fields.Boolean(string='¿Tiene Sala Comedor?', tracking=True)
    main_dining_room = fields.Boolean(string='¿Tiene Comedor?', tracking=True)
    auxiliary_dining_room = fields.Boolean(string='¿Tiene Comedor Auxiliar?', tracking=True)
    study = fields.Boolean(string='¿Tiene Estudio?', tracking=True)
    entrance_hall = fields.Boolean(string='¿Tiene Hall?', tracking=True)
    
    # Cocinas
    simple_kitchen = fields.Boolean(string='¿Tiene Cocina Sencilla?', tracking=True)
    integral_kitchen = fields.Boolean(string='¿Tiene Cocina Integral?', tracking=True)
    american_kitchen = fields.Boolean(string='¿Tiene Cocina tipo Americano?', tracking=True)
    mixed_integral_kitchen = fields.Boolean(string='¿Tiene Cocina Integral Mixta?', tracking=True)
    
    # Cuartos de servicio y baños
    service_room = fields.Boolean(string='¿Tiene Alcoba de Servicio?', tracking=True)
    service_bathroom = fields.Boolean(string='¿Tiene Baño de Servicio?', tracking=True)
    auxiliary_bathroom = fields.Boolean(string='¿Tiene Baño Auxiliar?', tracking=True)
    utility_room = fields.Boolean(string='¿Tiene Cuarto Útil?', tracking=True)
    
    # Almacenamiento
    closet = fields.Boolean(string='¿Tiene Clóset?', tracking=True)
    n_closet = fields.Integer(string='N° De Clóset', tracking=True, index=True)
    walk_in_closet = fields.Boolean(string='¿Tiene Walk-in Closet?', tracking=True)
    dressing_room = fields.Boolean(string='¿Tiene Vestidor?', tracking=True)
    n_dressing_room = fields.Integer(string='Vestidores', tracking=True)
    warehouse = fields.Boolean(string='¿Tiene Depósito/Bodega?', tracking=True)
    
    # =================== OUTDOOR AREAS ===================
    patio = fields.Boolean(string='¿Tiene Patio?', tracking=True)
    garden = fields.Boolean(string='¿Tiene Jardín?', tracking=True)
    balcony = fields.Boolean(string='¿Tiene Balcón?', tracking=True)
    terrace = fields.Boolean(string='¿Tiene Terraza?', tracking=True)
    solar_area = fields.Boolean(string='¿Tiene Solar?', tracking=True)
    solarium = fields.Boolean(string='¿Tiene Solarium?', tracking=True)
    laundry_area = fields.Boolean(string='¿Tiene Zona de lavandería?', tracking=True)
    
    # =================== FLOORS AND FINISHES ===================
    floor_type = fields.Selection([
        ('tile', 'Baldosa'),
        ('wood', 'Madera'),
        ('ceramic', 'Cerámica'),
        ('porcelain', 'Porcelanato'),
        ('marble', 'Mármol'),
        ('carpet', 'Alfombra'),
        ('aluminum', 'Aluminio'),
        ('fiberglass', 'Fibra de Vidrio')
    ], string='Tipo de piso', tracking=True)
    
    marble_floor = fields.Boolean(string='¿Tiene Piso en Baldosa/Mármol?', tracking=True)
    
    # =================== DOORS AND WINDOWS ===================
    door_type = fields.Selection([
        ('wood', 'Madera'),
        ('metal', 'Metal'),
        ('glass', 'Vidrio'),
        ('aluminum', 'Aluminio'),
        ('fiberglass', 'Fibra de Vidrio')
    ], string='Tipo de Puerta', tracking=True)
    
    security_door = fields.Boolean(string='¿Tiene Puerta de Seguridad?', tracking=True)
    truck_door = fields.Boolean(string='¿Tiene Puerta Camión?', tracking=True)
    blinds = fields.Boolean(string='¿Tiene Persiana?', tracking=True)
    
    # =================== PARKING ===================
    garage = fields.Boolean(string='¿Tiene Garaje?', tracking=True)
    n_garage = fields.Integer(string='N° Garaje', tracking=True)
    covered_parking = fields.Integer(string='N° Parqueadero Cubierto', tracking=True)
    uncovered_parking = fields.Integer(string='N° Parqueadero Descubierto', tracking=True)
    linear_double_parking = fields.Boolean(string='¿Tiene Parqueadero doble Lineal?', tracking=True)
    parallel_double_parking = fields.Boolean(string='¿Tiene Parqueadero doble Paralelo?', tracking=True)
    visitors_parking = fields.Boolean(string='¿Tiene Parqueadero de Visitantes?', tracking=True)
    common_parking = fields.Boolean(string='¿Tiene Parqueadero Común?', tracking=True)
    
    # =================== UTILITIES AND SERVICES ===================
    # Gas
    gas_installation = fields.Boolean(string='¿Tiene Red de Gas?', tracking=True)
    gas_heating = fields.Boolean(string='¿Tiene Calentador a Gas?', tracking=True)
    no_gas = fields.Boolean(string='¿Sin Gas?', tracking=True)
    
    # Electricidad
    electric_heating = fields.Boolean(string='¿Tiene Calentador Eléctrico?', tracking=True)
    electric_plant = fields.Boolean(string='¿Tiene Planta Eléctrica?', tracking=True)
    electrical_capacity = fields.Char(string='Capacidad Eléctrica', tracking=True)
    lamps_included = fields.Boolean(string='¿Tiene Lámparas Incluidas?', tracking=True)
    
    # NUEVO: Campos de agua optimizados
    has_water = fields.Boolean(string='¿Tiene Agua?', tracking=True, help="Disponibilidad general de agua")
    hot_water = fields.Boolean(string='¿Tiene Agua Caliente?', tracking=True)
    water_nearby = fields.Boolean(string='¿Tiene Agua Cerca?', tracking=True, 
                                 help="Para terrenos - disponibilidad de agua en proximidad")
    aqueduct_access = fields.Boolean(string='¿Tiene Acceso al Acueducto?', tracking=True)
    
    # Aire acondicionado
    air_conditioning = fields.Boolean(string='¿Tiene Aire Acondicionado?', tracking=True)
    n_air_conditioning = fields.Integer(string='N° Aire Acondicionado', tracking=True)
    ac_connections = fields.Boolean(string='¿Tiene Acometidas Aire Acondicionado?', tracking=True)
    n_ac_connections = fields.Integer(string='N° Acometidas Aire Acondicionado', tracking=True) 
    
    # Comunicaciones
    phone_lines = fields.Integer(string='N° Líneas Telefónicas', tracking=True)
    intercom = fields.Boolean(string='¿Tiene Citófono?', tracking=True)
    
    # =================== SECURITY ===================
    # NUEVO: Campos de seguridad consolidados
    has_security = fields.Boolean(string='¿Tiene Seguridad?', tracking=True)
    security_cameras = fields.Boolean(string='¿Tiene Cámaras de Vigilancia?', tracking=True)
    alarm = fields.Boolean(string='¿Tiene Alarma?', tracking=True)
    
    # =================== BUILDING AMENITIES ===================
    doorman = fields.Selection([
        ('24_hours', '24 Horas'),
        ('daytime', 'Diurna'),
        ('virtual', 'Video Citófonía'),
        ('none', 'Sin Portería')
    ], string='Tipo de Portería', tracking=True)
    
    doorman_hours = fields.Char(string='Horas Portería', tracking=True)
    doorman_phone = fields.Char(string='Teléfono de la Portería', tracking=True)
    
    elevator = fields.Boolean(string='¿Tiene Ascensor?', tracking=True)
    private_elevator = fields.Boolean(string='¿Tiene Ascensor Privado?', tracking=True)
    garbage_chute = fields.Boolean(string='¿Tiene Contenedor de Basuras?', tracking=True)
    
    # =================== RECREATIONAL AREAS ===================
    social_room = fields.Boolean(string='¿Tiene Salón Social?', tracking=True)
    gym = fields.Boolean(string='¿Tiene Gimnasio?', tracking=True)
    pools = fields.Boolean(string='¿Tiene Piscina?', tracking=True)
    n_pools = fields.Integer(string='N° Piscinas', tracking=True)
    sauna = fields.Boolean(string='¿Tiene Sauna?', tracking=True)
    turkish_bath = fields.Boolean(string='¿Tiene Turco?', tracking=True)
    jacuzzi = fields.Boolean(string='¿Tiene Jacuzzi?', tracking=True)
    green_areas = fields.Boolean(string='¿Tiene Zonas Verdes?', tracking=True)
    sports_area = fields.Boolean(string='¿Tiene Placa Polideportiva?', tracking=True)
    court = fields.Boolean(string='¿Tiene Cancha?', tracking=True)
    bar = fields.Boolean(string='¿Tiene Bar?', tracking=True)
    
    # NUEVO: Juegos infantiles específicos
    has_playground = fields.Boolean(string='¿Tiene Zona de Juegos?', tracking=True)
    playground_swings = fields.Boolean(string='¿Tiene Columpios?', tracking=True)
    playground_slides = fields.Boolean(string='¿Tiene Toboganes?', tracking=True)
    playground_seesaw = fields.Boolean(string='¿Tiene Balancines?', tracking=True)
    playground_sandbox = fields.Boolean(string='¿Tiene Arenero?', tracking=True)
    playground_climbing = fields.Boolean(string='¿Tiene Juegos de Escalar?', tracking=True)
    
    # =================== ADDITIONAL FEATURES ===================
    furnished = fields.Boolean(string='¿Está Amoblado?', tracking=True)
    fireplace = fields.Boolean(string='¿Tiene Chimenea?', tracking=True)
    mezzanine = fields.Boolean(string='¿Tiene Mezzanine?', tracking=True)
    
    # Tipo de apartamento
    apartment_type = fields.Selection([
        ('duplex', 'Dúplex'),
        ('loft', 'Loft'),
        ('penthouse', 'Penthouse')
    ], string='Tipo de apartamento', tracking=True, index=True)
    
    # =================== BUSINESS RELATED ===================
    real_estate_sign = fields.Char(string='Finca Raíz', tracking=True, index='trigram')
    poster_sign = fields.Boolean(string='¿Tiene Afiche?', tracking=True, index=True)
    real_estate_platform = fields.Boolean(string='¿Está en Biinmo?', tracking=True, index=True)
    urban_space = fields.Boolean(string='¿Tiene Espacio Urbano?', tracking=True, index=True)
    urban_space_note = fields.Char(string='Nota de Espacio Urbano?', tracking=True)
    construction_company = fields.Char(string='Constructora', tracking=True, index='trigram')
    referrer = fields.Char(string='Quien Refiere', tracking=True, index='trigram')
    
    # =================== FINANCIAL ===================
    liens = fields.Boolean(string='¿Tiene Gravámenes?', tracking=True)
    
    # =================== PRICING VENTA - SIMPLIFICADO ===================
    net_price = fields.Float("Precio Final de Venta", compute="_calc_price", store=True, readonly=False, tracking=True, index=True)
    price_before_discount = fields.Float('Precio Antes Descuento', compute='_calc_price', store=True, readonly=False, tracking=True, index=True)
    
    property_price_type = fields.Selection([
        ("fix", "Costo Fijo"), 
        ("sft", "Por Unidad")
    ], default="sft", string="Tipo Precio Venta", tracking=True, index=True)
    
    # SIMPLIFICADO: Un solo campo de precio por unidad
    price_per_unit = fields.Float("Precio por Unidad", tracking=True, index=True,
                                  help="Precio por unidad según la medida seleccionada")
    
    discount_type = fields.Selection([
        ("percentage", "Porcentaje"), 
        ("amount", "Monto")
    ], string="Tipo Descuento Venta", tracking=True, index=True)
    discount = fields.Float("Descuento Venta", tracking=True, index=True)
    
    # =================== PRICING ARRIENDO - SIMPLIFICADO ===================
    rental_price_type = fields.Selection([
        ("fix", "Costo Fijo"), 
        ("sft", "Por Unidad")
    ], default="fix", string="Tipo Precio Arriendo", tracking=True, index=True)
    
    # SIMPLIFICADO: Un solo campo de precio arriendo por unidad
    rental_price_per_unit = fields.Float("Precio Arriendo por Unidad", tracking=True, index=True,
                                         help="Precio arriendo por unidad según la medida seleccionada")
    
    # Precio final arriendo
    net_rental_price = fields.Float("Precio Final de Arriendo", compute="_calc_rental_price", 
                                   store=True, readonly=False, tracking=True, index=True)
    rental_price_before_discount = fields.Float('Precio Arriendo Antes Descuento', 
                                               compute='_calc_rental_price', store=True, readonly=False, tracking=True, index=True)
    
    rental_discount_type = fields.Selection([
        ("percentage", "Porcentaje"), 
        ("amount", "Monto")
    ], string="Tipo Descuento Arriendo", tracking=True, index=True)
    rental_discount = fields.Float("Descuento Arriendo", tracking=True, index=True)
    
    # =================== REFERENCIAS EN OTRAS UNIDADES ===================
    price_per_m2_ref = fields.Float("Precio por m² (Ref)", compute="_compute_unit_price_references", store=True)
    price_per_hectare_ref = fields.Float("Precio por Ha (Ref)", compute="_compute_unit_price_references", store=True)
    price_per_yard_ref = fields.Float("Precio por Yd² (Ref)", compute="_compute_unit_price_references", store=True)
    
    # OPTIMIZADO: Campos de rango con auto-llenado
    rent_value_from = fields.Float(string='Valor arriendo desde', tracking=True, index=True)
    rent_value_to = fields.Float(string='Valor arriendo hasta', tracking=True, index=True)
    sale_value_from = fields.Float(string='Valor venta desde', tracking=True, index=True)
    sale_value_to = fields.Float(string='Valor venta hasta', tracking=True, index=True)
    admin_value = fields.Float(string='Valor administración', tracking=True, index=True)
    cadastral_valuation = fields.Float(string='Avalúo catastral', tracking=True, index=True)
    property_tax = fields.Float(string='Impuesto predial', tracking=True, index=True)
    
    # =================== SCHEDULE ===================
    ideal_visit_schedule = fields.Char(string='Horario ideal visitas', tracking=True)
    
    # =================== MAINTENANCE AND UTILITIES ===================
    utility_ids = fields.One2many("property.utilities", "property_id")
    maintenance_type = fields.Selection([
        ("fix", "Costo Fijo"), 
        ("sft", "Por M²")
    ], default="fix", tracking=True)
    maintenance_charges = fields.Float(tracking=True)
    maintenance_count = fields.Integer(compute='_maintenance_count', string='Cantidad Mantenimientos')
    total_maintenance = fields.Float(compute="_calc_total", store=True, compute_sudo=True)
    total_cost = fields.Float(compute="_calc_total", store=True, compute_sudo=True)
    total_utilities = fields.Float(compute="_calc_utilities")
    
    # =================== LEGAL ===================
    license_code = fields.Char("Código de Licencia", size=16, tracking=True)
    license_date = fields.Date("Fecha de Licencia", tracking=True)
    date_added = fields.Date("Fecha Agregada a Notarización", tracking=True)
    license_location = fields.Char("Notarización de Licencia", tracking=True)
    registration_number = fields.Char(string='Folio Matrícula', tracking=True)
    cadastral_reference = fields.Char(string='Referencia Catastral', tracking=True)
    nearly_other = fields.Char(string='Cerca de', tracking=True)  
    
    # =================== CONSIGNMENT ===================
    consignment_date = fields.Date(string='Fecha de Consignación', default=fields.Date.context_today, tracking=True)
    property_consignee = fields.Selection([
        ('owner', 'Propietario'),
        ('tenant', 'Arrendatario'),
        ('agent', 'Agente Inmobiliario')
    ], string='Quién Consignó el Inmueble', tracking=True)
    
    social_fee_payer = fields.Selection([
        ('owner', 'Propietario'),
        ('tenant', 'Arrendatario'),
        ('real_estate', 'Inmobiliaria'),
    ], string='Quién Paga Cuota Sostenimiento', tracking=True)
    
    keys_location = fields.Selection([
        ('office', 'Oficina'),
        ('property', 'Inmueble'),
        ('doorman', 'Portería'),
        ('owner', 'Propietario'),
        ('other', 'Otro')
    ], string='Llaves en', tracking=True)
    key_note = fields.Char(string='Notas Sobre las llaves', tracking=True)
    
    user_consing_id = fields.Many2one(
        comodel_name='res.partner',
        string="Consignatario",
        compute='_compute_user_id',
        store=True, readonly=False, precompute=True, index=True,
        tracking=2,
    )
    
    # =================== OWNERS ===================
    owners_lines = fields.One2many('contract.owner.partner', 'product_id', string="Propietarios")
    is_multi_owner = fields.Boolean(default=False, string="¿Múltiples Propietarios?", tracking=True)
    
    # =================== DESCRIPTIONS ===================
    urbanization_description = fields.Text(string='Descripción Urbanización', tracking=True)
    property_description = fields.Text(string='Descripción Propiedad', tracking=True)
    observations = fields.Text(string='Observaciones', tracking=True)
    
    # =================== PROJECT INFO ===================
    project_worksite_id = fields.Many2one("project.worksite", "Proyecto", tracking=True)
    project_worksite_ids = fields.Many2many("project.worksite", "property_worksite_product_template_rel", 
                                            'pw_id', 'p_id', string="Propiedades")
    contact_ids = fields.Many2many("res.partner", string="Contactos")
    project_type = fields.Selection(selection=PROJECT_WORKSITE_TYPE + [('shop', 'Tienda')], default="tower", tracking=True)
    floor = fields.Integer("Piso", tracking=True)
    project_area = fields.Float("Área del Proyecto", tracking=True)
    
    # =================== RENTAL INFO ===================
    rental_fee = fields.Float("Tarifa de alquiler", digits=(16, 4), tracking=True)
    insurance_fee = fields.Float("Tarifa de seguro", tracking=True)
    template_id = fields.Many2one("installment.template", "Plantilla de Pago", tracking=True)
    
    # =================== FLAGS ===================
    is_property = fields.Boolean("¿Es Propiedad?", default=True, tracking=True)
    is_shop = fields.Boolean("¿Es Tienda?", default=False, tracking=True)
    
    # =================== BILLING ===================
    billing_address_id = fields.Many2one('res.partner', string='Dirección de la propiedad', 
                                         domain="[('parent_id', '=', partner_id)]", tracking=True)
    partner_is_blacklisted = fields.Boolean('Socio en lista negra', related='partner_id.is_blacklisted', readonly=True)
    
    # =================== CONTACT INFO ===================
    contact_name = fields.Char('Nombre del contacto', compute='_compute_contact_name', 
                               index='trigram', tracking=30, readonly=False, store=True)
    email_from = fields.Char('Email', tracking=40, index='trigram', readonly=False, store=True)
    email_normalized = fields.Char(index='trigram')
    email_domain_criterion = fields.Char(string='Criterio de Dominio de Email', index='btree_not_null', 
                                        store=True, unaccent=False)
    phone = fields.Char('Teléfono', tracking=50, compute='_compute_phone', inverse='_inverse_phone', 
                       readonly=False, store=True)
    mobile = fields.Char('Móvil', compute='_compute_mobile', readonly=False, store=True, tracking=True)
    phone_sanitized = fields.Char(index='btree_not_null')
    phone_state = fields.Selection([
        ('correct', 'Correcto'), 
        ('incorrect', 'Incorrecto')
    ], string='Calidad del Teléfono', compute="_compute_phone_state", store=True)
    email_state = fields.Selection([
        ('correct', 'Correcto'), 
        ('incorrect', 'Incorrecto')
    ], string='Calidad del Email', compute="_compute_email_state", store=True)
    website = fields.Char('Sitio Web', help="Sitio web del contacto", readonly=False, store=True, tracking=True)
    
    # =================== LANGUAGE ===================
    lang_id = fields.Many2one('res.lang', string='Idioma', compute='_compute_lang_id', readonly=False, store=True, tracking=True)
    lang_code = fields.Char(related='lang_id.code')
    lang_active_count = fields.Integer(compute='_compute_lang_active_count')
    
    # =================== COMPANY ===================
    company_id = fields.Many2one('res.company', string='Compañía', copy=False, store=True, 
                                 default=lambda self: self.env.company, tracking=True)
    country_enforce_cities = fields.Boolean(related='country_id.enforce_cities')
    
    # =================== IDENTIFICATION ===================
    l10n_latam_identification_type_id = fields.Many2one('l10n_latam.identification.type',
        string="Tipo documento", index='btree_not_null', auto_join=True,
        default=lambda self: self.env.ref('l10n_latam_base.it_vat', raise_if_not_found=False),
        help="El tipo de identificación", tracking=True)
    vat = fields.Char('NIT/CC', readonly=False, store=True, tracking=True)
    
    # =================== COUNTS ===================
    reservation_count = fields.Integer(compute="_reservation_count", string="Cantidad Reservas", store=True)
    
    # =================== ADDITIONAL FIELDS ===================
    building_unit = fields.Selection([
        ('urbanizacion', 'Urbanización'),
        ('edificio', 'Edificio'),
        ('conjunto_cerrado', 'Conjunto Cerrado'),
        ('conjunto_residencial', 'Conjunto Residencial'),
        ('complejo_mixto', 'Complejo Mixto'),
        ('proyecto_vip', 'Proyecto VIP'),
        ('proyecto_vis', 'Proyecto VIS'),], string='Tipo de unidad', tracking=True, index=True)
    
    is_vis = fields.Boolean(string='Es VIS', tracking=True, help='Vivienda de Interés Social', index=True)
    is_vip = fields.Boolean(string='Es VIP', tracking=True, help='Vivienda de Interés Prioritario', index=True)
    has_subsidy = fields.Boolean(string='Tiene Subsidio', tracking=True, index=True)
    
    doc_charges = fields.Float("Cargos de Documentos", tracking=True)
    tax_base_amount = fields.Float("Monto Base del Impuesto", tracking=True)
    partner_from = fields.Date("Fecha de Compra", tracking=True)
    partner_to = fields.Date("Fecha de Venta", tracking=True)
    
    # =================== CÁLCULOS NOTARIALES COMPLETOS ===================
    
    # Configuración del acto notarial
    notarial_act_type = fields.Selection([
        # COMPRAVENTAS DE VIVIENDA Y TERRENOS
        ('compraventa_inmueble', 'Compraventa Bien Inmueble'),
        ('compraventa_vis', 'Compraventa Vivienda de Interés Social'),
        ('compraventa_vip_subsidio', 'Compraventa VIP con Subsidio Familiar'),
        ('compraventa_vip_ahorradores', 'Compraventa VIP para Ahorradores con Subsidio'),
        ('compraventa_hipoteca_abierta', 'Compraventa con Hipoteca Abierta sin Límite'),
        ('compraventa_retroventa', 'Compraventa con Pacto de Retroventa'),
        ('compraventa_posesion', 'Compraventa de Posesión'),
        ('compraventa_derechos_cuota', 'Compraventa Derechos Cuota'),
        
        # HIPOTECAS
        ('hipoteca_normal', 'Hipoteca'),
        ('hipoteca_abierta', 'Hipoteca Abierta'),
        ('hipoteca_abierta_limite', 'Hipoteca Abierta con Límite de Cuantía'),
        ('hipoteca_abierta_sin_limite', 'Hipoteca Abierta sin Límite de Cuantía'),
        ('hipoteca_ley546_subsidio', 'Hipoteca Ley 546/99 con Subsidio (10%)'),
        ('hipoteca_ley546_sin_subsidio', 'Hipoteca Ley 546/99 sin Subsidio (40%)'),
        ('hipoteca_vis', 'Hipoteca Vivienda de Interés Social (50%)'),
        
        # CANCELACIONES DE HIPOTECA
        ('cancelacion_hipoteca', 'Cancelación Hipoteca'),
        ('cancelacion_hipoteca_abierta', 'Cancelación Hipoteca Abierta'),
        ('cancelacion_hipoteca_indeterminada', 'Cancelación Hipoteca Cuantía Indeterminada'),
        ('cancelacion_hipoteca_ley546', 'Cancelación Hipoteca Créditos Vivienda Ley 546'),
        ('cancelacion_hipoteca_ley546_subsidio', 'Cancelación Hipoteca Ley 546 con Subsidio'),
        ('cancelacion_hipoteca_ley546_sin_subsidio', 'Cancelación Hipoteca Ley 546 sin Subsidio'),
        ('cancelacion_hipoteca_mayor_extension', 'Cancelación Hipoteca Mayor Extensión'),
        ('cancelacion_parcial_hipoteca', 'Cancelación Parcial de Hipoteca'),
        
        # HERENCIAS Y LIQUIDACIONES ESPECIALES
        ('liquidacion_herencia', 'Liquidación de Herencia'),
        ('liquidacion_sociedad_conyugal', 'Liquidación de Sociedad Conyugal'),
        ('particion_herencia', 'Partición de Herencia'),
        ('adjudicacion_herencia', 'Adjudicación por Herencia'),
    ], string="Tipo de Acto Notarial", default='compraventa_inmueble', tracking=True)
    
    # Configuración de cuantía
    cuantia_source = fields.Selection([
        ('sale_value', 'Usar Valor de Venta'),
        ('custom_amount', 'Usar Cuantía Personalizada'),
        ('auto', 'Automático (Venta primero, luego cuantía)')
    ], string="Fuente de Cuantía", default='auto', tracking=True,
    help="Determina qué valor usar para los cálculos notariales")
    
    notarial_amount = fields.Monetary("Valor para Liquidación Notarial", currency_field='currency_id',
                                     tracking=True, help="Valor específico para cálculos notariales")
    
    # Características del acto
    sale_with_natural_person = fields.Boolean("Venta con Persona Natural", default=True, tracking=True,
                                             help="Indica si la venta es con persona natural para aplicar retención")
    is_nonprofit_buyer = fields.Boolean("Comprador Sin Ánimo de Lucro", default=False, tracking=True,
                                       help="Indica si el comprador es entidad sin ánimo de lucro (exenta de retención)")
    
    # Copias y documentos
    matriz_copies = fields.Integer("Copias Matriz", default=1, tracking=True,
                                  help="Número de copias de la matriz")
    protocolo_copies = fields.Integer("Copias Protocolo", default=1, tracking=True,
                                     help="Número de copias del protocolo")
    biometric_persons = fields.Integer("Personas para Biometría", default=2, tracking=True,
                                      help="Número de personas que requieren autenticación biométrica (mínimo 2)")
    
    # Distribución de costos
    cost_distribution = fields.Selection([
        ('50_50', '50% Comprador - 50% Vendedor'),
        ('100_buyer', '100% Comprador'),
        ('100_seller', '100% Vendedor'),
        ('custom', 'Personalizado'),
    ], string="Distribución de Costos", default='50_50', tracking=True)
    
    buyer_percentage = fields.Float("Porcentaje Comprador (%)", default=50.0, tracking=True)
    seller_percentage = fields.Float("Porcentaje Vendedor (%)", default=50.0, tracking=True)
    
    # =================== VALORES CALCULADOS NOTARIALES ===================
    
    # Componentes individuales del cálculo
    notarial_rights_value = fields.Monetary("Derechos Notariales", currency_field='currency_id',
                                           compute='_compute_notarial_rights_value', store=True,
                                           help="Valor de derechos notariales calculado")
    
    biometric_value = fields.Monetary("Valor Autenticación Biométrica", currency_field='currency_id',
                                     compute='_compute_biometric_value', store=True,
                                     help="Costo de autenticación biométrica por persona")
    
    copies_cost = fields.Monetary("Costo Copias", currency_field='currency_id',
                                 compute='_compute_copies_cost', store=True,
                                 help="Costo de copias matriz y protocolo")
    
    iva_value = fields.Monetary("IVA (19%)", currency_field='currency_id',
                               compute='_compute_iva_value', store=True,
                               help="IVA sobre conceptos gravados")
    
    snr_recaudo_value = fields.Monetary("Recaudo SNR", currency_field='currency_id',
                                       compute='_compute_recaudos', store=True,
                                       help="Recaudo Superintendencia")
    
    fondo_recaudo_value = fields.Monetary("Recaudo Fondo", currency_field='currency_id',
                                         compute='_compute_recaudos', store=True,
                                         help="Recaudo Fondo")
    
    stamp_tax_value = fields.Monetary("Impuesto de Timbre", currency_field='currency_id',
                                     compute='_compute_stamp_tax', store=True,
                                     help="Impuesto de timbre calculado")
    
    retention_value = fields.Monetary("Retención en la Fuente", currency_field='currency_id',
                                     compute='_compute_retention_value', store=True,
                                     help="Retención en la fuente que la notaría recauda")
    
    # Totales
    total_notarial_cost = fields.Monetary("Costo Total Notarial", currency_field='currency_id',
                                         compute='_compute_total_notarial_cost', store=True,
                                         help="Costo total de la liquidación notarial")
    
    buyer_cost = fields.Monetary("Costo Comprador", currency_field='currency_id',
                                compute='_compute_cost_distribution', store=True,
                                help="Costo que asume el comprador")
    
    seller_cost = fields.Monetary("Costo Vendedor", currency_field='currency_id',
                                 compute='_compute_cost_distribution', store=True,
                                 help="Costo que asume el vendedor")

    search_text = fields.Text(string='Texto de Búsqueda', compute='_compute_search_text', store=True, index=True)
    recent_view_ids = fields.Many2many('website.visitor', 'property_recent_views_rel', 'property_id', 'visitor_id', string='Visitantes Recientes')
    
    # =================== MÉTODOS DE CONVERSIÓN ===================
    
    @api.depends('property_area', 'unit_of_measure')
    def _compute_area_in_m2(self):
        """Convierte el área ingresada por el usuario a metros cuadrados para cálculos"""
        for record in self:
            if not record.property_area:
                record.area_in_m2 = 0.0
                continue
                
            if record.unit_of_measure == "hectare":
                record.area_in_m2 = record.property_area * 10000
            elif record.unit_of_measure == "yard":
                record.area_in_m2 = record.property_area * 0.836127
            else:  # metros
                record.area_in_m2 = record.property_area

    @api.depends('unit_of_measure')
    def _compute_unit_iso_info(self):
        """Generar información ISO de unidades"""
        for record in self:
            if record.unit_of_measure == "hectare":
                record.unit_iso_code = "ha"
                record.unit_display_name = "Hectárea"
            elif record.unit_of_measure == "yard":
                record.unit_iso_code = "yd²"
                record.unit_display_name = "Yarda Cuadrada"
            else:  # metros
                record.unit_iso_code = "m²"
                record.unit_display_name = "Metro Cuadrado"

    # NUEVO: Compute para etiqueta de unidad
    @api.depends('unit_of_measure')
    def _compute_unit_label(self):
        """Generar etiqueta para mostrar con /"""
        for record in self:
            if record.unit_of_measure == "hectare":
                record.unit_label = "/ha"
            elif record.unit_of_measure == "yard":
                record.unit_label = "/yd²"
            else:  # metros
                record.unit_label = "/m²"

    # =================== MÉTODOS DE CÁLCULO DE PRECIOS - OPTIMIZADOS ===================
    
    @api.depends('price_per_unit', 'unit_of_measure', 'area_in_m2')
    def _compute_unit_price_references(self):
        """Calcular precios de referencia en todas las unidades - CORREGIDO"""
        for record in self:
            if not record.price_per_unit or not record.area_in_m2:
                record.price_per_m2_ref = 0.0
                record.price_per_hectare_ref = 0.0
                record.price_per_yard_ref = 0.0
                continue
                
            # Calcular el precio total primero
            total_price = record.price_per_unit * record.property_area
            
            # Ahora convertir a precio por unidad en cada medida
            record.price_per_m2_ref = total_price / record.area_in_m2 if record.area_in_m2 > 0 else 0
            record.price_per_hectare_ref = total_price / (record.area_in_m2 / 10000) if record.area_in_m2 > 0 else 0
            record.price_per_yard_ref = total_price / (record.area_in_m2 / 0.836127) if record.area_in_m2 > 0 else 0

    @api.depends('price_per_unit', 'property_area', 'property_price_type', 'discount', 'discount_type')
    def _calc_price(self):
        """Método principal para calcular precios de venta - SIMPLIFICADO"""
        for record in self:
            if record.property_price_type == 'sft':
                if record.price_per_unit and record.property_area:
                    base_price = record.price_per_unit * record.property_area
                else:
                    base_price = 0.0
            else:
                base_price = record.net_price or 0.0
            
            record.price_before_discount = base_price
            
            if record.discount and record.discount > 0:
                if record.discount_type == 'percentage':
                    discount_amount = base_price * (record.discount / 100)
                else:  # amount
                    discount_amount = record.discount
                
                final_price = base_price - discount_amount
            else:
                final_price = base_price
            record.net_price = final_price

    @api.depends('rental_price_per_unit', 'property_area', 'rental_price_type', 'rental_discount', 'rental_discount_type')
    def _calc_rental_price(self):
        """Método principal para calcular precios de arriendo - SIMPLIFICADO"""
        for record in self:
            if record.rental_price_type == 'sft':
                if record.rental_price_per_unit and record.property_area:
                    base_rental_price = record.rental_price_per_unit * record.property_area
                else:
                    base_rental_price = 0.0
            else:
                # Precio fijo - usar el valor ya establecido
                base_rental_price = record.net_rental_price or 0.0
            
            # Precio antes del descuento
            record.rental_price_before_discount = base_rental_price
            
            # Aplicar descuento
            if record.rental_discount and record.rental_discount > 0:
                if record.rental_discount_type == 'percentage':
                    discount_amount = base_rental_price * (record.rental_discount / 100)
                else:  # amount
                    discount_amount = record.rental_discount
                
                final_rental_price = base_rental_price - discount_amount
            else:
                final_rental_price = base_rental_price
            
            # Asignar precio final de arriendo
            record.net_rental_price = final_rental_price

    @api.depends('net_price', 'net_rental_price')
    def _auto_fill_range_fields(self):
        """Auto-llenar campos de rango si están vacíos"""
        for record in self:
            if not record.sale_value_from and record.net_price:
                record.sale_value_from = record.net_price
            
            if not record.rent_value_from and record.net_rental_price:
                record.rent_value_from = record.net_rental_price

    @api.depends("maintenance_charges", "utility_ids")
    def _calc_total(self):
        for rec in self:
            maintenance_charges = rec.maintenance_charges
            if rec.maintenance_type != "fix":
                maintenance_charges = rec.maintenance_charges * rec.area_in_m2 or 0
            rec.total_maintenance = maintenance_charges + sum(rec.utility_ids.mapped("price"))
            rec.total_cost = rec.total_maintenance + rec.net_price

    def _calc_utilities(self):
        for rec in self:
            rec.total_utilities = sum(rec.utility_ids.mapped('price'))

    # =================== MÉTODOS AUXILIARES NOTARIALES ===================
    
    def _get_notarial_constants(self):
        """Retorna las constantes notariales según Resolución 00585 de 2025"""
        return {
            'ACTO_SIN_CUANTIA': 86200.0,
            'ACTO_CUANTIA_MINIMA': 29400.0,
            'ACTO_CUANTIA_UMBRAL': 246700.0,
            'ACTO_CUANTIA_PORCENTAJE': 0.3,  # 3×1000
            'HERENCIA_UMBRAL_UVB': 56238.53,  # 1591,90 UVB en pesos 2025
            'HERENCIA_PORCENTAJE': 0.35,  # 3.5×1000
            'FOLIO_ADICIONAL_VALOR': 3500.0,
            'COPIA_AUTENTICA': 5300.0,
            'COPIA_SIMPLE': 700.0,
            'BIOMETRIC_AUTHENTICATION': 4600.0,
        }
    
    def _get_recaudo_ranges(self):
        """Retorna los rangos de recaudo SNR y Fondo según tabla oficial"""
        return [
            {'min': 0, 'max': 100000000, 'snr': 9200, 'fondo': 9200},
            {'min': 100000001, 'max': 300000000, 'snr': 13800, 'fondo': 13800},
            {'min': 300000001, 'max': 500000000, 'snr': 20900, 'fondo': 20900},
            {'min': 500000001, 'max': 1000000000, 'snr': 25200, 'fondo': 25200},
            {'min': 1000000001, 'max': 1500000000, 'snr': 34300, 'fondo': 34300},
            {'min': 1500000001, 'max': float('inf'), 'snr': 46000, 'fondo': 46000},
        ]
    
    def _get_act_factor(self):
        """Retorna el factor de reducción según tipo de acto notarial"""
        factors = {
            # Compraventas normales - sin reducción
            'compraventa_inmueble': 1.0,
            'compraventa_hipoteca_abierta': 1.0,
            'compraventa_retroventa': 1.0,
            'compraventa_posesion': 1.0,
            'compraventa_derechos_cuota': 1.0,
            
            # Compraventas VIS - 50% reducción
            'compraventa_vis': 0.5,
            'compraventa_vip_subsidio': 0.5,
            'compraventa_vip_ahorradores': 0.5,
            
            # Hipotecas normales - sin reducción
            'hipoteca_normal': 1.0,
            'hipoteca_abierta': 1.0,
            'hipoteca_abierta_limite': 1.0,
            'hipoteca_abierta_sin_limite': 1.0,
            
            # Hipotecas con reducción
            'hipoteca_ley546_subsidio': 0.1,  # 10%
            'hipoteca_ley546_sin_subsidio': 0.4,  # 40%
            'hipoteca_vis': 0.5,  # 50%
            
            # Cancelaciones - sin reducción
            'cancelacion_hipoteca': 1.0,
            'cancelacion_hipoteca_abierta': 1.0,
            'cancelacion_hipoteca_indeterminada': 1.0,
            'cancelacion_hipoteca_ley546': 1.0,
            'cancelacion_hipoteca_ley546_subsidio': 1.0,
            'cancelacion_hipoteca_ley546_sin_subsidio': 1.0,
            'cancelacion_hipoteca_mayor_extension': 1.0,
            'cancelacion_parcial_hipoteca': 1.0,
            
            # Herencias - sin reducción (se calcula especial)
            'liquidacion_herencia': 1.0,
            'liquidacion_sociedad_conyugal': 1.0,
            'particion_herencia': 1.0,
            'adjudicacion_herencia': 1.0,
        }
        return factors.get(self.notarial_act_type, 1.0)
    
    def _is_cancellation_act(self):
        """Verifica si es un acto de cancelación"""
        return self.notarial_act_type and self.notarial_act_type.startswith('cancelacion')
    
    def _is_inheritance_act(self):
        """Verifica si es un acto de herencia"""
        inheritance_acts = [
            'liquidacion_herencia',
            'liquidacion_sociedad_conyugal', 
            'particion_herencia',
            'adjudicacion_herencia'
        ]
        return self.notarial_act_type in inheritance_acts
    
    def _get_copy_factor(self):
        """Retorna el factor de reducción para copias en actos VIS"""
        vis_acts = ['compraventa_vis', 'compraventa_vip_subsidio', 'compraventa_vip_ahorradores', 'hipoteca_vis']
        return 0.5 if self.notarial_act_type in vis_acts else 1.0
    
    def _get_notarial_cuantia(self):
        """Obtiene la cuantía para cálculos notariales según fuente elegida"""
        if self.cuantia_source == 'sale_value':
            return self.sale_value_from or 0.0
        elif self.cuantia_source == 'custom_amount':
            return self.notarial_amount or 0.0
        else:  # auto
            return self.sale_value_from or self.notarial_amount or 0.0
    
    def _round_centena(self, value):
        """Redondea a la centena legal (art. 56 D‑1069/15)"""
        return float((Decimal(str(value)) / 100).to_integral_value(ROUND_HALF_UP) * 100)

    # =================== MÉTODOS COMPUTADOS NOTARIALES ===================
    
    @api.depends('biometric_persons')
    def _compute_biometric_value(self):
        """Calcula el valor de autenticación biométrica por persona"""
        for record in self:
            constants = record._get_notarial_constants()
            num_personas = max(record.biometric_persons, 2)  # Mínimo 2 personas
            record.biometric_value = constants['BIOMETRIC_AUTHENTICATION'] * num_personas
    
    @api.depends('sale_value_from', 'notarial_amount', 'notarial_act_type', 'cuantia_source')
    def _compute_notarial_rights_value(self):
        """Calcula los derechos notariales según el tipo de acto"""
        for record in self:
            cuantia = record._get_notarial_cuantia()
            
            if not cuantia and not record._is_cancellation_act():
                record.notarial_rights_value = 0.0
                continue
                
            constants = record._get_notarial_constants()
            
            # Para cancelaciones, usar acto sin cuantía
            if record._is_cancellation_act():
                derechos_base = constants['ACTO_SIN_CUANTIA']
            
            # Para herencias, aplicar lógica especial (Art. 2 literal c)
            elif record._is_inheritance_act():
                umbral_herencia = constants['HERENCIA_UMBRAL_UVB']
                if cuantia <= umbral_herencia:
                    derechos_base = constants['ACTO_SIN_CUANTIA']
                else:
                    excedente = cuantia - umbral_herencia
                    excedente_valor = record._round_centena(excedente * constants['HERENCIA_PORCENTAJE'] / 100)
                    derechos_base = constants['ACTO_SIN_CUANTIA'] + excedente_valor
            
            # Para compraventas e hipotecas con cuantía (Art. 2 literal b)
            else:
                if cuantia <= constants['ACTO_CUANTIA_UMBRAL']:
                    derechos_base = constants['ACTO_CUANTIA_MINIMA']
                else:
                    excedente = cuantia - constants['ACTO_CUANTIA_UMBRAL']
                    excedente_valor = record._round_centena(excedente * constants['ACTO_CUANTIA_PORCENTAJE'] / 100)
                    derechos_base = constants['ACTO_CUANTIA_MINIMA'] + excedente_valor
            
            # Aplicar factor de reducción según tipo de acto
            factor = record._get_act_factor()
            derechos_final = record._round_centena(derechos_base * factor)
            
            record.notarial_rights_value = derechos_final
    
    @api.depends('matriz_copies', 'protocolo_copies', 'notarial_act_type')
    def _compute_copies_cost(self):
        """Calcula el costo de copias matriz y protocolo"""
        for record in self:
            constants = record._get_notarial_constants()
            copy_factor = record._get_copy_factor()
            
            # Copias matriz - se cobran desde 1
            copias_matriz = record.matriz_copies * constants['COPIA_AUTENTICA'] * copy_factor
            
            # Copias protocolo - se cobran desde 1
            copias_protocolo = record.protocolo_copies * constants['COPIA_AUTENTICA'] * copy_factor
            
            record.copies_cost = copias_matriz + copias_protocolo
    
    @api.depends('notarial_rights_value', 'biometric_value', 'copies_cost')
    def _compute_iva_value(self):
        """Calcula el IVA SOLO sobre conceptos gravados"""
        for record in self:
            base_imponible = (
                record.notarial_rights_value + 
                record.biometric_value + 
                record.copies_cost
            )
            record.iva_value = record._round_centena(base_imponible * 0.19)
    
    @api.depends('sale_value_from', 'notarial_amount', 'notarial_act_type', 'cuantia_source')
    def _compute_recaudos(self):
        """Calcula recaudos SNR y Fondo según rangos de cuantía"""
        for record in self:
            cuantia = record._get_notarial_cuantia()
            
            if not cuantia and not record._is_cancellation_act():
                record.snr_recaudo_value = 0.0
                record.fondo_recaudo_value = 0.0
                continue
            
            rangos = record._get_recaudo_ranges()
            
            # Para cancelaciones y herencias sin cuantía, usar rango mínimo
            if record._is_cancellation_act() or (record._is_inheritance_act() and cuantia == 0):
                record.snr_recaudo_value = rangos[0]['snr']
                record.fondo_recaudo_value = rangos[0]['fondo']
                continue
            
            # Buscar el rango correspondiente
            for rango in rangos:
                if rango['min'] <= cuantia <= rango['max']:
                    record.snr_recaudo_value = rango['snr']
                    record.fondo_recaudo_value = rango['fondo']
                    break
            else:
                # Si no encuentra rango, usar el último (para cuantías muy altas)
                record.snr_recaudo_value = rangos[-1]['snr']
                record.fondo_recaudo_value = rangos[-1]['fondo']
    
    @api.depends('sale_value_from', 'notarial_amount', 'notarial_act_type', 'cuantia_source')
    def _compute_stamp_tax(self):
        """Calcula el impuesto de timbre"""
        for record in self:
            cuantia = record._get_notarial_cuantia()
            
            # Solo para compraventas con cuantía alta
            if (not cuantia or 
                not record.notarial_act_type.startswith('compraventa')):
                record.stamp_tax_value = 0.0
                continue
            
            # Umbral mínimo para timbre
            TIMBRE_UMBRAL = 133000000  # 133 SMLV aproximadamente
            TIMBRE_PORCENTAJE = 0.5  # 0.5%
            
            if cuantia >= TIMBRE_UMBRAL:
                record.stamp_tax_value = record._round_centena(cuantia * TIMBRE_PORCENTAJE / 100)
            else:
                record.stamp_tax_value = 0.0
    
    @api.depends('sale_value_from', 'notarial_amount', 'sale_with_natural_person', 'partner_id', 'notarial_act_type', 'is_nonprofit_buyer', 'cuantia_source')
    def _compute_retention_value(self):
        """Retención se SUMA al total porque la notaría la recauda"""
        for record in self:
            cuantia = record._get_notarial_cuantia()
            
            if (not cuantia or 
                not record.sale_with_natural_person or 
                not record.notarial_act_type.startswith('compraventa') or
                record.is_nonprofit_buyer):
                record.retention_value = 0.0
                continue
            
            if record.partner_id and hasattr(record.partner_id, 'document_type') and record.partner_id.document_type == '31':
                record.retention_value = 0.0
                continue
            
            # Retención 1% sobre la cuantía
            RETENCION_PORCENTAJE = 1.0
            record.retention_value = record._round_centena(cuantia * RETENCION_PORCENTAJE / 100)
    
    @api.depends('notarial_rights_value', 'iva_value', 'snr_recaudo_value', 'fondo_recaudo_value', 
                 'retention_value', 'stamp_tax_value', 'copies_cost', 'biometric_value')
    def _compute_total_notarial_cost(self):
        """Calcula el costo total - LA RETENCIÓN SE SUMA porque la notaría la recauda"""
        for record in self:
            # TODOS LOS VALORES SE SUMAN
            record.total_notarial_cost = (
                record.notarial_rights_value +     # Derechos notariales
                record.biometric_value +           # Autenticación biométrica  
                record.copies_cost +               # Copias matriz y protocolo
                record.iva_value +                 # IVA sobre conceptos gravados
                record.snr_recaudo_value +         # Recaudo SNR
                record.fondo_recaudo_value +       # Recaudo Fondo
                record.stamp_tax_value +           # Impuesto de timbre
                record.retention_value             # Retención (SE SUMA - notaría recauda)
            )
    
    @api.depends('total_notarial_cost', 'cost_distribution', 'buyer_percentage', 'seller_percentage', 'retention_value')
    def _compute_cost_distribution(self):
        """Calcula la distribución de costos - LA RETENCIÓN SIEMPRE AL VENDEDOR"""
        for record in self:
            total = record.total_notarial_cost
            total_sin_retencion = total - record.retention_value
            
            if record.cost_distribution == '50_50':
                record.buyer_cost = total_sin_retencion * 0.5
                record.seller_cost = (total_sin_retencion * 0.5) + record.retention_value
                
            elif record.cost_distribution == '100_buyer':
                record.buyer_cost = total_sin_retencion
                record.seller_cost = record.retention_value
                
            elif record.cost_distribution == '100_seller':
                record.buyer_cost = 0.0
                record.seller_cost = total
                
            elif record.cost_distribution == 'custom':
                record.buyer_cost = total_sin_retencion * (record.buyer_percentage / 100)
                record.seller_cost = (total_sin_retencion * (record.seller_percentage / 100)) + record.retention_value
                
            else:
                record.buyer_cost = total_sin_retencion * 0.5
                record.seller_cost = (total_sin_retencion * 0.5) + record.retention_value

    # =================== ONCHANGE METHODS - OPTIMIZADOS ===================
    
    @api.onchange('property_area', 'unit_of_measure')
    def _onchange_property_area(self):
        """Recalcular conversiones cuando cambia el área o unidad"""
        self._compute_area_in_m2()

    @api.onchange('price_per_unit', 'property_area')
    def _onchange_price_per_unit(self):
        """Recalcular precios cuando cambia precio por unidad"""
        if self.property_price_type == 'sft':
            if self.price_per_unit and self.property_area:
                self.net_price = self.price_per_unit * self.property_area

    @api.onchange('net_price', 'property_area')
    def _onchange_calculate_price_per_unit_from_total(self):
        """Calcular precio por unidad cuando cambia precio total"""
        if self.net_price and self.property_area and self.property_area > 0:
            calculated_price = self.net_price / self.property_area
            if not self.price_per_unit:  # Solo actualizar si está vacío
                self.price_per_unit = calculated_price

    @api.onchange('rental_price_per_unit', 'property_area')
    def _onchange_rental_price_per_unit(self):
        """Recalcular precios arriendo cuando cambia precio por unidad"""
        if self.rental_price_type == 'sft':
            if self.rental_price_per_unit and self.property_area:
                self.net_rental_price = self.rental_price_per_unit * self.property_area

    @api.onchange('net_rental_price', 'property_area')
    def _onchange_calculate_rental_price_per_unit_from_total(self):
        """Calcular precio arriendo por unidad cuando cambia precio total"""
        if self.net_rental_price and self.property_area and self.property_area > 0:
            calculated_rental_price = self.net_rental_price / self.property_area
            if not self.rental_price_per_unit:  # Solo actualizar si está vacío
                self.rental_price_per_unit = calculated_rental_price

    @api.onchange('cost_distribution')
    def _onchange_cost_distribution(self):
        """Actualiza porcentajes según el tipo de distribución"""
        if self.cost_distribution == '50_50':
            self.buyer_percentage = 50.0
            self.seller_percentage = 50.0
        elif self.cost_distribution == '100_buyer':
            self.buyer_percentage = 100.0
            self.seller_percentage = 0.0
        elif self.cost_distribution == '100_seller':
            self.buyer_percentage = 0.0
            self.seller_percentage = 100.0

    @api.onchange('buyer_percentage')
    def _onchange_buyer_percentage(self):
        """Actualiza porcentaje vendedor automáticamente"""
        if self.cost_distribution == 'custom':
            self.seller_percentage = 100.0 - self.buyer_percentage

    @api.onchange('seller_percentage')
    def _onchange_seller_percentage(self):
        """Actualiza porcentaje comprador automáticamente"""
        if self.cost_distribution == 'custom':
            self.buyer_percentage = 100.0 - self.seller_percentage

    @api.onchange('sale_value_from')
    def _onchange_sale_price_auto_notarial(self):
        """Auto-llenar cuantía notarial"""
        if self.sale_value_from and not self.notarial_amount:
            self.notarial_amount = self.sale_value_from

    # NUEVO: OnChange para auto-llenar rangos
    @api.onchange('net_price')
    def _onchange_auto_fill_sale_range(self):
        """Auto-llenar rango de venta"""
        if self.net_price and not self.sale_value_from:
            self.sale_value_from = self.net_price

    @api.onchange('net_rental_price')
    def _onchange_auto_fill_rental_range(self):
        """Auto-llenar rango de arriendo"""
        if self.net_rental_price and not self.rent_value_from:
            self.rent_value_from = self.net_rental_price

    # =================== MÉTODOS EXISTENTES ===================
    
    def _maintenance_count(self):
        maintenance_obj = self.env['repair.order']
        for unit in self:
            maintenance_ids = maintenance_obj.search([('product_id.product_tmpl_id', '=', unit.id)])
            unit.maintenance_count = len(maintenance_ids)

    def _reservation_count(self):
        reservation_obj = self.env["property.reservation"]
        for property_id in self:
            property_id.reservation_count = len(reservation_obj.search([("property_id", "=", property_id.id)]))

    @api.depends('name', 'default_code', 'street', 'city', 'department', 
                 'municipality', 'neighborhood', 'region_id.name')
    def _compute_search_text(self):
        """Crear texto concatenado para búsqueda full-text"""
        for rec in self:
            search_parts = []
            if rec.name:
                search_parts.append(rec.name)
            if rec.default_code:
                search_parts.append(rec.default_code)
            if rec.street:
                search_parts.append(rec.street)
            if rec.city:
                search_parts.append(rec.city)
            if rec.department:
                search_parts.append(rec.department)
            if rec.municipality:
                search_parts.append(rec.municipality)
            if rec.neighborhood:
                search_parts.append(rec.neighborhood)
            if rec.region_id:
                search_parts.append(rec.region_id.name)
            
            rec.search_text = ' '.join(filter(None, search_parts)).lower()

    # =================== COMPUTED METHODS EXISTENTES ===================
    
    @api.depends('partner_id')
    def _compute_user_id(self):
        for order in self:
            if order.partner_id and not (order._origin.id and order.user_consing_id):
                order.user_consing_id = (
                    order.partner_id.user_id.partner_id
                    or order.partner_id.commercial_partner_id.user_id.partner_id
                    or (self.env.user.has_group('sales_team.group_sale_salesman') and self.env.user.partner_id)
                )

    @api.depends('email_from')
    def _compute_email_state(self):
        for lead in self:
            email_state = False
            if lead.email_from:
                email_state = 'incorrect'
                for email in email_split(lead.email_from):
                    if mail_validation.mail_validate(email):
                        email_state = 'correct'
                        break
            lead.email_state = email_state

    @api.depends('partner_id')
    def _compute_contact_name(self):
        for lead in self:
            if not lead.contact_name or lead.partner_id.name:
                lead.contact_name = lead.partner_id.name

    @api.depends('partner_id')
    def _compute_mobile(self):
        for lead in self:
            if not lead.mobile or lead.partner_id.mobile:
                lead.mobile = lead.partner_id.mobile

    @api.depends('phone', 'country_id.code')
    def _compute_phone_state(self):
        for lead in self:
            phone_status = False
            if lead.phone:
                country_code = lead.country_id.code if lead.country_id and lead.country_id.code else None
                try:
                    if phone_validation.phone_parse(lead.phone, country_code):
                        phone_status = 'correct'
                except UserError:
                    phone_status = 'incorrect'
            lead.phone_state = phone_status

    @api.depends('partner_id.phone')
    def _compute_phone(self):
        for lead in self:
            if lead.partner_id.phone and lead._get_partner_phone_update():
                lead.phone = lead.partner_id.phone

    @api.depends('lang_id')
    def _compute_lang_active_count(self):
        self.lang_active_count = len(self.env['res.lang'].get_installed())

    @api.depends('partner_id')
    def _compute_lang_id(self):
        lang_codes = [code for code in self.mapped('partner_id.lang') if code]
        if lang_codes:
            lang_id_by_code = dict(
                (code, self.env['res.lang']._lang_get(code))
                for code in lang_codes
            )
        else:
            lang_id_by_code = {}
        for lead in self.filtered('partner_id'):
            lead.lang_id = lang_id_by_code.get(lead.partner_id.lang, False)

    # =================== ACTIONS ===================
    
    def action_reservation(self):
        reservation_obj = self.env["property.reservation"]
        reservation_ids = []
        for rec in self:
            reservation_id = reservation_obj.create({
                "partner_id": rec.partner_id.id,
                "region_id": rec.region_id.id,
                "project_id": rec.project_worksite_id.id,
                "property_id": rec.id,
                "property_code": rec.default_code,
                "floor": rec.floor,
                "net_price": rec.net_price,
                "address": rec.street,
                "property_type_id": rec.property_type_id.id,
                "property_area": rec.property_area,
                "price_per_m": rec.price_per_unit,
                "property_price_type": rec.property_price_type,
            })
            reservation_ids.append(reservation_id.id)

        return {
            "type": "ir.actions.act_window",
            "res_model": reservation_obj._name,
            "view_type": "form",
            "view_mode": "form",
            "target": "current",
            "res_id": reservation_ids and reservation_ids[0] or False
        }

    def view_maintenance(self):
        maintenance_ids = self.env['repair.order'].search([('product_id.product_tmpl_id', 'in', self.ids)])
        return {
            'name': _('Solicitudes de Mantenimiento'),
            'domain': [('id', 'in', maintenance_ids.ids)],
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'repair.order',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'view_id': False,
            'target': 'current',
        }

    def view_reservations(self):
        reservation_obj = self.env["property.reservation"]
        reservations_ids = reservation_obj.search([("property_id", "=", self.ids)])
        reservations = []
        for obj in reservations_ids:
            reservations.append(obj.id)
        return {
            "name": _("Reservas"),
            "domain": [("id", "in", reservations)],
            "view_type": "form",
            "view_mode": "list,form",
            "res_model": "property.reservation",
            "type": "ir.actions.act_window",
            "nodestroy": True,
            "view_id": False,
            "target": "current",
        }

    # =================== CRUD METHODS ===================
    
    # =================== MÉTODOS DE GEOLOCALIZACIÓN ===================

    @api.depends('street', 'street2', 'city_id', 'region_id', 'state_id', 'country_id', 'zip')
    def _compute_full_address_geo(self):
        """Construye la dirección completa para geocodificación"""
        for prop in self:
            parts = []

            # Agregar componentes de dirección en orden
            if prop.street:
                parts.append(prop.street)
            if prop.street2:
                parts.append(prop.street2)
            if prop.region_id and prop.region_id.name:
                parts.append(prop.region_id.name)
            if prop.city_id and prop.city_id.name:
                parts.append(prop.city_id.name)
            elif prop.city:  # Fallback al campo char si no hay city_id
                parts.append(prop.city)
            if prop.state_id and prop.state_id.name:
                parts.append(prop.state_id.name)
            if prop.country_id and prop.country_id.name:
                parts.append(prop.country_id.name)
            if prop.zip:
                parts.append(prop.zip)

            prop.full_computed_address = ', '.join(parts) if parts else ''



    def _geocode_address(self, address):
        """
        Obtiene coordenadas GPS usando Nominatim (OpenStreetMap)
        Alternativa gratuita a Google Maps API
        """
        if not address:
            return False

        try:
            # Usar Nominatim de OpenStreetMap (gratuito, sin API key)
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': address,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            headers = {
                'User-Agent': 'Odoo Real Estate Module/1.0'  # Requerido por Nominatim
            }

            response = requests.get(url, params=params, headers=headers, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    result = data[0]
                    return {
                        'lat': float(result['lat']),
                        'lng': float(result['lon'])
                    }

        except requests.RequestException as e:
            _logger.error(f"Error en geocodificación: {e}")
        except (KeyError, ValueError, IndexError) as e:
            _logger.error(f"Error procesando respuesta de geocodificación: {e}")

        return False

    def action_geocode(self):
        """Acción manual para geocodificar la dirección"""
        self.ensure_one()

        if not self.full_computed_address:
            raise UserError(_("No hay dirección completa para geocodificar"))

        coords = self._geocode_address(self.full_computed_address)
        if coords:
            self.write({
                'latitude': coords['lat'],
                'longitude': coords['lng'],
                'geocoding_status': 'success'
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Geocodificación exitosa'),
                    'message': _('Coordenadas actualizadas: %.6f, %.6f') % (coords['lat'], coords['lng']),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            self.geocoding_status = 'failed'
            raise UserError(_("No se pudieron obtener las coordenadas para esta dirección"))

    def action_open_map(self):
        """Abre la ubicación en Google Maps"""
        self.ensure_one()

        if not (self.latitude and self.longitude):
            raise UserError(_("Este inmueble no tiene coordenadas GPS"))

        url = f"https://www.google.com/maps/search/?api=1&query={self.latitude},{self.longitude}"

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    @api.onchange('street', 'city_id', 'region_id')
    def _onchange_address_geocode(self):
        """Marca para recalcular coordenadas cuando cambia la dirección"""
        if self.street or self.city_id or self.region_id:
            self.geocoding_status = 'pending'

    @api.model
    def geocode_all_pending(self):
        """Método para geocodificar todas las propiedades pendientes (para cron)"""
        pending_props = self.search([
            ('is_property', '=', True),
            ('geocoding_status', 'in', ['pending', 'failed']),
            ('full_computed_address', '!=', False)
        ], limit=50)  # Limitar para no sobrecargar

        for prop in pending_props:
            try:
                prop._compute_geolocation()
            except Exception as e:
                _logger.error(f"Error geocodificando {prop.name}: {e}")

        return True

    @api.model
    def create(self, vals):
        record = super(Property, self).create(vals)
        record._handle_main_owner_and_billing_address()
        record._auto_associate_partner_by_vat()
        return record

    def write(self, vals):
        result = super(Property, self).write(vals)
        if any(field in vals for field in ['street', 'street2', 'zip', 'city', 'city_id', 'state_id', 'country_id', 'region_id']):
            self._handle_main_owner_and_billing_address()
        return result

    def _handle_main_owner_and_billing_address(self):
        for record in self:
            if not record.partner_id and record.is_property:
                record.partner_id = record._create_main_owner()
            record.billing_address_id = record._create_or_update_billing_address()

    def _create_main_owner(self):
        if self.contact_name:
            return self.env['res.partner'].create({
                'name': self.contact_name,
                'type': 'contact',
                'street': self.street,
                'street2': self.street2,
                'zip': self.zip,
                'city': self.city,
                'vat': self.vat,
                'l10n_latam_identification_type_id': self.l10n_latam_identification_type_id.id if self.l10n_latam_identification_type_id else False,
                'city_id': self.city_id.id if self.city_id else False,
                'state_id': self.state_id.id if self.state_id else False,
                'country_id': self.country_id.id if self.country_id else False,
            })
        return False

    def _create_or_update_billing_address(self):
        self.ensure_one()
        billing_address = self.env['res.partner'].search([
            ('parent_id', '=', self.partner_id.id),
            ('type', '=', 'invoice'),
            ('name', '=', f"{self.street} - {self.name}")
        ], limit=1)

        vals = {
            'name': f"{self.street} - {self.name}",
            'type': 'invoice',
            'parent_id': self.partner_id.id,
            'street': self.street,
            'street2': self.street2,
            'zip': self.zip,
            'city': self.city,
            'partner_latitude': self.latitude,
            'partner_longitude': self.longitude,
            'city_id': self.city_id.id if self.city_id else False,
            'state_id': self.state_id.id if self.state_id else False,
            'country_id': self.country_id.id if self.country_id else False,
            'property_product_ids': [(4, self.id)]
        }

        if billing_address:
            billing_address.write(vals)
        else:
            billing_address = self.env['res.partner'].create(vals)

        return billing_address

    def _auto_associate_partner_by_vat(self):
        """Auto-asociar tercero por número de documento"""
        self.ensure_one()
        if self.vat and not self.partner_id:
            partner = self.env['res.partner'].search([('vat', '=', self.vat)], limit=1)
            if partner:
                self.partner_id = partner.id

    def _get_partner_phone_update(self):
        self.ensure_one()
        if self.partner_id and self.phone != self.partner_id.phone:
            lead_phone_formatted = self._phone_format(fname='phone') or self.phone or False
            partner_phone_formatted = self.partner_id._phone_format(fname='phone') or self.partner_id.phone or False
            return lead_phone_formatted != partner_phone_formatted
        return False

    def _inverse_phone(self):
        for lead in self:
            if lead._get_partner_phone_update():
                lead.partner_id.phone = lead.phone

    # =================== CONSTRAINTS ===================
    
    @api.constrains('buyer_percentage', 'seller_percentage')
    def _check_percentage_total(self):
        """Valida que los porcentajes sumen 100%"""
        for record in self:
            if record.cost_distribution == 'custom':
                total = record.buyer_percentage + record.seller_percentage
                if abs(total - 100.0) > 0.01:
                    raise UserError("Los porcentajes de comprador y vendedor deben sumar 100%")

    @api.constrains('biometric_persons')
    def _check_biometric_persons(self):
        """Valida que las personas biométricas sean mínimo 2"""
        for record in self:
            if record.biometric_persons < 2:
                raise UserError("El número de personas para biometría debe ser mínimo 2")

    @api.constrains('property_area')
    def _check_property_area_positive(self):
        """Validar que el área sea positiva"""
        for record in self:
            if record.property_area and record.property_area <= 0:
                raise ValidationError("El área de la propiedad debe ser mayor a cero")

    # =================== UTILITY METHODS - OPTIMIZADOS ===================

    def get_current_unit_symbol(self):
        """Obtener símbolo de la unidad actual"""
        return self.unit_iso_code or "m²"

    def get_current_unit_name(self):
        """Obtener nombre de la unidad actual"""
        return self.unit_display_name or "Metro Cuadrado"

    def get_current_unit_label(self):
        """Obtener etiqueta de la unidad actual con /"""
        return self.unit_label or "/m²"

    def get_price_per_unit_formatted(self):
        """Obtener precio por unidad formateado"""
        price = self.price_per_unit or 0
        label = self.get_current_unit_label()
        return f"${price:,.2f}{label}"

    def get_rental_price_per_unit_formatted(self):
        """Obtener precio arriendo por unidad formateado"""
        price = self.rental_price_per_unit or 0
        label = self.get_current_unit_label()
        return f"${price:,.2f}{label}"

    @api.model
    def get_property_summary(self):
        """Obtener resumen de características para mostrar en cards"""
        summary = []
        if self.num_bedrooms:
            summary.append(f"{self.num_bedrooms} hab.")
        if self.num_bathrooms:
            summary.append(f"{self.num_bathrooms} baños")
        if self.property_area:
            unit = dict(self._fields['unit_of_measure'].selection).get(self.unit_of_measure, 'm²')
            summary.append(f"{self.property_area} {unit}")
        if self.floor_number:
            summary.append(f"Piso {self.floor_number}")
        
        return " • ".join(summary)
    
    # =================== CONSTRAINTS ===================
    
    _sql_constraints = [
        (
            "unique_property_code",
            "UNIQUE (default_code,project_worksite_id,region_id)",
            "¡El código de propiedad debe ser único!",
        ),
        (
            "unique_property_project_code",
            "UNIQUE (default_code,project_worksite_id)",
            "¡El código de propiedad debe ser único por proyecto!",
        ),
    ]

class ContractOwnerPartner(models.Model):
    _name = 'contract.owner.partner'
    _description = 'Propietario del Contrato'
    _order = 'is_main_owner, id'
    

    partner_id = fields.Many2one("res.partner", "Propietario", required=True)
    product_id = fields.Many2one("product.template", "Propiedad", index=True)
    ownership_percentage = fields.Float("Porcentaje de Propiedad", default=100.0)
    is_main_owner = fields.Boolean("Propietario Principal", default=False)
    start_date = fields.Date("Fecha de Inicio")
    end_date = fields.Date("Fecha de Fin")
    notes = fields.Text("Notas")
    contract_scenery_id = fields.Many2one(
        comodel_name='contract_scenery.contract_scenery',
        string='Escenario')

    @api.constrains('ownership_percentage')
    def _check_ownership_percentage(self):
        for record in self:
            if record.ownership_percentage < 0 or record.ownership_percentage > 100:
                raise UserError("El porcentaje de propiedad debe estar entre 0 y 100")

    @api.model
    def create(self, vals):
        if vals.get('is_main_owner') and vals.get('product_id'):
            existing_main = self.search([
                ('product_id', '=', vals['product_id']),
                ('is_main_owner', '=', True)
            ])
            existing_main.write({'is_main_owner': False})
        return super().create(vals)   
    

    @api.depends('product_id', 'partner_id', 'ownership_percentage')
    def _compute_display_name(self):
        for template in self:
            partner_name = template.partner_id.name or ''
            percentage = template.ownership_percentage or 0
            product_name =  ''
            
            if partner_name and percentage:
                template.display_name = f'[{percentage}% ] {partner_name}'
            elif partner_name:
                template.display_name = f'[{partner_name}] {product_name}'
            else:
                template.display_name = product_name


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    property_product_ids = fields.Many2many('product.template', string="Propiedades Asociadas")
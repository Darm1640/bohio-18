import json
import logging
from datetime import datetime, timedelta
from functools import lru_cache

from odoo import api, fields, models, tools, _
from odoo.osv import expression
from odoo.exceptions import ValidationError, UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)


class PropertyTemplate(models.Model):
    _inherit = "product.template"

    # =================== NUEVOS CAMPOS MEJORADOS ===================
    property_filters_config = fields.Json(
        string='Configuración de Filtros',
        default=lambda self: self._get_default_filters_config(),
        help="Configuración JSON para activar/desactivar filtros de propiedades"
    )
    
    property_search_vector = fields.Text(
        string='Vector de Búsqueda',
        compute='_compute_search_vector',
        store=True,
        help="Vector de búsqueda optimizado para consultas de texto"
    )
    
    property_popularity_score = fields.Float(
        string='Score de Popularidad',
        default=0.0,
        help="Score basado en visualizaciones y interacciones"
    )
    
    property_last_viewed = fields.Datetime(
        string='Última Visualización',
        help="Fecha de última visualización para ordenamiento"
    )

    # =================== CAMPOS COMPUTADOS MEJORADOS ===================
    @api.depends('name', 'city', 'neighborhood', 'street', 'street2', 'property_description')
    def _compute_search_vector(self):
        """Computa vector de búsqueda optimizado"""
        for record in self:
            if record.is_property:
                search_parts = []
                for field in ['name', 'city', 'neighborhood', 'street', 'street2', 'property_description']:
                    value = getattr(record, field, '')
                    if value:
                        search_parts.append(str(value).strip())
                record.property_search_vector = ' '.join(search_parts).lower()
            else:
                record.property_search_vector = False

    # =================== VALIDACIONES MEJORADAS ===================
    @api.constrains('sale_value_from', 'sale_value_to')
    def _check_sale_price_range(self):
        """Valida rangos de precios de venta"""
        for record in self:
            if record.is_property and record.sale_value_from and record.sale_value_to:
                if record.sale_value_from > record.sale_value_to:
                    raise ValidationError(_("El precio mínimo de venta no puede ser mayor al máximo"))

    @api.constrains('rent_value_from', 'rent_value_to') 
    def _check_rent_price_range(self):
        """Valida rangos de precios de arriendo"""
        for record in self:
            if record.is_property and record.rent_value_from and record.rent_value_to:
                if record.rent_value_from > record.rent_value_to:
                    raise ValidationError(_("El precio mínimo de arriendo no puede ser mayor al máximo"))

    @api.constrains('num_bedrooms', 'num_bathrooms')
    def _check_rooms_validity(self):
        """Valida números de habitaciones y baños"""
        for record in self:
            if record.is_property:
                if record.num_bedrooms and record.num_bedrooms < 0:
                    raise ValidationError(_("El número de habitaciones no puede ser negativo"))
                if record.num_bathrooms and record.num_bathrooms < 0:
                    raise ValidationError(_("El número de baños no puede ser negativo"))

    # =================== CACHE MEJORADO ===================
    def _get_cache_key(self, domain, website_id=None):
        """Genera clave de cache única"""
        domain_str = str(sorted(domain)) if domain else "empty"
        website_str = str(website_id) if website_id else "no_website"
        return f"property_filters_{tools.ustr(domain_str)}_{website_str}".replace(" ", "_")

    @api.model
    def _get_cached_filter_options(self, domain=None, website=None):
        """Obtiene opciones de filtros con cache"""
        cache_key = self._get_cache_key(domain, website.id if website else None)
        
        # Intentar obtener del cache
        cache_manager = self.env['property.cache']
        cached_result = cache_manager.get_cache(cache_key)
        
        if cached_result:
            _logger.debug(f"Cache hit para filtros: {cache_key}")
            return cached_result
        
        # Calcular y guardar en cache
        _logger.debug(f"Cache miss para filtros: {cache_key}")
        result = self._get_property_filter_options_computed(domain, website)
        
        # Guardar en cache por 1 hora
        cache_manager.set_cache(cache_key, result, ttl=3600)
        
        return result

    def _get_default_filters_config(self):
        """Configuración por defecto mejorada"""
        return {
            'version': '1.1.0',
            'selection_filters': {
                'type_service': {
                    'active': True, 
                    'label': 'Tipo de Servicio',
                    'weight': 10,
                    'show_count': True
                },
                'property_type_id': {
                    'active': True, 
                    'label': 'Tipo de Propiedad',
                    'weight': 20,
                    'show_count': True
                },
                'state': {
                    'active': True, 
                    'label': 'Estado',
                    'weight': 30,
                    'show_count': True
                },
                'stratum': {
                    'active': True, 
                    'label': 'Estrato',
                    'weight': 40,
                    'show_count': True
                },
                'apartment_type': {
                    'active': True, 
                    'label': 'Tipo de Apartamento',
                    'weight': 50,
                    'show_count': True
                },
                'building_unit': {
                    'active': True, 
                    'label': 'Tipo de Unidad',
                    'weight': 60,
                    'show_count': True
                },
                'property_status': {
                    'active': True, 
                    'label': 'Estado del Inmueble',
                    'weight': 70,
                    'show_count': True
                },
            },
            'range_filters': {
                'num_bedrooms': {
                    'active': True, 
                    'label': 'Habitaciones', 
                    'min': 0, 
                    'max': 10,
                    'step': 1,
                    'weight': 10
                },
                'num_bathrooms': {
                    'active': True, 
                    'label': 'Baños', 
                    'min': 0, 
                    'max': 8,
                    'step': 0.5,
                    'weight': 20
                },
                'property_area': {
                    'active': True, 
                    'label': 'Área (m²)', 
                    'min': 0, 
                    'max': 1000,
                    'step': 10,
                    'weight': 30
                },
                'sale_value_from': {
                    'active': True, 
                    'label': 'Precio Venta', 
                    'min': 0, 
                    'max': 10000000000,
                    'step': 1000000,
                    'weight': 40,
                    'format': 'currency'
                },
                'rent_value_from': {
                    'active': True, 
                    'label': 'Precio Arriendo', 
                    'min': 0, 
                    'max': 50000000,
                    'step': 100000,
                    'weight': 50,
                    'format': 'currency'
                },
                'floor_number': {
                    'active': True, 
                    'label': 'Piso', 
                    'min': 0, 
                    'max': 50,
                    'step': 1,
                    'weight': 60
                },
                'property_age': {
                    'active': True, 
                    'label': 'Antigüedad (años)', 
                    'min': 0, 
                    'max': 100,
                    'step': 1,
                    'weight': 70
                },
            },
            'boolean_filters': {
                'furnished': {'active': True, 'label': 'Amoblado', 'weight': 10},
                'garage': {'active': True, 'label': 'Garaje', 'weight': 20},
                'pools': {'active': True, 'label': 'Piscina', 'weight': 30},
                'gym': {'active': True, 'label': 'Gimnasio', 'weight': 40},
                'elevator': {'active': True, 'label': 'Ascensor', 'weight': 50},
                'air_conditioning': {'active': True, 'label': 'Aire Acondicionado', 'weight': 60},
                'balcony': {'active': True, 'label': 'Balcón', 'weight': 70},
                'terrace': {'active': True, 'label': 'Terraza', 'weight': 80},
                'garden': {'active': True, 'label': 'Jardín', 'weight': 90},
                'study': {'active': True, 'label': 'Estudio', 'weight': 100},
                'service_room': {'active': True, 'label': 'Cuarto de Servicio', 'weight': 110},
                'walk_in_closet': {'active': True, 'label': 'Walk-in Closet', 'weight': 120},
                'social_room': {'active': True, 'label': 'Salón Social', 'weight': 130},
                'playground': {'active': True, 'label': 'Juegos Infantiles', 'weight': 140},
                'green_areas': {'active': True, 'label': 'Zonas Verdes', 'weight': 150},
                'is_vis': {'active': True, 'label': 'VIS', 'weight': 160},
                'is_vip': {'active': True, 'label': 'VIP', 'weight': 170},
                'has_subsidy': {'active': True, 'label': 'Con Subsidio', 'weight': 180},
            },
            'advanced_filters': {
                'location_radius': {
                    'active': True,
                    'label': 'Radio de búsqueda (km)',
                    'default': 5,
                    'options': [1, 5, 10, 20, 50]
                },
                'construction_year': {
                    'active': True,
                    'label': 'Año de construcción',
                    'min': 1950,
                    'max': datetime.now().year + 2
                },
                'energy_rating': {
                    'active': True,
                    'label': 'Calificación energética',
                    'options': ['A', 'B', 'C', 'D', 'E']
                }
            }
        }

    @api.model
    def _get_property_filter_options_computed(self, domain=None, website=None):
        """Versión optimizada del cálculo de filtros"""
        start_time = datetime.now()
        
        if not website:
            website = self.env['website'].get_current_website()
        
        base_domain = website.sale_product_domain()
        if domain:
            base_domain = expression.AND([base_domain, domain])
        
        # Filtrar solo propiedades activas y publicadas
        base_domain = expression.AND([
            base_domain, 
            [
                ('is_property', '=', True),
                ('active', '=', True),
                ('is_published', '=', True)
            ]
        ])
        
        config = self._get_default_filters_config()
        result = {
            'selection_filters': {},
            'range_filters': {},
            'boolean_filters': {},
            'advanced_filters': {},
            '_metadata': {
                'generated_at': fields.Datetime.now(),
                'domain_size': self.search_count(base_domain),
                'website_id': website.id
            }
        }
        
        # Obtener configuración activa del website
        active_config = website._get_property_filters_config()
        
        try:
            # Selection Filters optimizados
            self._compute_selection_filters(result, base_domain, config, active_config)
            
            # Range Filters optimizados  
            self._compute_range_filters(result, base_domain, config, active_config)
            
            # Boolean Filters optimizados
            self._compute_boolean_filters(result, base_domain, config, active_config)
            
            # Advanced Filters
            self._compute_advanced_filters(result, base_domain, config, active_config)
            
        except Exception as e:
            _logger.error(f"Error calculando filtros: {e}")
            raise UserError(_("Error calculando opciones de filtros: %s") % str(e))
        
        computation_time = (datetime.now() - start_time).total_seconds()
        result['_metadata']['computation_time'] = computation_time
        
        _logger.debug(f"Filtros calculados en {computation_time:.3f}s para {result['_metadata']['domain_size']} propiedades")
        
        return result

    def _compute_selection_filters(self, result, base_domain, config, active_config):
        """Computa filtros de selección optimizados"""
        selection_field_mapping = {
            'type_service': 'type_service',
            'property_type_id': 'property_type_id',
            'state': 'state',
            'stratum': 'stratum',
            'apartment_type': 'apartment_type',
            'building_unit': 'building_unit',
            'property_status': 'property_status',
        }
        
        for filter_key, field_name in selection_field_mapping.items():
            if not active_config['selection_filters'].get(filter_key, {}).get('active', True):
                continue
                
            if filter_key == 'property_type_id':
                self._compute_property_type_filter(result, base_domain, config)
            else:
                self._compute_standard_selection_filter(result, base_domain, config, filter_key, field_name)

    def _compute_property_type_filter(self, result, base_domain, config):
        """Computa filtro de tipo de propiedad"""
        property_types = self.env['property.type'].search([
            ('is_published', '=', True),
            ('active', '=', True)
        ], order='sequence, name')
        
        options = []
        for prop_type in property_types:
            count_domain = expression.AND([base_domain, [('property_type_id', '=', prop_type.id)]])
            count = self.search_count(count_domain)
            if count > 0:
                options.append({
                    'value': prop_type.id,
                    'label': prop_type.display_name if hasattr(prop_type, 'display_name') else prop_type.name,
                    'count': count,
                    'sequence': prop_type.sequence
                })
        
        if options:
            result['selection_filters']['property_type_id'] = {
                'label': 'Tipo de Propiedad',
                'options': sorted(options, key=lambda x: x['sequence']),
                'weight': config['selection_filters']['property_type_id'].get('weight', 20)
            }

    def _compute_standard_selection_filter(self, result, base_domain, config, filter_key, field_name):
        """Computa filtros de selección estándar"""
        field_info = self._fields.get(field_name)
        if not field_info or not hasattr(field_info, 'selection'):
            return
            
        selection_values = field_info.selection
        if callable(selection_values):
            selection_values = selection_values(self)
        
        # Usar query optimizada para obtener conteos
        query = f"""
            SELECT {field_name}, COUNT(*) 
            FROM product_template 
            WHERE {self._build_domain_sql(base_domain)}
            AND {field_name} IS NOT NULL
            GROUP BY {field_name}
            HAVING COUNT(*) > 0
            ORDER BY COUNT(*) DESC
        """
        
        self.env.cr.execute(query)
        db_results = dict(self.env.cr.fetchall())
        
        options = []
        for value, label in selection_values:
            count = db_results.get(value, 0)
            if count > 0:
                options.append({
                    'value': value,
                    'label': label,
                    'count': count
                })
        
        if options:
            result['selection_filters'][filter_key] = {
                'label': config['selection_filters'][filter_key]['label'],
                'options': options,
                'weight': config['selection_filters'][filter_key].get('weight', 0)
            }
            
        #except Exception as e:
        #    _logger.warning(f"Error en consulta optimizada para {filter_key}: {e}")
        #    # Fallback a método tradicional
        #    self._compute_selection_filter_fallback(result, base_domain, config, filter_key, field_name, selection_values)

    def _compute_range_filters(self, result, base_domain, config, active_config):
        """Computa filtros de rango optimizados"""
        for field_name, field_config in config['range_filters'].items():
            if not active_config['range_filters'].get(field_name, {}).get('active', True):
                continue
                
            if field_name not in self._fields:
                continue
            
            # Query optimizada para min/max
            query = f"""
                SELECT MIN({field_name}), MAX({field_name}), COUNT(*)
                FROM product_template
                WHERE {self._build_domain_sql(base_domain)}
                AND {field_name} IS NOT NULL 
                AND {field_name} > 0
            """
            
            try:
                self.env.cr.execute(query)
                db_result = self.env.cr.fetchone()
                
                if db_result and db_result[0] is not None and db_result[2] > 0:
                    result['range_filters'][field_name] = {
                        'label': field_config['label'],
                        'min_value': float(db_result[0]),
                        'max_value': float(db_result[1]),
                        'default_min': field_config.get('min', 0),
                        'default_max': field_config.get('max', db_result[1]),
                        'step': field_config.get('step', 1),
                        'format': field_config.get('format', 'number'),
                        'weight': field_config.get('weight', 0),
                        'count': db_result[2]
                    }
            except Exception as e:
                _logger.warning(f"Error calculando rango para {field_name}: {e}")

    def _compute_boolean_filters(self, result, base_domain, config, active_config):
        """Computa filtros booleanos optimizados"""
        boolean_fields = list(config['boolean_filters'].keys())
        
        # Query optimizada para todos los campos booleanos
        select_parts = [f"SUM(CASE WHEN {field} = true THEN 1 ELSE 0 END) as {field}_count" 
                       for field in boolean_fields if field in self._fields]
        
        if not select_parts:
            return
            
        query = f"""
            SELECT {', '.join(select_parts)}
            FROM product_template
            WHERE {self._build_domain_sql(base_domain)}
        """
        
        try:
            self.env.cr.execute(query)
            db_result = self.env.cr.fetchone()
            
            if db_result:
                for i, field_name in enumerate(boolean_fields):
                    if field_name not in self._fields:
                        continue
                        
                    if not active_config['boolean_filters'].get(field_name, {}).get('active', True):
                        continue
                    
                    count = db_result[i] if i < len(db_result) else 0
                    if count > 0:
                        field_config = config['boolean_filters'][field_name]
                        result['boolean_filters'][field_name] = {
                            'label': field_config['label'],
                            'count': count,
                            'weight': field_config.get('weight', 0)
                        }
        except Exception as e:
            _logger.warning(f"Error calculando filtros booleanos: {e}")

    def _compute_advanced_filters(self, result, base_domain, config, active_config):
        """Computa filtros avanzados"""
        advanced_config = config.get('advanced_filters', {})
        
        for filter_key, filter_config in advanced_config.items():
            if not filter_config.get('active', False):
                continue
                
            if filter_key == 'construction_year':
                # Calcular rango de años de construcción
                current_year = datetime.now().year
                query = f"""
                    SELECT MIN({current_year} - property_age), MAX({current_year} - property_age)
                    FROM product_template
                    WHERE {self._build_domain_sql(base_domain)}
                    AND property_age IS NOT NULL
                """
                
                try:
                    self.env.cr.execute(query)
                    db_result = self.env.cr.fetchone()
                    if db_result and db_result[0]:
                        result['advanced_filters'][filter_key] = {
                            'label': filter_config['label'],
                            'min_value': int(db_result[0]),
                            'max_value': int(db_result[1]),
                            'type': 'range'
                        }
                except Exception as e:
                    _logger.warning(f"Error calculando filtro {filter_key}: {e}")

    def _build_domain_sql(self, domain):
        """Construye cláusula WHERE SQL desde dominio Odoo"""
        # Simplificación para casos comunes - en producción usar query builder completo
        conditions = ["is_property = true", "active = true"]
        
        for condition in domain:
            if isinstance(condition, (list, tuple)) and len(condition) == 3:
                field, operator, value = condition
                if operator == '=' and isinstance(value, (str, int, bool)):
                    if isinstance(value, bool):
                        conditions.append(f"{field} = {value}")
                    elif isinstance(value, str):
                        conditions.append(f"{field} = '{value}'")
                    else:
                        conditions.append(f"{field} = {value}")
        
        return " AND ".join(conditions)

    # =================== MÉTODOS DE BÚSQUEDA MEJORADOS ===================
    @api.model
    def _search_properties_advanced(self, search_term, filters=None, limit=20, offset=0):
        """Búsqueda avanzada con relevancia y filtros"""
        if not search_term and not filters:
            return {'properties': [], 'total': 0}
        
        base_domain = [
            ('is_property', '=', True),
            ('active', '=', True),
            ('is_published', '=', True)
        ]
        
        # Aplicar filtros
        if filters:
            filter_domain = self._build_property_search_domain([], filters)
            base_domain.extend(filter_domain)
        
        # Búsqueda por texto con scoring
        if search_term:
            # Usar búsqueda full-text con PostgreSQL
            search_domain = self._build_fulltext_search_domain(search_term)
            base_domain.extend(search_domain)
        
        # Contar total
        total = self.search_count(base_domain)
        
        # Buscar con ordenamiento por relevancia
        order = self._get_search_order(search_term)
        properties = self.search(base_domain, limit=limit, offset=offset, order=order)
        
        # Formatear resultados
        results = []
        for prop in properties:
            results.append(self._format_property_result(prop, search_term))
        
        return {
            'properties': results,
            'total': total,
            'has_more': offset + limit < total
        }

    def _build_fulltext_search_domain(self, search_term):
        """Construye dominio para búsqueda full-text"""
        # Usar vector de búsqueda precomputado
        return [('property_search_vector', 'ilike', f'%{search_term.lower()}%')]

    def _get_search_order(self, search_term=None):
        """Obtiene orden de búsqueda por relevancia"""
        if search_term:
            # Ordenar por relevancia de texto y popularidad
            return 'property_popularity_score DESC, property_last_viewed DESC, create_date DESC'
        else:
            return 'property_popularity_score DESC, create_date DESC'

    def _format_property_result(self, prop, search_term=None):
        """Formatea resultado de propiedad para API"""
        location_parts = []
        if prop.city:
            location_parts.append(prop.city)
        if prop.region_id:
            location_parts.append(prop.region_id.name)
        if prop.state_id:
            location_parts.append(prop.state_id.name)
        
        return {
            'id': prop.id,
            'name': prop.name,
            'location': ', '.join(location_parts),
            'full_address': prop.street or '',
            'url': prop.website_url,
            'image_url': f'/web/image/product.template/{prop.id}/image_512',
            'type_service': dict(prop._fields['type_service'].selection).get(prop.type_service, ''),
            'property_type': prop.property_type_id.display_name if prop.property_type_id and hasattr(prop.property_type_id, 'display_name') else (prop.property_type_id.name if prop.property_type_id else ''),
            'price': {
                'sale': prop.sale_value_from if prop.sale_value_from else None,
                'rent': prop.rent_value_from if prop.rent_value_from else None,
                'currency': 'COP'  # O usar configuración de website
            },
            'features': {
                'bedrooms': int(prop.num_bedrooms) if prop.num_bedrooms else None,
                'bathrooms': prop.num_bathrooms if prop.num_bathrooms else None,
                'area': int(prop.property_area) if prop.property_area else None,
                'stratum': prop.stratum if prop.stratum else None,
            },
            'amenities': {
                'furnished': prop.furnished,
                'garage': prop.garage,
                'pool': prop.pools,
                'gym': prop.gym,
                'elevator': prop.elevator,
                'air_conditioning': prop.air_conditioning,
            },
            'popularity_score': prop.property_popularity_score,
            'last_viewed': prop.property_last_viewed.isoformat() if prop.property_last_viewed else None,
        }

    # =================== MÉTODOS DE ANALYTICS ===================
    def track_property_view(self):
        """Registra visualización de propiedad"""
        self.ensure_one()
        if self.is_property:
            self.sudo().write({
                'property_last_viewed': fields.Datetime.now(),
                'property_popularity_score': self.property_popularity_score + 0.1
            })
            
            # Registrar en analytics
            analytics = self.env['property.analytics']
            analytics.record_view(self.id)

    @api.model
    def get_trending_properties(self, limit=10, days=7):
        """Obtiene propiedades trending"""
        date_from = fields.Datetime.now() - timedelta(days=days)
        
        domain = [
            ('is_property', '=', True),
            ('active', '=', True),
            ('is_published', '=', True),
            ('property_last_viewed', '>=', date_from)
        ]
        
        return self.search(domain, limit=limit, order='property_popularity_score DESC, property_last_viewed DESC')

    # =================== API METHODS ===================
    @api.model
    def api_get_filter_options(self, domain=None, website_id=None):
        """API endpoint para obtener opciones de filtros"""
        try:
            website = self.env['website'].browse(website_id) if website_id else self.env['website'].get_current_website()
            
            if domain and isinstance(domain, str):
                domain = json.loads(domain)
            
            result = self._get_cached_filter_options(domain, website)
            
            return {
                'success': True,
                'data': result,
                'timestamp': fields.Datetime.now().isoformat()
            }
        except Exception as e:
            _logger.error(f"Error en API get_filter_options: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': fields.Datetime.now().isoformat()
            }

    @api.model
    def api_search_properties(self, search_term='', filters=None, limit=20, offset=0):
        """API endpoint para búsqueda de propiedades"""
        try:
            if filters and isinstance(filters, str):
                filters = json.loads(filters)
            
            result = self._search_properties_advanced(search_term, filters, limit, offset)
            
            return {
                'success': True,
                'data': result,
                'timestamp': fields.Datetime.now().isoformat()
            }
        except Exception as e:
            _logger.error(f"Error en API search_properties: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': fields.Datetime.now().isoformat()
            }



class PropertyCache(models.Model):
    _name = 'property.cache'
    _description = 'Cache para filtros de propiedades'
    _rec_name = 'cache_key'

    cache_key = fields.Char(string='Clave Cache', required=True, index=True)
    cache_data = fields.Text(string='Datos Cache')
    expiry_date = fields.Datetime(string='Fecha Expiración', required=True, index=True)
    create_date = fields.Datetime(string='Fecha Creación', default=fields.Datetime.now)
    hit_count = fields.Integer(string='Conteo Accesos', default=0)

    _sql_constraints = [
        ('unique_cache_key', 'UNIQUE(cache_key)', 'La clave de cache debe ser única')
    ]

    @api.model
    def get_cache(self, cache_key):
        """Obtiene valor del cache"""
        try:
            cache_record = self.search([
                ('cache_key', '=', cache_key),
                ('expiry_date', '>', fields.Datetime.now())
            ], limit=1)
            
            if cache_record:
                # Incrementar contador de accesos
                cache_record.sudo().hit_count += 1
                
                # Deserializar datos
                return json.loads(cache_record.cache_data)
            
            return None
        except Exception as e:
            _logger.warning(f"Error obteniendo cache {cache_key}: {e}")
            return None

    @api.model
    def set_cache(self, cache_key, data, ttl=3600):
        """Establece valor en cache"""
        try:
            expiry_date = fields.Datetime.now() + timedelta(seconds=ttl)
            cache_data = json.dumps(data, default=str)
            
            # Buscar registro existente
            existing = self.search([('cache_key', '=', cache_key)], limit=1)
            
            if existing:
                existing.write({
                    'cache_data': cache_data,
                    'expiry_date': expiry_date,
                    'hit_count': 0
                })
            else:
                self.create({
                    'cache_key': cache_key,
                    'cache_data': cache_data,
                    'expiry_date': expiry_date
                })
            
            return True
        except Exception as e:
            _logger.error(f"Error estableciendo cache {cache_key}: {e}")
            return False

    @api.model
    def clear_cache(self, pattern=None):
        """Limpia cache por patrón o todo"""
        try:
            domain = []
            if pattern:
                domain = [('cache_key', 'ilike', pattern)]
            
            records = self.search(domain)
            count = len(records)
            records.unlink()
            
            _logger.info(f"Cache limpiado: {count} registros eliminados")
            return count
        except Exception as e:
            _logger.error(f"Error limpiando cache: {e}")
            return 0

    @api.model
    def cleanup_expired(self):
        """Limpia registros expirados"""
        try:
            expired_records = self.search([
                ('expiry_date', '<=', fields.Datetime.now())
            ])
            count = len(expired_records)
            expired_records.unlink()
            
            _logger.info(f"Cache expirado limpiado: {count} registros")
            return count
        except Exception as e:
            _logger.error(f"Error limpiando cache expirado: {e}")
            return 0

    @api.model
    def get_cache_stats(self):
        """Obtiene estadísticas del cache"""
        try:
            total_records = self.search_count([])
            expired_records = self.search_count([
                ('expiry_date', '<=', fields.Datetime.now())
            ])
            active_records = total_records - expired_records
            
            # Top keys por accesos
            top_keys = self.search([
                ('expiry_date', '>', fields.Datetime.now())
            ], order='hit_count DESC', limit=10)
            
            return {
                'total_records': total_records,
                'active_records': active_records,
                'expired_records': expired_records,
                'hit_rate': sum(top_keys.mapped('hit_count')) / max(active_records, 1),
                'top_keys': [{'key': r.cache_key, 'hits': r.hit_count} for r in top_keys]
            }
        except Exception as e:
            _logger.error(f"Error obteniendo estadísticas cache: {e}")
            return {}

# 

class PropertyAnalytics(models.Model):
    _name = 'property.analytics'
    _description = 'Analytics de propiedades'
    _rec_name = 'property_id'

    property_id = fields.Many2one('product.template', string='Propiedad', required=True, index=True)
    event_type = fields.Selection([
        ('view', 'Visualización'),
        ('search', 'Búsqueda'),
        ('filter', 'Filtro Aplicado'),
        ('contact', 'Contacto'),
        ('favorite', 'Favorito')
    ], string='Tipo Evento', required=True, index=True)
    event_data = fields.Json(string='Datos Evento')
    user_id = fields.Many2one('res.users', string='Usuario')
    session_id = fields.Char(string='Sesión')
    ip_address = fields.Char(string='IP')
    user_agent = fields.Text(string='User Agent')
    referrer = fields.Char(string='Referrer')
    event_date = fields.Datetime(string='Fecha Evento', default=fields.Datetime.now, index=True)

    @api.model
    def record_view(self, property_id, user_id=None, session_id=None, **kwargs):
        """Registra visualización de propiedad"""
        try:
            self.create({
                'property_id': property_id,
                'event_type': 'view',
                'user_id': user_id or self.env.user.id,
                'session_id': session_id,
                'event_data': kwargs,
                'ip_address': kwargs.get('ip_address'),
                'user_agent': kwargs.get('user_agent'),
                'referrer': kwargs.get('referrer')
            })
        except Exception as e:
            _logger.error(f"Error registrando vista de propiedad {property_id}: {e}")

    @api.model
    def record_search(self, search_term, filters=None, results_count=0, **kwargs):
        """Registra búsqueda de propiedades"""
        try:
            event_data = {
                'search_term': search_term,
                'filters': filters,
                'results_count': results_count,
                **kwargs
            }
            
            self.create({
                'property_id': None,  # Búsqueda general
                'event_type': 'search',
                'event_data': event_data,
                'user_id': self.env.user.id,
                'session_id': kwargs.get('session_id'),
                'ip_address': kwargs.get('ip_address'),
                'user_agent': kwargs.get('user_agent')
            })
        except Exception as e:
            _logger.error(f"Error registrando búsqueda: {e}")

    @api.model
    def get_popular_properties(self, limit=10, days=30):
        """Obtiene propiedades más populares"""
        date_from = fields.Datetime.now() - timedelta(days=days)
        
        query = """
            SELECT property_id, COUNT(*) as view_count
            FROM property_analytics
            WHERE event_type = 'view'
            AND event_date >= %s
            AND property_id IS NOT NULL
            GROUP BY property_id
            ORDER BY view_count DESC
            LIMIT %s
        """
        
        self.env.cr.execute(query, (date_from, limit))
        results = self.env.cr.fetchall()
        
        property_ids = [r[0] for r in results]
        properties = self.env['product.template'].browse(property_ids)
        
        return [{
            'property': prop,
            'view_count': next(r[1] for r in results if r[0] == prop.id)
        } for prop in properties]

    @api.model
    def get_search_trends(self, days=30):
        """Obtiene tendencias de búsqueda"""
        date_from = fields.Datetime.now() - timedelta(days=days)
        
        analytics = self.search([
            ('event_type', '=', 'search'),
            ('event_date', '>=', date_from)
        ])
        
        search_terms = {}
        filter_usage = {}
        
        for record in analytics:
            data = record.event_data or {}
            
            # Contar términos de búsqueda
            search_term = data.get('search_term', '').strip().lower()
            if search_term:
                search_terms[search_term] = search_terms.get(search_term, 0) + 1
            
            # Contar uso de filtros
            filters = data.get('filters', {})
            for filter_type, filter_data in filters.items():
                if filter_data:
                    filter_usage[filter_type] = filter_usage.get(filter_type, 0) + 1
        
        return {
            'popular_searches': sorted(search_terms.items(), key=lambda x: x[1], reverse=True)[:20],
            'popular_filters': sorted(filter_usage.items(), key=lambda x: x[1], reverse=True),
            'total_searches': len(analytics)
        }
class Website(models.Model):
    _inherit = 'website'

    # property_filters_active = fields.Boolean(
    #     string='Activar Filtros de Propiedades',
    #     default=True,
    #     help="Habilita los filtros específicos para propiedades inmobiliarias"
    # )

    # property_filters_config = fields.Json(
    #     string='Configuración Filtros Propiedades',
    #     default=lambda self: self.env['product.template']._get_default_filters_config(),
    #     help="Configuración personalizada de filtros para este website"
    # )

    def _get_property_filters_config(self):
        """Obtiene la configuración de filtros del website"""
        self.ensure_one()
        return self.env['product.template']._get_default_filters_config()

    def _is_property_filters_active(self):
        """Verifica si los filtros de propiedades están activos"""
        self.ensure_one()
        return True

    @api.model
    def get_property_search_suggestions(self, search_term, limit=10):
        """Obtiene sugerencias de búsqueda para propiedades"""
        suggestions = {
            'cities': [],
            'neighborhoods': [],
            'property_types': []
        }
        
        if not search_term or len(search_term) < 2:
            return suggestions
        
        # Buscar ciudades
        self.env.cr.execute("""
            SELECT DISTINCT city, COUNT(*) as count
            FROM product_template 
            WHERE is_property = true 
            AND city ILIKE %s 
            AND city IS NOT NULL
            GROUP BY city 
            ORDER BY count DESC 
            LIMIT %s
        """, (f'%{search_term}%', limit))
        
        for city, count in self.env.cr.fetchall():
            suggestions['cities'].append({
                'name': city,
                'count': count,
                'url': f'/shop/properties?city={city}'
            })
        
        # Buscar barrios
        self.env.cr.execute("""
            SELECT DISTINCT neighborhood, COUNT(*) as count
            FROM product_template 
            WHERE is_property = true 
            AND neighborhood ILIKE %s 
            AND neighborhood IS NOT NULL
            GROUP BY neighborhood 
            ORDER BY count DESC 
            LIMIT %s
        """, (f'%{search_term}%', limit))
        
        for neighborhood, count in self.env.cr.fetchall():
            suggestions['neighborhoods'].append({
                'name': neighborhood,
                'count': count,
                'url': f'/shop/properties?search={neighborhood}'
            })
        
        # Buscar tipos de propiedades
        property_types = self.env['property.type'].search([
            ('name', 'ilike', search_term),
            ('is_published', '=', True)
        ], limit=limit)
        
        for ptype in property_types:
            count = self.env['product.template'].search_count([
                ('is_property', '=', True),
                ('property_type_id', '=', ptype.id)
            ])
            if count > 0:
                suggestions['property_types'].append({
                    'name': ptype.display_name if hasattr(ptype, 'display_name') else ptype.name,
                    'count': count,
                    'url': f'/shop/properties?property_type_id={ptype.id}'
                })
        
        return suggestions


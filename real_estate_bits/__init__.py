from . import models
from . import wizard
from . import controllers
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def pre_init_hook(env):
    """Hook ejecutado antes de la instalación"""
    _logger.info("Property Website Filters: Iniciando pre-instalación...")

    # Verificar dependencias opcionales
    try:
        import redis
        _logger.info("Redis disponible para cache")
    except ImportError:
        _logger.warning("Redis no disponible - cache deshabilitado")

    try:
        import geopy
        _logger.info("GeoPy disponible para geocoding")
    except ImportError:
        _logger.warning("GeoPy no disponible - geocoding deshabilitado")


def post_init_hook(env):
    """Hook ejecutado después de la instalación"""
    _logger.info("Property Website Filters: Iniciando post-instalación...")

    # En Odoo 18, los hooks reciben directamente el Environment
    # No necesitamos crear uno nuevo

    _create_database_indexes(env.cr)

    _setup_initial_cache(env)

    _setup_seo_data(env)

    _logger.info("Property Website Filters: Post-instalación completada")


def uninstall_hook(env):
    """Hook ejecutado durante desinstalación"""
    _logger.info("Property Website Filters: Iniciando desinstalación...")

    _cleanup_database_indexes(env.cr)
    
    _logger.info("Property Website Filters: Desinstalación completada")


def _create_database_indexes(cr):
    """Crea índices optimizados para consultas de propiedades"""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_product_template_property_location ON product_template (city, state_id, region_id) WHERE is_property = true;",
        "CREATE INDEX IF NOT EXISTS idx_product_template_property_type ON product_template (type_service, property_type_id) WHERE is_property = true;",
        "CREATE INDEX IF NOT EXISTS idx_product_template_property_features ON product_template (num_bedrooms, num_bathrooms, property_area) WHERE is_property = true;",
        "CREATE INDEX IF NOT EXISTS idx_product_template_property_price ON product_template (sale_value_from, rent_value_from) WHERE is_property = true;",
        "CREATE INDEX IF NOT EXISTS idx_product_template_property_state ON product_template (state, stratum) WHERE is_property = true;",
        
        "CREATE INDEX IF NOT EXISTS idx_product_template_search_gin ON product_template USING gin(to_tsvector('spanish', coalesce(name,'') || ' ' || coalesce(city,'') || ' ' || coalesce(neighborhood,''))) WHERE is_property = true;",
        
        "CREATE INDEX IF NOT EXISTS idx_product_template_property_date ON product_template (create_date DESC, write_date DESC) WHERE is_property = true;",
        
        "CREATE INDEX IF NOT EXISTS idx_product_template_property_active ON product_template (active, website_published, is_property, create_date DESC) WHERE is_property = true;",
    ]
    
    for index_sql in indexes:
        try:
            cr.execute(index_sql)
            _logger.info(f"Índice creado: {index_sql[:50]}...")
        except Exception as e:
            _logger.warning(f"Error creando índice: {e}")


def _cleanup_database_indexes(cr):
    """Limpia índices creados por el módulo"""
    indexes_to_drop = [
        "idx_product_template_property_location",
        "idx_product_template_property_type",
        "idx_product_template_property_features", 
        "idx_product_template_property_price",
        "idx_product_template_property_state",
        "idx_product_template_search_gin",
        "idx_product_template_property_date",
        "idx_product_template_property_active",
    ]
    
    for index_name in indexes_to_drop:
        try:
            cr.execute(f"DROP INDEX IF EXISTS {index_name};")
            _logger.info(f"Índice eliminado: {index_name}")
        except Exception as e:
            _logger.warning(f"Error eliminando índice {index_name}: {e}")


def _setup_initial_cache(env):
    """Configura cache inicial para filtros"""
    try:
        websites = env['website'].search([('property_filters_active', '=', True)])
        for website in websites:
            env['product.template'].with_context(website_id=website.id)._get_property_filter_options()
        _logger.info("Cache inicial configurado")
    except Exception as e:
        _logger.warning(f"Error configurando cache inicial: {e}")


def _setup_seo_data(env):
    """Configura datos SEO básicos"""
    try:
        websites = env['website'].search([])
        for website in websites:
            if not website.property_seo_config:
                website.property_seo_config = {
                    'enable_structured_data': True,
                    'default_meta_description': 'Encuentra la propiedad perfecta con nuestros filtros avanzados',
                    'default_meta_keywords': 'propiedades, inmobiliarias, casas, apartamentos',
                }
        _logger.info("Datos SEO configurados")
    except Exception as e:
        _logger.warning(f"Error configurando SEO: {e}")
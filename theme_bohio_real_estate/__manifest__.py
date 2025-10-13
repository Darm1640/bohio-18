# -*- coding: utf-8 -*-
{
    'name': 'Theme Bohio Real Estate',
    'category': 'Theme/Website',
    'version': '18.0.3.0.0',
    'summary': 'Tema inmobiliario profesional con búsqueda avanzada',
    'description': """
        Tema profesional para inmobiliarias BOHIO con:
        - Homepage moderna con carrusel y búsqueda
        - Búsqueda por ciudad/barrio (trigram)
        - Shop de propiedades con filtros avanzados
        - Vista de mapa con pins personalizados
        - Diseño responsivo Bootstrap 5
        - Integración redes sociales
    """,
    'depends': [
        'website',
        'web_editor',
        'bohio_real_estate',
        'utm',
    ],
    'external_dependencies': {
        'python': [],
    },
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'data': [
        # Layout
        'views/layout/loader_template.xml',
        'views/layout/pwa_fix.xml',

        # Data - Snippet Filters
        'data/property_snippet_filters.xml',

        # Data - Torre Rialto (orden: proyecto, propiedades, planos)
        'data/torre_rialto_proyecto.xml',
        'data/torre_rialto_propiedades.xml',
        'data/torre_rialto_planos.xml',

        # Views - Homepage
        'views/homepage_new.xml',

        # Views - Pages
        'views/pages/servicios_page.xml',
        'views/pages/sobre_nosotros_page.xml',
        'views/pages/contacto_page.xml',
        'views/pages/proyectos_page.xml',
        'views/pages/proyecto_detalle.xml',
        'views/pages/property_contact_response.xml',

        # Views - Properties
        'views/properties_shop_template.xml',
        'views/property_detail_template.xml',

        # Snippets
        'views/snippets/property_carousels_snippet.xml',
        'views/snippets/property_snippet_templates.xml',
        'views/snippets/property_snippet_templates_simple.xml',
        'views/snippets/s_dynamic_snippet_properties.xml',

        # Menus
        'views/menus/website_menu.xml',

        # Headers & Footers
        'views/headers/header_template.xml',
        'views/footers/footer_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # External - Leaflet Maps
            'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
            'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',

            # Bootstrap Icons
            'theme_bohio_real_estate/static/src/lib/bootstrap-icons/bootstrap-icons.min.css',

            # CSS
            'theme_bohio_real_estate/static/src/css/style.css',
            'theme_bohio_real_estate/static/src/css/homepage_autocomplete.css',
            'theme_bohio_real_estate/static/src/css/homepage_maps.css',
            'theme_bohio_real_estate/static/src/css/map_styles.css',
            'theme_bohio_real_estate/static/src/css/proyecto_detalle.css',
            'theme_bohio_real_estate/static/src/css/property_detail_modals.css',

            # SCSS
            'theme_bohio_real_estate/static/src/scss/loader.scss',
            'theme_bohio_real_estate/static/src/scss/homepage.scss',
            'theme_bohio_real_estate/static/src/scss/pages.scss',
            'theme_bohio_real_estate/static/src/scss/property_detail.scss',
            'theme_bohio_real_estate/static/src/scss/header.scss',
            'theme_bohio_real_estate/static/src/scss/footer.scss',
            'theme_bohio_real_estate/static/src/scss/property_shop.scss',

            # JavaScript - Core
            'theme_bohio_real_estate/static/src/js/page_loader.js',
            'theme_bohio_real_estate/static/src/js/property_compare.js',
            'theme_bohio_real_estate/static/src/js/homepage_autocomplete.js',
            'theme_bohio_real_estate/static/src/js/homepage_properties.js',
            'theme_bohio_real_estate/static/src/js/property_filters.js',
            'theme_bohio_real_estate/static/src/js/property_shop.js',
            'theme_bohio_real_estate/static/src/js/proyectos.js',
            'theme_bohio_real_estate/static/src/js/proyecto_detalle.js',
            'theme_bohio_real_estate/static/src/js/property_detail_gallery.js',

            # CSS Additional
            'theme_bohio_real_estate/static/src/css/property_carousels.css',
            'theme_bohio_real_estate/static/src/css/property_snippets.css',

            # JavaScript - Property Carousels (Vanilla JS with RPC)
            'theme_bohio_real_estate/static/src/js/init_carousels.js',
        ],
        'web.assets_backend': [
            # JavaScript - Property Snippet Options (Website Builder)
            # NO necesitamos options.js porque usamos el sistema nativo de filtros
            # 'theme_bohio_real_estate/static/src/snippets/s_dynamic_snippet_properties/options.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}

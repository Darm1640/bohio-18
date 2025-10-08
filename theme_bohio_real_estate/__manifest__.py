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
        'bohio_real_estate',
    ],
    'data': [
        # Views
        'views/homepage_new.xml',
        'views/properties_shop_template.xml',
        'views/property_detail_template.xml',

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

            # SCSS
            'theme_bohio_real_estate/static/src/scss/homepage.scss',
            'theme_bohio_real_estate/static/src/scss/header.scss',
            'theme_bohio_real_estate/static/src/scss/footer.scss',

            # JavaScript
            'theme_bohio_real_estate/static/src/js/homepage_new.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}

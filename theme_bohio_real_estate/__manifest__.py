# -*- coding: utf-8 -*-
{
    'name': 'Theme Bohio Real Estate',
    'category': 'Theme/Website',
    'version': '18.0.1.0.0',
    'summary': 'Tema inmobiliario para Bohio - Portal de búsqueda y gestión de propiedades',
    'description': """
        Tema profesional para inmobiliarias con:
        - Búsqueda avanzada de propiedades por barrio
        - Portal de clientes personalizado
        - Diseño moderno y responsivo
        - Integración con módulo bohio_real_estate
    """,
    'depends': [
        'website',
        'portal',
        'bohio_real_estate',
    ],
    'data': [
        'views/assets.xml',
        'views/portal_template.xml',
        'views/property_search_template.xml',
        'views/homepage_template.xml',

        # Headers
        'views/headers/header_template.xml',

        # Footers
        'views/footers/footer_template.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('prepend', '/theme_bohio_real_estate/static/src/scss/color_variables.scss'),
            '/theme_bohio_real_estate/static/src/scss/theme_variables.scss',
        ],
        'web.assets_frontend': [
            # CSS
            '/theme_bohio_real_estate/static/src/scss/common.scss',
            '/theme_bohio_real_estate/static/src/scss/header.scss',
            '/theme_bohio_real_estate/static/src/scss/footer.scss',
            '/theme_bohio_real_estate/static/src/scss/homepage.scss',
            '/theme_bohio_real_estate/static/src/scss/property_search.scss',
            '/theme_bohio_real_estate/static/src/scss/portal.scss',

            # JS
            '/theme_bohio_real_estate/static/src/js/property_search.js',
            '/theme_bohio_real_estate/static/src/js/portal.js',
            '/theme_bohio_real_estate/static/src/js/common.js',
        ],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}

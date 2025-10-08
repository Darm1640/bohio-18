# -*- coding: utf-8 -*-
{
    'name': 'Theme Bohio Real Estate',
    'category': 'Theme/Website',
    'version': '18.0.2.0.0',
    'summary': 'Tema inmobiliario completo - Website público y portal con modo oscuro',
    'description': """
        Tema profesional para inmobiliarias con:
        - Website público con búsqueda avanzada de propiedades
        - Modo oscuro automático y manual
        - Sistema de favoritos con persistencia
        - Comparador de propiedades (hasta 3)
        - Tienda de propiedades (shop)
        - Detalles de propiedades
        - Homepage moderna
        - Portal de clientes personalizado
        - Diseño moderno y responsivo
        - Headers y Footers personalizados
        - Accesibilidad mejorada (WCAG 2.1)
    """,
    'depends': [
        'website',
        'portal',
        'bohio_real_estate',
    ],
    'data': [
        'views/assets.xml',

        # Portal Templates
        'views/portal_template.xml',

        # Website Public Templates
        'views/website_templates.xml',
        'views/properties_shop_template.xml',
        'views/property_detail_template.xml',
        'views/properties_list_map.xml',
        'views/homepage_landing.xml',
        'views/homepage_template.xml',
        'views/property_search_template.xml',

        # Pages
        'views/pages/about_us.xml',

        # Menus
        'views/menus/website_menu.xml',

        # Headers & Footers
        'views/headers/header_template.xml',
        'views/footers/footer_template.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('prepend', '/theme_bohio_real_estate/static/src/scss/color_variables.scss'),
            '/theme_bohio_real_estate/static/src/scss/theme_variables.scss',
            '/theme_bohio_real_estate/static/src/scss/bohio_variables.scss',
        ],
        'web.assets_frontend': [
            # Theme CSS/SCSS - Base
            '/theme_bohio_real_estate/static/src/scss/bohio_theme.scss',
            '/theme_bohio_real_estate/static/src/scss/bohio_variables.scss',
            '/theme_bohio_real_estate/static/src/scss/common.scss',
            '/theme_bohio_real_estate/static/src/scss/header.scss',
            '/theme_bohio_real_estate/static/src/scss/footer.scss',
            '/theme_bohio_real_estate/static/src/scss/homepage.scss',
            '/theme_bohio_real_estate/static/src/scss/homepage_landing.scss',
            '/theme_bohio_real_estate/static/src/scss/property_search.scss',
            '/theme_bohio_real_estate/static/src/scss/property_comparison.scss',
            '/theme_bohio_real_estate/static/src/scss/properties_list_map.scss',
            '/theme_bohio_real_estate/static/src/scss/portal.scss',

            # Website JS - Utils
            '/theme_bohio_real_estate/static/src/js/utils/api.js',
            '/theme_bohio_real_estate/static/src/js/utils/dom.js',
            '/theme_bohio_real_estate/static/src/js/utils/formatters.js',
            '/theme_bohio_real_estate/static/src/js/utils/debounce.js',
            '/theme_bohio_real_estate/static/src/js/utils/validation.js',
            '/theme_bohio_real_estate/static/src/js/utils/url.js',

            # Website JS - New Features (from files/ integration)
            '/theme_bohio_real_estate/static/src/js/dark_mode.js',
            '/theme_bohio_real_estate/static/src/js/favorites_manager.js',
            '/theme_bohio_real_estate/static/src/js/property_comparator.js',
            '/theme_bohio_real_estate/static/src/js/property_comparison_widget.js',

            # Website JS - Components
            '/theme_bohio_real_estate/static/src/js/search/search_bar.js',
            '/theme_bohio_real_estate/static/src/js/properties/property_card.js',
            '/theme_bohio_real_estate/static/src/js/properties/properties_list.js',
            '/theme_bohio_real_estate/static/src/js/homepage/homepage.js',
            '/theme_bohio_real_estate/static/src/js/contact/contact_form.js',

            # Website JS - Main
            '/theme_bohio_real_estate/static/src/js/bohio_main.js',
            '/theme_bohio_real_estate/static/src/js/properties_shop.js',
            '/theme_bohio_real_estate/static/src/js/property_search.js',
            '/theme_bohio_real_estate/static/src/js/properties_list_map.js',
            '/theme_bohio_real_estate/static/src/js/homepage_landing.js',
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

# -*- coding: utf-8 -*-
{
    'name': 'Theme Bohio Real Estate',
    'category': 'Theme/Website',
    'version': '18.0.3.0.1',
    'summary': 'Tema inmobiliario profesional con búsqueda avanzada',
    'description': """
        Tema profesional para inmobiliarias BOHIO con:
        - Homepage moderna con carrusel y búsqueda
        - Búsqueda por ciudad/barrio (trigram)
        - Shop de propiedades con filtros avanzados
        - Vista de mapa con pins personalizados
        - Diseño responsivo Bootstrap 5.3.3
        - Integración redes sociales

        Versión 18.0.3.0.1:
        - Limpieza de assets inexistentes
        - Optimización de manifest
    """,
    'author': 'BOHIO Inmobiliaria',
    'website': 'https://www.bohio.com.co',
    'depends': [
        'website',
        'web_editor',
        'bohio_real_estate',
        'utm',
    ],
    'data': [
        # ========== LAYOUT ==========
        'views/layout/loader_template.xml',
        'views/layout/pwa_fix.xml',

        'data/property_snippet_filters.xml',

        'data/torre_rialto_proyecto.xml',
        'data/torre_rialto_propiedades.xml',
        'data/torre_rialto_planos.xml',
        'views/homepage_new.xml',
        'views/pages/servicios_page.xml',
        'views/pages/sobre_nosotros_page.xml',
        'views/pages/contacto_page.xml',
        'views/pages/proyectos_page.xml',
        'views/pages/proyecto_detalle.xml',
        'views/pages/property_contact_response.xml',

        'views/properties_shop_template.xml',
        'views/property_detail_template.xml',

        'views/snippets/property_carousels_snippet.xml',
        'views/snippets/property_card_qweb_template.xml',
        'views/snippets/property_snippet_templates.xml',
        'views/snippets/property_snippet_templates_simple.xml',
        'views/snippets/s_dynamic_snippet_properties.xml',

        'views/templates/property_shop_templates.xml',
        'views/templates/homepage_autocomplete_templates.xml',
        'views/menus/website_menu.xml',

        'views/headers/header_template.xml',
        'views/footers/footer_template.xml',

        'views/mapa_propiedades.xml',
        'views/property_map_fullpage.xml',
        'views/property_map_no_coordinates.xml',

        'views/mejoras_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
           
            'theme_bohio_real_estate/static/lib/bootstrap-5.3.3/css/bootstrap.min.css',
            'theme_bohio_real_estate/static/lib/bootstrap-5.3.3/js/bootstrap.bundle.min.js',
            'theme_bohio_real_estate/static/src/css/style.css',
            'theme_bohio_real_estate/static/src/css/homepage_autocomplete.css',
            'theme_bohio_real_estate/static/src/css/homepage_maps.css',
            'theme_bohio_real_estate/static/src/css/map_styles.css',
            'theme_bohio_real_estate/static/src/css/proyecto_detalle.css',
            'theme_bohio_real_estate/static/src/css/property_detail_modals.css',
            # SCSS - Variables y Mixins
            'theme_bohio_real_estate/static/src/scss/_variables.scss',
            'theme_bohio_real_estate/static/src/scss/_mixins.scss',
            'theme_bohio_real_estate/static/src/scss/footer.scss',
            'theme_bohio_real_estate/static/src/scss/header.scss',
            'theme_bohio_real_estate/static/src/scss/homepage.scss',
            'theme_bohio_real_estate/static/src/scss/loader.scss',
            'theme_bohio_real_estate/static/src/scss/mapa_propiedades.scss',
            'theme_bohio_real_estate/static/src/scss/pages.scss',
            'theme_bohio_real_estate/static/src/scss/property_cards.scss',
            'theme_bohio_real_estate/static/src/scss/property_detail.scss',
            'theme_bohio_real_estate/static/src/scss/property_shop.scss',
            'theme_bohio_real_estate/static/src/scss/components/_property_card_enhanced.scss',
            'theme_bohio_real_estate/static/src/scss/components/_property_card_clean.scss',

            # JavaScript - Utils (Orden: utils primero, luego DOM, luego widgets)
            'theme_bohio_real_estate/static/src/js/utils/constants.js',
            'theme_bohio_real_estate/static/src/js/utils/formatters.js',
            'theme_bohio_real_estate/static/src/js/utils/template_renderer.js',
            'theme_bohio_real_estate/static/src/js/utils/geolocation.js',
            'theme_bohio_real_estate/static/src/js/utils/url_params.js',
            'theme_bohio_real_estate/static/src/js/utils/dom_helpers.js',

            # JavaScript - DOM Manipulation (usa utils)
            'theme_bohio_real_estate/static/src/js/dom/markers.js',

            # JavaScript - Services (servicios centralizados - REFACTORIZACIÓN)
            'theme_bohio_real_estate/static/src/js/services/property_service.js',
            'theme_bohio_real_estate/static/src/js/services/map_service.js',
            'theme_bohio_real_estate/static/src/js/services/wishlist_service.js',

            # JavaScript - Components (componentes reutilizables - REFACTORIZACIÓN)
            'theme_bohio_real_estate/static/src/js/components/property_card.js',
            'theme_bohio_real_estate/static/src/js/components/property_gallery.js',

            # JavaScript - Widgets (PublicWidget - usa utils y dom)
            'theme_bohio_real_estate/static/src/js/widgets/map_widget.js',
            'theme_bohio_real_estate/static/src/js/widgets/homepage_properties_widget.js',
            'theme_bohio_real_estate/static/src/js/widgets/service_type_selector_widget.js',

            # ========================================================================
            # JAVASCRIPT - CORE (ACTIVOS)
            # ========================================================================
            'theme_bohio_real_estate/static/src/js/page_loader.js',
            'theme_bohio_real_estate/static/src/js/homepage_autocomplete.js',
            'theme_bohio_real_estate/static/src/js/property_filters.js',
            'theme_bohio_real_estate/static/src/js/lazy_image_loader.js',
            'theme_bohio_real_estate/static/src/js/property_shop.js',
            'theme_bohio_real_estate/static/src/js/proyectos.js',
            'theme_bohio_real_estate/static/src/js/proyecto_detalle.js',
            'theme_bohio_real_estate/static/src/js/property_detail_gallery.js',
            'theme_bohio_real_estate/static/src/js/property_wishlist.js',
            'theme_bohio_real_estate/static/src/js/property_carousels.js',
            'theme_bohio_real_estate/static/src/js/property_detail_modals.js',

            # ========================================================================
            # CSS - PROPERTY SNIPPETS Y CAROUSELS
            # ========================================================================
            'theme_bohio_real_estate/static/src/css/property_carousels.css',
            'theme_bohio_real_estate/static/src/css/property_snippets.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
    'web_icon': 'theme_bohio_real_estate/static/description/icon.png',
}

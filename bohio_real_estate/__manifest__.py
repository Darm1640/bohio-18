{
    'name': 'BOHIO Real Estate Theme',
    'version': '18.0.1.0.0',
    'category': 'Website/Theme',
    'summary': 'BOHIO branding and theme for real estate module',
    'description': """
        BOHIO Real Estate Theme
        ========================
        Extiende el módulo real_estate_bits con:
        - Diseño personalizado BOHIO
        - Templates web personalizados
        - Integración con recursos de Figma
        - Estilos y branding corporativo
    """,
    'author': 'BOHIO Inmobiliaria',
    'website': 'https://www.bohio.com.co',
    'depends': [
        'real_estate_bits',
        'website',
        'website_sale',
        'crm',
        'hr_expense',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/website_data.xml',
        'views/property_inherit_views.xml',
        'views/property_document_views.xml',
        'views/website_templates.xml',
        'views/properties_shop_template.xml',
        'views/property_detail_template.xml',
        'views/homepage/homepage.xml',
        'views/services_templates.xml',
        'views/property_templates.xml',
        'views/contact_templates.xml',
        'views/portal_templates.xml',
        'views/properties/property_map_openstreet.xml',
        'views/properties/property_map_view.xml',
        'views/compare/property_compare.xml',
        'views/crm_dashboard_views.xml',
        'views/crm_lead_form_inherit.xml',
        'views/crm_metrics_dashboard.xml',
        'views/property_compare_wizard_views.xml',
        'views/menu_items.xml',
        'report/property_comparison_report.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'bohio_real_estate/static/src/css/bohio_theme.css',
            'bohio_real_estate/static/src/scss/bohio_theme.scss',
            'bohio_real_estate/static/src/js/bohio_main.js',
            'bohio_real_estate/static/src/js/properties_shop.js',
            'bohio_real_estate/static/src/fonts/arista-pro-bold.ttf',
            'bohio_real_estate/static/src/fonts/Ciutadella SemiBold.ttf',
            'bohio_real_estate/static/src/fonts/Ciutadella Light.ttf',
        ],
        'web.assets_backend': [
            'bohio_real_estate/static/src/css/venture_crm_dashboard.css',
            'bohio_real_estate/static/src/scss/crm_dashboard.scss',
            'bohio_real_estate/static/src/js/crm_dashboard.js',
            'bohio_real_estate/static/src/xml/crm_dashboard_templates.xml',
        ],
    },
    'images': [
        'static/description/icon.png',
        'static/description/banner.jpg',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
}
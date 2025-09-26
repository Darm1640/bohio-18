{
    "name": "Gestión Inmobiliaria | Administración de Propiedades | Contratos de Venta y Alquiler",
    "version": '18.0.1.0.0',
    "category": "Bienes Raíces",
    "sequence": 14,
    "summary": """
        Este módulo permite gestionar proyectos inmobiliarios, contratos de venta y alquiler de propiedades, calcular comisiones de corredores y mucho más.
        Gestión Avanzada de Ventas y Alquileres | Ventas de Propiedades | Alquiler de Propiedades
    """,
    "description": """
        Este módulo permite gestionar proyectos inmobiliarios, contratos de venta y alquiler de propiedades, calcular comisiones de corredores y mucho más.
        Gestión Avanzada de Ventas y Alquileres | Ventas de Propiedades | Alquiler de Propiedades
    """,
    "author": "Terabits Technolab",
    "website": "https://www.terabits.xyz",
    "depends": ["base", "account", "analytic", 'repair', 'sale_management', 'web', "website_sale"],
    "license": "OPL-1",
    "price": "399.99",
    "currency": "USD",
    "data": [
        "data/ir_sequence.xml",
        "security/ir.model.access.csv",
        "views/view_account_invoice.xml",
        "views/view_attachment_line.xml",
        "views/view_crm_team.xml",
        "views/view_installment_template.xml",
        "views/view_product_category.xml",
        "views/view_project_worksite.xml",
        "views/view_property.xml",
        "views/news_contracts.xml",
        "views/view_property_contract.xml",
        "views/view_property_reservation.xml",
        "views/view_region.xml",
        "views/view_repair_order.xml",
        "views/view_res_config_settings.xml",
        "views/view_sale_order.xml",
        "views/view_sales_commission.xml",
        "views/news_recaudo_odoo.xml",
        "views/reporte_recaudo.xml",
        "views/menu_items.xml",
        "views/templates.xml",
        "views/property_dashboard_views.xml",
        "static/src/xml/home.xml",
        
    ],
    "assets": {
        "web.assets_backend": [
            "web/static/lib/luxon/luxon.js",
            "web/static/lib/Chart/Chart.js",
            "web/static/lib/chartjs-adapter-luxon/chartjs-adapter-luxon.js",
            "real_estate_bits/static/src/css/report-style.css",
            "real_estate_bits/static/src/xml/gmap.xml",
            # "real_estate_bits/static/src/js/init.js",
            # "real_estate_bits/static/src/js/map_widget.js",
            # "real_estate_bits/static/src/js/map_widget_multi.js",
            "real_estate_bits/static/src/js/place_autocomplete.js",
            # "real_estate_bits/static/src/js/place_autocomplete_multi.js",
            "real_estate_bits/static/src/xml/property_dashboard.xml",
            "real_estate_bits/static/src/xml/autocomplete.xml",
            "real_estate_bits/static/src/css/property_dashboard.css",
            "real_estate_bits/static/src/js/property_dashboard.js",
           # "real_estate_bits/static/src/js/property_filters.js", #real_estate_bits/static/src/js/property_filters.js
            #"real_estate_bits/static/src/css/style.scss",
        ],
        'web.assets_frontend': [
            "real_estate_bits/static/src/css/filters.css",
            "real_estate_bits/static/src/js/property_filters.js",
            "real_estate_bits/static/src/js/filters.js",
            "real_estate_bits/static/src/css/style.scss",
        ],
    },
    'external_dependencies': {
        "python": [
            "numerize",
            "requests",
        ],
    },
    "images": ["static/description/banner.gif"],
    'live_test_url': 'https://www.terabits.xyz/request_demo?source=index&version=16&app=real_estate_bits',
    "installable": True,
    "license": "LGPL-3",
    "auto_install": False,
    "application": True,
   # 'pre_init_hook': 'pre_init_hook',
    #'post_init_hook': 'post_init_hook',
   # 'uninstall_hook': 'uninstall_hook',


}

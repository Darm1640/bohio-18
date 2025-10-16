{
    'name': 'BOHIO CRM',
    'version': '18.0.1.0.3',
    'category': 'Sales/CRM',
    'summary': 'CRM especializado para negocio inmobiliario',
    'description': """
        BOHIO CRM
        =========
        Módulo de CRM especializado para gestión inmobiliaria:
        - Dashboard personalizado por vendedor
        - Pipeline de oportunidades con métricas
        - Extensión de leads con campos inmobiliarios
        - Comparador de hasta 4 propiedades
        - Cálculo automático de comisiones
        - Integración con propiedades

        Versión 18.0.1.0.3 - REFACTORIZACIÓN:
        - Eliminación de campos duplicados
        - Consolidación de nomenclatura
        - Migración automática de datos
    """,
    'author': 'BOHIO Inmobiliaria',
    'website': 'https://www.bohio.com.co',
    'depends': [
        'crm',
        'account',
        'hr_expense',
        'real_estate_bits',
        'portal',
        'l10n_co_dian',  # Facturación electrónica Colombia
    ],
    'data': [
        # Seguridad
        'security/ir.model.access.csv',

        # Datos - IMPORTANTE: server_actions ANTES de automated_actions
        'data/crm_server_actions.xml',       # Server actions con codigo Python (Odoo 18)
        'data/crm_automated_actions_v2.xml',  # Base automations que referencian server actions

        # Reportes PDF - Bohío Consultores
        'report/report_comprobante_egreso.xml',   # Comprobante de Egreso
        'report/report_recibo_caja.xml',          # Recibo de Caja (Ingreso)
        'report/report_factura_electronica.xml',  # Factura Electrónica DIAN

        # Vistas Principales
        'views/crm_lead_views.xml',          # Vista List y Kanban mejoradas con js_class
        'views/crm_dashboard.xml',           # Dashboard CRM BOHIO
        'views/menu.xml',                    # Menús (vacío por ahora)
    ],
    'assets': {
        'web.assets_backend': [
            # CSS Activos
            'bohio_crm/static/src/css/bohio_crm_kanban.css',
            'bohio_crm/static/src/css/bohio_crm_list.css',
            'bohio_crm/static/src/css/bohio_dashboard.css',
            'bohio_crm/static/src/css/crm_modern_style.css',       # Estilos Modernos con Iconos Bootstrap
            'bohio_crm/static/src/css/property_compare_zoom.css',  # Widget de Zoom

            # JavaScript - Vistas Kanban y List con Dashboard
            'bohio_crm/static/src/views/bohio_crm_dashboard.js',
            'bohio_crm/static/src/views/bohio_crm_dashboard.xml',
            'bohio_crm/static/src/views/bohio_crm_kanbanview.js',
            'bohio_crm/static/src/views/bohio_crm_kanbanview.xml',
            'bohio_crm/static/src/views/bohio_crm_modern_views.js',

            # JavaScript - Dashboard del Vendedor (con barra deslizable)
            'bohio_crm/static/src/js/crm_salesperson_dashboard.js',
            'bohio_crm/static/src/xml/crm_salesperson_dashboard.xml',

            # JavaScript - Widget de Zoom para Comparación de Propiedades
            'bohio_crm/static/src/js/property_compare_zoom.js',
            'bohio_crm/static/src/xml/property_compare_zoom.xml',
        ],
        'web.report_assets_common': [
            # Estilos para reportes PDF
            'bohio_crm/static/src/scss/bohio_reports.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'web_icon': 'bohio_crm/static/description/icon.png',
}

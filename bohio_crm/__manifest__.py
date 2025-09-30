{
    'name': 'BOHIO CRM',
    'version': '18.0.1.0.1',
    'category': 'Sales/CRM',
    'summary': 'CRM especializado para negocio inmobiliario',
    'description': """
        BOHIO CRM
        =========
        Módulo de CRM especializado para gestión inmobiliaria:
        - Extensión de leads con campos inmobiliarios
        - Comparador de hasta 4 propiedades
        - Dashboard CRM personalizado
        - Cálculo automático de comisiones
        - Métricas de arriendo y ventas
        - Gestión de PQRS
        - Integración con propiedades
        - Vista Timeline con actividades y propiedades
    """,
    'author': 'BOHIO Inmobiliaria',
    'website': 'https://www.bohio.com.co',
    'depends': [
        'crm',
        'account',
        'real_estate_bits',
        'portal',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
        'views/crm_lead_form_complete.xml',
        'views/bohio_crm_complete_views.xml',
        'views/crm_metrics_views.xml',
        'views/company_contract_config_views.xml',
        'views/bohio_crm_menu.xml',
        'report/property_comparison_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bohio_crm/static/src/css/crm_metrics.css',
            'bohio_crm/static/src/css/crm_bohio_form.css',
            'bohio_crm/static/src/css/bohio_crm_kanban.css',
            'bohio_crm/static/src/css/bohio_crm_list.css',
            'bohio_crm/static/src/js/crm_metrics_controller.js',
            'bohio_crm/static/src/js/crm_bohio_form.js',
        ],
    },
    'external_dependencies': {
        'javascript': ['leaflet'],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

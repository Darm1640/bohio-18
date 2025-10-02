{
    'name': 'BOHIO CRM',
    'version': '18.0.1.0.2',
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
        # Seguridad
        'security/ir.model.access.csv',

        # Vistas
        'views/bohio_crm_complete_views.xml',
        'views/crm_lead_form_complete.xml',
        'views/company_contract_config_views.xml',
        'views/crm_salesperson_dashboard_views.xml',

        # Acciones y Menús
        'views/bohio_crm_actions.xml',
        'views/bohio_crm_menu.xml',

        # Reportes
        'report/property_comparison_report.xml',

        # Timeline View
        'views/bohio_timeline_view_actions.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # CSS
            'bohio_crm/static/src/css/crm_bohio_form.css',
            'bohio_crm/static/src/css/bohio_crm_kanban.css',
            'bohio_crm/static/src/css/bohio_crm_list.css',
            'bohio_crm/static/src/css/bohio_dashboard.css',

            # JS - Dashboard
            'bohio_crm/static/src/js/crm_bohio_form.js',
            'bohio_crm/static/src/views/bohio_crm_dashboard.js',
            'bohio_crm/static/src/views/bohio_crm_dashboard.xml',
            'bohio_crm/static/src/views/bohio_crm_kanbanview.js',
            'bohio_crm/static/src/views/bohio_crm_kanbanview.xml',

            # Timeline View
            'bohio_crm/static/src/components/timeline_view/bohio_timeline_view.scss',
            'bohio_crm/static/src/components/timeline_view/bohio_timeline_view.js',
            'bohio_crm/static/src/components/timeline_view/bohio_timeline_view.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
}

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
        'hr_expense',
        'real_estate_bits',
        'portal',
    ],
    'data': [
        # Seguridad
        'security/ir.model.access.csv',

        # Datos
        'data/crm_automated_actions.xml',  # NUEVO: Automatizaciones

        # Vistas
        'views/bohio_crm_complete_views.xml',
        'views/crm_lead_form_complete.xml',
        'views/crm_lead_quick_create_form.xml',  # NUEVA: Quick Create Inteligente
        'views/company_contract_config_views.xml',
        'views/crm_salesperson_dashboard_views.xml',

        # Acciones y Menús
        'views/bohio_crm_actions.xml',
        'views/bohio_crm_menu.xml',

        # Reportes
        'report/property_comparison_report.xml',
        'views/crm_capture_commission_report.xml',  # NUEVO: Reportes de Comisiones y Campañas

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
            'bohio_crm/static/src/css/crm_quick_create_smart.css',  # NUEVO: Quick Create CSS

            # JS - Dashboard
            'bohio_crm/static/src/js/crm_bohio_form.js',
            'bohio_crm/static/src/views/bohio_crm_dashboard.js',
            'bohio_crm/static/src/views/bohio_crm_dashboard.xml',
            'bohio_crm/static/src/views/bohio_crm_kanbanview.js',
            'bohio_crm/static/src/views/bohio_crm_kanbanview.xml',

            # Quick Create Inteligente
            'bohio_crm/static/src/js/crm_quick_create_smart.js',  # NUEVO: Quick Create JS

            # Salesperson Dashboard
            'bohio_crm/static/src/js/crm_salesperson_dashboard.js',
            'bohio_crm/static/src/xml/crm_salesperson_dashboard.xml',

            # Timeline View V2 (Vista timeline principal)
            'bohio_crm/static/src/components/timeline_view_v2/bohio_timeline_view_v2.js',
            'bohio_crm/static/src/components/timeline_view_v2/bohio_timeline_view_v2.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
    'web_icon': 'bohio_crm/static/description/icon.png',
}

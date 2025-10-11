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

        # Datos - IMPORTANTE: server_actions ANTES de automated_actions
        'data/crm_server_actions.xml',       # Server actions con codigo Python (Odoo 18)
        'data/crm_automated_actions_v2.xml',  # Base automations que referencian server actions

        # Acciones y Reportes - ANTES de las vistas que las referencian
        'views/bohio_crm_actions.xml',
        'report/property_comparison_report.xml',
        'views/crm_capture_commission_report.xml',  # Define action_crm_capture_commission_report

        # Vistas - DESPUES de las acciones
        'views/bohio_crm_complete_views.xml',
        'views/crm_lead_form_complete.xml',          # USA action_crm_capture_commission_report
        'views/crm_lead_quick_create_form.xml',
        'views/crm_lead_form_expandable_full.xml',   # Vista Form Expandible Completa
        'views/crm_lead_kanban_canvas.xml',          # Vista Kanban Canvas ÚNICA (con mapa y lista)
        'views/company_contract_config_views.xml',
        'views/crm_salesperson_dashboard_views.xml',

        # Menús - Al final
        'views/bohio_crm_menu.xml',

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
            'bohio_crm/static/src/css/crm_quick_create_smart.css',  # Quick Create CSS
            'bohio_crm/static/src/css/crm_form_expandable.css',     # Form Expandible CSS
            'bohio_crm/static/src/css/crm_kanban_canvas.css',       # Kanban Canvas CSS ÚNICA

            # JS - Dashboard
            'bohio_crm/static/src/js/crm_bohio_form.js',
            'bohio_crm/static/src/views/bohio_crm_dashboard.js',
            'bohio_crm/static/src/views/bohio_crm_dashboard.xml',
            'bohio_crm/static/src/views/bohio_crm_kanbanview.js',
            'bohio_crm/static/src/views/bohio_crm_kanbanview.xml',

            # Quick Create Inteligente
            'bohio_crm/static/src/js/crm_quick_create_smart.js',    # Quick Create JS

            # Kanban Expandible con Sidebar
            'bohio_crm/static/src/js/crm_kanban_sidebar.js',        # Kanban Sidebar JS
            'bohio_crm/static/src/xml/crm_kanban_sidebar_templates.xml',  # Kanban Sidebar Templates

            # Form Expandible Completo
            'bohio_crm/static/src/js/crm_form_expandable.js',       # Form Expandible JS
            'bohio_crm/static/src/js/crm_map_widget.js',             # Widget de Mapa Leaflet
            'bohio_crm/static/src/xml/crm_map_widget_template.xml', # Template del Mapa

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

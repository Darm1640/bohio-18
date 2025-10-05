{
    'name': 'BOHIO Real Estate - Portal & Loans',
    'version': '18.0.3.0.0',
    'category': 'Portal',
    'summary': 'Portal clientes inmobiliarios y gestión de préstamos',
    'description': """
        BOHIO Real Estate - Portal & Loans
        ===================================
        Portal personalizado para:
        - Propietarios: dashboard, propiedades, pagos, facturas, préstamos
        - Arrendatarios: contratos, pagos, facturas
        - Gestión de préstamos con plantillas

        IMPORTANTE:
        - La lógica de CRM está en bohio_crm
        - El website público está en theme_bohio_real_estate
        - Este módulo solo maneja PORTAL y PRÉSTAMOS
    """,
    'author': 'BOHIO Inmobiliaria',
    'website': 'https://www.bohio.com.co',
    'depends': [
        'real_estate_bits',
        'bohio_crm',
        'website',
        'helpdesk',
        'portal',
        'account_loans',  # Odoo Enterprise - Gestión de préstamos
    ],
    'external_dependencies': {
        'odoo': ['documents', 'sign'],  # Opcionales - Odoo Enterprise
    },
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        # Data
        'data/property_document_category_data.xml',

        # Partner Views
        'views/res_partner_views.xml',

        # Contract Types & Documents
        # 'views/property_contract_type_views.xml',  # Migrado a real_estate_bits
        'views/property_contract_inherit_views.xml',

        # Loan Management
        'views/account_loan_template_views.xml',
        'views/account_loan_views.xml',
        'views/account_loan_menu.xml',

        # Portal Access
        'views/portal_access_actions.xml',

        # Portal Templates
        'views/portal/common/portal_my_home.xml',
        'views/portal/common/portal_layout.xml',
        'views/portal/common/no_role.xml',
        'views/portal/common/tickets.xml',
        'views/portal/common/admin_portal_view.xml',

        # Owner Portal
        'views/portal/owner/owner_dashboard.xml',
        'views/portal/owner/owner_properties.xml',
        'views/portal/owner/owner_payments.xml',
        'views/portal/owner/owner_invoices.xml',
        'views/portal/owner/owner_opportunities.xml',
        'views/portal/owner/owner_documents.xml',

        # Tenant Portal
        'views/portal/tenant/tenant_dashboard.xml',
        'views/portal/tenant/tenant_contracts.xml',
        'views/portal/tenant/tenant_payments.xml',
        'views/portal/tenant/tenant_invoices.xml',
        'views/portal/tenant/tenant_documents.xml',

        # Salesperson Portal
        'views/portal/salesperson/salesperson_dashboard.xml',
        'views/portal/salesperson/salesperson_opportunities.xml',
        'views/portal/salesperson/salesperson_opportunity_detail.xml',
        'views/portal/salesperson/salesperson_clients.xml',
        'views/portal/salesperson/salesperson_properties.xml',

        # Portal Templates
        'views/portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Solo CSS de portal (el resto está en theme)
            'bohio_real_estate/static/src/css/mybohio_portal.css',
        ],
        'web.assets_backend': [
        ],
    },
    'images': [
        'static/description/icon.png',
        'static/description/banner.jpg',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'web_icon': 'bohio_real_estate/static/description/icon.png',
}

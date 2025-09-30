{
    'name': 'BOHIO Real Estate Portal & Website',
    'version': '18.0.1.0.2',
    'category': 'Website',
    'summary': 'BOHIO portal for owners/tenants and public website',
    'description': """
        BOHIO Real Estate Portal & Website
        ===================================
        Portal personalizado para:
        - Propietarios: dashboard, propiedades, pagos, facturas, oportunidades
        - Arrendatarios: contratos, pagos, facturas
        - Website público con búsqueda avanzada
        - Sistema PQRS con Helpdesk
    """,
    'author': 'BOHIO Inmobiliaria',
    'website': 'https://www.bohio.com.co',
    'depends': [
        'real_estate_bits',
        'bohio_crm',
        'website',
        'helpdesk',
        'portal',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/res_partner_views.xml',
        'views/website_templates.xml',
        'views/portal/common/portal_my_home.xml',
        'views/portal/common/portal_layout.xml',
        'views/portal/common/no_role.xml',
        'views/portal/owner/owner_dashboard.xml',
        'views/portal/owner/owner_properties.xml',
        'views/portal/owner/owner_payments.xml',
        'views/portal/owner/owner_invoices.xml',
        'views/portal/owner/owner_opportunities.xml',
        'views/portal/owner/owner_documents.xml',
        'views/portal/tenant/tenant_dashboard.xml',
        'views/portal/tenant/tenant_contracts.xml',
        'views/portal/tenant/tenant_payments.xml',
        'views/portal/tenant/tenant_invoices.xml',
        'views/portal/tenant/tenant_documents.xml',
        'views/portal/common/tickets.xml',
        'views/portal/common/admin_portal_view.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'bohio_real_estate/static/src/css/mybohio_portal.css',
            'bohio_real_estate/static/src/js/utils/api.js',
            'bohio_real_estate/static/src/js/utils/dom.js',
            'bohio_real_estate/static/src/js/utils/formatters.js',
            'bohio_real_estate/static/src/js/utils/debounce.js',
            'bohio_real_estate/static/src/js/utils/validation.js',
            'bohio_real_estate/static/src/js/utils/url.js',
            'bohio_real_estate/static/src/js/search/search_bar.js',
            'bohio_real_estate/static/src/js/properties/property_card.js',
            'bohio_real_estate/static/src/js/properties/properties_list.js',
            'bohio_real_estate/static/src/js/homepage/homepage.js',
            'bohio_real_estate/static/src/js/contact/contact_form.js',
        ],
        'web.assets_backend': [
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
}

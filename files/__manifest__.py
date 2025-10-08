# -*- coding: utf-8 -*-
{
    'name': 'BOHIO Real Estate - Theme & Website',
    'version': '2.0.0',
    'category': 'Website/Website',
    'summary': 'Tema y sitio web personalizado para BOHIO Inmobiliaria con modo oscuro y diseño responsivo',
    'description': """
        BOHIO Real Estate - Tema Premium
        ===================================
        
        Características principales:
        ----------------------------
        * Diseño moderno y responsivo
        * Modo oscuro automático y manual
        * Búsqueda avanzada de propiedades
        * Sistema de favoritos y comparación
        * Optimizado para SEO
        * Accesibilidad AAA
        * Lazy loading de imágenes
        * Animaciones suaves
        * Fuentes personalizadas
        * Integración completa con Odoo
        
        Versión 2.0:
        ------------
        * Rediseño completo del frontend
        * Implementación de modo oscuro
        * Mejoras de rendimiento
        * Optimización móvil
        * Sistema de favoritos
        * Comparador de propiedades
        * Búsqueda por código
        * Filtros persistentes
    """,
    'author': 'BOHIO Inmobiliaria S.A.S.',
    'website': 'https://www.bohio.com.co',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'website',
        'website_sale',
        'product',
        'portal',
    ],
    'data': [
        # Seguridad
        'security/ir.model.access.csv',
        
        # Datos
        'data/property_types.xml',
        
        # Vistas
        'views/homepage_mejorado.xml',
        'views/properties_shop_template_mejorado.xml',
        'views/property_detail_view.xml',
        'views/portal_templates.xml',
        'views/website_menu.xml',
        
        # Templates
        'views/templates/header.xml',
        'views/templates/footer.xml',
        'views/templates/snippets.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # CSS - Orden de carga
            'bohio_real_estate/static/src/css/bohio_custom_styles.css',
            
            # JavaScript - Orden de carga
            'bohio_real_estate/static/src/js/bohio_custom_scripts.js',
        ],
        
        # Assets específicos para backend
        'web.assets_backend': [
            'bohio_real_estate/static/src/css/backend_styles.css',
        ],
        
        # Assets para modo oscuro
        'web._assets_primary_variables': [
            'bohio_real_estate/static/src/css/variables.css',
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/icon.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 10,
    'price': 0.00,
    'currency': 'USD',
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}

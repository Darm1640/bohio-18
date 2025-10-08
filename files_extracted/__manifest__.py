# -*- coding: utf-8 -*-
{
    'name': 'Real Estate Bits - Advanced Property Search',
    'version': '18.0.1.0.0',
    'category': 'Real Estate/Property Management',
    'summary': 'Advanced property search system with comparison and smart autocomplete',
    'description': """
Real Estate Advanced Property Search
=====================================

Complete property search system with:
* Multi-context search (public, admin, project, quick)
* Smart autocomplete with subdivisions
* Property comparison system (up to 4 properties)
* Dynamic filters by location, price, features
* Responsive UI with animations
* Real-time notifications
* Session persistence

Key Features:
-------------
- Contextual Search: Different search modes for different users
- Smart Autocomplete: Search cities, neighborhoods, projects, or properties
- Property Comparison: Compare up to 4 properties side-by-side
- Automatic Difference Detection: Highlights differences between properties
- Advanced Filters: Dynamic filters by type, location, price, features
- Responsive Design: Works on desktop, tablet, and mobile
- Performance Optimized: Debouncing, caching, lazy loading

Use Cases:
----------
1. Public Portal: End customers searching for properties
2. Admin Dashboard: Real estate agents managing properties
3. Project Pages: Showcase properties from specific projects
4. Quick Search: Embedded widgets in other pages

Technical:
----------
- Odoo 18.0 compatible
- Python 3.10+
- PostgreSQL 12+
- Bootstrap 4 responsive design
- Vanilla JavaScript (no external dependencies)
    """,
    
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    
    # Dependencies
    'depends': [
        'base',
        'website',
        'website_sale',
        'product',
        'web',
    ],
    
    # Data files
    'data': [
        # Security
        'security/ir.model.access.csv',
        
        # Views
        'views/property_search_templates.xml',
        
        # Menus
        'views/website_menus.xml',
    ],
    
    # Assets
    'assets': {
        'web.assets_frontend': [
            # JavaScript
            'real_estate_bits/static/src/js/property_search.js',
            
            # CSS
            'real_estate_bits/static/src/css/property_search.css',
        ],
        
        'web.assets_backend': [
            # Si necesitas assets en el backend
        ],
    },
    
    # Images and documentation
    'images': [
        'static/description/icon.png',
        'static/description/banner.png',
        'static/description/screenshot_1.png',
        'static/description/screenshot_2.png',
    ],
    
    # Module configuration
    'installable': True,
    'application': True,
    'auto_install': False,
    
    # Odoo App Store (si aplica)
    'price': 0.00,
    'currency': 'USD',
    
    # External dependencies
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    
    # Demo data (opcional)
    'demo': [
        # 'demo/property_demo.xml',
    ],
    
    # QWeb templates
    'qweb': [
        # Si tienes templates QWeb adicionales
    ],
    
    # Post-init hook (opcional)
    # 'post_init_hook': 'post_init_hook',
    
    # Uninstall hook (opcional)
    # 'uninstall_hook': 'uninstall_hook',
}

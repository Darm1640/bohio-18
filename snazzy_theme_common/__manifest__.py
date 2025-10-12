# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.
{
    # Theme information
    'name': 'Snazzy Theme Common',
    'category': 'Website',
    'version': '18.0.0.7',
    'author': 'Bizople Solutions Pvt. Ltd.',
    'website': 'https://www.bizople.com',
    'summary': 'Snazzy Theme Common',
    'description': """Snazzy Theme Common""",
    'depends': [
        'website',
        'portal',
        'web_editor',
        'website_blog',
        'sale_management',
        'website_sale',
        'website_sale_wishlist',
        'website_sale_comparison',
        'website_sale_stock',
        'stock',
    ],

    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/category_template.xml',
        'views/brand_template.xml',
        'views/manifest.xml',
        'views/pwa_offline.xml',
        #Megamenus
        'views/megamenus/s_megamenu_one_snippet.xml',
        'views/megamenus/s_mega_menu_category_one.xml',
        'views/megamenus/s_megamenu_two_snippet.xml',
        'views/megamenus/s_mega_menu_category_two_snippet.xml',
        'views/megamenus/s_megamenu_three_snippet.xml',
        'views/megamenus/s_mega_menu_category_three_snippet.xml',
        'views/megamenus/s_mega_menu_dynamic_snippet.xml',
        'views/megamenus/s_megamenu_four_snippet.xml',
        'views/megamenus/s_megamenu_five_snippet.xml',
    ],
    'images': [
       'static/description/banner.jpg'
    ],

    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'OPL-1',
    'price': 25,
    'currency': 'EUR',
}

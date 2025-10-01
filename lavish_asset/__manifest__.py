# -*- coding: utf-8 -*-
{
    'name': 'Lavish Asset NIIF Colombia',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Assets',
    'summary': 'Gestión de Activos Fijos NIIF para Colombia',
    'description': """
        Módulo de activos fijos con doble depreciación NIIF y Fiscal para Colombia.
        Basado en la arquitectura de Odoo 18 Enterprise.
    """,
    'author': 'Lavish',
    'website': 'https://www.lavish.com.co',
    'depends': [
        'account_asset',
        'niif_account_co',
    ],
    'data': [
        'views/account_asset_views.xml',
        'views/menuitem.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
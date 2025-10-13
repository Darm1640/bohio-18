#!/usr/bin/env python3
"""
Verificar estado del módulo theme_bohio_real_estate en Odoo.com
"""

import xmlrpc.client

# Configuración Odoo.com
URL = 'https://darm1640-bohio-18.odoo.com'
DB = 'darm1640-bohio-18'
USERNAME = 'darm1640@hotmail.com'
PASSWORD = 'tE^9E6*9'

print(f"[*] Conectando a {URL}...")

try:
    common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})

    if not uid:
        print("[ERROR] No se pudo autenticar")
        exit(1)

    print(f"[OK] Autenticado - UID: {uid}")

    models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

    # Buscar todos los módulos de bohio/real estate
    print("\n[*] Buscando módulos relacionados con 'bohio' y 'real_estate'...")

    modules = models.execute_kw(DB, uid, PASSWORD,
        'ir.module.module', 'search_read',
        [[['name', 'ilike', 'bohio']]],
        {'fields': ['name', 'state', 'summary', 'latest_version', 'installed_version']})

    if modules:
        print(f"\n[INFO] Módulos BOHIO encontrados: {len(modules)}")
        for mod in modules:
            print(f"\n  Nombre: {mod['name']}")
            print(f"  Estado: {mod['state']}")
            print(f"  Resumen: {mod.get('summary', 'N/A')}")
            print(f"  Versión instalada: {mod.get('installed_version', 'N/A')}")
            print(f"  Última versión: {mod.get('latest_version', 'N/A')}")

    # Buscar módulos real_estate
    modules_re = models.execute_kw(DB, uid, PASSWORD,
        'ir.module.module', 'search_read',
        [[['name', 'ilike', 'real_estate']]],
        {'fields': ['name', 'state', 'summary']})

    if modules_re:
        print(f"\n[INFO] Módulos REAL_ESTATE encontrados: {len(modules_re)}")
        for mod in modules_re:
            print(f"\n  Nombre: {mod['name']}")
            print(f"  Estado: {mod['state']}")
            print(f"  Resumen: {mod.get('summary', 'N/A')}")

    # Buscar específicamente theme_bohio_real_estate
    print("\n" + "="*60)
    print("[*] Verificando módulo theme_bohio_real_estate...")

    theme_mod = models.execute_kw(DB, uid, PASSWORD,
        'ir.module.module', 'search_read',
        [[['name', '=', 'theme_bohio_real_estate']]],
        {'fields': ['name', 'state', 'summary', 'latest_version',
                    'installed_version', 'author', 'website']})

    if theme_mod:
        mod = theme_mod[0]
        print(f"\n[INFO] Módulo encontrado:")
        print(f"  ID: {mod['id']}")
        print(f"  Nombre: {mod['name']}")
        print(f"  Estado: {mod['state']}")
        print(f"  Autor: {mod.get('author', 'N/A')}")
        print(f"  Website: {mod.get('website', 'N/A')}")
        print(f"  Versión instalada: {mod.get('installed_version', 'N/A')}")
        print(f"  Última versión: {mod.get('latest_version', 'N/A')}")

        if mod['state'] == 'installed':
            print("\n[OK] El módulo ESTÁ instalado")
        elif mod['state'] == 'uninstalled':
            print("\n[AVISO] El módulo está DESINSTALADO")
        elif mod['state'] == 'to upgrade':
            print("\n[AVISO] El módulo tiene actualización pendiente")
        else:
            print(f"\n[INFO] Estado del módulo: {mod['state']}")
    else:
        print("\n[ERROR] Módulo theme_bohio_real_estate NO encontrado")

    # Verificar las rutas/controladores
    print("\n" + "="*60)
    print("[*] Verificando rutas del módulo...")

    # Buscar la vista homepage
    homepage_view = models.execute_kw(DB, uid, PASSWORD,
        'ir.ui.view', 'search_read',
        [[['name', 'ilike', 'bohio_homepage'], ['active', '=', True]]],
        {'fields': ['name', 'model', 'type', 'key', 'active'], 'limit': 5})

    if homepage_view:
        print(f"\n[INFO] Vistas de homepage encontradas: {len(homepage_view)}")
        for view in homepage_view:
            print(f"  - {view['name']} (ID: {view['id']}, Tipo: {view.get('type', 'N/A')})")
    else:
        print("\n[AVISO] No se encontraron vistas de homepage")

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()

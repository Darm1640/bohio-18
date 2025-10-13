#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificar si la vista bohio_homepage_new existe en Odoo
"""

import xmlrpc.client

url = 'https://darm1640-bohio-18.odoo.com'
db = 'darm1640-bohio-18-main-24081960'
username = 'admin'
password = '123456'

def main():
    print("="*70)
    print("VERIFICANDO VISTA DE HOMEPAGE")
    print("="*70)

    try:
        # Conectar
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})

        if not uid:
            print("ERROR: No se pudo autenticar")
            return

        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        print(f"[OK] Conectado - UID: {uid}")

        # Buscar la vista bohio_homepage_new
        print("\n1. Buscando vista 'bohio_homepage_new':")
        views = models.execute_kw(
            db, uid, password,
            'ir.ui.view', 'search_read',
            [[('name', 'ilike', 'bohio_homepage')]],
            {'fields': ['id', 'name', 'key', 'type', 'active', 'model']}
        )

        if views:
            print(f"   Encontradas {len(views)} vistas:")
            for view in views:
                print(f"\n   ID: {view['id']}")
                print(f"   Nombre: {view['name']}")
                print(f"   Key: {view.get('key', 'N/A')}")
                print(f"   Tipo: {view.get('type', 'N/A')}")
                print(f"   Activa: {view.get('active', False)}")
                print(f"   Modelo: {view.get('model', 'N/A')}")
        else:
            print("   [PROBLEMA] NO se encontró la vista bohio_homepage_new")
            print("   → El módulo necesita ser actualizado")

        # Verificar el template específico
        print("\n2. Buscando template con XML ID:")
        try:
            template_id = models.execute_kw(
                db, uid, password,
                'ir.model.data', 'search_read',
                [[
                    ('module', '=', 'theme_bohio_real_estate'),
                    ('name', '=', 'bohio_homepage_new')
                ]],
                {'fields': ['id', 'name', 'model', 'res_id']}
            )

            if template_id:
                print(f"   [OK] Template encontrado:")
                print(f"   Res ID: {template_id[0]['res_id']}")
            else:
                print("   [PROBLEMA] Template XML ID no encontrado")
                print("   → Necesitas actualizar el módulo")
        except Exception as e:
            print(f"   Error: {e}")

        # Verificar estado del módulo
        print("\n3. Verificando estado del módulo:")
        module = models.execute_kw(
            db, uid, password,
            'ir.module.module', 'search_read',
            [[('name', '=', 'theme_bohio_real_estate')]],
            {'fields': ['name', 'state', 'latest_version', 'installed_version']}
        )

        if module:
            mod = module[0]
            print(f"   Módulo: {mod['name']}")
            print(f"   Estado: {mod['state']}")
            print(f"   Versión instalada: {mod.get('installed_version', 'N/A')}")
            print(f"   Última versión: {mod.get('latest_version', 'N/A')}")

            if mod['state'] != 'installed':
                print(f"\n   [PROBLEMA] Módulo NO está instalado")
            else:
                print(f"\n   [OK] Módulo está instalado")
        else:
            print("   [ERROR] Módulo no encontrado")

        # Verificar controlador
        print("\n4. Verificando ruta del controlador:")
        print("   Ruta: /")
        print("   Controlador: BohioRealEstateController.homepage_new")
        print("   Template esperado: theme_bohio_real_estate.bohio_homepage_new")

        print("\n" + "="*70)
        print("RESUMEN:")
        print("="*70)
        if views:
            print("✅ La vista existe en la base de datos")
            print("\nSi la homepage no muestra los contenedores:")
            print("  1. Verifica que la vista esté ACTIVA")
            print("  2. Limpia cache: Settings → Technical → Clear Assets")
            print("  3. Recarga la página con Ctrl+Shift+R")
        else:
            print("❌ La vista NO existe en la base de datos")
            print("\nACCIÓN REQUERIDA:")
            print("  1. Ir a Settings → Apps")
            print("  2. Buscar 'theme_bohio_real_estate'")
            print("  3. Clic en 'Upgrade' o 'Actualizar'")
            print("  4. Esperar a que termine")
            print("  5. Refrescar la homepage")

    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == '__main__':
    main()

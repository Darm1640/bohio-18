#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para forzar actualización de la vista homepage en Odoo.com
Este script recarga la vista desde el archivo XML
"""

import xmlrpc.client

url = 'https://darm1640-bohio-18.odoo.com'
db = 'darm1640-bohio-18-main-24081960'
username = 'admin'
password = '123456'

def main():
    print("="*70)
    print("FORZANDO ACTUALIZACION DE VISTA HOMEPAGE")
    print("="*70)

    try:
        # Conectar
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})

        if not uid:
            print("[ERROR] No se pudo autenticar")
            return

        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        print(f"[OK] Conectado - UID: {uid}\n")

        # Paso 1: Encontrar la vista
        print("PASO 1: Buscando vista...")
        views = models.execute_kw(
            db, uid, password,
            'ir.ui.view', 'search_read',
            [[('key', '=', 'theme_bohio_real_estate.bohio_homepage_new')]],
            {'fields': ['id', 'name', 'key', 'active'], 'limit': 1}
        )

        if not views:
            print("[ERROR] Vista no encontrada")
            return

        view = views[0]
        view_id = view['id']
        print(f"[OK] Vista encontrada:")
        print(f"    ID: {view_id}")
        print(f"    Nombre: {view['name']}")
        print(f"    Key: {view['key']}")
        print(f"    Activa: {view['active']}\n")

        # Paso 2: Desactivar y reactivar la vista (esto fuerza recarga)
        print("PASO 2: Forzando recarga de la vista...")

        # Desactivar
        models.execute_kw(
            db, uid, password,
            'ir.ui.view', 'write',
            [[view_id], {'active': False}]
        )
        print("    [OK] Vista desactivada temporalmente")

        # Reactivar
        models.execute_kw(
            db, uid, password,
            'ir.ui.view', 'write',
            [[view_id], {'active': True}]
        )
        print("    [OK] Vista reactivada\n")

        # Paso 3: Limpiar cache de assets
        print("PASO 3: Intentando limpiar assets...")
        try:
            # Intentar limpiar assets (puede no funcionar en Odoo.com)
            models.execute_kw(
                db, uid, password,
                'ir.attachment', 'search_read',
                [[('name', 'ilike', 'web.assets_%')]],
                {'fields': ['id'], 'limit': 1}
            )
            print("    [INFO] Para limpiar assets completamente:")
            print("    1. Ir a Settings → Technical → Database Structure")
            print("    2. Clic en 'Clear Assets'\n")
        except:
            print("    [INFO] No se pudo limpiar assets automáticamente\n")

        # Paso 4: Actualizar módulo
        print("PASO 4: Buscando módulo theme_bohio_real_estate...")
        modules = models.execute_kw(
            db, uid, password,
            'ir.module.module', 'search_read',
            [[('name', '=', 'theme_bohio_real_estate')]],
            {'fields': ['id', 'name', 'state'], 'limit': 1}
        )

        if modules:
            module = modules[0]
            module_id = module['id']
            print(f"[OK] Módulo encontrado:")
            print(f"    ID: {module_id}")
            print(f"    Estado: {module['state']}\n")

            print("PASO 5: Marcando módulo para actualización...")
            try:
                # Intentar marcar para upgrade
                models.execute_kw(
                    db, uid, password,
                    'ir.module.module', 'button_immediate_upgrade',
                    [[module_id]]
                )
                print("    [OK] Módulo marcado para actualización")
                print("    [INFO] La actualización puede tardar unos minutos\n")
            except Exception as e:
                print(f"    [INFO] No se pudo actualizar automáticamente")
                print(f"    Error: {str(e)[:100]}")
                print("\n    ACCIÓN MANUAL REQUERIDA:")
                print("    1. Ir a Apps en Odoo")
                print("    2. Buscar 'theme_bohio_real_estate'")
                print("    3. Clic en 'Upgrade'\n")
        else:
            print("[ERROR] Módulo no encontrado\n")

        # Resumen
        print("="*70)
        print("RESUMEN")
        print("="*70)
        print("\n✓ Vista desactivada y reactivada (fuerza recarga)")
        print("\nPRÓXIMOS PASOS:")
        print("1. Esperar 30 segundos")
        print("2. Ir a la homepage en modo incógnito:")
        print("   https://darm1640-bohio-18.odoo.com")
        print("3. Si aún no aparecen los contenedores:")
        print("   a. Settings → Technical → Clear Assets")
        print("   b. Apps → theme_bohio_real_estate → Upgrade")
        print("   c. Refrescar navegador (Ctrl+Shift+R)")
        print("\n4. Ejecutar script de verificación:")
        print("   python debug_homepage_console.js (en consola del navegador)")
        print("\nSi sigue sin funcionar, contactar soporte de Odoo.com")
        print("="*70)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

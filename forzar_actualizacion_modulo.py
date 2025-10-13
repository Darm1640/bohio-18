#!/usr/bin/env python3
"""
Script para forzar actualización del módulo theme_bohio_real_estate en Odoo.com
"""

import xmlrpc.client
import sys

# Configuración
URL = 'https://darm1640-bohio-18.odoo.com'
DB = 'bohio_db'  # El nombre real de la base de datos
USERNAME = 'darm1640@hotmail.com'
PASSWORD = 'tE^9E6*9'
MODULE_NAME = 'theme_bohio_real_estate'

def main():
    print(f"[*] Conectando a {URL}...")

    try:
        # Autenticación
        common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
        uid = common.authenticate(DB, USERNAME, PASSWORD, {})

        if not uid:
            print("[ERROR] Error de autenticacion")
            return False

        print(f"[OK] Conectado - UID: {uid}")

        models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

        # Buscar el módulo
        print(f"\n[*] Buscando modulo '{MODULE_NAME}'...")
        module_ids = models.execute_kw(DB, uid, PASSWORD,
            'ir.module.module', 'search',
            [[('name', '=', MODULE_NAME)]])

        if not module_ids:
            print(f"[ERROR] Modulo '{MODULE_NAME}' no encontrado")
            return False

        module_id = module_ids[0]
        print(f"[OK] Modulo encontrado - ID: {module_id}")

        # Obtener info del módulo
        module_info = models.execute_kw(DB, uid, PASSWORD,
            'ir.module.module', 'read',
            [module_id], {'fields': ['name', 'state', 'latest_version']})

        print(f"\n[INFO] Informacion del modulo:")
        print(f"   Nombre: {module_info[0]['name']}")
        print(f"   Estado: {module_info[0]['state']}")
        print(f"   Version: {module_info[0].get('latest_version', 'N/A')}")

        # Actualizar módulo
        print(f"\n[*] Actualizando modulo...")
        models.execute_kw(DB, uid, PASSWORD,
            'ir.module.module', 'button_immediate_upgrade',
            [[module_id]])

        print("[OK] Modulo actualizado correctamente")

        # Limpiar cachés
        print("\n[*] Limpiando caches...")

        # Limpiar caché de vistas
        models.execute_kw(DB, uid, PASSWORD,
            'ir.ui.view', 'clear_caches', [[]])
        print("   [OK] Cache de vistas limpiado")

        # Limpiar caché de QWeb
        models.execute_kw(DB, uid, PASSWORD,
            'ir.qweb', 'clear_caches', [[]])
        print("   [OK] Cache de QWeb limpiado")

        print("\n" + "="*60)
        print("[OK] ACTUALIZACION COMPLETADA")
        print("="*60)
        print("\n[PROXIMOS PASOS]:")
        print("1. Limpia el cache del navegador (Ctrl + Shift + Delete)")
        print("2. Cierra todas las pestanas de Odoo")
        print("3. Abre una nueva pestana y ve a:")
        print(f"   {URL}/home")
        print("4. Abre la consola (F12) y verifica los logs [HOMEPAGE]")
        print()

        return True

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ver contenido de la vista homepage
"""

import xmlrpc.client

url = 'https://darm1640-bohio-18.odoo.com'
db = 'darm1640-bohio-18-main-24081960'
username = 'admin'
password = '123456'

def main():
    print("VERIFICANDO CONTENIDO DE LA VISTA")
    print("="*70)

    try:
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

        # Obtener la vista
        views = models.execute_kw(
            db, uid, password,
            'ir.ui.view', 'search_read',
            [[('key', '=', 'theme_bohio_real_estate.bohio_homepage_new')]],
            {'fields': ['id', 'name', 'arch_db'], 'limit': 1}
        )

        if views:
            view = views[0]
            arch = view['arch_db']

            print(f"Vista ID: {view['id']}")
            print(f"Nombre: {view['name']}")
            print(f"\nContenido XML (primeros 2000 caracteres):")
            print("="*70)
            print(arch[:2000])
            print("="*70)

            # Verificar si contiene los IDs que necesitamos
            ids_necesarios = [
                'arriendo-properties-grid',
                'used-sale-properties-grid',
                'projects-properties-grid'
            ]

            print("\nVERIFICANDO CONTENEDORES:")
            for id_needed in ids_necesarios:
                if id_needed in arch:
                    print(f"  [OK] {id_needed} - ENCONTRADO")
                else:
                    print(f"  [FALTA] {id_needed} - NO ENCONTRADO")

            print("\n" + "="*70)
            if all(id_needed in arch for id_needed in ids_necesarios):
                print("RESULTADO: La vista TIENE todos los contenedores")
                print("\nPROBLEMA: Puede ser cache del navegador")
                print("SOLUCION:")
                print("  1. Ctrl+Shift+Del → Limpiar cache")
                print("  2. Cerrar navegador completamente")
                print("  3. Abrir en modo incognito")
            else:
                print("RESULTADO: La vista NO TIENE todos los contenedores")
                print("\nPROBLEMA: La vista en la BD esta desactualizada")
                print("SOLUCION:")
                print("  1. Settings → Technical → Clear Assets")
                print("  2. Apps → theme_bohio_real_estate → Upgrade")
                print("  3. Refrescar navegador")

        else:
            print("ERROR: Vista no encontrada")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == '__main__':
    main()

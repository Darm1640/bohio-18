#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script rápido para migrar propiedades con city_id vacío
"""

import xmlrpc.client
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

url = 'https://darm1640-bohio-18.odoo.com'
db = 'darm1640-bohio-18-main-24081960'
username = 'admin'
password = '123456'

try:
    print("Conectando...")
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    print(f"[OK] Conectado (UID: {uid})")

    # Buscar propiedades SIN city_id
    print("\nBuscando propiedades SIN city_id...")
    props_sin_city = models.execute_kw(
        db, uid, password,
        'product.template', 'search',
        [[('is_property', '=', True), ('city_id', '=', False)]],
        {'limit': 1000}
    )

    print(f"[RESULTADO] {len(props_sin_city)} propiedades SIN city_id")

    if props_sin_city:
        # Leer solo las primeras 50 para análisis
        props_data = models.execute_kw(
            db, uid, password,
            'product.template', 'read',
            [props_sin_city[:50]],
            {'fields': ['id', 'default_code', 'name', 'city']}
        )

        print("\nPrimeras 50 propiedades sin city_id:")
        print("-" * 80)
        for p in props_data:
            print(f"  [{p.get('default_code', 'N/A')}] {p.get('name', '')[:40]} | city: '{p.get('city', 'N/A')}'")
        print("-" * 80)

        # Crear un diccionario de ciudades comunes
        print("\nCargando ciudades mas comunes...")
        common_cities = {
            'montería': 1554,
            'monteria': 1554,
            'medellin': 294,
            'medellín': 294,
            'bogota': 130,
            'bogotá': 130,
            'cali': 2090,
            'cartagena': 1557,
            'barranquilla': 1143,
            'bucaramanga': 1149,
            'cereté': 1558,
            'cerete': 1558
        }

        print("\nMigrando propiedades...")
        success = 0
        failed = 0

        for prop_id in props_sin_city:
            try:
                # Leer la propiedad
                prop = models.execute_kw(
                    db, uid, password,
                    'product.template', 'read',
                    [[prop_id]],
                    {'fields': ['city']}
                )[0]

                city_text = prop.get('city', '').strip().lower()

                if city_text in common_cities:
                    city_id = common_cities[city_text]

                    # Actualizar
                    models.execute_kw(
                        db, uid, password,
                        'product.template', 'write',
                        [[prop_id], {'city_id': city_id}]
                    )
                    success += 1

                    if success % 10 == 0:
                        print(f"  Procesadas: {success}")

            except Exception as e:
                failed += 1

        print(f"\n[RESULTADO]")
        print(f"  Exitosas: {success}")
        print(f"  Fallidas: {failed}")
        print(f"  Pendientes: {len(props_sin_city) - success - failed}")

    else:
        print("\n[OK] TODAS las propiedades tienen city_id!")

except Exception as e:
    print(f"[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()

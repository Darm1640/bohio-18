#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Revisar las propiedades restantes sin city_id
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
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    print("=" * 80)
    print("PROPIEDADES RESTANTES SIN city_id")
    print("=" * 80)

    # Buscar propiedades sin city_id
    props_ids = models.execute_kw(
        db, uid, password,
        'product.template', 'search',
        [[('is_property', '=', True), ('city_id', '=', False)]],
        {'limit': 200}
    )

    print(f"\n[ENCONTRADAS] {len(props_ids)} propiedades sin city_id\n")

    if props_ids:
        # Leer datos
        props = models.execute_kw(
            db, uid, password,
            'product.template', 'read',
            [props_ids],
            {'fields': ['id', 'default_code', 'name', 'city', 'active']}
        )

        # Agrupar por ciudad (texto)
        cities_count = {}
        props_sin_city_text = []

        for prop in props:
            city_text = (prop.get('city') or '').strip()

            if city_text:
                if city_text not in cities_count:
                    cities_count[city_text] = []
                cities_count[city_text].append(prop)
            else:
                props_sin_city_text.append(prop)

        # Mostrar resumen
        print(f"Propiedades SIN campo 'city' (texto): {len(props_sin_city_text)}")
        print(f"Propiedades CON campo 'city' pero sin city_id: {len(props) - len(props_sin_city_text)}")

        if props_sin_city_text:
            print(f"\nEjemplos de propiedades SIN city (texto):")
            print("-" * 80)
            for prop in props_sin_city_text[:20]:
                status = "INACTIVA" if not prop.get('active') else "ACTIVA"
                print(f"  [{prop.get('default_code', 'N/A')}] {prop.get('name', 'N/A')[:50]} | {status}")
            print("-" * 80)

        if cities_count:
            print(f"\nCiudades (texto) que no se pudieron asociar:")
            print("-" * 80)
            for city_text, props_list in sorted(cities_count.items(), key=lambda x: len(x[1]), reverse=True):
                print(f"  '{city_text}' ({len(props_list)} propiedades)")
                for prop in props_list[:3]:
                    print(f"     - [{prop.get('default_code', 'N/A')}] {prop.get('name', 'N/A')[:40]}")
            print("-" * 80)

        # Contar activas vs inactivas
        activas = sum(1 for p in props if p.get('active'))
        inactivas = len(props) - activas

        print(f"\nESTADO:")
        print(f"  Activas: {activas}")
        print(f"  Inactivas: {inactivas}")

    else:
        print("[OK] TODAS las propiedades tienen city_id!")

    print("\n" + "=" * 80)

except Exception as e:
    print(f"[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()

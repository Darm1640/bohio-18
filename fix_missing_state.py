#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Completar departamento (state_id) desde city_id
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
    print("Completando departamentos y codigos postales...")

    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    # Buscar propiedades CON city_id pero SIN state_id
    props_ids = models.execute_kw(
        db, uid, password,
        'product.template', 'search',
        [[('is_property', '=', True), ('city_id', '!=', False), ('state_id', '=', False)]]
    )

    print(f"Propiedades con city_id pero sin state_id: {len(props_ids)}")

    if props_ids:
        # Cargar ciudades con sus departamentos
        city_ids = models.execute_kw(db, uid, password, 'res.city', 'search', [[]])
        cities = models.execute_kw(
            db, uid, password,
            'res.city', 'read',
            [city_ids],
            {'fields': ['id', 'state_id', 'zipcode']}
        )

        # Crear índice
        cities_dict = {c['id']: c for c in cities}

        success = 0
        failed = 0

        for prop_id in props_ids:
            try:
                # Leer propiedad
                prop = models.execute_kw(
                    db, uid, password,
                    'product.template', 'read',
                    [[prop_id]],
                    {'fields': ['city_id', 'zip']}
                )[0]

                city_id = prop['city_id'][0] if prop.get('city_id') else None

                if city_id and city_id in cities_dict:
                    city_data = cities_dict[city_id]
                    updates = {}

                    if city_data.get('state_id'):
                        updates['state_id'] = city_data['state_id'][0]

                    if not prop.get('zip') and city_data.get('zipcode'):
                        updates['zip'] = city_data['zipcode']

                    if updates:
                        models.execute_kw(
                            db, uid, password,
                            'product.template', 'write',
                            [[prop_id], updates]
                        )
                        success += 1

                        if success % 50 == 0:
                            print(f"  Procesadas: {success}/{len(props_ids)}")

            except Exception as e:
                failed += 1

        print(f"\nResultado: {success} exitosas | {failed} fallidas")

    # Verificar resultado
    print("\nVerificando...")
    con_state = models.execute_kw(
        db, uid, password,
        'product.template', 'search_count',
        [[('is_property', '=', True), ('state_id', '!=', False)]]
    )

    total = models.execute_kw(
        db, uid, password,
        'product.template', 'search_count',
        [[('is_property', '=', True)]]
    )

    print(f"Propiedades con departamento: {con_state}/{total} ({con_state*100//total}%)")

except Exception as e:
    print(f"ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

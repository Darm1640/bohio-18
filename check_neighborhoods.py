#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para revisar datos de barrios en propiedades
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
    print("ANALISIS DE BARRIOS EN PROPIEDADES")
    print("=" * 80)

    # Buscar propiedades
    property_ids = models.execute_kw(
        db, uid, password,
        'product.template', 'search',
        [[('is_property', '=', True)]],
        {'limit': 200}
    )

    properties = models.execute_kw(
        db, uid, password,
        'product.template', 'read',
        [property_ids],
        {'fields': ['id', 'default_code', 'name', 'street2', 'region_id', 'city_id']}
    )

    print(f"\n[OK] Propiedades analizadas: {len(properties)}\n")

    # Estadísticas
    con_neighborhood = []
    con_region_id = []
    sin_barrio = []

    for prop in properties:
        if prop.get('street2'):
            con_neighborhood.append(prop)
        if prop.get('region_id'):
            con_region_id.append(prop)
        if not prop.get('street2') and not prop.get('region_id'):
            sin_barrio.append(prop)

    print("ESTADISTICAS:")
    print(f"  Con street2 (texto): {len(con_neighborhood)}")
    print(f"  Con region_id (relacion): {len(con_region_id)}")
    print(f"  Sin datos de barrio: {len(sin_barrio)}")

    if con_neighborhood:
        print(f"\nEJEMPLOS CON STREET2 (texto):")
        print("-" * 80)
        for prop in con_neighborhood[:10]:
            print(f"  [{prop.get('default_code', 'N/A')}]")
            print(f"    Nombre: {prop.get('name', 'N/A')[:50]}")
            print(f"    Barrio (texto): {prop.get('street2', 'N/A')}")
            print(f"    Region ID: {prop.get('region_id', 'N/A')}")
            print(f"    Ciudad ID: {prop.get('city_id', 'N/A')}")
            print("-" * 80)

    # Buscar barrios disponibles
    print("\n\nCATALOGO DE BARRIOS DISPONIBLES:")
    print("=" * 80)

    region_ids = models.execute_kw(
        db, uid, password,
        'region.region', 'search',
        [[]]
    )

    regions = models.execute_kw(
        db, uid, password,
        'region.region', 'read',
        [region_ids],
        {'fields': ['id', 'name', 'city_id', 'state_id']}
    )

    print(f"\n[OK] Total barrios en catalogo: {len(regions)}")

    # Agrupar por ciudad
    regions_by_city = {}
    for region in regions:
        city_id = region.get('city_id')
        if city_id:
            city_key = city_id[0] if isinstance(city_id, list) else city_id
            city_name = city_id[1] if isinstance(city_id, list) else str(city_id)

            if city_key not in regions_by_city:
                regions_by_city[city_key] = {'city_name': city_name, 'regions': []}

            regions_by_city[city_key]['regions'].append(region['name'])

    print(f"\nBarrios agrupados por ciudad (top 5 ciudades):")
    print("-" * 80)

    for i, (city_id, data) in enumerate(list(regions_by_city.items())[:5]):
        print(f"\n{i+1}. {data['city_name']} (ID: {city_id}) - {len(data['regions'])} barrios")
        print(f"   Ejemplos: {', '.join(data['regions'][:5])}")

    print("\n" + "=" * 80)

except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para encontrar y migrar propiedades con city_id vacío
"""

import xmlrpc.client
import sys
import io
from difflib import SequenceMatcher

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

url = 'https://darm1640-bohio-18.odoo.com'
db = 'darm1640-bohio-18-main-24081960'
username = 'admin'
password = '123456'

def similarity_ratio(a, b):
    """Calcula el ratio de similitud entre dos strings"""
    if not a or not b:
        return 0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_best_match(search_term, options, threshold=0.75):
    """Encuentra la mejor coincidencia en una lista de opciones"""
    if not search_term or not options:
        return None

    best_match = None
    best_ratio = 0

    for option in options:
        ratio = similarity_ratio(search_term, option['name'])
        if ratio > best_ratio and ratio >= threshold:
            best_ratio = ratio
            best_match = option

    return best_match, best_ratio if best_match else (None, 0)

try:
    print("=" * 80)
    print("BUSCANDO PROPIEDADES CON city_id VACIO")
    print("=" * 80)

    # Autenticación
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})

    if not uid:
        print("[ERROR] No se pudo autenticar")
        exit(1)

    print(f"[OK] Autenticado (UID: {uid})\n")

    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    # Buscar TODAS las propiedades (sin límite)
    print("Buscando todas las propiedades...")
    all_property_ids = models.execute_kw(
        db, uid, password,
        'product.template', 'search',
        [[('is_property', '=', True)]]
    )

    print(f"[OK] Total de propiedades encontradas: {len(all_property_ids)}\n")

    # Leer todas las propiedades
    print("Cargando datos de propiedades...")
    all_properties = models.execute_kw(
        db, uid, password,
        'product.template', 'read',
        [all_property_ids],
        {'fields': ['id', 'name', 'default_code', 'city', 'city_id']}
    )

    # Filtrar propiedades sin city_id
    properties_sin_city_id = []
    properties_con_city_id = []

    for prop in all_properties:
        if not prop.get('city_id'):
            properties_sin_city_id.append(prop)
        else:
            properties_con_city_id.append(prop)

    print(f"\n[RESULTADO]")
    print(f"  Propiedades CON city_id: {len(properties_con_city_id)}")
    print(f"  Propiedades SIN city_id: {len(properties_sin_city_id)}")

    if properties_sin_city_id:
        print(f"\n[ALERTA] Se encontraron {len(properties_sin_city_id)} propiedades sin city_id")
        print("\nPrimeras 20 propiedades sin city_id:")
        print("-" * 80)

        for i, prop in enumerate(properties_sin_city_id[:20]):
            print(f"  {i+1}. ID: {prop['id']} | Codigo: {prop.get('default_code', 'N/A')}")
            print(f"     Nombre: {prop.get('name', 'N/A')[:60]}")
            print(f"     City (texto): '{prop.get('city', 'N/A')}'")
            print(f"     City_id: {prop.get('city_id', 'VACIO')}")
            print("-" * 80)

        # Cargar catálogo de ciudades
        print("\nCargando catalogo de ciudades...")
        city_ids = models.execute_kw(db, uid, password, 'res.city', 'search', [[]])
        cities = models.execute_kw(db, uid, password, 'res.city', 'read', [city_ids], {'fields': ['id', 'name', 'state_id']})
        print(f"[OK] {len(cities)} ciudades cargadas\n")

        # Intentar encontrar coincidencias
        migrations = []
        sin_coincidencia = []

        for prop in properties_sin_city_id:
            if prop.get('city'):
                city_name = prop['city'].strip()
                best_match, ratio = find_best_match(city_name, cities, threshold=0.70)

                if best_match:
                    migrations.append({
                        'property_id': prop['id'],
                        'code': prop.get('default_code', 'N/A'),
                        'name': prop.get('name', 'N/A')[:40],
                        'city_text': city_name,
                        'city_id': best_match['id'],
                        'city_name': best_match['name'],
                        'similarity': ratio
                    })
                else:
                    sin_coincidencia.append({
                        'property_id': prop['id'],
                        'code': prop.get('default_code', 'N/A'),
                        'city_text': city_name
                    })

        print(f"[ANALISIS]")
        print(f"  Propiedades que se pueden migrar: {len(migrations)}")
        print(f"  Propiedades sin coincidencia: {len(sin_coincidencia)}")

        if migrations:
            print(f"\nPrimeras 15 migraciones propuestas:")
            print("-" * 80)
            for i, m in enumerate(migrations[:15]):
                print(f"  {i+1}. [{m['code']}] '{m['city_text']}' -> '{m['city_name']}' (similitud: {m['similarity']*100:.0f}%)")

            print(f"\n{'=' * 80}")
            print(f"APLICANDO {len(migrations)} MIGRACIONES...")
            print(f"{'=' * 80}\n")

            success = 0
            failed = 0

            for m in migrations:
                try:
                    models.execute_kw(
                        db, uid, password,
                        'product.template', 'write',
                        [[m['property_id']], {'city_id': m['city_id']}]
                    )
                    success += 1
                    if success % 10 == 0:
                        print(f"  Procesadas: {success}/{len(migrations)}")
                except Exception as e:
                    failed += 1
                    print(f"  [ERROR] {m['code']}: {str(e)}")

            print(f"\n[RESULTADO FINAL]")
            print(f"  Exitosas: {success}")
            print(f"  Fallidas: {failed}")

        if sin_coincidencia:
            print(f"\n[ADVERTENCIA] {len(sin_coincidencia)} propiedades sin coincidencia:")
            for i, prop in enumerate(sin_coincidencia[:10]):
                print(f"  {i+1}. [{prop['code']}] Ciudad: '{prop['city_text']}'")

    else:
        print("\n[OK] TODAS las propiedades tienen city_id configurado!")

    print("\n" + "=" * 80)
    print("PROCESO COMPLETADO")
    print("=" * 80)

except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

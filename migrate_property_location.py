#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para migrar datos de ubicación de propiedades en Odoo 18
- Busca ciudades por nombre y las asocia al campo city_id
- Busca barrios por nombre y los asocia al campo region_id
Base de datos: darm1640-bohio-18-main-24081960
"""

import xmlrpc.client
import sys
import io
from difflib import SequenceMatcher

# Configurar la salida para UTF-8 en Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración de conexión
url = 'https://darm1640-bohio-18.odoo.com'
db = 'darm1640-bohio-18-main-24081960'
username = 'admin'
password = '123456'

def similarity_ratio(a, b):
    """Calcula el ratio de similitud entre dos strings"""
    if not a or not b:
        return 0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def find_best_match(search_term, options, threshold=0.8):
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

print("=" * 80)
print("MIGRACIÓN DE DATOS DE UBICACIÓN EN PRODUCTOS INMOBILIARIOS")
print("=" * 80)
print(f"\nConectando a: {url}")
print(f"Base de datos: {db}")
print(f"Usuario: {username}\n")

try:
    # Autenticación
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})

    if not uid:
        print("[ERROR] No se pudo autenticar. Verifica las credenciales.")
        exit(1)

    print(f"[OK] Autenticacion exitosa (UID: {uid})\n")

    # Conexión al modelo
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    # ========================================================================
    # PASO 1: CARGAR CATÁLOGOS DE CIUDADES Y BARRIOS
    # ========================================================================

    print("=" * 80)
    print("PASO 1: CARGANDO CATÁLOGOS")
    print("=" * 80)

    # Cargar todas las ciudades disponibles
    print("\nCargando ciudades (res.city)...")
    city_ids = models.execute_kw(
        db, uid, password,
        'res.city', 'search',
        [[]]
    )

    cities = models.execute_kw(
        db, uid, password,
        'res.city', 'read',
        [city_ids],
        {'fields': ['id', 'name', 'state_id', 'country_id']}
    )

    print(f"[OK] Se cargaron {len(cities)} ciudades")

    # Cargar todos los barrios disponibles
    print("\nCargando barrios (region.region)...")
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

    print(f"[OK] Se cargaron {len(regions)} barrios")

    # ========================================================================
    # PASO 2: CARGAR PROPIEDADES A MIGRAR
    # ========================================================================

    print("\n" + "=" * 80)
    print("PASO 2: CARGANDO PROPIEDADES")
    print("=" * 80)

    # Buscar propiedades sin city_id pero con city (texto)
    print("\nBuscando propiedades a migrar...")
    property_ids = models.execute_kw(
        db, uid, password,
        'product.template', 'search',
        [[('is_property', '=', True)]],
        {'limit': 500}
    )

    properties = models.execute_kw(
        db, uid, password,
        'product.template', 'read',
        [property_ids],
        {'fields': ['id', 'name', 'default_code', 'city', 'city_id',
                   'street2', 'region_id', 'state_id']}
    )

    print(f"[OK] Se encontraron {len(properties)} propiedades\n")

    # ========================================================================
    # PASO 3: MIGRAR CIUDADES
    # ========================================================================

    print("=" * 80)
    print("PASO 3: MIGRANDO CIUDADES (city -> city_id)")
    print("=" * 80)

    stats_cities = {
        'total': 0,
        'con_city_text': 0,
        'sin_city_id': 0,
        'migraciones_exitosas': 0,
        'migraciones_fallidas': 0,
        'ya_migradas': 0
    }

    migrations_to_apply = []

    for prop in properties:
        stats_cities['total'] += 1

        # Si ya tiene city_id, skip
        if prop.get('city_id'):
            stats_cities['ya_migradas'] += 1
            continue

        # Si tiene city (texto)
        if prop.get('city'):
            stats_cities['con_city_text'] += 1
            stats_cities['sin_city_id'] += 1

            city_name = prop.get('city', '').strip()

            # Buscar coincidencia en el catálogo de ciudades
            best_match, ratio = find_best_match(city_name, cities, threshold=0.75)

            if best_match:
                migrations_to_apply.append({
                    'property_id': prop['id'],
                    'property_name': prop.get('name', 'N/A')[:40],
                    'property_code': prop.get('default_code', 'N/A'),
                    'city_text': city_name,
                    'city_id': best_match['id'],
                    'city_name': best_match['name'],
                    'similarity': ratio
                })

    print(f"\nEstadisticas de ciudades:")
    print(f"  Total propiedades: {stats_cities['total']}")
    print(f"  Con city (texto): {stats_cities['con_city_text']}")
    print(f"  Sin city_id: {stats_cities['sin_city_id']}")
    print(f"  Ya migradas: {stats_cities['ya_migradas']}")
    print(f"  Migraciones encontradas: {len(migrations_to_apply)}")

    if migrations_to_apply:
        print(f"\n[INFO] Se encontraron {len(migrations_to_apply)} propiedades para migrar")
        print("\nPrimeros 5 ejemplos de migracion:")
        print("-" * 80)

        for i, migration in enumerate(migrations_to_apply[:5]):
            print(f"  {i+1}. Propiedad: {migration['property_code']} - {migration['property_name']}")
            print(f"     Ciudad actual (texto): '{migration['city_text']}'")
            print(f"     Nueva ciudad (ID {migration['city_id']}): '{migration['city_name']}'")
            print(f"     Similitud: {migration['similarity']*100:.1f}%")
            print("-" * 80)

        # Preguntar confirmación
        print(f"\n[PREGUNTA] Deseas aplicar estas {len(migrations_to_apply)} migraciones?")
        print("  - Escribe 'si' para aplicar")
        print("  - Escribe 'no' para cancelar")
        print("  - Presiona Enter para aplicar (por defecto)")

        respuesta = input("\nTu respuesta: ").strip().lower()

        if respuesta in ['si', 's', 'yes', 'y', '']:
            print("\n[INFO] Aplicando migraciones de ciudades...")

            for migration in migrations_to_apply:
                try:
                    models.execute_kw(
                        db, uid, password,
                        'product.template', 'write',
                        [[migration['property_id']], {'city_id': migration['city_id']}]
                    )
                    stats_cities['migraciones_exitosas'] += 1
                    print(f"  [OK] Propiedad {migration['property_code']} -> Ciudad ID {migration['city_id']}")
                except Exception as e:
                    stats_cities['migraciones_fallidas'] += 1
                    print(f"  [ERROR] Propiedad {migration['property_code']}: {str(e)}")

            print(f"\n[RESULTADO] Migraciones de ciudades completadas:")
            print(f"  Exitosas: {stats_cities['migraciones_exitosas']}")
            print(f"  Fallidas: {stats_cities['migraciones_fallidas']}")
        else:
            print("\n[INFO] Migracion de ciudades cancelada por el usuario")
    else:
        print("\n[INFO] No hay propiedades para migrar (ciudades)")

    # ========================================================================
    # PASO 4: MIGRAR BARRIOS
    # ========================================================================

    print("\n" + "=" * 80)
    print("PASO 4: MIGRANDO BARRIOS (street2 -> region_id)")
    print("=" * 80)

    stats_regions = {
        'total': 0,
        'con_neighborhood_text': 0,
        'sin_region_id': 0,
        'migraciones_exitosas': 0,
        'migraciones_fallidas': 0,
        'ya_migradas': 0
    }

    migrations_regions = []

    # Recargar propiedades para tener datos actualizados
    properties = models.execute_kw(
        db, uid, password,
        'product.template', 'read',
        [property_ids],
        {'fields': ['id', 'name', 'default_code', 'city', 'city_id',
                   'street2', 'region_id', 'state_id']}
    )

    for prop in properties:
        stats_regions['total'] += 1

        # Si ya tiene region_id, skip
        if prop.get('region_id'):
            stats_regions['ya_migradas'] += 1
            continue

        # Si tiene street2 (texto)
        if prop.get('street2'):
            stats_regions['con_neighborhood_text'] += 1
            stats_regions['sin_region_id'] += 1

            neighborhood_name = prop.get('street2', '').strip()

            # Filtrar barrios por ciudad si la propiedad tiene city_id
            regions_to_search = regions
            if prop.get('city_id'):
                city_id = prop['city_id'][0] if isinstance(prop['city_id'], list) else prop['city_id']
                regions_to_search = [
                    r for r in regions
                    if r.get('city_id') and r['city_id'][0] == city_id
                ]

            # Buscar coincidencia en el catálogo de barrios
            best_match, ratio = find_best_match(neighborhood_name, regions_to_search, threshold=0.70)

            if best_match:
                migrations_regions.append({
                    'property_id': prop['id'],
                    'property_name': prop.get('name', 'N/A')[:40],
                    'property_code': prop.get('default_code', 'N/A'),
                    'neighborhood_text': neighborhood_name,
                    'region_id': best_match['id'],
                    'region_name': best_match['name'],
                    'similarity': ratio
                })

    print(f"\nEstadisticas de barrios:")
    print(f"  Total propiedades: {stats_regions['total']}")
    print(f"  Con street2 (texto): {stats_regions['con_neighborhood_text']}")
    print(f"  Sin region_id: {stats_regions['sin_region_id']}")
    print(f"  Ya migradas: {stats_regions['ya_migradas']}")
    print(f"  Migraciones encontradas: {len(migrations_regions)}")

    if migrations_regions:
        print(f"\n[INFO] Se encontraron {len(migrations_regions)} propiedades para migrar")
        print("\nPrimeros 5 ejemplos de migracion:")
        print("-" * 80)

        for i, migration in enumerate(migrations_regions[:5]):
            print(f"  {i+1}. Propiedad: {migration['property_code']} - {migration['property_name']}")
            print(f"     Barrio actual (texto): '{migration['neighborhood_text']}'")
            print(f"     Nuevo barrio (ID {migration['region_id']}): '{migration['region_name']}'")
            print(f"     Similitud: {migration['similarity']*100:.1f}%")
            print("-" * 80)

        # Preguntar confirmación
        print(f"\n[PREGUNTA] Deseas aplicar estas {len(migrations_regions)} migraciones?")
        print("  - Escribe 'si' para aplicar")
        print("  - Escribe 'no' para cancelar")
        print("  - Presiona Enter para aplicar (por defecto)")

        respuesta = input("\nTu respuesta: ").strip().lower()

        if respuesta in ['si', 's', 'yes', 'y', '']:
            print("\n[INFO] Aplicando migraciones de barrios...")

            for migration in migrations_regions:
                try:
                    models.execute_kw(
                        db, uid, password,
                        'product.template', 'write',
                        [[migration['property_id']], {'region_id': migration['region_id']}]
                    )
                    stats_regions['migraciones_exitosas'] += 1
                    print(f"  [OK] Propiedad {migration['property_code']} -> Barrio ID {migration['region_id']}")
                except Exception as e:
                    stats_regions['migraciones_fallidas'] += 1
                    print(f"  [ERROR] Propiedad {migration['property_code']}: {str(e)}")

            print(f"\n[RESULTADO] Migraciones de barrios completadas:")
            print(f"  Exitosas: {stats_regions['migraciones_exitosas']}")
            print(f"  Fallidas: {stats_regions['migraciones_fallidas']}")
        else:
            print("\n[INFO] Migracion de barrios cancelada por el usuario")
    else:
        print("\n[INFO] No hay propiedades para migrar (barrios)")

    # ========================================================================
    # RESUMEN FINAL
    # ========================================================================

    print("\n" + "=" * 80)
    print("RESUMEN FINAL")
    print("=" * 80)

    print(f"\nCIUDADES:")
    print(f"  Migraciones exitosas: {stats_cities['migraciones_exitosas']}")
    print(f"  Migraciones fallidas: {stats_cities['migraciones_fallidas']}")

    print(f"\nBARRIOS:")
    print(f"  Migraciones exitosas: {stats_regions['migraciones_exitosas']}")
    print(f"  Migraciones fallidas: {stats_regions['migraciones_fallidas']}")

    print("\n" + "=" * 80)
    print("MIGRACIÓN COMPLETADA")
    print("=" * 80)

except Exception as e:
    print(f"\n[ERROR] Error durante la ejecucion:")
    print(f"   {type(e).__name__}: {str(e)}")
    import traceback
    print("\nTraceback completo:")
    traceback.print_exc()
    exit(1)

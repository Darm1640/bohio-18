#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para migrar datos de ubicación de propiedades en Odoo 18 (VERSIÓN AUTOMÁTICA)
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

# MODO AUTOMÁTICO: Cambiar a False para hacer dry-run (solo mostrar, no aplicar)
AUTO_APPLY = True
DRY_RUN = not AUTO_APPLY

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
print("MIGRACION DE DATOS DE UBICACION EN PRODUCTOS INMOBILIARIOS")
if DRY_RUN:
    print("MODO: DRY-RUN (Solo analisis, no se aplicaran cambios)")
else:
    print("MODO: AUTOMATICO (Se aplicaran los cambios)")
print("=" * 80)
print(f"\nConectando a: {url}")
print(f"Base de datos: {db}\n")

try:
    # Autenticación
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})

    if not uid:
        print("[ERROR] No se pudo autenticar.")
        exit(1)

    print(f"[OK] Autenticacion exitosa (UID: {uid})\n")

    # Conexión al modelo
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    # ========================================================================
    # PASO 1: CARGAR CATÁLOGOS
    # ========================================================================

    print("PASO 1: CARGANDO CATALOGOS...")

    # Cargar ciudades
    city_ids = models.execute_kw(db, uid, password, 'res.city', 'search', [[]])
    cities = models.execute_kw(db, uid, password, 'res.city', 'read', [city_ids], {'fields': ['id', 'name']})
    print(f"[OK] {len(cities)} ciudades cargadas")

    # Cargar barrios
    region_ids = models.execute_kw(db, uid, password, 'region.region', 'search', [[]])
    regions = models.execute_kw(db, uid, password, 'region.region', 'read', [region_ids], {'fields': ['id', 'name', 'city_id']})
    print(f"[OK] {len(regions)} barrios cargados\n")

    # ========================================================================
    # PASO 2: CARGAR PROPIEDADES
    # ========================================================================

    print("PASO 2: CARGANDO PROPIEDADES...")
    property_ids = models.execute_kw(db, uid, password, 'product.template', 'search', [[('is_property', '=', True)]], {'limit': 200})
    properties = models.execute_kw(
        db, uid, password,
        'product.template', 'read',
        [property_ids],
        {'fields': ['id', 'name', 'default_code', 'city', 'city_id', 'neighborhood', 'region_id']}
    )
    print(f"[OK] {len(properties)} propiedades cargadas\n")

    # ========================================================================
    # PASO 3: MIGRAR CIUDADES
    # ========================================================================

    print("=" * 80)
    print("PASO 3: MIGRANDO CIUDADES (city -> city_id)")
    print("=" * 80)

    migrations_cities = []
    for prop in properties:
        if not prop.get('city_id') and prop.get('city'):
            city_name = prop.get('city', '').strip()
            best_match, ratio = find_best_match(city_name, cities, threshold=0.75)
            if best_match:
                migrations_cities.append({
                    'property_id': prop['id'],
                    'code': prop.get('default_code', 'N/A'),
                    'city_text': city_name,
                    'city_id': best_match['id'],
                    'city_name': best_match['name'],
                    'similarity': ratio
                })

    print(f"\n[INFO] Encontradas {len(migrations_cities)} propiedades para migrar")

    if migrations_cities:
        print("\nPrimeros 10 ejemplos:")
        for i, m in enumerate(migrations_cities[:10]):
            print(f"  {i+1}. [{m['code']}] '{m['city_text']}' -> '{m['city_name']}' (similitud: {m['similarity']*100:.0f}%)")

        if not DRY_RUN:
            print(f"\n[INFO] Aplicando {len(migrations_cities)} migraciones de ciudades...")
            success = 0
            failed = 0

            for m in migrations_cities:
                try:
                    models.execute_kw(db, uid, password, 'product.template', 'write', [[m['property_id']], {'city_id': m['city_id']}])
                    success += 1
                except Exception as e:
                    failed += 1
                    print(f"  [ERROR] {m['code']}: {str(e)}")

            print(f"\n[RESULTADO CIUDADES] Exitosas: {success} | Fallidas: {failed}")

    # ========================================================================
    # PASO 4: MIGRAR BARRIOS
    # ========================================================================

    print("\n" + "=" * 80)
    print("PASO 4: MIGRANDO BARRIOS (neighborhood -> region_id)")
    print("=" * 80)

    # Recargar propiedades para tener city_id actualizado
    properties = models.execute_kw(
        db, uid, password,
        'product.template', 'read',
        [property_ids],
        {'fields': ['id', 'name', 'default_code', 'city', 'city_id', 'neighborhood', 'region_id']}
    )

    migrations_regions = []
    for prop in properties:
        if not prop.get('region_id') and prop.get('neighborhood'):
            neighborhood_name = prop.get('neighborhood', '').strip()

            # Filtrar barrios por ciudad si está disponible
            regions_to_search = regions
            if prop.get('city_id'):
                city_id = prop['city_id'][0] if isinstance(prop['city_id'], list) else prop['city_id']
                regions_to_search = [r for r in regions if r.get('city_id') and r['city_id'][0] == city_id]

            best_match, ratio = find_best_match(neighborhood_name, regions_to_search, threshold=0.70)
            if best_match:
                migrations_regions.append({
                    'property_id': prop['id'],
                    'code': prop.get('default_code', 'N/A'),
                    'neighborhood_text': neighborhood_name,
                    'region_id': best_match['id'],
                    'region_name': best_match['name'],
                    'similarity': ratio
                })

    print(f"\n[INFO] Encontradas {len(migrations_regions)} propiedades para migrar")

    if migrations_regions:
        print("\nPrimeros 10 ejemplos:")
        for i, m in enumerate(migrations_regions[:10]):
            print(f"  {i+1}. [{m['code']}] '{m['neighborhood_text']}' -> '{m['region_name']}' (similitud: {m['similarity']*100:.0f}%)")

        if not DRY_RUN:
            print(f"\n[INFO] Aplicando {len(migrations_regions)} migraciones de barrios...")
            success = 0
            failed = 0

            for m in migrations_regions:
                try:
                    models.execute_kw(db, uid, password, 'product.template', 'write', [[m['property_id']], {'region_id': m['region_id']}])
                    success += 1
                except Exception as e:
                    failed += 1
                    print(f"  [ERROR] {m['code']}: {str(e)}")

            print(f"\n[RESULTADO BARRIOS] Exitosas: {success} | Fallidas: {failed}")

    # ========================================================================
    # RESUMEN FINAL
    # ========================================================================

    print("\n" + "=" * 80)
    print("MIGRACION COMPLETADA")
    print("=" * 80)
    print(f"\nCiudades migradas: {len(migrations_cities)}")
    print(f"Barrios migrados: {len(migrations_regions)}")
    print()

except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

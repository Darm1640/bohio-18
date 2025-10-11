#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script optimizado para migrar TODAS las propiedades con city_id vacío
Procesa en lotes para mayor eficiencia
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

BATCH_SIZE = 100  # Procesar de 100 en 100

def similarity_ratio(a, b):
    if not a or not b:
        return 0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

try:
    print("=" * 80)
    print("MIGRACION MASIVA DE CIUDADES")
    print("=" * 80)

    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    print(f"\n[OK] Conectado (UID: {uid})")

    # Buscar TODAS las propiedades sin city_id
    print("\nBuscando propiedades sin city_id...")
    props_sin_city_ids = models.execute_kw(
        db, uid, password,
        'product.template', 'search',
        [[('is_property', '=', True), ('city_id', '=', False)]]
    )

    total_props = len(props_sin_city_ids)
    print(f"[ENCONTRADAS] {total_props} propiedades sin city_id")

    if total_props == 0:
        print("\n[OK] TODAS las propiedades ya tienen city_id!")
        exit(0)

    # Cargar catálogo de ciudades (optimizado)
    print("\nCargando catalogo de ciudades...")
    city_ids = models.execute_kw(db, uid, password, 'res.city', 'search', [[]])
    cities = models.execute_kw(db, uid, password, 'res.city', 'read', [city_ids], {'fields': ['id', 'name']})

    # Crear índice para búsqueda rápida
    cities_index = {}
    for city in cities:
        city_key = city['name'].lower().strip()
        if city_key not in cities_index:
            cities_index[city_key] = city['id']

    print(f"[OK] {len(cities)} ciudades cargadas")

    # Estadísticas
    stats = {
        'procesadas': 0,
        'exitosas': 0,
        'fallidas': 0,
        'sin_coincidencia': 0
    }

    # Procesar en lotes
    print(f"\n{'='*80}")
    print(f"PROCESANDO {total_props} PROPIEDADES EN LOTES DE {BATCH_SIZE}")
    print(f"{'='*80}\n")

    for i in range(0, total_props, BATCH_SIZE):
        batch_ids = props_sin_city_ids[i:i+BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (total_props + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"[LOTE {batch_num}/{total_batches}] Procesando propiedades {i+1} a {min(i+BATCH_SIZE, total_props)}...")

        # Leer propiedades del lote
        batch_props = models.execute_kw(
            db, uid, password,
            'product.template', 'read',
            [batch_ids],
            {'fields': ['id', 'default_code', 'city']}
        )

        # Procesar cada propiedad del lote
        for prop in batch_props:
            stats['procesadas'] += 1
            city_text = (prop.get('city') or '').strip()

            if not city_text:
                stats['sin_coincidencia'] += 1
                continue

            # Buscar ciudad - primero exacta, luego similar
            city_key = city_text.lower()
            city_id = None

            # Búsqueda exacta
            if city_key in cities_index:
                city_id = cities_index[city_key]
            else:
                # Búsqueda por similitud
                best_ratio = 0
                for city_name, cid in cities_index.items():
                    ratio = similarity_ratio(city_key, city_name)
                    if ratio > best_ratio and ratio >= 0.75:
                        best_ratio = ratio
                        city_id = cid

            if city_id:
                try:
                    models.execute_kw(
                        db, uid, password,
                        'product.template', 'write',
                        [[prop['id']], {'city_id': city_id}]
                    )
                    stats['exitosas'] += 1
                except Exception as e:
                    stats['fallidas'] += 1
                    print(f"     [ERROR] {prop.get('default_code')}: {str(e)}")
            else:
                stats['sin_coincidencia'] += 1

        # Mostrar progreso
        porcentaje = (stats['procesadas'] * 100) // total_props
        print(f"     Progreso: {stats['procesadas']}/{total_props} ({porcentaje}%) | Exitosas: {stats['exitosas']} | Fallidas: {stats['fallidas']} | Sin coincidencia: {stats['sin_coincidencia']}")

    # Resumen final
    print(f"\n{'='*80}")
    print("RESUMEN FINAL")
    print(f"{'='*80}")
    print(f"Total procesadas: {stats['procesadas']}")
    print(f"Migradas exitosamente: {stats['exitosas']} ({stats['exitosas']*100//stats['procesadas'] if stats['procesadas'] > 0 else 0}%)")
    print(f"Fallidas: {stats['fallidas']}")
    print(f"Sin coincidencia: {stats['sin_coincidencia']}")
    print(f"{'='*80}")

    # Verificar resultado final
    print("\nVerificando resultado...")
    count_sin = models.execute_kw(
        db, uid, password,
        'product.template', 'search_count',
        [[('is_property', '=', True), ('city_id', '=', False)]]
    )

    count_con = models.execute_kw(
        db, uid, password,
        'product.template', 'search_count',
        [[('is_property', '=', True), ('city_id', '!=', False)]]
    )

    print(f"\n[RESULTADO FINAL]")
    print(f"  Propiedades CON city_id: {count_con}")
    print(f"  Propiedades SIN city_id: {count_sin}")
    print(f"\n{'='*80}")

except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

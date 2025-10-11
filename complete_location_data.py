#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para completar datos de ubicación:
- city_id (ciudad)
- state_id (departamento)
- country_id (país)
- zip (código postal)
"""

import xmlrpc.client
import sys
import io
import unicodedata

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

url = 'https://darm1640-bohio-18.odoo.com'
db = 'darm1640-bohio-18-main-24081960'
username = 'admin'
password = '123456'

def normalize_text(text):
    """Normaliza texto: sin tildes, minúsculas, sin espacios extras"""
    if not text:
        return ''
    # Remover tildes
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    # Minúsculas y strip
    return text.lower().strip()

try:
    print("=" * 80)
    print("COMPLETAR DATOS DE UBICACION")
    print("=" * 80)

    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    print(f"\n[OK] Conectado (UID: {uid})")

    # ========================================================================
    # PASO 1: CARGAR CATÁLOGOS
    # ========================================================================

    print("\n[1/3] Cargando catalogos...")

    # Cargar ciudades con departamento y país
    city_ids = models.execute_kw(db, uid, password, 'res.city', 'search', [[]])
    cities = models.execute_kw(
        db, uid, password,
        'res.city', 'read',
        [city_ids],
        {'fields': ['id', 'name', 'state_id', 'country_id', 'zipcode']}
    )

    # Crear índice normalizado
    cities_normalized = {}
    for city in cities:
        key = normalize_text(city['name'])
        if key not in cities_normalized:
            cities_normalized[key] = city

    print(f"   {len(cities)} ciudades cargadas")

    # ========================================================================
    # PASO 2: MIGRAR CITY_ID
    # ========================================================================

    print("\n[2/3] Migrando city_id...")

    # Buscar propiedades sin city_id
    props_ids = models.execute_kw(
        db, uid, password,
        'product.template', 'search',
        [[('is_property', '=', True), ('city_id', '=', False)]]
    )

    print(f"   {len(props_ids)} propiedades sin city_id")

    if props_ids:
        # Leer propiedades
        props = models.execute_kw(
            db, uid, password,
            'product.template', 'read',
            [props_ids],
            {'fields': ['id', 'default_code', 'city']}
        )

        success_city = 0
        failed_city = 0

        for prop in props:
            city_text = (prop.get('city') or '').strip()
            if not city_text:
                continue

            # Buscar con normalización
            city_key = normalize_text(city_text)
            if city_key in cities_normalized:
                city_data = cities_normalized[city_key]

                try:
                    models.execute_kw(
                        db, uid, password,
                        'product.template', 'write',
                        [[prop['id']], {'city_id': city_data['id']}]
                    )
                    success_city += 1
                except Exception as e:
                    failed_city += 1
                    print(f"      [ERROR] {prop.get('default_code')}: {str(e)}")

        print(f"   Migradas: {success_city} | Fallidas: {failed_city}")

    # ========================================================================
    # PASO 3: COMPLETAR DEPARTAMENTO, PAÍS Y CÓDIGO POSTAL
    # ========================================================================

    print("\n[3/3] Completando departamento, pais y codigo postal...")

    # Buscar propiedades CON city_id pero sin state_id o country_id
    props_incomplete_ids = models.execute_kw(
        db, uid, password,
        'product.template', 'search',
        [[
            ('is_property', '=', True),
            ('city_id', '!=', False),
            '|', '|',
            ('state_id', '=', False),
            ('country_id', '=', False),
            ('zip', '=', False)
        ]]
    )

    print(f"   {len(props_incomplete_ids)} propiedades con datos incompletos")

    if props_incomplete_ids:
        # Leer propiedades
        props_incomplete = models.execute_kw(
            db, uid, password,
            'product.template', 'read',
            [props_incomplete_ids],
            {'fields': ['id', 'default_code', 'city_id', 'state_id', 'country_id', 'zip']}
        )

        success_complete = 0
        failed_complete = 0

        for prop in props_incomplete:
            if not prop.get('city_id'):
                continue

            city_id = prop['city_id'][0] if isinstance(prop['city_id'], list) else prop['city_id']

            # Buscar datos de la ciudad
            city_data = next((c for c in cities if c['id'] == city_id), None)

            if city_data:
                updates = {}

                # Actualizar state_id si está vacío y la ciudad tiene state_id
                if not prop.get('state_id') and city_data.get('state_id'):
                    updates['state_id'] = city_data['state_id'][0]

                # Actualizar country_id si está vacío y la ciudad tiene country_id
                if not prop.get('country_id') and city_data.get('country_id'):
                    updates['country_id'] = city_data['country_id'][0]

                # Actualizar zip si está vacío y la ciudad tiene zipcode
                if not prop.get('zip') and city_data.get('zipcode'):
                    updates['zip'] = city_data['zipcode']

                if updates:
                    try:
                        models.execute_kw(
                            db, uid, password,
                            'product.template', 'write',
                            [[prop['id']], updates]
                        )
                        success_complete += 1
                    except Exception as e:
                        failed_complete += 1
                        print(f"      [ERROR] {prop.get('default_code')}: {str(e)}")

        print(f"   Completadas: {success_complete} | Fallidas: {failed_complete}")

    # ========================================================================
    # RESUMEN FINAL
    # ========================================================================

    print("\n" + "=" * 80)
    print("VERIFICANDO RESULTADOS FINALES")
    print("=" * 80)

    # Contar propiedades con city_id
    count_con_city = models.execute_kw(
        db, uid, password,
        'product.template', 'search_count',
        [[('is_property', '=', True), ('city_id', '!=', False)]]
    )

    count_sin_city = models.execute_kw(
        db, uid, password,
        'product.template', 'search_count',
        [[('is_property', '=', True), ('city_id', '=', False)]]
    )

    count_total = models.execute_kw(
        db, uid, password,
        'product.template', 'search_count',
        [[('is_property', '=', True)]]
    )

    # Contar con state_id
    count_con_state = models.execute_kw(
        db, uid, password,
        'product.template', 'search_count',
        [[('is_property', '=', True), ('state_id', '!=', False)]]
    )

    # Contar con country_id
    count_con_country = models.execute_kw(
        db, uid, password,
        'product.template', 'search_count',
        [[('is_property', '=', True), ('country_id', '!=', False)]]
    )

    # Contar con zip
    count_con_zip = models.execute_kw(
        db, uid, password,
        'product.template', 'search_count',
        [[('is_property', '=', True), ('zip', '!=', False)]]
    )

    print(f"\nTotal propiedades: {count_total}")
    print(f"\nCiudad (city_id):")
    print(f"  Con dato: {count_con_city} ({count_con_city*100//count_total}%)")
    print(f"  Sin dato: {count_sin_city} ({count_sin_city*100//count_total}%)")

    print(f"\nDepartamento (state_id):")
    print(f"  Con dato: {count_con_state} ({count_con_state*100//count_total}%)")

    print(f"\nPais (country_id):")
    print(f"  Con dato: {count_con_country} ({count_con_country*100//count_total}%)")

    print(f"\nCodigo Postal (zip):")
    print(f"  Con dato: {count_con_zip} ({count_con_zip*100//count_total}%)")

    print("\n" + "=" * 80)
    print("PROCESO COMPLETADO")
    print("=" * 80)

except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

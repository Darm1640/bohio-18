#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

    print(f"Conectado (UID: {uid})\n")

    # Contar propiedades CON city_id
    count_con = models.execute_kw(
        db, uid, password,
        'product.template', 'search_count',
        [[('is_property', '=', True), ('city_id', '!=', False)]]
    )

    # Contar propiedades SIN city_id
    count_sin = models.execute_kw(
        db, uid, password,
        'product.template', 'search_count',
        [[('is_property', '=', True), ('city_id', '=', False)]]
    )

    # Total
    count_total = models.execute_kw(
        db, uid, password,
        'product.template', 'search_count',
        [[('is_property', '=', True)]]
    )

    print("=" * 60)
    print("CONTEO DE PROPIEDADES")
    print("=" * 60)
    print(f"Total propiedades: {count_total}")
    print(f"CON city_id: {count_con} ({count_con*100//count_total if count_total > 0 else 0}%)")
    print(f"SIN city_id: {count_sin} ({count_sin*100//count_total if count_total > 0 else 0}%)")
    print("=" * 60)

except Exception as e:
    print(f"ERROR: {str(e)}")

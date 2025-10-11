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

    total = models.execute_kw(db, uid, password, 'product.template', 'search_count', [[('is_property', '=', True)]])

    con_city = models.execute_kw(db, uid, password, 'product.template', 'search_count', [[('is_property', '=', True), ('city_id', '!=', False)]])
    con_state = models.execute_kw(db, uid, password, 'product.template', 'search_count', [[('is_property', '=', True), ('state_id', '!=', False)]])
    con_country = models.execute_kw(db, uid, password, 'product.template', 'search_count', [[('is_property', '=', True), ('country_id', '!=', False)]])
    con_zip = models.execute_kw(db, uid, password, 'product.template', 'search_count', [[('is_property', '=', True), ('zip', '!=', False)]])

    print("=" * 60)
    print(f"PROGRESO - Total propiedades: {total}")
    print("=" * 60)
    print(f"Ciudad (city_id):      {con_city:4} ({con_city*100//total:3}%)")
    print(f"Departamento (state):  {con_state:4} ({con_state*100//total:3}%)")
    print(f"Pais (country):        {con_country:4} ({con_country*100//total:3}%)")
    print(f"Codigo Postal (zip):   {con_zip:4} ({con_zip*100//total:3}%)")
    print("=" * 60)

except Exception as e:
    print(f"ERROR: {str(e)}")

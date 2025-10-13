#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verifica qué campos están llenos en una propiedad de Odoo 18
"""
import sys
import io
import json
import xmlrpc.client

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración Odoo.com
odoo_config = {
    'url': 'https://darm1640-bohio-18.odoo.com',
    'db': 'darm1640-bohio-18-main-24081960',
    'username': 'admin',
    'password': '123456'
}

print("Conectando a Odoo.com...")
odoo_common = xmlrpc.client.ServerProxy(f"{odoo_config['url']}/xmlrpc/2/common")
odoo_uid = odoo_common.authenticate(odoo_config['db'], odoo_config['username'], odoo_config['password'], {})
odoo_models = xmlrpc.client.ServerProxy(f"{odoo_config['url']}/xmlrpc/2/object")

print(f"✅ Conectado como UID: {odoo_uid}\n")

# Buscar una propiedad recién migrada (código 1)
prop_ids = odoo_models.execute_kw(
    odoo_config['db'], odoo_uid, odoo_config['password'],
    'product.template', 'search',
    [[('default_code', '=', '1')]], {'limit': 1}
)

if not prop_ids:
    print("❌ No se encontró la propiedad con código 1")
    sys.exit(1)

prop_id = prop_ids[0]
print(f"Propiedad ID: {prop_id}")
print(f"Código: 1\n")

# Campos que queremos verificar (SOLO LOS QUE EXISTEN)
campos_verificar = [
    'default_code', 'name', 'street', 'street2', 'zip',
    'state_id', 'city_id', 'region_id',
    'categ_id',
    'num_bedrooms', 'num_bathrooms', 'property_area',
    'list_price', 'latitude', 'longitude'
]

# Leer campos
data = odoo_models.execute_kw(
    odoo_config['db'], odoo_uid, odoo_config['password'],
    'product.template', 'read',
    [prop_id], {'fields': campos_verificar}
)

if data:
    prop_data = data[0]

    print("="*80)
    print("CAMPOS VERIFICADOS")
    print("="*80)

    # Separar en llenos y vacíos
    campos_llenos = []
    campos_vacios = []

    for field, value in prop_data.items():
        if field == 'id':
            continue

        # Verificar si está vacío
        is_empty = False
        if value is None or value == False:
            is_empty = True
        elif isinstance(value, str) and not value.strip():
            is_empty = True
        elif isinstance(value, list) and not value:
            is_empty = True
        elif isinstance(value, (int, float)) and value == 0:
            # Para números, 0 puede ser válido, así que no lo contamos como vacío
            pass

        if is_empty:
            campos_vacios.append(field)
        else:
            campos_llenos.append((field, value))

    print("\n✅ CAMPOS LLENOS:")
    print("-"*80)
    for field, value in campos_llenos:
        if isinstance(value, list) and len(value) >= 2:
            print(f"   {field:25} = {value[1]}")
        else:
            print(f"   {field:25} = {value}")

    if campos_vacios:
        print(f"\n❌ CAMPOS VACÍOS ({len(campos_vacios)}):")
        print("-"*80)
        for field in campos_vacios:
            print(f"   {field}")

    print("\n" + "="*80)
    print(f"RESUMEN: {len(campos_llenos)} llenos, {len(campos_vacios)} vacíos")
    print("="*80)

    # Mostrar JSON completo
    print("\nJSON COMPLETO:")
    print(json.dumps(prop_data, indent=2, ensure_ascii=False))

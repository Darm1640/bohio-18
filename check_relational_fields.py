#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verifica qué campos relacionales tiene una propiedad en CloudPepper
"""
import sys
import io
import json
import xmlrpc.client

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración CloudPepper
cp_config = {
    'url': 'https://inmobiliariabohio.cloudpepper.site',
    'db': 'inmobiliariabohio.cloudpepper.site',
    'username': 'admin',
    'password': 'admin'
}

print("Conectando a CloudPepper...")
cp_common = xmlrpc.client.ServerProxy(f"{cp_config['url']}/xmlrpc/2/common")
cp_uid = cp_common.authenticate(cp_config['db'], cp_config['username'], cp_config['password'], {})
cp_models = xmlrpc.client.ServerProxy(f"{cp_config['url']}/xmlrpc/2/object")

print(f"✅ Conectado como UID: {cp_uid}\n")

# Buscar una propiedad
prop_ids = cp_models.execute_kw(
    cp_config['db'], cp_uid, cp_config['password'],
    'product.template', 'search',
    [[('active', '=', True)]], {'limit': 1}
)

if not prop_ids:
    print("❌ No se encontraron propiedades")
    sys.exit(1)

prop_id = prop_ids[0]
print(f"Propiedad ID: {prop_id}\n")

# Primero verificar qué campos existen
print("Obteniendo definición de campos relacionales...")
all_fields = cp_models.execute_kw(
    cp_config['db'], cp_uid, cp_config['password'],
    'product.template', 'fields_get',
    [], {'attributes': ['type', 'string', 'relation']}
)

# Filtrar solo many2one relacionados con ubicación
location_fields = {}
for field_name, field_def in all_fields.items():
    if field_def['type'] == 'many2one':
        relation = field_def.get('relation', '')
        if any(x in relation for x in ['city', 'state', 'region', 'neighborhood', 'barrio', 'sector']):
            location_fields[field_name] = field_def

print("Campos de ubicación encontrados:")
print("="*80)
for field_name, field_def in location_fields.items():
    print(f"{field_name:30} -> {field_def['relation']:30} ({field_def['string']})")

# Campos relacionales que buscamos (ajustados)
relational_fields = list(location_fields.keys())[:10]  # Primeros 10

if not relational_fields:
    print("\n❌ No se encontraron campos de ubicación")
    sys.exit(1)

print(f"\n{'='*80}")
print(f"Leyendo datos de la propiedad {prop_id}...")
print("="*80)

# Leer campos
data = cp_models.execute_kw(
    cp_config['db'], cp_uid, cp_config['password'],
    'product.template', 'read',
    [prop_id], {'fields': relational_fields}
)

if data:
    print("Campos relacionales encontrados:")
    print("="*80)
    for field, value in data[0].items():
        if field == 'id':
            continue
        print(f"{field:20} = {value}")

    print("\n" + "="*80)
    print("JSON completo:")
    print(json.dumps(data[0], indent=2, ensure_ascii=False))

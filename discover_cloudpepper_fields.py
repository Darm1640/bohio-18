#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para descubrir qué campos existen en CloudPepper (Odoo 17)
para product.template relacionados con propiedades
"""
import xmlrpc.client
import sys
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración CloudPepper
ODOO17 = {
    'url': 'https://inmobiliariabohio.cloudpepper.site',
    'db': 'inmobiliariabohio.cloudpepper.site',
    'username': 'admin',
    'password': 'admin'
}

def main():
    print("=" * 90)
    print("DESCUBRIMIENTO DE CAMPOS EN CLOUDPEPPER (ODOO 17)")
    print("=" * 90)

    # Conectar
    common = xmlrpc.client.ServerProxy(f"{ODOO17['url']}/xmlrpc/2/common")
    uid = common.authenticate(ODOO17['db'], ODOO17['username'], ODOO17['password'], {})

    if not uid:
        print("ERROR: No se pudo conectar")
        return

    print(f"Conectado (UID: {uid})\n")
    models = xmlrpc.client.ServerProxy(f"{ODOO17['url']}/xmlrpc/2/object")

    # Obtener TODOS los campos
    print("[1] Obteniendo todos los campos de product.template...")

    try:
        all_fields = models.execute_kw(
            ODOO17['db'], uid, ODOO17['password'],
            'product.template', 'fields_get',
            [],
            {'attributes': ['string', 'type', 'relation', 'required', 'help']}
        )

        print(f"    Total campos: {len(all_fields)}")

    except Exception as e:
        print(f"    ERROR: {e}")
        return

    # Filtrar campos relacionados con propiedades y ubicación
    keywords = [
        'property', 'state', 'city', 'region', 'neighborhood', 'location',
        'address', 'street', 'zip', 'latitude', 'longitude', 'gps',
        'bedroom', 'bathroom', 'garage', 'area', 'floor', 'unit', 'tower',
        'price', 'rent', 'sale', 'type', 'subtype', 'status'
    ]

    relevant_fields = {}
    for field_name, field_info in all_fields.items():
        field_lower = field_name.lower()
        string_lower = field_info.get('string', '').lower()

        if any(kw in field_lower or kw in string_lower for kw in keywords):
            relevant_fields[field_name] = field_info

    print(f"\n[2] Campos relevantes para propiedades: {len(relevant_fields)}")
    print("=" * 90)

    # Agrupar por categorías
    categories = {
        'Ubicación': [],
        'Características': [],
        'Precio': [],
        'Tipo/Estado': [],
        'Otros': []
    }

    for field_name, field_info in sorted(relevant_fields.items()):
        field_lower = field_name.lower()

        if any(kw in field_lower for kw in ['state', 'city', 'region', 'neighborhood', 'street', 'zip', 'latitude', 'longitude', 'location', 'address']):
            categories['Ubicación'].append((field_name, field_info))
        elif any(kw in field_lower for kw in ['bedroom', 'bathroom', 'garage', 'area', 'floor', 'unit', 'tower']):
            categories['Características'].append((field_name, field_info))
        elif any(kw in field_lower for kw in ['price', 'rent', 'sale', 'cost']):
            categories['Precio'].append((field_name, field_info))
        elif any(kw in field_lower for kw in ['type', 'subtype', 'status', 'property']):
            categories['Tipo/Estado'].append((field_name, field_info))
        else:
            categories['Otros'].append((field_name, field_info))

    # Imprimir por categorías
    for category, fields in categories.items():
        if fields:
            print(f"\n{'='*90}")
            print(f"{category.upper()} ({len(fields)} campos)")
            print("=" * 90)

            for field_name, field_info in fields:
                print(f"\n  {field_name}")
                print(f"    Etiqueta: {field_info.get('string')}")
                print(f"    Tipo: {field_info.get('type')}")

                if field_info.get('relation'):
                    print(f"    Relación: {field_info.get('relation')}")

                if field_info.get('required'):
                    print(f"    Requerido: SÍ")

                if field_info.get('help'):
                    help_text = field_info['help'][:100]
                    print(f"    Ayuda: {help_text}...")

    # Guardar en JSON
    output = {
        'total_campos': len(all_fields),
        'campos_propiedades': len(relevant_fields),
        'campos_por_categoria': {
            cat: [
                {
                    'nombre': f[0],
                    'etiqueta': f[1].get('string'),
                    'tipo': f[1].get('type'),
                    'relacion': f[1].get('relation')
                }
                for f in fields
            ]
            for cat, fields in categories.items() if fields
        }
    }

    with open('cloudpepper_property_fields.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 90)
    print(f"💾 Guardado en: cloudpepper_property_fields.json")
    print("=" * 90)

    # Intentar leer una propiedad de ejemplo
    print("\n[3] Leyendo propiedad de ejemplo (ID=9947)...")

    try:
        # Leer solo campos básicos primero
        basic_fields = ['id', 'name', 'default_code', 'is_property']

        property_data = models.execute_kw(
            ODOO17['db'], uid, ODOO17['password'],
            'product.template', 'read',
            [[9947]],
            {'fields': basic_fields}
        )[0]

        print(f"\n    ID: {property_data.get('id')}")
        print(f"    Nombre: {property_data.get('name')}")
        print(f"    Código: {property_data.get('default_code')}")
        print(f"    Es Propiedad: {property_data.get('is_property')}")

        # Ahora intentar leer campos de ubicación uno por uno
        print("\n[4] Probando campos de ubicación individualmente...")

        location_fields_to_test = [
            'state_id', 'city_id', 'region_id', 'neighborhood_id',
            'property_state_id', 'property_city_id', 'property_region_id', 'property_neighborhood_id',
            'street', 'street2', 'zip', 'latitude', 'longitude'
        ]

        available_location_fields = []

        for field in location_fields_to_test:
            try:
                data = models.execute_kw(
                    ODOO17['db'], uid, ODOO17['password'],
                    'product.template', 'read',
                    [[9947]],
                    {'fields': [field]}
                )[0]

                if field in data:
                    available_location_fields.append(field)
                    print(f"    ✅ {field}: {data[field]}")

            except:
                print(f"    ❌ {field}: NO EXISTE")

        print(f"\n    Campos de ubicación disponibles: {len(available_location_fields)}")
        print(f"    {available_location_fields}")

    except Exception as e:
        print(f"    ERROR: {e}")

    print("\n" + "=" * 90)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para comparar el modelo product.template entre dos bases de datos de Odoo
"""
import xmlrpc.client
import sys
import io
import json

# Configurar salida UTF-8 para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración de las dos bases de datos
DB1 = {
    'name': 'CloudPepper (Producción)',
    'url': 'https://inmobiliariabohio.cloudpepper.site',
    'db': 'inmobiliariabohio.cloudpepper.site',
    'username': 'admin',
    'password': 'admin'
}

DB2 = {
    'name': 'Odoo.com (Desarrollo)',
    'url': 'https://darm1640-bohio-18.odoo.com',
    'db': 'darm1640-bohio-18-main-24081960',
    'username': 'admin',
    'password': '123456'
}


def conectar_odoo(config):
    """Conectar a una instancia de Odoo y autenticar"""
    try:
        print(f"\nConectando a {config['name']}...")
        print(f"  URL: {config['url']}")

        common = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/common")
        uid = common.authenticate(config['db'], config['username'], config['password'], {})

        if not uid:
            print(f"  ERROR: Autenticación fallida")
            return None, None

        print(f"  OK: UID={uid}")
        models = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/object")
        return uid, models

    except Exception as e:
        print(f"  ERROR: {e}")
        return None, None


def obtener_campos_modelo(uid, models, db_config, modelo='product.template'):
    """Obtener todos los campos de un modelo"""
    try:
        print(f"\nObteniendo campos del modelo '{modelo}'...")

        # Obtener información de campos usando fields_get
        campos = models.execute_kw(
            db_config['db'], uid, db_config['password'],
            modelo, 'fields_get',
            [],
            {'attributes': ['string', 'type', 'relation', 'required', 'readonly', 'help', 'store']}
        )

        print(f"  Total campos encontrados: {len(campos)}")
        return campos

    except Exception as e:
        print(f"  ERROR: {e}")
        return {}


def comparar_campos(campos_db1, campos_db2):
    """Comparar campos entre dos bases de datos"""

    campos1_set = set(campos_db1.keys())
    campos2_set = set(campos_db2.keys())

    # Campos solo en DB1
    solo_db1 = campos1_set - campos2_set

    # Campos solo en DB2
    solo_db2 = campos2_set - campos1_set

    # Campos en ambas
    comunes = campos1_set & campos2_set

    # Campos con diferencias en tipo
    diferencias = []
    for campo in comunes:
        info1 = campos_db1[campo]
        info2 = campos_db2[campo]

        if info1.get('type') != info2.get('type'):
            diferencias.append({
                'campo': campo,
                'tipo_db1': info1.get('type'),
                'tipo_db2': info2.get('type')
            })

    return {
        'solo_db1': sorted(solo_db1),
        'solo_db2': sorted(solo_db2),
        'comunes': sorted(comunes),
        'diferencias_tipo': diferencias
    }


def filtrar_campos_propiedades(campos):
    """Filtrar solo campos relacionados con propiedades inmobiliarias"""
    keywords = [
        'property', 'real_estate', 'estate', 'location', 'address',
        'bedroom', 'bathroom', 'area', 'size', 'garage', 'parking',
        'amenity', 'tower', 'floor', 'unit', 'project', 'worksite',
        'image', 'photo', 'gallery', 'attachment', 'document',
        'contract', 'rental', 'sale', 'price', 'city', 'state',
        'neighborhood', 'region', 'zone', 'latitude', 'longitude',
        'gps', 'map', 'street', 'number'
    ]

    campos_filtrados = {}
    for nombre, info in campos.items():
        nombre_lower = nombre.lower()
        string_lower = info.get('string', '').lower()

        if any(keyword in nombre_lower or keyword in string_lower for keyword in keywords):
            campos_filtrados[nombre] = info

    return campos_filtrados


def imprimir_detalle_campo(nombre, info, prefijo="  "):
    """Imprimir detalles de un campo"""
    print(f"{prefijo}{nombre}")
    print(f"{prefijo}  Etiqueta: {info.get('string', 'N/A')}")
    print(f"{prefijo}  Tipo: {info.get('type', 'N/A')}")

    if info.get('relation'):
        print(f"{prefijo}  Relación: {info['relation']}")

    if info.get('required'):
        print(f"{prefijo}  Requerido: Sí")

    if info.get('readonly'):
        print(f"{prefijo}  Solo lectura: Sí")

    if info.get('help'):
        print(f"{prefijo}  Ayuda: {info['help'][:100]}...")

    print()


def main():
    print("=" * 80)
    print("COMPARACIÓN DE MODELO product.template ENTRE DOS BASES DE DATOS")
    print("=" * 80)

    # Conectar a ambas bases de datos
    uid1, models1 = conectar_odoo(DB1)
    uid2, models2 = conectar_odoo(DB2)

    if not uid1 or not uid2:
        print("\nERROR: No se pudo conectar a una o ambas bases de datos")
        sys.exit(1)

    # Obtener campos
    campos_db1 = obtener_campos_modelo(uid1, models1, DB1)
    campos_db2 = obtener_campos_modelo(uid2, models2, DB2)

    # Comparar
    comparacion = comparar_campos(campos_db1, campos_db2)

    print("\n" + "=" * 80)
    print("RESUMEN DE COMPARACIÓN")
    print("=" * 80)
    print(f"\nCampos en {DB1['name']}: {len(campos_db1)}")
    print(f"Campos en {DB2['name']}: {len(campos_db2)}")
    print(f"Campos comunes: {len(comparacion['comunes'])}")
    print(f"Solo en {DB1['name']}: {len(comparacion['solo_db1'])}")
    print(f"Solo en {DB2['name']}: {len(comparacion['solo_db2'])}")
    print(f"Diferencias de tipo: {len(comparacion['diferencias_tipo'])}")

    # Filtrar campos de propiedades
    print("\n" + "=" * 80)
    print("CAMPOS RELACIONADOS CON PROPIEDADES INMOBILIARIAS")
    print("=" * 80)

    campos_prop_db1 = filtrar_campos_propiedades(campos_db1)
    campos_prop_db2 = filtrar_campos_propiedades(campos_db2)

    print(f"\nCampos de propiedades en {DB1['name']}: {len(campos_prop_db1)}")
    print(f"Campos de propiedades en {DB2['name']}: {len(campos_prop_db2)}")

    # Campos de propiedades solo en DB1
    campos_prop_solo_db1 = set(campos_prop_db1.keys()) - set(campos_prop_db2.keys())
    if campos_prop_solo_db1:
        print(f"\n--- CAMPOS DE PROPIEDADES SOLO EN {DB1['name']} ({len(campos_prop_solo_db1)}) ---")
        for campo in sorted(campos_prop_solo_db1):
            imprimir_detalle_campo(campo, campos_prop_db1[campo])

    # Campos de propiedades solo en DB2
    campos_prop_solo_db2 = set(campos_prop_db2.keys()) - set(campos_prop_db1.keys())
    if campos_prop_solo_db2:
        print(f"\n--- CAMPOS DE PROPIEDADES SOLO EN {DB2['name']} ({len(campos_prop_solo_db2)}) ---")
        for campo in sorted(campos_prop_solo_db2):
            imprimir_detalle_campo(campo, campos_prop_db2[campo])

    # Campos de propiedades con diferencias
    campos_prop_comunes = set(campos_prop_db1.keys()) & set(campos_prop_db2.keys())
    diferencias_props = []
    for campo in campos_prop_comunes:
        info1 = campos_prop_db1[campo]
        info2 = campos_prop_db2[campo]

        if info1.get('type') != info2.get('type') or info1.get('relation') != info2.get('relation'):
            diferencias_props.append({
                'campo': campo,
                'db1': info1,
                'db2': info2
            })

    if diferencias_props:
        print(f"\n--- CAMPOS DE PROPIEDADES CON DIFERENCIAS ({len(diferencias_props)}) ---")
        for diff in diferencias_props:
            print(f"\nCampo: {diff['campo']}")
            print(f"  En {DB1['name']}:")
            print(f"    Tipo: {diff['db1'].get('type')}")
            print(f"    Relación: {diff['db1'].get('relation', 'N/A')}")
            print(f"  En {DB2['name']}:")
            print(f"    Tipo: {diff['db2'].get('type')}")
            print(f"    Relación: {diff['db2'].get('relation', 'N/A')}")

    # Guardar resultados en JSON
    resultado = {
        'db1': {
            'nombre': DB1['name'],
            'total_campos': len(campos_db1),
            'campos_propiedades': len(campos_prop_db1),
            'campos_exclusivos': list(campos_prop_solo_db1)
        },
        'db2': {
            'nombre': DB2['name'],
            'total_campos': len(campos_db2),
            'campos_propiedades': len(campos_prop_db2),
            'campos_exclusivos': list(campos_prop_solo_db2)
        },
        'diferencias': [
            {
                'campo': d['campo'],
                'tipo_db1': d['db1'].get('type'),
                'tipo_db2': d['db2'].get('type'),
                'relacion_db1': d['db1'].get('relation'),
                'relacion_db2': d['db2'].get('relation')
            }
            for d in diferencias_props
        ]
    }

    with open('comparacion_template_models.json', 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("Resultados guardados en: comparacion_template_models.json")
    print("=" * 80)


if __name__ == "__main__":
    main()

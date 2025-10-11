#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para revisar la ciudad y barrios de los productos inmobiliarios en Odoo 18
Base de datos: darm1640-bohio-18-main-24081960
"""

import xmlrpc.client
import sys
import io

# Configurar la salida para UTF-8 en Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración de conexión
url = 'https://darm1640-bohio-18.odoo.com'
db = 'darm1640-bohio-18-main-24081960'
username = 'admin'
password = '123456'

print("=" * 80)
print("REVISIÓN DE CIUDADES Y BARRIOS EN PRODUCTOS INMOBILIARIOS")
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

    # Campos a revisar
    fields_to_check = [
        'id', 'name', 'default_code',
        'city', 'city_id',
        'neighborhood', 'region_id',
        'street', 'street2',
        'state_id', 'country_id',
        'type_service'
    ]

    # Buscar todas las propiedades
    print("Buscando propiedades en el sistema...")
    property_ids = models.execute_kw(
        db, uid, password,
        'product.template', 'search',
        [[('is_property', '=', True)]],
        {'limit': 100}
    )

    total_properties = len(property_ids)
    print(f"[OK] Se encontraron {total_properties} propiedades\n")

    if total_properties == 0:
        print("[ADVERTENCIA] No hay propiedades en el sistema")
        exit(0)

    # Leer información de las propiedades
    properties = models.execute_kw(
        db, uid, password,
        'product.template', 'read',
        [property_ids],
        {'fields': fields_to_check}
    )

    # Análisis de datos
    print("=" * 80)
    print("ANÁLISIS DE UBICACIONES")
    print("=" * 80)

    stats = {
        'total': total_properties,
        'con_city_id': 0,
        'con_city_char': 0,
        'con_neighborhood': 0,
        'con_region_id': 0,
        'sin_ubicacion': 0,
        'venta': 0,
        'arriendo': 0
    }

    properties_sin_ubicacion = []

    for prop in properties:
        # Estadísticas de campos de ubicación
        if prop.get('city_id'):
            stats['con_city_id'] += 1
        if prop.get('city'):
            stats['con_city_char'] += 1
        if prop.get('neighborhood'):
            stats['con_neighborhood'] += 1
        if prop.get('region_id'):
            stats['con_region_id'] += 1

        # Propiedades sin ninguna ubicación
        if not any([prop.get('city_id'), prop.get('city'),
                   prop.get('neighborhood'), prop.get('region_id')]):
            stats['sin_ubicacion'] += 1
            properties_sin_ubicacion.append(prop)

        # Tipo de servicio
        if prop.get('type_service') == 'sale':
            stats['venta'] += 1
        elif prop.get('type_service') == 'rent':
            stats['arriendo'] += 1

    # Mostrar estadísticas
    print(f"\nESTADISTICAS GENERALES:")
    print(f"  Total de propiedades: {stats['total']}")
    print(f"  Propiedades en venta: {stats['venta']}")
    print(f"  Propiedades en arriendo: {stats['arriendo']}")

    print(f"\nDATOS DE UBICACION:")
    print(f"  Con city_id (Many2one res.city): {stats['con_city_id']} ({stats['con_city_id']*100//stats['total'] if stats['total'] > 0 else 0}%)")
    print(f"  Con city (campo Char): {stats['con_city_char']} ({stats['con_city_char']*100//stats['total'] if stats['total'] > 0 else 0}%)")
    print(f"  Con neighborhood (Barrio Char): {stats['con_neighborhood']} ({stats['con_neighborhood']*100//stats['total'] if stats['total'] > 0 else 0}%)")
    print(f"  Con region_id (Barrio Many2one): {stats['con_region_id']} ({stats['con_region_id']*100//stats['total'] if stats['total'] > 0 else 0}%)")
    print(f"  Sin datos de ubicacion: {stats['sin_ubicacion']}")

    # Mostrar propiedades sin ubicación
    if properties_sin_ubicacion:
        print(f"\n[ADVERTENCIA] PROPIEDADES SIN DATOS DE UBICACION ({len(properties_sin_ubicacion)}):")
        print("-" * 80)
        for prop in properties_sin_ubicacion[:10]:  # Mostrar máximo 10
            print(f"  ID: {prop['id']}")
            print(f"  Codigo: {prop.get('default_code', 'N/A')}")
            print(f"  Nombre: {prop.get('name', 'N/A')}")
            print(f"  Tipo: {prop.get('type_service', 'N/A')}")
            print("-" * 80)

    # Mostrar ejemplos de propiedades CON ubicación completa
    print(f"\n[OK] EJEMPLOS DE PROPIEDADES CON UBICACION COMPLETA:")
    print("-" * 80)

    ejemplos_completos = [
        p for p in properties
        if p.get('city_id') and p.get('region_id')
    ][:5]

    for prop in ejemplos_completos:
        print(f"  ID: {prop['id']}")
        print(f"  Codigo: {prop.get('default_code', 'N/A')}")
        print(f"  Nombre: {prop.get('name', 'N/A')[:60]}")
        print(f"  Ciudad (city_id): {prop.get('city_id', ['', ''])[1] if prop.get('city_id') else 'N/A'}")
        print(f"  Ciudad (char): {prop.get('city', 'N/A')}")
        print(f"  Barrio (neighborhood): {prop.get('neighborhood', 'N/A')}")
        print(f"  Barrio (region_id): {prop.get('region_id', ['', ''])[1] if prop.get('region_id') else 'N/A'}")
        print(f"  Direccion: {prop.get('street', 'N/A')}")
        print(f"  Tipo: {prop.get('type_service', 'N/A')}")
        print("-" * 80)

    # Resumen final
    print(f"\nRESUMEN:")
    if stats['con_city_id'] > 0 and stats['con_region_id'] > 0:
        print(f"  [OK] La mayoria de propiedades tienen datos de ciudad y barrio")
        print(f"  [OK] Se esta usando el campo city_id (Many2one)")
        print(f"  [OK] Se esta usando el campo region_id (Many2one) para barrios")
    elif stats['con_city_char'] > 0 or stats['con_neighborhood'] > 0:
        print(f"  [ADVERTENCIA] Hay propiedades con campos de texto (Char) pero sin relaciones (Many2one)")
        print(f"  [INFO] Se recomienda usar city_id y region_id para mejor integracion")
    else:
        print(f"  [ERROR] Muchas propiedades sin datos de ubicacion")
        print(f"  [INFO] Se recomienda completar los datos de ciudad y barrio")

    print("\n" + "=" * 80)
    print("REVISIÓN COMPLETADA")
    print("=" * 80)

except Exception as e:
    print(f"\n[ERROR] Error durante la ejecucion:")
    print(f"   {type(e).__name__}: {str(e)}")
    import traceback
    print("\nTraceback completo:")
    traceback.print_exc()
    exit(1)

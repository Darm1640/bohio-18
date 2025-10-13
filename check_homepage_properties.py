#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar propiedades que aparecerían en el homepage
Verifica los 3 filtros principales: Arriendo, Venta usada, Proyectos
"""

import xmlrpc.client

# Configuración de conexión
URL = 'http://localhost:8069'
DB = 'bohio_db'
USERNAME = 'admin'
PASSWORD = 'admin'

# Conectar
common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
uid = common.authenticate(DB, USERNAME, PASSWORD, {})

if not uid:
    print("❌ Error de autenticación")
    exit(1)

models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

print("="*80)
print("ANÁLISIS DE PROPIEDADES PARA HOMEPAGE")
print("="*80)

# 1. ARRIENDO con ubicación
print("\n1️⃣  ARRIENDO (type_service=rent, has_location=true)")
print("-" * 80)

rent_domain = [
    ('is_property', '=', True),
    ('active', '=', True),
    ('state', '=', 'free'),
    '|', '|',
    ('type_service', '=', 'rent'),
    ('type_service', '=', 'sale_rent'),
    ('type_service', '=', 'vacation_rent'),
    ('latitude', '!=', False),
    ('longitude', '!=', False),
]

rent_count = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_count', [rent_domain])
print(f"Total propiedades de arriendo CON ubicación: {rent_count}")

if rent_count > 0:
    rent_props = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_read',
        [rent_domain],
        {'fields': ['name', 'default_code', 'type_service', 'latitude', 'longitude', 'city_id', 'net_rental_price'], 'limit': 10, 'order': 'create_date desc'})

    print(f"\nPrimeras {min(10, rent_count)} propiedades:")
    for prop in rent_props:
        city = prop.get('city_id', [False, 'Sin ciudad'])[1] if prop.get('city_id') else 'Sin ciudad'
        lat = prop.get('latitude', 0)
        lon = prop.get('longitude', 0)
        price = prop.get('net_rental_price', 0)
        print(f"  - {prop['default_code'] or 'N/A'}: {prop['name']}")
        print(f"    Ciudad: {city} | Coords: ({lat:.4f}, {lon:.4f}) | Precio: ${price:,.0f}/mes")
else:
    print("⚠️  NO HAY PROPIEDADES DE ARRIENDO CON UBICACIÓN")
    # Verificar cuántas hay sin ubicación
    rent_no_loc = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_count', [
        ('is_property', '=', True),
        ('active', '=', True),
        ('state', '=', 'free'),
        '|', '|',
        ('type_service', '=', 'rent'),
        ('type_service', '=', 'sale_rent'),
        ('type_service', '=', 'vacation_rent'),
        '|',
        ('latitude', '=', False),
        ('longitude', '=', False),
    ])
    print(f"   Propiedades de arriendo SIN ubicación: {rent_no_loc}")

# 2. VENTA USADA con ubicación (sin proyecto)
print("\n\n2️⃣  VENTA DE INMUEBLES USADOS (type_service=sale, has_location=true, has_project=false)")
print("-" * 80)

used_sale_domain = [
    ('is_property', '=', True),
    ('active', '=', True),
    ('state', '=', 'free'),
    '|',
    ('type_service', '=', 'sale'),
    ('type_service', '=', 'sale_rent'),
    ('latitude', '!=', False),
    ('longitude', '!=', False),
    ('project_worksite_id', '=', False),  # SIN proyecto
]

used_count = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_count', [used_sale_domain])
print(f"Total propiedades usadas en venta CON ubicación (SIN proyecto): {used_count}")

if used_count > 0:
    used_props = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_read',
        [used_sale_domain],
        {'fields': ['name', 'default_code', 'type_service', 'latitude', 'longitude', 'city_id', 'net_price', 'project_worksite_id'], 'limit': 10, 'order': 'create_date desc'})

    print(f"\nPrimeras {min(10, used_count)} propiedades:")
    for prop in used_props:
        city = prop.get('city_id', [False, 'Sin ciudad'])[1] if prop.get('city_id') else 'Sin ciudad'
        lat = prop.get('latitude', 0)
        lon = prop.get('longitude', 0)
        price = prop.get('net_price', 0)
        has_project = prop.get('project_worksite_id', False)
        print(f"  - {prop['default_code'] or 'N/A'}: {prop['name']}")
        print(f"    Ciudad: {city} | Coords: ({lat:.4f}, {lon:.4f}) | Precio: ${price:,.0f} | Proyecto: {has_project}")
else:
    print("⚠️  NO HAY PROPIEDADES USADAS EN VENTA CON UBICACIÓN")
    # Verificar con proyecto
    used_with_project = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_count', [
        ('is_property', '=', True),
        ('active', '=', True),
        ('state', '=', 'free'),
        '|',
        ('type_service', '=', 'sale'),
        ('type_service', '=', 'sale_rent'),
        ('project_worksite_id', '!=', False),
    ])
    print(f"   Propiedades en venta CON proyecto: {used_with_project}")

# 3. PROYECTOS con ubicación
print("\n\n3️⃣  PROYECTOS EN VENTA (type_service=sale, has_location=true, has_project=true)")
print("-" * 80)

project_domain = [
    ('is_property', '=', True),
    ('active', '=', True),
    ('state', '=', 'free'),
    '|',
    ('type_service', '=', 'sale'),
    ('type_service', '=', 'sale_rent'),
    ('latitude', '!=', False),
    ('longitude', '!=', False),
    ('project_worksite_id', '!=', False),  # CON proyecto
]

project_count = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_count', [project_domain])
print(f"Total proyectos en venta CON ubicación: {project_count}")

if project_count > 0:
    project_props = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_read',
        [project_domain],
        {'fields': ['name', 'default_code', 'type_service', 'latitude', 'longitude', 'city_id', 'net_price', 'project_worksite_id'], 'limit': 10, 'order': 'create_date desc'})

    print(f"\nPrimeros {min(10, project_count)} proyectos:")
    for prop in project_props:
        city = prop.get('city_id', [False, 'Sin ciudad'])[1] if prop.get('city_id') else 'Sin ciudad'
        lat = prop.get('latitude', 0)
        lon = prop.get('longitude', 0)
        price = prop.get('net_price', 0)
        project = prop.get('project_worksite_id', [False, 'N/A'])[1] if prop.get('project_worksite_id') else 'N/A'
        print(f"  - {prop['default_code'] or 'N/A'}: {prop['name']}")
        print(f"    Ciudad: {city} | Proyecto: {project} | Coords: ({lat:.4f}, {lon:.4f}) | Precio: ${price:,.0f}")
else:
    print("⚠️  NO HAY PROYECTOS EN VENTA CON UBICACIÓN")

# RESUMEN GENERAL
print("\n" + "="*80)
print("RESUMEN")
print("="*80)
print(f"✅ Arriendo (con ubicación): {rent_count} propiedades")
print(f"✅ Venta usada (con ubicación, sin proyecto): {used_count} propiedades")
print(f"✅ Proyectos (con ubicación): {project_count} propiedades")
print()

if rent_count == 0 and used_count == 0 and project_count == 0:
    print("❌ PROBLEMA CRÍTICO: NO HAY PROPIEDADES CON UBICACIÓN (LATITUD/LONGITUD)")
    print()
    print("SOLUCIONES:")
    print("1. Agregar coordenadas (latitude, longitude) a las propiedades existentes")
    print("2. Cambiar homepage_properties.js para NO requerir has_location: true")
    print("3. Usar un servicio de geocodificación automática para asignar coordenadas")
else:
    print("✅ El homepage debería mostrar propiedades correctamente")
    if rent_count < 4:
        print(f"⚠️  ADVERTENCIA: Solo {rent_count} propiedades de arriendo (se recomiendan mínimo 4 para grid)")
    if used_count < 4:
        print(f"⚠️  ADVERTENCIA: Solo {used_count} propiedades usadas (se recomiendan mínimo 4 para grid)")
    if project_count < 4:
        print(f"⚠️  ADVERTENCIA: Solo {project_count} proyectos (se recomiendan mínimo 4 para grid)")

print("\n" + "="*80)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import xmlrpc.client

URL = 'http://localhost:8069'
DB = 'bohio_db'
USERNAME = 'admin'
PASSWORD = 'admin'

common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common', allow_none=True)
uid = common.authenticate(DB, USERNAME, PASSWORD, {})

if not uid:
    print("Error autenticación")
    exit(1)

models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object', allow_none=True)

# Check 1: Total propiedades
total = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_count', [
    [('is_property', '=', True), ('active', '=', True), ('state', '=', 'free')]
])
print(f"Total propiedades LIBRES: {total}")

# Check 2: Con ubicación
with_location = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_count', [
    [('is_property', '=', True), ('active', '=', True), ('state', '=', 'free'),
     ('latitude', '!=', False), ('longitude', '!=', False)]
])
print(f"Con ubicación (lat/lon): {with_location}")

# Check 3: Arriendo con ubicación
rent_located = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_count', [
    [('is_property', '=', True), ('active', '=', True), ('state', '=', 'free'),
     ('type_service', 'in', ['rent', 'sale_rent', 'vacation_rent']),
     ('latitude', '!=', False), ('longitude', '!=', False)]
])
print(f"Arriendo CON ubicación: {rent_located}")

# Check 4: Venta usada (sin proyecto) con ubicación
sale_no_project = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_count', [
    [('is_property', '=', True), ('active', '=', True), ('state', '=', 'free'),
     ('type_service', 'in', ['sale', 'sale_rent']),
     ('project_worksite_id', '=', False),
     ('latitude', '!=', False), ('longitude', '!=', False)]
])
print(f"Venta usada CON ubicación: {sale_no_project}")

# Check 5: Proyectos con ubicación
projects_located = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_count', [
    [('is_property', '=', True), ('active', '=', True), ('state', '=', 'free'),
     ('type_service', 'in', ['sale', 'sale_rent']),
     ('project_worksite_id', '!=', False),
     ('latitude', '!=', False), ('longitude', '!=', False)]
])
print(f"Proyectos CON ubicación: {projects_located}")

print("\n" + "="*50)
if with_location == 0:
    print("❌ PROBLEMA: Ninguna propiedad tiene coordenadas")
    print("SOLUCIÓN: Quitar filtro has_location en JavaScript")
elif rent_located < 4 or sale_no_project < 4 or projects_located < 4:
    print("⚠️  ADVERTENCIA: Pocas propiedades por categoría")
    print(f"   Mínimo recomendado: 4 por sección")
else:
    print("✅ Suficientes propiedades con ubicación")

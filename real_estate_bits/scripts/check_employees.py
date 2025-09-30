#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Verificación de Empleados
====================================
"""

import xmlrpc.client

DESTINATION = {
    'url': 'https://darm1640-bohio-18.odoo.com',
    'db': 'darm1640-bohio-18-main-24081960',
    'username': 'admin',
    'password': 'admin'
}

print("\nConectando...")
common = xmlrpc.client.ServerProxy(f"{DESTINATION['url']}/xmlrpc/2/common")
models = xmlrpc.client.ServerProxy(f"{DESTINATION['url']}/xmlrpc/2/object")
uid = common.authenticate(DESTINATION['db'], DESTINATION['username'], DESTINATION['password'], {})

# Buscar todos los empleados
print("\n=== EMPLEADOS ACTIVOS ===")
active_ids = models.execute_kw(
    DESTINATION['db'], uid, DESTINATION['password'],
    'hr.employee', 'search',
    [[('active', '=', True)]]
)
print(f"Total activos: {len(active_ids)}")

if active_ids:
    emps = models.execute_kw(
        DESTINATION['db'], uid, DESTINATION['password'],
        'hr.employee', 'read',
        [active_ids], {'fields': ['id', 'name', 'work_email', 'user_id']}
    )
    for emp in emps[-10:]:  # Últimos 10
        user_info = f" -> Usuario: {emp['user_id'][1]}" if emp.get('user_id') else " [sin usuario]"
        print(f"  ID {emp['id']}: {emp['name']}{user_info}")

print("\n=== EMPLEADOS INACTIVOS ===")
inactive_ids = models.execute_kw(
    DESTINATION['db'], uid, DESTINATION['password'],
    'hr.employee', 'search',
    [[('active', '=', False)]]
)
print(f"Total inactivos: {len(inactive_ids)}")

print("\n=== USUARIOS ===")
user_ids = models.execute_kw(
    DESTINATION['db'], uid, DESTINATION['password'],
    'res.users', 'search',
    [[('id', '!=', 1)]]
)
print(f"Total usuarios (sin admin): {len(user_ids)}")
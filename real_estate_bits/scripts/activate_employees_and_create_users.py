#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Activación de Empleados y Creación de Usuarios
=========================================================
Activa empleados existentes y crea sus usuarios sin enviar emails
"""

import xmlrpc.client
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

DESTINATION = {
    'url': 'https://darm1640-bohio-18.odoo.com',
    'db': 'darm1640-bohio-18-main-24081960',
    'username': 'admin',
    'password': 'admin'
}

logger.info("\n" + "="*70)
logger.info("# ACTIVACIÓN DE EMPLEADOS Y CREACIÓN DE USUARIOS")
logger.info("="*70)

logger.info("\nConectando...")
common = xmlrpc.client.ServerProxy(f"{DESTINATION['url']}/xmlrpc/2/common")
models = xmlrpc.client.ServerProxy(f"{DESTINATION['url']}/xmlrpc/2/object")
uid = common.authenticate(DESTINATION['db'], DESTINATION['username'], DESTINATION['password'], {})
logger.info(f"OK - Conectado (UID: {uid})")

# Buscar empleados inactivos
logger.info("\nBuscando empleados inactivos...")
inactive_ids = models.execute_kw(
    DESTINATION['db'], uid, DESTINATION['password'],
    'hr.employee', 'search',
    [[('active', '=', False)]]
)

logger.info(f"Encontrados {len(inactive_ids)} empleados inactivos")

if not inactive_ids:
    logger.info("No hay empleados inactivos para procesar")
    exit()

# Leer datos de empleados
logger.info("\nLeyendo datos de empleados...")
employees = models.execute_kw(
    DESTINATION['db'], uid, DESTINATION['password'],
    'hr.employee', 'read',
    [inactive_ids], {'fields': ['id', 'name', 'work_email', 'user_id']}
)

# Buscar grupo de empleado
logger.info("\nBuscando grupo 'Employee'...")
employee_group_ids = models.execute_kw(
    DESTINATION['db'], uid, DESTINATION['password'],
    'res.groups', 'search',
    [[('name', '=', 'Employee')]], {'limit': 1}
)
employee_group = employee_group_ids[0] if employee_group_ids else 1
logger.info(f"Grupo Employee ID: {employee_group}")

# Obtener company_id
company_ids = models.execute_kw(
    DESTINATION['db'], uid, DESTINATION['password'],
    'res.company', 'search',
    [[('id', '=', 1)]], {'limit': 1}
)
company_id = company_ids[0] if company_ids else 1

# Procesar cada empleado
activated = 0
users_created = 0
users_skipped = 0

for emp in employees:
    emp_id = emp['id']
    emp_name = emp['name']
    work_email = emp.get('work_email')

    logger.info(f"\n[{emp_id}] {emp_name}")

    # 1. Activar empleado
    try:
        models.execute_kw(
            DESTINATION['db'], uid, DESTINATION['password'],
            'hr.employee', 'write',
            [[emp_id], {'active': True}]
        )
        logger.info(f"   ✓ Empleado activado")
        activated += 1
    except Exception as e:
        logger.error(f"   ✗ Error activando: {e}")
        continue

    # 2. Crear usuario si tiene email y no tiene usuario
    if not work_email:
        logger.info(f"   - Sin email, no se crea usuario")
        users_skipped += 1
        continue

    if emp.get('user_id'):
        logger.info(f"   - Ya tiene usuario: {emp['user_id'][1]}")
        users_skipped += 1
        continue

    # Verificar si ya existe usuario con ese email
    try:
        existing_user_ids = models.execute_kw(
            DESTINATION['db'], uid, DESTINATION['password'],
            'res.users', 'search',
            [[('login', '=', work_email)]], {'limit': 1}
        )

        if existing_user_ids:
            user_id = existing_user_ids[0]
            logger.info(f"   ✓ Usuario existente encontrado: {work_email} -> {user_id}")

            # Vincular usuario existente al empleado
            models.execute_kw(
                DESTINATION['db'], uid, DESTINATION['password'],
                'hr.employee', 'write',
                [[emp_id], {'user_id': user_id}]
            )
            logger.info(f"   ✓ Usuario vinculado al empleado")
            users_skipped += 1
            continue

        # Crear nuevo usuario ACTIVO
        user_vals = {
            'name': emp_name,
            'login': work_email,
            'email': work_email,
            'company_id': company_id,
            'company_ids': [(6, 0, [company_id])],
            'active': True,
            'password': 'changeme123',  # Password temporal
            'groups_id': [(6, 0, [employee_group])]
        }

        user_id = models.execute_kw(
            DESTINATION['db'], uid, DESTINATION['password'],
            'res.users', 'create',
            [[user_vals]]
        )

        logger.info(f"   ✓ Usuario creado: {work_email} -> {user_id}")

        # Vincular usuario al empleado
        models.execute_kw(
            DESTINATION['db'], uid, DESTINATION['password'],
            'hr.employee', 'write',
            [[emp_id], {'user_id': user_id}]
        )
        logger.info(f"   ✓ Usuario vinculado al empleado")
        users_created += 1

    except Exception as e:
        logger.error(f"   ✗ Error creando usuario: {e}")
        users_skipped += 1

# Resumen final
logger.info("\n" + "="*70)
logger.info("# RESUMEN FINAL")
logger.info("="*70)
logger.info(f"Total empleados procesados: {len(employees)}")
logger.info(f"Empleados activados:        {activated}")
logger.info(f"Usuarios creados:           {users_created}")
logger.info(f"Usuarios omitidos:          {users_skipped}")
logger.info("="*70)
logger.info("\n✓ Proceso completado")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Vinculación de Usuarios a Empleados
==============================================
Vincula usuarios con empleados por email
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
logger.info("# VINCULACIÓN DE USUARIOS A EMPLEADOS")
logger.info("="*70)

logger.info("\nConectando...")
common = xmlrpc.client.ServerProxy(f"{DESTINATION['url']}/xmlrpc/2/common")
models = xmlrpc.client.ServerProxy(f"{DESTINATION['url']}/xmlrpc/2/object")
uid = common.authenticate(DESTINATION['db'], DESTINATION['username'], DESTINATION['password'], {})
logger.info(f"OK - Conectado (UID: {uid})")

# Buscar empleados sin usuario
logger.info("\nBuscando empleados sin usuario vinculado...")
emp_ids = models.execute_kw(
    DESTINATION['db'], uid, DESTINATION['password'],
    'hr.employee', 'search',
    [[('user_id', '=', False), ('work_email', '!=', False)]]
)

logger.info(f"Encontrados {len(emp_ids)} empleados sin usuario")

if not emp_ids:
    logger.info("Todos los empleados ya tienen usuario vinculado")
    exit()

# Leer empleados
employees = models.execute_kw(
    DESTINATION['db'], uid, DESTINATION['password'],
    'hr.employee', 'read',
    [emp_ids], {'fields': ['id', 'name', 'work_email']}
)

linked = 0
not_found = 0

for emp in employees:
    emp_id = emp['id']
    emp_name = emp['name']
    work_email = emp.get('work_email')

    if not work_email:
        continue

    logger.info(f"\n[{emp_id}] {emp_name} ({work_email})")

    # Buscar usuario con ese email
    user_ids = models.execute_kw(
        DESTINATION['db'], uid, DESTINATION['password'],
        'res.users', 'search',
        [[('login', '=', work_email)]], {'limit': 1}
    )

    if not user_ids:
        logger.info(f"   ✗ Usuario NO encontrado")
        not_found += 1
        continue

    user_id = user_ids[0]
    logger.info(f"   ✓ Usuario encontrado: {user_id}")

    # Vincular usando write directamente en el usuario (evita el error)
    try:
        models.execute_kw(
            DESTINATION['db'], uid, DESTINATION['password'],
            'res.users', 'write',
            [[user_id], {'employee_ids': [(4, emp_id)]}]
        )
        logger.info(f"   ✓ Usuario vinculado al empleado")
        linked += 1
    except Exception as e:
        logger.error(f"   ✗ Error vinculando: {e}")

# Resumen
logger.info("\n" + "="*70)
logger.info("# RESUMEN")
logger.info("="*70)
logger.info(f"Empleados procesados: {len(employees)}")
logger.info(f"Usuarios vinculados:  {linked}")
logger.info(f"Usuarios no encontrados: {not_found}")
logger.info("="*70)
logger.info("\n✓ Proceso completado")
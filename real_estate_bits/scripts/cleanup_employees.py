#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Limpieza de Empleados
================================
Elimina empleados creados recientemente para re-migrar

Versión: 1.0.0
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

logger.info("\nConectando a DESTINO...")
common = xmlrpc.client.ServerProxy(f"{DESTINATION['url']}/xmlrpc/2/common")
models = xmlrpc.client.ServerProxy(f"{DESTINATION['url']}/xmlrpc/2/object")
uid = common.authenticate(DESTINATION['db'], DESTINATION['username'], DESTINATION['password'], {})

logger.info(f"OK - Conectado (UID: {uid})")

# Buscar empleados inactivos creados recientemente (IDs > 27)
logger.info("\nBuscando empleados a eliminar (ID >= 28)...")
emp_ids = models.execute_kw(
    DESTINATION['db'], uid, DESTINATION['password'],
    'hr.employee', 'search',
    [[('id', '>=', 28)]]
)

logger.info(f"Encontrados {len(emp_ids)} empleados: {emp_ids}")

if emp_ids:
    # Buscar usuarios asociados a estos empleados
    logger.info("\nBuscando usuarios asociados...")
    user_ids = models.execute_kw(
        DESTINATION['db'], uid, DESTINATION['password'],
        'res.users', 'search',
        [[('id', 'in', emp_ids)]]
    )

    logger.info(f"Encontrados {len(user_ids)} usuarios asociados")

    # Eliminar usuarios primero
    if user_ids:
        logger.info(f"\nEliminando {len(user_ids)} usuarios...")
        try:
            models.execute_kw(
                DESTINATION['db'], uid, DESTINATION['password'],
                'res.users', 'unlink',
                [user_ids]
            )
            logger.info("✓ Usuarios eliminados")
        except Exception as e:
            logger.warning(f"No se pudieron eliminar usuarios: {e}")

    # Eliminar empleados
    logger.info(f"\nEliminando {len(emp_ids)} empleados...")
    try:
        models.execute_kw(
            DESTINATION['db'], uid, DESTINATION['password'],
            'hr.employee', 'unlink',
            [emp_ids]
        )
        logger.info("✓ Empleados eliminados")
    except Exception as e:
        logger.error(f"Error eliminando empleados: {e}")
else:
    logger.info("\nNo hay empleados para eliminar")

logger.info("\n✓ Proceso completado")
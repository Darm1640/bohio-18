#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para BORRAR todos los contratos antes de importar

IMPORTANTE: Este script eliminará TODOS los contratos de la base de datos
"""

import xmlrpc.client
import ssl
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

DESTINATION = {
    'url': 'https://darm1640-bohio-18.odoo.com',
    'db': 'darm1640-bohio-18-main-24081960',
    'username': 'admin',
    'password': 'admin'
}


def main():
    logger.info("\n" + "#"*70)
    logger.info("# ELIMINACIÓN DE CONTRATOS")
    logger.info("# ADVERTENCIA: Se eliminarán TODOS los contratos")
    logger.info("#"*70 + "\n")

    # Conectar
    context = ssl._create_unverified_context()
    common = xmlrpc.client.ServerProxy(
        f'{DESTINATION["url"]}/xmlrpc/2/common',
        context=context
    )
    models = xmlrpc.client.ServerProxy(
        f'{DESTINATION["url"]}/xmlrpc/2/object',
        context=context
    )

    logger.info(f"Conectando a: {DESTINATION['url']}")
    uid = common.authenticate(
        DESTINATION['db'],
        DESTINATION['username'],
        DESTINATION['password'],
        {}
    )
    logger.info(f"OK - Conectado (UID: {uid})\n")

    # Buscar TODOS los contratos
    logger.info("Buscando contratos...")
    contract_ids = models.execute_kw(
        DESTINATION['db'], uid, DESTINATION['password'],
        'property.contract', 'search',
        [[]]
    )

    total = len(contract_ids)
    logger.info(f"Encontrados: {total} contratos\n")

    if not contract_ids:
        logger.info("No hay contratos para eliminar")
        return

    # Primero eliminar loan_lines (cuotas) manualmente
    logger.info("Eliminando cuotas de pago (loan_lines)...")
    loan_line_ids = models.execute_kw(
        DESTINATION['db'], uid, DESTINATION['password'],
        'loan.line', 'search',
        [[('contract_id', 'in', contract_ids)]]
    )

    if loan_line_ids:
        logger.info(f"  Encontradas {len(loan_line_ids)} cuotas")
        # Borrar en lotes de 100
        batch_size = 100
        for i in range(0, len(loan_line_ids), batch_size):
            batch = loan_line_ids[i:i+batch_size]
            models.execute_kw(
                DESTINATION['db'], uid, DESTINATION['password'],
                'loan.line', 'unlink',
                [batch]
            )
            logger.info(f"  Eliminadas {min(i+batch_size, len(loan_line_ids))}/{len(loan_line_ids)} cuotas")
        logger.info("  OK - Cuotas eliminadas\n")

    # Ahora poner contratos en borrador y eliminar
    logger.info("Poniendo contratos en estado borrador...")
    models.execute_kw(
        DESTINATION['db'], uid, DESTINATION['password'],
        'property.contract', 'write',
        [contract_ids, {'state': 'draft'}]
    )
    logger.info("OK\n")

    # Eliminar contratos en lotes
    logger.info("Eliminando contratos...")
    batch_size = 50
    deleted = 0
    errors = 0

    for i in range(0, total, batch_size):
        batch = contract_ids[i:i+batch_size]
        try:
            models.execute_kw(
                DESTINATION['db'], uid, DESTINATION['password'],
                'property.contract', 'unlink',
                [batch]
            )
            deleted += len(batch)
            logger.info(f"  Eliminados {deleted}/{total} contratos")
        except Exception as e:
            logger.error(f"  Error eliminando lote {i}-{i+len(batch)}: {e}")
            # Intentar uno por uno
            for contract_id in batch:
                try:
                    models.execute_kw(
                        DESTINATION['db'], uid, DESTINATION['password'],
                        'property.contract', 'unlink',
                        [[contract_id]]
                    )
                    deleted += 1
                except Exception as e2:
                    logger.error(f"  Error eliminando contrato ID {contract_id}: {e2}")
                    errors += 1

    logger.info(f"\n{'='*70}")
    logger.info(f"RESUMEN")
    logger.info(f"{'='*70}")
    logger.info(f"Total:      {total}")
    logger.info(f"Eliminados: {deleted}")
    logger.info(f"Errores:    {errors}")
    logger.info(f"{'='*70}\n")


if __name__ == '__main__':
    main()
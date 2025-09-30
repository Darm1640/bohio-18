#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Migración: contract_scenery.contract_scenery
======================================================
Copia escenarios de contrato entre bases incluyendo:
- Cuentas contables
- Impuestos (inquilinos y propietarios)
- Validación de cuentas en líneas

Versión: 1.0.0
"""

import xmlrpc.client
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

# =================== CONFIGURACIÓN ===================

SOURCE = {
    'url': 'https://inmobiliariabohio.cloudpepper.site',
    'db': 'inmobiliariabohio.cloudpepper.site',
    'username': 'admin',
    'password': 'admin'
}

DESTINATION = {
    'url': 'https://darm1640-bohio-18.odoo.com',
    'db': 'darm1640-bohio-18-main-24081960',
    'username': 'admin',
    'password': 'admin'
}


# =================== CLASE DE CONEXIÓN ===================

class OdooAPI:
    def __init__(self, url, db, username, password):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self.models = None

    def connect(self):
        common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self.uid = common.authenticate(self.db, self.username, self.password, {})
        self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
        return self.uid

    def execute(self, model, method, args, kwargs=None):
        kwargs = kwargs or {}
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, method, args, kwargs
        )

    def search(self, model, domain, limit=None):
        args = [domain]
        kwargs = {'limit': limit} if limit else {}
        return self.execute(model, 'search', args, kwargs)

    def read(self, model, ids, fields=None):
        args = [ids]
        kwargs = {'fields': fields} if fields else {}
        return self.execute(model, 'read', args, kwargs)

    def create(self, model, vals):
        return self.execute(model, 'create', [vals])

    def write(self, model, ids, vals):
        return self.execute(model, 'write', [ids, vals])


# =================== CLASE PRINCIPAL ===================

class ContractSceneryMigration:
    def __init__(self):
        self.src = OdooAPI(**SOURCE)
        self.dst = OdooAPI(**DESTINATION)

        # Cache para evitar búsquedas repetidas
        self.cache = {
            'accounts': {},  # code -> id
            'taxes': {},     # name -> id
        }

        self.company_id = None

    def connect(self):
        logger.info(f"\nConectando a ORIGEN: {SOURCE['url']} - DB: {SOURCE['db']}")
        self.src.connect()
        logger.info(f"OK - Conectado (UID: {self.src.uid})")

        logger.info(f"\nConectando a DESTINO: {DESTINATION['url']} - DB: {DESTINATION['db']}")
        self.dst.connect()
        logger.info(f"OK - Conectado (UID: {self.dst.uid})")

        # Obtener company_id del destino
        company_ids = self.dst.search('res.company', [('name', '!=', False)], 1)
        self.company_id = company_ids[0] if company_ids else 1
        logger.info(f"\nUsando company_id: {self.company_id}")

    def get_or_create_account(self, code, name, account_type):
        """Busca o crea cuenta contable por código"""
        if code in self.cache['accounts']:
            return self.cache['accounts'][code]

        # Buscar por código
        account_ids = self.dst.search('account.account', [('code', '=', code)], 1)

        if account_ids:
            self.cache['accounts'][code] = account_ids[0]
            logger.info(f"   ✓ Cuenta encontrada: {code} - {name}")
            return account_ids[0]

        # Crear cuenta si no existe
        try:
            vals = {
                'code': code,
                'name': name,
                'account_type': account_type,
                'bohio': True,
            }
            account_id = self.dst.create('account.account', vals)
            self.cache['accounts'][code] = account_id
            logger.info(f"   + Cuenta CREADA: {code} - {name} -> ID {account_id}")
            return account_id
        except Exception as e:
            logger.error(f"   ✗ Error creando cuenta {code}: {e}")
            return None

    def get_or_create_tax(self, name, amount, type_tax_use, is_bohio=True):
        """Busca o crea impuesto por nombre"""
        key = f"{name}_{type_tax_use}"
        if key in self.cache['taxes']:
            return self.cache['taxes'][key]

        # Buscar por nombre y tipo
        tax_ids = self.dst.search('account.tax', [
            ('name', '=', name),
            ('type_tax_use', '=', type_tax_use),
            ('company_id', '=', self.company_id)
        ], 1)

        if tax_ids:
            # Actualizar campo bohio
            self.dst.write('account.tax', tax_ids[0], {'bohio': is_bohio})
            self.cache['taxes'][key] = tax_ids[0]
            logger.info(f"   ✓ Impuesto encontrado: {name} ({type_tax_use})")
            return tax_ids[0]

        # Crear impuesto si no existe
        try:
            vals = {
                'name': name,
                'amount': amount,
                'amount_type': 'percent',
                'type_tax_use': type_tax_use,
                'company_id': self.company_id,
                'bohio': is_bohio,
            }
            tax_id = self.dst.create('account.tax', vals)
            self.cache['taxes'][key] = tax_id
            logger.info(f"   + Impuesto CREADO: {name} ({type_tax_use}) -> ID {tax_id}")
            return tax_id
        except Exception as e:
            logger.error(f"   ✗ Error creando impuesto {name}: {e}")
            return None

    def copy_scenery(self, scenery):
        """Copia un escenario de contrato"""
        try:
            code = scenery.get('code')
            name = scenery.get('name')

            logger.info(f"\n{'='*70}")
            logger.info(f"Escenario: {name} (Código: {code})")

            # Verificar si ya existe
            existing = self.dst.search('contract_scenery.contract_scenery', [
                ('code', '=', code),
                ('company_id', '=', self.company_id)
            ], 1)

            if existing:
                logger.info(f"   ⚠ Ya existe, actualizando...")
                scenery_id = existing[0]
                action = 'update'
            else:
                action = 'create'

            # === PROCESAR CUENTAS ===
            logger.info("\n   Procesando cuentas contables...")

            # Cuentas de Inquilino
            income_inq_id = None
            if scenery.get('income_account_inq'):
                src_account = self.src.read('account.account', [scenery['income_account_inq'][0]], ['code', 'name', 'account_type'])
                if src_account:
                    acc = src_account[0]
                    income_inq_id = self.get_or_create_account(acc['code'], acc['name'], acc.get('account_type', 'income'))

            receivable_inq_id = None
            if scenery.get('account_receivable_inq'):
                src_account = self.src.read('account.account', [scenery['account_receivable_inq'][0]], ['code', 'name', 'account_type'])
                if src_account:
                    acc = src_account[0]
                    receivable_inq_id = self.get_or_create_account(acc['code'], acc['name'], acc.get('account_type', 'asset_receivable'))

            # Cuentas de Propietario
            income_own_id = None
            if scenery.get('income_account_own'):
                src_account = self.src.read('account.account', [scenery['income_account_own'][0]], ['code', 'name', 'account_type'])
                if src_account:
                    acc = src_account[0]
                    income_own_id = self.get_or_create_account(acc['code'], acc['name'], acc.get('account_type', 'income'))

            receivable_own_id = None
            if scenery.get('account_receivable_own'):
                src_account = self.src.read('account.account', [scenery['account_receivable_own'][0]], ['code', 'name', 'account_type'])
                if src_account:
                    acc = src_account[0]
                    receivable_own_id = self.get_or_create_account(acc['code'], acc['name'], acc.get('account_type', 'asset_receivable'))

            # Cuenta de Banco
            payment_own_id = None
            if scenery.get('account_payment_own'):
                src_account = self.src.read('account.account', [scenery['account_payment_own'][0]], ['code', 'name', 'account_type'])
                if src_account:
                    acc = src_account[0]
                    payment_own_id = self.get_or_create_account(acc['code'], acc['name'], acc.get('account_type', 'asset_cash'))

            # === PROCESAR IMPUESTOS ===
            logger.info("\n   Procesando impuestos...")

            # Impuestos Inquilinos
            inq_tax_ids = []
            if scenery.get('inq_tax_ids'):
                src_taxes = self.src.read('account.tax', scenery['inq_tax_ids'], ['name', 'amount', 'type_tax_use'])
                for tax in src_taxes:
                    tax_id = self.get_or_create_tax(tax['name'], tax['amount'], tax['type_tax_use'], is_bohio=True)
                    if tax_id:
                        inq_tax_ids.append(tax_id)

            # Impuestos Propietarios
            prop_tax_ids = []
            if scenery.get('prop_tax_ids'):
                src_taxes = self.src.read('account.tax', scenery['prop_tax_ids'], ['name', 'amount', 'type_tax_use'])
                for tax in src_taxes:
                    tax_id = self.get_or_create_tax(tax['name'], tax['amount'], tax['type_tax_use'], is_bohio=False)
                    if tax_id:
                        prop_tax_ids.append(tax_id)

            # === CONSTRUIR VALORES ===
            vals = {
                'code': code,
                'name': name,
                'company_id': self.company_id,
            }

            if scenery.get('description'):
                vals['description'] = scenery['description']

            if scenery.get('credit_limit'):
                vals['credit_limit'] = scenery['credit_limit']

            # Asignar cuentas
            if income_inq_id:
                vals['income_account_inq'] = income_inq_id
            if receivable_inq_id:
                vals['account_receivable_inq'] = receivable_inq_id
            if income_own_id:
                vals['income_account_own'] = income_own_id
            if receivable_own_id:
                vals['account_receivable_own'] = receivable_own_id
            if payment_own_id:
                vals['account_payment_own'] = payment_own_id

            # Asignar impuestos (formato Many2many: [(6, 0, [ids])])
            if inq_tax_ids:
                vals['inq_tax_ids'] = [(6, 0, inq_tax_ids)]
            if prop_tax_ids:
                vals['prop_tax_ids'] = [(6, 0, prop_tax_ids)]

            # Crear o actualizar
            if action == 'create':
                scenery_id = self.dst.create('contract_scenery.contract_scenery', vals)
                logger.info(f"\n   ✓ Escenario CREADO -> ID {scenery_id}")
            else:
                self.dst.write('contract_scenery.contract_scenery', scenery_id, vals)
                logger.info(f"\n   ✓ Escenario ACTUALIZADO -> ID {scenery_id}")

            # Resumen
            logger.info(f"\n   Resumen:")
            logger.info(f"     - Cuentas: {len([x for x in [income_inq_id, receivable_inq_id, income_own_id, receivable_own_id, payment_own_id] if x])} configuradas")
            logger.info(f"     - Impuestos Inquilinos: {len(inq_tax_ids)}")
            logger.info(f"     - Impuestos Propietarios: {len(prop_tax_ids)}")

            return scenery_id

        except Exception as e:
            logger.error(f"\n   ✗ ERROR: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def run(self):
        logger.info("\n" + "="*70)
        logger.info("# MIGRACIÓN: contract_scenery.contract_scenery")
        logger.info("="*70)

        # Obtener escenarios del origen
        logger.info("\nBuscando escenarios en origen...")
        scenery_ids = self.src.search('contract_scenery.contract_scenery', [])
        logger.info(f"Encontrados {len(scenery_ids)} escenarios")

        if not scenery_ids:
            logger.info("No hay escenarios para migrar")
            return

        # Leer todos los escenarios
        sceneries = self.src.read('contract_scenery.contract_scenery', scenery_ids)

        # Copiar cada escenario
        success = 0
        failed = 0

        for i, scenery in enumerate(sceneries, 1):
            logger.info(f"\n[{i}/{len(sceneries)}]")
            result = self.copy_scenery(scenery)
            if result:
                success += 1
            else:
                failed += 1

        # Resumen final
        logger.info("\n" + "="*70)
        logger.info("# RESUMEN FINAL")
        logger.info("="*70)
        logger.info(f"Total: {len(sceneries)}")
        logger.info(f"Exitosos: {success}")
        logger.info(f"Fallidos: {failed}")
        logger.info(f"Cuentas en cache: {len(self.cache['accounts'])}")
        logger.info(f"Impuestos en cache: {len(self.cache['taxes'])}")


# =================== MAIN ===================

if __name__ == '__main__':
    migration = ContractSceneryMigration()
    migration.connect()
    migration.run()
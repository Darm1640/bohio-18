#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para importar contratos desde Excel a Odoo 18

ANÁLISIS DEL EXCEL:
- Consecutivo: Número de contrato
- Propiedad: Código y dirección de propiedad (ej: "180 - CR 9 B W # 24 - 55 BRR EL DORADO")
- Propietario de Propiedad: [ID] NIT - NOMBRE
- Inquilino: [ID] NIT - NOMBRE
- Valor Canon: $1,910,938.00
- Canon Total: 1910938
- % Comisión: 9 %
- Periodicidad: Mensual
- Escenario: Texto del escenario
- Estado: Activo/Inactivo
- Fecha Inicio: 2013-01-17
- Fecha Fin: 2025-12-16
- Uso: Comercial/Residencial
"""

import xmlrpc.client
import ssl
import pandas as pd
import re
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# CONFIGURACIÓN
EXCEL_FILE = r'C:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\bohio_real_estate\Contratos (4).xlsx'

DESTINATION = {
    'url': 'https://darm1640-bohio-18.odoo.com',
    'db': 'darm1640-bohio-18-main-24081960',
    'username': 'admin',
    'password': 'admin'
}

DRY_RUN = False  # True = solo simular, False = crear contratos

# FECHA DE CORTE PARA MIGRACIÓN
# Solo las cuotas POSTERIORES a esta fecha quedarán pendientes
# Las cuotas anteriores se marcarán como PAGADAS
CUTOFF_DATE = '2025-09-30'  # Formato: YYYY-MM-DD

# Mapeo de escenarios del Excel a IDs de Odoo
ESCENARIO_MAPPING = {
    # El script detectará automáticamente los escenarios disponibles
}


class OdooConnection:
    def __init__(self, config):
        self.url = config['url']
        self.db = config['db']
        self.username = config['username']
        self.password = config['password']

        # Deshabilitar verificación SSL
        context = ssl._create_unverified_context()

        self.common = xmlrpc.client.ServerProxy(
            f'{self.url}/xmlrpc/2/common',
            context=context,
            allow_none=True
        )
        self.models = xmlrpc.client.ServerProxy(
            f'{self.url}/xmlrpc/2/object',
            context=context,
            allow_none=True
        )
        self.uid = None

    def connect(self):
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})
        return self.uid

    def search(self, model, domain, limit=None):
        kwargs = {'limit': limit} if limit else {}
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, 'search', [domain], kwargs
        )

    def read(self, model, ids, fields):
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, 'read', [ids], {'fields': fields}
        )

    def search_read(self, model, domain, fields, limit=None):
        kwargs = {'fields': fields}
        if limit:
            kwargs['limit'] = limit
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, 'search_read', [domain], kwargs
        )

    def create(self, model, vals):
        result = self.models.execute_kw(
            self.db, self.uid, self.password,
            model, 'create', [[vals]]
        )
        return result[0] if isinstance(result, list) else result


class ContractImporter:
    def __init__(self, odoo_conn):
        self.odoo = odoo_conn
        self.cache = {
            'partners': {},
            'properties': {},
            'sceneries': {},
            'users': {}
        }
        self.company_id = 1
        self.stats = {
            'total': 0,
            'created': 0,
            'skipped': 0,
            'errors': []
        }

    def load_cache(self):
        """Cargar datos en cache para búsquedas rápidas"""
        logger.info("\n=== CARGANDO CACHE ===")

        # Cargar escenarios
        sceneries = self.odoo.search_read(
            'contract_scenery.contract_scenery',
            [],
            ['id', 'name']
        )
        logger.info(f"Escenarios encontrados: {len(sceneries)}")
        for sc in sceneries:
            self.cache['sceneries'][sc['name'].lower().strip()] = sc['id']
            logger.info(f"  - {sc['name']} (ID: {sc['id']})")

        # Cargar propiedades
        properties = self.odoo.search_read(
            'product.template',
            [('is_property', '=', True)],
            ['id', 'name', 'default_code', 'street']
        )
        logger.info(f"\nPropiedades encontradas: {len(properties)}")
        for prop in properties:
            # Indexar por código
            if prop.get('default_code'):
                code = prop['default_code'].strip()
                self.cache['properties'][code] = prop['id']
            # Indexar por dirección
            if prop.get('street'):
                address = prop['street'].upper().strip()
                self.cache['properties'][address] = prop['id']

    def parse_partner_data(self, text):
        """
        Extraer datos del partner desde texto
        Formato: "[ID] NIT - NOMBRE"
        Ejemplo: "[1] 70160738 - ALFONSO GARCES ZULUAGA"
        """
        if not text or pd.isna(text):
            return None

        text = str(text).strip()

        # Patrón: [ID] NIT - NOMBRE
        match = re.match(r'\[(\d+)\]\s+(\S+)\s*-\s*(.+)', text)
        if match:
            return {
                'old_id': match.group(1),
                'vat': match.group(2),
                'name': match.group(3).strip()
            }
        return None

    def parse_property_code(self, text):
        """
        Extraer código de propiedad desde texto
        Formato: "CODIGO - DIRECCION"
        Ejemplo: "180 - CR 9 B W # 24 - 55 BRR EL DORADO"
        """
        if not text or pd.isna(text):
            return None, None

        text = str(text).strip()

        # Buscar patrón: NUMERO - DIRECCION
        match = re.match(r'^(\d+)\s*-\s*(.+)$', text)
        if match:
            return match.group(1).strip(), match.group(2).strip().upper()

        return None, text.upper()

    def get_or_create_partner(self, partner_data):
        """Buscar o crear partner"""
        if not partner_data:
            return None

        vat = partner_data['vat']

        # Buscar en cache
        if vat in self.cache['partners']:
            return self.cache['partners'][vat]

        # Buscar en Odoo por VAT
        partner_ids = self.odoo.search(
            'res.partner',
            [('vat', '=', vat)],
            1
        )

        if partner_ids:
            partner_id = partner_ids[0] if isinstance(partner_ids, list) else partner_ids
            self.cache['partners'][vat] = partner_id
            logger.info(f"   + Partner encontrado: {partner_data['name']} ({vat}) -> ID {partner_id}")
            return partner_id

        # Crear nuevo partner
        if DRY_RUN:
            logger.info(f"   [DRY RUN] Crear partner: {partner_data['name']} ({vat})")
            return 999

        vals = {
            'name': partner_data['name'],
            'vat': vat,
            'company_id': self.company_id,
            'customer_rank': 1
        }

        partner_id = self.odoo.create('res.partner', vals)
        self.cache['partners'][vat] = partner_id
        logger.info(f"   + Partner CREADO: {partner_data['name']} ({vat}) -> ID {partner_id}")
        return partner_id

    def find_property(self, code, address):
        """Buscar propiedad por código o dirección"""
        # Buscar por código exacto
        if code and code in self.cache['properties']:
            return self.cache['properties'][code]

        # Buscar por dirección exacta
        if address and address in self.cache['properties']:
            return self.cache['properties'][address]

        # Buscar directo en Odoo por código
        if code:
            prop_ids = self.odoo.search(
                'product.template',
                [('default_code', '=', code), ('is_property', '=', True)],
                1
            )
            if prop_ids:
                prop_id = prop_ids[0] if isinstance(prop_ids, list) else prop_ids
                self.cache['properties'][code] = prop_id
                return prop_id

        # Buscar por dirección con ILIKE (búsqueda flexible)
        if address:
            # Tomar primeras palabras significativas de la dirección
            address_words = address.split()[:4]  # Primeras 4 palabras
            search_term = ' '.join(address_words)

            prop_ids = self.odoo.search(
                'product.template',
                [('street', 'ilike', search_term), ('is_property', '=', True)],
                1
            )
            if prop_ids:
                prop_id = prop_ids[0] if isinstance(prop_ids, list) else prop_ids
                logger.info(f"   + Propiedad encontrada por dirección: {search_term} -> ID {prop_id}")
                self.cache['properties'][address] = prop_id
                return prop_id

        return None

    def find_scenery(self, text):
        """Buscar escenario por similitud de texto"""
        if not text or pd.isna(text):
            return None

        text = str(text).lower().strip()

        # Buscar match exacto
        if text in self.cache['sceneries']:
            return self.cache['sceneries'][text]

        # Buscar por palabras clave
        for key, scenery_id in self.cache['sceneries'].items():
            # Verificar si el escenario contiene palabras clave del texto
            if any(word in text for word in key.split() if len(word) > 3):
                logger.info(f"   + Escenario por similitud: '{text}' -> '{key}' (ID {scenery_id})")
                return scenery_id

        logger.warning(f"   ! Escenario no encontrado: {text[:50]}...")
        return None

    def parse_amount(self, text):
        """Convertir texto de monto a float"""
        if pd.isna(text):
            return 0.0

        if isinstance(text, (int, float)):
            return float(text)

        # Remover símbolos y convertir
        text = str(text).replace('$', '').replace(',', '').replace('.', '').strip()
        try:
            return float(text)
        except:
            return 0.0

    def parse_date(self, date_val):
        """Convertir fecha a formato Odoo"""
        if pd.isna(date_val):
            return False

        # Si ya es datetime
        if isinstance(date_val, pd.Timestamp):
            return date_val.strftime('%Y-%m-%d')

        # Si es string, intentar parsear
        if isinstance(date_val, str):
            try:
                dt = pd.to_datetime(date_val)
                return dt.strftime('%Y-%m-%d')
            except:
                return False

        return False

    def parse_commission(self, text):
        """Extraer porcentaje de comisión"""
        if pd.isna(text):
            return 0.0

        text = str(text).replace('%', '').strip()
        try:
            return float(text)
        except:
            return 0.0

    def import_contract(self, row):
        """Importar un contrato desde una fila del Excel"""
        try:
            consecutivo = row['Consecutivo']
            logger.info(f"\n{'='*70}")
            logger.info(f"Contrato #{consecutivo}")

            # Verificar si ya existe
            existing = self.odoo.search(
                'property.contract',
                [('name', '=', str(consecutivo))],
                1
            )
            if existing:
                logger.info(f"   ! Contrato YA EXISTE: {consecutivo}")
                self.stats['skipped'] += 1
                return True

            # Parsear datos
            prop_code, prop_address = self.parse_property_code(row['Propiedad'])
            owner_data = self.parse_partner_data(row['Propietario de Propiedad'])
            tenant_data = self.parse_partner_data(row['Inquilino'])

            logger.info(f"  Propiedad: {prop_code} - {prop_address}")
            logger.info(f"  Propietario: {owner_data['name'] if owner_data else 'N/A'}")
            logger.info(f"  Inquilino: {tenant_data['name'] if tenant_data else 'N/A'}")

            # Buscar/crear entidades
            property_id = self.find_property(prop_code, prop_address)
            if not property_id:
                logger.warning(f"   ! Propiedad NO ENCONTRADA: {prop_code} - {prop_address}")
                self.stats['errors'].append(f"Contrato {consecutivo}: Propiedad no encontrada")
                return False

            tenant_id = self.get_or_create_partner(tenant_data)
            if not tenant_id:
                logger.warning(f"   ! Inquilino requerido")
                self.stats['errors'].append(f"Contrato {consecutivo}: Inquilino no encontrado")
                return False

            scenery_id = self.find_scenery(row['Escenario'])
            if not scenery_id:
                logger.warning(f"   ! Escenario requerido")
                self.stats['errors'].append(f"Contrato {consecutivo}: Escenario no encontrado")
                return False

            # Construir valores del contrato
            vals = {
                'name': str(consecutivo),
                'partner_id': tenant_id,
                'property_id': property_id,
                'contract_scenery_id': scenery_id,
                'date_from': self.parse_date(row['Fecha Inicio']),
                'date_to': self.parse_date(row['Fecha Fin']),
                'rental_fee': self.parse_amount(row['Canon Total']),
                'periodicity': '1',  # Mensual por defecto
                'company_id': self.company_id,
                'insurance_fee': 0,
                'state': 'draft'  # Siempre crear como borrador primero
            }

            is_active = row['Estado'] == 'Activo'

            # Fecha de terminación real
            date_end = self.parse_date(row.get('Fecha de Terminación'))
            if date_end:
                vals['date_end'] = date_end

            logger.info(f"  Canon: ${vals['rental_fee']:,.0f}")
            logger.info(f"  Período: {vals['date_from']} a {vals['date_to']}")
            logger.info(f"  Estado Excel: {'Activo' if is_active else 'Inactivo'}")

            if DRY_RUN:
                logger.info(f"  [DRY RUN] Contrato NO CREADO - Solo simulación")
                self.stats['created'] += 1
                return True

            # Crear contrato
            contract_id = self.odoo.create('property.contract', vals)
            logger.info(f"  ✓ Contrato CREADO: ID {contract_id}")

            # Generar líneas de pago
            try:
                self.odoo.models.execute_kw(
                    self.odoo.db, self.odoo.uid, self.odoo.password,
                    'property.contract', 'prepare_lines',
                    [[contract_id]]
                )
                logger.info(f"  ✓ Líneas de pago GENERADAS")

                # Marcar como pagadas las líneas anteriores a la fecha de corte
                loan_lines = self.odoo.search_read(
                    'loan.line',
                    [('contract_id', '=', contract_id), ('date', '<', CUTOFF_DATE)],
                    ['id', 'date']
                )

                if loan_lines:
                    line_ids = [line['id'] for line in loan_lines]
                    self.odoo.models.execute_kw(
                        self.odoo.db, self.odoo.uid, self.odoo.password,
                        'loan.line', 'write',
                        [line_ids, {'payment_state': 'paid'}]
                    )
                    logger.info(f"  ✓ {len(line_ids)} cuotas anteriores marcadas como PAGADAS")

                # Contar cuotas pendientes
                pending_lines = self.odoo.search(
                    'loan.line',
                    [('contract_id', '=', contract_id), ('date', '>=', CUTOFF_DATE)]
                )
                logger.info(f"  ✓ {len(pending_lines) if pending_lines else 0} cuotas PENDIENTES desde {CUTOFF_DATE}")

                # Confirmar contrato si está activo
                if is_active:
                    self.odoo.models.execute_kw(
                        self.odoo.db, self.odoo.uid, self.odoo.password,
                        'property.contract', 'action_confirm',
                        [[contract_id]]
                    )
                    logger.info(f"  ✓ Contrato CONFIRMADO")

            except Exception as e:
                logger.warning(f"  ! Error al procesar líneas: {e}")
                import traceback
                logger.warning(traceback.format_exc())

            self.stats['created'] += 1
            return True

        except Exception as e:
            logger.error(f"  ✗ ERROR: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.stats['errors'].append(f"Contrato {row.get('Consecutivo', '?')}: {str(e)}")
            return False

    def import_all(self, df):
        """Importar todos los contratos"""
        self.stats['total'] = len(df)

        logger.info(f"\n{'#'*70}")
        if DRY_RUN:
            logger.info(f"# MODO PRUEBA (DRY RUN) - Solo simulación")
        else:
            logger.info(f"# IMPORTACIÓN DE CONTRATOS")
        logger.info(f"{'#'*70}")
        logger.info(f"Total contratos a importar: {self.stats['total']}\n")

        for idx, row in df.iterrows():
            logger.info(f"\n[{idx + 1}/{self.stats['total']}]")
            self.import_contract(row)

        # Resumen final
        logger.info(f"\n{'='*70}")
        logger.info(f"RESUMEN FINAL")
        logger.info(f"{'='*70}")
        logger.info(f"Total:    {self.stats['total']}")
        logger.info(f"Creados:  {self.stats['created']}")
        logger.info(f"Omitidos: {self.stats['skipped']}")
        logger.info(f"Errores:  {len(self.stats['errors'])}")

        if self.stats['errors']:
            logger.info(f"\nERRORES:")
            for err in self.stats['errors'][:10]:  # Mostrar primeros 10
                logger.info(f"  - {err}")
            if len(self.stats['errors']) > 10:
                logger.info(f"  ... y {len(self.stats['errors']) - 10} errores más")

        logger.info(f"{'='*70}\n")


def main():
    logger.info("\n" + "#"*70)
    logger.info("# IMPORTACIÓN DE CONTRATOS DESDE EXCEL")
    logger.info("# Excel -> Odoo 18")
    logger.info("#"*70 + "\n")

    # Leer Excel
    logger.info(f"Leyendo archivo: {EXCEL_FILE}")
    df = pd.read_excel(EXCEL_FILE)
    logger.info(f"OK - {len(df)} contratos encontrados\n")

    # Conectar a Odoo
    logger.info(f"Conectando a Odoo: {DESTINATION['url']}")
    odoo = OdooConnection(DESTINATION)
    uid = odoo.connect()
    if not uid:
        logger.error("ERROR: No se pudo conectar a Odoo")
        return
    logger.info(f"OK - Conectado (UID: {uid})\n")

    # Importar contratos
    importer = ContractImporter(odoo)
    importer.load_cache()
    importer.import_all(df)


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Simplificado de Carga de Propiedades - XML-RPC
=====================================================
Carga propiedades mediante XML-RPC a Odoo 18

Autor: Claude Code
Fecha: 2025-09-30
Versión: 2.0.0 - CORREGIDO
"""

import xmlrpc.client
import json
import logging
from datetime import date
from typing import Dict, List, Optional

# =================== CONFIGURACIÓN ===================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de conexión
MODE = 'cloud'  # 'local' o 'cloud'

CONNECTIONS = {
    'local': {
        'url': 'http://localhost:8069',
        'db': 'david_test',
        'username': 'admin',
        'password': 'admin'
    },
    'cloud': {
        'url': 'https://darm1640-bohio-18.odoo.com',
        'db': 'darm1640-bohio-18-main-24081960',
        'username': 'admin',
        'password': 'admin'
    }
}

CONFIG = CONNECTIONS[MODE]


class OdooLoader:
    """Cargador XML-RPC para Odoo"""

    def __init__(self, url, db, username, password):
        logger.info(f"🔌 Conectando a Odoo...")
        logger.info(f"   URL: {url}")
        logger.info(f"   BD:  {db}")

        self.url = url
        self.db = db
        self.username = username
        self.password = password

        # Conexiones XML-RPC
        self.common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

        # Autenticar
        try:
            self.uid = self.common.authenticate(db, username, password, {})
            if not self.uid:
                raise Exception("Autenticación fallida")
            logger.info(f"✅ Conectado exitosamente (UID: {self.uid})")
        except Exception as e:
            logger.error(f"❌ Error de conexión: {e}")
            raise

        # Cachear registros base
        self._cache_base_records()

    def _cache_base_records(self):
        """Cachea registros base"""
        logger.info("📦 Cacheando registros base...")

        # País Colombia
        ids = self.models.execute_kw(
            self.db, self.uid, self.password,
            'res.country', 'search',
            [[('code', '=', 'CO')]], {'limit': 1}
        )
        self.country_co_id = ids[0] if ids else None
        logger.info(f"   ✓ País CO: {self.country_co_id}")

        # Compañía
        ids = self.models.execute_kw(
            self.db, self.uid, self.password,
            'res.company', 'search',
            [[('id', '=', 1)]], {'limit': 1}
        )
        self.company_id = ids[0] if ids else 1
        logger.info(f"   ✓ Compañía: {self.company_id}")

        # Moneda COP
        ids = self.models.execute_kw(
            self.db, self.uid, self.password,
            'res.currency', 'search',
            [[('name', '=', 'COP')]], {'limit': 1}
        )
        self.currency_id = ids[0] if ids else None
        logger.info(f"   ✓ Moneda COP: {self.currency_id}")

        # Tipo documento CC
        ids = self.models.execute_kw(
            self.db, self.uid, self.password,
            'l10n_latam.identification.type', 'search',
            [[('name', '=', 'CC')]], {'limit': 1}
        )
        self.doc_type_cc = ids[0] if ids else None
        logger.info(f"   ✓ Tipo Doc CC: {self.doc_type_cc}")

    def search_one(self, model: str, domain: List) -> Optional[int]:
        """Busca un registro y retorna su ID"""
        ids = self.models.execute_kw(
            self.db, self.uid, self.password,
            model, 'search',
            [domain], {'limit': 1}
        )
        return ids[0] if ids else None

    def create_record(self, model: str, vals: Dict) -> int:
        """Crea un registro"""
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, 'create',
            [[vals]]
        )

    def get_or_create_partner(self, data: Dict) -> int:
        """Obtiene o crea un partner"""
        # Buscar por VAT
        if data.get('vat'):
            partner_id = self.search_one('res.partner', [('vat', '=', data['vat'])])
            if partner_id:
                logger.info(f"   ✓ Partner existente (VAT: {data['vat']}): ID {partner_id}")
                return partner_id

        # Buscar por nombre
        if data.get('name'):
            partner_id = self.search_one('res.partner', [('name', '=', data['name'])])
            if partner_id:
                logger.info(f"   ✓ Partner existente (Nombre: {data['name']}): ID {partner_id}")
                return partner_id

        # Crear nuevo
        vals = {
            'name': data.get('name', 'Propietario'),
            'type': 'contact',
            'customer_rank': 1,
            'country_id': self.country_co_id,
        }

        # Agregar campos opcionales
        optional_fields = ['vat', 'phone', 'email', 'is_company', 'street', 'city']
        for field in optional_fields:
            if data.get(field):
                vals[field] = data[field]

        partner_id = self.create_record('res.partner', vals)
        logger.info(f"   ✅ Partner creado: {vals['name']} (ID: {partner_id})")
        return partner_id

    def get_state_id(self, state_name: str) -> Optional[int]:
        """Obtiene ID del departamento"""
        if not state_name:
            return None
        return self.search_one('res.country.state', [
            ('name', 'ilike', state_name),
            ('country_id', '=', self.country_co_id)
        ])

    def get_city_id(self, city_name: str, state_id: Optional[int] = None) -> Optional[int]:
        """Obtiene ID de la ciudad"""
        if not city_name:
            return None
        domain = [('name', 'ilike', city_name)]
        if state_id:
            domain.append(('state_id', '=', state_id))
        return self.search_one('res.city', domain)

    def get_or_create_region(self, region_name: str, city_id: Optional[int]) -> Optional[int]:
        """Obtiene o crea una región (barrio)"""
        if not region_name or not city_id:
            return None

        # Buscar existente
        region_id = self.search_one('region.region', [
            ('name', '=', region_name),
            ('city_id', '=', city_id)
        ])

        if region_id:
            logger.info(f"   ✓ Región existente: {region_name} (ID: {region_id})")
            return region_id

        # Crear nueva
        vals = {
            'name': region_name,
            'city_id': city_id,
            'country_id': self.country_co_id,
        }

        region_id = self.create_record('region.region', vals)
        logger.info(f"   ✅ Región creada: {region_name} (ID: {region_id})")
        return region_id

    def get_or_create_property_type(self, type_name: str) -> int:
        """Obtiene o crea tipo de propiedad"""
        if not type_name:
            type_name = "Apartamento"

        # Buscar existente
        type_id = self.search_one('property.type', [('name', '=', type_name)])

        if type_id:
            logger.info(f"   ✓ Tipo existente: {type_name} (ID: {type_id})")
            return type_id

        # Crear nuevo
        vals = {
            'name': type_name,
            'property_type': 'apartment',
        }

        type_id = self.create_record('property.type', vals)
        logger.info(f"   ✅ Tipo creado: {type_name} (ID: {type_id})")
        return type_id

    def create_property(self, data: Dict) -> tuple:
        """Crea una propiedad completa"""
        try:
            logger.info(f"\n📍 Procesando: {data.get('name', 'Sin nombre')}")

            # Validar nombre
            if not data.get('name'):
                return False, 0, "Error: Nombre requerido"

            # 1. Propietario
            partner_id = None
            if data.get('partner_data'):
                partner_id = self.get_or_create_partner(data['partner_data'])

            # 2. Ubicación
            state_id = None
            if data.get('state_name'):
                state_id = self.get_state_id(data['state_name'])
                logger.info(f"   ✓ Departamento: {data['state_name']} (ID: {state_id})")

            city_id = None
            if data.get('city_name'):
                city_id = self.get_city_id(data['city_name'], state_id)
                logger.info(f"   ✓ Ciudad: {data['city_name']} (ID: {city_id})")

            region_id = None
            if data.get('region_name') and city_id:
                region_id = self.get_or_create_region(data['region_name'], city_id)

            # 3. Tipo de propiedad
            property_type_id = None
            if data.get('property_type_name'):
                property_type_id = self.get_or_create_property_type(data['property_type_name'])

            # 4. Construir valores de la propiedad
            vals = {
                # Básicos
                'name': data['name'],
                'detailed_type': 'service',
                'is_property': True,

                # Ubicación
                'partner_id': partner_id,
                'region_id': region_id,
                'state_id': state_id,
                'city_id': city_id,
                'country_id': self.country_co_id,
                'street': data.get('street'),
                'zip': data.get('zip'),

                # Tipo
                'property_type_id': property_type_id,
                'type_service': data.get('type_service', 'rent'),

                # Características
                'property_area': data.get('property_area', 0.0),
                'num_bedrooms': data.get('num_bedrooms', 0),
                'num_bathrooms': data.get('num_bathrooms', 0),
                'stratum': data.get('stratum'),

                # Precios
                'net_rental_price': data.get('net_rental_price', 0.0),
                'rent_value_from': data.get('rent_value_from', 0.0),
                'admin_value': data.get('admin_value', 0.0),

                # Sistema
                'company_id': self.company_id,
                'currency_id': self.currency_id,
            }

            # Agregar campos booleanos comunes
            bool_fields = ['garage', 'elevator', 'pools', 'gym', 'furnished',
                          'balcony', 'has_security']
            for field in bool_fields:
                if field in data:
                    vals[field] = data[field]

            # Limpiar valores None
            vals = {k: v for k, v in vals.items() if v is not None}

            # 5. Crear propiedad
            logger.info(f"   📝 Creando propiedad en Odoo...")
            property_id = self.create_record('product.template', vals)

            logger.info(f"   ✅ PROPIEDAD CREADA: ID {property_id}")
            return True, property_id, f"Propiedad creada exitosamente"

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(f"   ❌ {error_msg}")
            return False, 0, error_msg

    def bulk_create(self, properties: List[Dict]) -> Dict:
        """Carga masiva de propiedades"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 CARGA MASIVA DE {len(properties)} PROPIEDADES")
        logger.info(f"{'='*70}\n")

        stats = {
            'total': len(properties),
            'success': 0,
            'failed': 0,
            'errors': []
        }

        for idx, prop_data in enumerate(properties, 1):
            logger.info(f"\n{'─'*70}")
            logger.info(f"[{idx}/{stats['total']}]")

            success, prop_id, message = self.create_property(prop_data)

            if success:
                stats['success'] += 1
            else:
                stats['failed'] += 1
                stats['errors'].append({
                    'property': prop_data.get('name', 'Sin nombre'),
                    'error': message
                })

        # Resumen final
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 RESUMEN FINAL")
        logger.info(f"{'='*70}")
        logger.info(f"Total:    {stats['total']}")
        logger.info(f"Exitosas: {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
        logger.info(f"Fallidas: {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")
        logger.info(f"{'='*70}\n")

        if stats['errors']:
            logger.error(f"\n❌ ERRORES:")
            for error in stats['errors']:
                logger.error(f"  - {error['property']}: {error['error']}")

        return stats


# =================== FUNCIONES DE CARGA DE DATOS ===================

def load_from_json(file_path: str) -> List[Dict]:
    """Carga propiedades desde archivo JSON"""
    with open(file_path, 'r', encoding='utf-8') as f:
        properties = json.load(f)
    logger.info(f"✅ Cargadas {len(properties)} propiedades desde {file_path}")
    return properties


# =================== FUNCIÓN PRINCIPAL ===================

def main():
    """Función principal"""
    logger.info(f"\n{'#'*70}")
    logger.info(f"# SCRIPT DE CARGA DE PROPIEDADES - ODOO 18")
    logger.info(f"{'#'*70}\n")

    # Conectar a Odoo
    loader = OdooLoader(
        url=CONFIG['url'],
        db=CONFIG['db'],
        username=CONFIG['username'],
        password=CONFIG['password']
    )

    # IMPORTANTE: Cargar desde archivo JSON
    # Crear archivo properties.json con tus datos
    logger.info("\n📄 Para cargar propiedades:")
    logger.info("   1. Crea un archivo 'properties.json' en este mismo directorio")
    logger.info("   2. Usa el formato de ejemplo que se muestra abajo")
    logger.info("   3. Descomenta la línea de carga\n")

    logger.info("📝 Formato de ejemplo properties.json:")
    logger.info("""
[
    {
        "name": "Apartamento Centro",
        "state_name": "Antioquia",
        "city_name": "Medellín",
        "region_name": "El Poblado",
        "street": "Carrera 43A #5-33",
        "property_type_name": "Apartamento",
        "type_service": "rent",
        "property_area": 85.0,
        "num_bedrooms": 3,
        "num_bathrooms": 2,
        "stratum": "6",
        "net_rental_price": 2500000.0,
        "rent_value_from": 2500000.0,
        "admin_value": 350000.0,
        "garage": true,
        "elevator": true,
        "pools": true,
        "gym": true,
        "partner_data": {
            "name": "Juan Pérez",
            "vat": "1234567890",
            "phone": "+57 301 234 5678",
            "email": "juan@example.com"
        }
    }
]
    """)

    # Descomentar para cargar desde JSON:
    # properties = load_from_json('properties.json')
    # stats = loader.bulk_create(properties)

    logger.info("\n✅ Script listo para usar")
    logger.info("   Descomenta las líneas de carga y ejecuta nuevamente\n")


if __name__ == '__main__':
    main()
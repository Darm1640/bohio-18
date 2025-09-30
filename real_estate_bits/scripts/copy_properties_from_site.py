#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Copia de Propiedades - Site → Odoo 18
================================================
Copia propiedades reales desde inmobiliariabohio.cloudpepper.site
hacia darm1640-bohio-18.odoo.com

Autor: Claude Code
Fecha: 2025-09-30
Versión: 1.0.0
"""

import xmlrpc.client
import logging
from typing import Dict, List, Optional

# =================== CONFIGURACIÓN ===================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# =================== CONFIGURACIÓN DE CONEXIONES ===================

# ORIGEN: Site de producción (desde donde se copian)
SOURCE = {
    'url': 'https://inmobiliariabohio.cloudpepper.site',
    'db': 'inmobiliariabohio.cloudpepper.site',
    'username': 'admin',
    'password': 'admin'
}

# DESTINO: Odoo 18 (hacia donde se copian)
DESTINATION = {
    'url': 'https://darm1640-bohio-18.odoo.com',
    'db': 'darm1640-bohio-18-main-24081960',
    'username': 'admin',
    'password': 'admin'
}

# Límite de propiedades a copiar (empezar con pocas para probar)
LIMIT_PROPERTIES = 2

# Modo de prueba: solo muestra qué se copiaría sin crear nada
DRY_RUN = False  # Cambiar a True para solo ver


# =================== CLASE DE CONEXIÓN ODOO ===================

class OdooConnection:
    """Maneja conexión a una instancia de Odoo"""

    def __init__(self, name: str, url: str, db: str, username: str, password: str):
        self.name = name
        self.url = url
        self.db = db
        self.username = username
        self.password = password

        logger.info(f"\n{'='*70}")
        logger.info(f"🔌 Conectando a {name}")
        logger.info(f"   URL: {url}")
        logger.info(f"   DB:  {db}")
        logger.info(f"{'='*70}")

        # Conexiones XML-RPC
        self.common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

        # Autenticar
        try:
            self.uid = self.common.authenticate(db, username, password, {})
            if not self.uid:
                raise Exception(f"Autenticación fallida en {name}")
            logger.info(f"✅ Conectado a {name} (UID: {self.uid})\n")
        except Exception as e:
            logger.error(f"❌ Error conectando a {name}: {e}")
            raise

    def search(self, model: str, domain: List, limit: int = None) -> List[int]:
        """Busca registros"""
        kwargs = {}
        if limit:
            kwargs['limit'] = limit

        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, 'search',
            [domain], kwargs
        )

    def read(self, model: str, ids: List[int], fields: List[str] = None) -> List[Dict]:
        """Lee registros"""
        kwargs = {}
        if fields:
            kwargs['fields'] = fields

        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, 'read',
            [ids], kwargs
        )

    def create(self, model: str, vals: Dict) -> int:
        """Crea un registro"""
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, 'create',
            [[vals]]
        )

    def search_read(self, model: str, domain: List, fields: List[str], limit: int = None) -> List[Dict]:
        """Busca y lee en una sola llamada"""
        kwargs = {'fields': fields}
        if limit:
            kwargs['limit'] = limit

        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, 'search_read',
            [domain], kwargs
        )


# =================== CLASE COPIADORA ===================

class PropertyCopier:
    """Copia propiedades entre instancias de Odoo"""

    def __init__(self, source: OdooConnection, destination: OdooConnection):
        self.source = source
        self.dest = destination

        # Cache de IDs mapeados
        self.partner_map = {}  # {source_id: dest_id}
        self.region_map = {}
        self.property_type_map = {}
        self.state_map = {}
        self.city_map = {}

        # Inicializar registros base en destino
        self._init_destination_base_records()

    def _init_destination_base_records(self):
        """Inicializa registros base en destino"""
        logger.info("📦 Cacheando registros base en destino...")

        # País Colombia
        ids = self.dest.search('res.country', [('code', '=', 'CO')], limit=1)
        self.dest_country_id = ids[0] if ids else None
        logger.info(f"   ✓ País CO: {self.dest_country_id}")

        # Compañía
        ids = self.dest.search('res.company', [('id', '=', 1)], limit=1)
        self.dest_company_id = ids[0] if ids else 1
        logger.info(f"   ✓ Compañía: {self.dest_company_id}")

        # Moneda COP
        ids = self.dest.search('res.currency', [('name', '=', 'COP')], limit=1)
        self.dest_currency_id = ids[0] if ids else None
        logger.info(f"   ✓ Moneda COP: {self.dest_currency_id}\n")

    def get_or_create_partner(self, source_partner_id: int, source_partner_name: str) -> Optional[int]:
        """Obtiene o crea partner en destino"""
        # Si ya está mapeado, retornar
        if source_partner_id in self.partner_map:
            return self.partner_map[source_partner_id]

        # Leer partner completo del origen
        try:
            partner_data = self.source.read('res.partner', [source_partner_id], [
                'name', 'vat', 'phone', 'mobile', 'email', 'street', 'street2',
                'zip', 'city', 'is_company', 'type'
            ])

            if not partner_data:
                logger.warning(f"   ⚠ No se pudo leer partner {source_partner_id}")
                return None

            partner = partner_data[0]

            # Buscar en destino por VAT
            if partner.get('vat'):
                dest_ids = self.dest.search('res.partner', [('vat', '=', partner['vat'])], limit=1)
                if dest_ids:
                    dest_partner_id = dest_ids[0]
                    self.partner_map[source_partner_id] = dest_partner_id
                    logger.info(f"   ✓ Partner existente (VAT): {partner['name']} → ID {dest_partner_id}")
                    return dest_partner_id

            # Buscar por nombre exacto
            dest_ids = self.dest.search('res.partner', [('name', '=', partner['name'])], limit=1)
            if dest_ids:
                dest_partner_id = dest_ids[0]
                self.partner_map[source_partner_id] = dest_partner_id
                logger.info(f"   ✓ Partner existente (Nombre): {partner['name']} → ID {dest_partner_id}")
                return dest_partner_id

            # Crear nuevo partner
            vals = {
                'name': partner.get('name', 'Propietario'),
                'type': partner.get('type', 'contact'),
                'customer_rank': 1,
                'country_id': self.dest_country_id,
            }

            # Campos opcionales
            optional_fields = ['vat', 'phone', 'mobile', 'email', 'street',
                             'street2', 'zip', 'city', 'is_company']
            for field in optional_fields:
                if partner.get(field):
                    vals[field] = partner[field]

            dest_partner_id = self.dest.create('res.partner', vals)
            self.partner_map[source_partner_id] = dest_partner_id
            logger.info(f"   ✅ Partner creado: {vals['name']} → ID {dest_partner_id}")
            return dest_partner_id

        except Exception as e:
            logger.error(f"   ❌ Error procesando partner {source_partner_id}: {e}")
            return None

    def get_or_create_state(self, state_name: str) -> Optional[int]:
        """Obtiene o crea departamento en destino"""
        if not state_name:
            return None

        # Buscar en caché
        if state_name in self.state_map:
            return self.state_map[state_name]

        # Buscar en destino
        dest_ids = self.dest.search('res.country.state', [
            ('name', 'ilike', state_name),
            ('country_id', '=', self.dest_country_id)
        ], limit=1)

        if dest_ids:
            self.state_map[state_name] = dest_ids[0]
            return dest_ids[0]

        return None

    def get_or_create_city(self, city_name: str, state_id: Optional[int]) -> Optional[int]:
        """Obtiene o crea ciudad en destino"""
        if not city_name:
            return None

        cache_key = f"{city_name}_{state_id}"
        if cache_key in self.city_map:
            return self.city_map[cache_key]

        # Buscar en destino
        domain = [('name', 'ilike', city_name)]
        if state_id:
            domain.append(('state_id', '=', state_id))

        dest_ids = self.dest.search('res.city', domain, limit=1)

        if dest_ids:
            self.city_map[cache_key] = dest_ids[0]
            return dest_ids[0]

        return None

    def get_or_create_region(self, region_name: str, city_id: Optional[int]) -> Optional[int]:
        """Obtiene o crea región (barrio) en destino"""
        if not region_name or not city_id:
            return None

        cache_key = f"{region_name}_{city_id}"
        if cache_key in self.region_map:
            return self.region_map[cache_key]

        # Buscar en destino
        dest_ids = self.dest.search('region.region', [
            ('name', '=', region_name),
            ('city_id', '=', city_id)
        ], limit=1)

        if dest_ids:
            self.region_map[cache_key] = dest_ids[0]
            return dest_ids[0]

        # Crear nueva región
        try:
            vals = {
                'name': region_name,
                'city_id': city_id,
                'country_id': self.dest_country_id,
            }
            dest_region_id = self.dest.create('region.region', vals)
            self.region_map[cache_key] = dest_region_id
            logger.info(f"   ✅ Región creada: {region_name} → ID {dest_region_id}")
            return dest_region_id
        except Exception as e:
            logger.error(f"   ❌ Error creando región {region_name}: {e}")
            return None

    def get_or_create_property_type(self, type_name: str) -> Optional[int]:
        """Obtiene o crea tipo de propiedad en destino"""
        if not type_name:
            return None

        if type_name in self.property_type_map:
            return self.property_type_map[type_name]

        # Buscar en destino
        dest_ids = self.dest.search('property.type', [('name', '=', type_name)], limit=1)

        if dest_ids:
            self.property_type_map[type_name] = dest_ids[0]
            return dest_ids[0]

        # Crear nuevo tipo
        try:
            vals = {
                'name': type_name,
                'property_type': 'apartment',  # Default
            }
            dest_type_id = self.dest.create('property.type', vals)
            self.property_type_map[type_name] = dest_type_id
            logger.info(f"   ✅ Tipo propiedad creado: {type_name} → ID {dest_type_id}")
            return dest_type_id
        except Exception as e:
            logger.error(f"   ❌ Error creando tipo {type_name}: {e}")
            return None

    def copy_property(self, source_property: Dict) -> tuple:
        """Copia una propiedad desde origen a destino"""
        try:
            prop_name = source_property.get('name', 'Sin nombre')
            prop_id = source_property.get('id')

            logger.info(f"\n{'─'*70}")
            logger.info(f"📦 Copiando: {prop_name} (ID origen: {prop_id})")

            # 1. Propietario principal
            dest_partner_id = None
            if source_property.get('partner_id'):
                source_partner_id = source_property['partner_id'][0]
                source_partner_name = source_property['partner_id'][1]
                dest_partner_id = self.get_or_create_partner(source_partner_id, source_partner_name)

            # 2. Ubicación
            dest_state_id = None
            dest_city_id = None
            dest_region_id = None

            # Departamento
            if source_property.get('state_id'):
                state_name = source_property['state_id'][1]
                dest_state_id = self.get_or_create_state(state_name)
                if dest_state_id:
                    logger.info(f"   ✓ Departamento: {state_name} → ID {dest_state_id}")

            # Ciudad
            if source_property.get('city_id'):
                city_name = source_property['city_id'][1]
                dest_city_id = self.get_or_create_city(city_name, dest_state_id)
                if dest_city_id:
                    logger.info(f"   ✓ Ciudad: {city_name} → ID {dest_city_id}")
            elif source_property.get('city'):
                # Si no tiene city_id pero tiene city (char), intentar buscar
                city_name = source_property['city']
                dest_city_id = self.get_or_create_city(city_name, dest_state_id)
                if dest_city_id:
                    logger.info(f"   ✓ Ciudad (char): {city_name} → ID {dest_city_id}")

            # Región/Barrio
            if source_property.get('region_id') and dest_city_id:
                region_name = source_property['region_id'][1]
                dest_region_id = self.get_or_create_region(region_name, dest_city_id)

            # 3. Tipo de propiedad
            dest_property_type_id = None
            if source_property.get('property_type_id'):
                type_name = source_property['property_type_id'][1]
                dest_property_type_id = self.get_or_create_property_type(type_name)

            # 4. Construir valores para crear propiedad
            vals = {
                # Básicos
                'name': prop_name,
                'type': 'service'  # CORREGIDO,
                'is_property': True,
                'active': True,

                # Relaciones
                'partner_id': dest_partner_id,
                'region_id': dest_region_id,
                'state_id': dest_state_id,
                'city_id': dest_city_id,
                'country_id': self.dest_country_id,
                'property_type_id': dest_property_type_id,

                # Ubicación
                'street': source_property.get('street'),
                'street2': source_property.get('street2'),
                'zip': source_property.get('zip'),
                'city': source_property.get('city'),
                'neighborhood': source_property.get('neighborhood'),

                # Características numéricas
                'property_area': source_property.get('property_area', 0.0),
                'num_bedrooms': source_property.get('num_bedrooms', 0),
                'num_bathrooms': source_property.get('num_bathrooms', 0),
                'floor_number': source_property.get('floor_number', 0),

                # Precios
                'net_rental_price': source_property.get('net_rental_price', 0.0),
                'rent_value_from': source_property.get('rent_value_from', 0.0),
                'admin_value': source_property.get('admin_value', 0.0),
                'net_price': source_property.get('net_price', 0.0),
                'sale_value_from': source_property.get('sale_value_from', 0.0),

                # Campos de selección
                'state': source_property.get('state', 'free'),
                'stratum': source_property.get('stratum'),
                'type_service': source_property.get('type_service', 'rent'),
                'property_status': source_property.get('property_status'),

                # Sistema
                'company_id': self.dest_company_id,
                'currency_id': self.dest_currency_id,
            }

            # Campos booleanos comunes
            bool_fields = [
                'garage', 'elevator', 'pools', 'gym', 'furnished', 'balcony',
                'has_security', 'living_room', 'integral_kitchen', 'air_conditioning',
                'service_room', 'garden', 'terrace', 'social_room', 'green_areas'
            ]
            for field in bool_fields:
                if field in source_property:
                    vals[field] = source_property[field]

            # Limpiar valores None y False no booleanos
            vals = {k: v for k, v in vals.items() if v is not None and (v is not False or isinstance(v, bool))}

            # 5. Crear propiedad en destino
            logger.info(f"   📝 Creando propiedad en destino...")
            dest_property_id = self.dest.create('product.template', vals)

            logger.info(f"   ✅ PROPIEDAD COPIADA: {prop_name}")
            logger.info(f"      Origen ID: {prop_id} → Destino ID: {dest_property_id}")

            return True, dest_property_id, "Copiada exitosamente"

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            logger.error(f"   ❌ {error_msg}")
            return False, 0, error_msg

    def copy_properties(self, limit: int = None) -> Dict:
        """Copia múltiples propiedades"""
        logger.info(f"\n{'='*70}")
        logger.info(f"🚀 INICIANDO COPIA DE PROPIEDADES")
        logger.info(f"{'='*70}\n")

        # Campos a leer del origen
        fields = [
            'id', 'name', 'partner_id', 'region_id', 'state_id', 'city_id', 'city',
            'property_type_id', 'street', 'street2', 'zip', 'neighborhood',
            'property_area', 'num_bedrooms', 'num_bathrooms', 'floor_number',
            'net_rental_price', 'rent_value_from', 'admin_value',
            'net_price', 'sale_value_from', 'state', 'stratum', 'type_service',
            'property_status', 'garage', 'elevator', 'pools', 'gym', 'furnished',
            'balcony', 'has_security', 'living_room', 'integral_kitchen',
            'air_conditioning', 'service_room', 'garden', 'terrace',
            'social_room', 'green_areas'
        ]

        # Buscar propiedades en origen
        logger.info(f"🔍 Buscando propiedades en origen...")
        source_properties = self.source.search_read(
            'product.template',
            [('is_property', '=', True), ('active', '=', True)],
            fields,
            limit=limit
        )

        logger.info(f"   ✓ Encontradas {len(source_properties)} propiedades\n")

        if not source_properties:
            logger.warning("⚠ No se encontraron propiedades para copiar")
            return {'total': 0, 'success': 0, 'failed': 0, 'errors': []}

        # Estadísticas
        stats = {
            'total': len(source_properties),
            'success': 0,
            'failed': 0,
            'errors': []
        }

        # Copiar cada propiedad
        for idx, prop in enumerate(source_properties, 1):
            logger.info(f"\n[{idx}/{stats['total']}]")

            success, dest_id, message = self.copy_property(prop)

            if success:
                stats['success'] += 1
            else:
                stats['failed'] += 1
                stats['errors'].append({
                    'property': prop.get('name', 'Sin nombre'),
                    'source_id': prop.get('id'),
                    'error': message
                })

        # Resumen final
        logger.info(f"\n{'='*70}")
        logger.info(f"📊 RESUMEN FINAL")
        logger.info(f"{'='*70}")
        logger.info(f"Total propiedades: {stats['total']}")
        logger.info(f"Copiadas:          {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
        logger.info(f"Fallidas:          {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")
        logger.info(f"{'='*70}\n")

        if stats['errors']:
            logger.error(f"\n❌ ERRORES:")
            for error in stats['errors']:
                logger.error(f"  - {error['property']} (ID: {error['source_id']}): {error['error']}")

        return stats


# =================== FUNCIÓN PRINCIPAL ===================

def main():
    """Función principal"""
    logger.info(f"\n{'#'*70}")
    logger.info(f"# COPIA DE PROPIEDADES: SITE → ODOO 18")
    logger.info(f"{'#'*70}\n")

    # Conectar a origen
    source_conn = OdooConnection(
        name="ORIGEN (Site)",
        url=SOURCE['url'],
        db=SOURCE['db'],
        username=SOURCE['username'],
        password=SOURCE['password']
    )

    # Conectar a destino
    dest_conn = OdooConnection(
        name="DESTINO (Odoo 18)",
        url=DESTINATION['url'],
        db=DESTINATION['db'],
        username=DESTINATION['username'],
        password=DESTINATION['password']
    )

    # Crear copiador
    copier = PropertyCopier(source_conn, dest_conn)

    # Ejecutar copia
    stats = copier.copy_properties(limit=LIMIT_PROPERTIES)

    # Mostrar resumen
    logger.info(f"\n✅ Proceso completado")
    logger.info(f"   Total: {stats['total']}")
    logger.info(f"   Exitosas: {stats['success']}")
    logger.info(f"   Fallidas: {stats['failed']}\n")


if __name__ == '__main__':
    main()
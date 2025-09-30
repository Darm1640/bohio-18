#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Copia COMPLETA de Propiedades - Site → Odoo 18
=========================================================
Copia TODOS los campos posibles de propiedades

Version: 3.0.0 - COMPLETO
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

LIMIT = 900000  # Número de propiedades a copiar
DRY_RUN = False  # True = solo simular, False = crear real


# =================== LISTA COMPLETA DE CAMPOS ===================
# Todos los campos posibles de product.template con is_property=True

PROPERTY_FIELDS = [
    # === IDENTIFICACIÓN ===
    'id', 'name', 'sequence', 'state',

    # === RELACIONES PRINCIPALES ===
    'partner_id', 'region_id', 'state_id', 'city_id', 'property_type_id',

    # === UBICACIÓN COMPLETA ===
    'address', 'street', 'street2', 'zip', 'city', 'neighborhood',
    'department', 'municipality',

    # === GEOLOCALIZACIÓN ===
    'latitude', 'longitude',
    # === CARACTERÍSTICAS BÁSICAS ===
    'stratum', 'type_service', 'property_status',

    # === MEDIDAS ===
    'property_area', 'unit_of_measure', 'front_meters', 'depth_meters',

    # === CARACTERÍSTICAS FÍSICAS ===
    'num_bedrooms', 'num_bathrooms', 'property_age', 'num_living_room',
    'floor_number', 'number_of_levels',

    # === SALAS Y ESPACIOS ===
    'living_room', 'living_dining_room', 'main_dining_room', 'study',

    # === COCINAS ===
    'simple_kitchen', 'integral_kitchen', 'american_kitchen',

    # === BAÑOS Y SERVICIOS ===
    'service_room', 'service_bathroom', 'auxiliary_bathroom',

    # === ALMACENAMIENTO ===
    'closet', 'n_closet', 'walk_in_closet', 'warehouse',

    # === ÁREAS EXTERIORES ===
    'patio', 'garden', 'balcony', 'terrace', 'laundry_area',

    # === PISOS Y ACABADOS ===
    'floor_type', 'marble_floor',

    # === PUERTAS Y VENTANAS ===
    'door_type', 'security_door', 'blinds',

    # === PARQUEADERO ===
    'garage', 'n_garage', 'covered_parking', 'uncovered_parking', 'visitors_parking',

    # === SERVICIOS PÚBLICOS ===
    'gas_installation', 'gas_heating', 'electric_heating', 'has_water',
    'hot_water', 'air_conditioning', 'n_air_conditioning',

    # === COMUNICACIONES ===
    'phone_lines', 'intercom',

    # === SEGURIDAD ===
    'has_security', 'security_cameras', 'alarm',

    # === AMENIDADES DEL EDIFICIO ===
    'doorman', 'elevator', 'garbage_chute',

    # === ÁREAS RECREATIVAS ===
    'social_room', 'gym', 'pools', 'n_pools', 'sauna', 'jacuzzi',
    'green_areas', 'sports_area', 'has_playground',

    # === CARACTERÍSTICAS ADICIONALES ===
    'furnished', 'fireplace', 'mezzanine', 'apartment_type',

    # === PRECIOS DE VENTA ===
    'property_price_type', 'price_per_unit', 'net_price',
    'discount_type', 'discount', 'sale_value_from', 'sale_value_to',

    # === PRECIOS DE ARRIENDO ===
    'rental_price_type', 'rental_price_per_unit', 'net_rental_price',
    'rental_discount_type', 'rental_discount',
    'rent_value_from', 'rent_value_to',

    # === ADMINISTRACIÓN ===
    'admin_value', 'cadastral_valuation', 'property_tax',

    # === MANTENIMIENTO ===
    'maintenance_type', 'maintenance_charges',

    # === INFORMACIÓN LEGAL ===
    'license_code', 'registration_number', 'cadastral_reference', 'liens',

    # === CONSIGNACIÓN ===
    'consignment_date', 'property_consignee', 'keys_location', 'key_note',

    # === DESCRIPCIONES ===
    'urbanization_description', 'property_description', 'observations', 'note',

    # === INFORMACIÓN DE CONTACTO ===
    'contact_name', 'email_from', 'phone', 'mobile', 'website',

    # === IDENTIFICACIÓN FISCAL ===
    'vat', 'l10n_latam_identification_type_id',

    # === PROYECTO ===
    'building_unit', 'is_vis', 'is_vip',
]


class OdooConnection:
    def __init__(self, name, url, db, username, password):
        self.name = name
        self.url = url
        self.db = db
        logger.info(f"\nConectando a {name}: {url} - DB: {db}")

        self.common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

        self.uid = self.common.authenticate(db, username, password, {})
        if not self.uid:
            raise Exception(f"Error autenticando en {name}")
        logger.info(f"OK - Conectado (UID: {self.uid})")

    def search(self, model, domain, limit=None):
        kwargs = {'limit': limit} if limit else {}
        return self.models.execute_kw(self.db, self.uid, 'admin', model, 'search', [domain], kwargs)

    def read(self, model, ids, fields=None):
        kwargs = {'fields': fields} if fields else {}
        return self.models.execute_kw(self.db, self.uid, 'admin', model, 'read', [ids], kwargs)

    def create(self, model, vals):
        return self.models.execute_kw(self.db, self.uid, 'admin', model, 'create', [[vals]])

    def search_read(self, model, domain, fields, limit=None):
        kwargs = {'fields': fields, 'limit': limit} if limit else {'fields': fields}
        return self.models.execute_kw(self.db, self.uid, 'admin', model, 'search_read', [domain], kwargs)


class Copier:
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst
        self.cache = {'partner': {}, 'region': {}, 'type': {}, 'state': {}, 'city': {}}

        # IDs base
        ids = self.dst.search('res.country', [('code', '=', 'CO')], 1)
        self.country_id = ids[0] if ids else None
        ids = self.dst.search('res.company', [('id', '=', 1)], 1)
        self.company_id = ids[0] if ids else 1
        ids = self.dst.search('res.currency', [('name', '=', 'COP')], 1)
        self.currency_id = ids[0] if ids else None

        logger.info(f"\nCache base: Pais={self.country_id}, Cia={self.company_id}, Mon={self.currency_id}\n")

    def get_partner(self, src_id, src_name):
        if src_id in self.cache['partner']:
            return self.cache['partner'][src_id]

        try:
            data = self.src.read('res.partner', [src_id], ['name', 'vat', 'phone', 'email', 'mobile'])[0]

            # Buscar por VAT
            if data.get('vat'):
                ids = self.dst.search('res.partner', [('vat', '=', data['vat'])], 1)
                if ids:
                    partner_id = ids[0] if isinstance(ids, list) else ids
                    self.cache['partner'][src_id] = partner_id
                    logger.info(f"   + Partner existente (VAT): {data['name']} -> {partner_id}")
                    return partner_id

            # Buscar por nombre
            ids = self.dst.search('res.partner', [('name', '=', data['name'])], 1)
            if ids:
                partner_id = ids[0] if isinstance(ids, list) else ids
                self.cache['partner'][src_id] = partner_id
                logger.info(f"   + Partner existente (Nombre): {data['name']} -> {partner_id}")
                return partner_id

            # Crear nuevo
            vals = {
                'name': data.get('name', 'Propietario'),
                'type': 'contact',
                'customer_rank': 1,
                'country_id': self.country_id
            }
            for f in ['vat', 'phone', 'email', 'mobile']:
                if data.get(f):
                    vals[f] = data[f]

            new_id = self.dst.create('res.partner', vals)
            # Asegurar que es integer
            new_id = new_id[0] if isinstance(new_id, list) else new_id
            self.cache['partner'][src_id] = new_id
            logger.info(f"   + Partner CREADO: {vals['name']} -> {new_id}")
            return new_id
        except:
            return None

    def get_state(self, name):
        if not name or name in self.cache['state']:
            return self.cache['state'].get(name)
        ids = self.dst.search('res.country.state', [('name', 'ilike', name), ('country_id', '=', self.country_id)], 1)
        if ids:
            self.cache['state'][name] = ids[0]
            return ids[0]
        return None

    def get_city(self, name, state_id, region_name=None):
        """
        Obtiene ciudad, si no encuentra busca por barrio.
        Retorna dict: {'city_id': X, 'state_id': Y, 'country_id': Z}
        Si encuentra ciudad, llena automáticamente state y country desde la ciudad.
        """
        key = f"{name}_{state_id}"
        if key in self.cache['city']:
            return self.cache['city'][key]

        # Buscar ciudad directamente
        domain = [('name', 'ilike', name.upper())]
        ids = self.dst.search('res.city', domain, 1)
        if ids:
            # Leer state_id y country_id de la ciudad
            city_data = self.dst.read('res.city', [ids[0]], ['state_id', 'country_id'])
            result = {
                'city_id': ids[0],
                'state_id': city_data[0]['state_id'][0] if city_data[0].get('state_id') else state_id,
                'country_id': city_data[0]['country_id'][0] if city_data[0].get('country_id') else self.country_id
            }
            self.cache['city'][key] = result
            logger.info(f"   + Ciudad encontrada: {name} -> {ids[0]} (Depto: {result['state_id']})")
            return result

        # Si no encuentra y hay nombre de barrio, buscar ciudad por barrio
        if region_name:
            logger.info(f"   ? Ciudad '{name}' no encontrada, buscando por barrio '{region_name}'...")
            region_domain = [('name', '=', region_name.upper())]
            if state_id:
                region_domain.append(('state_id', '=', state_id))
            region_ids = self.dst.search('region.region', region_domain, 1)

            if region_ids:
                # Leer ciudad del barrio
                region_data = self.dst.read('region.region', [region_ids[0]], ['city_id'])
                if region_data and region_data[0].get('city_id'):
                    city_id = region_data[0]['city_id'][0]
                    # Leer state_id y country_id de la ciudad
                    city_data = self.dst.read('res.city', [city_id], ['state_id', 'country_id'])
                    result = {
                        'city_id': city_id,
                        'state_id': city_data[0]['state_id'][0] if city_data[0].get('state_id') else state_id,
                        'country_id': city_data[0]['country_id'][0] if city_data[0].get('country_id') else self.country_id
                    }
                    self.cache['city'][key] = result
                    logger.info(f"   + Ciudad encontrada via barrio: {region_name} -> ciudad {city_id} (Depto: {result['state_id']})")
                    return result

        return None

    def get_region(self, name, city_id):
        if not name or not city_id:
            return None
        key = f"{name}_{city_id}"
        if key in self.cache['region']:
            return self.cache['region'][key]

        ids = self.dst.search('region.region', [('name', '=', name), ('city_id', '=', city_id)], 1)
        if ids:
            self.cache['region'][key] = ids[0]
            return ids[0]

        # Crear
        try:
            new_id = self.dst.create('region.region', {'name': name, 'city_id': city_id, 'country_id': self.country_id})
            self.cache['region'][key] = new_id
            logger.info(f"   + Region CREADA: {name} -> {new_id}")
            return new_id
        except:
            return None

    def get_type(self, name):
        if not name or name in self.cache['type']:
            return self.cache['type'].get(name)
        ids = self.dst.search('property.type', [('name', '=', name)], 1)
        if ids:
            self.cache['type'][name] = ids[0]
            return ids[0]
        try:
            new_id = self.dst.create('property.type', {'name': name, 'property_type': 'apartment'})
            # Asegurar que retorna integer, no lista
            if isinstance(new_id, list):
                new_id = new_id[0]
            self.cache['type'][name] = new_id
            logger.info(f"   + Tipo CREADO: {name} -> {new_id}")
            return new_id
        except:
            return None

    def copy_one(self, prop):
        try:
            name = prop.get('name', 'Sin nombre')
            src_id = prop.get('id')

            logger.info(f"\n{'='*70}")
            logger.info(f"Propiedad: {name} (ID origen: {src_id})")

            # Verificar si ya existe la propiedad por nombre
            existing = self.dst.search('product.template', [('name', '=', name), ('is_property', '=', True)], 1)
            if existing:
                logger.info(f"   ! Propiedad YA EXISTE en destino: ID {existing[0]}")
                return True, existing[0]

            # Propietario
            partner_id = None
            if prop.get('partner_id'):
                partner_id = self.get_partner(prop['partner_id'][0], prop['partner_id'][1])

            # Ubicacion - Buscar por Many2one O por texto
            # IMPORTANTE: Si encuentra ciudad, también llena state y country automáticamente
            state_id = None
            city_id = None
            region_id = None
            country_id = self.country_id  # Default

            # 1. Obtener nombre de barrio para búsqueda alternativa
            region_name = None
            if prop.get('region_id'):
                region_name = prop['region_id'][1]
            elif prop.get('neighborhood'):
                region_name = prop['neighborhood']

            # 2. Buscar CIUDAD primero (porque trae state y country automáticamente)
            city_result = None
            if prop.get('city_id'):
                # Si existe Many2one, usarlo
                city_result = self.get_city(prop['city_id'][1], None, region_name)
            elif prop.get('city'):
                # Si no, buscar usando campo de texto 'city'
                city_result = self.get_city(prop['city'], None, region_name)

            # 3. Si encontró ciudad, extraer city_id, state_id, country_id
            if city_result:
                city_id = city_result['city_id']
                state_id = city_result['state_id']
                country_id = city_result['country_id']

            # 4. Si NO encontró ciudad, buscar state manualmente
            if not state_id:
                if prop.get('state_id'):
                    state_id = self.get_state(prop['state_id'][1])
                    if state_id:
                        logger.info(f"   + Depto: {prop['state_id'][1]} -> {state_id}")
                elif prop.get('department'):
                    state_id = self.get_state(prop['department'])
                    if state_id:
                        logger.info(f"   + Depto (texto): {prop['department']} -> {state_id}")

            # 5. Buscar/crear BARRIO
            if prop.get('region_id') and city_id:
                # Si existe Many2one, usarlo
                region_id = self.get_region(prop['region_id'][1], city_id)
            elif region_name and city_id:
                # Si no, crear/buscar usando campo de texto 'neighborhood'
                region_id = self.get_region(region_name, city_id)

            # Tipo
            type_id = None
            if prop.get('property_type_id'):
                type_id = self.get_type(prop['property_type_id'][1])

            # === CONSTRUIR VALORES COMPLETOS ===
            vals = {
                # Sistema - SIEMPRE REQUERIDOS
                'name': name,
                'type': 'service',
                'is_property': True,
                'active': True,
                'currency_id': self.currency_id,
                'country_id': country_id,  # Usar el country_id de la ciudad si se encontró
            }

            # === MAPEO DE CAMPOS DIRECTOS ===
            # Estos campos se copian tal cual del origen al destino

            # Relaciones principales
            if partner_id:
                vals['partner_id'] = partner_id
            if region_id:
                vals['region_id'] = region_id
            if state_id:
                vals['state_id'] = state_id
            if city_id:
                vals['city_id'] = city_id
            if type_id:
                vals['property_type_id'] = type_id

            # Campos de texto
            text_fields = [
                'address', 'street', 'street2', 'zip', 'city', 'neighborhood',
                'department', 'municipality', 'urbanization_description',
                'property_description', 'observations', 'note', 'contact_name',
                'email_from', 'phone', 'mobile', 'website', 'vat',
                'license_code', 'registration_number', 'cadastral_reference',
                'key_note'
            ]
            for field in text_fields:
                if prop.get(field):
                    vals[field] = prop[field]

            # Campos numéricos (float)
            float_fields = [
                'property_area', 'front_meters', 'depth_meters', 'latitude', 'longitude',
                'price_per_unit', 'net_price', 'discount', 'sale_value_from', 'sale_value_to',
                'rental_price_per_unit', 'net_rental_price', 'rental_discount',
                'rent_value_from', 'rent_value_to', 'admin_value', 'cadastral_valuation',
                'property_tax', 'maintenance_charges'
            ]
            for field in float_fields:
                if field in prop and prop[field] is not False:
                    vals[field] = float(prop[field]) if prop[field] else 0.0

            # Campos numéricos (integer)
            int_fields = [
                'sequence', 'num_bedrooms', 'num_bathrooms', 'property_age',
                'num_living_room', 'floor_number', 'number_of_levels', 'n_closet',
                'n_garage', 'covered_parking', 'uncovered_parking', 'phone_lines',
                'n_air_conditioning', 'n_pools'
            ]
            for field in int_fields:
                if field in prop and prop[field] is not False:
                    vals[field] = int(prop[field]) if prop[field] else 0

            # Campos de selección
            selection_fields = [
                'state', 'stratum', 'type_service', 'property_status',
                'unit_of_measure', 'floor_type', 'door_type', 'doorman',
                'property_price_type', 'discount_type', 'rental_price_type',
                'rental_discount_type', 'maintenance_type', 'property_consignee',
                'keys_location', 'apartment_type', 'building_unit',
            
            ]
            for field in selection_fields:
                if prop.get(field):
                    vals[field] = prop[field]

            # Campos booleanos - TODOS
            boolean_fields = [
                'living_room', 'living_dining_room', 'main_dining_room', 'study',
                'simple_kitchen', 'integral_kitchen', 'american_kitchen',
                'service_room', 'service_bathroom', 'auxiliary_bathroom',
                'closet', 'walk_in_closet', 'warehouse', 'patio', 'garden',
                'balcony', 'terrace', 'laundry_area', 'marble_floor',
                'security_door', 'blinds', 'garage', 'visitors_parking',
                'gas_installation', 'gas_heating', 'electric_heating',
                'has_water', 'hot_water', 'air_conditioning', 'intercom',
                'has_security', 'security_cameras', 'alarm', 'elevator',
                'garbage_chute', 'social_room', 'gym', 'pools', 'sauna',
                'jacuzzi', 'green_areas', 'sports_area', 'has_playground',
                'furnished', 'fireplace', 'mezzanine', 'is_vis', 'is_vip',
                'liens'
            ]
            for field in boolean_fields:
                if field in prop:
                    vals[field] = bool(prop[field])

            # Campos de fecha
            date_fields = ['consignment_date']
            for field in date_fields:
                if prop.get(field):
                    vals[field] = prop[field]

            # Contar campos copiados
            total_fields = len(vals)
            logger.info(f"\nTotal campos a copiar: {total_fields}")
            logger.info(f"Resumen:")
            logger.info(f"  Propietario: {partner_id}")

            # Mostrar ubicación con nombres
            dept_name = prop.get('department') or (prop['state_id'][1] if prop.get('state_id') else 'N/A')
            city_name = prop.get('city') or (prop['city_id'][1] if prop.get('city_id') else 'N/A')
            region_name_display = region_name or 'N/A'
            logger.info(f"  Ubicacion: Depto {dept_name} [{state_id or 'X'}], Ciudad {city_name} [{city_id or 'X'}], Barrio {region_name_display} [{region_id or 'X'}]")
            logger.info(f"  Area: {vals.get('property_area', 0)} m2")
            logger.info(f"  Habitaciones: {vals.get('num_bedrooms', 0)} | Banos: {vals.get('num_bathrooms', 0)}")
            logger.info(f"  Arriendo: ${vals.get('net_rental_price', 0):,.0f}")
            logger.info(f"  Venta: ${vals.get('net_price', 0):,.0f}")

            # Mostrar amenidades
            amenities = []
            if vals.get('garage'):
                amenities.append('Garage')
            if vals.get('elevator'):
                amenities.append('Ascensor')
            if vals.get('pools'):
                amenities.append('Piscina')
            if vals.get('gym'):
                amenities.append('Gimnasio')
            if vals.get('social_room'):
                amenities.append('Salon Social')
            if vals.get('has_security'):
                amenities.append('Seguridad')
            if amenities:
                logger.info(f"  Amenidades: {', '.join(amenities)}")

            if DRY_RUN:
                logger.info(f"\n[DRY RUN] NO SE CREO - Solo simulacion")
                logger.info(f"  Se copiarian {total_fields} campos")
                return True, 0

            # Crear
            logger.info(f"\nCreando en destino con {total_fields} campos...")
            new_id = self.dst.create('product.template', vals)
            logger.info(f"OK! Propiedad creada: {name} -> ID {new_id}")
            return True, new_id

        except Exception as e:
            logger.error(f"ERROR: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False, 0

    def copy_all(self, limit):
        logger.info(f"\n{'#'*70}")
        if DRY_RUN:
            logger.info(f"# MODO PRUEBA (DRY RUN) - Solo simulacion")
        else:
            logger.info(f"# COPIA COMPLETA DE PROPIEDADES")
        logger.info(f"{'#'*70}\n")

        logger.info(f"Buscando propiedades en origen...")
        logger.info(f"Campos a copiar: {len(PROPERTY_FIELDS)}")

        props = self.src.search_read(
            'product.template',
            [('is_property', '=', True), ('active', '=', True)],
            PROPERTY_FIELDS,
            limit
        )

        logger.info(f"Encontradas {len(props)} propiedades\n")

        if not props:
            logger.warning("No hay propiedades para copiar")
            return {'total': 0, 'ok': 0, 'fail': 0}

        stats = {'total': len(props), 'ok': 0, 'fail': 0, 'errors': []}

        for idx, prop in enumerate(props, 1):
            logger.info(f"\n[{idx}/{stats['total']}]")
            success, new_id = self.copy_one(prop)
            if success:
                stats['ok'] += 1
            else:
                stats['fail'] += 1
                stats['errors'].append(prop.get('name', 'Sin nombre'))

        logger.info(f"\n{'='*70}")
        logger.info(f"RESUMEN FINAL")
        logger.info(f"{'='*70}")
        logger.info(f"Total:    {stats['total']}")
        logger.info(f"Exitosas: {stats['ok']} ({stats['ok']/stats['total']*100:.1f}%)")
        logger.info(f"Fallidas: {stats['fail']}")
        if stats['errors']:
            logger.info(f"\nPropiedades con error:")
            for err in stats['errors']:
                logger.info(f"  - {err}")
        logger.info(f"{'='*70}\n")

        return stats


def main():
    logger.info("\n" + "#"*70)
    logger.info("# COPIA COMPLETA DE PROPIEDADES: SITE -> ODOO 18")
    logger.info("# Version 3.0 - TODOS LOS CAMPOS")
    logger.info("#"*70)

    src = OdooConnection("ORIGEN", SOURCE['url'], SOURCE['db'], SOURCE['username'], SOURCE['password'])
    dst = OdooConnection("DESTINO", DESTINATION['url'], DESTINATION['db'], DESTINATION['username'], DESTINATION['password'])

    copier = Copier(src, dst)
    stats = copier.copy_all(LIMIT)

    logger.info(f"\nProceso completado: {stats['ok']}/{stats['total']} exitosas\n")


if __name__ == '__main__':
    main()
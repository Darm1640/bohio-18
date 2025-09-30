#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Copia de Propiedades - Site → Odoo 18 (CORREGIDO)
============================================================
Copia propiedades reales desde inmobiliariabohio.cloudpepper.site
hacia darm1640-bohio-18.odoo.com

Version: 2.0.0 - CORREGIDO
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

LIMIT = 5  # Número de propiedades a copiar
DRY_RUN = False  # True = solo simular, False = crear real


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
            data = self.src.read('res.partner', [src_id], ['name', 'vat', 'phone', 'email'])[0]

            # Buscar por VAT
            if data.get('vat'):
                ids = self.dst.search('res.partner', [('vat', '=', data['vat'])], 1)
                if ids:
                    self.cache['partner'][src_id] = ids[0]
                    logger.info(f"   + Partner existente (VAT): {data['name']} -> {ids[0]}")
                    return ids[0]

            # Buscar por nombre
            ids = self.dst.search('res.partner', [('name', '=', data['name'])], 1)
            if ids:
                self.cache['partner'][src_id] = ids[0]
                logger.info(f"   + Partner existente (Nombre): {data['name']} -> {ids[0]}")
                return ids[0]

            # Crear nuevo
            vals = {
                'name': data.get('name', 'Propietario'),
                'type': 'contact',
                'customer_rank': 1,
                'country_id': self.country_id
            }
            for f in ['vat', 'phone', 'email']:
                if data.get(f):
                    vals[f] = data[f]

            new_id = self.dst.create('res.partner', vals)
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

    def get_city(self, name, state_id):
        key = f"{name}_{state_id}"
        if key in self.cache['city']:
            return self.cache['city'][key]
        domain = [('name', 'ilike', name)]
        if state_id:
            domain.append(('state_id', '=', state_id))
        ids = self.dst.search('res.city', domain, 1)
        if ids:
            self.cache['city'][key] = ids[0]
            return ids[0]
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

            # Propietario
            partner_id = None
            if prop.get('partner_id'):
                partner_id = self.get_partner(prop['partner_id'][0], prop['partner_id'][1])

            # Ubicacion
            state_id = None
            if prop.get('state_id'):
                state_id = self.get_state(prop['state_id'][1])
                if state_id:
                    logger.info(f"   + Depto: {prop['state_id'][1]} -> {state_id}")

            city_id = None
            if prop.get('city_id'):
                city_id = self.get_city(prop['city_id'][1], state_id)
                if city_id:
                    logger.info(f"   + Ciudad: {prop['city_id'][1]} -> {city_id}")
            elif prop.get('city'):
                city_id = self.get_city(prop['city'], state_id)
                if city_id:
                    logger.info(f"   + Ciudad (char): {prop['city']} -> {city_id}")

            region_id = None
            if prop.get('region_id') and city_id:
                region_id = self.get_region(prop['region_id'][1], city_id)

            # Tipo
            type_id = None
            if prop.get('property_type_id'):
                type_id = self.get_type(prop['property_type_id'][1])

            # Valores
            vals = {
                'name': name,
                'type': 'service',  # CORRECTO para Odoo 18
                'is_property': True,
                'active': True,
                'partner_id': partner_id,
                'region_id': region_id,
                'state_id': state_id,
                'city_id': city_id,
                'country_id': self.country_id,
                'property_type_id': type_id,
                'street': prop.get('street'),
                'zip': prop.get('zip'),
                'city': prop.get('city'),
                'property_area': prop.get('property_area', 0.0),
                'num_bedrooms': prop.get('num_bedrooms', 0),
                'num_bathrooms': prop.get('num_bathrooms', 0),
                'net_rental_price': prop.get('net_rental_price', 0.0),
                'rent_value_from': prop.get('rent_value_from', 0.0),
                'admin_value': prop.get('admin_value', 0.0),
                'net_price': prop.get('net_price', 0.0),
                'sale_value_from': prop.get('sale_value_from', 0.0),
                'state': prop.get('state', 'free'),
                'stratum': prop.get('stratum'),
                'type_service': prop.get('type_service', 'rent'),
                'company_id': self.company_id,
                'currency_id': self.currency_id,
            }

            # Booleanos
            for f in ['garage', 'elevator', 'pools', 'gym', 'furnished', 'balcony']:
                if f in prop:
                    vals[f] = prop[f]

            # Limpiar
            vals = {k: v for k, v in vals.items() if v is not None and (v is not False or isinstance(v, bool))}

            # Resumen
            logger.info(f"\nResumen:")
            logger.info(f"  Propietario: {partner_id}")
            logger.info(f"  Ubicacion: Depto {state_id}, Ciudad {city_id}, Barrio {region_id}")
            logger.info(f"  Area: {vals.get('property_area')} m2 | Hab: {vals.get('num_bedrooms')} | Banos: {vals.get('num_bathrooms')}")
            logger.info(f"  Arriendo: ${vals.get('net_rental_price'):,.0f} | Venta: ${vals.get('net_price'):,.0f}")

            if DRY_RUN:
                logger.info(f"\n[DRY RUN] NO SE CREO - Solo simulacion")
                return True, 0

            # Crear
            logger.info(f"\nCreando en destino...")
            new_id = self.dst.create('product.template', vals)
            logger.info(f"OK! Propiedad creada: {name} -> ID {new_id}")
            return True, new_id

        except Exception as e:
            logger.error(f"ERROR: {e}")
            return False, 0

    def copy_all(self, limit):
        logger.info(f"\n{'#'*70}")
        if DRY_RUN:
            logger.info(f"# MODO PRUEBA (DRY RUN) - Solo simulacion")
        else:
            logger.info(f"# COPIA DE PROPIEDADES")
        logger.info(f"{'#'*70}\n")

        # Campos a leer
        fields = [
            'id', 'name', 'partner_id', 'region_id', 'state_id', 'city_id', 'city',
            'property_type_id', 'street', 'zip', 'property_area', 'num_bedrooms',
            'num_bathrooms', 'net_rental_price', 'rent_value_from', 'admin_value',
            'net_price', 'sale_value_from', 'state', 'stratum', 'type_service',
            'garage', 'elevator', 'pools', 'gym', 'furnished', 'balcony'
        ]

        logger.info(f"Buscando propiedades en origen...")
        props = self.src.search_read('product.template', [('is_property', '=', True), ('active', '=', True)], fields, limit)
        logger.info(f"Encontradas {len(props)} propiedades\n")

        if not props:
            logger.warning("No hay propiedades para copiar")
            return {'total': 0, 'ok': 0, 'fail': 0}

        stats = {'total': len(props), 'ok': 0, 'fail': 0}

        for idx, prop in enumerate(props, 1):
            logger.info(f"\n[{idx}/{stats['total']}]")
            success, new_id = self.copy_one(prop)
            if success:
                stats['ok'] += 1
            else:
                stats['fail'] += 1

        logger.info(f"\n{'='*70}")
        logger.info(f"RESUMEN")
        logger.info(f"{'='*70}")
        logger.info(f"Total:    {stats['total']}")
        logger.info(f"Exitosas: {stats['ok']} ({stats['ok']/stats['total']*100:.1f}%)")
        logger.info(f"Fallidas: {stats['fail']}")
        logger.info(f"{'='*70}\n")

        return stats


def main():
    logger.info("\n" + "#"*70)
    logger.info("# COPIA DE PROPIEDADES: SITE -> ODOO 18")
    logger.info("#"*70)

    src = OdooConnection("ORIGEN", SOURCE['url'], SOURCE['db'], SOURCE['username'], SOURCE['password'])
    dst = OdooConnection("DESTINO", DESTINATION['url'], DESTINATION['db'], DESTINATION['username'], DESTINATION['password'])

    copier = Copier(src, dst)
    stats = copier.copy_all(LIMIT)

    logger.info(f"\nProceso completado: {stats['ok']}/{stats['total']} exitosas\n")


if __name__ == '__main__':
    main()
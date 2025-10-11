#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para migrar propiedades completas de Odoo 17 (CloudPepper) a Odoo 18 (Odoo.com)
Incluye: código, región, ciudad, departamento, barrio, terceros y todos los campos
"""
import xmlrpc.client
import sys
import io
import json
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración Odoo 17 (ORIGEN - CloudPepper Producción)
ODOO17 = {
    'name': 'Odoo 17 - CloudPepper',
    'url': 'https://inmobiliariabohio.cloudpepper.site',
    'db': 'inmobiliariabohio.cloudpepper.site',
    'username': 'admin',
    'password': 'admin'
}

# Configuración Odoo 18 (DESTINO - Odoo.com Desarrollo)
ODOO18 = {
    'name': 'Odoo 18 - Odoo.com',
    'url': 'https://darm1640-bohio-18.odoo.com',
    'db': 'darm1640-bohio-18-main-24081960',
    'username': 'admin',
    'password': '123456'
}


class PropertyMigrator:
    """Migra propiedades entre instancias de Odoo"""

    def __init__(self, source_config, target_config):
        self.source = source_config
        self.target = target_config
        self.source_uid = None
        self.target_uid = None
        self.source_models = None
        self.target_models = None

        # Cache para mapeo de IDs
        self.cache = {
            'states': {},       # Departamentos
            'cities': {},       # Ciudades
            'regions': {},      # Regiones
            'neighborhoods': {},  # Barrios
            'partners': {},     # Terceros
            'property_types': {},  # Tipos de propiedad
        }

    def connect_source(self):
        """Conectar a Odoo origen (17)"""
        try:
            print(f"\n🔌 Conectando a ORIGEN: {self.source['name']}")
            print(f"   URL: {self.source['url']}")

            common = xmlrpc.client.ServerProxy(f"{self.source['url']}/xmlrpc/2/common")
            self.source_uid = common.authenticate(
                self.source['db'],
                self.source['username'],
                self.source['password'],
                {}
            )

            if not self.source_uid:
                print("   ❌ Autenticación fallida")
                return False

            print(f"   ✅ Conectado (UID: {self.source_uid})")
            self.source_models = xmlrpc.client.ServerProxy(f"{self.source['url']}/xmlrpc/2/object")
            return True

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def connect_target(self):
        """Conectar a Odoo destino (18)"""
        try:
            print(f"\n🔌 Conectando a DESTINO: {self.target['name']}")
            print(f"   URL: {self.target['url']}")

            common = xmlrpc.client.ServerProxy(f"{self.target['url']}/xmlrpc/2/common")
            self.target_uid = common.authenticate(
                self.target['db'],
                self.target['username'],
                self.target['password'],
                {}
            )

            if not self.target_uid:
                print("   ❌ Autenticación fallida")
                return False

            print(f"   ✅ Conectado (UID: {self.target_uid})")
            self.target_models = xmlrpc.client.ServerProxy(f"{self.target['url']}/xmlrpc/2/object")
            return True

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def get_or_create_state(self, state_name, country_code='CO'):
        """Obtener o crear departamento en destino"""
        if state_name in self.cache['states']:
            return self.cache['states'][state_name]

        try:
            # Buscar en destino
            state_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'res.country.state', 'search',
                [[('name', '=', state_name)]]
            )

            if state_ids:
                self.cache['states'][state_name] = state_ids[0]
                return state_ids[0]

            # Buscar país
            country_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'res.country', 'search',
                [[('code', '=', country_code)]]
            )

            if not country_ids:
                print(f"      ⚠️  País {country_code} no encontrado")
                return None

            # Crear departamento
            state_id = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'res.country.state', 'create',
                [{
                    'name': state_name,
                    'code': state_name[:3].upper(),
                    'country_id': country_ids[0]
                }]
            )

            print(f"      ✅ Departamento creado: {state_name}")
            self.cache['states'][state_name] = state_id
            return state_id

        except Exception as e:
            print(f"      ❌ Error con departamento {state_name}: {e}")
            return None

    def get_or_create_city(self, city_name, state_id):
        """Obtener o crear ciudad en destino"""
        cache_key = f"{city_name}_{state_id}"

        if cache_key in self.cache['cities']:
            return self.cache['cities'][cache_key]

        try:
            # Buscar en destino
            city_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'res.city', 'search',
                [[('name', '=', city_name), ('state_id', '=', state_id)]]
            )

            if city_ids:
                self.cache['cities'][cache_key] = city_ids[0]
                return city_ids[0]

            # Crear ciudad
            city_id = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'res.city', 'create',
                [{
                    'name': city_name,
                    'state_id': state_id
                }]
            )

            print(f"      ✅ Ciudad creada: {city_name}")
            self.cache['cities'][cache_key] = city_id
            return city_id

        except Exception as e:
            print(f"      ❌ Error con ciudad {city_name}: {e}")
            return None

    def get_or_create_region(self, region_name, city_id):
        """Obtener o crear región en destino"""
        cache_key = f"{region_name}_{city_id}"

        if cache_key in self.cache['regions']:
            return self.cache['regions'][cache_key]

        try:
            # Buscar en destino
            region_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'property.region', 'search',
                [[('name', '=', region_name), ('city_id', '=', city_id)]]
            )

            if region_ids:
                self.cache['regions'][cache_key] = region_ids[0]
                return region_ids[0]

            # Crear región
            region_id = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'property.region', 'create',
                [{
                    'name': region_name,
                    'city_id': city_id
                }]
            )

            print(f"      ✅ Región creada: {region_name}")
            self.cache['regions'][cache_key] = region_id
            return region_id

        except Exception as e:
            print(f"      ❌ Error con región {region_name}: {e}")
            return None

    def get_or_create_neighborhood(self, neighborhood_name, region_id):
        """Obtener o crear barrio en destino"""
        cache_key = f"{neighborhood_name}_{region_id}"

        if cache_key in self.cache['neighborhoods']:
            return self.cache['neighborhoods'][cache_key]

        try:
            # Buscar en destino
            neighborhood_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'property.neighborhood', 'search',
                [[('name', '=', neighborhood_name), ('region_id', '=', region_id)]]
            )

            if neighborhood_ids:
                self.cache['neighborhoods'][cache_key] = neighborhood_ids[0]
                return neighborhood_ids[0]

            # Crear barrio
            neighborhood_id = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'property.neighborhood', 'create',
                [{
                    'name': neighborhood_name,
                    'region_id': region_id
                }]
            )

            print(f"      ✅ Barrio creado: {neighborhood_name}")
            self.cache['neighborhoods'][cache_key] = neighborhood_id
            return neighborhood_id

        except Exception as e:
            print(f"      ❌ Error con barrio {neighborhood_name}: {e}")
            return None

    def migrate_property_location(self, property_data):
        """Migrar datos de ubicación de la propiedad"""
        location_mapping = {}

        print("      📍 Migrando ubicación...")

        # 1. Departamento (state_id)
        if property_data.get('property_state_id'):
            state = property_data['property_state_id']
            state_name = state[1] if isinstance(state, (list, tuple)) else state

            state_id = self.get_or_create_state(state_name)
            if state_id:
                location_mapping['property_state_id'] = state_id

        # 2. Ciudad (city_id)
        if property_data.get('property_city_id') and location_mapping.get('property_state_id'):
            city = property_data['property_city_id']
            city_name = city[1] if isinstance(city, (list, tuple)) else city

            city_id = self.get_or_create_city(city_name, location_mapping['property_state_id'])
            if city_id:
                location_mapping['property_city_id'] = city_id

        # 3. Región (region_id)
        if property_data.get('property_region_id') and location_mapping.get('property_city_id'):
            region = property_data['property_region_id']
            region_name = region[1] if isinstance(region, (list, tuple)) else region

            region_id = self.get_or_create_region(region_name, location_mapping['property_city_id'])
            if region_id:
                location_mapping['property_region_id'] = region_id

        # 4. Barrio (neighborhood_id)
        if property_data.get('property_neighborhood_id') and location_mapping.get('property_region_id'):
            neighborhood = property_data['property_neighborhood_id']
            neighborhood_name = neighborhood[1] if isinstance(neighborhood, (list, tuple)) else neighborhood

            neighborhood_id = self.get_or_create_neighborhood(
                neighborhood_name,
                location_mapping['property_region_id']
            )
            if neighborhood_id:
                location_mapping['property_neighborhood_id'] = neighborhood_id

        # 5. Coordenadas GPS
        if property_data.get('latitude'):
            location_mapping['latitude'] = property_data['latitude']

        if property_data.get('longitude'):
            location_mapping['longitude'] = property_data['longitude']

        # 6. Dirección
        if property_data.get('street'):
            location_mapping['street'] = property_data['street']

        if property_data.get('street2'):
            location_mapping['street2'] = property_data['street2']

        return location_mapping

    def migrate_property(self, property_code):
        """Migrar una propiedad específica"""
        print(f"\n{'='*80}")
        print(f"   Migrando Propiedad: {property_code}")
        print(f"{'='*80}")

        # 1. Buscar propiedad en origen
        print("   [1] Buscando en origen...")

        try:
            # Buscar por default_code o variaciones
            search_domains = [
                [('default_code', '=', property_code)],
                [('default_code', '=', f'BOH-{property_code}')],
                [('id', '=', int(property_code)) if property_code.isdigit() else ('id', '=', -1)]
            ]

            property_ids = []
            for domain in search_domains:
                property_ids = self.source_models.execute_kw(
                    self.source['db'], self.source_uid, self.source['password'],
                    'product.template', 'search',
                    [domain]
                )
                if property_ids:
                    break

            if not property_ids:
                print(f"      ❌ Propiedad no encontrada en origen")
                return None

            property_id = property_ids[0]
            print(f"      ✅ Encontrada: ID={property_id}")

        except Exception as e:
            print(f"      ❌ Error buscando propiedad: {e}")
            return None

        # 2. Leer datos completos de la propiedad
        print("   [2] Leyendo datos completos...")

        try:
            fields_to_read = [
                'name', 'default_code', 'description', 'description_sale',
                'property_state_id', 'property_city_id', 'property_region_id',
                'property_neighborhood_id', 'latitude', 'longitude',
                'street', 'street2', 'zip',
                'list_price', 'standard_price', 'property_price_rent',
                'property_type_id', 'property_subtype_id',
                'property_bedrooms', 'property_bathrooms', 'property_garages',
                'property_area_built', 'property_area_total',
                'property_floor_number', 'property_unit_number',
                'property_status', 'is_property', 'active'
            ]

            property_data = self.source_models.execute_kw(
                self.source['db'], self.source_uid, self.source['password'],
                'product.template', 'read',
                [property_id],
                {'fields': fields_to_read}
            )[0]

            print(f"      ✅ Datos leídos: {property_data.get('name')}")

        except Exception as e:
            print(f"      ❌ Error leyendo datos: {e}")
            return None

        # 3. Verificar si ya existe en destino
        print("   [3] Verificando existencia en destino...")

        try:
            existing_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'product.template', 'search',
                [[('default_code', '=', property_data['default_code'])]]
            )

            if existing_ids:
                print(f"      ⚠️  Ya existe en destino: ID={existing_ids[0]}")
                return existing_ids[0]

        except Exception as e:
            print(f"      ❌ Error verificando: {e}")
            return None

        # 4. Migrar ubicación
        location_mapping = self.migrate_property_location(property_data)

        # 5. Preparar datos para crear en destino
        print("   [4] Preparando datos para creación...")

        vals = {
            'name': property_data['name'],
            'default_code': property_data['default_code'],
            'is_property': True,
            'active': property_data.get('active', True),
            'type': 'consu',  # Consumible para propiedades
        }

        # Descripción
        if property_data.get('description'):
            vals['description'] = property_data['description']

        if property_data.get('description_sale'):
            vals['description_sale'] = property_data['description_sale']

        # Ubicación
        vals.update(location_mapping)

        # Precios
        if property_data.get('list_price'):
            vals['list_price'] = property_data['list_price']

        if property_data.get('property_price_rent'):
            vals['property_price_rent'] = property_data['property_price_rent']

        # Características
        if property_data.get('property_bedrooms'):
            vals['property_bedrooms'] = property_data['property_bedrooms']

        if property_data.get('property_bathrooms'):
            vals['property_bathrooms'] = property_data['property_bathrooms']

        if property_data.get('property_garages'):
            vals['property_garages'] = property_data['property_garages']

        if property_data.get('property_area_built'):
            vals['property_area_built'] = property_data['property_area_built']

        if property_data.get('property_area_total'):
            vals['property_area_total'] = property_data['property_area_total']

        # 6. Crear en destino
        print("   [5] Creando propiedad en destino...")

        try:
            new_id = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'product.template', 'create',
                [vals]
            )

            print(f"      ✅ Propiedad creada: ID={new_id}")
            return new_id

        except Exception as e:
            print(f"      ❌ Error creando propiedad: {e}")
            print(f"      Datos que se intentaron crear: {vals}")
            return None

    def migrate_properties_from_list(self, list_file="property_images/listado.txt"):
        """Migrar propiedades desde archivo de listado"""
        print("\n" + "="*80)
        print("MIGRACIÓN MASIVA DE PROPIEDADES ODOO 17 → ODOO 18")
        print("="*80)

        # Leer listado
        try:
            with open(list_file, 'r', encoding='utf-8') as f:
                codes = [line.strip() for line in f if line.strip()]

            print(f"\n📋 Total propiedades en listado: {len(codes)}")

        except FileNotFoundError:
            print(f"❌ Archivo no encontrado: {list_file}")
            return

        # Estadísticas
        stats = {
            'total': len(codes),
            'migrated': 0,
            'existing': 0,
            'failed': 0
        }

        # Migrar cada propiedad
        for idx, code in enumerate(codes[:10], 1):  # LIMITAR A 10 PARA PRUEBA
            print(f"\n[{idx}/{len(codes[:10])}] Código: {code}")

            result = self.migrate_property(code)

            if result:
                if result > 0:
                    stats['migrated'] += 1
                else:
                    stats['existing'] += 1
            else:
                stats['failed'] += 1

        # Reporte final
        print("\n" + "="*80)
        print("📊 REPORTE FINAL")
        print("="*80)
        print(f"   Total:     {stats['total']}")
        print(f"   ✅ Migradas:  {stats['migrated']}")
        print(f"   ⚠️  Existentes: {stats['existing']}")
        print(f"   ❌ Fallidas:  {stats['failed']}")
        print("="*80)

        # Guardar cache
        with open('migration_cache.json', 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)

        print("\n💾 Cache guardado en: migration_cache.json")


def main():
    print("="*80)
    print("MIGRACIÓN DE PROPIEDADES: ODOO 17 → ODOO 18")
    print("="*80)

    migrator = PropertyMigrator(ODOO17, ODOO18)

    # Conectar a ambas bases
    if not migrator.connect_source():
        print("\n❌ No se pudo conectar a origen")
        return

    if not migrator.connect_target():
        print("\n❌ No se pudo conectar a destino")
        return

    # Migrar propiedades
    migrator.migrate_properties_from_list()


if __name__ == "__main__":
    main()

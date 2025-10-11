#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script COMPLETO para migrar propiedades de Odoo 17 (CloudPepper) a Odoo 18 (Odoo.com)
Incluye TODOS los campos: ubicación, características, booleanos, unidades de medida, precios, etc.
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

# MAPEO COMPLETO DE CAMPOS: Odoo 17 → Odoo 18
FIELD_MAPPING = {
    # Campos básicos (sin cambio)
    'name': 'name',
    'default_code': 'default_code',
    'description': 'description',
    'description_sale': 'description_sale',
    'active': 'active',
    'is_property': 'is_property',

    # UBICACIÓN (cambio de nombres)
    'state_id': 'property_state_id',        # res.country.state
    'city_id': 'property_city_id',          # res.city
    'region_id': 'region_id',                # region.region (SIN CAMBIO)
    'street': 'street',
    'street2': 'street2',
    'zip': 'zip',
    'latitude': 'latitude',
    'longitude': 'longitude',
    'address': 'address',                    # Dirección completa
    'city': 'city',                          # Ciudad (texto)
    'neighborhood': 'neighborhood',          # Barrio (texto)

    # CARACTERÍSTICAS - Números
    'num_bedrooms': 'property_bedrooms',
    'num_bathrooms': 'property_bathrooms',
    'n_garage': 'property_garages',
    'property_area': 'property_area_total',
    'area_in_m2': 'property_area_built',
    'floor_number': 'property_floor_number',
    'floor': 'floor',                        # Piso (si existe en destino)
    'property_age': 'property_age',          # Antigüedad

    # CARACTERÍSTICAS - Booleanos
    'garage': 'garage',                      # ¿Tiene Garaje?
    'auxiliary_bathroom': 'auxiliary_bathroom',
    'service_bathroom': 'service_bathroom',
    'laundry_area': 'laundry_area',
    'green_areas': 'green_areas',
    'sports_area': 'sports_area',
    'solar_area': 'solar_area',
    'marble_floor': 'marble_floor',

    # UNIDADES DE MEDIDA
    'unit_of_measure': 'unit_of_measure',
    'unit_display_name': 'unit_display_name',
    'unit_label': 'unit_label',
    'unit_iso_code': 'unit_iso_code',
    'base_unit_count': 'base_unit_count',
    'base_unit_id': 'base_unit_id',
    'base_unit_name': 'base_unit_name',
    'base_unit_price': 'base_unit_price',

    # PRECIOS - Venta
    'list_price': 'list_price',              # Precio de venta
    'standard_price': 'standard_price',      # Costo
    'net_price': 'net_price',                # Precio neto venta
    'price_before_discount': 'price_before_discount',
    'price_per_unit': 'price_per_unit',
    'property_price_type': 'property_price_type',
    'sale_value_from': 'sale_value_from',
    'sale_value_to': 'sale_value_to',
    'discount_type': 'discount_type',
    'compare_list_price': 'compare_list_price',

    # PRECIOS - Arriendo
    'rental_fee': 'property_price_rent',     # MAPEO IMPORTANTE
    'net_rental_price': 'net_rental_price',
    'rental_price_before_discount': 'rental_price_before_discount',
    'rental_discount': 'rental_discount',
    'rental_discount_type': 'rental_discount_type',
    'rental_price_type': 'rental_price_type',
    'rent_value_from': 'rent_value_from',
    'rent_value_to': 'rent_value_to',
    'price_per_m2_ref': 'price_per_m2_ref',
    'price_per_hectare_ref': 'price_per_hectare_ref',
    'price_per_yard_ref': 'price_per_yard_ref',

    # TIPO Y ESTADO
    'property_type': 'property_type',        # Selection
    'property_type_id': 'property_type_id',  # Many2one
    'property_status': 'property_status',    # Estado del inmueble
    'apartment_type': 'apartment_type',
    'building_unit': 'building_unit',
    'floor_type': 'floor_type',
    'door_type': 'door_type',
    'project_type': 'project_type',
    'type_service': 'type_service',

    # IMPUESTOS Y CONTABILIDAD
    'property_tax': 'property_tax',          # Impuesto predial
    'commission_type': 'commission_type',

    # PROYECTO/OBRA
    'project_area': 'project_area',

    # OTROS CAMPOS ESPECÍFICOS
    'front_meters': 'front_meters',
    'electrical_capacity': 'electrical_capacity',
    'keys_location': 'keys_location',
    'license_location': 'license_location',
    'real_estate_platform': 'real_estate_platform',
    'real_estate_sign': 'real_estate_sign',
    'property_consignee': 'property_consignee',
    'property_date': 'property_date',
    'property_description': 'property_description',
    'notarial_act_type': 'notarial_act_type',
    'billing_address_id': 'billing_address_id',
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
            'states': {},
            'cities': {},
            'regions': {},
        }

        # Estadísticas
        self.stats = {
            'total': 0,
            'migrated': 0,
            'existing': 0,
            'failed': 0,
            'fields_migrated': {},
            'fields_skipped': {}
        }

    def connect_source(self):
        """Conectar a Odoo origen (17)"""
        try:
            print(f"\nConectando a ORIGEN: {self.source['name']}")
            print(f"   URL: {self.source['url']}")

            common = xmlrpc.client.ServerProxy(f"{self.source['url']}/xmlrpc/2/common")
            self.source_uid = common.authenticate(
                self.source['db'],
                self.source['username'],
                self.source['password'],
                {}
            )

            if not self.source_uid:
                print("   Error: Autenticación fallida")
                return False

            print(f"   Conectado (UID: {self.source_uid})")
            self.source_models = xmlrpc.client.ServerProxy(f"{self.source['url']}/xmlrpc/2/object")
            return True

        except Exception as e:
            print(f"   Error: {e}")
            return False

    def connect_target(self):
        """Conectar a Odoo destino (18)"""
        try:
            print(f"\nConectando a DESTINO: {self.target['name']}")
            print(f"   URL: {self.target['url']}")

            common = xmlrpc.client.ServerProxy(f"{self.target['url']}/xmlrpc/2/common")
            self.target_uid = common.authenticate(
                self.target['db'],
                self.target['username'],
                self.target['password'],
                {}
            )

            if not self.target_uid:
                print("   Error: Autenticación fallida")
                return False

            print(f"   Conectado (UID: {self.target_uid})")
            self.target_models = xmlrpc.client.ServerProxy(f"{self.target['url']}/xmlrpc/2/object")
            return True

        except Exception as e:
            print(f"   Error: {e}")
            return False

    def get_or_create_state(self, state_data):
        """Obtener o crear departamento en destino"""
        if not state_data:
            return None

        # Extraer nombre del estado
        state_name = state_data[1] if isinstance(state_data, (list, tuple)) else state_data

        if state_name in self.cache['states']:
            return self.cache['states'][state_name]

        try:
            # Buscar en destino por nombre
            state_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'res.country.state', 'search',
                [[('name', 'ilike', state_name)]]
            )

            if state_ids:
                self.cache['states'][state_name] = state_ids[0]
                return state_ids[0]

            print(f"      Advertencia: Departamento '{state_name}' no encontrado")
            return None

        except Exception as e:
            print(f"      Error con departamento {state_name}: {e}")
            return None

    def get_or_create_city(self, city_data, state_id):
        """Obtener o crear ciudad en destino"""
        if not city_data or not state_id:
            return None

        # Extraer nombre de la ciudad
        city_name = city_data[1] if isinstance(city_data, (list, tuple)) else city_data

        # Limpiar código de ciudad (ej: "MONTERÍA (230017)" -> "MONTERÍA")
        if '(' in city_name:
            city_name = city_name.split('(')[0].strip()

        cache_key = f"{city_name}_{state_id}"

        if cache_key in self.cache['cities']:
            return self.cache['cities'][cache_key]

        try:
            # Buscar en destino
            city_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'res.city', 'search',
                [[('name', 'ilike', city_name), ('state_id', '=', state_id)]]
            )

            if city_ids:
                self.cache['cities'][cache_key] = city_ids[0]
                return city_ids[0]

            print(f"      Advertencia: Ciudad '{city_name}' no encontrada")
            return None

        except Exception as e:
            print(f"      Error con ciudad {city_name}: {e}")
            return None

    def get_or_create_region(self, region_data):
        """Obtener o crear región en destino (modelo region.region)"""
        if not region_data:
            return None

        # Si es False, retornar None
        if region_data is False:
            return None

        # Extraer ID y nombre de la región
        if isinstance(region_data, (list, tuple)):
            region_id = region_data[0]
            region_name = region_data[1]
        else:
            return None

        if region_id in self.cache['regions']:
            return self.cache['regions'][region_id]

        try:
            # Buscar en destino por nombre (modelo region.region)
            target_region_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'region.region', 'search',
                [[('name', 'ilike', region_name)]]
            )

            if target_region_ids:
                self.cache['regions'][region_id] = target_region_ids[0]
                return target_region_ids[0]

            # Si no existe, intentar crear
            # Necesitamos saber a qué ciudad pertenece en origen
            try:
                source_region = self.source_models.execute_kw(
                    self.source['db'], self.source_uid, self.source['password'],
                    'region.region', 'read',
                    [[region_id]],
                    {'fields': ['name']}
                )[0]

                # Crear en destino
                new_region_id = self.target_models.execute_kw(
                    self.target['db'], self.target_uid, self.target['password'],
                    'region.region', 'create',
                    [{'name': source_region['name']}]
                )

                print(f"      Region creada: {source_region['name']}")
                self.cache['regions'][region_id] = new_region_id
                return new_region_id

            except Exception as create_error:
                print(f"      Advertencia: No se pudo crear región '{region_name}': {create_error}")
                return None

        except Exception as e:
            print(f"      Error con región {region_name}: {e}")
            return None

    def migrate_property(self, property_code):
        """Migrar una propiedad específica con TODOS sus campos"""
        print(f"\n{'='*80}")
        print(f"   Propiedad: {property_code}")
        print(f"{'='*80}")

        # 1. Buscar propiedad en origen
        try:
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
                print(f"   No encontrada en origen")
                return None

            property_id = property_ids[0]
            print(f"   ID en origen: {property_id}")

        except Exception as e:
            print(f"   Error buscando: {e}")
            return None

        # 2. Leer TODOS los campos de origen (solo los que existen)
        fields_to_read = list(FIELD_MAPPING.keys())

        try:
            property_data = self.source_models.execute_kw(
                self.source['db'], self.source_uid, self.source['password'],
                'product.template', 'read',
                [[property_id]],
                {'fields': fields_to_read}
            )[0]

            print(f"   Nombre: {property_data.get('name', 'N/A')}")

        except Exception as e:
            print(f"   Error leyendo datos: {e}")
            return None

        # 3. Verificar si ya existe en destino
        try:
            existing_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'product.template', 'search',
                [[('default_code', '=', property_data['default_code'])]]
            )

            if existing_ids:
                print(f"   Ya existe en destino: ID={existing_ids[0]}")
                return existing_ids[0]

        except Exception as e:
            print(f"   Error verificando: {e}")
            return None

        # 4. Preparar datos para destino
        vals = {'type': 'consu'}  # Tipo de producto

        # Procesar ubicación con relaciones Many2one
        if property_data.get('state_id'):
            target_state_id = self.get_or_create_state(property_data['state_id'])
            if target_state_id:
                vals['property_state_id'] = target_state_id

                # Solo procesar ciudad si tenemos departamento
                if property_data.get('city_id'):
                    target_city_id = self.get_or_create_city(property_data['city_id'], target_state_id)
                    if target_city_id:
                        vals['property_city_id'] = target_city_id

        # Región (modelo region.region - sin cambio)
        if property_data.get('region_id'):
            target_region_id = self.get_or_create_region(property_data['region_id'])
            if target_region_id:
                vals['region_id'] = target_region_id

        # Mapear todos los demás campos
        for source_field, target_field in FIELD_MAPPING.items():
            # Saltar campos ya procesados
            if source_field in ['state_id', 'city_id', 'region_id']:
                continue

            # Saltar campos que no existen en origen
            if source_field not in property_data:
                continue

            value = property_data.get(source_field)

            # Saltar valores None o False vacíos
            if value is None:
                continue

            # Para Many2one, solo tomar el ID
            if isinstance(value, (list, tuple)) and len(value) == 2:
                value = value[0]

            # Asignar valor
            if value not in [False, '', 0, 0.0] or isinstance(value, bool):
                vals[target_field] = value

                # Estadística
                if target_field not in self.stats['fields_migrated']:
                    self.stats['fields_migrated'][target_field] = 0
                self.stats['fields_migrated'][target_field] += 1

        # 5. Crear en destino
        try:
            new_id = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'product.template', 'create',
                [vals]
            )

            print(f"   Creada en destino: ID={new_id}")
            print(f"   Campos migrados: {len(vals)}")
            return new_id

        except Exception as e:
            print(f"   Error creando: {e}")
            print(f"   Datos intentados: {json.dumps(vals, indent=2, default=str)}")
            return None

    def migrate_properties_from_list(self, list_file="property_images/listado.txt", limit=10):
        """Migrar propiedades desde archivo de listado"""
        print("\n" + "="*80)
        print("MIGRACIÓN COMPLETA DE PROPIEDADES ODOO 17 → ODOO 18")
        print("="*80)

        # Leer listado
        try:
            with open(list_file, 'r', encoding='utf-8') as f:
                codes = [line.strip() for line in f if line.strip() and line.strip() != 'default_code']

            print(f"\nTotal propiedades en listado: {len(codes)}")
            print(f"Procesando: {limit} propiedades")

        except FileNotFoundError:
            print(f"Error: Archivo no encontrado: {list_file}")
            return

        self.stats['total'] = min(limit, len(codes))

        # Migrar cada propiedad
        for idx, code in enumerate(codes[:limit], 1):
            print(f"\n[{idx}/{limit}] Código: {code}")

            result = self.migrate_property(code)

            if result and result > 0:
                self.stats['migrated'] += 1
            elif result and result < 0:
                self.stats['existing'] += 1
            else:
                self.stats['failed'] += 1

        # Reporte final
        print("\n" + "="*80)
        print("REPORTE FINAL")
        print("="*80)
        print(f"   Total procesadas: {self.stats['total']}")
        print(f"   Migradas:         {self.stats['migrated']}")
        print(f"   Ya existentes:    {self.stats['existing']}")
        print(f"   Fallidas:         {self.stats['failed']}")

        print(f"\nCampos más migrados:")
        sorted_fields = sorted(self.stats['fields_migrated'].items(), key=lambda x: x[1], reverse=True)
        for field, count in sorted_fields[:20]:
            print(f"   {field}: {count}")

        print("="*80)

        # Guardar cache
        with open('migration_cache.json', 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)

        print("\nCache guardado en: migration_cache.json")


def main():
    print("="*80)
    print("MIGRACIÓN DE PROPIEDADES: ODOO 17 → ODOO 18")
    print("VERSIÓN COMPLETA - TODOS LOS CAMPOS")
    print("="*80)

    migrator = PropertyMigrator(ODOO17, ODOO18)

    # Conectar a ambas bases
    if not migrator.connect_source():
        print("\nError: No se pudo conectar a origen")
        return

    if not migrator.connect_target():
        print("\nError: No se pudo conectar a destino")
        return

    # Migrar propiedades (10 para prueba)
    migrator.migrate_properties_from_list(limit=10)


if __name__ == "__main__":
    main()

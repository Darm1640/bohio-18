#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migración optimizada en bloques de 500 propiedades usando JSON-RPC
Incluye: city_id, state_id, region_id, property_type_id
"""
import xmlrpc.client
import json
import time

class BatchMigrator:
    def __init__(self):
        # CloudPepper
        self.cp_config = {
            'url': 'https://inmobiliariabohio.cloudpepper.site',
            'db': 'inmobiliariabohio.cloudpepper.site',
            'username': 'admin',
            'password': 'admin'
        }

        # Odoo.com
        self.odoo_config = {
            'url': 'https://darm1640-bohio-18.odoo.com',
            'db': 'darm1640-bohio-18-main-24081960',
            'username': 'admin',
            'password': '123456'
        }

        self.cp_common = None
        self.cp_models = None
        self.cp_uid = None

        self.odoo_common = None
        self.odoo_models = None
        self.odoo_uid = None

        # Cachés para búsquedas
        self.city_cache = {}
        self.state_cache = {}
        self.region_cache = {}
        self.property_type_cache = {}

        # Campos comunes
        self.common_fields = []
        self.load_common_fields()

    def load_common_fields(self):
        """Carga campos comunes desde archivo"""
        try:
            with open('comparacion_campos.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.common_fields = data.get('comunes', [])
                print(f"OK - {len(self.common_fields)} campos comunes cargados")
        except Exception as e:
            print(f"WARN - No se pudo cargar campos comunes: {e}")

    def connect_cloudpepper(self):
        """Conecta a CloudPepper"""
        print("\n📡 Conectando a CloudPepper...")
        self.cp_common = xmlrpc.client.ServerProxy(f"{self.cp_config['url']}/xmlrpc/2/common")
        self.cp_uid = self.cp_common.authenticate(
            self.cp_config['db'],
            self.cp_config['username'],
            self.cp_config['password'],
            {}
        )
        self.cp_models = xmlrpc.client.ServerProxy(f"{self.cp_config['url']}/xmlrpc/2/object")
        print(f"   OK Conectado como UID: {self.cp_uid}")

    def connect_odoo(self):
        """Conecta a Odoo.com"""
        print("\n📡 Conectando a Odoo.com...")
        self.odoo_common = xmlrpc.client.ServerProxy(f"{self.odoo_config['url']}/xmlrpc/2/common")
        self.odoo_uid = self.odoo_common.authenticate(
            self.odoo_config['db'],
            self.odoo_config['username'],
            self.odoo_config['password'],
            {}
        )
        self.odoo_models = xmlrpc.client.ServerProxy(f"{self.odoo_config['url']}/xmlrpc/2/object")
        print(f"   OK Conectado como UID: {self.odoo_uid}")

    def search_city_by_code(self, city_code):
        """Busca ciudad por código DIVIPOLA"""
        if not city_code or city_code in self.city_cache:
            return self.city_cache.get(city_code)

        try:
            city_ids = self.odoo_models.execute_kw(
                self.odoo_config['db'], self.odoo_uid, self.odoo_config['password'],
                'res.city', 'search',
                [[('l10n_co_edi_code', '=', city_code)]],
                {'limit': 1}
            )
            if city_ids:
                self.city_cache[city_code] = city_ids[0]
                return city_ids[0]

            # Intentar con campo 'code'
            city_ids = self.odoo_models.execute_kw(
                self.odoo_config['db'], self.odoo_uid, self.odoo_config['password'],
                'res.city', 'search',
                [[('code', '=', city_code)]],
                {'limit': 1}
            )
            if city_ids:
                self.city_cache[city_code] = city_ids[0]
                return city_ids[0]
        except:
            pass

        self.city_cache[city_code] = None
        return None

    def get_state_from_city(self, city_id):
        """Obtiene state_id desde city_id"""
        if city_id in self.state_cache:
            return self.state_cache[city_id]

        try:
            city_data = self.odoo_models.execute_kw(
                self.odoo_config['db'], self.odoo_uid, self.odoo_config['password'],
                'res.city', 'read',
                [city_id],
                {'fields': ['state_id']}
            )
            if city_data and city_data[0].get('state_id'):
                state_value = city_data[0]['state_id']
                if isinstance(state_value, list) and len(state_value) > 0:
                    self.state_cache[city_id] = state_value[0]
                    return state_value[0]
        except:
            pass

        self.state_cache[city_id] = None
        return None

    def search_property_type_by_name(self, type_name):
        """Busca tipo de propiedad por nombre"""
        if not type_name or type_name in self.property_type_cache:
            return self.property_type_cache.get(type_name)

        try:
            type_ids = self.odoo_models.execute_kw(
                self.odoo_config['db'], self.odoo_uid, self.odoo_config['password'],
                'property.type', 'search',
                [[('name', '=', type_name)]],
                {'limit': 1}
            )
            if type_ids:
                self.property_type_cache[type_name] = type_ids[0]
                return type_ids[0]

            type_ids = self.odoo_models.execute_kw(
                self.odoo_config['db'], self.odoo_uid, self.odoo_config['password'],
                'property.type', 'search',
                [[('name', 'ilike', type_name)]],
                {'limit': 1}
            )
            if type_ids:
                self.property_type_cache[type_name] = type_ids[0]
                return type_ids[0]
        except:
            pass

        self.property_type_cache[type_name] = None
        return None

    def get_valid_fields(self):
        """Obtiene campos válidos en Odoo.com"""
        target_fields = self.odoo_models.execute_kw(
            self.odoo_config['db'], self.odoo_uid, self.odoo_config['password'],
            'product.template', 'fields_get',
            [],
            {'attributes': ['type', 'readonly', 'required']}
        )

        valid = []
        for field in self.common_fields:
            if field in target_fields:
                field_info = target_fields[field]
                if not field_info.get('readonly', False):
                    if field_info['type'] not in ['many2many', 'one2many', 'many2one']:
                        valid.append(field)

        return valid, target_fields

    def read_batch_properties(self, property_ids, valid_fields):
        """Lee un lote de propiedades desde CloudPepper"""
        print(f"\n📖 Leyendo {len(property_ids)} propiedades...")

        # Leer campos simples en batch
        properties_data = []
        batch_size = 50

        for i in range(0, len(property_ids), batch_size):
            batch_ids = property_ids[i:i+batch_size]
            try:
                batch_data = self.cp_models.execute_kw(
                    self.cp_config['db'], self.cp_uid, self.cp_config['password'],
                    'product.template', 'read',
                    [batch_ids],
                    {'fields': valid_fields}
                )
                properties_data.extend(batch_data)
            except Exception as e:
                print(f"   WARN  Error leyendo batch: {e}")

        # Leer campos relacionales
        print(f"📖 Leyendo campos relacionales...")
        try:
            relational_data = self.cp_models.execute_kw(
                self.cp_config['db'], self.cp_uid, self.cp_config['password'],
                'product.template', 'read',
                [property_ids],
                {'fields': ['city_id', 'property_type_id']}
            )

            # Merge relational data
            for i, prop in enumerate(properties_data):
                if i < len(relational_data):
                    prop['city_id'] = relational_data[i].get('city_id')
                    prop['property_type_id'] = relational_data[i].get('property_type_id')
        except Exception as e:
            print(f"   WARN  Error leyendo relacionales: {e}")

        # Enriquecer con city_code y property_type_name
        print(f"📖 Enriqueciendo datos...")
        city_ids_to_read = []
        type_ids_to_read = []

        for prop in properties_data:
            if prop.get('city_id') and isinstance(prop['city_id'], list):
                city_ids_to_read.append(prop['city_id'][0])
            if prop.get('property_type_id') and isinstance(prop['property_type_id'], list):
                type_ids_to_read.append(prop['property_type_id'][0])

        # Leer códigos de ciudades
        city_codes = {}
        if city_ids_to_read:
            try:
                cities = self.cp_models.execute_kw(
                    self.cp_config['db'], self.cp_uid, self.cp_config['password'],
                    'res.city', 'read',
                    [list(set(city_ids_to_read))],
                    {'fields': ['id', 'code']}
                )
                city_codes = {c['id']: c.get('code') for c in cities}
            except:
                pass

        # Leer nombres de tipos
        type_names = {}
        if type_ids_to_read:
            try:
                types = self.cp_models.execute_kw(
                    self.cp_config['db'], self.cp_uid, self.cp_config['password'],
                    'property.type', 'read',
                    [list(set(type_ids_to_read))],
                    {'fields': ['id', 'name']}
                )
                type_names = {t['id']: t.get('name') for t in types}
            except:
                pass

        # Agregar datos enriquecidos
        for prop in properties_data:
            if prop.get('city_id') and isinstance(prop['city_id'], list):
                city_id_cp = prop['city_id'][0]
                prop['city_code'] = city_codes.get(city_id_cp)

            if prop.get('property_type_id') and isinstance(prop['property_type_id'], list):
                type_id_cp = prop['property_type_id'][0]
                prop['property_type_name'] = type_names.get(type_id_cp)

        print(f"   OK {len(properties_data)} propiedades leídas")
        return properties_data

    def prepare_batch_values(self, properties_data, valid_fields, target_fields):
        """Prepara valores para crear en batch"""
        print(f"\n🔧 Preparando {len(properties_data)} propiedades...")
        batch_vals = []

        for prop_data in properties_data:
            vals = {'type': 'consu', 'active': True}

            # Campos simples
            for field in valid_fields:
                if field not in prop_data:
                    continue
                value = prop_data[field]
                if value is None or value == '' or (isinstance(value, list) and not value):
                    continue

                field_type = target_fields[field]['type']

                try:
                    if field_type == 'boolean':
                        vals[field] = bool(value)
                    elif field_type in ['integer', 'float', 'monetary']:
                        if field_type == 'integer':
                            vals[field] = int(value) if value else 0
                        else:
                            vals[field] = float(value) if value else 0.0
                    elif field_type == 'selection':
                        if isinstance(value, str) and value:
                            vals[field] = value
                    else:
                        vals[field] = value
                except:
                    continue

            # Ubicación: city_id y state_id
            city_code = prop_data.get('city_code')
            if city_code:
                city_id = self.search_city_by_code(city_code)
                if city_id:
                    vals['city_id'] = city_id
                    state_id = self.get_state_from_city(city_id)
                    if state_id:
                        vals['state_id'] = state_id

            # Tipo de propiedad
            property_type_name = prop_data.get('property_type_name')
            if property_type_name:
                property_type_id = self.search_property_type_by_name(property_type_name)
                if property_type_id:
                    vals['property_type_id'] = property_type_id

            batch_vals.append(vals)

        print(f"   OK {len(batch_vals)} registros preparados")
        return batch_vals

    def create_batch(self, batch_vals):
        """Crea propiedades en batch usando create múltiple"""
        print(f"\n💾 Creando {len(batch_vals)} propiedades...")

        try:
            created_ids = self.odoo_models.execute_kw(
                self.odoo_config['db'], self.odoo_uid, self.odoo_config['password'],
                'product.template', 'create',
                [batch_vals]
            )
            print(f"   OK {len(created_ids)} propiedades creadas")
            return created_ids
        except Exception as e:
            print(f"   ERR Error creando batch: {e}")
            return []

    def migrate(self):
        """Proceso completo de migración en bloques de 500"""
        print("\n" + "="*80)
        print("MIGRACIÓN EN BLOQUES DE 500")
        print("="*80)

        self.connect_cloudpepper()
        self.connect_odoo()

        # Obtener campos válidos
        print("\n🔍 Obteniendo campos válidos...")
        valid_fields, target_fields = self.get_valid_fields()
        print(f"   OK {len(valid_fields)} campos válidos")

        # Obtener todas las propiedades de CloudPepper
        print("\n📦 Obteniendo propiedades de CloudPepper...")
        all_property_ids = self.cp_models.execute_kw(
            self.cp_config['db'], self.cp_uid, self.cp_config['password'],
            'product.template', 'search',
            [[('type', '=', 'consu')]],
            {'order': 'id asc'}
        )
        total = len(all_property_ids)
        print(f"   Total: {total} propiedades")

        # Migrar en bloques de 500
        batch_size = 500
        total_created = 0

        for i in range(0, total, batch_size):
            batch_ids = all_property_ids[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total + batch_size - 1) // batch_size

            print("\n" + "="*80)
            print(f"LOTE {batch_num}/{total_batches}: Propiedades {i+1} a {i+len(batch_ids)}")
            print("="*80)

            start_time = time.time()

            # Leer propiedades
            properties_data = self.read_batch_properties(batch_ids, valid_fields)

            # Preparar valores
            batch_vals = self.prepare_batch_values(properties_data, valid_fields, target_fields)

            # Crear en Odoo.com
            created_ids = self.create_batch(batch_vals)
            total_created += len(created_ids)

            elapsed = time.time() - start_time
            print(f"\n[T]  Tiempo lote {batch_num}: {elapsed:.1f}s")
            print(f"📊 Progreso: {total_created}/{total} ({100*total_created/total:.1f}%)")

            # Pausa breve entre lotes
            time.sleep(1)

        print("\n" + "="*80)
        print("MIGRACIÓN COMPLETA")
        print("="*80)
        print(f"OK Total creadas: {total_created}/{total}")
        print("="*80)

if __name__ == "__main__":
    migrator = BatchMigrator()
    migrator.migrate()

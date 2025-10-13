#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migración COMPLETA con búsqueda inteligente
- Busca regiones por street + city_id
- Busca partners por VAT (NIT) y nombre
- Usa código postal para ubicaciones
"""
import sys
import io
import json
import xmlrpc.client
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class SmartPropertyMigrator:
    """Migrador con búsqueda inteligente de ubicaciones y terceros"""

    def __init__(self):
        # Configuración CloudPepper (Source)
        self.cp_config = {
            'url': 'https://inmobiliariabohio.cloudpepper.site',
            'db': 'inmobiliariabohio.cloudpepper.site',
            'username': 'admin',
            'password': 'admin'
        }

        # Configuración Odoo.com (Target)
        self.odoo_config = {
            'url': 'https://darm1640-bohio-18.odoo.com',
            'db': 'darm1640-bohio-18-main-24081960',
            'username': 'admin',
            'password': '123456'
        }

        # Conexiones
        self.cp_common = None
        self.cp_models = None
        self.cp_uid = None

        self.odoo_common = None
        self.odoo_models = None
        self.odoo_uid = None

        # Cachés
        self.state_cache = {}
        self.city_cache = {}
        self.region_cache = {}
        self.partner_cache = {}
        self.partner_vat_cache = {}

        # Campos comunes
        self.common_fields = []
        self.load_common_fields()

    def load_common_fields(self):
        """Carga campos comunes"""
        try:
            with open('comparacion_campos.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.common_fields = data.get('campos_comunes', [])
                print(f"✅ {len(self.common_fields)} campos comunes cargados")
        except FileNotFoundError:
            print("⚠️  comparacion_campos.json no encontrado")
            self.common_fields = []

    def connect_cloudpepper(self):
        """Conecta a CloudPepper"""
        print(f"\n📡 Conectando a CloudPepper...")
        self.cp_common = xmlrpc.client.ServerProxy(f"{self.cp_config['url']}/xmlrpc/2/common")
        self.cp_uid = self.cp_common.authenticate(
            self.cp_config['db'],
            self.cp_config['username'],
            self.cp_config['password'],
            {}
        )
        if not self.cp_uid:
            raise Exception("❌ Error de autenticación en CloudPepper")
        self.cp_models = xmlrpc.client.ServerProxy(f"{self.cp_config['url']}/xmlrpc/2/object")
        print(f"   ✅ Conectado como UID: {self.cp_uid}")

    def connect_odoo(self):
        """Conecta a Odoo.com"""
        print(f"\n📡 Conectando a Odoo.com...")
        self.odoo_common = xmlrpc.client.ServerProxy(f"{self.odoo_config['url']}/xmlrpc/2/common")
        self.odoo_uid = self.odoo_common.authenticate(
            self.odoo_config['db'],
            self.odoo_config['username'],
            self.odoo_config['password'],
            {}
        )
        if not self.odoo_uid:
            raise Exception("❌ Error de autenticación en Odoo.com")
        self.odoo_models = xmlrpc.client.ServerProxy(f"{self.odoo_config['url']}/xmlrpc/2/object")
        print(f"   ✅ Conectado como UID: {self.odoo_uid}")

    def search_state_by_name(self, state_name):
        """Busca estado/departamento por nombre"""
        if not state_name:
            return None

        if state_name in self.state_cache:
            return self.state_cache[state_name]

        try:
            state_ids = self.odoo_models.execute_kw(
                self.odoo_config['db'],
                self.odoo_uid,
                self.odoo_config['password'],
                'res.country.state',
                'search',
                [[('name', 'ilike', state_name)]],
                {'limit': 1}
            )

            if state_ids:
                self.state_cache[state_name] = state_ids[0]
                return state_ids[0]
        except Exception as e:
            print(f"   ⚠️  Error buscando estado '{state_name}': {e}")

        return None

    def search_city_by_code_or_name(self, city_code=None, city_name=None, state_id=None):
        """
        Busca ciudad por código (code o l10n_co_edi_code DIVIPOLA) primero, luego por nombre
        """
        cache_key = f"{city_code}_{city_name}_{state_id}"
        if cache_key in self.city_cache:
            return self.city_cache[cache_key]

        try:
            # ESTRATEGIA 1: Buscar por código DIVIPOLA (l10n_co_edi_code)
            if city_code:
                # Intentar primero con l10n_co_edi_code (código DIVIPOLA DIAN)
                try:
                    domain = [('l10n_co_edi_code', '=', city_code)]
                    city_ids = self.odoo_models.execute_kw(
                        self.odoo_config['db'],
                        self.odoo_uid,
                        self.odoo_config['password'],
                        'res.city',
                        'search',
                        [domain],
                        {'limit': 1}
                    )
                    if city_ids:
                        self.city_cache[cache_key] = city_ids[0]
                        print(f"   🔍 Ciudad encontrada por DIVIPOLA: {city_code}")
                        return city_ids[0]
                except:
                    pass

                # Si no encuentra, intentar con code
                try:
                    domain = [('code', '=', city_code)]
                    city_ids = self.odoo_models.execute_kw(
                        self.odoo_config['db'],
                        self.odoo_uid,
                        self.odoo_config['password'],
                        'res.city',
                        'search',
                        [domain],
                        {'limit': 1}
                    )
                    if city_ids:
                        self.city_cache[cache_key] = city_ids[0]
                        print(f"   🔍 Ciudad encontrada por CODE: {city_code}")
                        return city_ids[0]
                except:
                    pass

            # ESTRATEGIA 2: Buscar por nombre + estado
            if city_name:
                domain = [('name', 'ilike', city_name)]
                if state_id:
                    domain.append(('state_id', '=', state_id))

                city_ids = self.odoo_models.execute_kw(
                    self.odoo_config['db'],
                    self.odoo_uid,
                    self.odoo_config['password'],
                    'res.city',
                    'search',
                    [domain],
                    {'limit': 1}
                )

                if city_ids:
                    self.city_cache[cache_key] = city_ids[0]
                    return city_ids[0]

        except Exception as e:
            print(f"   ⚠️  Error buscando ciudad code={city_code}, name={city_name}: {e}")

        return None

    def search_region_by_street2_and_city(self, street2, city_id, city_name=None):
        """
        Busca región/barrio usando street2 (campo de barrio) + nombre de ciudad
        Busca primero por city_id, si no encuentra busca por nombre de ciudad
        """
        if not street2:
            return None

        cache_key = f"street2_{street2}_{city_id}_{city_name}"
        if cache_key in self.region_cache:
            return self.region_cache[cache_key]

        try:
            barrio_name = str(street2).strip()

            if barrio_name and len(barrio_name) > 2:
                # ESTRATEGIA 1: Buscar por nombre de barrio + city_id
                if city_id:
                    domain = [
                        ('name', 'ilike', barrio_name),
                        ('city_id', '=', city_id)
                    ]

                    # Intentar en property.neighborhood primero
                    try:
                        region_ids = self.odoo_models.execute_kw(
                            self.odoo_config['db'],
                            self.odoo_uid,
                            self.odoo_config['password'],
                            'property.neighborhood',
                            'search',
                            [domain],
                            {'limit': 1}
                        )
                        if region_ids:
                            self.region_cache[cache_key] = region_ids[0]
                            print(f"   🔍 Barrio encontrado: {barrio_name} (city_id)")
                            return region_ids[0]
                    except:
                        pass

                    # Si no existe property.neighborhood, intentar property.region
                    try:
                        region_ids = self.odoo_models.execute_kw(
                            self.odoo_config['db'],
                            self.odoo_uid,
                            self.odoo_config['password'],
                            'property.region',
                            'search',
                            [domain],
                            {'limit': 1}
                        )
                        if region_ids:
                            self.region_cache[cache_key] = region_ids[0]
                            print(f"   🔍 Región encontrada: {barrio_name} (city_id)")
                            return region_ids[0]
                    except:
                        pass

                # ESTRATEGIA 2: Buscar por nombre de barrio + nombre de ciudad
                if city_name:
                    # Buscar ciudad con ese nombre para obtener su ID
                    try:
                        city_search = self.odoo_models.execute_kw(
                            self.odoo_config['db'],
                            self.odoo_uid,
                            self.odoo_config['password'],
                            'res.city',
                            'search',
                            [[('name', 'ilike', city_name)]],
                            {'limit': 1}
                        )

                        if city_search:
                            city_found_id = city_search[0]
                            domain = [
                                ('name', 'ilike', barrio_name),
                                ('city_id', '=', city_found_id)
                            ]

                            # Intentar property.neighborhood
                            try:
                                region_ids = self.odoo_models.execute_kw(
                                    self.odoo_config['db'],
                                    self.odoo_uid,
                                    self.odoo_config['password'],
                                    'property.neighborhood',
                                    'search',
                                    [domain],
                                    {'limit': 1}
                                )
                                if region_ids:
                                    self.region_cache[cache_key] = region_ids[0]
                                    print(f"   🔍 Barrio encontrado: {barrio_name} (city_name: {city_name})")
                                    return region_ids[0]
                            except:
                                pass

                            # Intentar property.region
                            try:
                                region_ids = self.odoo_models.execute_kw(
                                    self.odoo_config['db'],
                                    self.odoo_uid,
                                    self.odoo_config['password'],
                                    'property.region',
                                    'search',
                                    [domain],
                                    {'limit': 1}
                                )
                                if region_ids:
                                    self.region_cache[cache_key] = region_ids[0]
                                    print(f"   🔍 Región encontrada: {barrio_name} (city_name: {city_name})")
                                    return region_ids[0]
                            except:
                                pass
                    except:
                        pass

        except Exception as e:
            print(f"   ⚠️  Error buscando barrio: {e}")

        return None

    def search_partner_by_vat_or_name(self, partner_name, vat=None):
        """
        Busca partner primero por VAT (NIT), luego por nombre
        """
        if not partner_name and not vat:
            return None

        # Intentar primero por VAT si existe
        if vat:
            cache_key = f"vat_{vat}"
            if cache_key in self.partner_vat_cache:
                return self.partner_vat_cache[cache_key]

            try:
                partner_ids = self.odoo_models.execute_kw(
                    self.odoo_config['db'],
                    self.odoo_uid,
                    self.odoo_config['password'],
                    'res.partner',
                    'search',
                    [[('vat', '=', vat)]],
                    {'limit': 1}
                )

                if partner_ids:
                    self.partner_vat_cache[cache_key] = partner_ids[0]
                    print(f"   🔍 Partner encontrado por VAT: {vat}")
                    return partner_ids[0]
            except Exception as e:
                print(f"   ⚠️  Error buscando partner por VAT: {e}")

        # Intentar por nombre
        if partner_name:
            if partner_name in self.partner_cache:
                return self.partner_cache[partner_name]

            try:
                partner_ids = self.odoo_models.execute_kw(
                    self.odoo_config['db'],
                    self.odoo_uid,
                    self.odoo_config['password'],
                    'res.partner',
                    'search',
                    [[('name', 'ilike', partner_name)]],
                    {'limit': 1}
                )

                if partner_ids:
                    self.partner_cache[partner_name] = partner_ids[0]
                    return partner_ids[0]
            except Exception as e:
                print(f"   ⚠️  Error buscando partner por nombre: {e}")

        return None

    def get_valid_fields_for_migration(self):
        """Obtiene campos válidos para migración"""
        print("\n🔍 Obteniendo definiciones de campos...")

        target_fields = self.odoo_models.execute_kw(
            self.odoo_config['db'],
            self.odoo_uid,
            self.odoo_config['password'],
            'product.template',
            'fields_get',
            [],
            {'attributes': ['type', 'string', 'readonly', 'store', 'compute', 'related', 'relation']}
        )

        excluded_fields = {
            'id', 'create_date', 'write_date', 'create_uid', 'write_uid',
            '__last_update', 'display_name', 'message_ids', 'message_follower_ids',
            'activity_ids', 'message_attachment_count', 'rating_ids',
            'website_message_ids', 'access_token', 'access_url',
            'image_1920', 'image_1024', 'image_512', 'image_256', 'image_128'
        }

        # Campos relacionales con búsqueda inteligente
        relational_fields_to_search = {
            'state_id', 'city_id', 'region_id',
            'property_owner_id', 'user_id', 'categ_id'
        }

        valid_fields = []
        relational_fields = []

        for field_name in self.common_fields:
            if field_name in excluded_fields:
                continue

            field_def = target_fields.get(field_name)
            if not field_def:
                continue

            if field_def.get('compute') and not field_def.get('store'):
                continue

            if field_def.get('related'):
                continue

            field_type = field_def['type']

            if field_type in ['many2one', 'many2many'] and field_name in relational_fields_to_search:
                relational_fields.append((field_name, field_type, field_def.get('relation')))
                continue

            if field_type in ['many2one', 'many2many', 'one2many']:
                continue

            valid_fields.append(field_name)

        print(f"   ✅ {len(valid_fields)} campos simples válidos")
        print(f"   🔍 {len(relational_fields)} campos relacionales a buscar")

        return valid_fields, relational_fields, target_fields

    def get_cloudpepper_properties(self, limit=None, offset=0):
        """Obtiene propiedades de CloudPepper"""
        print(f"\n📦 Obteniendo propiedades de CloudPepper...")

        domain = [
            ('active', '=', True),
            '|',
            ('type', '=', 'consu'),
            ('type', '=', 'service')
        ]

        total = self.cp_models.execute_kw(
            self.cp_config['db'],
            self.cp_uid,
            self.cp_config['password'],
            'product.template',
            'search_count',
            [domain]
        )

        print(f"   Total propiedades en CloudPepper: {total}")

        search_params = {'order': 'id asc'}
        if limit:
            search_params['limit'] = limit
        if offset:
            search_params['offset'] = offset

        property_ids = self.cp_models.execute_kw(
            self.cp_config['db'],
            self.cp_uid,
            self.cp_config['password'],
            'product.template',
            'search',
            [domain],
            search_params
        )

        print(f"   ✅ {len(property_ids)} propiedades a procesar (offset: {offset})")
        return property_ids

    def read_property_data(self, property_id, fields_to_read):
        """Lee datos en lotes pequeños"""
        batch_size = 50
        all_data = {}

        for i in range(0, len(fields_to_read), batch_size):
            batch_fields = fields_to_read[i:i+batch_size]

            try:
                data = self.cp_models.execute_kw(
                    self.cp_config['db'],
                    self.cp_uid,
                    self.cp_config['password'],
                    'product.template',
                    'read',
                    [property_id],
                    {'fields': batch_fields}
                )

                if data and len(data) > 0:
                    all_data.update(data[0])

            except xmlrpc.client.Fault as e:
                if 'XML-RPC limits' in str(e):
                    for field in batch_fields:
                        try:
                            single_data = self.cp_models.execute_kw(
                                self.cp_config['db'],
                                self.cp_uid,
                                self.cp_config['password'],
                                'product.template',
                                'read',
                                [property_id],
                                {'fields': [field]}
                            )
                            if single_data:
                                all_data.update(single_data[0])
                        except:
                            continue
                else:
                    raise

        return all_data if all_data else None

    def read_relational_data(self, property_id, relational_fields):
        """
        Lee datos relacionales + campos extras para búsqueda inteligente
        También obtiene el CODE de ciudad desde CloudPepper para búsqueda exacta
        """
        fields_to_read = [f[0] for f in relational_fields]

        # Agregar campos necesarios para búsqueda inteligente
        fields_to_read.extend(['street', 'street2', 'zip', 'vat'])

        try:
            data = self.cp_models.execute_kw(
                self.cp_config['db'],
                self.cp_uid,
                self.cp_config['password'],
                'product.template',
                'read',
                [property_id],
                {'fields': fields_to_read}
            )

            result = data[0] if data else {}

            # IMPORTANTE: Obtener el CODE de la ciudad desde res.city en CloudPepper
            if result.get('city_id'):
                city_value = result['city_id']
                if isinstance(city_value, list) and len(city_value) > 0:
                    city_id_cp = city_value[0]

                    # Leer código de ciudad desde CloudPepper
                    # En Odoo 17 (CloudPepper) solo existe 'code'
                    try:
                        city_data = self.cp_models.execute_kw(
                            self.cp_config['db'],
                            self.cp_uid,
                            self.cp_config['password'],
                            'res.city',
                            'read',
                            [city_id_cp],
                            {'fields': ['code']}
                        )
                        if city_data and len(city_data) > 0:
                            result['city_code'] = city_data[0].get('code')
                            if result.get('city_code'):
                                print(f"   📋 City code encontrado: {result['city_code']}")
                    except Exception as e:
                        print(f"   ⚠️  No se pudo leer city code: {e}")

            return result
        except:
            return {}

    def prepare_migration_values(self, source_data, valid_fields, target_fields):
        """Prepara valores para migración"""
        vals = {'type': 'consu'}
        fields_migrated = []
        fields_skipped = []

        for field_name in valid_fields:
            if field_name not in source_data:
                continue

            value = source_data[field_name]

            if value is None or value == '' or (isinstance(value, list) and not value):
                continue

            field_def = target_fields[field_name]
            field_type = field_def['type']

            try:
                if field_type == 'boolean':
                    vals[field_name] = bool(value)
                    fields_migrated.append(field_name)
                elif field_type in ['integer', 'float', 'monetary']:
                    try:
                        if field_type == 'integer':
                            vals[field_name] = int(value) if value else 0
                        else:
                            vals[field_name] = float(value) if value else 0.0
                        fields_migrated.append(field_name)
                    except (ValueError, TypeError):
                        fields_skipped.append(f"{field_name} (conversion error)")
                elif field_type == 'selection':
                    if isinstance(value, str) and value:
                        vals[field_name] = value
                        fields_migrated.append(field_name)
                else:
                    vals[field_name] = value
                    fields_migrated.append(field_name)

            except Exception as e:
                fields_skipped.append(f"{field_name} (error: {str(e)})")
                continue

        return vals, fields_migrated, fields_skipped

    def add_relational_fields_smart(self, vals, relational_data, relational_fields):
        """
        Agrega campos relacionales con búsqueda inteligente
        - Usa VAT para partners
        - Usa street2 + city para barrios (street2 = barrio)
        - Usa código postal para ciudades
        """
        fields_found = []
        fields_not_found = []

        # Extraer datos auxiliares
        street = relational_data.get('street', '')
        street2 = relational_data.get('street2', '')  # street2 normalmente es el barrio
        zip_code = relational_data.get('zip', '')
        vat = relational_data.get('vat', '')

        for field_name, field_type, relation_model in relational_fields:
            if field_name not in relational_data:
                continue

            value = relational_data[field_name]
            if not value:
                continue

            # Extraer nombre
            name = None
            if isinstance(value, list) and len(value) >= 2:
                name = value[1]
                if '(' in name:
                    name = name.split('(')[0].strip()
            elif isinstance(value, str):
                name = value

            if not name:
                continue

            # Buscar según el campo
            found_id = None

            if field_name == 'state_id':
                # Si el nombre está vacío, intentar extraer desde otros campos
                if not name or name == 'False':
                    # Intentar extraer estado desde city_id
                    if 'city_id' in relational_data and relational_data['city_id']:
                        city_value = relational_data['city_id']
                        if isinstance(city_value, list) and len(city_value) >= 2:
                            city_full = city_value[1]
                            # Formato: "MONTERÍA (230017)" -> extraer estado si existe
                            if '-' in city_full:
                                potential_state = city_full.split('-')[-1].strip()
                                if '(' in potential_state:
                                    potential_state = potential_state.split('(')[0].strip()
                                found_id = self.search_state_by_name(potential_state)
                else:
                    found_id = self.search_state_by_name(name)

            elif field_name == 'city_id':
                state_id = vals.get('state_id')

                # Obtener city_code desde relational_data si existe
                city_code = relational_data.get('city_code')

                # Si el nombre está vacío, buscar por código o extraer desde otros campos
                if not name or name == 'False':
                    # Estrategia 1: Buscar por city_code (DIVIPOLA) - MÁS CONFIABLE
                    if city_code:
                        found_id = self.search_city_by_code_or_name(city_code, None, state_id)

                    # Estrategia 2: Extraer de street2 si tiene formato "Barrio - Ciudad"
                    if not found_id and street2 and '-' in street2:
                        parts = street2.split('-')
                        if len(parts) >= 2:
                            potential_city = parts[-1].strip()
                            if len(potential_city) > 2:
                                found_id = self.search_city_by_code_or_name(None, potential_city, state_id)
                else:
                    # Buscar usando city_code si existe, sino usar nombre
                    found_id = self.search_city_by_code_or_name(city_code, name, state_id)

                # IMPORTANTE: Si encontró ciudad, obtener el state_id automáticamente
                if found_id and not vals.get('state_id'):
                    try:
                        city_data = self.odoo_models.execute_kw(
                            self.odoo_config['db'],
                            self.odoo_uid,
                            self.odoo_config['password'],
                            'res.city',
                            'read',
                            [found_id],
                            {'fields': ['state_id']}
                        )
                        if city_data and city_data[0].get('state_id'):
                            state_value = city_data[0]['state_id']
                            if isinstance(state_value, list) and len(state_value) > 0:
                                vals['state_id'] = state_value[0]
                                print(f"   🔍 Departamento obtenido desde ciudad: {state_value[1]}")
                    except:
                        pass

            elif field_name == 'region_id':
                # Buscar por street2 (barrio) + city
                city_id = vals.get('city_id')

                # Obtener nombre de la ciudad desde relational_data
                city_name = None
                if 'city_id' in relational_data and relational_data['city_id']:
                    city_value = relational_data['city_id']
                    if isinstance(city_value, list) and len(city_value) >= 2:
                        city_name = city_value[1]
                        if '(' in city_name:
                            city_name = city_name.split('(')[0].strip()

                # Intentar con street2 primero
                if street2:
                    found_id = self.search_region_by_street2_and_city(street2, city_id, city_name)

                # Si no encuentra con street2, intentar con el nombre del campo region_id
                if not found_id and name:
                    found_id = self.search_region_by_street2_and_city(name, city_id, city_name)

            elif field_name == 'property_owner_id':
                # Buscar por VAT o nombre
                found_id = self.search_partner_by_vat_or_name(name, vat)

            elif field_name == 'user_id':
                found_id = self.search_partner_by_vat_or_name(name, None)

            if found_id:
                if field_type == 'many2one':
                    vals[field_name] = found_id
                elif field_type == 'many2many':
                    vals[field_name] = [(6, 0, [found_id])]
                fields_found.append(f"{field_name} → {name}")
            else:
                fields_not_found.append(f"{field_name} → {name}")

        return fields_found, fields_not_found

    def property_exists_in_target(self, default_code):
        """Verifica si existe"""
        if not default_code:
            return None

        try:
            existing = self.odoo_models.execute_kw(
                self.odoo_config['db'],
                self.odoo_uid,
                self.odoo_config['password'],
                'product.template',
                'search',
                [[('default_code', '=', default_code)]],
                {'limit': 1}
            )
            return existing[0] if existing else None
        except:
            return None

    def create_or_update_property(self, vals, default_code):
        """Crea o actualiza"""
        existing_id = self.property_exists_in_target(default_code)

        try:
            if existing_id:
                update_vals = vals.copy()
                update_vals.pop('default_code', None)

                self.odoo_models.execute_kw(
                    self.odoo_config['db'],
                    self.odoo_uid,
                    self.odoo_config['password'],
                    'product.template',
                    'write',
                    [[existing_id], update_vals]
                )
                return existing_id, 'updated'
            else:
                new_id = self.odoo_models.execute_kw(
                    self.odoo_config['db'],
                    self.odoo_uid,
                    self.odoo_config['password'],
                    'product.template',
                    'create',
                    [vals]
                )
                return new_id, 'created'
        except Exception as e:
            raise Exception(f"Error en create/update: {str(e)}")

    def migrate(self, limit=None, offset=0):
        """Proceso completo"""
        print("\n" + "="*80)
        print("MIGRACIÓN CON BÚSQUEDA INTELIGENTE")
        print("VAT para Partners | Street para Barrios | Zip para Ciudades")
        print("="*80)

        self.connect_cloudpepper()
        self.connect_odoo()

        valid_fields, relational_fields, target_fields = self.get_valid_fields_for_migration()
        property_ids = self.get_cloudpepper_properties(limit=limit, offset=offset)

        stats = {
            'total': len(property_ids),
            'created': 0,
            'updated': 0,
            'failed': 0,
            'total_fields_migrated': 0,
            'total_relational_found': 0,
            'total_relational_not_found': 0,
            'failed_properties': []
        }

        print(f"\n{'='*80}")
        print(f"PROCESANDO {stats['total']} PROPIEDADES")
        print(f"{'='*80}")

        for idx, prop_id in enumerate(property_ids, 1):
            source_data = None
            default_code = 'N/A'

            try:
                source_data = self.read_property_data(prop_id, valid_fields)

                if not source_data:
                    print(f"\n[{idx}/{stats['total']}] ❌ No se pudo leer ID {prop_id}")
                    stats['failed'] += 1
                    continue

                default_code = source_data.get('default_code', 'N/A')
                name = source_data.get('name', 'Sin nombre')

                print(f"\n{'='*80}")
                print(f"[{idx}/{stats['total']}] {default_code} - {name[:50]}")
                print(f"{'='*80}")

                vals, fields_migrated, fields_skipped = self.prepare_migration_values(
                    source_data, valid_fields, target_fields
                )

                relational_data = self.read_relational_data(prop_id, relational_fields)
                fields_found, fields_not_found = self.add_relational_fields_smart(
                    vals, relational_data, relational_fields
                )

                new_id, action = self.create_or_update_property(vals, default_code)

                if action == 'created':
                    stats['created'] += 1
                    print(f"✅ CREADA - ID: {new_id}")
                else:
                    stats['updated'] += 1
                    print(f"✅ ACTUALIZADA - ID: {new_id}")

                stats['total_fields_migrated'] += len(fields_migrated)
                stats['total_relational_found'] += len(fields_found)
                stats['total_relational_not_found'] += len(fields_not_found)

                print(f"   📊 Campos simples: {len(fields_migrated)}")
                print(f"   🔍 Relacionales encontrados: {len(fields_found)}")
                if fields_not_found:
                    print(f"   ⚠️  Relacionales no encontrados: {len(fields_not_found)}")

            except Exception as e:
                print(f"\n[{idx}/{stats['total']}] ❌ ERROR: {str(e)}")
                stats['failed'] += 1
                stats['failed_properties'].append({
                    'id': prop_id,
                    'default_code': default_code,
                    'error': str(e)
                })

        # Reporte final
        print("\n" + "="*80)
        print("REPORTE FINAL")
        print("="*80)
        print(f"   Total Procesadas: {stats['total']}")
        print(f"   ✅ Creadas: {stats['created']}")
        print(f"   ✅ Actualizadas: {stats['updated']}")
        print(f"   ❌ Fallidas: {stats['failed']}")
        print(f"   📊 Campos Simples: {stats['total_fields_migrated']}")
        print(f"   🔍 Relacionales Encontrados: {stats['total_relational_found']}")
        print(f"   ⚠️  Relacionales No Encontrados: {stats['total_relational_not_found']}")

        if stats['total'] > 0 and (stats['created'] + stats['updated']) > 0:
            avg_simple = stats['total_fields_migrated'] / (stats['created'] + stats['updated'])
            avg_relational = stats['total_relational_found'] / (stats['created'] + stats['updated'])
            print(f"   📈 Promedio Campos Simples/Prop: {avg_simple:.1f}")
            print(f"   📈 Promedio Relacionales/Prop: {avg_relational:.1f}")

        if stats['failed_properties']:
            print(f"\n❌ Propiedades Fallidas ({len(stats['failed_properties'])}):")
            for i, prop in enumerate(stats['failed_properties'][:10], 1):
                print(f"   {i}. {prop['default_code']} - {prop['error']}")

        print("="*80)
        return stats


def main():
    print("="*80)
    print("MIGRADOR CON BÚSQUEDA INTELIGENTE")
    print("="*80)

    limit = None
    offset = 0

    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"\n⚙️  Límite: {limit} propiedades")
        except:
            print("\nUSO: python migrate_cloudpepper_busqueda_inteligente.py [limit] [offset]")
            return

    if len(sys.argv) > 2:
        try:
            offset = int(sys.argv[2])
            print(f"⚙️  Offset: {offset}")
        except:
            pass

    migrator = SmartPropertyMigrator()
    migrator.migrate(limit=limit, offset=offset)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script OPTIMIZADO con JSON-RPC
- Pre-carga TODOS los cachés
- Búsqueda de barrio: ciudad de la propiedad → busca nombre en barrios de esa ciudad
- Preparación completa en memoria
- Creación en bloques
"""
import sys
import io
import json
import requests
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class JSONRPCMigrator:
    """Migrador optimizado con JSON-RPC"""

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

        # UIDs de autenticación
        self.cp_uid = None
        self.odoo_uid = None

        # Cachés optimizados
        self.cities = {}                      # {city_id: {'code': ..., 'name': ..., 'state_id': ...}}
        self.city_by_code = {}                # {code: city_id}
        self.regions_by_city = defaultdict(dict)  # {city_id: {region_name: region_id}}
        self.property_types = {}              # {type_name: type_id}
        self.states = {}                      # {state_id: name}

        # Campos comunes
        self.common_fields = []
        self.load_common_fields()

    def load_common_fields(self):
        """Carga campos comunes desde JSON"""
        try:
            with open('comparacion_campos.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.common_fields = data.get('campos_comunes', [])
                print(f"✅ {len(self.common_fields)} campos comunes cargados")
        except FileNotFoundError:
            print("⚠️  comparacion_campos.json no encontrado")
            self.common_fields = []

    def jsonrpc_call(self, config, uid, model, method, args=None, kwargs=None):
        """Llamada JSON-RPC genérica"""
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    config['db'],
                    uid,
                    config['password'],
                    model,
                    method,
                    args,
                    kwargs
                ]
            },
            "id": 1
        }

        response = requests.post(
            f"{config['url']}/jsonrpc",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=300
        )

        result = response.json()
        if 'error' in result:
            raise Exception(f"JSON-RPC Error: {result['error']}")
        
        return result.get('result')

    def authenticate(self, config):
        """Autenticación JSON-RPC"""
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "authenticate",
                "args": [
                    config['db'],
                    config['username'],
                    config['password'],
                    {}
                ]
            },
            "id": 1
        }

        response = requests.post(
            f"{config['url']}/jsonrpc",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        result = response.json()
        if 'error' in result:
            raise Exception(f"Authentication Error: {result['error']}")
        
        uid = result.get('result')
        if not uid:
            raise Exception("Authentication failed: No UID returned")
        
        return uid

    def connect_cloudpepper(self):
        """Conecta a CloudPepper"""
        print(f"\n📡 Conectando a CloudPepper (JSON-RPC)...")
        self.cp_uid = self.authenticate(self.cp_config)
        print(f"   ✅ Conectado como UID: {self.cp_uid}")

    def connect_odoo(self):
        """Conecta a Odoo.com"""
        print(f"\n📡 Conectando a Odoo.com (JSON-RPC)...")
        self.odoo_uid = self.authenticate(self.odoo_config)
        print(f"   ✅ Conectado como UID: {self.odoo_uid}")

    def preload_all_caches(self):
        """PRE-CARGA TODOS LOS CACHÉS"""
        print("\n" + "="*80)
        print("PRE-CARGANDO CACHÉS (JSON-RPC)")
        print("="*80)

        # 1. CIUDADES
        print("\n🏙️  Cargando ciudades...")
        city_ids = self.jsonrpc_call(
            self.odoo_config, self.odoo_uid,
            'res.city', 'search',
            args=[[]]
        )
        
        if city_ids:
            cities_data = self.jsonrpc_call(
                self.odoo_config, self.odoo_uid,
                'res.city', 'read',
                args=[city_ids],
                kwargs={'fields': ['id', 'name', 'code', 'state_id']}
            )
            
            for city in cities_data:
                city_id = city['id']
                city_name = city.get('name', '').strip().lower()
                
                # Extraer state_id
                state_id = None
                if city.get('state_id'):
                    state_id = city['state_id'][0] if isinstance(city['state_id'], list) else city['state_id']
                
                # Guardar en caché principal
                self.cities[city_id] = {
                    'name': city_name,
                    'state_id': state_id,
                    'code': city.get('code')
                }
                

                if city.get('code'):
                    self.city_by_code[city['code']] = city_id
            
            print(f"   ✅ {len(cities_data)} ciudades cargadas")
            print(f"   ✅ {len(self.city_by_code)} códigos indexados")

        # 2. ESTADOS/DEPARTAMENTOS
        print("\n🗺️  Cargando departamentos...")
        try:
            state_ids = self.jsonrpc_call(
                self.odoo_config, self.odoo_uid,
                'res.country.state', 'search',
                args=[[]]
            )
            
            if state_ids:
                states_data = self.jsonrpc_call(
                    self.odoo_config, self.odoo_uid,
                    'res.country.state', 'read',
                    args=[state_ids],
                    kwargs={'fields': ['id', 'name']}
                )
                
                for state in states_data:
                    self.states[state['id']] = state['name']
                
                print(f"   ✅ {len(states_data)} departamentos cargados")
        except Exception as e:
            print(f"   ❌ Error cargando departamentos: {e}")

        # 3. REGIONES/BARRIOS (INDEXADOS POR CIUDAD)
        print("\n🏘️  Cargando regiones/barrios indexados por ciudad...")
        try:
            region_ids = self.jsonrpc_call(
                self.odoo_config, self.odoo_uid,
                'property.region', 'search',
                args=[[]]
            )
            
            if region_ids:
                regions_data = self.jsonrpc_call(
                    self.odoo_config, self.odoo_uid,
                    'property.region', 'read',
                    args=[region_ids],
                    kwargs={'fields': ['id', 'name', 'city_id']}
                )
                
                # Indexar por ciudad
                for region in regions_data:
                    region_id = region['id']
                    region_name = region.get('name', '').strip().lower()
                    
                    if region.get('city_id') and region_name:
                        city_id = region['city_id'][0] if isinstance(region['city_id'], list) else region['city_id']
                        
                        # Indexar: {city_id: {region_name: region_id}}
                        self.regions_by_city[city_id][region_name] = region_id
                
                total_regions = sum(len(regions) for regions in self.regions_by_city.values())
                print(f"   ✅ {len(regions_data)} regiones cargadas")
                print(f"   ✅ {len(self.regions_by_city)} ciudades con regiones")
                print(f"   ✅ {total_regions} combinaciones ciudad-región indexadas")
        except Exception as e:
            print(f"   ❌ Error cargando regiones: {e}")

        # 4. TIPOS DE PROPIEDAD
        print("\n🏠 Cargando tipos de propiedad...")
        try:
            type_ids = self.jsonrpc_call(
                self.odoo_config, self.odoo_uid,
                'property.type', 'search',
                args=[[]]
            )
            
            if type_ids:
                types_data = self.jsonrpc_call(
                    self.odoo_config, self.odoo_uid,
                    'property.type', 'read',
                    args=[type_ids],
                    kwargs={'fields': ['id', 'name']}
                )
                
                for ptype in types_data:
                    type_name = ptype.get('name', '').strip().lower()
                    if type_name:
                        self.property_types[type_name] = ptype['id']
                
                print(f"   ✅ {len(types_data)} tipos cargados")
        except Exception as e:
            print(f"   ❌ Error cargando tipos: {e}")

        print("\n✅ PRE-CARGA COMPLETA")

    def archive_all_properties(self):
        """Archiva todas las propiedades activas"""
        print("\n" + "="*80)
        print("ARCHIVANDO PROPIEDADES EXISTENTES")
        print("="*80)

        active_ids = self.jsonrpc_call(
            self.odoo_config, self.odoo_uid,
            'product.template', 'search',
            args=[[('active', '=', True), ('type', '=', 'consu')]]
        )

        total = len(active_ids)
        print(f"\n📦 Total propiedades activas: {total}")

        if total == 0:
            print("✅ No hay propiedades activas para archivar")
            return 0

        # Archivar en lotes de 200
        batch_size = 200
        archived = 0

        for i in range(0, total, batch_size):
            batch = active_ids[i:i+batch_size]
            try:
                self.jsonrpc_call(
                    self.odoo_config, self.odoo_uid,
                    'product.template', 'write',
                    args=[batch, {'active': False}]
                )
                archived += len(batch)
                print(f"   📁 Archivadas: {archived}/{total}")
            except Exception as e:
                print(f"   ❌ Error archivando lote: {e}")

        print(f"\n✅ Total archivadas: {archived}/{total}")
        return archived

    def get_cloudpepper_properties(self, limit=None):
        """Obtiene IDs de propiedades de CloudPepper"""
        print(f"\n📦 Obteniendo propiedades de CloudPepper...")

        domain = [('active', '=', True), '|', ('type', '=', 'consu'), ('type', '=', 'service')]

        total = self.jsonrpc_call(
            self.cp_config, self.cp_uid,
            'product.template', 'search_count',
            args=[domain]
        )
        print(f"   Total: {total}")

        kwargs = {'order': 'id asc'}
        if limit:
            kwargs['limit'] = limit

        property_ids = self.jsonrpc_call(
            self.cp_config, self.cp_uid,
            'product.template', 'search',
            args=[domain],
            kwargs=kwargs
        )

        print(f"   ✅ {len(property_ids)} a procesar")
        return property_ids

    def read_all_properties_bulk(self, property_ids, valid_fields):
        """Lee TODAS las propiedades en bloques"""
        print(f"\n📖 Leyendo {len(property_ids)} propiedades...")
        
        all_properties = []
        batch_size = 100
        
        # Campos a leer
        read_fields = list(set(valid_fields + ['city_id', 'region_id', 'property_type_id']))
        
        for i in range(0, len(property_ids), batch_size):
            batch_ids = property_ids[i:i+batch_size]
            try:
                properties = self.jsonrpc_call(
                    self.cp_config, self.cp_uid,
                    'product.template', 'read',
                    args=[batch_ids],
                    kwargs={'fields': read_fields}
                )
                all_properties.extend(properties)
                print(f"   📖 Leídas: {len(all_properties)}/{len(property_ids)}")
            except Exception as e:
                print(f"   ⚠️  Error en lote: {e}, leyendo uno por uno...")
                for prop_id in batch_ids:
                    try:
                        prop = self.jsonrpc_call(
                            self.cp_config, self.cp_uid,
                            'product.template', 'read',
                            args=[prop_id],
                            kwargs={'fields': read_fields}
                        )
                        if prop:
                            all_properties.append(prop[0])
                    except:
                        continue
        
        print(f"   ✅ Total leídas: {len(all_properties)}")
        return all_properties

    def enrich_property_data(self, properties):
        """Enriquece datos relacionales"""
        print(f"\n🔍 Enriqueciendo datos relacionales...")
        
        # Recopilar IDs únicos
        city_ids_to_read = set()
        region_ids_to_read = set()
        type_ids_to_read = set()
        
        for prop in properties:
            if prop.get('city_id'):
                city_id = prop['city_id'][0] if isinstance(prop['city_id'], list) else prop['city_id']
                city_ids_to_read.add(city_id)
            
            if prop.get('region_id'):
                region_id = prop['region_id'][0] if isinstance(prop['region_id'], list) else prop['region_id']
                region_ids_to_read.add(region_id)
            
            if prop.get('property_type_id'):
                type_id = prop['property_type_id'][0] if isinstance(prop['property_type_id'], list) else prop['property_type_id']
                type_ids_to_read.add(type_id)
        
        # Leer ciudades
        city_data = {}
        if city_ids_to_read:
            print(f"   🏙️  Leyendo {len(city_ids_to_read)} ciudades...")
            try:
                cities = self.jsonrpc_call(
                    self.cp_config, self.cp_uid,
                    'res.city', 'read',
                    args=[list(city_ids_to_read)],
                    kwargs={'fields': ['id', 'code', 'name']}
                )
                for city in cities:
                    city_data[city['id']] = {
                        'code': city.get('code'),
                        'name': city.get('name', '').strip().lower()
                    }
            except Exception as e:
                print(f"   ⚠️  Error leyendo ciudades: {e}")
        
        # Leer regiones
        region_data = {}
        if region_ids_to_read:
            print(f"   🏘️  Leyendo {len(region_ids_to_read)} regiones...")
            try:
                regions = self.jsonrpc_call(
                    self.cp_config, self.cp_uid,
                    'property.region', 'read',
                    args=[list(region_ids_to_read)],
                    kwargs={'fields': ['id', 'name']}
                )
                for region in regions:
                    region_data[region['id']] = region.get('name', '').strip().lower()
            except Exception as e:
                print(f"   ⚠️  Error leyendo regiones: {e}")
        
        # Leer tipos
        type_data = {}
        if type_ids_to_read:
            print(f"   🏠 Leyendo {len(type_ids_to_read)} tipos...")
            try:
                types = self.jsonrpc_call(
                    self.cp_config, self.cp_uid,
                    'property.type', 'read',
                    args=[list(type_ids_to_read)],
                    kwargs={'fields': ['id', 'name']}
                )
                for ptype in types:
                    type_data[ptype['id']] = ptype.get('name', '').strip().lower()
            except Exception as e:
                print(f"   ⚠️  Error leyendo tipos: {e}")
        
        # Enriquecer propiedades
        for prop in properties:
            # Ciudad
            if prop.get('city_id'):
                city_id = prop['city_id'][0] if isinstance(prop['city_id'], list) else prop['city_id']
                if city_id in city_data:
                    prop['city_code'] = city_data[city_id]['code']
                    prop['city_name'] = city_data[city_id]['name']
                    prop['_city_id_value'] = city_id  # Guardar ID para búsqueda
            
            # Región
            if prop.get('region_id'):
                region_id = prop['region_id'][0] if isinstance(prop['region_id'], list) else prop['region_id']
                if region_id in region_data:
                    prop['region_name'] = region_data[region_id]
            
            # Tipo
            if prop.get('property_type_id'):
                type_id = prop['property_type_id'][0] if isinstance(prop['property_type_id'], list) else prop['property_type_id']
                if type_id in type_data:
                    prop['property_type_name'] = type_data[type_id]
        
        print(f"   ✅ Datos enriquecidos")

    def find_region_id(self, region_name, city_id):
        """
        Busca región por nombre EN LA CIUDAD especificada
        LÓGICA: Toma la ciudad de la propiedad → busca el nombre del barrio en esa ciudad
        """
        if not region_name or not city_id:
            return None
        
        region_name_clean = region_name.strip().lower()
        
        # Buscar en regiones de esta ciudad específica
        if city_id in self.regions_by_city:
            return self.regions_by_city[city_id].get(region_name_clean)
        
        return None

    def prepare_all_values(self, properties, valid_fields, target_fields):
        """Prepara TODOS los valores en memoria"""
        print(f"\n⚙️  Preparando valores para {len(properties)} propiedades...")
        
        prepared = []
        failed = []
        stats = {
            'with_city': 0,
            'with_region': 0,
            'with_type': 0,
            'region_not_found': 0
        }
        
        for idx, source_data in enumerate(properties, 1):
            try:
                vals = {'type': 'consu', 'active': True}
                migrated = []
                
                # Validar nombre (obligatorio)
                name = source_data.get('name', '').strip()
                if not name:
                    code = source_data.get('default_code', 'N/A')
                    name = f"Propiedad {code}"
                vals['name'] = name
                migrated.append('name')
                
                # Procesar campos simples
                for field in valid_fields:
                    if field in ['name', 'city_id', 'region_id', 'property_type_id', 'state_id']:
                        continue
                    
                    if field not in source_data:
                        continue
                    
                    value = source_data[field]
                    if value is None or value == '' or (isinstance(value, list) and not value):
                        continue
                    
                    field_type = target_fields[field]['type']
                    
                    try:
                        if field_type == 'boolean':
                            vals[field] = bool(value)
                        elif field_type == 'integer':
                            vals[field] = int(value) if value else 0
                        elif field_type in ['float', 'monetary']:
                            vals[field] = float(value) if value else 0.0
                        elif field_type == 'selection':
                            if isinstance(value, str) and value:
                                vals[field] = value
                        else:
                            vals[field] = value
                        migrated.append(field)
                    except:
                        continue
                
                # PROCESAR CIUDAD
                city_code = source_data.get('city_code')
                city_id_found = None
                
                if city_code and city_code in self.city_by_code:
                    city_id_found = self.city_by_code[city_code]
                    vals['city_id'] = city_id_found
                    migrated.append('city_id')
                    stats['with_city'] += 1
                    
                    # Obtener state_id
                    if city_id_found in self.cities:
                        state_id = self.cities[city_id_found]['state_id']
                        if state_id:
                            vals['state_id'] = state_id
                            migrated.append('state_id')
                
                # PROCESAR REGIÓN/BARRIO
                # LÓGICA: Usa la ciudad de la propiedad → busca nombre del barrio en esa ciudad
                region_name = source_data.get('region_name')
                if not region_name:
                    region_name = source_data.get('street2', '').strip()
                
                if region_name and city_id_found:
                    # Buscar región en LA CIUDAD de la propiedad
                    region_id = self.find_region_id(region_name, city_id_found)
                    
                    if region_id:
                        vals['region_id'] = region_id
                        migrated.append('region_id')
                        stats['with_region'] += 1
                    else:
                        stats['region_not_found'] += 1
                        # Debug info
                        if city_id_found in self.cities:
                            city_name = self.cities[city_id_found]['name']
                            if idx <= 5:  # Solo primeros 5 para no saturar
                                print(f"   ⚠️  Barrio '{region_name}' no encontrado en {city_name}")
                
                # PROCESAR TIPO DE PROPIEDAD
                property_type_name = source_data.get('property_type_name')
                if property_type_name:
                    type_name_clean = property_type_name.strip().lower()
                    if type_name_clean in self.property_types:
                        vals['property_type_id'] = self.property_types[type_name_clean]
                        migrated.append('property_type_id')
                        stats['with_type'] += 1
                
                prepared.append({
                    'vals': vals,
                    'migrated': migrated,
                    'source_id': source_data.get('id'),
                    'code': source_data.get('default_code', 'N/A'),
                    'name': name[:50]
                })
                
            except Exception as e:
                failed.append({
                    'id': source_data.get('id'),
                    'error': str(e)
                })
        
        print(f"   ✅ Preparadas: {len(prepared)}")
        print(f"   ⚠️  Fallidas: {len(failed)}")
        print(f"\n📊 Estadísticas:")
        print(f"   🏙️  Con ciudad: {stats['with_city']}")
        print(f"   🏘️  Con barrio: {stats['with_region']}")
        print(f"   🏠 Con tipo: {stats['with_type']}")
        print(f"   ⚠️  Barrios no encontrados: {stats['region_not_found']}")
        
        return prepared, failed

    def create_bulk(self, prepared_data):
        """Crea propiedades EN BLOQUES usando JSON-RPC"""
        print(f"\n🚀 Creando {len(prepared_data)} propiedades en bloques...")
        
        batch_size = 50
        created = 0
        failed = []
        total_fields = 0
        
        for i in range(0, len(prepared_data), batch_size):
            batch = prepared_data[i:i+batch_size]
            vals_list = [item['vals'] for item in batch]
            
            try:
                # Crear en bloque
                new_ids = self.jsonrpc_call(
                    self.odoo_config, self.odoo_uid,
                    'product.template', 'create',
                    args=[vals_list]
                )
                
                created += len(new_ids) if isinstance(new_ids, list) else 1
                for item in batch:
                    total_fields += len(item['migrated'])
                
                print(f"   ✅ Creadas: {created}/{len(prepared_data)}")
                
            except Exception as e:
                print(f"   ⚠️  Error en bloque: {e}, creando uno por uno...")
                # Fallback: crear uno por uno
                for item in batch:
                    try:
                        new_id = self.jsonrpc_call(
                            self.odoo_config, self.odoo_uid,
                            'product.template', 'create',
                            args=[item['vals']]
                        )
                        created += 1
                        total_fields += len(item['migrated'])
                    except Exception as e2:
                        failed.append({
                            'id': item['source_id'],
                            'code': item['code'],
                            'error': str(e2)
                        })
        
        return created, failed, total_fields

    def get_valid_fields(self):
        """Obtiene campos válidos para migración"""
        print("\n🔍 Obteniendo campos válidos...")

        target_fields = self.jsonrpc_call(
            self.odoo_config, self.odoo_uid,
            'product.template', 'fields_get',
            args=[],
            kwargs={'attributes': ['type', 'string', 'readonly', 'store', 'compute', 'related']}
        )

        excluded = {
            'id', 'create_date', 'write_date', 'create_uid', 'write_uid',
            '__last_update', 'display_name', 'message_ids', 'message_follower_ids',
            'activity_ids', 'message_attachment_count', 'rating_ids',
            'website_message_ids', 'access_token', 'access_url',
            'image_1920', 'image_1024', 'image_512', 'image_256', 'image_128'
        }

        valid_fields = []
        for field_name in self.common_fields:
            if field_name in excluded:
                continue
            field_def = target_fields.get(field_name)
            if not field_def:
                continue
            if field_def.get('compute') and not field_def.get('store'):
                continue
            if field_def.get('related'):
                continue
            if field_def['type'] in ['many2one', 'many2many', 'one2many']:
                continue
            valid_fields.append(field_name)

        print(f"   ✅ {len(valid_fields)} campos válidos")
        return valid_fields, target_fields

    def migrate(self, limit=None, archive_first=True):
        """Proceso completo OPTIMIZADO con JSON-RPC"""
        print("\n" + "="*80)
        print("MIGRACIÓN OPTIMIZADA: JSON-RPC + BLOQUES")
        print("="*80)

        # 1. Conectar
        self.connect_cloudpepper()
        self.connect_odoo()

        # 2. Pre-cargar cachés
        self.preload_all_caches()

        # 3. Archivar existentes
        archived = 0
        if archive_first:
            archived = self.archive_all_properties()

        # 4. Obtener campos válidos
        valid_fields, target_fields = self.get_valid_fields()

        # 5. Obtener IDs de propiedades
        property_ids = self.get_cloudpepper_properties(limit)

        # 6. Leer TODAS en bloques
        properties = self.read_all_properties_bulk(property_ids, valid_fields)

        # 7. Enriquecer datos relacionales
        self.enrich_property_data(properties)

        # 8. Preparar TODOS los valores
        prepared_data, prep_failed = self.prepare_all_values(properties, valid_fields, target_fields)

        # 9. Crear EN BLOQUES
        created, create_failed, total_fields = self.create_bulk(prepared_data)

        # 10. Reporte final
        print("\n" + "="*80)
        print("REPORTE FINAL")
        print("="*80)
        print(f"   📁 Archivadas: {archived}")
        print(f"   ✅ Creadas: {created}/{len(properties)}")
        print(f"   ❌ Fallidas preparación: {len(prep_failed)}")
        print(f"   ❌ Fallidas creación: {len(create_failed)}")
        print(f"   📊 Campos migrados: {total_fields}")
        if created > 0:
            print(f"   📈 Promedio: {total_fields/created:.1f} campos/propiedad")

        if create_failed:
            print(f"\n❌ Errores de creación ({len(create_failed[:5])}):")
            for item in create_failed[:5]:
                print(f"   {item['code']}: {item['error'][:60]}")

        print("="*80)


def main():
    print("="*80)
    print("MIGRACIÓN OPTIMIZADA - JSON-RPC")
    print("="*80)

    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"\n⚙️  Límite: {limit}")
        except:
            print("\nUSO: python migrate_jsonrpc.py [limit]")
            return

    migrator = JSONRPCMigrator()
    migrator.migrate(limit=limit, archive_first=True)


if __name__ == "__main__":
    main()

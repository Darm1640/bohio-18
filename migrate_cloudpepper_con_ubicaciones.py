#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migración COMPLETA de propiedades CloudPepper -> Odoo 18
INCLUYE búsqueda de ubicaciones (state, city, region, neighborhood) por nombre
"""
import sys
import io
import json
import xmlrpc.client
from datetime import datetime

# Configurar salida UTF-8 para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class CompletePropertyMigratorWithLocations:
    """Migrador completo con búsqueda de ubicaciones por nombre"""

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

        # Cachés para búsquedas
        self.state_cache = {}  # name -> id
        self.city_cache = {}  # name -> id
        self.region_cache = {}  # name -> id
        self.neighborhood_cache = {}  # name -> id
        self.partner_cache = {}  # name -> id

        # Cargar campos comunes
        self.common_fields = []
        self.load_common_fields()

    def load_common_fields(self):
        """Carga los 415 campos comunes desde comparacion_campos.json"""
        try:
            with open('comparacion_campos.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.common_fields = data.get('campos_comunes', [])
                print(f"✅ {len(self.common_fields)} campos comunes cargados")
        except FileNotFoundError:
            print("⚠️  comparacion_campos.json no encontrado, usando autodiscovery")
            self.common_fields = []

    def connect_cloudpepper(self):
        """Conecta a CloudPepper"""
        print(f"\n📡 Conectando a CloudPepper...")
        print(f"   URL: {self.cp_config['url']}")

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
        print(f"   URL: {self.odoo_config['url']}")

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
        """Busca un estado/departamento por nombre en Odoo.com"""
        if not state_name:
            return None

        # Verificar caché
        if state_name in self.state_cache:
            return self.state_cache[state_name]

        try:
            # Buscar en res.country.state
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

    def search_city_by_name(self, city_name, state_id=None):
        """Busca una ciudad por nombre en Odoo.com"""
        if not city_name:
            return None

        cache_key = f"{city_name}_{state_id}" if state_id else city_name

        # Verificar caché
        if cache_key in self.city_cache:
            return self.city_cache[cache_key]

        try:
            # Buscar en res.city
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
            print(f"   ⚠️  Error buscando ciudad '{city_name}': {e}")

        return None

    def search_region_by_name(self, region_name, city_id=None):
        """Busca una región/sector por nombre en Odoo.com"""
        if not region_name:
            return None

        cache_key = f"{region_name}_{city_id}" if city_id else region_name

        # Verificar caché
        if cache_key in self.region_cache:
            return self.region_cache[cache_key]

        try:
            # Buscar en property.region
            domain = [('name', 'ilike', region_name)]
            if city_id:
                domain.append(('city_id', '=', city_id))

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
                return region_ids[0]

        except Exception as e:
            print(f"   ⚠️  Error buscando región '{region_name}': {e}")

        return None

    def search_category_by_name(self, category_name):
        """Busca una categoría de producto por nombre en Odoo.com"""
        if not category_name:
            return None

        # Verificar caché
        if category_name in self.neighborhood_cache:  # Reusar caché
            return self.neighborhood_cache[category_name]

        try:
            # Buscar en product.category
            categ_ids = self.odoo_models.execute_kw(
                self.odoo_config['db'],
                self.odoo_uid,
                self.odoo_config['password'],
                'product.category',
                'search',
                [[('name', 'ilike', category_name)]],
                {'limit': 1}
            )

            if categ_ids:
                self.neighborhood_cache[category_name] = categ_ids[0]
                return categ_ids[0]

        except Exception as e:
            print(f"   ⚠️  Error buscando categoría '{category_name}': {e}")

        return None

    def search_partner_by_name(self, partner_name):
        """Busca un partner/contacto por nombre en Odoo.com"""
        if not partner_name:
            return None

        # Verificar caché
        if partner_name in self.partner_cache:
            return self.partner_cache[partner_name]

        try:
            # Buscar en res.partner
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
            print(f"   ⚠️  Error buscando partner '{partner_name}': {e}")

        return None

    def get_valid_fields_for_migration(self):
        """
        Obtiene lista de campos válidos para migración
        Excluye campos computados, readonly, y campos especiales
        """
        print("\n🔍 Obteniendo definiciones de campos...")

        # Obtener todos los campos del target
        target_fields = self.odoo_models.execute_kw(
            self.odoo_config['db'],
            self.odoo_uid,
            self.odoo_config['password'],
            'product.template',
            'fields_get',
            [],
            {'attributes': ['type', 'string', 'readonly', 'store', 'compute', 'related', 'relation']}
        )

        # Campos a excluir (computed, related, readonly system fields)
        excluded_fields = {
            'id', 'create_date', 'write_date', 'create_uid', 'write_uid',
            '__last_update', 'display_name', 'message_ids', 'message_follower_ids',
            'activity_ids', 'message_attachment_count', 'rating_ids',
            'website_message_ids', 'access_token', 'access_url',
            'image_1920', 'image_1024', 'image_512', 'image_256', 'image_128'
        }

        # Campos relacionales que vamos a buscar por nombre
        # NOTA: En CloudPepper region_id = Barrio (region.region)
        # En Odoo.com hay property.neighborhood Y property.region
        relational_fields_to_search = {
            'state_id',  # res.country.state - Departamento
            'city_id',   # res.city - Ciudad
            'region_id', # region.region (CP) -> property.region (Odoo18) - Barrio/Sector
            'property_owner_id',  # res.partner - Propietario
            'user_id',   # res.users - Usuario responsable
            'categ_id'   # product.category - Categoría
        }

        # Filtrar campos válidos
        valid_fields = []
        relational_fields = []

        for field_name in self.common_fields:
            if field_name in excluded_fields:
                continue

            field_def = target_fields.get(field_name)
            if not field_def:
                continue

            # Excluir campos computados sin store
            if field_def.get('compute') and not field_def.get('store'):
                continue

            # Excluir campos related
            if field_def.get('related'):
                continue

            field_type = field_def['type']

            # Si es relacional y está en la lista de búsqueda, agregarlo a relational_fields
            if field_type in ['many2one', 'many2many'] and field_name in relational_fields_to_search:
                relational_fields.append((field_name, field_type, field_def.get('relation')))
                continue

            # Excluir otros campos many2one/many2many
            if field_type in ['many2one', 'many2many']:
                continue

            # Excluir one2many
            if field_type == 'one2many':
                continue

            valid_fields.append(field_name)

        print(f"   ✅ {len(valid_fields)} campos simples válidos")
        print(f"   🔍 {len(relational_fields)} campos relacionales a buscar")
        print(f"   ⏭️  {len(self.common_fields) - len(valid_fields) - len(relational_fields)} campos excluidos")

        return valid_fields, relational_fields, target_fields

    def get_cloudpepper_properties(self, limit=None, offset=0):
        """Obtiene propiedades de CloudPepper"""
        print(f"\n📦 Obteniendo propiedades de CloudPepper...")

        # Buscar todas las propiedades activas
        domain = [
            ('active', '=', True),
            '|',
            ('type', '=', 'consu'),
            ('type', '=', 'service')
        ]

        # Contar total
        total = self.cp_models.execute_kw(
            self.cp_config['db'],
            self.cp_uid,
            self.cp_config['password'],
            'product.template',
            'search_count',
            [domain]
        )

        print(f"   Total propiedades en CloudPepper: {total}")

        # Aplicar límites
        search_params = {'order': 'id asc'}
        if limit:
            search_params['limit'] = limit
        if offset:
            search_params['offset'] = offset

        # Buscar IDs
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
        """Lee datos completos de una propiedad en lotes pequeños"""
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
                    # Intentar campo por campo
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
        """Lee datos relacionales que necesitamos para buscar por nombre"""
        fields_to_read = [f[0] for f in relational_fields]

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
            return data[0] if data else {}
        except:
            return {}

    def prepare_migration_values(self, source_data, valid_fields, target_fields):
        """Prepara valores para migración (campos simples)"""
        vals = {'type': 'consu'}
        fields_migrated = []
        fields_skipped = []

        for field_name in valid_fields:
            if field_name not in source_data:
                continue

            value = source_data[field_name]

            # Saltar valores vacíos
            if value is None or value == '' or (isinstance(value, list) and not value):
                continue

            field_def = target_fields[field_name]
            field_type = field_def['type']

            try:
                # Boolean
                if field_type == 'boolean':
                    vals[field_name] = bool(value)
                    fields_migrated.append(field_name)

                # Integer/Float
                elif field_type in ['integer', 'float', 'monetary']:
                    try:
                        if field_type == 'integer':
                            vals[field_name] = int(value) if value else 0
                        else:
                            vals[field_name] = float(value) if value else 0.0
                        fields_migrated.append(field_name)
                    except (ValueError, TypeError):
                        fields_skipped.append(f"{field_name} (conversion error)")

                # Selection
                elif field_type == 'selection':
                    if isinstance(value, str) and value:
                        vals[field_name] = value
                        fields_migrated.append(field_name)

                # Campos simples (char, text, date, datetime)
                else:
                    vals[field_name] = value
                    fields_migrated.append(field_name)

            except Exception as e:
                fields_skipped.append(f"{field_name} (error: {str(e)})")
                continue

        return vals, fields_migrated, fields_skipped

    def add_relational_fields(self, vals, relational_data, relational_fields):
        """Agrega campos relacionales buscando por nombre"""
        fields_found = []
        fields_not_found = []

        for field_name, field_type, relation_model in relational_fields:
            if field_name not in relational_data:
                continue

            value = relational_data[field_name]
            if not value:
                continue

            # Extraer nombre del valor [id, name]
            name = None
            if isinstance(value, list) and len(value) >= 2:
                name = value[1]
                # Limpiar nombre - quitar códigos entre paréntesis
                if '(' in name:
                    name = name.split('(')[0].strip()
            elif isinstance(value, str):
                name = value

            if not name:
                continue

            # Buscar según el tipo de campo
            found_id = None

            if field_name == 'state_id':
                found_id = self.search_state_by_name(name)
            elif field_name == 'city_id':
                state_id = vals.get('state_id')
                found_id = self.search_city_by_name(name, state_id)
            elif field_name == 'region_id':
                # region_id en CloudPepper = Barrio/Sector
                city_id = vals.get('city_id')
                found_id = self.search_region_by_name(name, city_id)
            elif field_name == 'categ_id':
                found_id = self.search_category_by_name(name)
            elif field_name in ['property_owner_id', 'user_id']:
                found_id = self.search_partner_by_name(name)

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
        """Verifica si la propiedad ya existe en el target"""
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
        except Exception as e:
            print(f"   ⚠️  Error verificando existencia: {e}")
            return None

    def create_or_update_property(self, vals, default_code):
        """Crea o actualiza una propiedad"""
        existing_id = self.property_exists_in_target(default_code)

        try:
            if existing_id:
                # Actualizar
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
                # Crear
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
        """Proceso completo de migración"""
        print("\n" + "="*80)
        print("MIGRACIÓN COMPLETA CLOUDPEPPER -> ODOO 18")
        print("CON BÚSQUEDA DE UBICACIONES POR NOMBRE")
        print("="*80)

        # Conectar
        self.connect_cloudpepper()
        self.connect_odoo()

        # Obtener campos
        valid_fields, relational_fields, target_fields = self.get_valid_fields_for_migration()

        # Obtener propiedades
        property_ids = self.get_cloudpepper_properties(limit=limit, offset=offset)

        # Estadísticas
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

        # Procesar
        print(f"\n{'='*80}")
        print(f"PROCESANDO {stats['total']} PROPIEDADES")
        print(f"{'='*80}")

        for idx, prop_id in enumerate(property_ids, 1):
            source_data = None
            default_code = 'N/A'

            try:
                # Leer datos simples
                source_data = self.read_property_data(prop_id, valid_fields)

                if not source_data:
                    print(f"\n[{idx}/{stats['total']}] ❌ No se pudo leer propiedad ID {prop_id}")
                    stats['failed'] += 1
                    continue

                default_code = source_data.get('default_code', 'N/A')
                name = source_data.get('name', 'Sin nombre')

                print(f"\n{'='*80}")
                print(f"[{idx}/{stats['total']}] {default_code} - {name[:50]}")
                print(f"{'='*80}")

                # Preparar valores simples
                vals, fields_migrated, fields_skipped = self.prepare_migration_values(
                    source_data, valid_fields, target_fields
                )

                # Leer y agregar campos relacionales
                relational_data = self.read_relational_data(prop_id, relational_fields)
                fields_found, fields_not_found = self.add_relational_fields(
                    vals, relational_data, relational_fields
                )

                # Crear o actualizar
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

                # Resumen
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
            if len(stats['failed_properties']) > 10:
                print(f"   ... y {len(stats['failed_properties']) - 10} más")

        print("="*80)
        print("MIGRACIÓN COMPLETADA")
        print("="*80)

        return stats


def main():
    """Función principal"""
    print("="*80)
    print("MIGRADOR COMPLETO CON BÚSQUEDA DE UBICACIONES")
    print("="*80)

    limit = None
    offset = 0

    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"\n⚙️  Límite: {limit} propiedades")
        except:
            print("\nUSO:")
            print("   python migrate_cloudpepper_con_ubicaciones.py [limit] [offset]")
            return

    if len(sys.argv) > 2:
        try:
            offset = int(sys.argv[2])
            print(f"⚙️  Offset: {offset}")
        except:
            pass

    # Ejecutar
    migrator = CompletePropertyMigratorWithLocations()
    migrator.migrate(limit=limit, offset=offset)


if __name__ == "__main__":
    main()

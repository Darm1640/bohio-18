#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script INTELIGENTE para migrar propiedades de Odoo 17 → Odoo 18
- Solo migra campos que EXISTEN en ambas bases
- Omite campos sin homólogo
- Incluye TODOS los campos booleanos
"""
import xmlrpc.client
import sys
import io
import json
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración Odoo 17 (ORIGEN)
ODOO17 = {
    'name': 'Odoo 17 - CloudPepper',
    'url': 'https://inmobiliariabohio.cloudpepper.site',
    'db': 'inmobiliariabohio.cloudpepper.site',
    'username': 'admin',
    'password': 'admin'
}

# Configuración Odoo 18 (DESTINO)
ODOO18 = {
    'name': 'Odoo 18 - Odoo.com',
    'url': 'https://darm1640-bohio-18.odoo.com',
    'db': 'darm1640-bohio-18-main-24081960',
    'username': 'admin',
    'password': '123456'
}


class SmartPropertyMigrator:
    """Migrador inteligente que detecta campos disponibles automáticamente"""

    def __init__(self, source_config, target_config):
        self.source = source_config
        self.target = target_config
        self.source_uid = None
        self.target_uid = None
        self.source_models = None
        self.target_models = None

        # Campos disponibles en cada DB
        self.source_fields = {}
        self.target_fields = {}
        self.common_fields = []
        self.location_mapping = {}

        # Cache para IDs
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
        }

    def connect_source(self):
        """Conectar a Odoo origen"""
        try:
            print(f"\nConectando a ORIGEN: {self.source['name']}")
            common = xmlrpc.client.ServerProxy(f"{self.source['url']}/xmlrpc/2/common")
            self.source_uid = common.authenticate(
                self.source['db'], self.source['username'], self.source['password'], {}
            )
            if not self.source_uid:
                return False
            print(f"   Conectado (UID: {self.source_uid})")
            self.source_models = xmlrpc.client.ServerProxy(f"{self.source['url']}/xmlrpc/2/object")
            return True
        except Exception as e:
            print(f"   Error: {e}")
            return False

    def connect_target(self):
        """Conectar a Odoo destino"""
        try:
            print(f"\nConectando a DESTINO: {self.target['name']}")
            common = xmlrpc.client.ServerProxy(f"{self.target['url']}/xmlrpc/2/common")
            self.target_uid = common.authenticate(
                self.target['db'], self.target['username'], self.target['password'], {}
            )
            if not self.target_uid:
                return False
            print(f"   Conectado (UID: {self.target_uid})")
            self.target_models = xmlrpc.client.ServerProxy(f"{self.target['url']}/xmlrpc/2/object")
            return True
        except Exception as e:
            print(f"   Error: {e}")
            return False

    def discover_fields(self):
        """Descubrir campos disponibles en ambas bases"""
        print("\n" + "="*80)
        print("DESCUBRIENDO CAMPOS DISPONIBLES")
        print("="*80)

        # Obtener campos de origen
        print("\nObteniendo campos de ORIGEN...")
        self.source_fields = self.source_models.execute_kw(
            self.source['db'], self.source_uid, self.source['password'],
            'product.template', 'fields_get',
            [], {'attributes': ['type', 'relation']}
        )
        print(f"   Total campos en origen: {len(self.source_fields)}")

        # Obtener campos de destino
        print("\nObteniendo campos de DESTINO...")
        self.target_fields = self.target_models.execute_kw(
            self.target['db'], self.target_uid, self.target['password'],
            'product.template', 'fields_get',
            [], {'attributes': ['type', 'relation']}
        )
        print(f"   Total campos en destino: {len(self.target_fields)}")

        # EXCLUIR campos problemáticos que causan XML-RPC overflow
        problematic_fields = [
            'property_filters_config',  # JSON grande
            'property_search_vector',   # Text muy largo
            'message_ids',              # One2many con muchos registros
            'activity_ids',             # One2many con muchos registros
            'message_follower_ids',     # Many2many grande
            'website_message_ids',
        ]

        for field in problematic_fields:
            if field in self.source_fields:
                del self.source_fields[field]
            if field in self.target_fields:
                del self.target_fields[field]

        print(f"   Campos problemáticos excluidos: {len(problematic_fields)}")

        # Encontrar campos comunes (con mapeo de ubicación)
        print("\nAnalizando campos comunes...")

        # Mapeo de ubicación especial (SIN CAMBIO - mismos nombres en ambas DBs!)
        self.location_mapping = {
            'state_id': 'state_id',      # Sin cambio
            'city_id': 'city_id',        # Sin cambio
            'region_id': 'region_id',    # Sin cambio
        }

        # Campos comunes directos (mismo nombre)
        for field_name in self.source_fields:
            if field_name in self.target_fields:
                self.common_fields.append((field_name, field_name))

        # Agregar mapeo de ubicación
        for source, target in self.location_mapping.items():
            if source in self.source_fields and target in self.target_fields:
                if (source, source) in self.common_fields:
                    self.common_fields.remove((source, source))
                self.common_fields.append((source, target))

        print(f"   Campos comunes encontrados: {len(self.common_fields)}")

        # Filtrar solo campos relevantes para propiedades
        property_keywords = [
            'property', 'bedroom', 'bathroom', 'garage', 'area', 'floor', 'unit',
            'price', 'rent', 'rental', 'sale', 'type', 'status', 'state', 'city',
            'region', 'neighborhood', 'street', 'latitude', 'longitude', 'zip',
            'auxiliary', 'service', 'laundry', 'green', 'sports', 'solar', 'marble',
            'door', 'building', 'apartment', 'project', 'notarial', 'tax',
            'consignee', 'date', 'description', 'front', 'electrical', 'keys',
            'license', 'real_estate', 'sign'
        ]

        relevant_common = []
        for source_field, target_field in self.common_fields:
            # Incluir siempre campos básicos
            if source_field in ['name', 'default_code', 'active', 'is_property',
                               'description', 'description_sale', 'type']:
                relevant_common.append((source_field, target_field))
                continue

            # Incluir si coincide con keywords
            field_lower = source_field.lower()
            if any(kw in field_lower for kw in property_keywords):
                relevant_common.append((source_field, target_field))

        self.common_fields = relevant_common
        print(f"   Campos relevantes para propiedades: {len(self.common_fields)}")

        # Mostrar por tipo
        by_type = {}
        for source, target in self.common_fields:
            field_type = self.source_fields[source].get('type', 'unknown')
            if field_type not in by_type:
                by_type[field_type] = []
            by_type[field_type].append(source)

        print("\nCampos por tipo:")
        for ftype, fields in sorted(by_type.items()):
            print(f"   {ftype}: {len(fields)}")
            if ftype == 'boolean':
                print(f"      Booleanos: {', '.join(sorted(fields))}")

    def clean_state_name(self, state_data):
        """Limpiar nombre de departamento"""
        if not state_data:
            return None

        state_name = state_data[1] if isinstance(state_data, (list, tuple)) else state_data

        # Limpiar formato "Córdoba CO (CO)" -> "Córdoba"
        if '(' in state_name:
            parts = state_name.split('(')
            state_name = parts[0].strip()

        # Eliminar código de departamento si existe
        if state_name.endswith(' CO'):
            state_name = state_name[:-3].strip()

        return state_name

    def clean_city_name(self, city_data):
        """Limpiar nombre de ciudad"""
        if not city_data:
            return None

        city_name = city_data[1] if isinstance(city_data, (list, tuple)) else city_data

        # Limpiar formato "MONTERÍA (230017)" -> "MONTERÍA"
        if '(' in city_name:
            city_name = city_name.split('(')[0].strip()

        return city_name

    def get_or_create_state(self, state_data):
        """Obtener departamento en destino"""
        state_name = self.clean_state_name(state_data)
        if not state_name:
            return None

        if state_name in self.cache['states']:
            return self.cache['states'][state_name]

        try:
            # Buscar por nombre limpio
            state_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'res.country.state', 'search',
                [[('name', 'ilike', state_name)]]
            )

            if state_ids:
                self.cache['states'][state_name] = state_ids[0]
                return state_ids[0]

            return None

        except Exception as e:
            return None

    def get_or_create_city(self, city_data, state_id):
        """Obtener ciudad en destino"""
        city_name = self.clean_city_name(city_data)
        if not city_name or not state_id:
            return None

        cache_key = f"{city_name}_{state_id}"
        if cache_key in self.cache['cities']:
            return self.cache['cities'][cache_key]

        try:
            city_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'res.city', 'search',
                [[('name', 'ilike', city_name), ('state_id', '=', state_id)]]
            )

            if city_ids:
                self.cache['cities'][cache_key] = city_ids[0]
                return city_ids[0]

            return None

        except Exception as e:
            return None

    def get_or_create_region(self, region_data):
        """Obtener región en destino"""
        if not region_data or region_data is False:
            return None

        if isinstance(region_data, (list, tuple)):
            region_id = region_data[0]
            region_name = region_data[1]
        else:
            return None

        if region_id in self.cache['regions']:
            return self.cache['regions'][region_id]

        try:
            # Buscar por nombre
            target_region_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'region.region', 'search',
                [[('name', 'ilike', region_name)]]
            )

            if target_region_ids:
                self.cache['regions'][region_id] = target_region_ids[0]
                return target_region_ids[0]

            # Intentar crear
            try:
                new_region_id = self.target_models.execute_kw(
                    self.target['db'], self.target_uid, self.target['password'],
                    'region.region', 'create',
                    [{'name': region_name}]
                )
                self.cache['regions'][region_id] = new_region_id
                return new_region_id
            except:
                return None

        except Exception as e:
            return None

    def migrate_property(self, property_code):
        """Migrar una propiedad con solo campos comunes"""
        print(f"\n[{property_code}]", end=" ")

        # 1. Buscar en origen
        try:
            search_domains = [
                [('default_code', '=', property_code)],
                [('default_code', '=', f'BOH-{property_code}')],
                [('id', '=', int(property_code))] if property_code.isdigit() else [('id', '=', -1)]
            ]

            property_ids = []
            for domain in search_domains:
                property_ids = self.source_models.execute_kw(
                    self.source['db'], self.source_uid, self.source['password'],
                    'product.template', 'search', [domain]
                )
                if property_ids:
                    break

            if not property_ids:
                print("No encontrada")
                return None

            property_id = property_ids[0]

        except Exception as e:
            print(f"Error buscando: {e}")
            return None

        # 2. Leer solo campos comunes
        fields_to_read = [source for source, target in self.common_fields]

        try:
            property_data = self.source_models.execute_kw(
                self.source['db'], self.source_uid, self.source['password'],
                'product.template', 'read',
                [[property_id]],
                {'fields': fields_to_read}
            )[0]

            print(f"{property_data.get('name', 'N/A')[:30]}", end=" ")

        except Exception as e:
            print(f"Error leyendo: {e}")
            return None

        # 3. Verificar si existe en destino
        try:
            existing_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'product.template', 'search',
                [[('default_code', '=', property_data.get('default_code'))]]
            )

            if existing_ids:
                print(f"- Ya existe (ID={existing_ids[0]})")
                return existing_ids[0]

        except:
            pass

        # 4. Preparar datos
        vals = {'type': 'consu'}

        # Procesar ubicación (sin prefix "property_")
        if property_data.get('state_id'):
            target_state_id = self.get_or_create_state(property_data['state_id'])
            if target_state_id:
                vals['state_id'] = target_state_id

                if property_data.get('city_id'):
                    target_city_id = self.get_or_create_city(
                        property_data['city_id'],
                        target_state_id
                    )
                    if target_city_id:
                        vals['city_id'] = target_city_id

        if property_data.get('region_id'):
            target_region_id = self.get_or_create_region(property_data['region_id'])
            if target_region_id:
                vals['region_id'] = target_region_id

        # Mapear todos los campos comunes
        for source_field, target_field in self.common_fields:
            # Saltar ya procesados
            if source_field in ['state_id', 'city_id', 'region_id']:
                continue

            if source_field not in property_data:
                continue

            value = property_data.get(source_field)

            # Saltar valores vacíos (pero no False para booleanos)
            if value is None:
                continue

            # Para Many2one, solo tomar ID
            if isinstance(value, (list, tuple)) and len(value) == 2:
                value = value[0]

            # Asignar solo si tiene valor válido
            field_type = self.source_fields[source_field].get('type')

            if field_type == 'boolean':
                # Booleanos siempre se asignan
                vals[target_field] = value
            elif value not in [False, '', 0, 0.0]:
                vals[target_field] = value

            # Estadística
            if target_field in vals:
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

            print(f"- Creada (ID={new_id}, {len(vals)} campos)")
            return new_id

        except Exception as e:
            error_msg = str(e)
            # Extraer el mensaje de error real
            if 'ValueError' in error_msg:
                start = error_msg.find('ValueError:')
                if start > 0:
                    end = error_msg.find('\\n', start)
                    actual_error = error_msg[start:end] if end > 0 else error_msg[start:start+200]
                    print(f"- ERROR: {actual_error}")
                else:
                    print(f"- ERROR: {error_msg[:150]}")
            else:
                print(f"- ERROR: {error_msg[:150]}")
            return None

    def migrate_from_list(self, list_file="property_images/listado.txt", limit=10):
        """Migrar desde listado"""
        print("\n" + "="*80)
        print("MIGRACIÓN INTELIGENTE DE PROPIEDADES")
        print("="*80)

        # Leer listado
        try:
            with open(list_file, 'r', encoding='utf-8') as f:
                codes = [line.strip() for line in f
                        if line.strip() and line.strip() != 'default_code']

            print(f"\nPropiedades disponibles: {len(codes)}")
            print(f"Procesando: {limit}")

        except FileNotFoundError:
            print(f"Error: Archivo no encontrado: {list_file}")
            return

        self.stats['total'] = min(limit, len(codes))

        # Migrar
        for idx, code in enumerate(codes[:limit], 1):
            print(f"[{idx}/{limit}]", end=" ")
            result = self.migrate_property(code)

            if result and result > 0:
                self.stats['migrated'] += 1
            elif result:
                self.stats['existing'] += 1
            else:
                self.stats['failed'] += 1

        # Reporte
        print("\n" + "="*80)
        print("REPORTE FINAL")
        print("="*80)
        print(f"Total:        {self.stats['total']}")
        print(f"Migradas:     {self.stats['migrated']}")
        print(f"Existentes:   {self.stats['existing']}")
        print(f"Fallidas:     {self.stats['failed']}")

        print(f"\nTop 30 campos migrados:")
        sorted_fields = sorted(
            self.stats['fields_migrated'].items(),
            key=lambda x: x[1],
            reverse=True
        )
        for field, count in sorted_fields[:30]:
            print(f"   {field}: {count}")

        # Guardar cache
        with open('migration_cache.json', 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)

        print("\nCache: migration_cache.json")
        print("="*80)


def main():
    print("="*80)
    print("MIGRACIÓN INTELIGENTE: ODOO 17 → ODOO 18")
    print("="*80)

    migrator = SmartPropertyMigrator(ODOO17, ODOO18)

    # Conectar
    if not migrator.connect_source() or not migrator.connect_target():
        print("\nError de conexión")
        return

    # Descubrir campos
    migrator.discover_fields()

    # Migrar (10 para prueba)
    migrator.migrate_from_list(limit=10)


if __name__ == "__main__":
    main()

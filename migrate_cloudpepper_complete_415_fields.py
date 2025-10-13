#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migración COMPLETA de propiedades CloudPepper -> Odoo 18
Usa los 415 campos comunes identificados en la comparación de bases de datos
"""
import sys
import io
import json
import xmlrpc.client
from datetime import datetime

# Configurar salida UTF-8 para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class CompletePropertyMigrator:
    """Migrador completo con todos los campos comunes"""

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

        # Cargar campos comunes desde el archivo de comparación
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
            {'attributes': ['type', 'string', 'readonly', 'store', 'compute', 'related']}
        )

        # Campos a excluir (computed, related, readonly system fields)
        excluded_fields = {
            'id', 'create_date', 'write_date', 'create_uid', 'write_uid',
            '__last_update', 'display_name', 'message_ids', 'message_follower_ids',
            'activity_ids', 'message_attachment_count', 'rating_ids',
            'website_message_ids', 'access_token', 'access_url',
            'image_1920', 'image_1024', 'image_512', 'image_256', 'image_128'
        }

        # Filtrar campos válidos
        valid_fields = []
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

            # Excluir campos readonly del sistema
            if field_def.get('readonly') and field_def['type'] in ['one2many', 'many2many']:
                continue

            valid_fields.append(field_name)

        print(f"   ✅ {len(valid_fields)} campos válidos para migración")
        print(f"   ⏭️  {len(self.common_fields) - len(valid_fields)} campos excluidos (computed/readonly)")

        return valid_fields, target_fields

    def get_cloudpepper_properties(self, limit=None, offset=0):
        """Obtiene propiedades de CloudPepper"""
        print(f"\n📦 Obteniendo propiedades de CloudPepper...")

        # Buscar todas las propiedades activas con tipo 'consu' (propiedades inmobiliarias)
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
        search_params = {
            'order': 'id asc'  # Ordenar por ID para consistencia
        }
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
        """
        Lee datos completos de una propiedad en lotes pequeños
        para evitar el límite de XML-RPC con enteros grandes
        """
        # Dividir campos en lotes de 50
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
                    # Intentar campo por campo para este lote
                    print(f"   ⚠️  XML-RPC overflow en lote, leyendo campo por campo...")
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
                            # Saltar este campo
                            continue
                else:
                    raise

        return all_data if all_data else None

    def prepare_migration_values(self, source_data, valid_fields, target_fields):
        """Prepara valores para migración"""
        vals = {}
        fields_migrated = []
        fields_skipped = []

        # Asegurar tipo de producto correcto
        vals['type'] = 'consu'  # Consumible/Propiedad

        for field_name in valid_fields:
            if field_name not in source_data:
                continue

            value = source_data[field_name]

            # Saltar valores vacíos/None (excepto booleanos False explícitos)
            if value is None or value == '' or (isinstance(value, list) and not value):
                continue

            field_def = target_fields[field_name]
            field_type = field_def['type']

            try:
                # Many2one - convertir [id, name] a id (SKIP - IDs externos)
                if field_type == 'many2one':
                    # Saltar many2one - los IDs de CloudPepper no existen en Odoo.com
                    fields_skipped.append(f"{field_name} (many2one - IDs externos)")
                    continue

                # Many2many - convertir lista de IDs (SKIP para evitar problemas de constraint)
                elif field_type == 'many2many':
                    # Saltar many2many por ahora - pueden tener IDs de otra base de datos
                    fields_skipped.append(f"{field_name} (many2many - IDs externos)")
                    continue

                # One2many - NO migrar directamente (relación inversa)
                elif field_type == 'one2many':
                    fields_skipped.append(f"{field_name} (one2many)")
                    continue

                # Boolean - asegurar tipo correcto
                elif field_type == 'boolean':
                    vals[field_name] = bool(value)
                    fields_migrated.append(field_name)

                # Integer/Float - asegurar tipo correcto
                elif field_type in ['integer', 'float', 'monetary']:
                    try:
                        if field_type == 'integer':
                            vals[field_name] = int(value) if value else 0
                        else:
                            vals[field_name] = float(value) if value else 0.0
                        fields_migrated.append(field_name)
                    except (ValueError, TypeError):
                        fields_skipped.append(f"{field_name} (conversion error)")

                # Selection - validar que sea string
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
                # Actualizar - remover campos que no deben actualizarse
                update_vals = vals.copy()
                # Remover campos que podrían causar problemas en update
                update_vals.pop('default_code', None)  # No cambiar código

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
        print("415 CAMPOS COMUNES")
        print("="*80)

        # Conectar a ambas bases
        self.connect_cloudpepper()
        self.connect_odoo()

        # Obtener campos válidos
        valid_fields, target_fields = self.get_valid_fields_for_migration()

        # Obtener propiedades
        property_ids = self.get_cloudpepper_properties(limit=limit, offset=offset)

        # Estadísticas
        stats = {
            'total': len(property_ids),
            'created': 0,
            'updated': 0,
            'failed': 0,
            'total_fields_migrated': 0,
            'failed_properties': []
        }

        # Procesar cada propiedad
        print(f"\n{'='*80}")
        print(f"PROCESANDO {stats['total']} PROPIEDADES")
        print(f"{'='*80}")

        for idx, prop_id in enumerate(property_ids, 1):
            source_data = None
            default_code = 'N/A'

            try:
                # Leer datos de CloudPepper
                source_data = self.read_property_data(prop_id, valid_fields)

                if not source_data:
                    print(f"\n[{idx}/{stats['total']}] ❌ No se pudo leer propiedad ID {prop_id}")
                    stats['failed'] += 1
                    continue

                default_code = source_data.get('default_code', 'N/A')
                name = source_data.get('name', 'Sin nombre')

                print(f"\n{'='*80}")
                print(f"[{idx}/{stats['total']}] Propiedad: {default_code}")
                print(f"{'='*80}")
                print(f"Nombre: {name}")

                # Preparar valores
                vals, fields_migrated, fields_skipped = self.prepare_migration_values(
                    source_data, valid_fields, target_fields
                )

                print(f"Campos a migrar: {len(fields_migrated)}")

                # Crear o actualizar
                new_id, action = self.create_or_update_property(vals, default_code)

                if action == 'created':
                    stats['created'] += 1
                    print(f"✅ CREADA - ID: {new_id}")
                else:
                    stats['updated'] += 1
                    print(f"✅ ACTUALIZADA - ID: {new_id}")

                stats['total_fields_migrated'] += len(fields_migrated)

                # Mostrar resumen de campos
                print(f"\n📊 Resumen de campos:")
                print(f"   ✅ Migrados: {len(fields_migrated)}")
                if fields_skipped:
                    print(f"   ⏭️  Omitidos: {len(fields_skipped)}")

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
        print(f"   📊 Total Campos Migrados: {stats['total_fields_migrated']}")

        if stats['total'] > 0 and (stats['created'] + stats['updated']) > 0:
            avg_fields = stats['total_fields_migrated'] / (stats['created'] + stats['updated'])
            print(f"   📈 Promedio Campos/Propiedad: {avg_fields:.1f}")

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
    print("MIGRADOR COMPLETO - 415 CAMPOS COMUNES")
    print("="*80)

    # Parsear argumentos
    limit = None
    offset = 0

    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"\n⚙️  Límite: {limit} propiedades")
        except:
            print("\nUSO:")
            print("   python migrate_cloudpepper_complete_415_fields.py [limit] [offset]")
            print("\nEJEMPLOS:")
            print("   python migrate_cloudpepper_complete_415_fields.py")
            print("   python migrate_cloudpepper_complete_415_fields.py 50")
            print("   python migrate_cloudpepper_complete_415_fields.py 50 100")
            return

    if len(sys.argv) > 2:
        try:
            offset = int(sys.argv[2])
            print(f"⚙️  Offset: {offset}")
        except:
            pass

    # Ejecutar migración
    migrator = CompletePropertyMigrator()
    migrator.migrate(limit=limit, offset=offset)


if __name__ == "__main__":
    main()

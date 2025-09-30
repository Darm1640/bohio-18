#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Comparación de Campos de Modelos
==========================================
Analiza y compara campos de modelos entre dos bases de datos

Versión: 1.0.0
"""

import xmlrpc.client
import logging
import json
from collections import defaultdict

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

# Modelos a analizar
MODELS_TO_ANALYZE = [
    'product.template',  # Propiedades
    'hr.employee',       # Empleados
    'res.partner',       # Contactos
    'account.move',      # Facturas
    'account.move.line', # Líneas de factura
    'contract_scenery.contract_scenery',  # Escenarios
    'property.contract',  # Contratos de propiedad
]


# =================== CLASE DE CONEXIÓN ===================

class OdooAPI:
    def __init__(self, name, url, db, username, password):
        self.name = name
        self.url = url
        self.db = db
        logger.info(f"\nConectando a {name}: {url}")

        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

        self.uid = common.authenticate(db, username, password, {})
        if not self.uid:
            raise Exception(f"Error autenticando en {name}")
        logger.info(f"OK - Conectado (UID: {self.uid})")

    def get_fields(self, model):
        """Obtiene todos los campos de un modelo"""
        try:
            return self.models.execute_kw(
                self.db, self.uid, 'admin',
                model, 'fields_get', [], {}
            )
        except Exception as e:
            logger.error(f"Error obteniendo campos de {model}: {e}")
            return {}


# =================== CLASE PRINCIPAL ===================

class FieldComparator:
    def __init__(self):
        self.src = OdooAPI("ORIGEN", **SOURCE)
        self.dst = OdooAPI("DESTINO", **DESTINATION)
        self.results = {}

    def compare_model(self, model_name):
        """Compara campos de un modelo entre origen y destino"""
        logger.info(f"\n{'='*70}")
        logger.info(f"Analizando modelo: {model_name}")
        logger.info(f"{'='*70}")

        # Obtener campos
        src_fields = self.src.get_fields(model_name)
        dst_fields = self.dst.get_fields(model_name)

        if not src_fields and not dst_fields:
            logger.warning(f"   ⚠ Modelo {model_name} no existe en ninguna base")
            return None

        if not src_fields:
            logger.warning(f"   ⚠ Modelo {model_name} NO existe en ORIGEN")
            return None

        if not dst_fields:
            logger.warning(f"   ⚠ Modelo {model_name} NO existe en DESTINO")
            return None

        # Analizar campos
        src_field_names = set(src_fields.keys())
        dst_field_names = set(dst_fields.keys())

        common_fields = src_field_names.intersection(dst_field_names)
        only_in_src = src_field_names - dst_field_names
        only_in_dst = dst_field_names - src_field_names

        # Analizar tipos de campos comunes
        type_changes = []
        for field in common_fields:
            src_type = src_fields[field].get('type')
            dst_type = dst_fields[field].get('type')
            if src_type != dst_type:
                type_changes.append({
                    'field': field,
                    'src_type': src_type,
                    'dst_type': dst_type
                })

        # Resultado
        result = {
            'model': model_name,
            'src_count': len(src_field_names),
            'dst_count': len(dst_field_names),
            'common_count': len(common_fields),
            'only_src_count': len(only_in_src),
            'only_dst_count': len(only_in_dst),
            'type_changes_count': len(type_changes),
            'common_fields': sorted(list(common_fields)),
            'only_in_src': sorted(list(only_in_src)),
            'only_in_dst': sorted(list(only_in_dst)),
            'type_changes': type_changes,
            'src_fields_detail': src_fields,
            'dst_fields_detail': dst_fields
        }

        # Mostrar resumen
        logger.info(f"\n   Campos en ORIGEN:  {result['src_count']}")
        logger.info(f"   Campos en DESTINO: {result['dst_count']}")
        logger.info(f"   Campos COMUNES:    {result['common_count']} ({result['common_count']/result['src_count']*100:.1f}%)")
        logger.info(f"   Solo en ORIGEN:    {result['only_src_count']}")
        logger.info(f"   Solo en DESTINO:   {result['only_dst_count']}")
        logger.info(f"   Cambios de tipo:   {result['type_changes_count']}")

        if result['only_src_count'] > 0:
            logger.info(f"\n   Campos solo en ORIGEN (primeros 10):")
            for field in sorted(list(only_in_src))[:10]:
                field_type = src_fields[field].get('type', 'unknown')
                logger.info(f"     - {field} ({field_type})")

        if result['only_dst_count'] > 0:
            logger.info(f"\n   Campos solo en DESTINO (primeros 10):")
            for field in sorted(list(only_in_dst))[:10]:
                field_type = dst_fields[field].get('type', 'unknown')
                logger.info(f"     - {field} ({field_type})")

        if result['type_changes_count'] > 0:
            logger.info(f"\n   Cambios de tipo:")
            for change in type_changes:
                logger.info(f"     - {change['field']}: {change['src_type']} → {change['dst_type']}")

        self.results[model_name] = result
        return result

    def export_to_json(self, filename):
        """Exporta resultados a JSON"""
        logger.info(f"\nExportando resultados a {filename}...")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        logger.info(f"   ✓ Archivo creado: {filename}")

    def generate_migration_report(self, filename):
        """Genera reporte de campos para migración"""
        logger.info(f"\nGenerando reporte de migración...")

        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# REPORTE DE COMPARACIÓN DE CAMPOS - MIGRACIÓN\n")
            f.write("=" * 70 + "\n\n")

            for model_name, result in self.results.items():
                f.write(f"\n## Modelo: {model_name}\n")
                f.write("-" * 70 + "\n")
                f.write(f"Campos en origen:  {result['src_count']}\n")
                f.write(f"Campos en destino: {result['dst_count']}\n")
                f.write(f"Campos comunes:    {result['common_count']}\n\n")

                if result['only_src_count'] > 0:
                    f.write(f"\n### Campos SOLO en ORIGEN ({result['only_src_count']}):\n")
                    f.write("Estos campos NO existen en destino y NO se copiarán:\n\n")
                    for field in sorted(result['only_in_src']):
                        field_info = result['src_fields_detail'][field]
                        f.write(f"  - {field} ({field_info.get('type')}): {field_info.get('string', 'N/A')}\n")

                if result['only_dst_count'] > 0:
                    f.write(f"\n### Campos SOLO en DESTINO ({result['only_dst_count']}):\n")
                    f.write("Estos campos son nuevos en Odoo 18:\n\n")
                    for field in sorted(result['only_in_dst']):
                        field_info = result['dst_fields_detail'][field]
                        f.write(f"  - {field} ({field_info.get('type')}): {field_info.get('string', 'N/A')}\n")

                if result['type_changes_count'] > 0:
                    f.write(f"\n### Campos con CAMBIO DE TIPO ({result['type_changes_count']}):\n")
                    f.write("Estos campos existen pero cambiaron de tipo:\n\n")
                    for change in result['type_changes']:
                        f.write(f"  - {change['field']}: {change['src_type']} → {change['dst_type']}\n")

                f.write(f"\n### Campos COMUNES para migrar ({result['common_count']}):\n")
                f.write("Estos campos se pueden copiar directamente:\n\n")
                # Agrupar por tipo
                fields_by_type = defaultdict(list)
                for field in result['common_fields']:
                    field_type = result['dst_fields_detail'][field].get('type')
                    fields_by_type[field_type].append(field)

                for field_type, fields in sorted(fields_by_type.items()):
                    f.write(f"\n  Tipo: {field_type} ({len(fields)} campos)\n")
                    for field in sorted(fields)[:20]:  # Primeros 20
                        f.write(f"    - {field}\n")
                    if len(fields) > 20:
                        f.write(f"    ... y {len(fields)-20} más\n")

                f.write("\n" + "=" * 70 + "\n")

        logger.info(f"   ✓ Reporte creado: {filename}")

    def run(self):
        logger.info("\n" + "="*70)
        logger.info("# COMPARACIÓN DE CAMPOS DE MODELOS")
        logger.info("="*70)

        # Analizar cada modelo
        for model in MODELS_TO_ANALYZE:
            try:
                self.compare_model(model)
            except Exception as e:
                logger.error(f"Error analizando {model}: {e}")

        # Exportar resultados
        output_dir = "C:\\Program Files\\Odoo 18.0.20250830\\server\\addons\\real_estate_bits\\scripts"

        self.export_to_json(f"{output_dir}\\model_fields_comparison.json")
        self.generate_migration_report(f"{output_dir}\\migration_fields_report.txt")

        # Resumen final
        logger.info("\n" + "="*70)
        logger.info("# RESUMEN FINAL")
        logger.info("="*70)

        for model_name, result in self.results.items():
            compat_percent = result['common_count'] / result['src_count'] * 100 if result['src_count'] > 0 else 0
            logger.info(f"{model_name}:")
            logger.info(f"  Compatibilidad: {compat_percent:.1f}% ({result['common_count']}/{result['src_count']})")
            if result['only_src_count'] > 0:
                logger.info(f"  ⚠ {result['only_src_count']} campos perdidos en migración")


# =================== MAIN ===================

if __name__ == '__main__':
    comparator = FieldComparator()
    comparator.run()
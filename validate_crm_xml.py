#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para validar sintaxis XML de archivos del módulo bohio_crm
"""
import xml.etree.ElementTree as ET
import sys
import os
import io
from pathlib import Path

# Configurar salida UTF-8 para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def validate_xml_file(file_path):
    """Valida la sintaxis XML de un archivo"""
    print(f"\n{'='*80}")
    print(f"Validando: {file_path}")
    print(f"{'='*80}")

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        print(f"✅ Sintaxis XML válida")
        print(f"   Root tag: <{root.tag}>")
        print(f"   Elementos hijos: {len(list(root))}")

        # Verificar estructura Odoo
        if root.tag != 'odoo':
            print(f"⚠️  ADVERTENCIA: Root tag debería ser <odoo>, encontrado <{root.tag}>")
            return False

        # Contar records
        records = root.findall('.//record')
        templates = root.findall('.//template')
        print(f"   Records: {len(records)}")
        print(f"   Templates: {len(templates)}")

        # Validar IDs duplicados
        ids_found = {}
        for record in records:
            rec_id = record.get('id')
            if rec_id:
                if rec_id in ids_found:
                    print(f"❌ ERROR: ID duplicado '{rec_id}'")
                    print(f"   Primera aparición: línea {ids_found[rec_id]}")
                    return False
                ids_found[rec_id] = file_path

        for template in templates:
            tmpl_id = template.get('id')
            if tmpl_id:
                if tmpl_id in ids_found:
                    print(f"❌ ERROR: ID duplicado '{tmpl_id}'")
                    return False
                ids_found[tmpl_id] = file_path

        return True

    except ET.ParseError as e:
        print(f"❌ ERROR DE SINTAXIS XML:")
        print(f"   {e}")
        return False
    except FileNotFoundError:
        print(f"❌ ERROR: Archivo no encontrado")
        return False
    except Exception as e:
        print(f"❌ ERROR INESPERADO: {type(e).__name__}")
        print(f"   {e}")
        return False

def main():
    """Validar todos los archivos XML del módulo bohio_crm"""
    print("="*80)
    print("VALIDACIÓN DE ARCHIVOS XML - MÓDULO bohio_crm")
    print("="*80)

    base_path = Path(__file__).parent / 'bohio_crm'

    # Archivos a validar (según __manifest__.py)
    files_to_validate = [
        'security/ir.model.access.csv',  # No es XML, skip
        'data/crm_automated_actions.xml',
        'views/bohio_crm_complete_views.xml',
        'views/crm_lead_form_complete.xml',
        'views/crm_lead_quick_create_form.xml',
        'views/company_contract_config_views.xml',
        'views/crm_salesperson_dashboard_views.xml',
        'views/bohio_crm_actions.xml',
        'views/bohio_crm_menu.xml',
        'report/property_comparison_report.xml',
        'views/crm_capture_commission_report.xml',
        'views/bohio_timeline_view_actions.xml',
    ]

    results = {}

    for file_rel in files_to_validate:
        # Skip CSV
        if file_rel.endswith('.csv'):
            continue

        file_path = base_path / file_rel

        if not file_path.exists():
            print(f"\n⚠️  Archivo no existe: {file_rel}")
            results[file_rel] = 'NO_EXISTE'
            continue

        is_valid = validate_xml_file(file_path)
        results[file_rel] = 'OK' if is_valid else 'ERROR'

    # Resumen
    print(f"\n\n{'='*80}")
    print("RESUMEN DE VALIDACIÓN")
    print(f"{'='*80}")

    ok_count = sum(1 for v in results.values() if v == 'OK')
    error_count = sum(1 for v in results.values() if v == 'ERROR')
    missing_count = sum(1 for v in results.values() if v == 'NO_EXISTE')

    for file_rel, status in results.items():
        if status == 'OK':
            print(f"✅ {file_rel}")
        elif status == 'ERROR':
            print(f"❌ {file_rel}")
        else:
            print(f"⚠️  {file_rel} (no existe)")

    print(f"\n{'='*80}")
    print(f"Total archivos: {len(results)}")
    print(f"✅ Válidos: {ok_count}")
    print(f"❌ Con errores: {error_count}")
    print(f"⚠️  No encontrados: {missing_count}")
    print(f"{'='*80}")

    if error_count > 0:
        sys.exit(1)
    else:
        print("\n✅ TODOS LOS ARCHIVOS XML SON VÁLIDOS")
        sys.exit(0)

if __name__ == '__main__':
    main()

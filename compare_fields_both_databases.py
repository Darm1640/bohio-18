#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para COMPARAR campos de product.template en ambas bases de datos:
- CloudPepper (Odoo 17): Base de producción antigua
- Odoo.com (Odoo 18): Base nueva
"""
import xmlrpc.client
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def connect_database(config):
    """Conectar a una base de datos"""
    try:
        common = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/common")
        models = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/object")

        uid = common.authenticate(
            config['db'],
            config['username'],
            config['password'],
            {}
        )

        if uid:
            return uid, models
        else:
            return None, None
    except Exception as e:
        print(f"ERROR conectando a {config['url']}: {e}")
        return None, None


def get_fields(uid, models, config):
    """Obtener todos los campos del modelo product.template"""
    try:
        fields = models.execute_kw(
            config['db'], uid, config['password'],
            'product.template', 'fields_get', [],
            {'attributes': ['type', 'string', 'relation', 'required', 'readonly']}
        )
        return fields
    except Exception as e:
        print(f"ERROR obteniendo campos: {e}")
        return {}


def main():
    print("="*100)
    print("COMPARACIÓN DE CAMPOS: CLOUDPEPPER (ODOO 17) vs ODOO.COM (ODOO 18)")
    print("="*100)

    # Configuración CloudPepper (Odoo 17)
    cloudpepper = {
        'url': 'https://inmobiliariabohio.cloudpepper.site',
        'db': 'inmobiliariabohio.cloudpepper.site',
        'username': 'admin',
        'password': 'admin'
    }

    # Configuración Odoo.com (Odoo 18)
    odoocom = {
        'url': 'https://darm1640-bohio-18.odoo.com',
        'db': 'darm1640-bohio-18-main-24081960',
        'username': 'admin',
        'password': '123456'
    }

    # Conectar a CloudPepper
    print("\n[1/4] Conectando a CloudPepper (Odoo 17)...")
    cp_uid, cp_models = connect_database(cloudpepper)
    if not cp_uid:
        print("ERROR: No se pudo conectar a CloudPepper")
        return

    print(f"   OK (UID: {cp_uid})")

    # Conectar a Odoo.com
    print("\n[2/4] Conectando a Odoo.com (Odoo 18)...")
    od_uid, od_models = connect_database(odoocom)
    if not od_uid:
        print("ERROR: No se pudo conectar a Odoo.com")
        return

    print(f"   OK (UID: {od_uid})")

    # Obtener campos de CloudPepper
    print("\n[3/4] Obteniendo campos de CloudPepper...")
    cp_fields = get_fields(cp_uid, cp_models, cloudpepper)
    print(f"   Total campos: {len(cp_fields)}")

    # Obtener campos de Odoo.com
    print("\n[4/4] Obteniendo campos de Odoo.com...")
    od_fields = get_fields(od_uid, od_models, odoocom)
    print(f"   Total campos: {len(od_fields)}")

    # ANÁLISIS
    print("\n" + "="*100)
    print("ANÁLISIS DE CAMPOS")
    print("="*100)

    cp_names = set(cp_fields.keys())
    od_names = set(od_fields.keys())

    # Campos comunes
    common = cp_names & od_names
    print(f"\nCampos COMUNES en ambas bases: {len(common)}")

    # Campos solo en CloudPepper
    only_cp = cp_names - od_names
    print(f"Campos SOLO en CloudPepper: {len(only_cp)}")

    # Campos solo en Odoo.com
    only_od = od_names - cp_names
    print(f"Campos SOLO en Odoo.com: {len(only_od)}")

    # GUARDAR DETALLES
    print("\n" + "="*100)
    print("GUARDANDO DETALLES EN ARCHIVOS...")
    print("="*100)

    # 1. Campos de CloudPepper
    with open('campos_cloudpepper_odoo17.json', 'w', encoding='utf-8') as f:
        json.dump(cp_fields, f, indent=2, ensure_ascii=False)
    print(f"\n1. campos_cloudpepper_odoo17.json - {len(cp_fields)} campos")

    # 2. Campos de Odoo.com
    with open('campos_odoocom_odoo18.json', 'w', encoding='utf-8') as f:
        json.dump(od_fields, f, indent=2, ensure_ascii=False)
    print(f"2. campos_odoocom_odoo18.json - {len(od_fields)} campos")

    # 3. Comparación detallada
    comparison = {
        'total_cloudpepper': len(cp_fields),
        'total_odoocom': len(od_fields),
        'comunes': len(common),
        'solo_cloudpepper': len(only_cp),
        'solo_odoocom': len(only_od),
        'campos_comunes': sorted(list(common)),
        'campos_solo_cloudpepper': sorted(list(only_cp)),
        'campos_solo_odoocom': sorted(list(only_od))
    }

    with open('comparacion_campos.json', 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)
    print(f"3. comparacion_campos.json - Resumen de diferencias")

    # 4. Reporte en texto plano
    with open('COMPARACION_CAMPOS_DETALLADA.txt', 'w', encoding='utf-8') as f:
        f.write("="*100 + "\n")
        f.write("COMPARACIÓN DETALLADA DE CAMPOS: CLOUDPEPPER vs ODOO.COM\n")
        f.write("="*100 + "\n\n")

        f.write(f"Total CloudPepper (Odoo 17): {len(cp_fields)} campos\n")
        f.write(f"Total Odoo.com (Odoo 18): {len(od_fields)} campos\n")
        f.write(f"Comunes: {len(common)} campos\n")
        f.write(f"Solo CloudPepper: {len(only_cp)} campos\n")
        f.write(f"Solo Odoo.com: {len(only_od)} campos\n\n")

        # Campos COMUNES
        f.write("="*100 + "\n")
        f.write(f"CAMPOS COMUNES ({len(common)})\n")
        f.write("="*100 + "\n\n")

        for field_name in sorted(common):
            cp_info = cp_fields[field_name]
            od_info = od_fields[field_name]

            cp_type = cp_info.get('type', 'unknown')
            od_type = od_info.get('type', 'unknown')

            cp_string = cp_info.get('string', '')
            od_string = od_info.get('string', '')

            # Marcar si cambió el tipo
            type_changed = " ⚠️ TIPO CAMBIÓ" if cp_type != od_type else ""
            string_changed = " ⚠️ LABEL CAMBIÓ" if cp_string != od_string else ""

            f.write(f"{field_name:40s}\n")
            f.write(f"   CloudPepper: {cp_type:15s} | {cp_string}{type_changed}\n")
            f.write(f"   Odoo.com:    {od_type:15s} | {od_string}{string_changed}\n\n")

        # Campos SOLO EN CLOUDPEPPER
        f.write("\n" + "="*100 + "\n")
        f.write(f"CAMPOS SOLO EN CLOUDPEPPER ({len(only_cp)})\n")
        f.write("="*100 + "\n\n")

        for field_name in sorted(only_cp):
            field_info = cp_fields[field_name]
            field_type = field_info.get('type', 'unknown')
            field_string = field_info.get('string', '')
            f.write(f"{field_name:40s} ({field_type:15s}) - {field_string}\n")

        # Campos SOLO EN ODOO.COM
        f.write("\n" + "="*100 + "\n")
        f.write(f"CAMPOS SOLO EN ODOO.COM ({len(only_od)})\n")
        f.write("="*100 + "\n\n")

        for field_name in sorted(only_od):
            field_info = od_fields[field_name]
            field_type = field_info.get('type', 'unknown')
            field_string = field_info.get('string', '')
            f.write(f"{field_name:40s} ({field_type:15s}) - {field_string}\n")

    print(f"4. COMPARACION_CAMPOS_DETALLADA.txt - Reporte completo en texto")

    # RESUMEN EN CONSOLA
    print("\n" + "="*100)
    print("RESUMEN DE DIFERENCIAS")
    print("="*100)

    if only_cp:
        print(f"\nCampos SOLO en CloudPepper ({len(only_cp)}):")
        for field in sorted(list(only_cp))[:20]:
            field_info = cp_fields[field]
            print(f"   {field:40s} ({field_info.get('type', 'unknown'):15s}) - {field_info.get('string', '')}")
        if len(only_cp) > 20:
            print(f"   ... y {len(only_cp) - 20} más")

    if only_od:
        print(f"\nCampos SOLO en Odoo.com ({len(only_od)}):")
        for field in sorted(list(only_od))[:20]:
            field_info = od_fields[field]
            print(f"   {field:40s} ({field_info.get('type', 'unknown'):15s}) - {field_info.get('string', '')}")
        if len(only_od) > 20:
            print(f"   ... y {len(only_od) - 20} más")

    print("\n" + "="*100)
    print("ARCHIVOS GENERADOS:")
    print("="*100)
    print("   1. campos_cloudpepper_odoo17.json")
    print("   2. campos_odoocom_odoo18.json")
    print("   3. comparacion_campos.json")
    print("   4. COMPARACION_CAMPOS_DETALLADA.txt")
    print("="*100)


if __name__ == "__main__":
    main()

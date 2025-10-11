#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar campos estándar de Odoo 18 en product.template
y la alternativa a property_image_ids
"""
import xmlrpc.client
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración Odoo.com (Desarrollo - tiene Odoo 18 estándar)
DB_CONFIG = {
    'url': 'https://darm1640-bohio-18.odoo.com',
    'db': 'darm1640-bohio-18-main-24081960',
    'username': 'admin',
    'password': '123456'
}

def main():
    print("=" * 90)
    print("ANÁLISIS DE CAMPOS ESTÁNDAR DE ODOO 18 PARA IMÁGENES")
    print("=" * 90)

    # Conectar
    common = xmlrpc.client.ServerProxy(f"{DB_CONFIG['url']}/xmlrpc/2/common")
    uid = common.authenticate(DB_CONFIG['db'], DB_CONFIG['username'], DB_CONFIG['password'], {})

    if not uid:
        print("ERROR: No se pudo conectar")
        return

    print(f"Conectado (UID: {uid})\n")
    models = xmlrpc.client.ServerProxy(f"{DB_CONFIG['url']}/xmlrpc/2/object")

    # 1. Verificar product.image (modelo estándar)
    print("[1] Verificando modelo product.image (ESTÁNDAR ODOO):")
    try:
        campos_product_image = models.execute_kw(
            DB_CONFIG['db'], uid, DB_CONFIG['password'],
            'product.image', 'fields_get',
            [],
            {'attributes': ['string', 'type', 'relation', 'required', 'help']}
        )

        print(f"    ✅ Modelo existe - Total campos: {len(campos_product_image)}")
        print("\n    Campos principales:")

        campos_importantes = ['name', 'sequence', 'image_1920', 'product_tmpl_id', 'product_variant_id']
        for campo in campos_importantes:
            if campo in campos_product_image:
                info = campos_product_image[campo]
                print(f"      • {campo}")
                print(f"          Tipo: {info.get('type')}")
                print(f"          Etiqueta: {info.get('string')}")
                if info.get('relation'):
                    print(f"          Relación: {info.get('relation')}")

    except Exception as e:
        print(f"    ❌ Error: {e}")

    # 2. Verificar campos en product.template que apuntan a product.image
    print("\n[2] Campos en product.template relacionados con product.image:")
    try:
        campos_template = models.execute_kw(
            DB_CONFIG['db'], uid, DB_CONFIG['password'],
            'product.template', 'fields_get',
            [],
            {'attributes': ['string', 'type', 'relation', 'help']}
        )

        # Buscar campos que apunten a product.image
        campos_galeria = {}
        for nombre, info in campos_template.items():
            if info.get('relation') == 'product.image':
                campos_galeria[nombre] = info

        if campos_galeria:
            print(f"    Total campos encontrados: {len(campos_galeria)}")
            for nombre, info in campos_galeria.items():
                print(f"\n      • {nombre}")
                print(f"          Tipo: {info.get('type')}")
                print(f"          Etiqueta: {info.get('string')}")
                if info.get('help'):
                    print(f"          Ayuda: {info.get('help')[:80]}...")
        else:
            print("    ❌ No se encontraron campos")

    except Exception as e:
        print(f"    ❌ Error: {e}")

    # 3. Comparar property.image vs product.image
    print("\n[3] Comparando property.image (PERSONALIZADO) vs product.image (ESTÁNDAR):")

    try:
        # Obtener campos de property.image
        campos_property_image = models.execute_kw(
            DB_CONFIG['db'], uid, DB_CONFIG['password'],
            'property.image', 'fields_get',
            [],
            {'attributes': ['string', 'type', 'relation']}
        )

        print(f"\n    property.image (PERSONALIZADO):")
        print(f"      Total campos: {len(campos_property_image)}")

        # Campos clave en property.image
        campos_clave = ['name', 'sequence', 'image_1920', 'property_id', 'is_cover', 'image_type', 'is_public']
        for campo in campos_clave:
            if campo in campos_property_image:
                info = campos_property_image[campo]
                print(f"      • {campo} ({info.get('type')})")

        print(f"\n    product.image (ESTÁNDAR ODOO 18):")
        print(f"      Total campos: {len(campos_product_image)}")

        # Campos equivalentes en product.image
        campos_equiv = ['name', 'sequence', 'image_1920', 'product_tmpl_id', 'product_variant_id']
        for campo in campos_equiv:
            if campo in campos_product_image:
                info = campos_product_image[campo]
                print(f"      • {campo} ({info.get('type')})")

        # Comparar campos únicos
        print("\n    Campos SOLO en property.image:")
        solo_property = set(campos_property_image.keys()) - set(campos_product_image.keys())
        for campo in sorted(solo_property):
            if campo not in ['id', 'create_date', 'write_date', 'create_uid', 'write_uid', '__last_update', 'display_name']:
                print(f"      • {campo}")

    except Exception as e:
        print(f"    ❌ Error: {e}")

    # 4. Verificar relación en product.template
    print("\n[4] Campo de relación estándar en product.template:")

    if 'product_template_image_ids' in campos_template:
        info = campos_template['product_template_image_ids']
        print(f"    ✅ product_template_image_ids")
        print(f"       Tipo: {info.get('type')}")
        print(f"       Etiqueta: {info.get('string')}")
        print(f"       Relación: {info.get('relation')}")
        print(f"       → ESTE ES EL CAMPO ESTÁNDAR DE ODOO 18")

    if 'property_image_ids' in campos_template:
        info = campos_template['property_image_ids']
        print(f"\n    ✅ property_image_ids (PERSONALIZADO)")
        print(f"       Tipo: {info.get('type')}")
        print(f"       Etiqueta: {info.get('string')}")
        print(f"       Relación: {info.get('relation')}")
        print(f"       → Campo personalizado para inmobiliarias")

    # 5. Recomendación
    print("\n" + "=" * 90)
    print("💡 RECOMENDACIÓN PARA MIGRACIÓN:")
    print("=" * 90)

    print("\n🎯 ESTRATEGIA 1: Usar product.image (ESTÁNDAR)")
    print("   Ventajas:")
    print("   • ✅ Funciona en ambas bases de datos (CloudPepper y Odoo.com)")
    print("   • ✅ Compatible con Odoo estándar")
    print("   • ✅ Integrado con website/eCommerce")
    print("   • ✅ No requiere módulos adicionales")
    print("\n   Cambios necesarios:")
    print("   • Modificar create_images_in_odoo.py:")
    print("     - Cambiar modelo: 'property.image' → 'product.image'")
    print("     - Cambiar campo relación: 'property_id' → 'product_tmpl_id'")
    print("     - Eliminar campos personalizados: is_cover, image_type, is_public")
    print("     - Usar sequence para orden (primera imagen = sequence 0)")

    print("\n🎯 ESTRATEGIA 2: Usar property.image (PERSONALIZADO)")
    print("   Ventajas:")
    print("   • ✅ Campos adicionales (is_cover, image_type, is_public)")
    print("   • ✅ Lógica específica para inmobiliarias")
    print("\n   Requisitos:")
    print("   • ⚠️  Instalar theme_bohio_real_estate en CloudPepper")
    print("   • ⚠️  Verificar que el modelo exista antes de migrar")

    print("\n📝 CÓDIGO DE EJEMPLO - ESTRATEGIA 1 (product.image):")
    print("-" * 90)
    print("""
vals = {
    'name': filename,
    'sequence': sequence,  # 0 para primera imagen (principal)
    'image_1920': image_base64,
    'product_tmpl_id': property_id,  # ID del product.template
}

# Crear en product.image (modelo estándar)
image_id = models.execute_kw(
    db, uid, password,
    'product.image', 'create',
    [vals]
)

# La primera imagen (sequence=0) se sincroniza automáticamente
# con product.template.image_1920
    """)

    print("\n" + "=" * 90)


if __name__ == "__main__":
    main()

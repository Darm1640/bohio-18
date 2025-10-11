#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar la existencia del modelo property.image
y la estructura de imágenes en ambas bases de datos
"""
import xmlrpc.client
import sys
import io

# Configurar salida UTF-8 para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración de las dos bases de datos
DATABASES = [
    {
        'name': 'CloudPepper (Producción)',
        'url': 'https://inmobiliariabohio.cloudpepper.site',
        'db': 'inmobiliariabohio.cloudpepper.site',
        'username': 'admin',
        'password': 'admin'
    },
    {
        'name': 'Odoo.com (Desarrollo)',
        'url': 'https://darm1640-bohio-18.odoo.com',
        'db': 'darm1640-bohio-18-main-24081960',
        'username': 'admin',
        'password': '123456'
    }
]


def verificar_modelo_existe(uid, models, db_config, modelo):
    """Verificar si un modelo existe en la base de datos"""
    try:
        model_ids = models.execute_kw(
            db_config['db'], uid, db_config['password'],
            'ir.model', 'search',
            [[('model', '=', modelo)]]
        )
        return len(model_ids) > 0
    except Exception as e:
        print(f"    Error verificando modelo: {e}")
        return False


def obtener_info_modelo(uid, models, db_config, modelo):
    """Obtener información detallada de un modelo"""
    try:
        model_ids = models.execute_kw(
            db_config['db'], uid, db_config['password'],
            'ir.model', 'search',
            [[('model', '=', modelo)]]
        )

        if not model_ids:
            return None

        info = models.execute_kw(
            db_config['db'], uid, db_config['password'],
            'ir.model', 'read',
            [model_ids],
            {'fields': ['name', 'model', 'state', 'info']}
        )

        return info[0] if info else None

    except Exception as e:
        print(f"    Error obteniendo info del modelo: {e}")
        return None


def contar_registros_modelo(uid, models, db_config, modelo):
    """Contar registros existentes en un modelo"""
    try:
        count = models.execute_kw(
            db_config['db'], uid, db_config['password'],
            modelo, 'search_count',
            [[]]
        )
        return count
    except Exception as e:
        print(f"    Error contando registros: {e}")
        return -1


def verificar_campos_imagen_producto(uid, models, db_config):
    """Verificar campos relacionados con imágenes en product.template"""
    try:
        campos = models.execute_kw(
            db_config['db'], uid, db_config['password'],
            'product.template', 'fields_get',
            [],
            {'attributes': ['string', 'type', 'relation']}
        )

        campos_imagen = {}
        keywords = ['image', 'photo', 'gallery', 'picture', 'attachment', 'document']

        for nombre, info in campos.items():
            nombre_lower = nombre.lower()
            if any(kw in nombre_lower for kw in keywords):
                campos_imagen[nombre] = info

        return campos_imagen

    except Exception as e:
        print(f"    Error verificando campos: {e}")
        return {}


def verificar_modulo_instalado(uid, models, db_config, modulo):
    """Verificar si un módulo está instalado"""
    try:
        module_ids = models.execute_kw(
            db_config['db'], uid, db_config['password'],
            'ir.module.module', 'search',
            [[('name', '=', modulo), ('state', '=', 'installed')]]
        )
        return len(module_ids) > 0
    except Exception as e:
        print(f"    Error verificando módulo: {e}")
        return False


def main():
    print("=" * 90)
    print("VERIFICACIÓN DE MODELO property.image Y ESTRUCTURA DE IMÁGENES")
    print("=" * 90)

    resultados = {}

    for db_config in DATABASES:
        print(f"\n{'=' * 90}")
        print(f"BASE DE DATOS: {db_config['name']}")
        print(f"URL: {db_config['url']}")
        print("=" * 90)

        # Conectar
        try:
            common = xmlrpc.client.ServerProxy(f"{db_config['url']}/xmlrpc/2/common")
            uid = common.authenticate(db_config['db'], db_config['username'], db_config['password'], {})

            if not uid:
                print("  ERROR: Autenticación fallida")
                continue

            print(f"  Conectado (UID: {uid})")
            models = xmlrpc.client.ServerProxy(f"{db_config['url']}/xmlrpc/2/object")

        except Exception as e:
            print(f"  ERROR de conexión: {e}")
            continue

        resultado_db = {
            'nombre': db_config['name'],
            'conectado': True
        }

        # 1. Verificar modelo property.image
        print("\n  [1] Verificando modelo 'property.image'...")
        existe_property_image = verificar_modelo_existe(uid, models, db_config, 'property.image')

        if existe_property_image:
            print("      ✅ EXISTE")
            info = obtener_info_modelo(uid, models, db_config, 'property.image')
            if info:
                print(f"      Nombre: {info['name']}")
                print(f"      Estado: {info['state']}")

            count = contar_registros_modelo(uid, models, db_config, 'property.image')
            if count >= 0:
                print(f"      Total registros: {count}")
                resultado_db['property_image_count'] = count
        else:
            print("      ❌ NO EXISTE")

        resultado_db['tiene_property_image'] = existe_property_image

        # 2. Verificar modelo ir.attachment
        print("\n  [2] Verificando modelo 'ir.attachment'...")
        existe_attachment = verificar_modelo_existe(uid, models, db_config, 'ir.attachment')
        print(f"      {'✅' if existe_attachment else '❌'} {'EXISTE' if existe_attachment else 'NO EXISTE'}")

        if existe_attachment:
            count = contar_registros_modelo(uid, models, db_config, 'ir.attachment')
            if count >= 0:
                print(f"      Total registros: {count}")

        # 3. Verificar campos de imagen en product.template
        print("\n  [3] Campos relacionados con imágenes en product.template:")
        campos_imagen = verificar_campos_imagen_producto(uid, models, db_config)

        if campos_imagen:
            print(f"      Total campos encontrados: {len(campos_imagen)}")
            for nombre, info in sorted(campos_imagen.items()):
                tipo = info.get('type', 'N/A')
                relacion = f" → {info.get('relation')}" if info.get('relation') else ""
                print(f"        • {nombre} ({tipo}){relacion}")
        else:
            print("      No se encontraron campos de imagen")

        resultado_db['campos_imagen'] = list(campos_imagen.keys())

        # 4. Verificar módulos instalados relacionados
        print("\n  [4] Verificando módulos relacionados:")

        modulos = [
            'real_estate_bits',
            'theme_bohio_real_estate',
            'base_real_estate',
            'property_management'
        ]

        modulos_instalados = []
        for modulo in modulos:
            instalado = verificar_modulo_instalado(uid, models, db_config, modulo)
            estado = "✅ INSTALADO" if instalado else "❌ NO INSTALADO"
            print(f"      • {modulo}: {estado}")
            if instalado:
                modulos_instalados.append(modulo)

        resultado_db['modulos_instalados'] = modulos_instalados

        # 5. Verificar propiedades con imágenes
        print("\n  [5] Verificando propiedades con imágenes:")

        try:
            # Contar propiedades con image_1920
            props_con_imagen = models.execute_kw(
                db_config['db'], uid, db_config['password'],
                'product.template', 'search_count',
                [[('image_1920', '!=', False), ('is_property', '=', True)]]
            )
            print(f"      • Propiedades con image_1920: {props_con_imagen}")
            resultado_db['propiedades_con_imagen_principal'] = props_con_imagen

            # Si existe property_image_ids, contar propiedades con galería
            if 'property_image_ids' in campos_imagen:
                props_con_galeria = models.execute_kw(
                    db_config['db'], uid, db_config['password'],
                    'product.template', 'search_count',
                    [[('property_image_ids', '!=', False), ('is_property', '=', True)]]
                )
                print(f"      • Propiedades con galería (property_image_ids): {props_con_galeria}")
                resultado_db['propiedades_con_galeria'] = props_con_galeria

        except Exception as e:
            print(f"      Error verificando propiedades: {e}")

        resultados[db_config['name']] = resultado_db

    # RESUMEN FINAL
    print("\n" + "=" * 90)
    print("RESUMEN Y RECOMENDACIONES")
    print("=" * 90)

    print("\n📊 COMPARACIÓN:")
    print("-" * 90)

    for nombre, resultado in resultados.items():
        if resultado.get('conectado'):
            print(f"\n{nombre}:")
            print(f"  • Modelo property.image: {'✅ SÍ' if resultado.get('tiene_property_image') else '❌ NO'}")
            print(f"  • Campos de imagen: {len(resultado.get('campos_imagen', []))}")
            print(f"  • Módulos instalados: {', '.join(resultado.get('modulos_instalados', [])) or 'Ninguno'}")

            if 'propiedades_con_imagen_principal' in resultado:
                print(f"  • Propiedades con imagen: {resultado['propiedades_con_imagen_principal']}")

    print("\n" + "=" * 90)
    print("💡 RECOMENDACIONES PARA MIGRACIÓN DE IMÁGENES:")
    print("=" * 90)

    # Determinar estrategia
    cloudpepper = resultados.get('CloudPepper (Producción)', {})
    odoo_com = resultados.get('Odoo.com (Desarrollo)', {})

    if cloudpepper.get('tiene_property_image') and odoo_com.get('tiene_property_image'):
        print("\n✅ ESTRATEGIA: Migración Completa con Galería")
        print("   Ambas bases tienen property.image")
        print("   • Usar create_images_in_odoo.py sin modificaciones")
        print("   • Migrar galería completa de imágenes")
        print("   • Mantener is_cover, sequence, image_type")

    elif not cloudpepper.get('tiene_property_image') and odoo_com.get('tiene_property_image'):
        print("\n⚠️  ESTRATEGIA: Solo Imagen Principal")
        print("   CloudPepper NO tiene property.image")
        print("   • OPCIÓN 1: Instalar módulo real_estate_bits en CloudPepper")
        print("   • OPCIÓN 2: Modificar script para usar solo image_1920")
        print("   • OPCIÓN 3: Migrar solo a Desarrollo (Odoo.com)")

        print("\n   📝 Si eliges OPCIÓN 2, modificar create_images_in_odoo.py:")
        print("      - Solo subir primera imagen a product.template.image_1920")
        print("      - Ignorar galería property_image_ids")

    elif cloudpepper.get('tiene_property_image') and not odoo_com.get('tiene_property_image'):
        print("\n⚠️  CASO INUSUAL: Producción tiene property.image pero Desarrollo no")
        print("   • Verificar instalación de módulos en Desarrollo")

    else:
        print("\n⚠️  NINGUNA base tiene property.image")
        print("   • Usar solo image_1920 en product.template")
        print("   • Considerar instalar módulo real_estate_bits")

    print("\n" + "=" * 90)


if __name__ == "__main__":
    main()

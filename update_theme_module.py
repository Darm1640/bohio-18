#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para actualizar módulo theme_bohio_real_estate en Odoo.com
"""
import xmlrpc.client
import sys
import io

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración de conexión
url = 'https://darm1640-bohio-18.odoo.com'
db = 'darm1640-bohio-18-main-24081960'
username = 'admin'
password = '123456'

print("=" * 60)
print("ACTUALIZACIÓN DE MÓDULO theme_bohio_real_estate")
print("=" * 60)

try:
    # Autenticación
    print(f"\n1. Conectando a {url}...")
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})

    if not uid:
        print("❌ ERROR: No se pudo autenticar. Verifica usuario/contraseña.")
        exit(1)

    print(f"✅ Autenticado correctamente (UID: {uid})")

    # Conexión a modelos
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    # Buscar módulo theme_bohio_real_estate
    print("\n2. Buscando módulo theme_bohio_real_estate...")
    module_ids = models.execute_kw(
        db, uid, password,
        'ir.module.module', 'search',
        [[('name', '=', 'theme_bohio_real_estate')]]
    )

    if not module_ids:
        print("❌ ERROR: Módulo theme_bohio_real_estate no encontrado.")
        exit(1)

    module_id = module_ids[0]
    print(f"✅ Módulo encontrado (ID: {module_id})")

    # Obtener estado del módulo
    module_data = models.execute_kw(
        db, uid, password,
        'ir.module.module', 'read',
        [module_id],
        {'fields': ['name', 'state', 'latest_version']}
    )[0]

    print(f"\n3. Estado actual del módulo:")
    print(f"   - Nombre: {module_data['name']}")
    print(f"   - Estado: {module_data['state']}")
    print(f"   - Versión: {module_data.get('latest_version', 'N/A')}")

    if module_data['state'] != 'installed':
        print(f"\n❌ ERROR: El módulo no está instalado (estado: {module_data['state']})")
        exit(1)

    # Actualizar módulo
    print("\n4. Actualizando módulo...")
    print("   (Esto puede tomar algunos segundos...)")

    try:
        models.execute_kw(
            db, uid, password,
            'ir.module.module', 'button_immediate_upgrade',
            [[module_id]]
        )
        print("✅ Módulo actualizado correctamente")

        print("\n" + "=" * 60)
        print("ACTUALIZACIÓN COMPLETADA")
        print("=" * 60)
        print("\n📋 Próximos pasos:")
        print("1. Ir a: https://darm1640-bohio-18.odoo.com/shop/properties")
        print("2. Seleccionar 'Arriendo' como tipo de servicio")
        print("3. Buscar 'Barranquilla' en el autocompletado")
        print("4. Verificar:")
        print("   - Listado: '1 de 1 total' ✅")
        print("   - Mapa (tab): 1 pin en Barranquilla ✅")

    except Exception as e:
        print(f"❌ ERROR al actualizar módulo: {str(e)}")
        print("\nIntenta actualizar manualmente desde:")
        print("  Aplicaciones > theme_bohio_real_estate > Actualizar")
        exit(1)

except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print("\nPosibles causas:")
    print("  - Credenciales incorrectas")
    print("  - URL incorrecta")
    print("  - Problemas de conexión")
    exit(1)

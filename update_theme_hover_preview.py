#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para actualizar el módulo theme_bohio_real_estate en Odoo.com
con la nueva funcionalidad de preview en autocomplete
"""
import xmlrpc.client
import sys
import io

# Configurar salida UTF-8 para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Credenciales de Odoo.com
url = 'https://darm1640-bohio-18.odoo.com'
db = 'darm1640-bohio-18-main-24081960'
username = 'admin'
password = '123456'

print("=" * 80)
print("ACTUALIZACIÓN DE MÓDULO: theme_bohio_real_estate")
print("Funcionalidad: Preview en mapa al pasar mouse sobre autocomplete")
print("=" * 80)
print()

try:
    # Conectar a Odoo
    print(f"🔌 Conectando a {url}...")
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')

    # Autenticar
    print(f"🔑 Autenticando como '{username}'...")
    uid = common.authenticate(db, username, password, {})

    if not uid:
        print("❌ ERROR: Autenticación fallida")
        print("   Verifica las credenciales en el script")
        sys.exit(1)

    print(f"✅ Autenticación exitosa (UID: {uid})")
    print()

    # Conectar a models
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    # Buscar el módulo
    print("🔍 Buscando módulo 'theme_bohio_real_estate'...")
    module_ids = models.execute_kw(
        db, uid, password,
        'ir.module.module', 'search',
        [[('name', '=', 'theme_bohio_real_estate')]]
    )

    if not module_ids:
        print("❌ ERROR: Módulo 'theme_bohio_real_estate' no encontrado")
        sys.exit(1)

    module_id = module_ids[0]
    print(f"✅ Módulo encontrado (ID: {module_id})")
    print()

    # Obtener estado del módulo
    module_info = models.execute_kw(
        db, uid, password,
        'ir.module.module', 'read',
        [[module_id]], {'fields': ['name', 'state', 'latest_version']}
    )

    print("📦 Estado del módulo:")
    print(f"   Nombre: {module_info[0]['name']}")
    print(f"   Estado: {module_info[0]['state']}")
    print(f"   Versión: {module_info[0].get('latest_version', 'N/A')}")
    print()

    # Actualizar el módulo
    print("🔄 Actualizando módulo...")
    print("   ADVERTENCIA: Esto puede tomar varios segundos...")
    print()

    try:
        result = models.execute_kw(
            db, uid, password,
            'ir.module.module', 'button_immediate_upgrade',
            [[module_id]]
        )

        print("✅ MÓDULO ACTUALIZADO EXITOSAMENTE")
        print()
        print("📋 Cambios aplicados:")
        print("   • Preview de propiedades en mapa al pasar mouse sobre autocomplete")
        print("   • Eventos mouseenter/mouseleave en items del autocomplete")
        print("   • Funciones previewAutocompleteItem() y clearAutocompletePreview()")
        print("   • Guardado y restauración de filtros durante preview")
        print()
        print("🧪 Para probar:")
        print("   1. Ir a la página de búsqueda de propiedades")
        print("   2. Escribir nombre de ciudad/barrio/proyecto en el buscador")
        print("   3. Pasar el mouse sobre los items del dropdown SIN hacer click")
        print("   4. Ver cómo el mapa se actualiza con preview de propiedades")
        print("   5. Al salir del item, el mapa vuelve al estado anterior")
        print()

    except Exception as upgrade_error:
        print(f"❌ ERROR durante la actualización: {upgrade_error}")
        print()
        print("💡 Posibles causas:")
        print("   • El módulo tiene errores de sintaxis")
        print("   • Faltan archivos declarados en __manifest__.py")
        print("   • Problemas de permisos en el servidor")
        print()
        sys.exit(1)

except xmlrpc.client.Fault as e:
    print(f"❌ ERROR XML-RPC: {e.faultCode}")
    print(f"   Mensaje: {e.faultString}")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR INESPERADO: {type(e).__name__}")
    print(f"   Mensaje: {e}")
    sys.exit(1)

print("=" * 80)
print("✅ PROCESO COMPLETADO")
print("=" * 80)

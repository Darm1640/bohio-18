#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Diagnóstico: Propiedades Homepage
Verifica por qué no se muestran propiedades en la homepage
"""

import xmlrpc.client
import json

# Configuración de conexión
URL = 'http://localhost:8069'
DB = 'bohio_db'
USERNAME = 'admin'
PASSWORD = 'admin'

def conectar_odoo():
    """Conectar a Odoo vía XML-RPC"""
    try:
        common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
        uid = common.authenticate(DB, USERNAME, PASSWORD, {})

        if not uid:
            print("❌ Error: No se pudo autenticar en Odoo")
            return None, None

        models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')
        print(f"✅ Conectado a Odoo - UID: {uid}")
        return uid, models
    except Exception as e:
        print(f"❌ Error conectando a Odoo: {e}")
        return None, None

def verificar_propiedades_arriendo(uid, models):
    """Verificar propiedades de arriendo"""
    print("\n" + "="*80)
    print("📍 1. VERIFICANDO PROPIEDADES DE ARRIENDO")
    print("="*80)

    # Dominio base
    domain = [
        ('is_property', '=', True),
        ('active', '=', True),
        ('state', '=', 'free'),
        ('type_service', 'in', ['rent', 'sale_rent'])
    ]

    try:
        # Contar propiedades
        count = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_count', [domain])
        print(f"✅ Total propiedades de arriendo: {count}")

        if count > 0:
            # Obtener primeras 5 propiedades
            properties = models.execute_kw(
                DB, uid, PASSWORD,
                'product.template', 'search_read',
                [domain],
                {
                    'fields': ['id', 'name', 'default_code', 'type_service', 'state',
                              'net_rental_price', 'latitude', 'longitude', 'project_worksite_id'],
                    'limit': 5
                }
            )

            print("\n📋 Muestra de propiedades:")
            for prop in properties:
                tiene_ubicacion = '🗺️' if (prop['latitude'] and prop['longitude']) else '❌'
                tiene_proyecto = '🏢' if prop['project_worksite_id'] else '🏠'
                precio = f"${prop['net_rental_price']:,.0f}" if prop['net_rental_price'] else '❌ SIN PRECIO'

                print(f"\n  {tiene_ubicacion} {tiene_proyecto} ID: {prop['id']}")
                print(f"     Código: {prop['default_code'] or 'N/A'}")
                print(f"     Nombre: {prop['name'][:60]}...")
                print(f"     Servicio: {prop['type_service']}")
                print(f"     Estado: {prop['state']}")
                print(f"     Precio Arriendo: {precio}")
                print(f"     Proyecto: {prop['project_worksite_id'][1] if prop['project_worksite_id'] else 'Sin proyecto'}")
        else:
            print("⚠️ NO se encontraron propiedades de arriendo")
            print("\n🔍 Verificando si existen propiedades con otros estados:")

            # Verificar propiedades con otros estados
            all_states_domain = [
                ('is_property', '=', True),
                ('type_service', 'in', ['rent', 'sale_rent'])
            ]
            all_count = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_count', [all_states_domain])
            print(f"   Total propiedades de arriendo (todos los estados): {all_count}")

            if all_count > 0:
                # Ver estados
                states_data = models.execute_kw(
                    DB, uid, PASSWORD,
                    'product.template', 'read_group',
                    [[('is_property', '=', True), ('type_service', 'in', ['rent', 'sale_rent'])]],
                    ['state'],
                    ['state']
                )
                print("\n   📊 Distribución por estado:")
                for state in states_data:
                    print(f"      - {state['state']}: {state['state_count']} propiedades")

    except Exception as e:
        print(f"❌ Error verificando arriendos: {e}")

def verificar_propiedades_venta_usadas(uid, models):
    """Verificar propiedades de venta sin proyecto"""
    print("\n" + "="*80)
    print("📍 2. VERIFICANDO PROPIEDADES DE VENTA USADAS (SIN PROYECTO)")
    print("="*80)

    domain = [
        ('is_property', '=', True),
        ('active', '=', True),
        ('state', '=', 'free'),
        ('type_service', 'in', ['sale', 'sale_rent']),
        ('project_worksite_id', '=', False)  # Sin proyecto
    ]

    try:
        count = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_count', [domain])
        print(f"✅ Total propiedades de venta usadas: {count}")

        if count > 0:
            properties = models.execute_kw(
                DB, uid, PASSWORD,
                'product.template', 'search_read',
                [domain],
                {
                    'fields': ['id', 'name', 'default_code', 'type_service', 'state',
                              'net_price', 'latitude', 'longitude', 'project_worksite_id'],
                    'limit': 5
                }
            )

            print("\n📋 Muestra de propiedades:")
            for prop in properties:
                tiene_ubicacion = '🗺️' if (prop['latitude'] and prop['longitude']) else '❌'
                precio = f"${prop['net_price']:,.0f}" if prop['net_price'] else '❌ SIN PRECIO'

                print(f"\n  {tiene_ubicacion} 🏠 ID: {prop['id']}")
                print(f"     Código: {prop['default_code'] or 'N/A'}")
                print(f"     Nombre: {prop['name'][:60]}...")
                print(f"     Precio Venta: {precio}")
        else:
            print("⚠️ NO se encontraron propiedades de venta usadas")

            # Verificar cuántas tienen proyecto
            with_project_domain = [
                ('is_property', '=', True),
                ('active', '=', True),
                ('state', '=', 'free'),
                ('type_service', 'in', ['sale', 'sale_rent']),
                ('project_worksite_id', '!=', False)
            ]
            with_project_count = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_count', [with_project_domain])
            print(f"   ℹ️ Propiedades de venta CON proyecto: {with_project_count}")

    except Exception as e:
        print(f"❌ Error verificando ventas usadas: {e}")

def verificar_proyectos(uid, models):
    """Verificar propiedades de proyectos"""
    print("\n" + "="*80)
    print("📍 3. VERIFICANDO PROYECTOS EN VENTA (CON PROYECTO)")
    print("="*80)

    domain = [
        ('is_property', '=', True),
        ('active', '=', True),
        ('state', '=', 'free'),
        ('type_service', 'in', ['sale', 'sale_rent']),
        ('project_worksite_id', '!=', False)  # Con proyecto
    ]

    try:
        count = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_count', [domain])
        print(f"✅ Total propiedades en proyectos: {count}")

        if count > 0:
            properties = models.execute_kw(
                DB, uid, PASSWORD,
                'product.template', 'search_read',
                [domain],
                {
                    'fields': ['id', 'name', 'default_code', 'type_service', 'state',
                              'net_price', 'latitude', 'longitude', 'project_worksite_id'],
                    'limit': 5
                }
            )

            print("\n📋 Muestra de propiedades:")
            for prop in properties:
                tiene_ubicacion = '🗺️' if (prop['latitude'] and prop['longitude']) else '❌'
                precio = f"${prop['net_price']:,.0f}" if prop['net_price'] else '❌ SIN PRECIO'

                print(f"\n  {tiene_ubicacion} 🏢 ID: {prop['id']}")
                print(f"     Código: {prop['default_code'] or 'N/A'}")
                print(f"     Nombre: {prop['name'][:60]}...")
                print(f"     Proyecto: {prop['project_worksite_id'][1] if prop['project_worksite_id'] else 'N/A'}")
                print(f"     Precio Venta: {precio}")
        else:
            print("⚠️ NO se encontraron propiedades en proyectos")

    except Exception as e:
        print(f"❌ Error verificando proyectos: {e}")

def verificar_endpoint_ajax(uid, models):
    """Simular llamada al endpoint AJAX"""
    print("\n" + "="*80)
    print("📍 4. SIMULANDO ENDPOINT /property/search/ajax")
    print("="*80)

    try:
        # Simular parámetros del JavaScript
        tests = [
            {
                'name': 'Arriendo',
                'filters': {
                    'type_service': 'rent',
                    'limit': 10,
                    'order': 'newest'
                }
            },
            {
                'name': 'Venta Usada',
                'filters': {
                    'type_service': 'sale',
                    'has_project': False,
                    'limit': 10,
                    'order': 'newest'
                }
            },
            {
                'name': 'Proyectos',
                'filters': {
                    'type_service': 'sale',
                    'has_project': True,
                    'limit': 10,
                    'order': 'newest'
                }
            }
        ]

        for test in tests:
            print(f"\n🔍 Probando: {test['name']}")
            print(f"   Filtros: {json.dumps(test['filters'], indent=6)}")

            # Construir dominio manualmente (como lo hace el controlador)
            domain = [
                ('is_property', '=', True),
                ('active', '=', True),
                ('state', '=', 'free')
            ]

            # Aplicar filtro de tipo de servicio
            ts = test['filters'].get('type_service')
            if ts:
                if ts == 'sale_rent':
                    domain.append(('type_service', 'in', ['sale', 'rent', 'sale_rent']))
                else:
                    domain.append(('type_service', 'in', [ts, 'sale_rent']))

            # Aplicar filtro de proyecto
            if 'has_project' in test['filters']:
                if test['filters']['has_project']:
                    domain.append(('project_worksite_id', '!=', False))
                else:
                    domain.append(('project_worksite_id', '=', False))

            print(f"   Dominio aplicado:")
            for condition in domain:
                print(f"      {condition}")

            # Ejecutar búsqueda
            count = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'search_count', [domain])
            print(f"   ✅ Resultado: {count} propiedades")

    except Exception as e:
        print(f"❌ Error simulando endpoint: {e}")

def verificar_configuracion_modulo():
    """Verificar configuración del módulo"""
    print("\n" + "="*80)
    print("📍 5. VERIFICANDO CONFIGURACIÓN DEL MÓDULO")
    print("="*80)

    import os

    module_path = r"C:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\theme_bohio_real_estate"

    # Verificar __manifest__.py
    manifest_path = os.path.join(module_path, '__manifest__.py')
    if os.path.exists(manifest_path):
        print(f"✅ __manifest__.py existe")

        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()

            if 'homepage_properties.js' in content:
                print(f"✅ homepage_properties.js está registrado en __manifest__.py")
            else:
                print(f"❌ homepage_properties.js NO está registrado en __manifest__.py")

            if 'homepage_new.xml' in content:
                print(f"✅ homepage_new.xml está registrado en __manifest__.py")
            else:
                print(f"❌ homepage_new.xml NO está registrado en __manifest__.py")
    else:
        print(f"❌ __manifest__.py NO encontrado")

    # Verificar archivos
    js_path = os.path.join(module_path, 'static', 'src', 'js', 'homepage_properties.js')
    xml_path = os.path.join(module_path, 'views', 'homepage_new.xml')

    print(f"\n📁 Verificando archivos:")
    print(f"   homepage_properties.js: {'✅' if os.path.exists(js_path) else '❌'}")
    print(f"   homepage_new.xml: {'✅' if os.path.exists(xml_path) else '❌'}")

def main():
    """Función principal"""
    print("\n" + "="*80)
    print("DIAGNOSTICO: PROPIEDADES HOMEPAGE BOHIO")
    print("="*80)
    print(f"Base de Datos: {DB}")
    print(f"URL: {URL}")
    print(f"Usuario: {USERNAME}")

    # Conectar
    uid, models = conectar_odoo()
    if not uid or not models:
        print("\n❌ No se pudo conectar a Odoo. Verifica que esté corriendo.")
        return

    # Ejecutar verificaciones
    verificar_propiedades_arriendo(uid, models)
    verificar_propiedades_venta_usadas(uid, models)
    verificar_proyectos(uid, models)
    verificar_endpoint_ajax(uid, models)
    verificar_configuracion_modulo()

    # Resumen final
    print("\n" + "="*80)
    print("📊 RESUMEN DEL DIAGNÓSTICO")
    print("="*80)
    print("""
✅ Si ves propiedades en las verificaciones 1-3 pero NO en el navegador:
   → El problema está en el JavaScript o en la carga del módulo
   → Solución: Actualizar módulo y limpiar cache del navegador

⚠️ Si NO ves propiedades en las verificaciones 1-3:
   → El problema está en la base de datos
   → Solución: Importar o crear propiedades de prueba

🔍 Para más detalles:
   1. Abrir homepage en el navegador
   2. Presionar F12 (Consola del navegador)
   3. Buscar mensajes de console.log()
   4. Buscar errores en la pestaña Network
""")

if __name__ == '__main__':
    main()

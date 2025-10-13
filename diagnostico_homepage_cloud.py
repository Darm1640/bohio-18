#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnóstico Homepage - Instancia Cloud
Verifica propiedades en la instancia de producción
"""

import xmlrpc.client

# Configuración de conexión a instancia CLOUD
url = 'https://darm1640-bohio-18.odoo.com'
db = 'darm1640-bohio-18-main-24081960'
username = 'admin'
password = '123456'

def conectar():
    """Conectar a Odoo Cloud"""
    try:
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})

        if not uid:
            print("ERROR: No se pudo autenticar")
            return None, None

        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        print(f"[OK] Conectado a {url}")
        print(f"     BD: {db}")
        print(f"     UID: {uid}")
        return uid, models
    except Exception as e:
        print(f"ERROR conectando: {e}")
        return None, None

def verificar_propiedades(uid, models):
    """Verificar propiedades en las 3 categorías"""
    print("\n" + "="*70)
    print("VERIFICACION DE PROPIEDADES")
    print("="*70)

    categorias = [
        {
            'nombre': 'ARRIENDO',
            'domain': [
                ('is_property', '=', True),
                ('active', '=', True),
                ('state', '=', 'free'),
                ('type_service', 'in', ['rent', 'sale_rent'])
            ]
        },
        {
            'nombre': 'VENTA USADA (sin proyecto)',
            'domain': [
                ('is_property', '=', True),
                ('active', '=', True),
                ('state', '=', 'free'),
                ('type_service', 'in', ['sale', 'sale_rent']),
                ('project_worksite_id', '=', False)
            ]
        },
        {
            'nombre': 'PROYECTOS (con proyecto)',
            'domain': [
                ('is_property', '=', True),
                ('active', '=', True),
                ('state', '=', 'free'),
                ('type_service', 'in', ['sale', 'sale_rent']),
                ('project_worksite_id', '!=', False)
            ]
        }
    ]

    resultados = {}

    for cat in categorias:
        print(f"\n[{cat['nombre']}]")
        print("  Dominio aplicado:")
        for condition in cat['domain']:
            print(f"    {condition}")

        try:
            count = models.execute_kw(
                db, uid, password,
                'product.template', 'search_count',
                [cat['domain']]
            )
            print(f"  Resultado: {count} propiedades")
            resultados[cat['nombre']] = count

            # Si hay propiedades, mostrar muestra
            if count > 0:
                props = models.execute_kw(
                    db, uid, password,
                    'product.template', 'search_read',
                    [cat['domain']],
                    {
                        'fields': ['id', 'name', 'default_code', 'state',
                                  'type_service', 'project_worksite_id',
                                  'latitude', 'longitude'],
                        'limit': 3
                    }
                )

                print("  Muestra de propiedades:")
                for prop in props:
                    ubicacion = "[GPS]" if (prop.get('latitude') and prop.get('longitude')) else "[SIN GPS]"
                    proyecto = prop.get('project_worksite_id', [False])[1] if prop.get('project_worksite_id') else "Sin proyecto"
                    print(f"    {ubicacion} ID:{prop['id']} - {prop['default_code']} - {prop['name'][:40]}...")
                    print(f"            Estado:{prop['state']} | Servicio:{prop['type_service']} | Proyecto:{proyecto}")

        except Exception as e:
            print(f"  ERROR: {e}")
            resultados[cat['nombre']] = 0

    return resultados

def verificar_estados(uid, models):
    """Ver distribución de estados de propiedades"""
    print("\n" + "="*70)
    print("DISTRIBUCION POR ESTADO")
    print("="*70)

    try:
        # Contar propiedades por estado
        domain = [('is_property', '=', True)]
        states = models.execute_kw(
            db, uid, password,
            'product.template', 'read_group',
            [domain],
            ['state'],
            ['state']
        )

        print("\nPropiedades por estado:")
        for state in states:
            print(f"  {state['state']}: {state['state_count']} propiedades")

        # Contar propiedades por tipo de servicio
        services = models.execute_kw(
            db, uid, password,
            'product.template', 'read_group',
            [domain],
            ['type_service'],
            ['type_service']
        )

        print("\nPropiedades por tipo de servicio:")
        for service in services:
            print(f"  {service['type_service']}: {service['type_service_count']} propiedades")

    except Exception as e:
        print(f"ERROR: {e}")

def verificar_modulo(uid, models):
    """Verificar instalación del módulo theme_bohio_real_estate"""
    print("\n" + "="*70)
    print("VERIFICACION DEL MODULO")
    print("="*70)

    try:
        module = models.execute_kw(
            db, uid, password,
            'ir.module.module', 'search_read',
            [[('name', '=', 'theme_bohio_real_estate')]],
            {'fields': ['name', 'state', 'latest_version']}
        )

        if module:
            mod = module[0]
            print(f"\nModulo theme_bohio_real_estate:")
            print(f"  Estado: {mod['state']}")
            print(f"  Version: {mod.get('latest_version', 'N/A')}")

            if mod['state'] != 'installed':
                print("  [AVISO] El modulo NO esta instalado!")
        else:
            print("\n[ERROR] Modulo theme_bohio_real_estate NO encontrado")

    except Exception as e:
        print(f"ERROR: {e}")

def resumen_final(resultados):
    """Mostrar resumen y recomendaciones"""
    print("\n" + "="*70)
    print("RESUMEN Y DIAGNOSTICO")
    print("="*70)

    total = sum(resultados.values())

    if total == 0:
        print("\n[PROBLEMA] NO hay propiedades en NINGUNA categoria")
        print("\nPOSIBLES CAUSAS:")
        print("  1. No se han importado propiedades")
        print("  2. Las propiedades no tienen state='free'")
        print("  3. Las propiedades no tienen is_property=True")
        print("\nSOLUCION:")
        print("  - Importar propiedades desde API/Excel")
        print("  - Verificar el estado de las propiedades existentes")
        print("  - Activar propiedades (active=True)")

    elif all(v > 0 for v in resultados.values()):
        print("\n[OK] HAY propiedades en las 3 categorias")
        print("\nConteo:")
        for cat, count in resultados.items():
            print(f"  - {cat}: {count}")

        print("\nSi la homepage NO muestra propiedades, el problema es:")
        print("  1. JavaScript no esta cargando")
        print("  2. Cache del navegador")
        print("  3. Error en el endpoint /property/search/ajax")
        print("\nSOLUCION:")
        print("  - Limpiar cache del navegador (Ctrl+Shift+Del)")
        print("  - Abrir consola del navegador (F12) y buscar errores")
        print("  - Verificar Network tab para ver llamadas a /property/search/ajax")
        print("  - Actualizar modulo: odoo-bin -u theme_bohio_real_estate")

    else:
        print("\n[AVISO] Solo ALGUNAS categorias tienen propiedades")
        print("\nConteo:")
        for cat, count in resultados.items():
            status = "[OK]" if count > 0 else "[FALTA]"
            print(f"  {status} {cat}: {count}")

        print("\nSOLUCION:")
        print("  - Importar/crear propiedades para las categorias faltantes")
        print("  - Verificar que las propiedades tengan project_worksite_id correcto")

def main():
    """Función principal"""
    print("="*70)
    print("DIAGNOSTICO HOMEPAGE - INSTANCIA CLOUD")
    print("="*70)

    # Conectar
    uid, models = conectar()
    if not uid or not models:
        return

    # Ejecutar verificaciones
    resultados = verificar_propiedades(uid, models)
    verificar_estados(uid, models)
    verificar_modulo(uid, models)
    resumen_final(resultados)

    print("\n" + "="*70)
    print("DIAGNOSTICO COMPLETADO")
    print("="*70)

if __name__ == '__main__':
    main()

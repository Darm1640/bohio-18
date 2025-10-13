#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para actualizar el módulo theme_bohio_real_estate via XML-RPC
Útil cuando no se tiene acceso directo a odoo-bin
"""
import xmlrpc.client
import time

# Configuración
URL = 'http://localhost:8069'
DB = 'bohio_db'
USERNAME = 'admin'
PASSWORD = 'admin'
MODULE_NAME = 'theme_bohio_real_estate'

def main():
    print("=" * 60)
    print("ACTUALIZAR MÓDULO VÍA XML-RPC")
    print("=" * 60)

    try:
        # 1. Autenticar
        print("\n[1/4] Conectando a Odoo...")
        common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
        uid = common.authenticate(DB, USERNAME, PASSWORD, {})

        if not uid:
            print("❌ Error: No se pudo autenticar. Verifica usuario/contraseña.")
            return False

        print(f"✅ Conectado - UID: {uid}")

        # 2. Buscar el módulo
        print(f"\n[2/4] Buscando módulo '{MODULE_NAME}'...")
        models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

        module_ids = models.execute_kw(DB, uid, PASSWORD,
            'ir.module.module', 'search',
            [[('name', '=', MODULE_NAME)]])

        if not module_ids:
            print(f"❌ Error: Módulo '{MODULE_NAME}' no encontrado")
            return False

        module_id = module_ids[0]
        print(f"✅ Módulo encontrado - ID: {module_id}")

        # 3. Leer estado actual
        print("\n[3/4] Leyendo estado del módulo...")
        module_data = models.execute_kw(DB, uid, PASSWORD,
            'ir.module.module', 'read',
            [module_id],
            {'fields': ['name', 'state', 'installed_version']})

        if module_data:
            data = module_data[0]
            print(f"   Nombre: {data['name']}")
            print(f"   Estado: {data['state']}")
            print(f"   Versión: {data.get('installed_version', 'N/A')}")

        # 4. Actualizar módulo
        print("\n[4/4] Actualizando módulo...")
        print("⏳ Este proceso puede tardar 30-60 segundos...")

        try:
            # Método 1: button_immediate_upgrade (más rápido)
            result = models.execute_kw(DB, uid, PASSWORD,
                'ir.module.module', 'button_immediate_upgrade',
                [[module_id]])

            print("✅ Módulo actualizado exitosamente")

            # 5. Verificar estado final
            time.sleep(2)
            final_data = models.execute_kw(DB, uid, PASSWORD,
                'ir.module.module', 'read',
                [module_id],
                {'fields': ['state', 'installed_version']})

            if final_data:
                print(f"\n📊 Estado final:")
                print(f"   Estado: {final_data[0]['state']}")
                print(f"   Versión: {final_data[0].get('installed_version', 'N/A')}")

            print("\n" + "=" * 60)
            print("✅ ACTUALIZACIÓN COMPLETADA")
            print("=" * 60)
            print("\n📝 PRÓXIMOS PASOS:")
            print("   1. Abre tu navegador")
            print("   2. Presiona Ctrl+Shift+Delete")
            print("   3. Limpia el cache completamente")
            print("   4. Recarga la página del homepage")
            print("   5. Verifica que las propiedades se muestren")
            print("\n")

            return True

        except Exception as e:
            print(f"❌ Error al actualizar: {str(e)}")
            print("\n💡 ALTERNATIVA:")
            print("   Actualiza manualmente desde la web:")
            print(f"   1. Ve a: {URL}/web")
            print("   2. Apps → Busca 'theme_bohio' → Actualizar")
            return False

    except xmlrpc.client.Fault as e:
        print(f"❌ Error XML-RPC: {e.faultCode} - {e.faultString}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

if __name__ == '__main__':
    main()

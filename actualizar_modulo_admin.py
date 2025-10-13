#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para actualizar el modulo theme_bohio_real_estate
Ejecutar desde terminal con permisos de administrador
"""

import xmlrpc.client
import sys

# Configuracion
URL = 'http://localhost:8069'
DB = 'bohio_db'
USERNAME = 'admin'
PASSWORD = 'admin'
MODULE_NAME = 'theme_bohio_real_estate'

def update_module():
    """Actualizar el modulo para forzar recarga de templates"""
    try:
        print(f'\n[*] Actualizando modulo {MODULE_NAME}...')

        # Conectar a Odoo
        common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
        uid = common.authenticate(DB, USERNAME, PASSWORD, {})

        if not uid:
            print('❌ Error: No se pudo autenticar. Verifica usuario/contraseña.')
            return False

        print(f'✅ Conectado como UID: {uid}')

        # Acceder a models
        models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

        # Buscar el módulo
        print(f'\n🔍 Buscando módulo "{MODULE_NAME}"...')
        module_ids = models.execute_kw(
            DB, uid, PASSWORD,
            'ir.module.module', 'search',
            [[('name', '=', MODULE_NAME)]]
        )

        if not module_ids:
            print(f'❌ Módulo "{MODULE_NAME}" no encontrado')
            return False

        module_id = module_ids[0]
        print(f'✅ Módulo encontrado (ID: {module_id})')

        # Obtener estado actual
        module_data = models.execute_kw(
            DB, uid, PASSWORD,
            'ir.module.module', 'read',
            [module_id],
            {'fields': ['name', 'state', 'latest_version', 'installed_version']}
        )[0]

        print(f'\n📊 Estado actual:')
        print(f'   - Nombre: {module_data["name"]}')
        print(f'   - Estado: {module_data["state"]}')
        print(f'   - Versión instalada: {module_data.get("installed_version", "N/A")}')
        print(f'   - Última versión: {module_data.get("latest_version", "N/A")}')

        # Actualizar el módulo
        print(f'\n🔄 Ejecutando actualización...')
        try:
            models.execute_kw(
                DB, uid, PASSWORD,
                'ir.module.module', 'button_immediate_upgrade',
                [[module_id]]
            )
            print('✅ Módulo actualizado correctamente')
            print('\n⚠️  IMPORTANTE: Reinicia el navegador y haz Ctrl + Shift + R')
            return True

        except Exception as e:
            print(f'❌ Error al actualizar: {e}')
            print('\n💡 Intenta con este comando manual:')
            print(f'   python odoo-bin -c odoo.conf -d {DB} -u {MODULE_NAME} --stop-after-init')
            return False

    except Exception as e:
        print(f'❌ Error general: {e}')
        return False

if __name__ == '__main__':
    print('=' * 60)
    print('ACTUALIZACIÓN DE MÓDULO ODOO')
    print('=' * 60)

    success = update_module()

    print('\n' + '=' * 60)
    if success:
        print('✅ ACTUALIZACIÓN COMPLETADA')
        print('=' * 60)
        print('\n📋 PRÓXIMOS PASOS:')
        print('1. Ir al navegador')
        print('2. Presionar Ctrl + Shift + R (hard refresh)')
        print('3. Abrir consola (F12)')
        print('4. Ejecutar: openReportModal()')
        print('5. Verificar que el modal se abre')
    else:
        print('❌ ACTUALIZACIÓN FALLÓ')
        print('=' * 60)
        print('\n💡 ALTERNATIVA - Ejecutar manualmente:')
        print('1. Abrir terminal como Administrador')
        print('2. cd "C:\\Program Files\\Odoo 18.0.20250830\\server"')
        print(f'3. ..\\python\\python.exe odoo-bin -c odoo.conf -d {DB} -u {MODULE_NAME} --stop-after-init')

    sys.exit(0 if success else 1)

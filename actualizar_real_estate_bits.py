# -*- coding: utf-8 -*-
import xmlrpc.client
import ssl

# Ignorar verificación SSL
ssl._create_default_https_context = ssl._create_unverified_context

# Configuración
URL = 'https://104.131.70.107'
DB = 'bohio'
USERNAME = 'admin'
PASSWORD = '123456'
MODULE_NAME = 'real_estate_bits'

print('=' * 60)
print('ACTUALIZACIÓN DE MÓDULO REAL_ESTATE_BITS')
print('=' * 60)

try:
    # Conectar
    print(f'\n[*] Conectando a {URL}...')
    common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})
    print(f'[OK] Conectado como UID: {uid}')

    # Buscar módulo
    models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

    print(f'\n[*] Buscando módulo "{MODULE_NAME}"...')
    module_ids = models.execute_kw(DB, uid, PASSWORD, 'ir.module.module', 'search',
        [[('name', '=', MODULE_NAME)]])

    if not module_ids:
        print(f'[ERROR] Módulo "{MODULE_NAME}" no encontrado')
        exit(1)

    module_id = module_ids[0]
    print(f'[OK] Módulo encontrado (ID: {module_id})')

    # Obtener estado
    module = models.execute_kw(DB, uid, PASSWORD, 'ir.module.module', 'read',
        [module_id], {'fields': ['state', 'latest_version']})

    print(f'\n[INFO] Estado actual: {module[0]["state"]}')
    print(f'[INFO] Versión: {module[0].get("latest_version", "N/A")}')

    # Actualizar módulo
    print(f'\n[*] Actualizando módulo...')
    models.execute_kw(DB, uid, PASSWORD, 'ir.module.module', 'button_immediate_upgrade', [[module_id]])
    print('[OK] Módulo actualizado correctamente')

    print('\n[IMPORTANTE] Bootstrap Icons ahora está disponible para:')
    print('  - bohio_crm')
    print('  - bohio_real_estate')
    print('  - theme_bohio_real_estate')
    print('\n[IMPORTANTE] Reinicia el navegador y haz Ctrl + Shift + R')

except Exception as e:
    print(f'\n[ERROR] {str(e)}')
    exit(1)

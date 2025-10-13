# -*- coding: utf-8 -*-
import xmlrpc.client
import ssl

# Deshabilitar verificacion SSL para servidor con certificado autofirmado
ssl_context = ssl._create_unverified_context()

URL = 'https://104.131.70.107'
DB = 'bohio'
USERNAME = 'admin'
PASSWORD = '123456'
MODULE_NAME = 'theme_bohio_real_estate'

print('=' * 60)
print('ACTUALIZACION DE MODULO ODOO')
print('=' * 60)

try:
    print(f'\n[*] Conectando a {URL}...')
    common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common', context=ssl_context)
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})

    if not uid:
        print('[ERROR] No se pudo autenticar')
        exit(1)

    print(f'[OK] Conectado como UID: {uid}')

    models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object', context=ssl_context)

    print(f'\n[*] Buscando modulo "{MODULE_NAME}"...')
    module_ids = models.execute_kw(
        DB, uid, PASSWORD,
        'ir.module.module', 'search',
        [[('name', '=', MODULE_NAME)]]
    )

    if not module_ids:
        print(f'[ERROR] Modulo "{MODULE_NAME}" no encontrado')
        exit(1)

    module_id = module_ids[0]
    print(f'[OK] Modulo encontrado (ID: {module_id})')

    module_data = models.execute_kw(
        DB, uid, PASSWORD,
        'ir.module.module', 'read',
        [module_id],
        {'fields': ['name', 'state']}
    )[0]

    print(f'\n[INFO] Estado actual: {module_data["state"]}')

    print(f'\n[*] Actualizando modulo...')
    models.execute_kw(
        DB, uid, PASSWORD,
        'ir.module.module', 'button_immediate_upgrade',
        [[module_id]]
    )

    print('[OK] Modulo actualizado correctamente')
    print('\n[IMPORTANTE] Reinicia el navegador y haz Ctrl + Shift + R')

except Exception as e:
    print(f'[ERROR] {e}')
    print('\nAlternativa manual:')
    print(f'  python odoo-bin -c odoo.conf -d {DB} -u {MODULE_NAME} --stop-after-init')
    exit(1)

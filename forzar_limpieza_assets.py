# -*- coding: utf-8 -*-
import xmlrpc.client
import ssl

ssl_context = ssl._create_unverified_context()

URL = 'https://104.131.70.107'
DB = 'bohio'
USERNAME = 'admin'
PASSWORD = '123456'

print('=' * 60)
print('LIMPIEZA FORZADA DE ASSETS')
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

    # Eliminar todos los attachments de assets compilados
    print(f'\n[*] Buscando assets compilados...')

    # Buscar attachments con URL que contenga 'assets'
    asset_attachments = models.execute_kw(
        DB, uid, PASSWORD,
        'ir.attachment', 'search',
        [[
            '|', '|', '|',
            ('url', 'ilike', '/web/assets/'),
            ('url', 'ilike', 'web.assets_frontend'),
            ('url', 'ilike', 'web.assets_frontend_lazy'),
            ('name', 'ilike', '.min.js'),
        ]]
    )

    if asset_attachments:
        print(f'[INFO] Encontrados {len(asset_attachments)} assets compilados')
        print(f'[*] Eliminando assets...')

        models.execute_kw(
            DB, uid, PASSWORD,
            'ir.attachment', 'unlink',
            [asset_attachments]
        )
        print(f'[OK] {len(asset_attachments)} assets eliminados')
    else:
        print('[INFO] No se encontraron assets compilados')

    # Invalidar cache de QWeb
    print(f'\n[*] Invalidando cache de QWeb...')
    try:
        models.execute_kw(
            DB, uid, PASSWORD,
            'ir.qweb', 'clear_caches',
            []
        )
        print('[OK] Cache de QWeb invalidada')
    except Exception as e:
        print(f'[WARN] No se pudo invalidar QWeb cache: {e}')

    # Invalidar todas las vistas
    print(f'\n[*] Invalidando vistas...')
    views = models.execute_kw(
        DB, uid, PASSWORD,
        'ir.ui.view', 'search',
        [[('type', '=', 'qweb')]]
    )

    if views:
        print(f'[INFO] Encontradas {len(views)} vistas QWeb')
        # Forzar escritura para invalidar cache
        models.execute_kw(
            DB, uid, PASSWORD,
            'ir.ui.view', 'write',
            [views, {}]
        )
        print(f'[OK] {len(views)} vistas invalidadas')

    print(f'\n[OK] Limpieza completada')
    print('\n' + '=' * 60)
    print('[IMPORTANTE] PROXIMOS PASOS:')
    print('=' * 60)
    print('1. Los cambios locales NO estan en el servidor remoto')
    print('2. Debes SUBIR los archivos modificados al servidor:')
    print('   - theme_bohio_real_estate/static/src/js/property_detail_gallery.js')
    print('   - theme_bohio_real_estate/views/property_detail_template.xml')
    print('3. Usar Git, FTP, SCP o el metodo que uses normalmente')
    print('4. Despues de subir, ejecutar este script de nuevo')
    print('5. Finalmente hacer Ctrl + Shift + R en el navegador')

except Exception as e:
    print(f'[ERROR] {e}')
    exit(1)

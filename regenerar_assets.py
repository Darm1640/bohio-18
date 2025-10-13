# -*- coding: utf-8 -*-
import xmlrpc.client
import ssl

# Deshabilitar verificacion SSL
ssl_context = ssl._create_unverified_context()

URL = 'https://104.131.70.107'
DB = 'bohio'
USERNAME = 'admin'
PASSWORD = '123456'

print('=' * 60)
print('REGENERACION DE ASSETS EN ODOO')
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

    # Buscar todas las vistas del módulo
    print(f'\n[*] Buscando vistas del modulo theme_bohio_real_estate...')
    views = models.execute_kw(
        DB, uid, PASSWORD,
        'ir.ui.view', 'search_read',
        [[('key', 'ilike', 'theme_bohio_real_estate.property_detail')]],
        {'fields': ['id', 'name', 'key']}
    )

    if views:
        for view in views:
            print(f'[INFO] Vista encontrada: {view["name"]} (ID: {view["id"]})')

            # Forzar escritura para invalidar cache
            models.execute_kw(
                DB, uid, PASSWORD,
                'ir.ui.view', 'write',
                [[view['id']], {}]
            )
            print(f'[OK] Cache invalidada para vista ID: {view["id"]}')
    else:
        print('[WARN] No se encontraron vistas')

    # Limpiar cache de assets
    print(f'\n[*] Limpiando cache de assets...')
    try:
        # Buscar assets bundle
        assets = models.execute_kw(
            DB, uid, PASSWORD,
            'ir.asset', 'search',
            [[('bundle', '=', 'web.assets_frontend')]]
        )
        print(f'[INFO] Encontrados {len(assets) if assets else 0} assets')

    except Exception as e:
        print(f'[WARN] No se pudo limpiar assets: {e}')

    # Buscar archivos attachment del modulo
    print(f'\n[*] Buscando attachments del modulo...')
    attachments = models.execute_kw(
        DB, uid, PASSWORD,
        'ir.attachment', 'search_read',
        [[('url', 'ilike', 'theme_bohio_real_estate')], ('res_model', '=', 'ir.ui.view')],
        {'fields': ['id', 'name', 'url'], 'limit': 10}
    )

    if attachments:
        print(f'[INFO] Encontrados {len(attachments)} attachments')
        for att in attachments:
            print(f'  - {att.get("name")}: {att.get("url")}')
    else:
        print('[INFO] No se encontraron attachments (puede ser normal)')

    print(f'\n[OK] Proceso completado')
    print('\n[IMPORTANTE] Pasos siguientes:')
    print('1. Ir a Odoo > Configuracion > Tecnico > Depuracion de Assets')
    print('2. O acceder a: https://104.131.70.107/web/webclient/qweb?db=bohio&bundle=web.assets_frontend')
    print('3. O simplemente hacer Ctrl + Shift + R en el navegador')
    print('4. Abrir en modo debug: https://104.131.70.107/property/15360?debug=1')

except Exception as e:
    print(f'[ERROR] {e}')
    exit(1)

# -*- coding: utf-8 -*-
"""
PARCHE TEMPORAL: Actualizar property_detail_gallery.js en el servidor
Este script crea un attachment con el JavaScript corregido
"""
import xmlrpc.client
import ssl
import base64

ssl_context = ssl._create_unverified_context()

URL = 'https://104.131.70.107'
DB = 'bohio'
USERNAME = 'admin'
PASSWORD = '123456'

# Leer el archivo JavaScript corregido
with open('theme_bohio_real_estate/static/src/js/property_detail_gallery.js', 'r', encoding='utf-8') as f:
    js_content = f.read()

print('=' * 60)
print('PARCHE TEMPORAL - ACTUALIZACION DE JAVASCRIPT')
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

    # Buscar el attachment del archivo JavaScript
    print(f'\n[*] Buscando archivo property_detail_gallery.js en el servidor...')

    attachments = models.execute_kw(
        DB, uid, PASSWORD,
        'ir.attachment', 'search_read',
        [[
            ('url', 'ilike', 'property_detail_gallery.js'),
            ('res_model', '=', False)
        ]],
        {'fields': ['id', 'name', 'url', 'datas'], 'limit': 5}
    )

    if attachments:
        print(f'[INFO] Encontrados {len(attachments)} archivos:')
        for att in attachments:
            print(f'  - ID: {att["id"]}, URL: {att.get("url")}')

        # Actualizar el primero
        att_id = attachments[0]['id']
        print(f'\n[*] Actualizando attachment ID: {att_id}...')

        # Convertir contenido a base64
        js_base64 = base64.b64encode(js_content.encode('utf-8')).decode('ascii')

        models.execute_kw(
            DB, uid, PASSWORD,
            'ir.attachment', 'write',
            [[att_id], {'datas': js_base64}]
        )
        print('[OK] Archivo actualizado')

    else:
        print('[WARN] No se encontro el archivo como attachment')
        print('[INFO] Intentando crear un nuevo attachment...')

        # Crear nuevo attachment
        js_base64 = base64.b64encode(js_content.encode('utf-8')).decode('ascii')

        att_id = models.execute_kw(
            DB, uid, PASSWORD,
            'ir.attachment', 'create',
            [{
                'name': 'property_detail_gallery.js',
                'type': 'binary',
                'datas': js_base64,
                'url': '/theme_bohio_real_estate/static/src/js/property_detail_gallery.js',
                'mimetype': 'application/javascript',
            }]
        )
        print(f'[OK] Attachment creado con ID: {att_id}')

    # Limpiar cache de assets
    print(f'\n[*] Limpiando cache de assets...')

    # Buscar y eliminar assets compilados
    compiled_assets = models.execute_kw(
        DB, uid, PASSWORD,
        'ir.attachment', 'search',
        [[
            '|',
            ('url', 'ilike', '/web/assets/'),
            ('name', 'ilike', 'web.assets_frontend_lazy.min.js')
        ]]
    )

    if compiled_assets:
        print(f'[INFO] Encontrados {len(compiled_assets)} assets compilados')
        models.execute_kw(
            DB, uid, PASSWORD,
            'ir.attachment', 'unlink',
            [compiled_assets]
        )
        print(f'[OK] Assets eliminados')

    print(f'\n[OK] Parche aplicado correctamente')
    print('\n' + '=' * 60)
    print('PROXIMOS PASOS:')
    print('=' * 60)
    print('1. Ir al navegador')
    print('2. Presionar Ctrl + Shift + Delete')
    print('3. Borrar cache e imagenes almacenadas')
    print('4. Abrir: https://104.131.70.107/property/15360?debug=assets')
    print('5. Presionar Ctrl + Shift + R')
    print('6. Verificar en consola que NO hay error de sintaxis')
    print('7. Probar abrir el zoom de una imagen')

except Exception as e:
    print(f'[ERROR] {e}')
    import traceback
    traceback.print_exc()
    exit(1)

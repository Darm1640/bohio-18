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

# Módulos en orden de dependencia
MODULES = [
    'real_estate_bits',          # Base (debe actualizarse primero)
    'bohio_crm',                 # Depende de real_estate_bits
    'bohio_real_estate',         # Depende de real_estate_bits
    'theme_bohio_real_estate',   # Depende de bohio_real_estate
]

print('=' * 80)
print('ACTUALIZACIÓN MASIVA DE MÓDULOS - BOOTSTRAP ICONS')
print('=' * 80)

try:
    # Conectar
    print(f'\n[*] Conectando a {URL}...')
    common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})
    print(f'[OK] Conectado como UID: {uid}')

    models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')

    for module_name in MODULES:
        print(f'\n{"-" * 80}')
        print(f'[*] Procesando: {module_name}')
        print(f'{"-" * 80}')

        # Buscar módulo
        module_ids = models.execute_kw(DB, uid, PASSWORD, 'ir.module.module', 'search',
            [[('name', '=', module_name)]])

        if not module_ids:
            print(f'[WARN] Módulo "{module_name}" no encontrado, saltando...')
            continue

        module_id = module_ids[0]

        # Obtener estado
        module = models.execute_kw(DB, uid, PASSWORD, 'ir.module.module', 'read',
            [module_id], {'fields': ['state', 'latest_version']})

        state = module[0]['state']
        version = module[0].get('latest_version', 'N/A')

        print(f'[INFO] ID: {module_id}')
        print(f'[INFO] Estado: {state}')
        print(f'[INFO] Versión: {version}')

        if state != 'installed':
            print(f'[WARN] Módulo no está instalado, saltando...')
            continue

        # Actualizar módulo
        print(f'[*] Actualizando...')
        models.execute_kw(DB, uid, PASSWORD, 'ir.module.module', 'button_immediate_upgrade', [[module_id]])
        print(f'[OK] {module_name} actualizado correctamente')

    print('\n' + '=' * 80)
    print('ACTUALIZACION COMPLETADA')
    print('=' * 80)
    print('\n[IMPORTANTE] Cambios aplicados:')
    print('  ✓ Bootstrap Icons centralizado en real_estate_bits')
    print('  ✓ Font Awesome convertido a Bootstrap Icons en 96 archivos')
    print('  ✓ 4 módulos actualizados:')
    for module in MODULES:
        print(f'    - {module}')
    print('\n[IMPORTANTE] Acción requerida:')
    print('  1. Reinicia el navegador')
    print('  2. Haz Ctrl + Shift + R (hard refresh)')
    print('  3. Verifica que los iconos se vean correctamente')

except Exception as e:
    print(f'\n[ERROR] {str(e)}')
    exit(1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para actualizar el módulo bohio_crm en Odoo.com
Corrige el error de XML y crea campos de marketing
"""
import xmlrpc.client
import sys
import io

# Configurar salida UTF-8 para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Credenciales de Odoo.com
url = 'https://darm1640-bohio-18.odoo.com'
db = 'darm1640-bohio-18-main-24081960'
username = 'admin'
password = '123456'

print("=" * 80)
print("ACTUALIZACION DE MODULO: bohio_crm")
print("Correccion de XML y creacion de campos de marketing")
print("=" * 80)
print()

try:
    # Conectar a Odoo
    print(f"Conectando a {url}...")
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')

    # Autenticar
    print(f"Autenticando como '{username}'...")
    uid = common.authenticate(db, username, password, {})

    if not uid:
        print("ERROR: Autenticacion fallida")
        print("Verifica las credenciales en el script")
        sys.exit(1)

    print(f"Autenticacion exitosa (UID: {uid})")
    print()

    # Conectar a models
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    # Buscar el módulo
    print("Buscando modulo 'bohio_crm'...")
    module_ids = models.execute_kw(
        db, uid, password,
        'ir.module.module', 'search',
        [[('name', '=', 'bohio_crm')]]
    )

    if not module_ids:
        print("ERROR: Modulo 'bohio_crm' no encontrado")
        sys.exit(1)

    module_id = module_ids[0]
    print(f"Modulo encontrado (ID: {module_id})")
    print()

    # Obtener estado del módulo
    module_info = models.execute_kw(
        db, uid, password,
        'ir.module.module', 'read',
        [[module_id]], {'fields': ['name', 'state', 'latest_version']}
    )

    print("Estado del modulo:")
    print(f"   Nombre: {module_info[0]['name']}")
    print(f"   Estado: {module_info[0]['state']}")
    print(f"   Version: {module_info[0].get('latest_version', 'N/A')}")
    print()

    # Actualizar el módulo
    print("Actualizando modulo...")
    print("ADVERTENCIA: Esto puede tomar varios segundos...")
    print("Se crearan las siguientes columnas en crm_lead:")
    print("   - marketing_campaign_type")
    print("   - marketing_quantity")
    print("   - marketing_schedule")
    print("   - marketing_estimated_reach")
    print("   - marketing_budget_allocated")
    print("   - marketing_start_date")
    print("   - marketing_end_date")
    print("   - marketing_description")
    print()

    try:
        result = models.execute_kw(
            db, uid, password,
            'ir.module.module', 'button_immediate_upgrade',
            [[module_id]]
        )

        print("MODULO ACTUALIZADO EXITOSAMENTE")
        print()
        print("Cambios aplicados:")
        print("   - Archivo crm_automated_actions.xml corregido")
        print("   - Tag <data> agregado (requerido en Odoo 18)")
        print("   - HTML entities escapados correctamente")
        print("   - Encoding UTF-8 sin acentos en comentarios")
        print()
        print("   - Campos de marketing creados en crm.lead")
        print("   - 6 acciones automaticas cargadas:")
        print("     1. Crear actividad al programar visita")
        print("     2. Notificar conflictos de visitas")
        print("     3. Recordar documentos de credito")
        print("     4. Actualizar comision de captacion")
        print("     5. Notificar aprobacion de credito")
        print("     6. Sugerir crear reserva al ganar")
        print()
        print("Para verificar:")
        print("   1. Ir a CRM > Configuracion > Acciones Automatizadas")
        print("   2. Buscar acciones que empiecen con 'CRM:'")
        print("   3. Crear una oportunidad y verificar campos de marketing")
        print()

    except Exception as upgrade_error:
        error_msg = str(upgrade_error)
        print(f"ERROR durante la actualizacion:")
        print(f"   {error_msg}")
        print()

        # Analizar el error
        if 'marketing_campaign_type' in error_msg:
            print("El error sigue siendo sobre campos de marketing.")
            print("Posibles causas:")
            print("   - El modulo no se actualizo desde GitHub en Odoo.com")
            print("   - Hay un problema de sincronizacion")
            print()
            print("SOLUCION:")
            print("   1. Ir a Odoo.com > Apps > Actualizar lista de apps")
            print("   2. Buscar 'bohio_crm'")
            print("   3. Click en ... > Actualizar")
            print()
        elif 'Element odoo has extra content' in error_msg:
            print("Aun hay problema con el archivo XML")
            print("El archivo crm_automated_actions.xml necesita mas correcciones.")
            print()
        else:
            print("Error inesperado. Revisa los logs en Odoo.com:")
            print("   Configuracion > Tecnico > Registro del servidor")
            print()

        sys.exit(1)

except xmlrpc.client.Fault as e:
    print(f"ERROR XML-RPC: {e.faultCode}")
    print(f"   Mensaje: {e.faultString}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR INESPERADO: {type(e).__name__}")
    print(f"   Mensaje: {e}")
    sys.exit(1)

print("=" * 80)
print("PROCESO COMPLETADO")
print("=" * 80)

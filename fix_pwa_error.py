#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para agregar el campo enable_pwa al modelo website si no existe
"""
import xmlrpc.client

URL = 'http://localhost:8069'
DB = 'bohio_db'
USERNAME = 'admin'
PASSWORD = 'admin'

try:
    # Conectar a Odoo
    common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})
    
    if not uid:
        print('❌ Error: No se pudo autenticar')
        exit(1)
    
    print(f'✅ Conectado - UID: {uid}')
    
    models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')
    
    # Verificar si el campo existe
    fields_info = models.execute_kw(DB, uid, PASSWORD, 'website', 'fields_get', [[]])
    
    if 'enable_pwa' in fields_info:
        print('✅ El campo enable_pwa ya existe')
    else:
        print('❌ El campo enable_pwa NO existe')
        print('⚠️  Necesitas actualizar el módulo website')
        print('\nEjecuta esto en SQL:')
        print("""
        ALTER TABLE website ADD COLUMN IF NOT EXISTS enable_pwa boolean DEFAULT false;
        UPDATE website SET enable_pwa = false WHERE enable_pwa IS NULL;
        """)
        
except Exception as e:
    print(f'❌ Error: {e}')

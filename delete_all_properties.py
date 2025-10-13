#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Elimina TODAS las propiedades (activas y archivadas) de Odoo.com
"""
import xmlrpc.client

config = {
    'url': 'https://darm1640-bohio-18.odoo.com',
    'db': 'darm1640-bohio-18-main-24081960',
    'username': 'admin',
    'password': '123456'
}

print("Conectando a Odoo.com...")
common = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/common")
uid = common.authenticate(config['db'], config['username'], config['password'], {})
print(f"Conectado como UID: {uid}")

models = xmlrpc.client.ServerProxy(f"{config['url']}/xmlrpc/2/object")

# Buscar TODAS las propiedades (activas y archivadas)
print("\nBuscando TODAS las propiedades...")
# Buscar activas
active_props = models.execute_kw(
    config['db'], uid, config['password'],
    'product.template', 'search',
    [[('type', '=', 'consu'), ('active', '=', True)]]
)
# Buscar archivadas
archived_props = models.execute_kw(
    config['db'], uid, config['password'],
    'product.template', 'search',
    [[('type', '=', 'consu'), ('active', '=', False)]]
)
all_props = active_props + archived_props

total = len(all_props)
print(f"Total propiedades encontradas: {total}")

if total == 0:
    print("No hay propiedades para eliminar")
    exit(0)

confirm = input(f"\nELIMINAR {total} propiedades? (escribe 'SI' para confirmar): ")
if confirm != 'SI':
    print("Cancelado")
    exit(0)

# Eliminar en lotes de 100
print(f"\nEliminando {total} propiedades...")
batch_size = 100
deleted = 0

for i in range(0, total, batch_size):
    batch = all_props[i:i+batch_size]
    try:
        models.execute_kw(
            config['db'], uid, config['password'],
            'product.template', 'unlink',
            [batch]
        )
        deleted += len(batch)
        print(f"  Eliminadas: {deleted}/{total}")
    except Exception as e:
        print(f"  Error: {e}")

print(f"\nTOTAL ELIMINADAS: {deleted}/{total}")

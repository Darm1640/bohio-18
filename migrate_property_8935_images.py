#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migración de imágenes para Propiedad ID: 8935
Auto-generado desde: https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8935
"""
import xmlrpc.client
import requests
import base64

# Configuración Odoo
ODOO_URL = 'http://localhost:8069'
ODOO_DB = 'bohio_db'
ODOO_USER = 'admin'
ODOO_PASS = 'admin'

# Conectar
common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASS, {})
models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

# Buscar propiedad por código
# AJUSTAR: Usar el criterio correcto para buscar tu propiedad
property_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASS,
    'product.template', 'search',
    [[('default_code', '=', 'BOH-8935')]]  # O el campo que uses
)

if not property_ids:
    print(f"❌ Propiedad BOH-8935 no encontrada")
    exit(1)

property_id = property_ids[0]
print(f"✅ Propiedad encontrada: ID={property_id}")

# Imágenes a migrar
images_data = [
    {
        'sequence': 1,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6519.JPG',
        'filename': '800x600_GOPR6519.JPG',
        'is_cover': True,
        'image_type': 'main'
    },
    {
        'sequence': 2,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6515.JPG',
        'filename': '800x600_GOPR6515.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 3,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6516.JPG',
        'filename': '800x600_GOPR6516.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 4,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6479.JPG',
        'filename': '800x600_GOPR6479.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 5,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6481.JPG',
        'filename': '800x600_GOPR6481.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 6,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6487.JPG',
        'filename': '800x600_GOPR6487.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 7,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6489.JPG',
        'filename': '800x600_GOPR6489.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 8,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6491.JPG',
        'filename': '800x600_GOPR6491.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 9,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6495.JPG',
        'filename': '800x600_GOPR6495.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 10,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6497.JPG',
        'filename': '800x600_GOPR6497.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 11,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6498.JPG',
        'filename': '800x600_GOPR6498.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 12,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6499.JPG',
        'filename': '800x600_GOPR6499.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 13,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6500.JPG',
        'filename': '800x600_GOPR6500.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 14,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6501.JPG',
        'filename': '800x600_GOPR6501.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 15,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6503.JPG',
        'filename': '800x600_GOPR6503.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 16,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6505.JPG',
        'filename': '800x600_GOPR6505.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 17,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6507.JPG',
        'filename': '800x600_GOPR6507.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 18,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_eaca4c98ade23dfe_GOPR6544.JPG',
        'filename': '800x600_eaca4c98ade23dfe_GOPR6544.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 19,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6545.JPG',
        'filename': '800x600_GOPR6545.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 20,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6523.JPG',
        'filename': '800x600_GOPR6523.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 21,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6535.JPG',
        'filename': '800x600_GOPR6535.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 22,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6542.JPG',
        'filename': '800x600_GOPR6542.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 23,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6524.JPG',
        'filename': '800x600_GOPR6524.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 24,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6528.JPG',
        'filename': '800x600_GOPR6528.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 25,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6531.JPG',
        'filename': '800x600_GOPR6531.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
    {
        'sequence': 26,
        'url': 'https://bohio.arrendasoft.co/img/big/800x600_GOPR6534.JPG',
        'filename': '800x600_GOPR6534.JPG',
        'is_cover': False,
        'image_type': 'other'
    },
]

# Descargar y crear imágenes en Odoo
for img_data in images_data:
    try:
        print(f"\n📥 Descargando: {img_data['filename']}")
        response = requests.get(img_data['url'], timeout=30)
        response.raise_for_status()

        # Convertir a base64
        image_base64 = base64.b64encode(response.content).decode('utf-8')

        # Crear registro de imagen en property.image
        vals = {
            'name': img_data['filename'],
            'property_id': property_id,
            'sequence': img_data['sequence'],
            'is_cover': img_data['is_cover'],
            'image_type': img_data['image_type'],
            'image_1920': image_base64,
            'is_public': True
        }

        image_id = models.execute_kw(
            ODOO_DB, uid, ODOO_PASS,
            'property.image', 'create',
            [vals]
        )

        print(f"   ✅ Imagen creada: ID={image_id}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n✅ Migración completada")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para extraer imágenes de propiedades desde URLs de bohioconsultores.com
y preparar la estructura para migración a Odoo 18
"""
import re
import sys
import io
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

# Configurar salida UTF-8 para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class PropertyImageExtractor:
    """Extractor de imágenes de propiedades desde bohioconsultores.com"""

    def __init__(self):
        self.base_url = "https://bohioconsultores.com"
        self.image_base = "https://bohio.arrendasoft.co/img/big/"

    def extract_property_id_from_url(self, url):
        """
        Extrae el ID de propiedad desde URL
        Ejemplo: https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8935
        Retorna: 8935
        """
        # Buscar número al final de la URL
        match = re.search(r'-(\d+)$', url)
        if match:
            return match.group(1)

        # Intentar desde query params
        parsed = urlparse(url)
        query = parse_qs(parsed.query)

        # Buscar en cualquier parámetro
        for key, values in query.items():
            for value in values:
                match = re.search(r'-(\d+)$', value)
                if match:
                    return match.group(1)

        return None

    def fetch_property_page(self, url):
        """Obtiene el HTML de la página de propiedad"""
        try:
            print(f"\n📥 Obteniendo página: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"❌ Error obteniendo página: {e}")
            return None

    def extract_images_from_html(self, html):
        """
        Extrae todas las URLs de imágenes desde el HTML
        Busca imágenes de bohio.arrendasoft.co
        """
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        images = []

        # Buscar todas las imágenes en tags <img> y <a>
        for tag in soup.find_all(['img', 'a']):
            # Buscar en src, href, data-src
            for attr in ['src', 'href', 'data-src']:
                url = tag.get(attr, '')

                # Filtrar solo imágenes de arrendasoft
                if 'bohio.arrendasoft.co/img' in url and url.endswith(('.JPG', '.jpg', '.PNG', '.png')):
                    # Extraer nombre de archivo
                    filename = url.split('/')[-1]

                    if filename not in [img['filename'] for img in images]:
                        images.append({
                            'url': url,
                            'filename': filename,
                            'is_main': len(images) == 0  # Primera imagen es principal
                        })

        return images

    def extract_property_info(self, html, property_id):
        """Extrae información adicional de la propiedad"""
        if not html:
            return {}

        soup = BeautifulSoup(html, 'html.parser')

        info = {
            'property_id': property_id,
            'title': '',
            'price': '',
            'location': '',
            'type': ''
        }

        # Intentar extraer título
        title_tag = soup.find('h1')
        if title_tag:
            info['title'] = title_tag.get_text(strip=True)

            # Detectar tipo de propiedad desde título
            title_lower = info['title'].lower()
            if 'apartamento' in title_lower:
                info['type'] = 'Apartamento'
            elif 'casa' in title_lower:
                info['type'] = 'Casa'
            elif 'lote' in title_lower or 'terreno' in title_lower:
                info['type'] = 'Lote'
            elif 'bodega' in title_lower:
                info['type'] = 'Bodega'
            elif 'oficina' in title_lower:
                info['type'] = 'Oficina'

        return info

    def process_property_url(self, url):
        """
        Procesa una URL de propiedad completa
        Retorna información de la propiedad e imágenes
        """
        print("\n" + "="*80)
        print("🏠 EXTRACTOR DE IMÁGENES DE PROPIEDADES")
        print("="*80)

        # 1. Extraer ID
        property_id = self.extract_property_id_from_url(url)
        if not property_id:
            print(f"❌ No se pudo extraer ID de propiedad desde: {url}")
            return None

        print(f"\n✅ ID de Propiedad: {property_id}")

        # 2. Obtener HTML
        html = self.fetch_property_page(url)
        if not html:
            return None

        # 3. Extraer imágenes
        images = self.extract_images_from_html(html)
        print(f"\n📸 Total imágenes encontradas: {len(images)}")

        if images:
            print("\n🖼️  Lista de imágenes:")
            for idx, img in enumerate(images, 1):
                status = "⭐ PRINCIPAL" if img['is_main'] else "  "
                print(f"   {idx:2d}. {status} {img['filename']}")
                print(f"       URL: {img['url']}")

        # 4. Extraer info adicional
        info = self.extract_property_info(html, property_id)

        print(f"\n📋 Información de la propiedad:")
        print(f"   Título: {info.get('title', 'N/A')}")
        print(f"   Tipo: {info.get('type', 'N/A')}")

        # 5. Retornar estructura completa
        return {
            'property_id': property_id,
            'url': url,
            'info': info,
            'images': images,
            'total_images': len(images)
        }

    def generate_odoo_migration_script(self, property_data):
        """
        Genera un script Python para migrar las imágenes a Odoo 18
        """
        if not property_data or not property_data.get('images'):
            return None

        prop_id = property_data['property_id']

        script = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de migración de imágenes para Propiedad ID: {prop_id}
Auto-generado desde: {property_data['url']}
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
common = xmlrpc.client.ServerProxy(f'{{ODOO_URL}}/xmlrpc/2/common')
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASS, {{}})
models = xmlrpc.client.ServerProxy(f'{{ODOO_URL}}/xmlrpc/2/object')

# Buscar propiedad por código
# AJUSTAR: Usar el criterio correcto para buscar tu propiedad
property_ids = models.execute_kw(
    ODOO_DB, uid, ODOO_PASS,
    'product.template', 'search',
    [[('default_code', '=', 'BOH-{prop_id}')]]  # O el campo que uses
)

if not property_ids:
    print(f"❌ Propiedad BOH-{prop_id} no encontrada")
    exit(1)

property_id = property_ids[0]
print(f"✅ Propiedad encontrada: ID={{property_id}}")

# Imágenes a migrar
images_data = [
'''

        for idx, img in enumerate(property_data['images'], 1):
            script += f'''    {{
        'sequence': {idx},
        'url': '{img['url']}',
        'filename': '{img['filename']}',
        'is_cover': {str(img['is_main'])},
        'image_type': '{'main' if img['is_main'] else 'other'}'
    }},
'''

        script += ''']

# Descargar y crear imágenes en Odoo
for img_data in images_data:
    try:
        print(f"\\n📥 Descargando: {img_data['filename']}")
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

print("\\n✅ Migración completada")
'''

        return script


def main():
    """Función principal"""

    # URLs de ejemplo
    urls = [
        "https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8935",
        "https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta%20y%20Arriendo-8933"
    ]

    extractor = PropertyImageExtractor()

    # Permitir URL por argumento
    if len(sys.argv) > 1:
        urls = [sys.argv[1]]

    for url in urls:
        # Procesar propiedad
        result = extractor.process_property_url(url)

        if result and result['images']:
            # Generar script de migración
            migration_script = extractor.generate_odoo_migration_script(result)

            # Guardar script
            script_filename = f"migrate_property_{result['property_id']}_images.py"
            with open(script_filename, 'w', encoding='utf-8') as f:
                f.write(migration_script)

            print(f"\n💾 Script de migración guardado: {script_filename}")
            print(f"\n📝 Para ejecutar:")
            print(f"   python {script_filename}")

        print("\n" + "="*80)


if __name__ == "__main__":
    main()

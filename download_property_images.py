#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para descargar imágenes de propiedades desde bohioconsultores.com
y guardarlas localmente organizadas por código de propiedad
"""
import re
import sys
import io
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

# Configurar salida UTF-8 para Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class PropertyImageDownloader:
    """Descargador de imágenes de propiedades desde bohioconsultores.com"""

    def __init__(self, download_dir="property_images"):
        self.base_url = "https://bohioconsultores.com"
        self.image_base = "https://bohio.arrendasoft.co/img/big/"
        self.download_dir = download_dir

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

    def download_images_locally(self, property_id, images):
        """
        Descarga imágenes localmente en carpeta con código de propiedad
        """
        if not images:
            print("⚠️  No hay imágenes para descargar")
            return []

        # Crear directorio para la propiedad
        property_dir = os.path.join(self.download_dir, property_id)
        os.makedirs(property_dir, exist_ok=True)

        print(f"\n📁 Carpeta de descarga: {os.path.abspath(property_dir)}")
        print(f"📥 Descargando {len(images)} imágenes...\n")

        downloaded = []
        for idx, img in enumerate(images, 1):
            try:
                # Descargar imagen
                response = requests.get(img['url'], timeout=30)
                response.raise_for_status()

                # Guardar archivo
                file_path = os.path.join(property_dir, img['filename'])
                with open(file_path, 'wb') as f:
                    f.write(response.content)

                file_size = len(response.content) / 1024  # KB
                status = "⭐ PRINCIPAL" if img['is_main'] else "  "
                print(f"   {idx:2d}. {status} {img['filename']:40s} ({file_size:7.1f} KB)")

                downloaded.append({
                    **img,
                    'local_path': file_path,
                    'size_kb': file_size
                })

            except Exception as e:
                print(f"   ❌ Error descargando {img['filename']}: {e}")

        print(f"\n✅ {len(downloaded)} de {len(images)} imágenes descargadas exitosamente")
        return downloaded

    def process_property_url(self, url, download_locally=True):
        """
        Procesa una URL de propiedad completa
        Retorna información de la propiedad e imágenes
        """
        print("\n" + "="*80)
        print("🏠 DESCARGADOR DE IMÁGENES DE PROPIEDADES")
        print("="*80)

        # 1. Extraer ID
        property_id = self.extract_property_id_from_url(url)
        if not property_id:
            print(f"❌ No se pudo extraer ID de propiedad desde: {url}")
            return None

        print(f"\n✅ Código de Propiedad: {property_id}")

        # 2. Obtener HTML
        html = self.fetch_property_page(url)
        if not html:
            return None

        # 3. Extraer imágenes
        images = self.extract_images_from_html(html)
        print(f"\n📸 Total imágenes encontradas: {len(images)}")

        # 4. Extraer info adicional
        info = self.extract_property_info(html, property_id)

        if info.get('title') or info.get('type'):
            print(f"\n📋 Información de la propiedad:")
            if info.get('title'):
                print(f"   Título: {info['title']}")
            if info.get('type'):
                print(f"   Tipo: {info['type']}")

        # 5. Descargar imágenes localmente
        downloaded_images = []
        if download_locally and images:
            downloaded_images = self.download_images_locally(property_id, images)

        # 6. Retornar estructura completa
        return {
            'property_id': property_id,
            'url': url,
            'info': info,
            'images': images,
            'downloaded_images': downloaded_images,
            'total_images': len(images),
            'local_folder': os.path.abspath(os.path.join(self.download_dir, property_id)) if download_locally else None
        }


def main():
    """Función principal"""

    print("="*80)
    print("DESCARGADOR DE IMÁGENES DE PROPIEDADES - BOHIO CONSULTORES")
    print("="*80)

    # Obtener URL
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        print("\n📝 USO:")
        print("   python download_property_images.py <URL_PROPIEDAD>")
        print("\n📝 EJEMPLOS:")
        print('   python download_property_images.py "https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-8935"')
        print('   python download_property_images.py "https://bohioconsultores.com/detalle-propiedad/?Casa-en-Venta-8747"')
        print("\n💡 TIP: Puedes pegar directamente la URL desde el navegador")
        return

    # Procesar propiedad
    downloader = PropertyImageDownloader()
    result = downloader.process_property_url(url, download_locally=True)

    if result and result['downloaded_images']:
        print("\n" + "="*80)
        print("📊 RESUMEN DE DESCARGA")
        print("="*80)
        print(f"   Código Propiedad: {result['property_id']}")
        print(f"   Total Imágenes: {len(result['downloaded_images'])}")
        print(f"   Carpeta Local: {result['local_folder']}")

        # Calcular tamaño total
        total_size = sum(img['size_kb'] for img in result['downloaded_images'])
        print(f"   Tamaño Total: {total_size:.1f} KB ({total_size/1024:.2f} MB)")

        # Imagen principal
        main_image = next((img for img in result['downloaded_images'] if img['is_main']), None)
        if main_image:
            print(f"   Imagen Principal: {main_image['filename']}")

        print("="*80)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("="*80)

    else:
        print("\n❌ No se pudieron descargar imágenes")


if __name__ == "__main__":
    main()

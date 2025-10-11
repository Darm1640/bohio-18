#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para extraer URLs de propiedades desde página de búsqueda
y descargar todas las imágenes automáticamente
"""
import os
import sys
import time
import requests
from bs4 import BeautifulSoup

# Importar downloader
sys.path.insert(0, os.path.dirname(__file__))
from download_property_images import PropertyImageDownloader


class PropertyURLScraper:
    """Extrae URLs de propiedades desde página de búsqueda"""

    def __init__(self, output_file="property_urls.txt"):
        self.base_url = "https://bohioconsultores.com/resultados-de-busqueda/"
        self.output_file = output_file
        self.downloader = PropertyImageDownloader()

    def scrape_search_page(self, page=1, servicio=2):
        """
        Extrae propiedades de una página de búsqueda
        servicio: 1=Arriendo, 2=Venta, 3=Venta y Arriendo
        """
        url = f"{self.base_url}?Servicio={servicio}"

        try:
            print(f"\n📥 Obteniendo página {page} de búsqueda...")
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"❌ Error obteniendo página: {e}")
            return None

    def extract_property_urls_from_html(self, html):
        """Extrae URLs de propiedades desde HTML"""
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        urls = []

        # Buscar divs con clase 'caja movil-50'
        property_boxes = soup.find_all('div', class_='caja movil-50')

        for box in property_boxes:
            # Buscar el primer enlace <a href="...detalle-propiedad...">
            link = box.find('a', href=True)
            if link and 'detalle-propiedad' in link['href']:
                url = link['href']

                # Asegurar URL completa
                if not url.startswith('http'):
                    url = f"https://bohioconsultores.com{url}"

                # Extraer código
                code = self.downloader.extract_property_id_from_url(url)

                if url not in [u['url'] for u in urls]:
                    urls.append({
                        'url': url,
                        'code': code,
                        'found_in': 'search_page'
                    })

        return urls

    def save_urls_to_file(self, urls):
        """Guarda URLs en archivo de texto"""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write("# URLs DE PROPIEDADES EXTRAÍDAS\n")
                f.write(f"# Total: {len(urls)}\n")
                f.write(f"# Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("\n")

                for item in urls:
                    f.write(f"{item['code']}|{item['url']}\n")

            print(f"\n✅ URLs guardadas en: {self.output_file}")
            return True

        except Exception as e:
            print(f"❌ Error guardando URLs: {e}")
            return False

    def scrape_all_pages(self, max_pages=103):
        """
        Extrae URLs de todas las páginas de búsqueda
        max_pages: 103 según el HTML mostrado
        """
        print("\n" + "="*80)
        print("EXTRACTOR DE URLs DE PROPIEDADES")
        print("="*80)

        all_urls = []

        # Para esta página con AJAX, intentamos obtener directamente
        print(f"\n🔍 Extrayendo URLs de página de búsqueda...")

        html = self.scrape_search_page(page=1, servicio=2)
        urls = self.extract_property_urls_from_html(html)

        if urls:
            print(f"✅ Encontradas {len(urls)} URLs en la página")
            all_urls.extend(urls)

        # Guardar en archivo
        if all_urls:
            self.save_urls_to_file(all_urls)

            print("\n📊 RESUMEN:")
            print(f"   Total URLs extraídas: {len(all_urls)}")
            print(f"   Archivo: {self.output_file}")

        return all_urls

    def download_from_urls_file(self, urls_file=None):
        """Descarga imágenes desde archivo de URLs"""
        if urls_file is None:
            urls_file = self.output_file

        if not os.path.exists(urls_file):
            print(f"❌ Archivo no encontrado: {urls_file}")
            return

        print("\n" + "="*80)
        print("DESCARGA DE IMÁGENES DESDE ARCHIVO DE URLs")
        print("="*80)

        # Leer URLs
        urls = []
        with open(urls_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Formato: CODE|URL
                    parts = line.split('|')
                    if len(parts) == 2:
                        urls.append({
                            'code': parts[0],
                            'url': parts[1]
                        })

        print(f"\n📋 URLs encontradas en archivo: {len(urls)}")

        # Estadísticas
        stats = {
            'total': len(urls),
            'success': 0,
            'failed': 0,
            'no_images': 0,
            'total_images': 0
        }

        # Procesar cada URL
        for idx, item in enumerate(urls, 1):
            print(f"\n[{idx}/{len(urls)}] Código: {item['code']}")
            print("-" * 80)

            try:
                result = self.downloader.process_property_url(item['url'], download_locally=True)

                if result and result.get('downloaded_images'):
                    stats['success'] += 1
                    stats['total_images'] += len(result['downloaded_images'])
                    print(f"✅ {len(result['downloaded_images'])} imágenes descargadas")
                elif result:
                    stats['no_images'] += 1
                    print(f"⚠️  Sin imágenes")
                else:
                    stats['failed'] += 1
                    print(f"❌ Error procesando")

            except Exception as e:
                stats['failed'] += 1
                print(f"❌ Error: {e}")

            # Pausa entre descargas
            if idx < len(urls):
                time.sleep(1)

        # Reporte final
        print("\n" + "="*80)
        print("📊 REPORTE FINAL")
        print("="*80)
        print(f"   Total Procesadas: {stats['total']}")
        print(f"   ✅ Exitosas: {stats['success']}")
        print(f"   ❌ Fallidas: {stats['failed']}")
        print(f"   ⚠️  Sin imágenes: {stats['no_images']}")
        print(f"   📸 Total Imágenes: {stats['total_images']}")
        print("="*80)

        return stats


def main():
    """Función principal"""

    print("="*80)
    print("SISTEMA COMPLETO: EXTRAER URLs Y DESCARGAR IMÁGENES")
    print("="*80)

    scraper = PropertyURLScraper(output_file="property_urls.txt")

    # Opción 1: Solo extraer URLs
    if len(sys.argv) > 1 and sys.argv[1] == '--extract-only':
        print("\n💡 Modo: Solo extracción de URLs")
        scraper.scrape_all_pages()
        return

    # Opción 2: Solo descargar desde archivo existente
    if len(sys.argv) > 1 and sys.argv[1] == '--download-only':
        print("\n💡 Modo: Solo descarga desde archivo")
        scraper.download_from_urls_file()
        return

    # Opción 3: Proceso completo (extraer + descargar)
    print("\n💡 Modo: Proceso completo (extraer + descargar)")

    # Paso 1: Extraer URLs
    urls = scraper.scrape_all_pages()

    if not urls:
        print("\n❌ No se pudieron extraer URLs")
        return

    # Paso 2: Preguntar si descargar
    print("\n" + "="*80)
    response = input("¿Desea descargar las imágenes ahora? (s/n): ")

    if response.lower() == 's':
        scraper.download_from_urls_file()
    else:
        print("\n💡 Para descargar después, ejecute:")
        print(f"   python {sys.argv[0]} --download-only")


if __name__ == "__main__":
    main()

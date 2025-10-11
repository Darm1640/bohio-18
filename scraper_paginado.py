#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema completo de scraping con paginación
- Navega página por página
- Extrae URLs de cada página
- Descarga imágenes automáticamente
- Marca progreso en archivo
- Puede reanudar desde donde se quedó
"""
import os
import sys
import time
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from download_property_images import PropertyImageDownloader


class PaginatedScraper:
    """Scraper con paginación y tracking de progreso"""

    def __init__(self, progress_file="scraping_progress.json"):
        self.base_url = "https://bohioconsultores.com/resultados-de-busqueda/"
        self.progress_file = progress_file
        self.downloader = PropertyImageDownloader()
        self.progress = self.load_progress()

    def load_progress(self):
        """Carga progreso desde archivo JSON"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        # Progreso inicial
        return {
            'last_page': 0,
            'total_pages': 103,
            'processed_codes': [],
            'failed_codes': [],
            'stats': {
                'total_found': 0,
                'total_downloaded': 0,
                'total_images': 0,
                'total_failed': 0,
                'no_images': 0
            },
            'started_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }

    def save_progress(self):
        """Guarda progreso en archivo JSON"""
        self.progress['last_updated'] = datetime.now().isoformat()
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"⚠️  Error guardando progreso: {e}")
            return False

    def fetch_page(self, page_num=1):
        """
        Obtiene una página de resultados
        NOTA: La paginación puede ser por AJAX, necesitamos analizar el comportamiento
        """
        url = f"{self.base_url}?Servicio=2"

        # Si hay paginación por parámetro
        if page_num > 1:
            url += f"&page={page_num}"

        try:
            print(f"\n📄 Obteniendo página {page_num}/{self.progress['total_pages']}...")
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def extract_urls_from_page(self, html):
        """Extrae URLs de propiedades de una página"""
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        properties = []

        # Buscar todos los boxes de propiedades
        boxes = soup.find_all('div', class_='caja movil-50')

        for box in boxes:
            try:
                # Buscar enlace
                link = box.find('a', href=True)
                if not link or 'detalle-propiedad' not in link['href']:
                    continue

                url = link['href']
                if not url.startswith('http'):
                    url = f"https://bohioconsultores.com{url}"

                # Extraer código
                code = self.downloader.extract_property_id_from_url(url)

                # Extraer imagen preview (opcional)
                img = box.find('img', src=True)
                preview_img = img['src'] if img else None

                # Extraer info adicional
                caption = box.find('div', class_='contenido')
                address = ""
                property_type = ""

                if caption:
                    addr_p = caption.find('p', class_='properties_address')
                    if addr_p:
                        address = addr_p.get_text(strip=True)

                    type_p = caption.find('p', class_='sc_properties_item_type')
                    if type_p:
                        property_type = type_p.get_text(strip=True)

                properties.append({
                    'code': code,
                    'url': url,
                    'address': address,
                    'type': property_type,
                    'preview_img': preview_img
                })

            except Exception as e:
                print(f"⚠️  Error procesando box: {e}")
                continue

        return properties

    def is_already_processed(self, code):
        """Verifica si un código ya fue procesado"""
        return code in self.progress['processed_codes']

    def mark_as_processed(self, code, success=True):
        """Marca un código como procesado"""
        if success:
            if code not in self.progress['processed_codes']:
                self.progress['processed_codes'].append(code)
        else:
            if code not in self.progress['failed_codes']:
                self.progress['failed_codes'].append(code)

        self.save_progress()

    def download_property_images(self, property_data):
        """Descarga imágenes de una propiedad"""
        code = property_data['code']
        url = property_data['url']

        print(f"\n📥 Propiedad: {code}")
        print(f"   Dirección: {property_data['address']}")
        print(f"   Tipo: {property_data['type']}")

        try:
            result = self.downloader.process_property_url(url, download_locally=True)

            if result and result.get('downloaded_images'):
                images_count = len(result['downloaded_images'])
                print(f"✅ {images_count} imágenes descargadas")

                self.progress['stats']['total_downloaded'] += 1
                self.progress['stats']['total_images'] += images_count
                self.mark_as_processed(code, success=True)
                return True

            elif result:
                print(f"⚠️  Sin imágenes")
                self.progress['stats']['no_images'] += 1
                self.mark_as_processed(code, success=True)
                return True

            else:
                print(f"❌ Error descargando")
                self.progress['stats']['total_failed'] += 1
                self.mark_as_processed(code, success=False)
                return False

        except Exception as e:
            print(f"❌ Error: {e}")
            self.progress['stats']['total_failed'] += 1
            self.mark_as_processed(code, success=False)
            return False

    def process_all_pages(self, start_page=None, max_pages=None):
        """
        Procesa todas las páginas
        start_page: página desde donde empezar (None = continuar desde última)
        max_pages: máximo de páginas a procesar (None = todas)
        """
        print("\n" + "="*80)
        print("SCRAPER PAGINADO - EXTRACCIÓN Y DESCARGA COMPLETA")
        print("="*80)

        # Determinar página inicial
        if start_page is None:
            start_page = self.progress['last_page'] + 1

        if start_page > 1:
            print(f"\n🔄 Continuando desde página {start_page}")

        print(f"\n📊 Progreso anterior:")
        print(f"   Procesadas: {len(self.progress['processed_codes'])}")
        print(f"   Fallidas: {len(self.progress['failed_codes'])}")
        print(f"   Total imágenes: {self.progress['stats']['total_images']}")

        # IMPORTANTE: Por ahora, la paginación parece ser por AJAX
        # Vamos a extraer de la primera página y procesar
        print("\n⚠️  NOTA: La paginación parece ser por AJAX.")
        print("   Procesando propiedades visibles en página actual...")

        # Obtener página
        html = self.fetch_page(page_num=1)

        if not html:
            print("❌ No se pudo obtener la página")
            return

        # Extraer propiedades
        properties = self.extract_urls_from_page(html)

        if not properties:
            print("❌ No se encontraron propiedades")
            return

        print(f"\n✅ Encontradas {len(properties)} propiedades en la página")
        self.progress['stats']['total_found'] += len(properties)

        # Filtrar ya procesadas
        to_process = [p for p in properties if not self.is_already_processed(p['code'])]

        if not to_process:
            print("\n✅ Todas las propiedades de esta página ya fueron procesadas")
            return

        print(f"📋 Por procesar: {len(to_process)}")

        # Procesar cada propiedad
        for idx, prop in enumerate(to_process, 1):
            print(f"\n[{idx}/{len(to_process)}] " + "="*60)

            self.download_property_images(prop)

            # Guardar progreso cada 5 propiedades
            if idx % 5 == 0:
                self.save_progress()
                print(f"\n💾 Progreso guardado...")

            # Pausa entre descargas
            if idx < len(to_process):
                time.sleep(1)

        # Guardar progreso final
        self.progress['last_page'] = 1
        self.save_progress()

        # Reporte final
        self.print_final_report()

    def print_final_report(self):
        """Imprime reporte final"""
        print("\n" + "="*80)
        print("📊 REPORTE FINAL")
        print("="*80)

        stats = self.progress['stats']

        print(f"\n📈 ESTADÍSTICAS:")
        print(f"   Propiedades encontradas: {stats['total_found']}")
        print(f"   ✅ Descargadas exitosamente: {stats['total_downloaded']}")
        print(f"   ⚠️  Sin imágenes: {stats['no_images']}")
        print(f"   ❌ Fallidas: {stats['total_failed']}")
        print(f"   📸 Total imágenes descargadas: {stats['total_images']}")

        print(f"\n📋 PROCESADAS:")
        print(f"   Total: {len(self.progress['processed_codes'])}")
        if self.progress['processed_codes']:
            print(f"   Últimas 10: {', '.join(self.progress['processed_codes'][-10:])}")

        if self.progress['failed_codes']:
            print(f"\n❌ FALLIDAS ({len(self.progress['failed_codes'])}):")
            print(f"   Códigos: {', '.join(self.progress['failed_codes'][:20])}")

        print(f"\n📁 Archivos:")
        print(f"   Progreso: {self.progress_file}")
        print(f"   Imágenes: property_images/")

        print("\n" + "="*80)

    def export_to_txt(self, output_file="processed_properties.txt"):
        """Exporta lista de propiedades procesadas a TXT"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# PROPIEDADES PROCESADAS\n")
                f.write(f"# Total: {len(self.progress['processed_codes'])}\n")
                f.write(f"# Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("\n")

                f.write("## EXITOSAS\n")
                for code in self.progress['processed_codes']:
                    f.write(f"{code}\n")

                if self.progress['failed_codes']:
                    f.write("\n## FALLIDAS\n")
                    for code in self.progress['failed_codes']:
                        f.write(f"{code}\n")

            print(f"\n✅ Lista exportada a: {output_file}")
            return True

        except Exception as e:
            print(f"❌ Error exportando: {e}")
            return False


def main():
    """Función principal"""

    print("="*80)
    print("SCRAPER PAGINADO CON TRACKING DE PROGRESO")
    print("="*80)

    scraper = PaginatedScraper(progress_file="scraping_progress.json")

    # Verificar si hay progreso previo
    if scraper.progress['last_page'] > 0:
        print(f"\n📋 Progreso anterior detectado:")
        print(f"   Última página: {scraper.progress['last_page']}")
        print(f"   Procesadas: {len(scraper.progress['processed_codes'])}")
        print(f"   Imágenes: {scraper.progress['stats']['total_images']}")

        response = input("\n¿Continuar desde donde se quedó? (s/n): ")
        if response.lower() != 's':
            print("\n🔄 Reiniciando progreso...")
            scraper.progress = scraper.load_progress()
            scraper.progress['last_page'] = 0
            scraper.progress['processed_codes'] = []
            scraper.save_progress()

    # Opciones de línea de comandos
    start_page = None
    max_pages = None

    if len(sys.argv) > 1:
        try:
            start_page = int(sys.argv[1])
        except:
            pass

    if len(sys.argv) > 2:
        try:
            max_pages = int(sys.argv[2])
        except:
            pass

    # Procesar páginas
    scraper.process_all_pages(start_page=start_page, max_pages=max_pages)

    # Exportar lista
    scraper.export_to_txt("processed_properties.txt")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para descargar imágenes navegando página por página
Navega: página 1, 2, 3, 4, 5... hasta 105 o hasta que no haya más resultados
"""
import os
import sys
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote
import re
from download_property_images import PropertyImageDownloader


class PaginatedDownloader:
    """Descarga imágenes navegando página por página en el sitio web"""

    def __init__(self, output_dir="property_images"):
        self.output_dir = output_dir
        self.downloader = PropertyImageDownloader(download_dir=output_dir)
        self.base_url = "https://bohioconsultores.com/resultados-de-busqueda/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def get_page_url(self, page_number, servicio=2):
        """
        Construye URL de página específica
        página 1: ?Servicio=2
        página 2: ?Servicio=2&paged=2
        página 3: ?Servicio=2&paged=3
        """
        if page_number == 1:
            return f"{self.base_url}?Servicio={servicio}"
        else:
            return f"{self.base_url}?Servicio={servicio}&paged={page_number}"

    def fetch_page(self, page_number, servicio=2):
        """Obtiene HTML de una página específica"""
        url = self.get_page_url(page_number, servicio)

        try:
            print(f"\n📥 Obteniendo página {page_number}...")
            print(f"   URL: {url}")

            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'

            print(f"   ✅ Status: {response.status_code}")
            print(f"   📄 Tamaño: {len(response.text)} caracteres")

            return response.text

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None

    def extract_property_links(self, html):
        """Extrae enlaces de propiedades desde HTML"""
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')

        # Buscar enlaces con detalle-propiedad
        pattern_links = soup.find_all('a', href=re.compile(r'detalle-propiedad'))

        links = []
        seen = set()

        for link in pattern_links:
            href = link.get('href', '')
            if 'detalle-propiedad' in href:
                # Decodificar URL
                href_decoded = unquote(href)

                # Evitar duplicados
                if href_decoded not in seen:
                    seen.add(href_decoded)
                    links.append(href_decoded)

        return links

    def scrape_all_pages(self, servicio=2, max_pages=105, delay=2):
        """
        Navega todas las páginas extrayendo enlaces

        Args:
            servicio: 1=Arriendo, 2=Venta
            max_pages: Número máximo de páginas a navegar (default: 105)
            delay: Segundos entre páginas (default: 2)
        """
        print("\n" + "="*80)
        print("🔍 NAVEGACIÓN PAGINADA - BOHIO CONSULTORES")
        print("="*80)

        servicio_text = {1: "ARRIENDO", 2: "VENTA"}.get(servicio, "DESCONOCIDO")
        print(f"\n⚙️  Configuración:")
        print(f"   Tipo: {servicio_text}")
        print(f"   Páginas máximas: {max_pages}")
        print(f"   Delay entre páginas: {delay}s")

        all_links = []
        page_number = 1
        consecutive_empty = 0  # Contador de páginas vacías consecutivas

        while page_number <= max_pages:
            print(f"\n{'='*80}")
            print(f"📄 PÁGINA {page_number}/{max_pages}")
            print(f"{'='*80}")

            # Obtener HTML de la página
            html = self.fetch_page(page_number, servicio)

            if not html:
                print(f"⚠️  No se pudo obtener página {page_number}")
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    print(f"\n⚠️  3 páginas consecutivas sin respuesta, deteniendo...")
                    break
                page_number += 1
                time.sleep(delay)
                continue

            # Extraer enlaces
            links = self.extract_property_links(html)

            print(f"\n📊 Propiedades encontradas: {len(links)}")

            if not links:
                consecutive_empty += 1
                print(f"⚠️  Página vacía ({consecutive_empty}/3)")

                if consecutive_empty >= 3:
                    print(f"\n✅ 3 páginas consecutivas vacías, fin de resultados alcanzado")
                    break
            else:
                consecutive_empty = 0  # Resetear contador

                # Filtrar links nuevos
                new_links = [link for link in links if link not in all_links]
                all_links.extend(new_links)

                print(f"   ✅ Nuevas: {len(new_links)}")
                print(f"   📊 Total acumulado: {len(all_links)}")

                # Mostrar primeros 3 enlaces como muestra
                if new_links:
                    print(f"\n   Muestra de enlaces encontrados:")
                    for i, link in enumerate(new_links[:3], 1):
                        # Extraer código
                        code_match = re.search(r'-(\d+)$', link)
                        code = code_match.group(1) if code_match else "?"
                        print(f"      {i}. Código {code}")

            # Siguiente página
            page_number += 1

            # Pausa entre páginas
            if page_number <= max_pages:
                time.sleep(delay)

        print(f"\n{'='*80}")
        print(f"📊 RESUMEN DE NAVEGACIÓN")
        print(f"{'='*80}")
        print(f"   Páginas navegadas: {page_number - 1}")
        print(f"   Total propiedades encontradas: {len(all_links)}")
        print(f"{'='*80}")

        return all_links

    def download_from_links(self, links, max_properties=None, start_from=0):
        """Descarga imágenes de los enlaces extraídos"""

        print("\n" + "="*80)
        print("📥 DESCARGA DE IMÁGENES")
        print("="*80)

        # Aplicar límites
        if start_from > 0:
            links = links[start_from:]
            print(f"\n🔄 Iniciando desde posición: {start_from}")

        if max_properties:
            links = links[:max_properties]
            print(f"🔢 Limitando a: {max_properties} propiedades")

        print(f"\n🚀 Procesando {len(links)} propiedades...")

        # Estadísticas
        stats = {
            'total': len(links),
            'success': 0,
            'failed': 0,
            'no_images': 0,
            'total_images': 0,
            'failed_urls': []
        }

        # Procesar cada enlace
        for idx, url in enumerate(links, 1):
            print(f"\n{'='*80}")
            print(f"[{idx}/{len(links)}] Procesando propiedad")
            print(f"{'='*80}")

            # Extraer código
            code_match = re.search(r'-(\d+)$', url)
            code = code_match.group(1) if code_match else "N/A"

            print(f"Código: {code}")
            print(f"URL: {url}")

            try:
                # Descargar imágenes
                result = self.downloader.process_property_url(url, download_locally=True)

                if result and result.get('downloaded_images'):
                    stats['success'] += 1
                    stats['total_images'] += len(result['downloaded_images'])
                    print(f"✅ {len(result['downloaded_images'])} imágenes descargadas")
                elif result:
                    stats['no_images'] += 1
                    print(f"⚠️  Sin imágenes")
                else:
                    stats['failed'] += 1
                    stats['failed_urls'].append(url)
                    print(f"❌ Error procesando")

            except Exception as e:
                stats['failed'] += 1
                stats['failed_urls'].append(url)
                print(f"❌ Error: {e}")

            # Pausa entre propiedades
            if idx < len(links):
                time.sleep(1)

        # Reporte final
        print("\n" + "="*80)
        print("📊 REPORTE FINAL")
        print("="*80)
        print(f"   Total Procesadas: {stats['total']}")
        print(f"   ✅ Exitosas: {stats['success']}")
        print(f"   ❌ Fallidas: {stats['failed']}")
        print(f"   ⚠️  Sin imágenes: {stats['no_images']}")
        print(f"   📸 Total Imágenes Descargadas: {stats['total_images']}")

        if stats['failed_urls']:
            print(f"\n📋 URLs Fallidas ({len(stats['failed_urls'])}):")
            for i, url in enumerate(stats['failed_urls'][:10], 1):
                print(f"   {i}. {url}")
            if len(stats['failed_urls']) > 10:
                print(f"   ... y {len(stats['failed_urls']) - 10} más")

        print("="*80)

        return stats

    def run_full_process(self, servicio=2, max_pages=105, max_properties=None,
                        start_from=0, page_delay=2, download_delay=1):
        """
        Proceso completo: navega páginas y descarga imágenes
        """
        print("\n" + "="*80)
        print("🚀 PROCESO COMPLETO - NAVEGACIÓN Y DESCARGA")
        print("="*80)

        # Fase 1: Navegar páginas y extraer enlaces
        links = self.scrape_all_pages(
            servicio=servicio,
            max_pages=max_pages,
            delay=page_delay
        )

        if not links:
            print("\n❌ No se encontraron propiedades")
            return None

        # Guardar enlaces en archivo
        servicio_name = {1: "arriendo", 2: "venta"}.get(servicio, "todas")
        links_file = os.path.join(self.output_dir, f"property_links_{servicio_name}_paginated.txt")
        os.makedirs(self.output_dir, exist_ok=True)

        with open(links_file, 'w', encoding='utf-8') as f:
            for link in links:
                f.write(f"{link}\n")

        print(f"\n💾 Enlaces guardados en: {links_file}")

        # Fase 2: Descargar imágenes
        stats = self.download_from_links(
            links=links,
            max_properties=max_properties,
            start_from=start_from
        )

        print("\n" + "="*80)
        print("✅ PROCESO COMPLETADO")
        print("="*80)

        return {
            'links': links,
            'stats': stats
        }


def main():
    """Función principal"""

    print("="*80)
    print("DESCARGADOR CON NAVEGACIÓN PAGINADA")
    print("="*80)

    # Configuración
    servicio = 2  # 1=Arriendo, 2=Venta
    max_pages = 105  # Máximo de páginas a navegar
    max_properties = None  # None = todas
    start_from = 0  # Índice de inicio

    # Parsear argumentos
    if len(sys.argv) > 1:
        try:
            arg1 = sys.argv[1].lower()
            if arg1 == 'venta':
                servicio = 2
            elif arg1 == 'arriendo':
                servicio = 1
            else:
                max_pages = int(sys.argv[1])
        except:
            print("\n💡 USO:")
            print("   python batch_download_navegacion_paginas.py [tipo] [max_paginas] [max_propiedades]")
            print("\n💡 EJEMPLOS:")
            print("   python batch_download_navegacion_paginas.py venta")
            print("   python batch_download_navegacion_paginas.py venta 10")
            print("   python batch_download_navegacion_paginas.py venta 10 50")
            print("   python batch_download_navegacion_paginas.py arriendo 105")
            print("\n📝 Tipos: venta, arriendo")
            print("📝 Por defecto navega hasta página 105 o hasta que no haya más resultados")
            return

    if len(sys.argv) > 2:
        try:
            max_pages = int(sys.argv[2])
        except:
            pass

    if len(sys.argv) > 3:
        try:
            max_properties = int(sys.argv[3])
        except:
            pass

    # Crear descargador
    downloader = PaginatedDownloader()

    # Ejecutar proceso completo
    downloader.run_full_process(
        servicio=servicio,
        max_pages=max_pages,
        max_properties=max_properties,
        start_from=start_from,
        page_delay=2,  # 2 segundos entre páginas
        download_delay=1  # 1 segundo entre descargas
    )


if __name__ == "__main__":
    main()

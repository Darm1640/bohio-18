#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para descargar imágenes navegando página por página en resultados de búsqueda
Extrae links de propiedades de cada página y descarga sus imágenes
"""
import os
import sys
import io
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import re

# Importar la clase de descarga
sys.path.insert(0, os.path.dirname(__file__))
from download_property_images import PropertyImageDownloader


class PaginatedPropertyScraper:
    """Descarga imágenes navegando página por página en resultados de búsqueda"""

    def __init__(self, output_dir="property_images"):
        self.output_dir = output_dir
        self.downloader = PropertyImageDownloader(download_dir=output_dir)
        self.base_url = "https://bohioconsultores.com"

        # URLs de búsqueda disponibles
        self.search_urls = {
            'venta': "https://bohioconsultores.com/resultados-de-busqueda/?Servicio=2",
            'arriendo': "https://bohioconsultores.com/resultados-de-busqueda/?Servicio=1",
            'todas': "https://bohioconsultores.com/resultados-de-busqueda/"
        }

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def fetch_page(self, url, retry=3):
        """Obtiene una página con reintentos"""
        for attempt in range(retry):
            try:
                print(f"\n📥 Obteniendo: {url}")
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                response.encoding = 'utf-8'
                return response.text
            except Exception as e:
                print(f"⚠️  Intento {attempt + 1}/{retry} falló: {e}")
                if attempt < retry - 1:
                    time.sleep(2)
                else:
                    print(f"❌ Error después de {retry} intentos")
                    return None

    def extract_property_links_from_page(self, html):
        """
        Extrae todos los enlaces de propiedades desde una página de resultados
        """
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        property_links = []

        # Buscar enlaces que contengan "detalle-propiedad"
        for link in soup.find_all('a', href=True):
            href = link['href']

            # Filtrar solo enlaces de detalle de propiedad
            if 'detalle-propiedad' in href:
                # Construir URL completa
                full_url = urljoin(self.base_url, href)

                # Evitar duplicados
                if full_url not in property_links:
                    property_links.append(full_url)

        return property_links

    def extract_next_page_link(self, html):
        """
        Extrae el enlace a la siguiente página de resultados
        Busca botones de paginación, enlaces "Siguiente", etc.
        """
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Estrategia 1: Buscar enlace con texto "Siguiente", "Next", ">"
        patterns = ['siguiente', 'next', '›', '»', '→']
        for pattern in patterns:
            link = soup.find('a', string=re.compile(pattern, re.IGNORECASE))
            if link and link.get('href'):
                return urljoin(self.base_url, link['href'])

        # Estrategia 2: Buscar en clases comunes de paginación
        pagination_classes = ['pagination', 'pager', 'page-numbers', 'nav-links']
        for class_name in pagination_classes:
            pagination = soup.find(class_=re.compile(class_name, re.IGNORECASE))
            if pagination:
                # Buscar el último enlace activo (usualmente es "siguiente")
                links = pagination.find_all('a', href=True)
                if links:
                    # Tomar el último enlace
                    last_link = links[-1]
                    return urljoin(self.base_url, last_link['href'])

        # Estrategia 3: Buscar parámetros de página en URL
        # Ejemplo: ?page=2, ?p=2, ?pag=2
        current_page_match = re.search(r'[?&](page|p|pag|pagina)=(\d+)', html)
        if current_page_match:
            param_name = current_page_match.group(1)
            current_page = int(current_page_match.group(2))
            next_page = current_page + 1

            # Buscar URL base
            base_search = soup.find('form', {'action': re.compile('resultados-de-busqueda')})
            if base_search:
                action = base_search.get('action', '')
                return f"{action}?{param_name}={next_page}"

        return None

    def detect_pagination_info(self, html):
        """
        Detecta información de paginación: página actual, total de páginas, etc.
        """
        if not html:
            return {}

        soup = BeautifulSoup(html, 'html.parser')
        info = {
            'current_page': 1,
            'total_pages': None,
            'total_results': None
        }

        # Buscar texto como "Página 2 de 10" o "Resultados 1-20 de 145"
        text_patterns = [
            r'p[aá]gina\s+(\d+)\s+de\s+(\d+)',
            r'page\s+(\d+)\s+of\s+(\d+)',
            r'(\d+)\s+de\s+(\d+)\s+p[aá]ginas',
            r'resultados?\s+\d+-\d+\s+de\s+(\d+)',
        ]

        page_text = soup.get_text()
        for pattern in text_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    info['current_page'] = int(groups[0])
                    info['total_pages'] = int(groups[1])
                elif len(groups) == 1:
                    info['total_results'] = int(groups[0])
                break

        return info

    def scrape_all_pages(self, search_type='venta', max_pages=None, delay=2):
        """
        Navega todas las páginas de resultados y extrae enlaces de propiedades

        Args:
            search_type: 'venta', 'arriendo', o 'todas'
            max_pages: Número máximo de páginas a procesar (None = todas)
            delay: Segundos de espera entre páginas
        """
        print("\n" + "="*80)
        print("🔍 EXTRACTOR DE PROPIEDADES - NAVEGACIÓN PAGINADA")
        print("="*80)

        # Obtener URL de búsqueda
        search_url = self.search_urls.get(search_type, self.search_urls['venta'])
        print(f"\n🎯 Tipo de búsqueda: {search_type.upper()}")
        print(f"📍 URL base: {search_url}")

        all_property_links = []
        current_url = search_url
        page_number = 1

        while current_url:
            print(f"\n{'='*80}")
            print(f"📄 PÁGINA {page_number}")
            print(f"{'='*80}")

            # Obtener página
            html = self.fetch_page(current_url)
            if not html:
                print(f"❌ No se pudo obtener la página {page_number}")
                break

            # Detectar información de paginación
            pagination_info = self.detect_pagination_info(html)
            if pagination_info.get('total_pages'):
                print(f"📊 Página {pagination_info['current_page']} de {pagination_info['total_pages']}")
            if pagination_info.get('total_results'):
                print(f"📊 Total resultados: {pagination_info['total_results']}")

            # Extraer enlaces de propiedades
            property_links = self.extract_property_links_from_page(html)
            print(f"🏠 Propiedades encontradas en esta página: {len(property_links)}")

            # Agregar a lista total (evitar duplicados)
            new_links = [link for link in property_links if link not in all_property_links]
            all_property_links.extend(new_links)
            print(f"✅ Nuevas propiedades: {len(new_links)}")
            print(f"📊 Total acumulado: {len(all_property_links)}")

            # Verificar si continuar
            if max_pages and page_number >= max_pages:
                print(f"\n⏸️  Límite de páginas alcanzado: {max_pages}")
                break

            # Buscar siguiente página
            next_url = self.extract_next_page_link(html)
            if next_url:
                print(f"\n➡️  Siguiente página encontrada")
                current_url = next_url
                page_number += 1

                # Esperar antes de siguiente página
                print(f"⏱️  Esperando {delay} segundos...")
                time.sleep(delay)
            else:
                print(f"\n🏁 No hay más páginas")
                break

        print("\n" + "="*80)
        print("📊 RESUMEN DE EXTRACCIÓN")
        print("="*80)
        print(f"   Páginas procesadas: {page_number}")
        print(f"   Total propiedades encontradas: {len(all_property_links)}")
        print("="*80)

        return all_property_links

    def download_from_links(self, property_links, max_properties=None, start_from=0, delay=1):
        """
        Descarga imágenes de una lista de enlaces de propiedades
        """
        print("\n" + "="*80)
        print("📥 DESCARGA DE IMÁGENES")
        print("="*80)

        # Aplicar límites
        if start_from > 0:
            property_links = property_links[start_from:]
            print(f"🔄 Iniciando desde posición: {start_from}")

        if max_properties:
            property_links = property_links[:max_properties]
            print(f"🔢 Limitando a: {max_properties} propiedades")

        print(f"\n🚀 Procesando {len(property_links)} propiedades...")

        # Estadísticas
        stats = {
            'total': len(property_links),
            'success': 0,
            'failed': 0,
            'no_images': 0,
            'total_images': 0,
            'failed_urls': []
        }

        # Procesar cada enlace
        for idx, url in enumerate(property_links, 1):
            print(f"\n{'='*80}")
            print(f"[{idx}/{len(property_links)}] Procesando propiedad")
            print(f"{'='*80}")
            print(f"🔗 URL: {url}")

            try:
                # Descargar imágenes
                result = self.downloader.process_property_url(url, download_locally=True)

                if result and result.get('downloaded_images'):
                    stats['success'] += 1
                    stats['total_images'] += len(result['downloaded_images'])
                    print(f"✅ Código {result['property_id']}: {len(result['downloaded_images'])} imágenes")
                elif result:
                    stats['no_images'] += 1
                    print(f"⚠️  Código {result.get('property_id', 'N/A')}: Sin imágenes")
                else:
                    stats['failed'] += 1
                    stats['failed_urls'].append(url)
                    print(f"❌ No se pudo procesar")

            except Exception as e:
                stats['failed'] += 1
                stats['failed_urls'].append(url)
                print(f"❌ Error: {e}")

            # Pausa entre propiedades
            if idx < len(property_links):
                time.sleep(delay)

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
                print(f"   {i:2d}. {url}")
            if len(stats['failed_urls']) > 10:
                print(f"   ... y {len(stats['failed_urls']) - 10} más")

        print("="*80)

        return stats

    def run_full_process(self, search_type='venta', max_pages=None, max_properties=None,
                         start_from=0, page_delay=2, download_delay=1):
        """
        Proceso completo: navega páginas y descarga imágenes
        """
        print("\n" + "="*80)
        print("🚀 PROCESO COMPLETO DE DESCARGA")
        print("="*80)
        print(f"\n⚙️  Configuración:")
        print(f"   Tipo de búsqueda: {search_type}")
        print(f"   Máx. páginas: {max_pages or 'Todas'}")
        print(f"   Máx. propiedades: {max_properties or 'Todas'}")
        print(f"   Iniciar desde: {start_from}")
        print(f"   Delay entre páginas: {page_delay}s")
        print(f"   Delay entre descargas: {download_delay}s")

        # Fase 1: Extraer enlaces
        property_links = self.scrape_all_pages(
            search_type=search_type,
            max_pages=max_pages,
            delay=page_delay
        )

        if not property_links:
            print("\n❌ No se encontraron propiedades")
            return None

        # Guardar enlaces en archivo
        links_file = os.path.join(self.output_dir, f"property_links_{search_type}.txt")
        os.makedirs(self.output_dir, exist_ok=True)
        with open(links_file, 'w', encoding='utf-8') as f:
            for link in property_links:
                f.write(f"{link}\n")
        print(f"\n💾 Enlaces guardados en: {links_file}")

        # Fase 2: Descargar imágenes
        stats = self.download_from_links(
            property_links=property_links,
            max_properties=max_properties,
            start_from=start_from,
            delay=download_delay
        )

        print("\n" + "="*80)
        print("✅ PROCESO COMPLETADO")
        print("="*80)

        return {
            'property_links': property_links,
            'stats': stats
        }


def main():
    """Función principal"""

    print("="*80)
    print("DESCARGADOR PAGINADO - BOHIO CONSULTORES")
    print("="*80)

    # Configuración
    search_type = 'venta'  # 'venta', 'arriendo', 'todas'
    max_pages = None  # None = todas las páginas
    max_properties = None  # None = todas las propiedades
    start_from = 0  # Índice de inicio

    # Parsear argumentos
    if len(sys.argv) > 1:
        try:
            # Argumento 1: tipo de búsqueda
            if sys.argv[1] in ['venta', 'arriendo', 'todas']:
                search_type = sys.argv[1]
            else:
                max_pages = int(sys.argv[1])
        except:
            print("💡 USO:")
            print("   python batch_download_paginated.py [tipo] [max_paginas] [max_propiedades]")
            print("\n💡 EJEMPLOS:")
            print("   python batch_download_paginated.py venta 5 20")
            print("   python batch_download_paginated.py arriendo 10")
            print("   python batch_download_paginated.py todas")
            print("\n📝 Tipos: venta, arriendo, todas")
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

    # Crear scraper
    scraper = PaginatedPropertyScraper()

    # Ejecutar proceso completo
    scraper.run_full_process(
        search_type=search_type,
        max_pages=max_pages,
        max_properties=max_properties,
        start_from=start_from,
        page_delay=2,  # Segundos entre páginas
        download_delay=1  # Segundos entre descargas
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para descargar imágenes en batch desde lista de códigos de propiedades
Lee códigos desde listado.txt y construye URLs automáticamente
"""
import os
import sys
import io
import time
import requests
from bs4 import BeautifulSoup

# Importar la clase de descarga
sys.path.insert(0, os.path.dirname(__file__))
from download_property_images import PropertyImageDownloader


class BatchPropertyDownloader:
    """Descarga imágenes de múltiples propiedades desde lista de códigos"""

    def __init__(self, codes_file="property_images/listado.txt", output_dir="property_images"):
        self.codes_file = codes_file
        self.output_dir = output_dir
        self.downloader = PropertyImageDownloader(download_dir=output_dir)
        self.base_search_url = "https://bohioconsultores.com/resultados-de-busqueda/?Servicio=2"

    def read_property_codes(self):
        """Lee códigos de propiedades desde listado.txt"""
        if not os.path.exists(self.codes_file):
            print(f"❌ Archivo no encontrado: {self.codes_file}")
            return []

        codes = []
        with open(self.codes_file, 'r', encoding='utf-8') as f:
            for line in f:
                code = line.strip()
                # Saltar primera línea si es encabezado
                if code and code != 'default_code' and not code.startswith('BOH-'):
                    # Extraer solo números
                    if code.isdigit():
                        codes.append(code)
                    elif code.startswith('BOH-'):
                        # Extraer número después de BOH-
                        parts = code.split('-')
                        if len(parts) > 1 and parts[1].isdigit():
                            codes.append(parts[1])

        return codes

    def construct_property_url(self, code):
        """
        Construye URL de propiedad desde código
        Formato: https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-[CODE]
        """
        # Intentar diferentes patrones comunes
        patterns = [
            f"https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Venta-{code}",
            f"https://bohioconsultores.com/detalle-propiedad/?Casa-en-Venta-{code}",
            f"https://bohioconsultores.com/detalle-propiedad/?Lote-en-Venta-{code}",
            f"https://bohioconsultores.com/detalle-propiedad/?Apartamento-en-Arriendo-{code}",
            f"https://bohioconsultores.com/detalle-propiedad/?Casa-en-Arriendo-{code}",
        ]
        return patterns  # Retornar todos los patrones para probar

    def fetch_search_page(self, page_number=1):
        """
        Obtiene página de búsqueda para extraer URLs reales
        Soporta navegación por múltiples páginas
        """
        try:
            # Construir URL con paginación si es necesario
            url = self.base_search_url
            if page_number > 1:
                # Intentar diferentes formatos de paginación
                separator = '&' if '?' in url else '?'
                url = f"{url}{separator}page={page_number}"

            print(f"\n📥 Obteniendo página de búsqueda (página {page_number})...")
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            print(f"❌ Error obteniendo página de búsqueda: {e}")
            return None

    def extract_property_urls_from_search(self, html):
        """Extrae todas las URLs de propiedades desde página de búsqueda"""
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        urls = []

        # Buscar todos los enlaces que apuntan a detalle-propiedad
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'detalle-propiedad' in href:
                # Asegurar que sea URL completa
                if not href.startswith('http'):
                    href = f"https://bohioconsultores.com{href}"
                if href not in urls:
                    urls.append(href)

        return urls

    def scrape_all_pages(self, max_pages=10):
        """
        Navega múltiples páginas de resultados para obtener todas las propiedades
        """
        print("\n" + "="*80)
        print("🔍 NAVEGANDO PÁGINAS DE RESULTADOS DE BÚSQUEDA")
        print("="*80)

        all_urls = []
        page_number = 1

        while page_number <= max_pages:
            print(f"\n📄 Procesando página {page_number}/{max_pages}...")

            # Obtener HTML de la página
            html = self.fetch_search_page(page_number)
            if not html:
                print(f"⚠️  No se pudo obtener página {page_number}, deteniendo...")
                break

            # Extraer URLs de propiedades
            urls = self.extract_property_urls_from_search(html)

            if not urls:
                print(f"⚠️  No se encontraron propiedades en página {page_number}")
                if page_number == 1:
                    # Si no hay resultados en la primera página, algo está mal
                    print("❌ Error: No se encontraron resultados en la primera página")
                    break
                else:
                    # Si no hay más resultados, hemos llegado al final
                    print("✅ Fin de resultados alcanzado")
                    break

            # Filtrar URLs nuevas
            new_urls = [url for url in urls if url not in all_urls]
            all_urls.extend(new_urls)

            print(f"✅ Encontradas {len(urls)} propiedades ({len(new_urls)} nuevas)")
            print(f"📊 Total acumulado: {len(all_urls)} propiedades")

            # Si no hay URLs nuevas, probablemente llegamos al final
            if not new_urls:
                print("✅ No hay más propiedades nuevas, finalizando...")
                break

            page_number += 1

            # Pausa entre páginas para no sobrecargar el servidor
            if page_number <= max_pages:
                time.sleep(2)

        print(f"\n{'='*80}")
        print(f"📊 RESUMEN DE NAVEGACIÓN")
        print(f"{'='*80}")
        print(f"   Páginas procesadas: {page_number - 1}")
        print(f"   Total URLs encontradas: {len(all_urls)}")
        print("="*80)

        return all_urls

    def process_all_properties(self, max_properties=None, start_from=0, max_pages=10):
        """
        Procesa todas las propiedades
        max_properties: límite de propiedades a procesar (None = todas)
        start_from: índice desde donde empezar
        max_pages: número máximo de páginas de búsqueda a navegar
        """
        print("\n" + "="*80)
        print("BATCH DOWNLOADER - DESCARGA MASIVA DE IMÁGENES")
        print("="*80)

        # Opción 1: Leer códigos desde listado.txt
        codes = self.read_property_codes()
        print(f"\n📋 Códigos encontrados en {self.codes_file}: {len(codes)}")

        urls = []
        if not codes:
            print("⚠️  No se encontraron códigos válidos en listado.txt")
            print("💡 Intentando extraer desde páginas de búsqueda...")

            # Opción 2: Extraer URLs navegando múltiples páginas
            urls = self.scrape_all_pages(max_pages=max_pages)

            if urls:
                print(f"\n✅ Total URLs encontradas: {len(urls)}")
            else:
                print("❌ No se pudieron obtener URLs de propiedades")
                return

        # Si tenemos URLs directas, usarlas
        # Si tenemos códigos, intentar construir URLs
        if urls:
            # Ya tenemos URLs completas
            property_list = urls
        elif codes:
            # Tenemos códigos, intentar construir URLs
            property_list = codes
        else:
            print("❌ No se encontraron propiedades para procesar")
            return

        # Aplicar límites
        if start_from > 0:
            property_list = property_list[start_from:]
            print(f"🔄 Iniciando desde posición: {start_from}")

        if max_properties:
            property_list = property_list[:max_properties]
            print(f"🔢 Limitando a: {max_properties} propiedades")

        print(f"\n🚀 Procesando {len(property_list)} propiedades...")
        print("="*80)

        # Estadísticas
        stats = {
            'total': len(property_list),
            'success': 0,
            'failed': 0,
            'no_images': 0,
            'total_images': 0,
            'failed_items': []
        }

        # Procesar cada propiedad
        for idx, item in enumerate(property_list, 1):
            print(f"\n[{idx}/{len(property_list)}] Procesando propiedad")
            print("-" * 80)

            success = False

            # Determinar si es URL o código
            if isinstance(item, str) and item.startswith('http'):
                # Es una URL completa
                url = item
                print(f"🔗 URL: {url}")

                try:
                    # Descargar imágenes
                    result = self.downloader.process_property_url(url, download_locally=True)

                    if result and result.get('downloaded_images'):
                        stats['success'] += 1
                        stats['total_images'] += len(result['downloaded_images'])
                        print(f"✅ {len(result['downloaded_images'])} imágenes descargadas")
                        success = True
                    elif result:
                        stats['no_images'] += 1
                        print(f"⚠️  Sin imágenes")
                        success = True

                except Exception as e:
                    print(f"❌ Error: {e}")

                if not success:
                    stats['failed'] += 1
                    stats['failed_items'].append(url)

            else:
                # Es un código, intentar construir URL
                code = item
                print(f"🔢 Código: {code}")

                # Intentar con diferentes patrones de URL
                patterns = self.construct_property_url(code)

                for url_pattern in patterns:
                    try:
                        # Verificar si URL existe
                        test_response = requests.head(url_pattern, timeout=5, allow_redirects=True)

                        if test_response.status_code == 200:
                            print(f"✅ URL encontrada: {url_pattern}")

                            # Descargar imágenes
                            result = self.downloader.process_property_url(url_pattern, download_locally=True)

                            if result and result.get('downloaded_images'):
                                stats['success'] += 1
                                stats['total_images'] += len(result['downloaded_images'])
                                print(f"✅ {len(result['downloaded_images'])} imágenes descargadas")
                                success = True
                                break
                            elif result:
                                stats['no_images'] += 1
                                print(f"⚠️  Sin imágenes")
                                success = True
                                break

                    except requests.exceptions.RequestException:
                        # URL no válida, probar siguiente patrón
                        continue

                if not success:
                    stats['failed'] += 1
                    stats['failed_items'].append(code)
                    print(f"❌ No se pudo procesar código: {code}")

            # Pequeña pausa para no sobrecargar el servidor
            if idx < len(property_list):
                time.sleep(1)

        # Reporte final
        print("\n" + "="*80)
        print("📊 REPORTE FINAL DE DESCARGA BATCH")
        print("="*80)
        print(f"   Total Procesadas: {stats['total']}")
        print(f"   ✅ Exitosas: {stats['success']}")
        print(f"   ❌ Fallidas: {stats['failed']}")
        print(f"   ⚠️  Sin imágenes: {stats['no_images']}")
        print(f"   📸 Total Imágenes Descargadas: {stats['total_images']}")

        if stats['failed_items']:
            print(f"\n📋 Items Fallidos ({len(stats['failed_items'])}):")
            for i, item in enumerate(stats['failed_items'][:20], 1):
                print(f"   {i:2d}. {item}")
            if len(stats['failed_items']) > 20:
                print(f"   ... y {len(stats['failed_items']) - 20} más")

        print("="*80)
        print("✅ PROCESO COMPLETADO")
        print("="*80)

        return stats


def main():
    """Función principal"""

    print("="*80)
    print("BATCH DOWNLOADER - DESCARGA MASIVA DE IMÁGENES DE PROPIEDADES")
    print("="*80)

    # Parámetros configurables
    codes_file = "property_images/listado.txt"
    max_properties = None  # None = todas, o especificar número
    start_from = 0  # Índice desde donde empezar
    max_pages = 10  # Número máximo de páginas de búsqueda a navegar

    # Permitir parámetros por línea de comandos
    if len(sys.argv) > 1:
        try:
            max_properties = int(sys.argv[1])
            print(f"📝 Límite establecido: {max_properties} propiedades")
        except:
            print("💡 USO: python batch_download_from_list.py [max_propiedades] [start_from] [max_pages]")
            print("💡 EJEMPLOS:")
            print("   python batch_download_from_list.py 10")
            print("   python batch_download_from_list.py 20 0 5")
            print("   python batch_download_from_list.py")
            print()

    if len(sys.argv) > 2:
        try:
            start_from = int(sys.argv[2])
            print(f"🔄 Iniciando desde posición: {start_from}")
        except:
            pass

    if len(sys.argv) > 3:
        try:
            max_pages = int(sys.argv[3])
            print(f"📄 Máximo de páginas: {max_pages}")
        except:
            pass

    # Crear descargador
    downloader = BatchPropertyDownloader(codes_file=codes_file)

    # Procesar propiedades
    downloader.process_all_properties(
        max_properties=max_properties,
        start_from=start_from,
        max_pages=max_pages
    )


if __name__ == "__main__":
    main()

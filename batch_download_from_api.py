#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para descargar imágenes usando la API de Arrendasoft
Método MÁS EFICIENTE: obtiene todas las propiedades directamente desde la API
"""
import os
import sys
import time
import requests
from download_property_images import PropertyImageDownloader


class ArrendasoftAPIDownloader:
    """Descarga imágenes usando la API de Arrendasoft"""

    def __init__(self, output_dir="property_images"):
        self.output_dir = output_dir
        self.downloader = PropertyImageDownloader(download_dir=output_dir)
        self.api_url = "https://bohio.arrendasoft.co/service/v2/public/map-of-properties/data"

    def get_all_properties(self, servicio=None):
        """
        Obtiene todas las propiedades desde la API de Arrendasoft
        servicio: None=Todas, 1=Arriendo, 2=Venta
        """
        print("\n" + "="*80)
        print("OBTENIENDO PROPIEDADES DESDE API DE ARRENDASOFT")
        print("="*80)

        params = {}
        if servicio:
            params['Servicio'] = servicio

        servicio_text = {None: "TODAS", 1: "ARRIENDO", 2: "VENTA"}.get(servicio, "DESCONOCIDO")
        print(f"\nTipo: {servicio_text}")
        print(f"API URL: {self.api_url}")

        try:
            response = requests.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if 'campos' in data:
                propiedades = data['campos']
                print(f"\nRespuesta exitosa!")
                print(f"Total propiedades encontradas: {len(propiedades)}")
                return propiedades
            else:
                print(f"\nError: Formato de respuesta inesperado")
                print(f"Keys disponibles: {list(data.keys())}")
                return []

        except requests.exceptions.RequestException as e:
            print(f"\nError en la llamada a la API: {e}")
            return []
        except Exception as e:
            print(f"\nError inesperado: {e}")
            return []

    def construct_property_url(self, property_data):
        """
        Construye URL de propiedad desde datos de la API
        Formato: https://bohioconsultores.com/detalle-propiedad/?{Tipo}-en-{Servicio}-{Codigo}
        """
        codigo = property_data.get('Codigo')
        tipo = property_data.get('Tipo', 'Propiedad')
        servicio = property_data.get('Servicio', 'Venta')

        # Reemplazar espacios por guiones en el tipo
        tipo_formatted = tipo.replace(' ', '-')

        # Construir URL
        url = f"https://bohioconsultores.com/detalle-propiedad/?{tipo_formatted}-en-{servicio}-{codigo}"

        return url

    def download_from_api(self, servicio=None, max_properties=None, start_from=0):
        """
        Proceso completo: obtiene propiedades de API y descarga imágenes
        """
        print("\n" + "="*80)
        print("DESCARGA DESDE API - BOHIO CONSULTORES")
        print("="*80)

        # Obtener propiedades desde API
        propiedades = self.get_all_properties(servicio=servicio)

        if not propiedades:
            print("\nNo se encontraron propiedades")
            return None

        # Aplicar límites
        if start_from > 0:
            propiedades = propiedades[start_from:]
            print(f"\nIniciando desde posición: {start_from}")

        if max_properties:
            propiedades = propiedades[:max_properties]
            print(f"Limitando a: {max_properties} propiedades")

        print(f"\nProcesando {len(propiedades)} propiedades...")
        print("="*80)

        # Estadísticas
        stats = {
            'total': len(propiedades),
            'success': 0,
            'failed': 0,
            'no_images': 0,
            'total_images': 0,
            'failed_properties': []
        }

        # Procesar cada propiedad
        for idx, prop in enumerate(propiedades, 1):
            codigo = prop.get('Codigo')
            titulo = prop.get('Titulo', '')
            tipo = prop.get('Tipo', '')

            print(f"\n{'='*80}")
            print(f"[{idx}/{len(propiedades)}] Propiedad {codigo}")
            print(f"{'='*80}")
            print(f"Titulo: {titulo}")
            print(f"Tipo: {tipo}")

            # Construir URL
            url = self.construct_property_url(prop)
            print(f"URL: {url}")

            try:
                # Descargar imágenes
                result = self.downloader.process_property_url(url, download_locally=True)

                if result and result.get('downloaded_images'):
                    stats['success'] += 1
                    stats['total_images'] += len(result['downloaded_images'])
                    print(f"OK: {len(result['downloaded_images'])} imagenes descargadas")
                elif result:
                    stats['no_images'] += 1
                    print(f"AVISO: Sin imagenes")
                else:
                    stats['failed'] += 1
                    stats['failed_properties'].append({'codigo': codigo, 'titulo': titulo})
                    print(f"ERROR: No se pudo procesar")

            except Exception as e:
                stats['failed'] += 1
                stats['failed_properties'].append({'codigo': codigo, 'titulo': titulo, 'error': str(e)})
                print(f"ERROR: {e}")

            # Pausa entre propiedades
            if idx < len(propiedades):
                time.sleep(1)

        # Reporte final
        print("\n" + "="*80)
        print("REPORTE FINAL")
        print("="*80)
        print(f"   Total Procesadas: {stats['total']}")
        print(f"   Exitosas: {stats['success']}")
        print(f"   Fallidas: {stats['failed']}")
        print(f"   Sin imagenes: {stats['no_images']}")
        print(f"   Total Imagenes Descargadas: {stats['total_images']}")

        if stats['failed_properties']:
            print(f"\nPropiedades Fallidas ({len(stats['failed_properties'])}):")
            for i, prop in enumerate(stats['failed_properties'][:10], 1):
                print(f"   {i}. Codigo {prop['codigo']}: {prop['titulo']}")
            if len(stats['failed_properties']) > 10:
                print(f"   ... y {len(stats['failed_properties']) - 10} mas")

        print("="*80)
        print("PROCESO COMPLETADO")
        print("="*80)

        return stats


def main():
    """Función principal"""

    print("="*80)
    print("DESCARGADOR DE IMAGENES - API ARRENDASOFT")
    print("="*80)

    # Parámetros configurables
    servicio = None  # None=Todas, 1=Arriendo, 2=Venta
    max_properties = None  # None = todas
    start_from = 0  # Índice de inicio

    # Parsear argumentos
    if len(sys.argv) > 1:
        try:
            # Argumento 1: tipo de servicio o cantidad
            arg1 = sys.argv[1].lower()
            if arg1 == 'venta':
                servicio = 2
            elif arg1 == 'arriendo':
                servicio = 1
            elif arg1 == 'todas':
                servicio = None
            else:
                max_properties = int(sys.argv[1])
        except:
            print("\nUSO:")
            print("   python batch_download_from_api.py [tipo] [max_propiedades] [start_from]")
            print("\nEJEMPLOS:")
            print("   python batch_download_from_api.py venta")
            print("   python batch_download_from_api.py venta 20")
            print("   python batch_download_from_api.py arriendo 10 0")
            print("   python batch_download_from_api.py todas")
            print("   python batch_download_from_api.py 50")
            print("\nTipos: venta, arriendo, todas")
            return

    if len(sys.argv) > 2:
        try:
            max_properties = int(sys.argv[2])
        except:
            pass

    if len(sys.argv) > 3:
        try:
            start_from = int(sys.argv[3])
        except:
            pass

    # Crear descargador
    downloader = ArrendasoftAPIDownloader()

    # Procesar propiedades
    downloader.download_from_api(
        servicio=servicio,
        max_properties=max_properties,
        start_from=start_from
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test detallado de la API y construcción de URLs
"""
import requests
import json

print("="*80)
print("TEST DETALLADO API + CONSTRUCCION DE URLs")
print("="*80)

# Obtener propiedades
api_url = "https://bohio.arrendasoft.co/service/v2/public/map-of-properties/data"
response = requests.get(api_url, params={'Servicio': 2}, timeout=15)

if response.status_code == 200:
    data = response.json()

    if 'campos' in data:
        propiedades = data['campos']
        print(f"\nTotal propiedades encontradas: {len(propiedades)}")

        # Mostrar primeras 10 propiedades y construir URLs
        print("\nPrimeras 10 propiedades con URLs construidas:")
        print("="*80)

        for i, prop in enumerate(propiedades[:10], 1):
            codigo = prop.get('Codigo')
            titulo = prop.get('Titulo', '')
            tipo = prop.get('Tipo', '')
            servicio = prop.get('Servicio', '')

            # Construir diferentes formatos de URL para probar
            urls_posibles = [
                f"https://bohioconsultores.com/detalle-propiedad/?{tipo}-en-{servicio}-{codigo}",
                f"https://bohioconsultores.com/detalle-propiedad/{codigo}",
                f"https://bohioconsultores.com/detalle-propiedad/{tipo}-{codigo}",
                f"https://bohioconsultores.com/propiedad/{codigo}",
            ]

            print(f"\n{i}. Código: {codigo}")
            print(f"   Título: {titulo}")
            print(f"   Tipo: {tipo}")
            print(f"   Servicio: {servicio}")
            print(f"   URLs posibles:")
            for url in urls_posibles:
                print(f"      - {url}")

        # Guardar muestra completa
        print(f"\nGuardando muestra en api_sample.json...")
        with open('api_sample.json', 'w', encoding='utf-8') as f:
            json.dump(propiedades[:10], f, indent=2, ensure_ascii=False)

        # Probar primera URL
        if len(propiedades) > 0:
            prop = propiedades[0]
            codigo = prop.get('Codigo')
            tipo = prop.get('Tipo', '')
            servicio = prop.get('Servicio', '')

            test_url = f"https://bohioconsultores.com/detalle-propiedad/?{tipo}-en-{servicio}-{codigo}"

            print(f"\n{'='*80}")
            print(f"PROBANDO PRIMERA URL:")
            print(f"{'='*80}")
            print(f"URL: {test_url}")

            try:
                test_response = requests.head(test_url, timeout=10, allow_redirects=True)
                print(f"Status Code: {test_response.status_code}")
                print(f"URL Final: {test_response.url}")

                if test_response.status_code == 200:
                    print("URL VALIDA!")
                else:
                    print("URL no válida, probando formato alternativo...")

                    # Probar sin query string
                    alt_url = f"https://bohioconsultores.com/detalle-propiedad/{codigo}"
                    alt_response = requests.head(alt_url, timeout=10, allow_redirects=True)
                    print(f"\nURL Alternativa: {alt_url}")
                    print(f"Status Code: {alt_response.status_code}")

            except Exception as e:
                print(f"Error: {e}")

print("\n" + "="*80)
print("FIN")
print("="*80)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para la API de Arrendasoft
"""
import requests
import json

print("="*80)
print("TEST API ARRENDASOFT")
print("="*80)

# Endpoint de la API
api_url = "https://bohio.arrendasoft.co/service/v2/public/map-of-properties/data"

# Probar con diferentes parámetros
tests = [
    {'Servicio': 2, 'descripcion': 'Propiedades en VENTA'},
    {'Servicio': 1, 'descripcion': 'Propiedades en ARRIENDO'},
    {}, # Sin parámetros
]

for test in tests:
    params = {k: v for k, v in test.items() if k != 'descripcion'}
    descripcion = test.get('descripcion', 'Sin filtro')

    print(f"\n{'='*80}")
    print(f"Probando: {descripcion}")
    print(f"Parámetros: {params}")
    print(f"{'='*80}")

    try:
        response = requests.get(api_url, params=params, timeout=15)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Tipo de respuesta: {type(data)}")

                if isinstance(data, list):
                    print(f"Total propiedades: {len(data)}")

                    if len(data) > 0:
                        print("\nEstructura de la primera propiedad:")
                        first_prop = data[0]
                        for key, value in first_prop.items():
                            value_str = str(value)[:50]
                            print(f"  {key}: {value_str}")

                        # Guardar primeras 5 propiedades como ejemplo
                        print(f"\nGuardando primeras 5 propiedades en: sample_properties_{test.get('Servicio', 'all')}.json")
                        with open(f"sample_properties_{test.get('Servicio', 'all')}.json", 'w', encoding='utf-8') as f:
                            json.dump(data[:5], f, indent=2, ensure_ascii=False)

                elif isinstance(data, dict):
                    print(f"Respuesta es dict con keys: {list(data.keys())}")
                    if 'data' in data:
                        print(f"  data contiene: {len(data['data'])} items")
                    print("\nContenido completo:")
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:500])

            except json.JSONDecodeError as e:
                print(f"Error decodificando JSON: {e}")
                print(f"Contenido (primeros 500 chars): {response.text[:500]}")
        else:
            print(f"Error HTTP: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")

    except Exception as e:
        print(f"Error: {e}")

print("\n" + "="*80)
print("FIN DE PRUEBAS")
print("="*80)

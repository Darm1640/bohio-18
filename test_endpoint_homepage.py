#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Endpoint Homepage
Simula las llamadas que hace homepage_properties.js
"""

import json
import requests

# Configuración
BASE_URL = 'https://darm1640-bohio-18.odoo.com'
DB = 'darm1640-bohio-18-main-24081960'

def test_endpoint(filtros, nombre):
    """Probar endpoint /property/search/ajax"""
    url = f'{BASE_URL}/property/search/ajax'

    payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "context": "public",
            "filters": filtros,
            "page": 1,
            "ppg": 20,
            "order": "newest"
        },
        "id": None
    }

    print(f"\n{'='*70}")
    print(f"TEST: {nombre}")
    print(f"{'='*70}")
    print(f"URL: {url}")
    print(f"Filtros: {json.dumps(filtros, indent=2)}")

    try:
        response = requests.post(
            url,
            json=payload,
            headers={
                'Content-Type': 'application/json',
            },
            timeout=30
        )

        print(f"\nStatus Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if 'result' in data:
                result = data['result']
                print(f"[OK] Respuesta exitosa")
                print(f"     Total propiedades: {result.get('total', 0)}")
                print(f"     Propiedades en resultado: {len(result.get('properties', []))}")

                if result.get('properties'):
                    print(f"\n     Muestra de propiedades:")
                    for i, prop in enumerate(result['properties'][:3], 1):
                        print(f"       {i}. ID:{prop.get('id')} - {prop.get('name', '')[:40]}...")
                        print(f"          Precio: {prop.get('price', 'N/A')}")
                        print(f"          Ciudad: {prop.get('city', 'N/A')}")
                else:
                    print(f"\n     [AVISO] No se retornaron propiedades")
            elif 'error' in data:
                print(f"[ERROR] Error del servidor:")
                print(f"        {data['error'].get('message', 'Error desconocido')}")
                if 'data' in data['error']:
                    print(f"        {data['error']['data']}")
            else:
                print(f"[ERROR] Respuesta inesperada:")
                print(f"        {json.dumps(data, indent=2)[:500]}")

        else:
            print(f"[ERROR] Codigo HTTP: {response.status_code}")
            print(f"        Respuesta: {response.text[:500]}")

    except requests.exceptions.Timeout:
        print(f"[ERROR] Timeout - El servidor no respondio")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error de red: {e}")
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")

def main():
    """Función principal"""
    print("="*70)
    print("TEST DE ENDPOINT /property/search/ajax")
    print("="*70)

    # Test 1: ARRIENDO
    test_endpoint(
        {
            'type_service': 'rent',
            'limit': 10,
            'order': 'newest'
        },
        "ARRIENDO"
    )

    # Test 2: VENTA USADA (sin proyecto)
    test_endpoint(
        {
            'type_service': 'sale',
            'has_project': False,
            'limit': 10,
            'order': 'newest'
        },
        "VENTA USADA (sin proyecto)"
    )

    # Test 3: PROYECTOS (con proyecto)
    test_endpoint(
        {
            'type_service': 'sale',
            'has_project': True,
            'limit': 10,
            'order': 'newest'
        },
        "PROYECTOS (con proyecto)"
    )

    # Test 4: ARRIENDO con ubicación (para mapa)
    test_endpoint(
        {
            'type_service': 'rent',
            'has_location': True,
            'limit': 20,
            'order': 'newest'
        },
        "ARRIENDO con GPS (para mapa)"
    )

    print("\n" + "="*70)
    print("TESTS COMPLETADOS")
    print("="*70)

if __name__ == '__main__':
    main()

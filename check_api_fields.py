#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para ver QUE CAMPOS REALES tiene la API de Arrendasoft
"""
import requests
import json

api_url = "https://bohio.arrendasoft.co/service/v2/public/map-of-properties/data"

print("Consultando API...")
response = requests.get(api_url, timeout=30)
data = response.json()

if 'campos' in data:
    propiedades = data['campos']
    print(f"\nTotal propiedades: {len(propiedades)}")

    if propiedades:
        # Tomar primera propiedad como muestra
        primera = propiedades[0]

        print(f"\nCampos disponibles en la API ({len(primera)} campos):")
        print("="*80)

        for key, value in sorted(primera.items()):
            tipo_valor = type(value).__name__
            valor_muestra = str(value)[:50] if value else "(vacío)"
            print(f"   {key:20s} ({tipo_valor:10s}): {valor_muestra}")

        # Guardar ejemplo completo
        with open('api_property_example.json', 'w', encoding='utf-8') as f:
            json.dump(primera, f, indent=2, ensure_ascii=False)

        print(f"\nEjemplo completo guardado en: api_property_example.json")

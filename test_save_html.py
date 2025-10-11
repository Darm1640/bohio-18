#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Guardar HTML de la página para inspección
"""
import requests

url = "https://bohioconsultores.com/resultados-de-busqueda/?Servicio=2"

print(f"Obteniendo: {url}")
response = requests.get(url, timeout=15, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})
response.encoding = 'utf-8'

# Guardar HTML
with open('search_page.html', 'w', encoding='utf-8') as f:
    f.write(response.text)

print("HTML guardado en: search_page.html")
print(f"Tamaño: {len(response.text)} caracteres")

# Buscar palabras clave en el HTML
keywords = ['propiedad', 'detalle', 'listing', 'property', 'apartamento', 'casa']
for keyword in keywords:
    count = response.text.lower().count(keyword)
    print(f"  '{keyword}': {count} veces")

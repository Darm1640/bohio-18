#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para ver qué hay en la página de búsqueda
"""
import requests
from bs4 import BeautifulSoup

url = "https://bohioconsultores.com/resultados-de-busqueda/?Servicio=2"

print(f"Obteniendo: {url}")
response = requests.get(url, timeout=15)
response.encoding = 'utf-8'

print(f"Status: {response.status_code}")
print(f"Tamaño HTML: {len(response.text)} caracteres")

soup = BeautifulSoup(response.text, 'html.parser')

# Buscar todos los enlaces
all_links = soup.find_all('a', href=True)
print(f"\nTotal de enlaces encontrados: {len(all_links)}")

# Buscar enlaces que contengan "detalle"
detalle_links = [link for link in all_links if 'detalle' in link['href'].lower()]
print(f"Enlaces con 'detalle': {len(detalle_links)}")

if detalle_links:
    print("\nPrimeros 5 enlaces con 'detalle':")
    for i, link in enumerate(detalle_links[:5], 1):
        print(f"  {i}. {link['href']}")

# Buscar enlaces que contengan "propiedad"
propiedad_links = [link for link in all_links if 'propiedad' in link['href'].lower()]
print(f"\nEnlaces con 'propiedad': {len(propiedad_links)}")

if propiedad_links:
    print("\nPrimeros 5 enlaces con 'propiedad':")
    for i, link in enumerate(propiedad_links[:5], 1):
        print(f"  {i}. {link['href']}")

# Ver primeros 10 enlaces en general
print("\nPrimeros 10 enlaces en general:")
for i, link in enumerate(all_links[:10], 1):
    href = link['href']
    text = link.get_text(strip=True)[:50]
    print(f"  {i}. {href[:80]} - '{text}'")

# Buscar divs o clases que puedan contener propiedades
print("\n\n=== Buscando contenedores de propiedades ===")
containers = soup.find_all(['div', 'article', 'section'], class_=True)
print(f"Total de contenedores con clase: {len(containers)}")

# Mostrar algunas clases interesantes
interesting_classes = []
for container in containers:
    classes = ' '.join(container.get('class', []))
    if any(word in classes.lower() for word in ['property', 'propiedad', 'card', 'item', 'listing', 'resultado']):
        if classes not in interesting_classes:
            interesting_classes.append(classes)

print(f"\nClases interesantes encontradas: {len(interesting_classes)}")
for i, cls in enumerate(interesting_classes[:10], 1):
    print(f"  {i}. {cls}")

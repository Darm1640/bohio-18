#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrae enlaces de propiedades desde HTML guardado
"""
import re
import sys
from urllib.parse import unquote

def extract_property_links(html_file):
    """Extrae enlaces de propiedades desde HTML guardado"""

    print("="*80)
    print("EXTRACTOR DE ENLACES - HTML GUARDADO")
    print("="*80)

    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()

    print(f"\nArchivo: {html_file}")
    print(f"Tamaño: {len(html)} caracteres")

    # Buscar enlaces con detalle-propiedad
    pattern = r'href="(https://bohioconsultores\.com/detalle-propiedad/[^"]*)"'
    matches = re.findall(pattern, html)

    # Eliminar duplicados manteniendo orden
    seen = set()
    unique_links = []
    for url in matches:
        # Decodificar URL para comparar
        decoded = unquote(url)
        if decoded not in seen:
            seen.add(decoded)
            unique_links.append(url)

    print(f"\nEnlaces encontrados: {len(unique_links)}")
    print("="*80)

    # Mostrar enlaces
    for i, url in enumerate(unique_links, 1):
        # Extraer código de propiedad
        code_match = re.search(r'-(\d+)$', url)
        code = code_match.group(1) if code_match else "?"

        # Decodificar para mostrar
        url_decoded = unquote(url)

        print(f"{i:2d}. Código {code}: {url_decoded}")

    # Guardar en archivo
    output_file = "extracted_property_links.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        for url in unique_links:
            # Usar URL decodificada
            f.write(f"{unquote(url)}\n")

    print(f"\n{'-'*80}")
    print(f"Enlaces guardados en: {output_file}")
    print("="*80)

    # Estadísticas por tipo
    tipos = {}
    for url in unique_links:
        url_decoded = unquote(url)
        # Extraer tipo (Apartamento, Casa, etc.)
        tipo_match = re.search(r'\?(.*?)-en-', url_decoded)
        if tipo_match:
            tipo = tipo_match.group(1)
            tipos[tipo] = tipos.get(tipo, 0) + 1

    if tipos:
        print("\nEstadísticas por tipo:")
        for tipo, count in sorted(tipos.items()):
            print(f"  {tipo}: {count}")

    return unique_links


if __name__ == "__main__":
    if len(sys.argv) > 1:
        html_file = sys.argv[1]
    else:
        # Usar archivo por defecto
        html_file = r"C:\Users\darm1\Downloads\Para Lorena X\Resultados de la busqueda - Bohio Consultores.html"

    extract_property_links(html_file)

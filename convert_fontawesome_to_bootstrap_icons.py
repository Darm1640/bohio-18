# -*- coding: utf-8 -*-
"""
Script para convertir todos los iconos de Font Awesome a Bootstrap Icons
en todos los módulos BOHIO
"""

import os
import re
from pathlib import Path

# Mapeo de Font Awesome a Bootstrap Icons
ICON_MAPPING = {
    # Propiedades e Inmobiliaria
    'fa-home': 'bi-house-fill',
    'fa-building': 'bi-building',
    'fa-building-o': 'bi-building',
    'fa-bed': 'bi-bed',
    'fa-bath': 'bi-droplet',
    'fa-shower': 'bi-droplet',
    'fa-car': 'bi-car-front',
    'fa-parking': 'bi-car-front',
    'fa-tree': 'bi-flower2',
    'fa-swimming-pool': 'bi-water',
    'fa-ruler': 'bi-rulers',
    'fa-ruler-combined': 'bi-rulers',
    'fa-expand': 'bi-arrows-angle-expand',
    'fa-arrows-alt': 'bi-arrows-fullscreen',

    # Ubicación
    'fa-map-marker': 'bi-geo-alt-fill',
    'fa-map-marker-alt': 'bi-geo-alt-fill',
    'fa-location-arrow': 'bi-geo-alt-fill',
    'fa-map': 'bi-map-fill',
    'fa-map-o': 'bi-map',
    'fa-compass': 'bi-compass',
    'fa-globe': 'bi-globe',

    # Acciones
    'fa-search': 'bi-search',
    'fa-filter': 'bi-funnel',
    'fa-heart': 'bi-heart',
    'fa-heart-o': 'bi-heart',
    'fa-heart-fill': 'bi-heart-fill',
    'fa-share': 'bi-share',
    'fa-share-alt': 'bi-share-fill',
    'fa-share-nodes': 'bi-share-fill',
    'fa-download': 'bi-download',
    'fa-upload': 'bi-upload',
    'fa-print': 'bi-printer',
    'fa-printer': 'bi-printer-fill',
    'fa-edit': 'bi-pencil',
    'fa-pencil': 'bi-pencil',
    'fa-trash': 'bi-trash',
    'fa-trash-o': 'bi-trash',
    'fa-trash-alt': 'bi-trash',

    # Comunicación
    'fa-phone': 'bi-telephone',
    'fa-phone-alt': 'bi-telephone-fill',
    'fa-envelope': 'bi-envelope',
    'fa-envelope-o': 'bi-envelope',
    'fa-envelope-open': 'bi-envelope-open',
    'fa-comment': 'bi-chat',
    'fa-comment-o': 'bi-chat',
    'fa-comments': 'bi-chat-dots',
    'fa-comments-o': 'bi-chat-dots',
    'fa-whatsapp': 'bi-whatsapp',

    # Redes Sociales
    'fa-facebook': 'bi-facebook',
    'fa-facebook-f': 'bi-facebook',
    'fa-facebook-square': 'bi-facebook',
    'fa-instagram': 'bi-instagram',
    'fa-twitter': 'bi-twitter-x',
    'fa-x-twitter': 'bi-twitter-x',
    'fa-youtube': 'bi-youtube',
    'fa-linkedin': 'bi-linkedin',
    'fa-linkedin-in': 'bi-linkedin',

    # Navegación
    'fa-arrow-left': 'bi-arrow-left',
    'fa-arrow-right': 'bi-arrow-right',
    'fa-arrow-up': 'bi-arrow-up',
    'fa-arrow-down': 'bi-arrow-down',
    'fa-chevron-left': 'bi-chevron-left',
    'fa-chevron-right': 'bi-chevron-right',
    'fa-chevron-up': 'bi-chevron-up',
    'fa-chevron-down': 'bi-chevron-down',
    'fa-angle-left': 'bi-chevron-left',
    'fa-angle-right': 'bi-chevron-right',
    'fa-angle-up': 'bi-chevron-up',
    'fa-angle-down': 'bi-chevron-down',
    'fa-bars': 'bi-list',
    'fa-times': 'bi-x',
    'fa-times-circle': 'bi-x-circle',
    'fa-close': 'bi-x',

    # Multimedia
    'fa-image': 'bi-image',
    'fa-images': 'bi-images',
    'fa-camera': 'bi-camera',
    'fa-camera-retro': 'bi-camera-fill',
    'fa-video': 'bi-camera-video',
    'fa-video-camera': 'bi-camera-video-fill',
    'fa-play': 'bi-play',
    'fa-play-circle': 'bi-play-circle',
    'fa-pause': 'bi-pause',
    'fa-stop': 'bi-stop',
    'fa-eye': 'bi-eye',
    'fa-eye-slash': 'bi-eye-slash',

    # Estados
    'fa-check': 'bi-check',
    'fa-check-circle': 'bi-check-circle',
    'fa-check-circle-o': 'bi-check-circle',
    'fa-times-circle': 'bi-x-circle',
    'fa-exclamation': 'bi-exclamation',
    'fa-exclamation-triangle': 'bi-exclamation-triangle',
    'fa-exclamation-circle': 'bi-exclamation-circle',
    'fa-info': 'bi-info',
    'fa-info-circle': 'bi-info-circle',
    'fa-question': 'bi-question',
    'fa-question-circle': 'bi-question-circle',
    'fa-star': 'bi-star',
    'fa-star-o': 'bi-star',
    'fa-star-half': 'bi-star-half',
    'fa-star-half-o': 'bi-star-half',

    # Usuario
    'fa-user': 'bi-person',
    'fa-user-o': 'bi-person',
    'fa-user-circle': 'bi-person-circle',
    'fa-users': 'bi-people',
    'fa-user-plus': 'bi-person-plus',
    'fa-user-times': 'bi-person-x',

    # Finanzas
    'fa-dollar': 'bi-currency-dollar',
    'fa-dollar-sign': 'bi-currency-dollar',
    'fa-money': 'bi-cash',
    'fa-money-bill': 'bi-cash-stack',
    'fa-credit-card': 'bi-credit-card',
    'fa-credit-card-alt': 'bi-credit-card-2-front',
    'fa-wallet': 'bi-wallet',
    'fa-percentage': 'bi-percent',
    'fa-percent': 'bi-percent',

    # Documentos
    'fa-file': 'bi-file-earmark',
    'fa-file-o': 'bi-file-earmark',
    'fa-file-text': 'bi-file-text',
    'fa-file-text-o': 'bi-file-text',
    'fa-file-pdf': 'bi-file-pdf',
    'fa-file-pdf-o': 'bi-file-pdf',
    'fa-file-word': 'bi-file-word',
    'fa-file-excel': 'bi-file-excel',
    'fa-file-image': 'bi-file-image',
    'fa-folder': 'bi-folder',
    'fa-folder-o': 'bi-folder',
    'fa-folder-open': 'bi-folder-open',

    # UI
    'fa-cog': 'bi-gear',
    'fa-cogs': 'bi-gear-fill',
    'fa-sliders': 'bi-sliders',
    'fa-th': 'bi-grid',
    'fa-th-large': 'bi-grid-3x3',
    'fa-th-list': 'bi-list-ul',
    'fa-list': 'bi-list-ul',
    'fa-list-ul': 'bi-list-ul',
    'fa-list-ol': 'bi-list-ol',
    'fa-plus': 'bi-plus',
    'fa-plus-circle': 'bi-plus-circle',
    'fa-minus': 'bi-dash',
    'fa-minus-circle': 'bi-dash-circle',

    # Calendario y Tiempo
    'fa-calendar': 'bi-calendar',
    'fa-calendar-o': 'bi-calendar',
    'fa-calendar-alt': 'bi-calendar-event',
    'fa-calendar-check': 'bi-calendar-check',
    'fa-clock': 'bi-clock',
    'fa-clock-o': 'bi-clock',

    # Dashboard
    'fa-dashboard': 'bi-speedometer2',
    'fa-tachometer': 'bi-speedometer',
    'fa-tachometer-alt': 'bi-speedometer2',
    'fa-chart-bar': 'bi-bar-chart',
    'fa-chart-line': 'bi-graph-up',
    'fa-chart-pie': 'bi-pie-chart',

    # Otros
    'fa-tag': 'bi-tag',
    'fa-tags': 'bi-tags',
    'fa-bookmark': 'bi-bookmark',
    'fa-bookmark-o': 'bi-bookmark',
    'fa-bell': 'bi-bell',
    'fa-bell-o': 'bi-bell',
    'fa-key': 'bi-key',
    'fa-lock': 'bi-lock',
    'fa-unlock': 'bi-unlock',
    'fa-shield': 'bi-shield',
    'fa-shield-alt': 'bi-shield-fill',
    'fa-link': 'bi-link',
    'fa-unlink': 'bi-link-45deg',
    'fa-external-link': 'bi-box-arrow-up-right',
    'fa-external-link-alt': 'bi-box-arrow-up-right',
    'fa-copy': 'bi-clipboard',
    'fa-clipboard': 'bi-clipboard',
    'fa-paste': 'bi-clipboard-check',
    'fa-save': 'bi-save',
    'fa-sync': 'bi-arrow-repeat',
    'fa-sync-alt': 'bi-arrow-repeat',
    'fa-refresh': 'bi-arrow-clockwise',
    'fa-undo': 'bi-arrow-counterclockwise',
    'fa-redo': 'bi-arrow-clockwise',
    'fa-wrench': 'bi-wrench',
    'fa-tools': 'bi-tools',
    'fa-balance-scale': 'bi-balance-scale',
}

def convert_icon_classes(content, file_path):
    """Convierte las clases de Font Awesome a Bootstrap Icons"""
    changes = []
    original_content = content

    # Patrón para encontrar clases de Font Awesome
    # Busca: fa fa-*, fas fa-*, fab fa-*, far fa-*
    patterns = [
        (r'\bfa\s+fa-(\w+(?:-\w+)*)', 'fa'),      # fa fa-home
        (r'\bfas\s+fa-(\w+(?:-\w+)*)', 'fas'),    # fas fa-home
        (r'\bfab\s+fa-(\w+(?:-\w+)*)', 'fab'),    # fab fa-facebook
        (r'\bfar\s+fa-(\w+(?:-\w+)*)', 'far'),    # far fa-heart
    ]

    for pattern, prefix in patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            icon_name = match.group(1)
            fa_icon = f'fa-{icon_name}'

            # Buscar mapeo
            if fa_icon in ICON_MAPPING:
                bi_icon = ICON_MAPPING[fa_icon]
                old_class = match.group(0)
                new_class = f'bi {bi_icon}'

                content = content.replace(old_class, new_class)
                changes.append(f'  {old_class} → {new_class}')

    return content, changes

def process_file(file_path):
    """Procesa un archivo y convierte los iconos"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        new_content, changes = convert_icon_classes(content, file_path)

        if changes:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            print(f'\n[OK] {file_path}')
            for change in changes:
                print(change)

            return len(changes)

        return 0

    except Exception as e:
        print(f'\n[ERROR] {file_path}: {e}')
        return 0

def main():
    base_path = Path(r'c:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18')

    modules = [
        'theme_bohio_real_estate',
        'bohio_real_estate',
        'bohio_crm',
        'real_estate_bits',
    ]

    print('=' * 80)
    print('CONVERSIÓN DE FONT AWESOME A BOOTSTRAP ICONS')
    print('=' * 80)

    total_changes = 0
    total_files = 0

    for module in modules:
        print(f'\n\n{"="*80}')
        print(f'MÓDULO: {module}')
        print(f'{"="*80}')

        module_path = base_path / module

        # Buscar todos los archivos con extensiones relevantes
        extensions = ['.xml', '.py', '.js', '.html', '.md']

        for ext in extensions:
            for file_path in module_path.rglob(f'*{ext}'):
                # Saltar ciertos directorios
                skip_dirs = ['__pycache__', 'node_modules', '.git', 'static/description']
                if any(skip_dir in str(file_path) for skip_dir in skip_dirs):
                    continue

                changes_count = process_file(file_path)
                if changes_count > 0:
                    total_changes += changes_count
                    total_files += 1

    print(f'\n\n{"="*80}')
    print('RESUMEN')
    print(f'{"="*80}')
    print(f'Archivos modificados: {total_files}')
    print(f'Cambios totales: {total_changes}')
    print(f'\n[OK] Conversion completada')

if __name__ == '__main__':
    main()

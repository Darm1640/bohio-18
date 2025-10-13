#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para cargar imágenes de propiedades desde carpetas locales a Odoo 18
- La primera imagen se establece como imagen principal (image_1920)
- El resto de imágenes se cargan como imágenes secundarias en product.image
- Las imágenes aparecerán en el carrusel del sitio web
"""

import xmlrpc.client
import base64
import os
import sys
from pathlib import Path

# Fix para Windows - Forzar UTF-8 en stdout/stderr
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuración de conexión
URL = 'https://darm1640-bohio-18.odoo.com'
DB = 'darm1640-bohio-18-main-24081960'
USERNAME = 'admin'
PASSWORD = '123456'

# Ruta base de las imágenes
BASE_IMAGE_PATH = r'C:\Users\darm1\OneDrive\Documentos\GitHub\bohio-18\property_images'

def connect_odoo():
    """Conectar a Odoo y retornar el objeto models"""
    print(f"[1/4] Conectando a Odoo: {URL}")
    try:
        common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common')
        uid = common.authenticate(DB, USERNAME, PASSWORD, {})

        if not uid:
            print("❌ Error: No se pudo autenticar. Verifica usuario y contraseña.")
            sys.exit(1)

        print(f"✓ Conectado exitosamente - UID: {uid}")
        models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object')
        return models, uid
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        sys.exit(1)

def get_image_base64(image_path):
    """Leer imagen y convertirla a base64"""
    try:
        with open(image_path, 'rb') as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception as e:
        print(f"  ⚠ Error leyendo {image_path}: {e}")
        return None

def get_sorted_images(folder_path):
    """Obtener lista ordenada de imágenes en una carpeta"""
    valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    images = []

    try:
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path):
                ext = os.path.splitext(file)[1].lower()
                if ext in valid_extensions:
                    images.append(file_path)

        # Ordenar alfabéticamente
        images.sort()
        return images
    except Exception as e:
        print(f"  ⚠ Error leyendo carpeta {folder_path}: {e}")
        return []

def upload_images_for_property(models, uid, property_ref, property_folder):
    """
    Cargar imágenes de una propiedad específica

    Args:
        models: Objeto XML-RPC de Odoo
        uid: User ID autenticado
        property_ref: Referencia de la propiedad (nombre de carpeta)
        property_folder: Ruta completa de la carpeta con imágenes
    """
    print(f"\n{'='*80}")
    print(f"📦 Procesando propiedad: {property_ref}")
    print(f"{'='*80}")

    # 1. Buscar la propiedad por referencia
    try:
        property_ids = models.execute_kw(DB, uid, PASSWORD,
            'product.template', 'search',
            [[('default_code', '=', property_ref), ('is_property', '=', True)]],
            {'limit': 1}
        )

        if not property_ids:
            print(f"  ⚠ Propiedad con ref '{property_ref}' no encontrada. Buscando por ID...")

            # Intentar buscar por ID si el ref es numérico
            try:
                prop_id = int(property_ref)
                property_ids = models.execute_kw(DB, uid, PASSWORD,
                    'product.template', 'search',
                    [[('id', '=', prop_id), ('is_property', '=', True)]],
                    {'limit': 1}
                )

                if not property_ids:
                    print(f"  ❌ Propiedad con ID {property_ref} no encontrada. SALTANDO.")
                    return False
            except ValueError:
                print(f"  ❌ No se pudo encontrar la propiedad. SALTANDO.")
                return False

        property_id = property_ids[0]

        # Obtener nombre de la propiedad
        property_data = models.execute_kw(DB, uid, PASSWORD,
            'product.template', 'read',
            [property_id],
            {'fields': ['name', 'default_code']}
        )[0]

        print(f"  ✓ Propiedad encontrada: {property_data['name']} (ID: {property_id})")

    except Exception as e:
        print(f"  ❌ Error buscando propiedad: {e}")
        return False

    # 2. Obtener lista de imágenes ordenadas
    images = get_sorted_images(property_folder)

    if not images:
        print(f"  ⚠ No se encontraron imágenes en la carpeta.")
        return False

    print(f"  📸 Se encontraron {len(images)} imágenes")

    # 3. Procesar primera imagen como imagen principal
    print(f"\n  [IMAGEN PRINCIPAL]")
    first_image = images[0]
    print(f"  └─ {os.path.basename(first_image)}")

    image_base64 = get_image_base64(first_image)
    if image_base64:
        try:
            models.execute_kw(DB, uid, PASSWORD,
                'product.template', 'write',
                [[property_id], {'image_1920': image_base64}]
            )
            print(f"     ✓ Imagen principal actualizada")
        except Exception as e:
            print(f"     ❌ Error actualizando imagen principal: {e}")
            return False
    else:
        print(f"     ❌ No se pudo leer la imagen")
        return False

    # 4. Procesar resto de imágenes como imágenes secundarias
    if len(images) > 1:
        print(f"\n  [IMÁGENES SECUNDARIAS - CARRUSEL]")

        # Eliminar imágenes secundarias existentes para evitar duplicados
        try:
            existing_images = models.execute_kw(DB, uid, PASSWORD,
                'product.image', 'search',
                [[('product_tmpl_id', '=', property_id)]]
            )

            if existing_images:
                models.execute_kw(DB, uid, PASSWORD,
                    'product.image', 'unlink',
                    [existing_images]
                )
                print(f"  └─ Eliminadas {len(existing_images)} imágenes anteriores")
        except Exception as e:
            print(f"  ⚠ Error eliminando imágenes anteriores: {e}")

        # Cargar nuevas imágenes secundarias
        success_count = 0
        for idx, img_path in enumerate(images[1:], start=2):
            img_name = os.path.basename(img_path)
            print(f"  └─ [{idx}/{len(images)}] {img_name}", end=" ")

            img_base64 = get_image_base64(img_path)
            if img_base64:
                try:
                    models.execute_kw(DB, uid, PASSWORD,
                        'product.image', 'create',
                        [{
                            'name': img_name,
                            'product_tmpl_id': property_id,
                            'image_1920': img_base64,
                            'sequence': idx * 10  # Secuencia para ordenar
                        }]
                    )
                    print("✓")
                    success_count += 1
                except Exception as e:
                    print(f"❌ Error: {e}")
            else:
                print("❌ No se pudo leer")

        print(f"\n  📊 Resumen: {success_count}/{len(images)-1} imágenes secundarias cargadas")

    print(f"\n  ✅ Propiedad {property_ref} procesada exitosamente")
    print(f"     - 1 imagen principal")
    print(f"     - {len(images)-1} imágenes en carrusel")

    return True

def process_all_properties(models, uid, base_path):
    """Procesar todas las carpetas de propiedades"""
    print(f"\n[2/4] Escaneando carpetas de propiedades...")

    if not os.path.exists(base_path):
        print(f"❌ Error: La ruta {base_path} no existe")
        sys.exit(1)

    # Obtener todas las carpetas
    folders = []
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path):
            folders.append((item, item_path))

    folders.sort()

    print(f"✓ Se encontraron {len(folders)} carpetas de propiedades")

    print(f"\n[3/4] Procesando propiedades...")

    success_count = 0
    failed_count = 0
    skipped_count = 0

    for idx, (folder_name, folder_path) in enumerate(folders, start=1):
        print(f"\n[{idx}/{len(folders)}] {folder_name}")

        # Verificar si la carpeta tiene imágenes
        images = get_sorted_images(folder_path)
        if not images:
            print(f"  ⊘ Sin imágenes - SALTANDO")
            skipped_count += 1
            continue

        # Procesar propiedad
        result = upload_images_for_property(models, uid, folder_name, folder_path)

        if result:
            success_count += 1
        else:
            failed_count += 1

    # Resumen final
    print(f"\n{'='*80}")
    print(f"[4/4] RESUMEN FINAL")
    print(f"{'='*80}")
    print(f"  ✅ Exitosas:  {success_count}")
    print(f"  ❌ Fallidas:  {failed_count}")
    print(f"  ⊘  Saltadas:  {skipped_count}")
    print(f"  📦 Total:     {len(folders)}")
    print(f"{'='*80}\n")

def main():
    """Función principal"""
    print("="*80)
    print("  CARGA DE IMÁGENES DE PROPIEDADES - ODOO 18")
    print("  - Primera imagen: Imagen principal (image_1920)")
    print("  - Resto: Carrusel (product.image)")
    print("="*80)

    # Conectar a Odoo
    models, uid = connect_odoo()

    # Procesar todas las propiedades
    process_all_properties(models, uid, BASE_IMAGE_PATH)

    print("✅ Proceso completado")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Proceso interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

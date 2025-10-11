#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para crear imágenes en Odoo desde carpetas descargadas localmente
Lee las imágenes desde property_images/[CODE]/ y las sube a Odoo
"""
import os
import sys
import base64
import xmlrpc.client


class OdooImageUploader:
    """Sube imágenes a Odoo desde carpetas locales"""

    def __init__(self, odoo_url, odoo_db, odoo_user, odoo_pass):
        self.odoo_url = odoo_url
        self.odoo_db = odoo_db
        self.odoo_user = odoo_user
        self.odoo_pass = odoo_pass
        self.uid = None
        self.models = None

    def connect(self):
        """Conecta a Odoo"""
        try:
            print(f"\n🔌 Conectando a {self.odoo_url}...")
            common = xmlrpc.client.ServerProxy(f'{self.odoo_url}/xmlrpc/2/common')

            print(f"🔑 Autenticando como '{self.odoo_user}'...")
            self.uid = common.authenticate(self.odoo_db, self.odoo_user, self.odoo_pass, {})

            if not self.uid:
                print("❌ ERROR: Autenticación fallida")
                return False

            print(f"✅ Autenticación exitosa (UID: {self.uid})")
            self.models = xmlrpc.client.ServerProxy(f'{self.odoo_url}/xmlrpc/2/object')
            return True

        except Exception as e:
            print(f"❌ Error conectando a Odoo: {e}")
            return False

    def find_property_by_code(self, code):
        """Busca propiedad en Odoo por código"""
        try:
            # Intentar con default_code
            property_ids = self.models.execute_kw(
                self.odoo_db, self.uid, self.odoo_pass,
                'product.template', 'search',
                [[('default_code', '=', code)]]
            )

            if property_ids:
                return property_ids[0]

            # Intentar con BOH-CODE
            property_ids = self.models.execute_kw(
                self.odoo_db, self.uid, self.odoo_pass,
                'product.template', 'search',
                [[('default_code', '=', f'BOH-{code}')]]
            )

            if property_ids:
                return property_ids[0]

            # Intentar buscar por ID directo si es número
            if code.isdigit():
                property_ids = self.models.execute_kw(
                    self.odoo_db, self.uid, self.odoo_pass,
                    'product.template', 'search',
                    [[('id', '=', int(code))]]
                )

                if property_ids:
                    return property_ids[0]

            return None

        except Exception as e:
            print(f"❌ Error buscando propiedad {code}: {e}")
            return None

    def upload_image(self, property_id, image_path, sequence, is_cover=False):
        """Sube una imagen a Odoo"""
        try:
            # Leer imagen y convertir a base64
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            # Extraer nombre de archivo
            filename = os.path.basename(image_path)

            # Preparar valores
            vals = {
                'name': filename,
                'property_id': property_id,
                'sequence': sequence,
                'is_cover': is_cover,
                'image_type': 'main' if is_cover else 'other',
                'image_1920': image_data,
                'is_public': True
            }

            # Crear imagen en Odoo
            image_id = self.models.execute_kw(
                self.odoo_db, self.uid, self.odoo_pass,
                'property.image', 'create',
                [vals]
            )

            return image_id

        except Exception as e:
            print(f"❌ Error subiendo imagen {filename}: {e}")
            return None

    def process_property_folder(self, code, folder_path):
        """Procesa todas las imágenes de una carpeta"""
        print(f"\n📁 Procesando carpeta: {folder_path}")

        # Buscar propiedad en Odoo
        property_id = self.find_property_by_code(code)

        if not property_id:
            print(f"❌ Propiedad con código {code} no encontrada en Odoo")
            return None

        print(f"✅ Propiedad encontrada en Odoo: ID={property_id}")

        # Verificar si ya tiene imágenes
        existing_images = self.models.execute_kw(
            self.odoo_db, self.uid, self.odoo_pass,
            'property.image', 'search_count',
            [[('property_id', '=', property_id)]]
        )

        if existing_images > 0:
            print(f"⚠️  La propiedad ya tiene {existing_images} imágenes en Odoo")
            response = input("   ¿Desea agregar más imágenes? (s/n): ")
            if response.lower() != 's':
                print("   Saltando...")
                return None

        # Listar imágenes en carpeta
        images = []
        for filename in sorted(os.listdir(folder_path)):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                images.append(os.path.join(folder_path, filename))

        if not images:
            print("⚠️  No se encontraron imágenes en la carpeta")
            return None

        print(f"📸 Encontradas {len(images)} imágenes")

        # Subir imágenes
        stats = {
            'total': len(images),
            'success': 0,
            'failed': 0
        }

        for idx, image_path in enumerate(images, 1):
            filename = os.path.basename(image_path)
            is_cover = (idx == 1)  # Primera imagen es portada

            print(f"\n   [{idx}/{len(images)}] Subiendo: {filename}")

            if is_cover:
                print("      ⭐ PRINCIPAL")

            image_id = self.upload_image(property_id, image_path, idx, is_cover)

            if image_id:
                print(f"      ✅ Imagen creada en Odoo: ID={image_id}")
                stats['success'] += 1
            else:
                print(f"      ❌ Error subiendo imagen")
                stats['failed'] += 1

        return stats

    def process_all_folders(self, base_dir="property_images"):
        """Procesa todas las carpetas de propiedades"""
        print("\n" + "="*80)
        print("SUBIDA MASIVA DE IMÁGENES A ODOO")
        print("="*80)

        if not os.path.exists(base_dir):
            print(f"❌ Carpeta no encontrada: {base_dir}")
            return

        # Listar carpetas
        folders = []
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path) and item.isdigit():
                folders.append((item, item_path))

        if not folders:
            print(f"❌ No se encontraron carpetas de propiedades en {base_dir}")
            return

        print(f"\n📋 Encontradas {len(folders)} carpetas de propiedades")

        # Estadísticas globales
        global_stats = {
            'total_properties': len(folders),
            'processed': 0,
            'skipped': 0,
            'not_found': 0,
            'total_images': 0
        }

        # Procesar cada carpeta
        for idx, (code, folder_path) in enumerate(folders, 1):
            print(f"\n[{idx}/{len(folders)}] Propiedad: {code}")
            print("-" * 80)

            stats = self.process_property_folder(code, folder_path)

            if stats:
                global_stats['processed'] += 1
                global_stats['total_images'] += stats['success']
            elif stats is None:
                global_stats['skipped'] += 1
            else:
                global_stats['not_found'] += 1

        # Reporte final
        print("\n" + "="*80)
        print("📊 REPORTE FINAL DE SUBIDA")
        print("="*80)
        print(f"   Total Propiedades: {global_stats['total_properties']}")
        print(f"   ✅ Procesadas: {global_stats['processed']}")
        print(f"   ⚠️  Saltadas: {global_stats['skipped']}")
        print(f"   ❌ No encontradas en Odoo: {global_stats['not_found']}")
        print(f"   📸 Total Imágenes Subidas: {global_stats['total_images']}")
        print("="*80)


def main():
    """Función principal"""

    print("="*80)
    print("CREADOR DE IMÁGENES EN ODOO DESDE CARPETAS LOCALES")
    print("="*80)

    # Configuración Odoo
    ODOO_URL = 'http://localhost:8069'
    ODOO_DB = 'bohio_db'
    ODOO_USER = 'admin'
    ODOO_PASS = 'admin'

    print("\n📝 CONFIGURACIÓN:")
    print(f"   URL: {ODOO_URL}")
    print(f"   BD: {ODOO_DB}")
    print(f"   Usuario: {ODOO_USER}")

    # Crear uploader
    uploader = OdooImageUploader(ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASS)

    # Conectar
    if not uploader.connect():
        print("\n❌ No se pudo conectar a Odoo")
        return

    # Procesar carpetas
    uploader.process_all_folders("property_images")


if __name__ == "__main__":
    main()

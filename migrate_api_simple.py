#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script SIMPLE para migrar propiedades NUEVAS desde API Arrendasoft a Odoo 18
Solo usa campos BASICOS que sabemos que funcionan
"""
import os
import json
import requests
import xmlrpc.client


class SimpleAPIToOdoo18:
    """Migrador simple API -> Odoo 18"""

    def __init__(self, listado_file='listado.txt'):
        self.api_url = "https://bohio.arrendasoft.co/service/v2/public/map-of-properties/data"

        # Odoo 18
        self.target = {
            'url': 'https://darm1640-bohio-18.odoo.com',
            'db': 'darm1640-bohio-18-main-24081960',
            'username': 'admin',
            'password': '123456'
        }

        self.target_common = xmlrpc.client.ServerProxy(f"{self.target['url']}/xmlrpc/2/common")
        self.target_models = xmlrpc.client.ServerProxy(f"{self.target['url']}/xmlrpc/2/object")
        self.target_uid = None

        # Cache
        self.cache_file = 'migration_cache_new.json'
        self.cache = self._load_cache()

        # Códigos existentes (listado.txt)
        self.existing_codes = self._load_existing_codes(listado_file)

        print("\n" + "="*80)
        print("MIGRADOR SIMPLE: API ARRENDASOFT -> ODOO 18")
        print("="*80)

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'states': {}, 'cities': {}, 'regions': {}}

    def _save_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)

    def _load_existing_codes(self, listado_file):
        existing = set()
        if os.path.exists(listado_file):
            with open(listado_file, 'r', encoding='utf-8') as f:
                for line in f:
                    code = line.strip()
                    if code and code != 'default_code':
                        existing.add(code)
            print(f"\nCodigos en {listado_file}: {len(existing)}")
        else:
            print(f"\nArchivo {listado_file} no encontrado")
        return existing

    def connect_target(self):
        print("\n[1/2] Conectando a Odoo 18...")
        try:
            self.target_uid = self.target_common.authenticate(
                self.target['db'],
                self.target['username'],
                self.target['password'],
                {}
            )
            if self.target_uid:
                print(f"   OK (UID: {self.target_uid})")
                return True
            else:
                print("   ERROR: Credenciales invalidas")
                return False
        except Exception as e:
            print(f"   ERROR: {e}")
            return False

    def get_properties_from_api(self, servicio=None):
        print("\n[2/2] Obteniendo propiedades desde API...")

        params = {}
        if servicio:
            params['Servicio'] = servicio

        servicio_text = {None: "TODAS", 1: "ARRIENDO", 2: "VENTA"}.get(servicio, "DESCONOCIDO")
        print(f"   Tipo: {servicio_text}")

        try:
            response = requests.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if 'campos' in data:
                propiedades = data['campos']
                print(f"   OK {len(propiedades)} propiedades")
                return propiedades
            else:
                print(f"   ERROR Formato inesperado")
                return []

        except Exception as e:
            print(f"   ERROR: {e}")
            return []

    def create_property(self, prop):
        codigo = prop.get('Codigo', 'SIN_CODIGO')
        titulo = prop.get('Titulo', 'Sin titulo')[:50]

        print(f"\n   [{codigo}] {titulo}", end=" ")

        # Verificar si está en listado.txt
        if str(codigo) in self.existing_codes:
            print("- En listado.txt")
            return {'status': 'in_listado'}

        # Verificar si existe en Odoo 18
        try:
            existing = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'product.template', 'search',
                [[('default_code', '=', str(codigo))]]
            )

            if existing:
                print(f"- Ya existe ({existing[0]})")
                return {'status': 'exists', 'id': existing[0]}
        except:
            pass

        # Preparar datos (solo campos BÁSICOS que funcionan)
        vals = {
            'type': 'consu',  # IMPORTANTE: Este es el tipo que funciona
            'default_code': str(codigo),
            'name': prop.get('Titulo', f'Propiedad {codigo}'),
            'active': True,
            'sale_ok': True,
        }

        # DESCRIPCIÓN
        desc = prop.get('Descripcion', '')
        if desc:
            vals['description'] = desc

        # PRECIO
        precio = prop.get('Precio')
        if precio:
            try:
                vals['list_price'] = float(precio)
            except:
                vals['list_price'] = 0.0

        # UBICACIÓN
        direccion = prop.get('Direccion', '')
        ciudad = prop.get('Ciudad', '')
        barrio = prop.get('Barrio', '')

        if direccion:
            vals['street'] = direccion
        if barrio:
            vals['street2'] = barrio
            vals['neighborhood'] = barrio
        if ciudad:
            vals['city'] = ciudad

        # COORDENADAS
        lat = prop.get('Latitud')
        lng = prop.get('Longitud')
        if lat:
            try:
                vals['latitude'] = float(lat)
            except:
                pass
        if lng:
            try:
                vals['longitude'] = float(lng)
            except:
                pass

        # CARACTERÍSTICAS
        habitaciones = prop.get('Habitaciones')
        if habitaciones:
            try:
                vals['num_bedrooms'] = int(habitaciones)
            except:
                pass

        banos = prop.get('Banos')
        if banos:
            try:
                vals['num_bathrooms'] = int(banos)
            except:
                pass

        garajes = prop.get('Garajes')
        if garajes:
            try:
                vals['n_garage'] = int(garajes)
            except:
                pass

        area = prop.get('Area')
        if area:
            try:
                vals['property_area'] = float(area)
                vals['area_in_m2'] = float(area)
            except:
                pass

        # URL
        tipo_prop = prop.get('Tipo', 'Propiedad').replace(' ', '-')
        servicio_prop = prop.get('Servicio', 'Venta')
        vals['website'] = f"https://bohioconsultores.com/detalle-propiedad/?{tipo_prop}-en-{servicio_prop}-{codigo}"

        # Crear
        try:
            new_id = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'product.template', 'create',
                [vals]
            )

            print(f"- CREADA ({new_id}, {len(vals)} campos)")
            return {'status': 'created', 'id': new_id, 'fields': len(vals)}

        except Exception as e:
            error_msg = str(e)
            if 'Invalid field' in error_msg:
                start = error_msg.find("'")
                end = error_msg.find("'", start+1)
                field_name = error_msg[start+1:end] if start >= 0 and end > start else "?"
                print(f"- ERROR campo invalido: {field_name}")
            else:
                print(f"- ERROR: {error_msg[:80]}")
            return {'status': 'error', 'error': str(e)}

    def migrate_from_api(self, servicio=None, limit=None, offset=0):
        print("\n" + "="*80)
        print("MIGRACION: API -> ODOO 18")
        print("="*80)

        if not self.connect_target():
            return None

        propiedades = self.get_properties_from_api(servicio=servicio)

        if not propiedades:
            print("\nNo se encontraron propiedades")
            return None

        if offset > 0:
            propiedades = propiedades[offset:]
            print(f"\nIniciando desde: {offset}")

        if limit:
            propiedades = propiedades[:limit]
            print(f"Limitando a: {limit}")

        print(f"\n{'='*80}")
        print(f"PROCESANDO {len(propiedades)} PROPIEDADES")
        print(f"{'='*80}")

        stats = {
            'total': len(propiedades),
            'created': 0,
            'exists': 0,
            'in_listado': 0,
            'errors': 0,
            'total_fields': 0,
            'new_properties': []
        }

        for idx, prop in enumerate(propiedades, 1):
            print(f"[{idx}/{len(propiedades)}]", end="")

            result = self.create_property(prop)

            if result:
                if result['status'] == 'created':
                    stats['created'] += 1
                    stats['total_fields'] += result.get('fields', 0)
                    stats['new_properties'].append({
                        'codigo': prop.get('Codigo'),
                        'titulo': prop.get('Titulo', '')[:50],
                        'id': result.get('id')
                    })
                elif result['status'] == 'exists':
                    stats['exists'] += 1
                elif result['status'] == 'in_listado':
                    stats['in_listado'] += 1
                elif result['status'] == 'error':
                    stats['errors'] += 1

        # Reporte
        print("\n" + "="*80)
        print("REPORTE FINAL")
        print("="*80)
        print(f"   Total procesadas: {stats['total']}")
        print(f"   CREADAS NUEVAS: {stats['created']}")
        print(f"   En listado.txt: {stats['in_listado']}")
        print(f"   Ya existian: {stats['exists']}")
        print(f"   Errores: {stats['errors']}")

        if stats['created'] > 0:
            avg_fields = stats['total_fields'] / stats['created']
            print(f"   Promedio campos: {avg_fields:.1f}")
            print(f"\n   PROPIEDADES NUEVAS:")
            for prop in stats['new_properties']:
                print(f"      {prop['codigo']}: {prop['titulo']} (ID: {prop['id']})")

        print("="*80)

        self._save_cache()

        return stats


def main():
    import sys

    print("="*80)
    print("MIGRADOR SIMPLE: API -> ODOO 18")
    print("="*80)

    servicio = None
    limit = 10
    offset = 0

    if len(sys.argv) > 1:
        arg1 = sys.argv[1].lower()
        if arg1 == 'venta':
            servicio = 2
        elif arg1 == 'arriendo':
            servicio = 1
        elif arg1 == 'todas':
            servicio = None
        else:
            try:
                limit = int(sys.argv[1])
            except:
                print("\nUSO: python migrate_api_simple.py [limit] [offset]")
                print("EJEMPLOS:")
                print("   python migrate_api_simple.py 10")
                print("   python migrate_api_simple.py 50 10")
                print("   python migrate_api_simple.py venta")
                return

    if len(sys.argv) > 2:
        try:
            limit = int(sys.argv[2]) if servicio else int(sys.argv[2])
        except:
            pass

    if len(sys.argv) > 3:
        try:
            offset = int(sys.argv[3])
        except:
            pass

    migrator = SimpleAPIToOdoo18()
    migrator.migrate_from_api(servicio=servicio, limit=limit, offset=offset)


if __name__ == "__main__":
    main()

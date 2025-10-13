#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para migrar campo Caracteristicas_values de la API
Este campo contiene TODAS las características reales de las propiedades
"""
import os
import json
import requests
import xmlrpc.client
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class CaracteristicasMigrator:
    """Migrar características completas desde API"""

    def __init__(self):
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

        # Campos
        self.target_fields = {}

        # Mapeo de características API -> Odoo
        self.caracteristicas_map = {
            # Números
            'alcobas': 'num_bedrooms',
            'banos': 'num_bathrooms',
            'parqueadero_cubierto': 'n_garage',
            'garajes': 'n_garage',
            'piso_numero': 'floor_number',

            # Booleanos
            'sala_comedor': 'living_dining',
            'cocina_integral': 'integral_kitchen',
            'red_de_gas': 'gas_network',
            'balcon': 'balcony',
            'zona_de_ropas': 'laundry_area',
            'ascensor': 'elevator',
            'piscina': 'pool',
            'salon_social': 'social_hall',
            'gimnasio': 'gym',
            'amoblado': 'furnished',
            'parqueadero': 'garage',
            'porteria': 'concierge',
            'vigilancia': 'surveillance',
            'conjunto_cerrado': 'gated_community',
            'zona_verde': 'green_area',
            'terraza': 'terrace',
            'patio': 'patio',
            'jardin': 'garden',
            'chimenea': 'fireplace',
            'closets': 'closets',
            'alarma': 'alarm',
            'deposito': 'storage',

            # Texto
            'tipo_de_piso': 'floor_type',
        }

        # Stats
        self.stats = {
            'total': 0,
            'updated': 0,
            'not_found': 0,
            'errors': 0,
            'total_fields': 0,
            'fields_added': {}
        }

    def connect_target(self):
        print("\n[1/3] Conectando a Odoo 18...")
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
        except Exception as e:
            print(f"   ERROR: {e}")
            return False

    def discover_fields(self):
        print("\n[2/3] Descubriendo campos...")
        try:
            self.target_fields = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'product.template', 'fields_get', [],
                {'attributes': ['type', 'string']}
            )
            print(f"   Campos disponibles: {len(self.target_fields)}")
            return True
        except Exception as e:
            print(f"   ERROR: {e}")
            return False

    def get_properties_from_api(self):
        print("\n[3/3] Obteniendo propiedades desde API...")
        try:
            response = requests.get(self.api_url, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'campos' in data:
                propiedades = data['campos']
                print(f"   OK {len(propiedades)} propiedades")
                # Indexar por código
                return {str(p.get('Codigo')): p for p in propiedades}
            else:
                return {}
        except Exception as e:
            print(f"   ERROR: {e}")
            return {}

    def parse_caracteristicas(self, prop_data):
        """Parsear Caracteristicas_values y mapear a Odoo"""
        vals = {}

        if 'Caracteristicas_values' not in prop_data:
            return vals

        caract = prop_data['Caracteristicas_values']
        if not caract:
            return vals

        for api_key, api_value in caract.items():
            # Buscar mapeo
            odoo_field = self.caracteristicas_map.get(api_key)
            if not odoo_field:
                continue

            # Verificar que existe en Odoo
            if odoo_field not in self.target_fields:
                continue

            field_info = self.target_fields[odoo_field]
            field_type = field_info.get('type')

            try:
                # Integer
                if field_type == 'integer':
                    try:
                        vals[odoo_field] = int(api_value)
                        self.stats['fields_added'][odoo_field] = \
                            self.stats['fields_added'].get(odoo_field, 0) + 1
                    except:
                        pass

                # Boolean
                elif field_type == 'boolean':
                    # Considerar "1", "true", "si" como True
                    bool_val = str(api_value).lower() in ['1', 'true', 'si', 'sí', 'yes']
                    if bool_val:  # Solo agregar si es True
                        vals[odoo_field] = True
                        self.stats['fields_added'][odoo_field] = \
                            self.stats['fields_added'].get(odoo_field, 0) + 1

                # Char/Text
                elif field_type in ['char', 'text']:
                    if api_value and str(api_value).strip():
                        vals[odoo_field] = str(api_value)
                        self.stats['fields_added'][odoo_field] = \
                            self.stats['fields_added'].get(odoo_field, 0) + 1

            except Exception as e:
                pass

        # Parsear coordenadas (formato "lat:lng")
        if 'Coordenadas' in prop_data:
            coords = prop_data['Coordenadas']
            if coords and ':' in str(coords):
                try:
                    lat, lng = coords.split(':')
                    if 'latitude' in self.target_fields:
                        vals['latitude'] = float(lat)
                        self.stats['fields_added']['latitude'] = \
                            self.stats['fields_added'].get('latitude', 0) + 1
                    if 'longitude' in self.target_fields:
                        vals['longitude'] = float(lng)
                        self.stats['fields_added']['longitude'] = \
                            self.stats['fields_added'].get('longitude', 0) + 1
                except:
                    pass

        return vals

    def update_property(self, codigo, api_props):
        print(f"   [{codigo}]", end=" ")

        # Verificar si existe en API
        if codigo not in api_props:
            print("- No en API")
            return False

        api_prop = api_props[codigo]

        # Buscar en Odoo
        try:
            prop_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'product.template', 'search',
                [[('default_code', '=', codigo)]]
            )

            if not prop_ids:
                print("- No encontrada")
                self.stats['not_found'] += 1
                return False

            prop_id = prop_ids[0]
        except:
            print("- Error buscando")
            self.stats['errors'] += 1
            return False

        # Parsear características
        vals = self.parse_caracteristicas(api_prop)

        if not vals:
            print("- Sin caracteristicas")
            return True

        # Actualizar
        try:
            self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'product.template', 'write',
                [[prop_id], vals]
            )
            print(f"- ACTUALIZADA (+{len(vals)} campos)")
            self.stats['updated'] += 1
            self.stats['total_fields'] += len(vals)
            return True
        except Exception as e:
            print(f"- ERROR: {str(e)[:60]}")
            self.stats['errors'] += 1
            return False

    def update_from_range(self, start_id, end_id):
        print("\n" + "="*80)
        print("ACTUALIZACION: CARACTERISTICAS DESDE API")
        print("="*80)

        if not self.connect_target():
            return
        if not self.discover_fields():
            return

        # Obtener propiedades de API
        api_props = self.get_properties_from_api()
        if not api_props:
            return

        print(f"\n{'='*80}")
        print(f"ACTUALIZANDO PROPIEDADES ID {start_id} A {end_id}")
        print(f"{'='*80}")

        # Buscar propiedades en el rango
        try:
            prop_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'product.template', 'search',
                [[('id', '>=', start_id), ('id', '<=', end_id),
                  ('default_code', '!=', False)]]
            )

            if not prop_ids:
                print("\nNo se encontraron propiedades")
                return

            # Leer códigos
            props = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'product.template', 'read',
                [prop_ids], {'fields': ['default_code']}
            )

            print(f"\nEncontradas: {len(props)} propiedades")
            self.stats['total'] = len(props)

            # Actualizar
            for idx, prop in enumerate(props, 1):
                print(f"[{idx}/{len(props)}]", end="")
                self.update_property(prop['default_code'], api_props)

        except Exception as e:
            print(f"ERROR: {e}")
            return

        # Reporte
        print("\n" + "="*80)
        print("REPORTE FINAL")
        print("="*80)
        print(f"   Total procesadas: {self.stats['total']}")
        print(f"   ACTUALIZADAS: {self.stats['updated']}")
        print(f"   Sin características: {self.stats['total'] - self.stats['updated'] - self.stats['not_found'] - self.stats['errors']}")
        print(f"   No en API: {self.stats['not_found']}")
        print(f"   Errores: {self.stats['errors']}")

        if self.stats['updated'] > 0:
            avg = self.stats['total_fields'] / self.stats['updated']
            print(f"\n   Promedio campos agregados: {avg:.1f}")

            print(f"\n   Campos agregados:")
            for field, count in sorted(self.stats['fields_added'].items(),
                                      key=lambda x: x[1], reverse=True):
                field_label = self.target_fields.get(field, {}).get('string', field)
                print(f"      {field:25s} ({field_label[:30]:30s}): {count}")

        print("="*80)


def main():
    import sys

    if len(sys.argv) < 3:
        print("\nUSO: python migrate_api_caracteristicas.py [id_inicio] [id_fin]")
        print("\nEJEMPLOS:")
        print("   python migrate_api_caracteristicas.py 2365 2584")
        return

    try:
        start_id = int(sys.argv[1])
        end_id = int(sys.argv[2])
    except:
        print("ERROR: IDs deben ser numeros")
        return

    migrator = CaracteristicasMigrator()
    migrator.update_from_range(start_id, end_id)


if __name__ == "__main__":
    main()

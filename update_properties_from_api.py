#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para ACTUALIZAR propiedades existentes con TODOS los campos de la API
Lee propiedades creadas por migrate_api_simple.py (solo 9 campos)
Las actualiza con TODOS los campos disponibles desde la API
"""
import os
import json
import requests
import xmlrpc.client
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class PropertyUpdater:
    """Actualizador de propiedades con campos completos"""

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

        # Cache
        self.cache_file = 'migration_cache_api.json'
        self.cache = self._load_cache()

        # Campos
        self.target_fields = {}

        # Stats
        self.stats = {
            'total': 0,
            'updated': 0,
            'not_found': 0,
            'errors': 0,
            'with_state': 0,
            'with_city': 0,
            'with_region': 0,
            'total_fields': 0,
            'fields_added': {}
        }

        print("\n" + "="*80)
        print("ACTUALIZADOR: AGREGAR CAMPOS COMPLETOS DESDE API")
        print("="*80)

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'states': {}, 'cities': {}, 'regions': {}}

    def _save_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)

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
                {'attributes': ['type', 'relation']}
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
                print(f"   ERROR Formato inesperado")
                return {}
        except Exception as e:
            print(f"   ERROR: {e}")
            return {}

    def find_or_create_state(self, city_name):
        city_to_state = {
            'montería': 'Córdoba', 'monteria': 'Córdoba',
            'cerete': 'Córdoba', 'cereté': 'Córdoba',
            'montelibano': 'Córdoba', 'montelíbano': 'Córdoba',
            'sahagún': 'Córdoba', 'sahagun': 'Córdoba',
            'lorica': 'Córdoba', 'ayapel': 'Córdoba',
            'planeta rica': 'Córdoba', 'tierralta': 'Córdoba',
            'medellín': 'Antioquia', 'medellin': 'Antioquia',
            'bogotá': 'Cundinamarca', 'bogota': 'Cundinamarca',
            'cali': 'Valle del Cauca',
            'barranquilla': 'Atlántico',
            'cartagena': 'Bolívar',
            'tolu': 'Sucre', 'tolú': 'Sucre',
            'sincelejo': 'Sucre',
            'coveñas': 'Sucre', 'covenas': 'Sucre'
        }

        city_lower = city_name.lower() if city_name else ''
        state_name = city_to_state.get(city_lower)
        if not state_name:
            return None

        if state_name in self.cache['states']:
            return self.cache['states'][state_name]

        try:
            state_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'res.country.state', 'search',
                [[('name', 'ilike', state_name)]]
            )
            if state_ids:
                self.cache['states'][state_name] = state_ids[0]
                self._save_cache()
                return state_ids[0]
        except:
            pass
        return None

    def find_or_create_city(self, city_name, state_id):
        if not city_name or not state_id:
            return None
        cache_key = f"{city_name}_{state_id}"
        if cache_key in self.cache['cities']:
            return self.cache['cities'][cache_key]

        try:
            city_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'res.city', 'search',
                [[('name', 'ilike', city_name), ('state_id', '=', state_id)]]
            )
            if city_ids:
                self.cache['cities'][cache_key] = city_ids[0]
                self._save_cache()
                return city_ids[0]

            # Crear
            city_id = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'res.city', 'create',
                [{'name': city_name, 'state_id': state_id}]
            )
            self.cache['cities'][cache_key] = city_id
            self._save_cache()
            return city_id
        except:
            return None

    def find_or_create_region(self, barrio_name, city_id):
        if not barrio_name or not city_id:
            return None
        barrio_name = barrio_name.strip()
        if not barrio_name:
            return None

        cache_key = f"{barrio_name}_{city_id}"
        if cache_key in self.cache['regions']:
            return self.cache['regions'][cache_key]

        try:
            region_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'region.region', 'search',
                [[('name', 'ilike', barrio_name), ('city_id', '=', city_id)]]
            )
            if region_ids:
                self.cache['regions'][cache_key] = region_ids[0]
                self._save_cache()
                return region_ids[0]

            # Crear
            region_id = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'region.region', 'create',
                [{'name': barrio_name, 'city_id': city_id}]
            )
            self.cache['regions'][cache_key] = region_id
            self._save_cache()
            return region_id
        except:
            return None

    def map_api_to_odoo(self, prop):
        """Mapear TODOS los campos de API a Odoo"""
        vals = {}

        # Mapeo
        mapping = {
            'Descripcion': 'description',
            'Zona': 'zone',
            'AreaConstruida': 'construction_area',
            'Piso': 'floor_number',
            'Estrato': 'property_stratum',
            'Antiguedad': 'property_age',
            'Administracion': 'property_admin_price',
        }

        for api_field, odoo_field in mapping.items():
            if api_field not in prop:
                continue
            value = prop.get(api_field)
            if not value:
                continue
            if odoo_field not in self.target_fields:
                continue

            field_type = self.target_fields[odoo_field].get('type')
            try:
                if field_type == 'integer':
                    vals[odoo_field] = int(value)
                elif field_type == 'float' or field_type == 'monetary':
                    vals[odoo_field] = float(value)
                elif field_type == 'char' or field_type == 'text':
                    vals[odoo_field] = str(value)
                else:
                    vals[odoo_field] = value
                self.stats['fields_added'][odoo_field] = \
                    self.stats['fields_added'].get(odoo_field, 0) + 1
            except:
                pass

        return vals

    def update_property(self, codigo, prop_data, api_props):
        print(f"   [{codigo}]", end=" ")

        # Verificar si existe en API
        if codigo not in api_props:
            print("- No en API")
            return False

        api_prop = api_props[codigo]

        # Buscar propiedad en Odoo
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

        # Preparar campos a actualizar
        vals = self.map_api_to_odoo(api_prop)

        # UBICACIÓN
        ciudad = api_prop.get('Ciudad')
        barrio = api_prop.get('Barrio')

        if ciudad:
            state_id = self.find_or_create_state(ciudad)
            if state_id:
                vals['state_id'] = state_id
                self.stats['with_state'] += 1

                city_id = self.find_or_create_city(ciudad, state_id)
                if city_id:
                    vals['city_id'] = city_id
                    self.stats['with_city'] += 1

                    if barrio:
                        region_id = self.find_or_create_region(barrio, city_id)
                        if region_id:
                            vals['region_id'] = region_id
                            self.stats['with_region'] += 1

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
        print("ACTUALIZACION MASIVA")
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
                print("\nNo se encontraron propiedades en ese rango")
                return

            # Leer códigos
            props = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'product.template', 'read',
                [prop_ids], {'fields': ['default_code']}
            )

            print(f"\nEncontradas: {len(props)} propiedades")
            self.stats['total'] = len(props)

            # Actualizar cada una
            for idx, prop in enumerate(props, 1):
                print(f"[{idx}/{len(props)}]", end="")
                self.update_property(prop['default_code'], prop, api_props)

        except Exception as e:
            print(f"ERROR: {e}")
            return

        # Reporte
        print("\n" + "="*80)
        print("REPORTE FINAL")
        print("="*80)
        print(f"   Total procesadas: {self.stats['total']}")
        print(f"   ACTUALIZADAS: {self.stats['updated']}")
        print(f"   No en API: {self.stats['not_found']}")
        print(f"   Errores: {self.stats['errors']}")

        if self.stats['updated'] > 0:
            avg = self.stats['total_fields'] / self.stats['updated']
            print(f"\n   Promedio campos agregados: {avg:.1f}")
            print(f"   Con departamento: {self.stats['with_state']}")
            print(f"   Con ciudad: {self.stats['with_city']}")
            print(f"   Con region: {self.stats['with_region']}")

            print(f"\n   Top 10 campos agregados:")
            for field, count in sorted(self.stats['fields_added'].items(),
                                      key=lambda x: x[1], reverse=True)[:10]:
                print(f"      {field}: {count}")

        print("="*80)
        self._save_cache()


def main():
    import sys

    if len(sys.argv) < 3:
        print("\nUSO: python update_properties_from_api.py [id_inicio] [id_fin]")
        print("\nEJEMPLOS:")
        print("   python update_properties_from_api.py 2365 2584")
        print("   python update_properties_from_api.py 2373 2400")
        return

    try:
        start_id = int(sys.argv[1])
        end_id = int(sys.argv[2])
    except:
        print("ERROR: IDs deben ser números")
        return

    updater = PropertyUpdater()
    updater.update_from_range(start_id, end_id)


if __name__ == "__main__":
    main()

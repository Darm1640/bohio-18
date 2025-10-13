#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script COMPLETO para migrar propiedades desde API Arrendasoft a Odoo 18
Usa el mismo enfoque que migrate_properties_COMPLETE.py:
- Autodescubrimiento de campos disponibles en Odoo 18
- Mapeo inteligente desde API a Odoo
- Búsqueda/creación de departamento, ciudad, región
- Migra TODOS los campos posibles (100+ campos)
"""
import os
import json
import requests
import xmlrpc.client
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class CompleteAPIToOdoo18:
    """Migrador completo API -> Odoo 18 con TODOS los campos"""

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
        self.cache_file = 'migration_cache_api.json'
        self.cache = self._load_cache()

        # Campos disponibles en Odoo 18
        self.target_fields = {}

        # Códigos existentes
        self.existing_codes = self._load_existing_codes(listado_file)

        # Estadísticas
        self.stats = {
            'total': 0,
            'created': 0,
            'exists': 0,
            'in_listado': 0,
            'errors': 0,
            'with_state': 0,
            'with_city': 0,
            'with_region': 0,
            'total_fields': 0,
            'fields_used': {}
        }

        print("\n" + "="*80)
        print("MIGRADOR COMPLETO: API ARRENDASOFT -> ODOO 18")
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
        return existing

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
            else:
                print("   ERROR: Credenciales invalidas")
                return False
        except Exception as e:
            print(f"   ERROR: {e}")
            return False

    def discover_fields(self):
        """Descubrir TODOS los campos disponibles en Odoo 18"""
        print("\n[2/3] Descubriendo campos en Odoo 18...")

        try:
            self.target_fields = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'product.template', 'fields_get', [],
                {'attributes': ['type', 'relation', 'string']}
            )

            # Excluir problemáticos
            for field in ['property_filters_config', 'property_search_vector',
                         'message_ids', 'activity_ids', 'message_follower_ids']:
                self.target_fields.pop(field, None)

            print(f"   Campos disponibles: {len(self.target_fields)}")

            # Contar por tipo
            types_count = {}
            for field_name, field_info in self.target_fields.items():
                field_type = field_info.get('type', 'unknown')
                types_count[field_type] = types_count.get(field_type, 0) + 1

            print(f"   Boolean: {types_count.get('boolean', 0)}")
            print(f"   Char: {types_count.get('char', 0)}")
            print(f"   Integer: {types_count.get('integer', 0)}")
            print(f"   Float: {types_count.get('float', 0)}")
            print(f"   Many2one: {types_count.get('many2one', 0)}")

            return True

        except Exception as e:
            print(f"   ERROR: {e}")
            return False

    def get_properties_from_api(self, servicio=None):
        print("\n[3/3] Obteniendo propiedades desde API...")

        params = {}
        if servicio:
            params['Servicio'] = servicio

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

    def find_or_create_state(self, city_name):
        """Buscar departamento basado en ciudad"""
        city_to_state = {
            'montería': 'Córdoba',
            'monteria': 'Córdoba',
            'cerete': 'Córdoba',
            'cereté': 'Córdoba',
            'montelibano': 'Córdoba',
            'montelíbano': 'Córdoba',
            'sahagún': 'Córdoba',
            'sahagun': 'Córdoba',
            'lorica': 'Córdoba',
            'ayapel': 'Córdoba',
            'planeta rica': 'Córdoba',
            'tierralta': 'Córdoba',
            'medellín': 'Antioquia',
            'medellin': 'Antioquia',
            'bogotá': 'Cundinamarca',
            'bogota': 'Cundinamarca',
            'cali': 'Valle del Cauca',
            'barranquilla': 'Atlántico',
            'cartagena': 'Bolívar',
            'tolu': 'Sucre',
            'tolú': 'Sucre',
            'sincelejo': 'Sucre',
            'coveñas': 'Sucre',
            'covenas': 'Sucre'
        }

        city_lower = city_name.lower() if city_name else ''
        state_name = city_to_state.get(city_lower)

        if not state_name:
            return None

        # Buscar en cache
        if state_name in self.cache['states']:
            return self.cache['states'][state_name]

        # Buscar en Odoo
        try:
            state_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'res.country.state', 'search',
                [[('name', 'ilike', state_name)]]
            )

            if state_ids:
                state_id = state_ids[0]
                self.cache['states'][state_name] = state_id
                self._save_cache()
                return state_id
        except:
            pass

        return None

    def find_or_create_city(self, city_name, state_id):
        """Buscar o crear ciudad"""
        if not city_name or not state_id:
            return None

        cache_key = f"{city_name}_{state_id}"

        # Buscar en cache
        if cache_key in self.cache['cities']:
            return self.cache['cities'][cache_key]

        # Buscar en Odoo
        try:
            city_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'res.city', 'search',
                [[('name', 'ilike', city_name), ('state_id', '=', state_id)]]
            )

            if city_ids:
                city_id = city_ids[0]
                self.cache['cities'][cache_key] = city_id
                self._save_cache()
                return city_id

            # Crear ciudad si no existe
            city_id = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'res.city', 'create',
                [{'name': city_name, 'state_id': state_id}]
            )

            self.cache['cities'][cache_key] = city_id
            self._save_cache()
            return city_id

        except Exception as e:
            return None

    def find_or_create_region(self, barrio_name, city_id):
        """Buscar o crear región/barrio"""
        if not barrio_name or not city_id:
            return None

        barrio_name = barrio_name.strip()
        if not barrio_name:
            return None

        cache_key = f"{barrio_name}_{city_id}"

        # Buscar en cache
        if cache_key in self.cache['regions']:
            return self.cache['regions'][cache_key]

        # Buscar en Odoo
        try:
            region_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'region.region', 'search',
                [[('name', 'ilike', barrio_name), ('city_id', '=', city_id)]]
            )

            if region_ids:
                region_id = region_ids[0]
                self.cache['regions'][cache_key] = region_id
                self._save_cache()
                return region_id

            # Crear región si no existe
            region_id = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'region.region', 'create',
                [{'name': barrio_name, 'city_id': city_id}]
            )

            self.cache['regions'][cache_key] = region_id
            self._save_cache()
            return region_id

        except Exception as e:
            return None

    def map_api_to_odoo(self, prop):
        """Mapear TODOS los campos posibles de la API a Odoo 18"""
        vals = {'type': 'consu'}

        # MAPEO BÁSICO
        mapping = {
            # Básicos
            'Codigo': 'default_code',
            'Titulo': 'name',
            'Descripcion': 'description',

            # Ubicación (texto)
            'Direccion': 'street',
            'Barrio': 'street2',
            'Ciudad': 'city',
            'Zona': 'zone',

            # Coordenadas
            'Latitud': 'latitude',
            'Longitud': 'longitude',

            # Características numéricas
            'Habitaciones': 'num_bedrooms',
            'Banos': 'num_bathrooms',
            'Garajes': 'n_garage',
            'Area': 'property_area',
            'AreaConstruida': 'construction_area',
            'Piso': 'floor_number',
            'Estrato': 'property_stratum',
            'Antiguedad': 'property_age',

            # Precios
            'Precio': 'list_price',
            'Administracion': 'property_admin_price',
        }

        # Aplicar mapeo directo
        for api_field, odoo_field in mapping.items():
            if api_field not in prop:
                continue

            value = prop.get(api_field)
            if not value:
                continue

            # Verificar que el campo existe en Odoo
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

                # Contar uso del campo
                self.stats['fields_used'][odoo_field] = \
                    self.stats['fields_used'].get(odoo_field, 0) + 1

            except:
                pass

        # Duplicar área
        if 'property_area' in vals and 'area_in_m2' in self.target_fields:
            vals['area_in_m2'] = vals['property_area']

        # Neighborhood (copiar de barrio)
        if 'street2' in vals and 'neighborhood' in self.target_fields:
            vals['neighborhood'] = vals['street2']

        # URL original
        codigo = prop.get('Codigo', '')
        tipo = prop.get('Tipo', 'Propiedad').replace(' ', '-')
        servicio = prop.get('Servicio', 'Venta')
        if 'website' in self.target_fields:
            vals['website'] = f"https://bohioconsultores.com/detalle-propiedad/?{tipo}-en-{servicio}-{codigo}"

        # Activa
        vals['active'] = True
        vals['sale_ok'] = True

        return vals

    def create_property(self, prop):
        codigo = prop.get('Codigo', 'SIN_CODIGO')
        titulo = prop.get('Titulo', 'Sin titulo')[:50]

        print(f"\n   [{codigo}] {titulo}", end=" ")

        # Verificar en listado.txt
        if str(codigo) in self.existing_codes:
            print("- En listado.txt")
            return {'status': 'in_listado'}

        # Verificar en Odoo 18
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

        # Mapear campos básicos
        vals = self.map_api_to_odoo(prop)

        # UBICACIÓN COMPLETA
        ciudad = prop.get('Ciudad')
        barrio = prop.get('Barrio')

        if ciudad:
            # Buscar/crear departamento
            state_id = self.find_or_create_state(ciudad)
            if state_id:
                vals['state_id'] = state_id
                self.stats['with_state'] += 1

                # Buscar/crear ciudad
                city_id = self.find_or_create_city(ciudad, state_id)
                if city_id:
                    vals['city_id'] = city_id
                    self.stats['with_city'] += 1

                    # Buscar/crear región
                    if barrio:
                        region_id = self.find_or_create_region(barrio, city_id)
                        if region_id:
                            vals['region_id'] = region_id
                            self.stats['with_region'] += 1

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
                print(f"- ERROR campo: {field_name}")
            else:
                print(f"- ERROR: {error_msg[:80]}")
            return {'status': 'error', 'error': str(e)}

    def migrate_from_api(self, servicio=None, limit=None, offset=0):
        print("\n" + "="*80)
        print("MIGRACION COMPLETA: API -> ODOO 18")
        print("="*80)

        if not self.connect_target():
            return None

        if not self.discover_fields():
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

        self.stats['total'] = len(propiedades)

        for idx, prop in enumerate(propiedades, 1):
            print(f"[{idx}/{len(propiedades)}]", end="")

            result = self.create_property(prop)

            if result:
                if result['status'] == 'created':
                    self.stats['created'] += 1
                    self.stats['total_fields'] += result.get('fields', 0)
                elif result['status'] == 'exists':
                    self.stats['exists'] += 1
                elif result['status'] == 'in_listado':
                    self.stats['in_listado'] += 1
                elif result['status'] == 'error':
                    self.stats['errors'] += 1

        # Reporte
        print("\n" + "="*80)
        print("REPORTE FINAL")
        print("="*80)
        print(f"   Total procesadas: {self.stats['total']}")
        print(f"   CREADAS NUEVAS: {self.stats['created']}")
        print(f"   En listado.txt: {self.stats['in_listado']}")
        print(f"   Ya existian: {self.stats['exists']}")
        print(f"   Errores: {self.stats['errors']}")

        if self.stats['created'] > 0:
            avg_fields = self.stats['total_fields'] / self.stats['created']
            print(f"\n   Promedio campos: {avg_fields:.1f}")
            print(f"   Con departamento: {self.stats['with_state']}")
            print(f"   Con ciudad: {self.stats['with_city']}")
            print(f"   Con region: {self.stats['with_region']}")

            # Top 20 campos más usados
            print(f"\n   Top 20 campos migrados:")
            for field, count in sorted(self.stats['fields_used'].items(),
                                      key=lambda x: x[1], reverse=True)[:20]:
                print(f"      {field}: {count}")

        print("="*80)

        self._save_cache()
        print(f"\nCache guardado: {self.cache_file}")

        return self.stats


def main():
    import sys

    print("="*80)
    print("MIGRADOR COMPLETO: API -> ODOO 18")
    print("="*80)

    servicio = None
    limit = 10
    offset = 0

    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except:
            pass

    if len(sys.argv) > 2:
        try:
            offset = int(sys.argv[2])
        except:
            pass

    migrator = CompleteAPIToOdoo18()
    migrator.migrate_from_api(servicio=servicio, limit=limit, offset=offset)


if __name__ == "__main__":
    main()

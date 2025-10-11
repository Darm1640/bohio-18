#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script COMPLETO para migrar propiedades de Odoo 17 → Odoo 18
- Incluye propietario principal (billing_address_id)
- Busca región siempre (esté vacía o llena)
- Incluye TODOS los campos bool y char adicionales
- Migra: city (texto), street2, neighborhood (texto)
"""
import xmlrpc.client
import sys
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuración
ODOO17 = {
    'name': 'Odoo 17 - CloudPepper',
    'url': 'https://inmobiliariabohio.cloudpepper.site',
    'db': 'inmobiliariabohio.cloudpepper.site',
    'username': 'admin',
    'password': 'admin'
}

ODOO18 = {
    'name': 'Odoo 18 - Odoo.com',
    'url': 'https://darm1640-bohio-18.odoo.com',
    'db': 'darm1640-bohio-18-main-24081960',
    'username': 'admin',
    'password': '123456'
}


class CompletePropertyMigrator:
    """Migrador completo con propietarios y todos los campos"""

    def __init__(self, source_config, target_config):
        self.source = source_config
        self.target = target_config
        self.source_uid = None
        self.target_uid = None
        self.source_models = None
        self.target_models = None
        self.source_fields = {}
        self.target_fields = {}
        self.common_fields = []

        # Cache
        self.cache = {
            'states': {},
            'cities': {},
            'regions': {},
            'partners': {},  # NUEVO: Cache de propietarios
        }

        # Stats
        self.stats = {
            'total': 0,
            'migrated': 0,
            'existing': 0,
            'failed': 0,
            'with_owner': 0,  # NUEVO
            'with_region': 0,  # NUEVO
            'fields_migrated': {},
        }

    def connect_source(self):
        try:
            print(f"\nConectando a ORIGEN...")
            common = xmlrpc.client.ServerProxy(f"{self.source['url']}/xmlrpc/2/common")
            self.source_uid = common.authenticate(
                self.source['db'], self.source['username'], self.source['password'], {}
            )
            if not self.source_uid:
                return False
            print(f"   OK (UID: {self.source_uid})")
            self.source_models = xmlrpc.client.ServerProxy(f"{self.source['url']}/xmlrpc/2/object")
            return True
        except Exception as e:
            print(f"   Error: {e}")
            return False

    def connect_target(self):
        try:
            print(f"Conectando a DESTINO...")
            common = xmlrpc.client.ServerProxy(f"{self.target['url']}/xmlrpc/2/common")
            self.target_uid = common.authenticate(
                self.target['db'], self.target['username'], self.target['password'], {}
            )
            if not self.target_uid:
                return False
            print(f"   OK (UID: {self.target_uid})")
            self.target_models = xmlrpc.client.ServerProxy(f"{self.target['url']}/xmlrpc/2/object")
            return True
        except Exception as e:
            print(f"   Error: {e}")
            return False

    def discover_fields(self):
        print("\nDescubriendo campos...")

        # Origen
        self.source_fields = self.source_models.execute_kw(
            self.source['db'], self.source_uid, self.source['password'],
            'product.template', 'fields_get', [], {'attributes': ['type', 'relation']}
        )

        # Destino
        self.target_fields = self.target_models.execute_kw(
            self.target['db'], self.target_uid, self.target['password'],
            'product.template', 'fields_get', [], {'attributes': ['type', 'relation']}
        )

        # Excluir problemáticos
        for field in ['property_filters_config', 'property_search_vector', 'message_ids',
                     'activity_ids', 'message_follower_ids', 'website_message_ids']:
            self.source_fields.pop(field, None)
            self.target_fields.pop(field, None)

        # Campos comunes
        property_keywords = [
            'property', 'bedroom', 'bathroom', 'garage', 'area', 'floor', 'unit',
            'price', 'rent', 'rental', 'sale', 'type', 'status', 'state', 'city',
            'region', 'neighborhood', 'street', 'latitude', 'longitude', 'zip',
            'auxiliary', 'service', 'laundry', 'green', 'sports', 'solar', 'marble',
            'door', 'building', 'apartment', 'project', 'notarial', 'tax',
            'consignee', 'date', 'description', 'front', 'electrical', 'keys',
            'license', 'real_estate', 'sign', 'billing', 'security', 'dining',
            'poster', 'truck', 'solarium', 'room'  # Campos adicionales
        ]

        for field_name in self.source_fields:
            if field_name in self.target_fields:
                # Incluir básicos
                if field_name in ['name', 'default_code', 'active', 'is_property',
                                 'description', 'description_sale', 'type']:
                    self.common_fields.append((field_name, field_name))
                    continue

                # Incluir si coincide con keywords
                field_lower = field_name.lower()
                if any(kw in field_lower for kw in property_keywords):
                    self.common_fields.append((field_name, field_name))

        print(f"   Campos comunes: {len(self.common_fields)}")

        # Contar booleanos
        bools = [f for f, _ in self.common_fields
                if self.source_fields[f].get('type') == 'boolean']
        print(f"   Booleanos: {len(bools)}")

    def clean_state_name(self, state_data):
        if not state_data:
            return None
        state_name = state_data[1] if isinstance(state_data, (list, tuple)) else state_data
        if '(' in state_name:
            state_name = state_name.split('(')[0].strip()
        if state_name.endswith(' CO'):
            state_name = state_name[:-3].strip()
        return state_name

    def clean_city_name(self, city_data):
        if not city_data:
            return None
        city_name = city_data[1] if isinstance(city_data, (list, tuple)) else city_data
        if '(' in city_name:
            city_name = city_name.split('(')[0].strip()
        return city_name

    def get_or_create_state(self, state_data):
        state_name = self.clean_state_name(state_data)
        if not state_name:
            return None
        if state_name in self.cache['states']:
            return self.cache['states'][state_name]

        try:
            state_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'res.country.state', 'search', [[('name', 'ilike', state_name)]]
            )
            if state_ids:
                self.cache['states'][state_name] = state_ids[0]
                return state_ids[0]
        except:
            pass
        return None

    def get_or_create_city(self, city_data, state_id):
        city_name = self.clean_city_name(city_data)
        if not city_name or not state_id:
            return None
        cache_key = f"{city_name}_{state_id}"
        if cache_key in self.cache['cities']:
            return self.cache['cities'][cache_key]

        try:
            city_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'res.city', 'search', [[('name', 'ilike', city_name), ('state_id', '=', state_id)]]
            )
            if city_ids:
                self.cache['cities'][cache_key] = city_ids[0]
                return city_ids[0]
        except:
            pass
        return None

    def get_or_create_region(self, region_data, city_text=None, neighborhood_text=None, street2_text=None):
        """
        Buscar región SIEMPRE (esté llena o vacía)
        Prioridad:
        1. region_id si existe
        2. street2 (frecuentemente contiene barrio: "El Centro", "Santa Bárbara")
        3. neighborhood (campo texto barrio)
        """
        # 1. Si hay region_id con valor
        if region_data and region_data is not False:
            if isinstance(region_data, (list, tuple)):
                region_id = region_data[0]
                region_name = region_data[1]
            else:
                return None

            if region_id in self.cache['regions']:
                return self.cache['regions'][region_id]

            try:
                target_region_ids = self.target_models.execute_kw(
                    self.target['db'], self.target_uid, self.target['password'],
                    'region.region', 'search', [[('name', 'ilike', region_name)]]
                )
                if target_region_ids:
                    self.cache['regions'][region_id] = target_region_ids[0]
                    return target_region_ids[0]

                # Crear si no existe
                try:
                    new_id = self.target_models.execute_kw(
                        self.target['db'], self.target_uid, self.target['password'],
                        'region.region', 'create', [{'name': region_name}]
                    )
                    self.cache['regions'][region_id] = new_id
                    return new_id
                except:
                    pass
            except:
                pass

        # 2. Si region_id vacía, buscar por street2 (PRIORIDAD ALTA)
        # street2 frecuentemente tiene barrio: "El Centro", "Santa Bárbara", "Floresta"
        if not region_data and street2_text and street2_text.strip():
            cache_key = f"street2_{street2_text}"
            if cache_key in self.cache['regions']:
                return self.cache['regions'][cache_key]

            try:
                target_region_ids = self.target_models.execute_kw(
                    self.target['db'], self.target_uid, self.target['password'],
                    'region.region', 'search', [[('name', 'ilike', street2_text)]]
                )
                if target_region_ids:
                    self.cache['regions'][cache_key] = target_region_ids[0]
                    return target_region_ids[0]

                # Crear región con nombre de street2
                try:
                    new_id = self.target_models.execute_kw(
                        self.target['db'], self.target_uid, self.target['password'],
                        'region.region', 'create', [{'name': street2_text}]
                    )
                    self.cache['regions'][cache_key] = new_id
                    return new_id
                except:
                    pass
            except:
                pass

        # 3. Si no hay street2, intentar con neighborhood
        if not region_data and not street2_text and neighborhood_text and neighborhood_text.strip():
            cache_key = f"neighborhood_{neighborhood_text}"
            if cache_key in self.cache['regions']:
                return self.cache['regions'][cache_key]

            try:
                target_region_ids = self.target_models.execute_kw(
                    self.target['db'], self.target_uid, self.target['password'],
                    'region.region', 'search', [[('name', 'ilike', neighborhood_text)]]
                )
                if target_region_ids:
                    self.cache['regions'][cache_key] = target_region_ids[0]
                    return target_region_ids[0]

                # Crear región con nombre del barrio
                try:
                    new_id = self.target_models.execute_kw(
                        self.target['db'], self.target_uid, self.target['password'],
                        'region.region', 'create', [{'name': neighborhood_text}]
                    )
                    self.cache['regions'][cache_key] = new_id
                    return new_id
                except:
                    pass
            except:
                pass

        return None

    def get_or_find_partner(self, partner_id):
        """
        Buscar propietario en destino por datos de dirección
        NO crear automáticamente, solo encontrar si existe
        """
        if not partner_id or partner_id is False:
            return None

        # Extraer ID
        if isinstance(partner_id, (list, tuple)):
            partner_id = partner_id[0]

        # Cache
        if partner_id in self.cache['partners']:
            return self.cache['partners'][partner_id]

        try:
            # Leer datos del partner en origen
            partner_data = self.source_models.execute_kw(
                self.source['db'], self.source_uid, self.source['password'],
                'res.partner', 'read', [[partner_id]],
                {'fields': ['name', 'vat', 'email', 'phone', 'mobile', 'street']}
            )

            if not partner_data:
                return None

            partner_info = partner_data[0]

            # Buscar en destino por VAT (documento)
            if partner_info.get('vat'):
                existing_ids = self.target_models.execute_kw(
                    self.target['db'], self.target_uid, self.target['password'],
                    'res.partner', 'search', [[('vat', '=', partner_info['vat'])]]
                )
                if existing_ids:
                    self.cache['partners'][partner_id] = existing_ids[0]
                    return existing_ids[0]

            # Buscar por email
            if partner_info.get('email'):
                existing_ids = self.target_models.execute_kw(
                    self.target['db'], self.target_uid, self.target['password'],
                    'res.partner', 'search', [[('email', '=', partner_info['email'])]]
                )
                if existing_ids:
                    self.cache['partners'][partner_id] = existing_ids[0]
                    return existing_ids[0]

            # Buscar por nombre + dirección
            if partner_info.get('name') and partner_info.get('street'):
                existing_ids = self.target_models.execute_kw(
                    self.target['db'], self.target_uid, self.target['password'],
                    'res.partner', 'search',
                    [[('name', '=', partner_info['name']), ('street', '=', partner_info['street'])]]
                )
                if existing_ids:
                    self.cache['partners'][partner_id] = existing_ids[0]
                    return existing_ids[0]

        except Exception as e:
            pass

        return None

    def migrate_property(self, property_code):
        print(f"[{property_code}]", end=" ")

        # 1. Buscar
        try:
            for domain in [[('default_code', '=', property_code)],
                          [('default_code', '=', f'BOH-{property_code}')],
                          [('id', '=', int(property_code))] if property_code.isdigit() else []]:
                if not domain:
                    continue
                property_ids = self.source_models.execute_kw(
                    self.source['db'], self.source_uid, self.source['password'],
                    'product.template', 'search', [domain]
                )
                if property_ids:
                    break

            if not property_ids:
                print("No encontrada")
                return None

            property_id = property_ids[0]
        except Exception as e:
            print(f"Error buscando")
            return None

        # 2. Leer todos los campos
        fields_to_read = [source for source, target in self.common_fields]

        try:
            property_data = self.source_models.execute_kw(
                self.source['db'], self.source_uid, self.source['password'],
                'product.template', 'read', [[property_id]], {'fields': fields_to_read}
            )[0]

            print(f"{property_data.get('name', 'N/A')[:25]}", end=" ")
        except Exception as e:
            print(f"Error leyendo")
            return None

        # 3. Verificar si existe
        try:
            existing_ids = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'product.template', 'search',
                [[('default_code', '=', property_data.get('default_code'))]]
            )
            if existing_ids:
                print(f"- Ya existe ({existing_ids[0]})")
                return existing_ids[0]
        except:
            pass

        # 4. Preparar datos
        vals = {'type': 'consu'}

        # UBICACIÓN
        if property_data.get('state_id'):
            target_state_id = self.get_or_create_state(property_data['state_id'])
            if target_state_id:
                vals['state_id'] = target_state_id

                if property_data.get('city_id'):
                    target_city_id = self.get_or_create_city(
                        property_data['city_id'], target_state_id
                    )
                    if target_city_id:
                        vals['city_id'] = target_city_id

        # REGIÓN - Buscar SIEMPRE (con o sin valor)
        # Prioridad: region_id > street2 > neighborhood > city
        city_text = property_data.get('city')  # Texto de ciudad
        neighborhood_text = property_data.get('neighborhood')  # Texto de barrio
        street2_text = property_data.get('street2')  # Dirección secundaria (frecuentemente barrio)

        region_id = self.get_or_create_region(
            property_data.get('region_id'),
            city_text,
            neighborhood_text,
            street2_text  # NUEVO: Pasar street2 para búsqueda
        )
        if region_id:
            vals['region_id'] = region_id
            self.stats['with_region'] += 1

        # PROPIETARIO - Buscar si existe
        if property_data.get('billing_address_id'):
            owner_id = self.get_or_find_partner(property_data['billing_address_id'])
            if owner_id:
                vals['billing_address_id'] = owner_id
                self.stats['with_owner'] += 1

        # TODOS LOS DEMÁS CAMPOS
        for source_field, target_field in self.common_fields:
            if source_field in ['state_id', 'city_id', 'region_id', 'billing_address_id']:
                continue

            if source_field not in property_data:
                continue

            value = property_data.get(source_field)
            if value is None:
                continue

            # Many2one: solo ID
            if isinstance(value, (list, tuple)) and len(value) == 2:
                value = value[0]

            # Asignar según tipo
            field_type = self.source_fields[source_field].get('type')
            if field_type == 'boolean':
                vals[target_field] = value
            elif value not in [False, '', 0, 0.0]:
                vals[target_field] = value

            if target_field in vals:
                self.stats['fields_migrated'][target_field] = \
                    self.stats['fields_migrated'].get(target_field, 0) + 1

        # 5. Crear
        try:
            new_id = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'product.template', 'create', [vals]
            )
            print(f"- OK ({new_id}, {len(vals)} campos)")
            return new_id
        except Exception as e:
            error_msg = str(e)
            if 'ValueError' in error_msg:
                start = error_msg.find('ValueError:')
                if start > 0:
                    end = error_msg.find('\\n', start)
                    err = error_msg[start:end] if end > 0 else error_msg[start:start+100]
                    print(f"- ERROR: {err}")
                else:
                    print(f"- ERROR: {error_msg[:100]}")
            else:
                print(f"- ERROR: {error_msg[:100]}")
            return None

    def migrate_from_list(self, list_file="property_images/listado.txt", limit=10):
        self.migrate_from_list_with_offset(list_file, limit, 0)

    def migrate_from_list_with_offset(self, list_file="property_images/listado.txt", limit=10, offset=0):
        print("\n" + "="*80)
        print("MIGRACIÓN COMPLETA CON PROPIETARIOS Y REGIONES")
        print("="*80)

        try:
            with open(list_file, 'r', encoding='utf-8') as f:
                codes = [line.strip() for line in f
                        if line.strip() and line.strip() != 'default_code']
            print(f"\nDisponibles: {len(codes)} | Desde: {offset} | Procesando: {limit}")
        except FileNotFoundError:
            print(f"Archivo no encontrado: {list_file}")
            return

        # Tomar desde offset
        codes_to_process = codes[offset:offset+limit]
        self.stats['total'] = len(codes_to_process)

        for idx, code in enumerate(codes_to_process, 1):
            print(f"{idx}/{limit} ", end="")
            result = self.migrate_property(code)

            if result and result > 0:
                self.stats['migrated'] += 1
            elif result:
                self.stats['existing'] += 1
            else:
                self.stats['failed'] += 1

        # Reporte
        print("\n" + "="*80)
        print("REPORTE")
        print("="*80)
        print(f"Total:         {self.stats['total']}")
        print(f"Migradas:      {self.stats['migrated']}")
        print(f"Existentes:    {self.stats['existing']}")
        print(f"Fallidas:      {self.stats['failed']}")
        print(f"Con propietario: {self.stats['with_owner']}")
        print(f"Con región:     {self.stats['with_region']}")

        print(f"\nTop 30 campos:")
        for field, count in sorted(self.stats['fields_migrated'].items(),
                                   key=lambda x: x[1], reverse=True)[:30]:
            print(f"   {field}: {count}")

        with open('migration_cache.json', 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
        print("\nCache: migration_cache.json")


def main():
    print("="*80)
    print("MIGRACIÓN COMPLETA: ODOO 17 → ODOO 18")
    print("Incluye: Propietarios, Regiones, Todos los Bool/Char")
    print("="*80)

    migrator = CompletePropertyMigrator(ODOO17, ODOO18)

    if not migrator.connect_source() or not migrator.connect_target():
        print("\nError de conexión")
        return

    migrator.discover_fields()
    # Probar con las siguientes 10 propiedades (desde posición 20)
    migrator.migrate_from_list_with_offset(limit=10, offset=20)


if __name__ == "__main__":
    main()

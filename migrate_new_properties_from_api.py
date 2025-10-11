#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para migrar propiedades NUEVAS desde API de Arrendasoft a Odoo 18
No usa CloudPepper - trae datos directamente de la API y los crea en Odoo 18
"""
import os
import sys
import json
import requests
import xmlrpc.client
from datetime import datetime


class ArrendasoftToOdoo18Migrator:
    """Migra propiedades desde API Arrendasoft a Odoo 18"""

    def __init__(self, listado_file='listado.txt'):
        # API Arrendasoft
        self.api_url = "https://bohio.arrendasoft.co/service/v2/public/map-of-properties/data"

        # Odoo 18 Target (Odoo.com)
        self.target = {
            'url': 'https://darm1640-bohio-18.odoo.com',
            'db': 'darm1640-bohio-18-main-24081960',
            'username': 'admin',
            'password': '123456'
        }

        # Cache para evitar búsquedas repetidas
        self.cache_file = 'migration_cache_new.json'
        self.cache = self._load_cache()

        # Cargar códigos existentes desde listado.txt
        self.existing_codes = self._load_existing_codes(listado_file)

        # Conectar a Odoo 18
        self.target_common = xmlrpc.client.ServerProxy(f"{self.target['url']}/xmlrpc/2/common")
        self.target_models = xmlrpc.client.ServerProxy(f"{self.target['url']}/xmlrpc/2/object")
        self.target_uid = None

        print("\n" + "="*80)
        print("MIGRADOR: API ARRENDASOFT -> ODOO 18")
        print("="*80)

    def _load_cache(self):
        """Cargar cache desde archivo"""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'states': {}, 'cities': {}, 'regions': {}, 'partners': {}}

    def _load_existing_codes(self, listado_file):
        """Cargar códigos de propiedades existentes desde listado.txt"""
        existing = set()
        if os.path.exists(listado_file):
            with open(listado_file, 'r', encoding='utf-8') as f:
                for line in f:
                    code = line.strip()
                    if code:
                        existing.add(code)
            print(f"\nCodigos existentes en {listado_file}: {len(existing)}")
        else:
            print(f"\nArchivo {listado_file} no encontrado - procesara TODAS las propiedades")
        return existing

    def _save_cache(self):
        """Guardar cache a archivo"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)

    def connect_target(self):
        """Conectar a Odoo 18"""
        print("\n[1/2] Conectando a Odoo 18...")
        try:
            self.target_uid = self.target_common.authenticate(
                self.target['db'],
                self.target['username'],
                self.target['password'],
                {}
            )
            if self.target_uid:
                print(f"OK Conectado a Odoo 18 (UID: {self.target_uid})")
                return True
            else:
                print("ERROR: Credenciales invalidas")
                return False
        except Exception as e:
            print(f"ERROR de conexion: {e}")
            return False

    def get_properties_from_api(self, servicio=None):
        """
        Obtener propiedades desde API de Arrendasoft
        servicio: None=Todas, 1=Arriendo, 2=Venta
        """
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
                print(f"OK {len(propiedades)} propiedades obtenidas")
                return propiedades
            else:
                print(f"ERROR Formato de respuesta inesperado")
                return []

        except Exception as e:
            print(f"ERROR obteniendo propiedades: {e}")
            return []

    def map_arrendasoft_to_odoo(self, prop):
        """
        Mapear TODOS los datos de Arrendasoft a campos de Odoo 18
        """
        vals = {}

        # BÁSICOS
        codigo = prop.get('Codigo', '')
        vals['default_code'] = str(codigo)  # Código único
        vals['name'] = prop.get('Titulo', f'Propiedad {codigo}')
        vals['description'] = prop.get('Descripcion', '')

        # PRECIOS
        precio = prop.get('Precio')
        if precio:
            try:
                vals['list_price'] = float(precio)
            except:
                vals['list_price'] = 0.0

        # Precio de administración
        admin = prop.get('Administracion')
        if admin:
            try:
                vals['property_admin_price'] = float(admin)
            except:
                pass

        # UBICACIÓN (desde API)
        direccion = prop.get('Direccion', '')
        ciudad = prop.get('Ciudad', '')
        barrio = prop.get('Barrio', '')
        zona = prop.get('Zona', '')

        if direccion:
            vals['street'] = direccion
        if barrio:
            vals['street2'] = barrio  # Barrio en street2
            vals['neighborhood'] = barrio  # También en campo neighborhood
        if ciudad:
            vals['city'] = ciudad
        if zona:
            vals['zone'] = zona

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

        # CARACTERÍSTICAS NUMÉRICAS
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

        # Área construida
        area_construida = prop.get('AreaConstruida')
        if area_construida:
            try:
                vals['construction_area'] = float(area_construida)
            except:
                pass

        # Piso
        piso = prop.get('Piso')
        if piso:
            try:
                vals['floor_number'] = int(piso)
            except:
                pass

        # Estrato
        estrato = prop.get('Estrato')
        if estrato:
            try:
                vals['property_stratum'] = str(estrato)
            except:
                pass

        # Antigüedad
        antiguedad = prop.get('Antiguedad')
        if antiguedad:
            try:
                vals['property_age'] = int(antiguedad)
            except:
                pass

        # TIPO DE SERVICIO
        servicio = prop.get('Servicio', '')
        if servicio:
            if servicio.lower() == 'venta':
                vals['property_for_sale'] = True
                vals['property_for_rent'] = False
            elif servicio.lower() == 'arriendo':
                vals['property_for_rent'] = True
                vals['property_for_sale'] = False

        # TIPO DE PROPIEDAD
        tipo = prop.get('Tipo', '')
        if tipo:
            vals['property_type'] = tipo

        # CARACTERÍSTICAS BOOLEANAS (todas las posibles)
        # Buscar todos los campos boolean en prop
        boolean_mapping = {
            'Amoblado': 'furnished',
            'Amueblado': 'furnished',
            'Garaje': 'garage',
            'Parqueadero': 'garage',
            'Ascensor': 'elevator',
            'Balcon': 'balcony',
            'Terraza': 'terrace',
            'Patio': 'patio',
            'Jardin': 'garden',
            'Piscina': 'pool',
            'ZonaVerde': 'green_area',
            'Vigilancia': 'surveillance',
            'Porteria': 'concierge',
            'SalonComunal': 'communal_hall',
            'Gimnasio': 'gym',
            'Chimenea': 'fireplace',
            'Closets': 'closets',
            'VistaPanoramica': 'panoramic_view',
            'Alarma': 'alarm',
            'ConjuntoCerrado': 'gated_community',
            'ZonaInfantil': 'childrens_area',
            'CuartoServicio': 'service_room',
            'BanoServicio': 'service_bathroom',
            'BanoAuxiliar': 'auxiliary_bathroom',
            'Deposito': 'storage',
            'Sotano': 'basement',
            'Duplex': 'duplex',
            'Penthouse': 'penthouse',
            'Estudios': 'study_room',
            'VistaExterior': 'exterior_view'
        }

        # Intentar mapear todos los campos boolean
        for api_key, odoo_field in boolean_mapping.items():
            if api_key in prop:
                value = prop.get(api_key)
                if isinstance(value, bool):
                    vals[odoo_field] = value
                elif isinstance(value, str):
                    vals[odoo_field] = value.lower() in ['true', 'si', 'yes', '1', 'sí']
                elif isinstance(value, int):
                    vals[odoo_field] = bool(value)

        # ESTADO (Activa por defecto)
        vals['active'] = True
        vals['sale_ok'] = True

        # Estado de la propiedad (nuevo, usado)
        estado = prop.get('Estado', '')
        if estado:
            if 'nuevo' in estado.lower():
                vals['property_condition'] = 'new'
            elif 'usado' in estado.lower():
                vals['property_condition'] = 'used'

        # URL ORIGINAL
        codigo_prop = prop.get('Codigo', '')
        tipo_prop = prop.get('Tipo', 'Propiedad').replace(' ', '-')
        servicio_prop = prop.get('Servicio', 'Venta')
        vals['website'] = f"https://bohioconsultores.com/detalle-propiedad/?{tipo_prop}-en-{servicio_prop}-{codigo_prop}"

        # CAMPOS ADICIONALES (si existen en la API)
        # Referencia externa
        ref_externa = prop.get('ReferenciaExterna', '') or prop.get('Referencia', '')
        if ref_externa:
            vals['property_ref'] = str(ref_externa)

        # Notas internas
        notas = prop.get('Notas', '') or prop.get('NotasInternas', '')
        if notas:
            vals['description_sale'] = notas

        # Característica destacada
        destacado = prop.get('Destacado', '') or prop.get('Featured', '')
        if destacado:
            if isinstance(destacado, bool):
                vals['is_featured'] = destacado
            elif isinstance(destacado, str):
                vals['is_featured'] = destacado.lower() in ['true', 'si', 'yes', '1', 'sí']

        return vals

    def find_or_create_state(self, city_name):
        """Buscar o crear departamento basado en ciudad"""
        # Mapeo manual de ciudades a departamentos conocidos
        city_to_state = {
            'montería': 'Córdoba',
            'monteria': 'Córdoba',
            'medellín': 'Antioquia',
            'medellin': 'Antioquia',
            'bogotá': 'Cundinamarca',
            'bogota': 'Cundinamarca',
            'cali': 'Valle del Cauca',
            'barranquilla': 'Atlántico',
            'cartagena': 'Bolívar'
        }

        city_lower = city_name.lower() if city_name else ''
        state_name = city_to_state.get(city_lower)

        if not state_name:
            return False

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

        return False

    def find_or_create_city(self, city_name, state_id):
        """Buscar o crear ciudad"""
        if not city_name or not state_id:
            return False

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
            print(f"      Creando ciudad: {city_name}")
            city_id = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'res.city', 'create',
                [{'name': city_name, 'state_id': state_id}]
            )

            self.cache['cities'][cache_key] = city_id
            self._save_cache()
            return city_id

        except Exception as e:
            print(f"      Error buscando/creando ciudad: {e}")
            return False

    def find_or_create_region(self, barrio_name, city_id):
        """Buscar o crear región/barrio"""
        if not barrio_name or not city_id:
            return False

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
            print(f"      Creando región: {barrio_name}")
            region_id = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'region.region', 'create',
                [{'name': barrio_name, 'city_id': city_id}]
            )

            self.cache['regions'][cache_key] = region_id
            self._save_cache()
            return region_id

        except Exception as e:
            print(f"      Error buscando/creando región: {e}")
            return False

    def create_property(self, prop_data):
        """Crear propiedad en Odoo 18"""
        codigo = prop_data.get('Codigo', 'SIN_CODIGO')
        titulo = prop_data.get('Titulo', 'Sin título')

        print(f"\n   Procesando: {codigo} - {titulo[:50]}")

        # Verificar si está en listado.txt (ya migrada)
        if str(codigo) in self.existing_codes:
            print(f"      - En listado.txt (ya migrada)")
            return {'status': 'in_listado', 'code': codigo}

        # Verificar si ya existe en Odoo 18
        try:
            existing = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'product.template', 'search',
                [[('default_code', '=', str(codigo))]]
            )

            if existing:
                print(f"      ⊗ Ya existe en Odoo 18 (ID: {existing[0]})")
                return {'status': 'exists', 'id': existing[0]}
        except:
            pass

        # Mapear datos
        vals = self.map_arrendasoft_to_odoo(prop_data)

        # Procesar ubicación
        ciudad = prop_data.get('Ciudad')
        barrio = prop_data.get('Barrio')

        if ciudad:
            # Buscar/crear departamento
            state_id = self.find_or_create_state(ciudad)
            if state_id:
                vals['state_id'] = state_id
                print(f"      ✓ Departamento encontrado")

                # Buscar/crear ciudad
                city_id = self.find_or_create_city(ciudad, state_id)
                if city_id:
                    vals['city_id'] = city_id
                    print(f"      ✓ Ciudad: {ciudad}")

                    # Buscar/crear región
                    if barrio:
                        region_id = self.find_or_create_region(barrio, city_id)
                        if region_id:
                            vals['region_id'] = region_id
                            print(f"      ✓ Región: {barrio}")

        # Crear propiedad
        try:
            new_id = self.target_models.execute_kw(
                self.target['db'], self.target_uid, self.target['password'],
                'product.template', 'create',
                [vals]
            )

            print(f"      ✓ CREADA (ID: {new_id})")
            print(f"      Campos migrados: {len(vals)}")

            return {'status': 'created', 'id': new_id, 'fields': len(vals)}

        except Exception as e:
            print(f"      ERROR: {e}")
            return {'status': 'error', 'error': str(e)}

    def migrate_from_api(self, servicio=None, limit=None, offset=0):
        """
        Proceso completo: API → Odoo 18
        """
        print("\n" + "="*80)
        print("MIGRACION: API ARRENDASOFT -> ODOO 18")
        print("="*80)

        # Conectar
        if not self.connect_target():
            return None

        # Obtener propiedades
        propiedades = self.get_properties_from_api(servicio=servicio)

        if not propiedades:
            print("\n✗ No se encontraron propiedades")
            return None

        # Aplicar límites
        if offset > 0:
            propiedades = propiedades[offset:]
            print(f"\nIniciando desde posición: {offset}")

        if limit:
            propiedades = propiedades[:limit]
            print(f"Limitando a: {limit} propiedades")

        print(f"\n{'='*80}")
        print(f"PROCESANDO {len(propiedades)} PROPIEDADES")
        print(f"{'='*80}")

        # Estadísticas
        stats = {
            'total': len(propiedades),
            'created': 0,
            'exists': 0,
            'in_listado': 0,
            'errors': 0,
            'total_fields': 0,
            'new_properties': []
        }

        # Procesar cada propiedad
        for idx, prop in enumerate(propiedades, 1):
            print(f"\n[{idx}/{len(propiedades)}] {'='*60}")

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

        # Reporte final
        print("\n" + "="*80)
        print("REPORTE FINAL")
        print("="*80)
        print(f"   Total procesadas: {stats['total']}")
        print(f"   OK CREADAS NUEVAS: {stats['created']}")
        print(f"   - En listado.txt (ya migradas): {stats['in_listado']}")
        print(f"   - Ya existian en Odoo 18: {stats['exists']}")
        print(f"   ERROR Errores: {stats['errors']}")

        if stats['created'] > 0:
            avg_fields = stats['total_fields'] / stats['created']
            print(f"   Promedio campos por propiedad: {avg_fields:.1f}")
            print(f"\n   PROPIEDADES NUEVAS CREADAS:")
            for prop in stats['new_properties'][:20]:
                print(f"      {prop['codigo']}: {prop['titulo']} (ID: {prop['id']})")
            if len(stats['new_properties']) > 20:
                print(f"      ... y {len(stats['new_properties']) - 20} mas")

        print("="*80)

        return stats


def main():
    """Función principal"""

    print("="*80)
    print("MIGRADOR: API ARRENDASOFT -> ODOO 18")
    print("="*80)

    # Parámetros configurables
    servicio = None  # None=Todas, 1=Arriendo, 2=Venta
    limit = 10  # Número de propiedades a procesar (None = todas)
    offset = 0  # Índice de inicio

    # Parsear argumentos
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
                print("\nUSO:")
                print("   python migrate_new_properties_from_api.py [tipo] [limit] [offset]")
                print("\nEJEMPLOS:")
                print("   python migrate_new_properties_from_api.py venta")
                print("   python migrate_new_properties_from_api.py venta 20")
                print("   python migrate_new_properties_from_api.py arriendo 10 0")
                print("   python migrate_new_properties_from_api.py todas")
                print("   python migrate_new_properties_from_api.py 50")
                return

    if len(sys.argv) > 2:
        try:
            limit = int(sys.argv[2])
        except:
            pass

    if len(sys.argv) > 3:
        try:
            offset = int(sys.argv[3])
        except:
            pass

    # Crear migrador
    migrator = ArrendasoftToOdoo18Migrator()

    # Migrar
    migrator.migrate_from_api(
        servicio=servicio,
        limit=limit,
        offset=offset
    )


if __name__ == "__main__":
    main()

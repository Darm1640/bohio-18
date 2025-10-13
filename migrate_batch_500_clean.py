#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para SINCRONIZAR BARRIOS desde CloudPepper (Odoo 17) a Odoo.com
- Lee todos los barrios de CloudPepper
- Busca/crea ciudades en Odoo.com
- Crea barrios en Odoo.com asociados a la ciudad correcta
"""
import sys
import io
import json
import requests
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class RegionSyncronizer:
    """Sincronizador de barrios/regiones"""

    def __init__(self):
        # Configuración CloudPepper (Source - Odoo 17)
        self.cp_config = {
            'url': 'https://inmobiliariabohio.cloudpepper.site',
            'db': 'inmobiliariabohio.cloudpepper.site',
            'username': 'admin',
            'password': 'admin'
        }

        # Configuración Odoo.com (Target)
        self.odoo_config = {
            'url': 'https://darm1640-bohio-18.odoo.com',
            'db': 'darm1640-bohio-18-main-24081960',
            'username': 'admin',
            'password': '123456'
        }

        # UIDs
        self.cp_uid = None
        self.odoo_uid = None

        # Cachés
        self.cp_cities = {}           # {city_id: {'code': ..., 'name': ...}}
        self.odoo_cities = {}         # {code: city_id}
        self.odoo_regions = {}        # {(city_id, name): region_id}

    def jsonrpc_call(self, config, uid, model, method, args=None, kwargs=None):
        """Llamada JSON-RPC genérica"""
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    config['db'],
                    uid,
                    config['password'],
                    model,
                    method,
                    args,
                    kwargs
                ]
            },
            "id": 1
        }

        response = requests.post(
            f"{config['url']}/jsonrpc",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=300
        )

        result = response.json()
        if 'error' in result:
            raise Exception(f"JSON-RPC Error: {result['error']}")
        
        return result.get('result')

    def authenticate(self, config):
        """Autenticación JSON-RPC"""
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "authenticate",
                "args": [
                    config['db'],
                    config['username'],
                    config['password'],
                    {}
                ]
            },
            "id": 1
        }

        response = requests.post(
            f"{config['url']}/jsonrpc",
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        result = response.json()
        if 'error' in result:
            raise Exception(f"Authentication Error: {result['error']}")
        
        uid = result.get('result')
        if not uid:
            raise Exception("Authentication failed: No UID returned")
        
        return uid

    def connect_cloudpepper(self):
        """Conecta a CloudPepper"""
        print(f"\n📡 Conectando a CloudPepper (Odoo 17)...")
        self.cp_uid = self.authenticate(self.cp_config)
        print(f"   ✅ Conectado como UID: {self.cp_uid}")

    def connect_odoo(self):
        """Conecta a Odoo.com"""
        print(f"\n📡 Conectando a Odoo.com...")
        self.odoo_uid = self.authenticate(self.odoo_config)
        print(f"   ✅ Conectado como UID: {self.odoo_uid}")

    def load_cloudpepper_cities(self):
        """Carga ciudades de CloudPepper"""
        print("\n🏙️  Cargando ciudades de CloudPepper...")
        
        city_ids = self.jsonrpc_call(
            self.cp_config, self.cp_uid,
            'res.city', 'search',
            args=[[]]
        )
        
        if not city_ids:
            print("   ⚠️  No hay ciudades en CloudPepper")
            return
        
        cities = self.jsonrpc_call(
            self.cp_config, self.cp_uid,
            'res.city', 'read',
            args=[city_ids],
            kwargs={'fields': ['id', 'name', 'code', 'l10n_co_edi_code']}
        )
        
        for city in cities:
            city_id = city['id']
            self.cp_cities[city_id] = {
                'name': city.get('name', '').strip(),
                'code': city.get('code') or city.get('l10n_co_edi_code'),
                'name_lower': city.get('name', '').strip().lower()
            }
        
        print(f"   ✅ {len(cities)} ciudades cargadas de CloudPepper")

    def load_odoo_cities(self):
        """Carga ciudades de Odoo.com"""
        print("\n🏙️  Cargando ciudades de Odoo.com...")
        
        city_ids = self.jsonrpc_call(
            self.odoo_config, self.odoo_uid,
            'res.city', 'search',
            args=[[]]
        )
        
        if not city_ids:
            print("   ⚠️  No hay ciudades en Odoo.com")
            return
        
        cities = self.jsonrpc_call(
            self.odoo_config, self.odoo_uid,
            'res.city', 'read',
            args=[city_ids],
            kwargs={'fields': ['id', 'name', 'code', 'l10n_co_edi_code']}
        )
        
        for city in cities:
            # Indexar por código
            if city.get('code'):
                self.odoo_cities[city['code']] = city['id']
            if city.get('l10n_co_edi_code'):
                self.odoo_cities[city['l10n_co_edi_code']] = city['id']
        
        print(f"   ✅ {len(cities)} ciudades cargadas de Odoo.com")
        print(f"   ✅ {len(self.odoo_cities)} códigos indexados")

    def load_odoo_regions(self):
        """Carga regiones/barrios existentes en Odoo.com"""
        print("\n🏘️  Cargando regiones existentes en Odoo.com...")
        
        region_ids = self.jsonrpc_call(
            self.odoo_config, self.odoo_uid,
            'property.region', 'search',
            args=[[]]
        )
        
        if not region_ids:
            print("   ℹ️  No hay regiones en Odoo.com")
            return
        
        regions = self.jsonrpc_call(
            self.odoo_config, self.odoo_uid,
            'property.region', 'read',
            args=[region_ids],
            kwargs={'fields': ['id', 'name', 'city_id']}
        )
        
        for region in regions:
            region_name = region.get('name', '').strip().lower()
            city_id = None
            
            if region.get('city_id'):
                city_id = region['city_id'][0] if isinstance(region['city_id'], list) else region['city_id']
            
            if region_name and city_id:
                key = (city_id, region_name)
                self.odoo_regions[key] = region['id']
        
        print(f"   ✅ {len(regions)} regiones cargadas de Odoo.com")
        print(f"   ✅ {len(self.odoo_regions)} combinaciones indexadas")

    def get_cloudpepper_regions(self):
        """Obtiene todas las regiones de CloudPepper"""
        print("\n🏘️  Obteniendo regiones de CloudPepper...")
        
        region_ids = self.jsonrpc_call(
            self.cp_config, self.cp_uid,
            'property.region', 'search',
            args=[[]]
        )
        
        if not region_ids:
            print("   ⚠️  No hay regiones en CloudPepper")
            return []
        
        regions = self.jsonrpc_call(
            self.cp_config, self.cp_uid,
            'property.region', 'read',
            args=[region_ids],
            kwargs={'fields': ['id', 'name', 'city_id']}
        )
        
        print(f"   ✅ {len(regions)} regiones encontradas en CloudPepper")
        return regions

    def find_odoo_city_id(self, cp_city_id):
        """Encuentra el city_id en Odoo.com basándose en el city_id de CloudPepper"""
        if cp_city_id not in self.cp_cities:
            return None
        
        city_code = self.cp_cities[cp_city_id]['code']
        
        if city_code and city_code in self.odoo_cities:
            return self.odoo_cities[city_code]
        
        return None

    def create_region_in_odoo(self, region_name, city_id_odoo, cp_region_id):
        """Crea una región en Odoo.com"""
        try:
            vals = {
                'name': region_name,
                'city_id': city_id_odoo
            }
            
            new_id = self.jsonrpc_call(
                self.odoo_config, self.odoo_uid,
                'property.region', 'create',
                args=[vals]
            )
            
            return new_id
        except Exception as e:
            print(f"      ❌ Error creando región: {e}")
            return None

    def sync_regions(self, dry_run=False):
        """Sincroniza regiones de CloudPepper a Odoo.com"""
        print("\n" + "="*80)
        print("SINCRONIZACIÓN DE REGIONES/BARRIOS")
        print("="*80)
        
        if dry_run:
            print("\n⚠️  MODO DRY-RUN: No se crearán regiones, solo se mostrará qué se haría")
        
        # 1. Conectar
        self.connect_cloudpepper()
        self.connect_odoo()
        
        # 2. Cargar cachés
        self.load_cloudpepper_cities()
        self.load_odoo_cities()
        self.load_odoo_regions()
        
        # 3. Obtener regiones de CloudPepper
        cp_regions = self.get_cloudpepper_regions()
        
        if not cp_regions:
            print("\n⚠️  No hay regiones para sincronizar")
            return
        
        # 4. Procesar cada región
        print("\n" + "="*80)
        print("PROCESANDO REGIONES")
        print("="*80)
        
        stats = {
            'total': len(cp_regions),
            'created': 0,
            'exists': 0,
            'no_city': 0,
            'city_not_found': 0,
            'failed': 0,
            'by_city': defaultdict(int)
        }
        
        for idx, cp_region in enumerate(cp_regions, 1):
            cp_region_id = cp_region['id']
            region_name = cp_region.get('name', '').strip()
            
            if not region_name:
                print(f"\n[{idx}/{stats['total']}] ⚠️  Región sin nombre (ID: {cp_region_id})")
                stats['no_city'] += 1
                continue
            
            # Obtener ciudad en CloudPepper
            cp_city_id = None
            if cp_region.get('city_id'):
                cp_city_id = cp_region['city_id'][0] if isinstance(cp_region['city_id'], list) else cp_region['city_id']
            
            if not cp_city_id:
                print(f"\n[{idx}/{stats['total']}] ⚠️  {region_name}: Sin ciudad")
                stats['no_city'] += 1
                continue
            
            # Obtener nombre de ciudad
            city_name = self.cp_cities.get(cp_city_id, {}).get('name', 'N/A')
            
            # Buscar ciudad en Odoo.com
            odoo_city_id = self.find_odoo_city_id(cp_city_id)
            
            if not odoo_city_id:
                if idx <= 10:  # Solo mostrar primeras 10
                    print(f"\n[{idx}/{stats['total']}] ⚠️  {region_name} ({city_name}): Ciudad no encontrada en Odoo.com")
                stats['city_not_found'] += 1
                continue
            
            # Verificar si ya existe
            region_name_lower = region_name.lower()
            key = (odoo_city_id, region_name_lower)
            
            if key in self.odoo_regions:
                if idx <= 10:
                    print(f"\n[{idx}/{stats['total']}] ✅ {region_name} ({city_name}): Ya existe")
                stats['exists'] += 1
                continue
            
            # Crear en Odoo.com
            print(f"\n[{idx}/{stats['total']}] 🆕 {region_name} ({city_name})")
            
            if not dry_run:
                new_id = self.create_region_in_odoo(region_name, odoo_city_id, cp_region_id)
                
                if new_id:
                    print(f"   ✅ Creada con ID: {new_id}")
                    stats['created'] += 1
                    stats['by_city'][city_name] += 1
                    
                    # Agregar al caché
                    self.odoo_regions[key] = new_id
                else:
                    print(f"   ❌ Error creando")
                    stats['failed'] += 1
            else:
                print(f"   🔍 Se crearía: {region_name} → Ciudad ID: {odoo_city_id}")
                stats['created'] += 1
                stats['by_city'][city_name] += 1
        
        # 5. Reporte final
        print("\n" + "="*80)
        print("REPORTE FINAL")
        print("="*80)
        print(f"   📊 Total regiones en CloudPepper: {stats['total']}")
        print(f"   🆕 Creadas en Odoo.com: {stats['created']}")
        print(f"   ✅ Ya existían: {stats['exists']}")
        print(f"   ⚠️  Sin ciudad: {stats['no_city']}")
        print(f"   ⚠️  Ciudad no encontrada: {stats['city_not_found']}")
        print(f"   ❌ Fallidas: {stats['failed']}")
        
        if stats['by_city']:
            print(f"\n📍 Regiones creadas por ciudad (top 10):")
            sorted_cities = sorted(stats['by_city'].items(), key=lambda x: x[1], reverse=True)
            for city_name, count in sorted_cities[:10]:
                print(f"   {city_name}: {count}")
        
        print("="*80)
        
        if dry_run:
            print("\n⚠️  MODO DRY-RUN: No se creó nada realmente")
            print("   Para crear las regiones, ejecuta sin el parámetro 'test'")


def main():
    print("="*80)
    print("SINCRONIZACIÓN DE BARRIOS/REGIONES")
    print("CloudPepper (Odoo 17) → Odoo.com")
    print("="*80)
    
    dry_run = False
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['test', 'dry-run', 'dryrun']:
        dry_run = True
        print("\n⚠️  MODO TEST/DRY-RUN ACTIVADO")
    
    syncronizer = RegionSyncronizer()
    syncronizer.sync_regions(dry_run=dry_run)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para Actualizar Terceros como Propietarios de Propiedades
=================================================================
Actualiza automáticamente todos los res.partner que tengan propiedades
asociadas para marcarlos como propietarios.

Autor: Claude Code
Fecha: 2025-09-30
Versión: 1.0.0
"""

import xmlrpc.client
import logging
from typing import Dict, List, Tuple

# =================== CONFIGURACIÓN ===================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =================== CONFIGURACIÓN DE CONEXIÓN ===================
MODE = 'cloud'  # 'local' o 'cloud'

CONNECTIONS = {
    'local': {
        'url': 'http://localhost:8069',
        'db': 'david_test',
        'username': 'admin',
        'password': 'admin'
    },
    'cloud': {
        'url': 'https://darm1640-bohio-18.odoo.com',
        'db': 'darm1640-bohio-18-main-24081960',
        'username': 'admin',
        'password': 'admin'
    }
}

CONFIG = CONNECTIONS[MODE]


# =================== CLASE PRINCIPAL ===================
class PropertyOwnersUpdater:
    """Actualizador de propietarios de propiedades"""

    def __init__(self, url: str, db: str, username: str, password: str):
        """Inicializa la conexión con Odoo"""
        self.url = url
        self.db = db
        self.username = username
        self.password = password

        # Conexiones XML-RPC
        self.common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

        # Autenticación
        try:
            self.uid = self.common.authenticate(db, username, password, {})
            if not self.uid:
                raise Exception("Autenticación fallida")
            logger.info(f"✓ Conectado a {url} - Base: {db} (UID: {self.uid})")
        except Exception as e:
            logger.error(f"✗ Error de conexión: {e}")
            raise

    def execute(self, model: str, method: str, *args, **kwargs):
        """Ejecuta un método en Odoo mediante XML-RPC"""
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, method, args, kwargs
            )
        except Exception as e:
            logger.error(f"Error ejecutando {model}.{method}: {e}")
            raise

    def get_all_property_owners(self) -> List[Tuple[int, str, int]]:
        """
        Obtiene todos los propietarios principales de propiedades

        Returns:
            Lista de tuplas (partner_id, partner_name, property_count)
        """
        logger.info("Buscando propietarios de propiedades...")

        # Buscar todas las propiedades activas
        property_ids = self.execute(
            'product.template',
            'search',
            [('is_property', '=', True), ('active', '=', True)]
        )

        logger.info(f"  - Encontradas {len(property_ids)} propiedades")

        # Leer propietarios de las propiedades
        properties = self.execute(
            'product.template',
            'read',
            property_ids,
            ['id', 'name', 'partner_id']
        )

        # Contar propiedades por propietario
        owner_counts = {}
        owner_names = {}

        for prop in properties:
            if prop.get('partner_id'):
                partner_id = prop['partner_id'][0]
                partner_name = prop['partner_id'][1]

                owner_counts[partner_id] = owner_counts.get(partner_id, 0) + 1
                owner_names[partner_id] = partner_name

        # Convertir a lista de tuplas
        owners = [
            (partner_id, owner_names[partner_id], count)
            for partner_id, count in owner_counts.items()
        ]

        owners.sort(key=lambda x: x[2], reverse=True)  # Ordenar por cantidad de propiedades

        logger.info(f"  - Encontrados {len(owners)} propietarios únicos")

        return owners

    def get_all_contract_owners(self) -> List[Tuple[int, str, int]]:
        """
        Obtiene todos los propietarios desde contract.owner.partner

        Returns:
            Lista de tuplas (partner_id, partner_name, ownership_count)
        """
        logger.info("Buscando propietarios desde contratos...")

        # Buscar todos los registros de propietarios
        owner_ids = self.execute(
            'contract.owner.partner',
            'search',
            []
        )

        if not owner_ids:
            logger.info("  - No se encontraron registros en contract.owner.partner")
            return []

        logger.info(f"  - Encontrados {len(owner_ids)} registros de propietarios")

        # Leer datos de propietarios
        owners = self.execute(
            'contract.owner.partner',
            'read',
            owner_ids,
            ['partner_id', 'product_id', 'ownership_percentage', 'is_main_owner']
        )

        # Contar propiedades por propietario
        owner_counts = {}
        owner_names = {}

        for owner in owners:
            if owner.get('partner_id'):
                partner_id = owner['partner_id'][0]
                partner_name = owner['partner_id'][1]

                owner_counts[partner_id] = owner_counts.get(partner_id, 0) + 1
                owner_names[partner_id] = partner_name

        # Convertir a lista de tuplas
        contract_owners = [
            (partner_id, owner_names[partner_id], count)
            for partner_id, count in owner_counts.items()
        ]

        contract_owners.sort(key=lambda x: x[2], reverse=True)

        logger.info(f"  - Encontrados {len(contract_owners)} propietarios únicos en contratos")

        return contract_owners

    def update_partner_as_owner(self, partner_id: int, property_count: int) -> bool:
        """
        Actualiza un partner para marcarlo como propietario

        Args:
            partner_id: ID del partner
            property_count: Cantidad de propiedades que posee

        Returns:
            True si se actualizó exitosamente
        """
        try:
            # Verificar si el campo 'is_property_owner' existe
            # Si existe, actualizarlo; si no, solo actualizar supplier_rank

            # Leer datos actuales del partner
            partner = self.execute(
                'res.partner',
                'read',
                [partner_id],
                ['name', 'supplier_rank', 'customer_rank']
            )[0]

            # Preparar valores a actualizar
            vals = {
                'supplier_rank': max(partner.get('supplier_rank', 0), 1),  # Al menos 1
                'customer_rank': max(partner.get('customer_rank', 0), 1),  # Al menos 1
            }

            # Intentar agregar campo is_property_owner si existe
            try:
                # Verificar si el campo existe
                field_info = self.execute(
                    'res.partner',
                    'fields_get',
                    ['is_property_owner']
                )

                if 'is_property_owner' in field_info:
                    vals['is_property_owner'] = True
                    vals['property_count'] = property_count
            except:
                pass  # El campo no existe, continuar sin él

            # Actualizar partner
            self.execute(
                'res.partner',
                'write',
                [partner_id],
                vals
            )

            logger.debug(f"  ✓ Partner actualizado: {partner['name']} ({property_count} propiedades)")
            return True

        except Exception as e:
            logger.error(f"  ✗ Error actualizando partner {partner_id}: {e}")
            return False

    def update_all_property_owners(self) -> Dict:
        """
        Actualiza todos los terceros que tienen propiedades como propietarios

        Returns:
            Diccionario con estadísticas
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"INICIANDO ACTUALIZACIÓN DE PROPIETARIOS")
        logger.info(f"{'='*60}\n")

        stats = {
            'total_owners': 0,
            'updated': 0,
            'failed': 0,
            'total_properties': 0,
            'errors': []
        }

        # 1. Obtener propietarios principales de propiedades
        main_owners = self.get_all_property_owners()
        stats['total_properties'] = sum(count for _, _, count in main_owners)

        # 2. Obtener propietarios de contratos
        contract_owners = self.get_all_contract_owners()

        # 3. Combinar ambas listas (unión de propietarios)
        all_owners = {}

        # Agregar propietarios principales
        for partner_id, partner_name, count in main_owners:
            all_owners[partner_id] = {
                'name': partner_name,
                'properties': count,
                'contracts': 0
            }

        # Agregar propietarios de contratos
        for partner_id, partner_name, count in contract_owners:
            if partner_id in all_owners:
                all_owners[partner_id]['contracts'] = count
            else:
                all_owners[partner_id] = {
                    'name': partner_name,
                    'properties': 0,
                    'contracts': count
                }

        stats['total_owners'] = len(all_owners)

        logger.info(f"\n{'='*60}")
        logger.info(f"RESUMEN INICIAL")
        logger.info(f"{'='*60}")
        logger.info(f"Total de propietarios a actualizar: {stats['total_owners']}")
        logger.info(f"Total de propiedades: {stats['total_properties']}")
        logger.info(f"{'='*60}\n")

        # 4. Actualizar cada propietario
        for idx, (partner_id, owner_info) in enumerate(all_owners.items(), 1):
            total_count = owner_info['properties'] + owner_info['contracts']

            logger.info(f"[{idx}/{stats['total_owners']}] Actualizando: {owner_info['name']}")
            logger.info(f"  - Propiedades como principal: {owner_info['properties']}")
            logger.info(f"  - Propiedades en contratos: {owner_info['contracts']}")
            logger.info(f"  - Total: {total_count}")

            success = self.update_partner_as_owner(partner_id, total_count)

            if success:
                stats['updated'] += 1
            else:
                stats['failed'] += 1
                stats['errors'].append({
                    'partner': owner_info['name'],
                    'partner_id': partner_id
                })

        # 5. Resumen final
        logger.info(f"\n{'='*60}")
        logger.info(f"RESUMEN FINAL")
        logger.info(f"{'='*60}")
        logger.info(f"Total propietarios procesados: {stats['total_owners']}")
        logger.info(f"Actualizados exitosamente:    {stats['updated']} ({stats['updated']/stats['total_owners']*100:.1f}%)")
        logger.info(f"Fallidos:                     {stats['failed']} ({stats['failed']/stats['total_owners']*100:.1f}%)")
        logger.info(f"Total propiedades:            {stats['total_properties']}")
        logger.info(f"{'='*60}\n")

        if stats['errors']:
            logger.info(f"{'='*60}")
            logger.info(f"ERRORES DETALLADOS")
            logger.info(f"{'='*60}")
            for error in stats['errors']:
                logger.error(f"  - {error['partner']} (ID: {error['partner_id']})")

        return stats

    def generate_report(self, stats: Dict) -> str:
        """
        Genera un reporte detallado en formato texto

        Args:
            stats: Diccionario con estadísticas

        Returns:
            Reporte en texto
        """
        report = f"""
╔════════════════════════════════════════════════════════════╗
║         REPORTE DE ACTUALIZACIÓN DE PROPIETARIOS          ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  Total de propietarios procesados: {stats['total_owners']:>20} ║
║  Actualizados exitosamente:        {stats['updated']:>20} ║
║  Fallidos:                         {stats['failed']:>20} ║
║  Total de propiedades:             {stats['total_properties']:>20} ║
║                                                            ║
║  Tasa de éxito: {stats['updated']/stats['total_owners']*100:>6.1f}%                          ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
"""
        return report

    def get_top_owners(self, limit: int = 10) -> List[Dict]:
        """
        Obtiene los propietarios con más propiedades

        Args:
            limit: Cantidad de propietarios a retornar

        Returns:
            Lista de diccionarios con información de propietarios
        """
        logger.info(f"\nObteniendo top {limit} propietarios...")

        # Obtener propietarios
        main_owners = self.get_all_property_owners()
        contract_owners = self.get_all_contract_owners()

        # Combinar
        all_owners = {}
        for partner_id, partner_name, count in main_owners:
            all_owners[partner_id] = {
                'name': partner_name,
                'properties': count,
                'contracts': 0
            }

        for partner_id, partner_name, count in contract_owners:
            if partner_id in all_owners:
                all_owners[partner_id]['contracts'] = count
            else:
                all_owners[partner_id] = {
                    'name': partner_name,
                    'properties': 0,
                    'contracts': count
                }

        # Ordenar por total
        top_owners = []
        for partner_id, info in all_owners.items():
            total = info['properties'] + info['contracts']
            top_owners.append({
                'partner_id': partner_id,
                'name': info['name'],
                'properties': info['properties'],
                'contracts': info['contracts'],
                'total': total
            })

        top_owners.sort(key=lambda x: x['total'], reverse=True)
        top_owners = top_owners[:limit]

        # Mostrar tabla
        logger.info(f"\n{'='*80}")
        logger.info(f"TOP {limit} PROPIETARIOS CON MÁS PROPIEDADES")
        logger.info(f"{'='*80}")
        logger.info(f"{'#':<4} {'Propietario':<40} {'Propied.':<10} {'Contratos':<10} {'Total':<10}")
        logger.info(f"{'-'*80}")

        for idx, owner in enumerate(top_owners, 1):
            logger.info(
                f"{idx:<4} {owner['name'][:40]:<40} "
                f"{owner['properties']:<10} {owner['contracts']:<10} {owner['total']:<10}"
            )

        logger.info(f"{'='*80}\n")

        return top_owners


# =================== FUNCIÓN PRINCIPAL ===================
def main():
    """Función principal de ejecución"""

    # Conectar a Odoo
    updater = PropertyOwnersUpdater(
        url=CONFIG['url'],
        db=CONFIG['db'],
        username=CONFIG['username'],
        password=CONFIG['password']
    )

    # Mostrar top propietarios antes de actualizar
    logger.info("\n*** ANÁLISIS PREVIO ***")
    top_owners_before = updater.get_top_owners(limit=20)

    # Preguntar confirmación (comentar esta línea para ejecución automática)
    input("\nPresiona ENTER para continuar con la actualización...")

    # Ejecutar actualización
    stats = updater.update_all_property_owners()

    # Generar y mostrar reporte
    report = updater.generate_report(stats)
    print(report)

    # Guardar reporte en archivo
    report_file = f"property_owners_update_report_{CONFIG['db']}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    logger.info(f"Reporte guardado en: {report_file}")

    return stats


if __name__ == '__main__':
    main()
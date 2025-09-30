#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Copia de Empleados y Usuarios - Site → Odoo 18
=========================================================
Copia empleados desde el site y los crea también como usuarios

Version: 1.0.0
"""

import xmlrpc.client
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

# =================== CONFIGURACIÓN ===================

SOURCE = {
    'url': 'https://inmobiliariabohio.cloudpepper.site',
    'db': 'inmobiliariabohio.cloudpepper.site',
    'username': 'admin',
    'password': 'admin'
}

DESTINATION = {
    'url': 'https://darm1640-bohio-18.odoo.com',
    'db': 'darm1640-bohio-18-main-24081960',
    'username': 'admin',
    'password': 'admin'
}

LIMIT = 900000  # Número de empleados a copiar (todos)
DRY_RUN = False  # True = solo simular
CREATE_AS_USERS = True  # Crear también como usuarios de sistema


class OdooConnection:
    def __init__(self, name, url, db, username, password):
        self.name = name
        self.url = url
        self.db = db
        logger.info(f"\nConectando a {name}: {url}")

        self.common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        self.models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

        self.uid = self.common.authenticate(db, username, password, {})
        if not self.uid:
            raise Exception(f"Error autenticando en {name}")
        logger.info(f"OK - Conectado (UID: {self.uid})")

    def search(self, model, domain, limit=None):
        kwargs = {'limit': limit} if limit else {}
        return self.models.execute_kw(self.db, self.uid, 'admin', model, 'search', [domain], kwargs)

    def read(self, model, ids, fields=None):
        kwargs = {'fields': fields} if fields else {}
        return self.models.execute_kw(self.db, self.uid, 'admin', model, 'read', [ids], kwargs)

    def create(self, model, vals):
        return self.models.execute_kw(self.db, self.uid, 'admin', model, 'create', [[vals]])

    def search_read(self, model, domain, fields, limit=None):
        kwargs = {'fields': fields, 'limit': limit} if limit else {'fields': fields}
        return self.models.execute_kw(self.db, self.uid, 'admin', model, 'search_read', [domain], kwargs)

    def get_fields(self, model):
        """Obtiene todos los campos de un modelo"""
        return self.models.execute_kw(self.db, self.uid, 'admin', model, 'fields_get', [], {})


class EmployeeCopier:
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst
        self.cache = {'partner': {}, 'job': {}, 'department': {}, 'user': {}}

        # IDs base
        ids = self.dst.search('res.country', [('code', '=', 'CO')], 1)
        self.country_id = ids[0] if ids else None
        ids = self.dst.search('res.company', [('id', '=', 1)], 1)
        self.company_id = ids[0] if ids else 1

        logger.info(f"\nCache base: Pais={self.country_id}, Cia={self.company_id}\n")

        # Obtener campos disponibles en ambas bases
        logger.info("Detectando campos comunes de hr.employee...")
        self._detect_common_fields()

    def _detect_common_fields(self):
        """Detecta qué campos existen en ambas bases de datos"""
        try:
            src_fields = self.src.get_fields('hr.employee')
            dst_fields = self.dst.get_fields('hr.employee')

            # Campos comunes
            src_keys = set(src_fields.keys())
            dst_keys = set(dst_fields.keys())
            self.common_fields = src_keys.intersection(dst_keys)

            logger.info(f"   Campos en origen: {len(src_keys)}")
            logger.info(f"   Campos en destino: {len(dst_keys)}")
            logger.info(f"   Campos comunes: {len(self.common_fields)}")

            # Campos importantes para copiar
            self.priority_fields = [
                'name', 'work_email', 'work_phone', 'mobile_phone',
                'job_id', 'department_id', 'parent_id', 'coach_id',
                'address_home_id', 'work_location_id', 'user_id',
                'resource_calendar_id', 'tz', 'job_title',
                'work_contact_id', 'address_id', 'identification_id',
                'gender', 'birthday', 'place_of_birth', 'country_of_birth',
                'marital', 'spouse_complete_name', 'spouse_birthdate',
                'children', 'emergency_contact', 'emergency_phone',
                'visa_no', 'permit_no', 'visa_expire', 'certificate',
                'study_field', 'study_school', 'barcode', 'pin',
                'km_home_work', 'notes'
            ]

            # Filtrar solo campos que existan en ambas bases
            self.fields_to_copy = [f for f in self.priority_fields if f in self.common_fields]

            logger.info(f"   Campos a copiar: {len(self.fields_to_copy)}")
            logger.info(f"   Campos: {', '.join(self.fields_to_copy[:10])}...")

        except Exception as e:
            logger.error(f"Error detectando campos: {e}")
            # Campos mínimos por defecto
            self.fields_to_copy = ['name', 'work_email', 'work_phone', 'job_id', 'department_id']

    def get_or_create_job(self, job_name):
        """Obtiene o crea un puesto de trabajo"""
        if not job_name:
            return None

        if job_name in self.cache['job']:
            return self.cache['job'][job_name]

        # Buscar
        ids = self.dst.search('hr.job', [('name', '=', job_name)], 1)
        if ids:
            self.cache['job'][job_name] = ids[0]
            return ids[0]

        # Crear
        try:
            new_id = self.dst.create('hr.job', {
                'name': job_name,
                'company_id': self.company_id
            })
            self.cache['job'][job_name] = new_id
            logger.info(f"   + Puesto creado: {job_name} -> {new_id}")
            return new_id
        except:
            return None

    def get_or_create_department(self, dept_name):
        """Obtiene o crea un departamento"""
        if not dept_name:
            return None

        if dept_name in self.cache['department']:
            return self.cache['department'][dept_name]

        # Buscar
        ids = self.dst.search('hr.department', [('name', '=', dept_name)], 1)
        if ids:
            self.cache['department'][dept_name] = ids[0]
            return ids[0]

        # Crear
        try:
            new_id = self.dst.create('hr.department', {
                'name': dept_name,
                'company_id': self.company_id
            })
            self.cache['department'][dept_name] = new_id
            logger.info(f"   + Departamento creado: {dept_name} -> {new_id}")
            return new_id
        except:
            return None

    def get_or_create_partner(self, partner_data):
        """Obtiene o crea un partner (dirección particular)"""
        if not partner_data:
            return None

        name = partner_data.get('name')
        if not name:
            return None

        # Buscar por email si existe
        email = partner_data.get('email')
        if email:
            ids = self.dst.search('res.partner', [('email', '=', email)], 1)
            if ids:
                logger.info(f"   + Partner existente (email): {name} -> {ids[0]}")
                return ids[0]

        # Buscar por nombre
        ids = self.dst.search('res.partner', [('name', '=', name)], 1)
        if ids:
            logger.info(f"   + Partner existente (nombre): {name} -> {ids[0]}")
            return ids[0]

        # Crear
        try:
            vals = {
                'name': name,
                'type': 'contact',
                'country_id': self.country_id
            }

            for field in ['email', 'phone', 'mobile', 'street', 'city']:
                if partner_data.get(field):
                    vals[field] = partner_data[field]

            new_id = self.dst.create('res.partner', vals)
            logger.info(f"   + Partner creado: {name} -> {new_id}")
            return new_id
        except Exception as e:
            logger.error(f"   Error creando partner: {e}")
            return None

    def create_user(self, employee_name, work_email, employee_id):
        """Crea un usuario del sistema para el empleado"""
        if not work_email:
            logger.warning(f"   ! No se puede crear usuario sin email para {employee_name}")
            return None

        try:
            # Buscar si ya existe usuario con ese email
            ids = self.dst.search('res.users', [('login', '=', work_email)], 1)
            if ids:
                logger.info(f"   + Usuario existente: {work_email} -> {ids[0]}")
                return ids[0]

            # Buscar grupo de empleado
            employee_group_ids = self.dst.search('res.groups', [('name', '=', 'Employee')], 1)
            employee_group = employee_group_ids[0] if employee_group_ids else 1

            # Crear usuario ACTIVO sin enviar email
            vals = {
                'name': employee_name,
                'login': work_email,
                'email': work_email,
                'company_id': self.company_id,
                'company_ids': [(6, 0, [self.company_id])],
                'active': True,  # Usuario ACTIVO
                'password': 'changeme123',  # Password temporal
                'groups_id': [(6, 0, [employee_group])]
            }

            # Crear usuario normal (sin context que causa error)
            user_id = self.dst.create('res.users', vals)
            logger.info(f"   + Usuario creado: {work_email} -> {user_id}")

            # Actualizar empleado con el usuario
            self.dst.models.execute_kw(
                self.dst.db, self.dst.uid, 'admin',
                'hr.employee', 'write',
                [[employee_id], {'user_id': user_id}]
            )

            return user_id

        except Exception as e:
            logger.error(f"   Error creando usuario: {e}")
            return None

    def copy_one(self, emp):
        try:
            name = emp.get('name', 'Sin nombre')
            src_id = emp.get('id')

            logger.info(f"\n{'='*70}")
            logger.info(f"Empleado: {name} (ID origen: {src_id})")

            # Verificar si ya existe por work_email
            if emp.get('work_email'):
                existing = self.dst.search('hr.employee', [('work_email', '=', emp['work_email'])], 1)
                if existing:
                    logger.info(f"   ! Ya existe empleado con email {emp['work_email']}: ID {existing[0]}")
                    return True, existing[0]

            # Procesar relaciones
            job_id = None
            if emp.get('job_id'):
                job_id = self.get_or_create_job(emp['job_id'][1])

            department_id = None
            if emp.get('department_id'):
                department_id = self.get_or_create_department(emp['department_id'][1])

            # Partner de dirección particular
            address_home_id = None
            if emp.get('address_home_id'):
                # Leer datos del partner
                try:
                    partner_data = self.src.read('res.partner', [emp['address_home_id'][0]],
                                                 ['name', 'email', 'phone', 'mobile', 'street', 'city'])[0]
                    address_home_id = self.get_or_create_partner(partner_data)
                except:
                    pass

            # Construir valores del empleado
            vals = {
                'name': name,
                'company_id': self.company_id,
                'active': True,  # Crear empleados ACTIVOS
            }

            # Agregar campos detectados automáticamente
            # Excluir campos problemáticos
            excluded_fields = ['certificate', 'user_id', 'job_id', 'department_id', 'address_home_id']

            for field in self.fields_to_copy:
                if field in excluded_fields:
                    continue

                if field in emp and emp[field]:
                    value = emp[field]

                    # Manejar campos Many2one que no fueron procesados arriba
                    if isinstance(value, list) and len(value) == 2:
                        # Ignorar Many2one complejos por ahora
                        continue
                    else:
                        # Campos simples (char, text, date, integer, float, boolean)
                        vals[field] = value

            # Agregar Many2one ya procesados
            if job_id:
                vals['job_id'] = job_id
            if department_id:
                vals['department_id'] = department_id
            if address_home_id:
                vals['address_home_id'] = address_home_id

            # Campos especiales
            if emp.get('birthday'):
                vals['birthday'] = emp['birthday']

            # Resumen
            logger.info(f"\nResumen:")
            logger.info(f"  Email: {vals.get('work_email', 'N/A')}")
            logger.info(f"  Puesto: {job_id}")
            logger.info(f"  Departamento: {department_id}")
            logger.info(f"  Total campos: {len(vals)}")

            if DRY_RUN:
                logger.info(f"\n[DRY RUN] NO SE CREO - Solo simulacion")
                return True, 0

            # Crear empleado
            logger.info(f"\nCreando empleado en destino...")
            new_id = self.dst.create('hr.employee', vals)
            logger.info(f"OK! Empleado creado: {name} -> ID {new_id}")

            # Crear usuario si está habilitado
            if CREATE_AS_USERS and vals.get('work_email'):
                logger.info(f"\nCreando usuario de sistema...")
                user_id = self.create_user(name, vals['work_email'], new_id)
                if user_id:
                    logger.info(f"OK! Usuario asociado al empleado")

            return True, new_id

        except Exception as e:
            logger.error(f"ERROR: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False, 0

    def copy_all(self, limit):
        logger.info(f"\n{'#'*70}")
        if DRY_RUN:
            logger.info(f"# MODO PRUEBA (DRY RUN)")
        else:
            logger.info(f"# COPIA DE EMPLEADOS Y USUARIOS")
        logger.info(f"{'#'*70}\n")

        logger.info(f"Buscando empleados en origen...")

        # Usar campos detectados + id
        fields_to_read = ['id'] + self.fields_to_copy + ['active']

        emps = self.src.search_read(
            'hr.employee',
            [('active', '=', True)],
            fields_to_read,
            limit
        )

        logger.info(f"Encontrados {len(emps)} empleados activos\n")

        if not emps:
            logger.warning("No hay empleados para copiar")
            return {'total': 0, 'ok': 0, 'fail': 0}

        stats = {'total': len(emps), 'ok': 0, 'fail': 0, 'errors': []}

        for idx, emp in enumerate(emps, 1):
            logger.info(f"\n[{idx}/{stats['total']}]")
            success, new_id = self.copy_one(emp)
            if success:
                stats['ok'] += 1
            else:
                stats['fail'] += 1
                stats['errors'].append(emp.get('name', 'Sin nombre'))

        logger.info(f"\n{'='*70}")
        logger.info(f"RESUMEN FINAL")
        logger.info(f"{'='*70}")
        logger.info(f"Total:    {stats['total']}")
        logger.info(f"Exitosos: {stats['ok']} ({stats['ok']/stats['total']*100:.1f}%)")
        logger.info(f"Fallidos: {stats['fail']}")
        if stats['errors']:
            logger.info(f"\nEmpleados con error:")
            for err in stats['errors']:
                logger.info(f"  - {err}")
        logger.info(f"{'='*70}\n")

        return stats


def main():
    logger.info("\n" + "#"*70)
    logger.info("# COPIA DE EMPLEADOS Y USUARIOS: SITE -> ODOO 18")
    logger.info("#"*70)

    src = OdooConnection("ORIGEN", SOURCE['url'], SOURCE['db'], SOURCE['username'], SOURCE['password'])
    dst = OdooConnection("DESTINO", DESTINATION['url'], DESTINATION['db'], DESTINATION['username'], DESTINATION['password'])

    copier = EmployeeCopier(src, dst)
    stats = copier.copy_all(LIMIT)

    logger.info(f"\nProceso completado: {stats['ok']}/{stats['total']} exitosos")
    if CREATE_AS_USERS:
        logger.info(f"Usuarios creados para empleados con email\n")


if __name__ == '__main__':
    main()
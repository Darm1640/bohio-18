# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime, timedelta
import json


class PropertyDashboard(models.AbstractModel):
    _name = 'property.dashboard'
    _description = 'Dashboard de Propiedades Inmobiliarias'

    @api.model
    def get_dashboard_data(self):
        """Obtiene todos los datos necesarios para el dashboard"""
        import logging
        _logger = logging.getLogger(__name__)

        # Verificar si el usuario es solo vendedor
        user = self.env.user
        is_salesperson_only = user.has_group('sales_team.group_sale_salesman') and not user.has_group('sales_team.group_sale_salesman_all_leads')

        user_info = self._get_user_info()
        user_info['is_salesperson_only'] = is_salesperson_only

        data = {
            'properties_by_status': [],
            'properties_by_region': [],
            'expected_income': [],
            'properties_by_salesperson': [],
            'properties_by_type': [],
            'recent_activities': [],
            'map_data': [],
            'user_info': user_info,
            'contracts_data': {},
            'contracts_by_status': [],
            'monthly_billing': [],
            'payment_collection': [],
            'new_contracts_month': [],
        }

        # Cargar cada sección con manejo de errores
        try:
            data['properties_by_status'] = self._get_properties_by_status()
        except Exception as e:
            _logger.error(f"Error loading properties_by_status: {e}")

        try:
            data['properties_by_region'] = self._get_properties_by_region()
        except Exception as e:
            _logger.error(f"Error loading properties_by_region: {e}")

        try:
            data['expected_income'] = self._get_expected_income()
        except Exception as e:
            _logger.error(f"Error loading expected_income: {e}")

        try:
            data['properties_by_salesperson'] = self._get_properties_by_salesperson()
        except Exception as e:
            _logger.error(f"Error loading properties_by_salesperson: {e}")

        try:
            data['properties_by_type'] = self._get_properties_by_type()
        except Exception as e:
            _logger.error(f"Error loading properties_by_type: {e}")

        try:
            data['recent_activities'] = self._get_recent_activities()
        except Exception as e:
            _logger.error(f"Error loading recent_activities: {e}")

        try:
            data['map_data'] = self._get_map_data()
        except Exception as e:
            _logger.error(f"Error loading map_data: {e}")

        try:
            data['contracts_data'] = self._get_contracts_data(is_salesperson_only)
        except Exception as e:
            _logger.error(f"Error loading contracts_data: {e}")

        try:
            data['contracts_by_status'] = self._get_contracts_by_status(is_salesperson_only)
        except Exception as e:
            _logger.error(f"Error loading contracts_by_status: {e}")

        try:
            data['monthly_billing'] = self._get_monthly_billing(is_salesperson_only)
        except Exception as e:
            _logger.error(f"Error loading monthly_billing: {e}")

        try:
            data['payment_collection'] = self._get_payment_collection(is_salesperson_only)
        except Exception as e:
            _logger.error(f"Error loading payment_collection: {e}")

        try:
            data['new_contracts_month'] = self._get_new_contracts_month(is_salesperson_only)
        except Exception as e:
            _logger.error(f"Error loading new_contracts_month: {e}")

        return data

    def _get_user_info(self):
        """Obtiene información del usuario actual"""
        user = self.env.user
        partner = user.partner_id

        # Obtener la imagen del usuario (avatar)
        avatar_url = '/web/image?model=res.partner&id=%s&field=avatar_128' % partner.id if partner.avatar_128 else '/web/static/img/placeholder.png'

        # Obtener el puesto de trabajo (job position)
        job_title = partner.function or 'Usuario'

        return {
            'name': user.name or 'Usuario',
            'email': user.email or '',
            'avatar_url': avatar_url,
            'job_title': job_title,
            'company': user.company_id.name if user.company_id else '',
            'groups': [g.name for g in user.groups_id[:5]],  # Primeros 5 grupos
        }

    def _get_properties_by_status(self):
        """Obtiene propiedades agrupadas por estado"""
        properties = self.env['product.template'].search([('is_property', '=', True)])
        status_data = {}

        for prop in properties:
            status = prop.property_status or 'sin_estado'
            if status not in status_data:
                status_data[status] = {
                    'count': 0,
                    'total_value': 0,
                    'label': self._get_status_label(status)
                }
            status_data[status]['count'] += 1
            status_data[status]['total_value'] += prop.list_price

        return list(status_data.values())

    def _get_properties_by_region(self):
        """Obtiene propiedades agrupadas por barrio/región"""
        query = """
            SELECT
                rr.id as region_id,
                rr.name as region_name,
                rr.latitude,
                rr.longitude,
                COUNT(pt.id) as property_count,
                SUM(pt.list_price) as total_value,
                AVG(pt.list_price) as avg_price
            FROM product_template pt
            LEFT JOIN region_region rr ON pt.region_id = rr.id
            WHERE pt.is_property = true
            GROUP BY rr.id, rr.name, rr.latitude, rr.longitude
            ORDER BY property_count DESC
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def _get_expected_income(self):
        """Calcula el ingreso esperado mensual por tipo de propiedad"""
        query = """
            SELECT
                ptype.name as property_type,
                COUNT(pt.id) as count,
                SUM(CASE
                    WHEN pt.property_status = 'rented' THEN pt.net_rental_price
                    WHEN pt.property_status = 'available' THEN pt.net_rental_price * 0.7
                    ELSE 0
                END) as monthly_income
            FROM product_template pt
            LEFT JOIN property_type ptype ON pt.property_type_id = ptype.id
            WHERE pt.is_property = true
            GROUP BY ptype.name
            ORDER BY monthly_income DESC
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def _get_properties_by_salesperson(self):
        """Obtiene propiedades por vendedor"""
        query = """
            SELECT
                rp.name as salesperson_name,
                ru.id as user_id,
                COUNT(pt.id) as property_count,
                SUM(pt.list_price) as total_value,
                COUNT(CASE WHEN pt.property_status = 'sold' THEN 1 END) as sold_count,
                COUNT(CASE WHEN pt.property_status = 'rented' THEN 1 END) as rented_count
            FROM product_template pt
            LEFT JOIN res_users ru ON pt.user_consing_id = ru.id
            LEFT JOIN res_partner rp ON ru.partner_id = rp.id
            WHERE pt.is_property = true
            GROUP BY ru.id, rp.name
            ORDER BY property_count DESC
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def _get_properties_by_type(self):
        """Obtiene distribución de propiedades por tipo"""
        query = """
            SELECT
                COALESCE(ptype.name, 'Sin Tipo') as type_name,
                ptype.property_type as type_code,
                COUNT(pt.id) as count,
                AVG(pt.list_price) as avg_price,
                MIN(pt.list_price) as min_price,
                MAX(pt.list_price) as max_price
            FROM product_template pt
            LEFT JOIN property_type ptype ON pt.property_type_id = ptype.id
            WHERE pt.is_property = true
            GROUP BY ptype.name, ptype.property_type
            ORDER BY count DESC
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def _get_recent_activities(self):
        """Obtiene actividades recientes en propiedades"""
        # Últimas 10 actividades
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'product.template'),
        ], limit=10, order='create_date desc')

        result = []
        for activity in activities:
            if activity.res_id:
                prop = self.env['product.template'].browse(activity.res_id)
                if prop.is_property:
                    result.append({
                        'property_name': prop.name,
                        'property_id': prop.id,
                        'activity_type': activity.activity_type_id.name,
                        'summary': activity.summary,
                        'date_deadline': activity.date_deadline.strftime('%Y-%m-%d') if activity.date_deadline else '',
                        'user_name': activity.user_id.name
                    })
        return result

    def _get_map_data(self):
        """Obtiene datos para el mapa de propiedades"""
        query = """
            SELECT
                pt.id,
                pt.name,
                pt.list_price,
                pt.property_status,
                COALESCE(pt.latitude, rr.latitude) as latitude,
                COALESCE(pt.longitude, rr.longitude) as longitude,
                rr.name as region_name,
                ptype.name as type_name
            FROM product_template pt
            LEFT JOIN region_region rr ON pt.region_id = rr.id
            LEFT JOIN property_type ptype ON pt.property_type_id = ptype.id
            WHERE pt.is_property = true
                AND (pt.latitude IS NOT NULL OR rr.latitude IS NOT NULL)
                AND (pt.longitude IS NOT NULL OR rr.longitude IS NOT NULL)
            LIMIT 500
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def _get_status_label(self, status):
        """Retorna la etiqueta para cada estado"""
        labels = {
            'new': 'Nuevo',
            'available': 'Disponible',
            'booked': 'Reservado',
            'rented': 'Alquilado',
            'sold': 'Vendido',
            'sin_estado': 'Sin Estado'
        }
        return labels.get(status, status)

    @api.model
    def get_salesperson_properties(self, user_id):
        """Obtiene las propiedades de un vendedor específico"""
        if not user_id:
            return []

        properties = self.env['product.template'].search([
            ('is_property', '=', True),
            ('user_consing_id', '=', user_id)
        ])

        result = []
        for prop in properties:
            result.append({
                'id': prop.id,
                'name': prop.name,
                'status': prop.property_status,
                'price': prop.list_price,
                'type': prop.property_type_id.name if prop.property_type_id else 'Sin tipo',
                'region': prop.region_id.name if prop.region_id else 'Sin barrio',
                'bedrooms': prop.no_of_bathroom,
                'area': prop.ground_area,
            })

        return result

    def _get_contracts_data(self, is_salesperson_only=False):
        """Obtiene datos generales de contratos"""
        where_clause = ""
        if is_salesperson_only:
            where_clause = f"AND pc.user_id = {self.env.user.id}"

        query = f"""
            SELECT
                COUNT(DISTINCT pc.id) as total_contracts,
                COUNT(DISTINCT CASE WHEN pc.state = 'draft' THEN pc.id END) as draft_count,
                COUNT(DISTINCT CASE WHEN pc.state = 'confirmed' THEN pc.id END) as confirmed_count,
                COUNT(DISTINCT CASE WHEN pc.state = 'renew' THEN pc.id END) as renewed_count,
                COUNT(DISTINCT CASE WHEN pc.state = 'cancel' THEN pc.id END) as cancelled_count,
                COUNT(DISTINCT CASE WHEN pc.contract_type = 'is_rental' THEN pc.id END) as rental_count,
                COUNT(DISTINCT CASE WHEN pc.contract_type = 'is_ownership' THEN pc.id END) as ownership_count,
                SUM(DISTINCT pc.rental_fee) as total_rental_fee,
                COALESCE(SUM(ll.amount), 0) as total_contract_value
            FROM property_contract pc
            LEFT JOIN loan_line ll ON ll.contract_id = pc.id
            WHERE 1=1 {where_clause}
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchone()

    def _get_contracts_by_status(self, is_salesperson_only=False):
        """Obtiene contratos agrupados por estado"""
        where_clause = ""
        if is_salesperson_only:
            where_clause = f"AND pc.user_id = {self.env.user.id}"

        query = f"""
            SELECT
                pc.state,
                COUNT(DISTINCT pc.id) as count,
                SUM(pc.rental_fee) as total_rental,
                COALESCE(SUM(ll.amount), 0) as total_value,
                AVG(pc.rental_fee) as avg_rental
            FROM property_contract pc
            LEFT JOIN loan_line ll ON ll.contract_id = pc.id
            WHERE 1=1 {where_clause}
            GROUP BY pc.state
            ORDER BY count DESC
        """
        self.env.cr.execute(query)
        results = self.env.cr.dictfetchall()

        # Agregar etiquetas legibles
        state_labels = {
            'draft': 'Borrador',
            'confirmed': 'Confirmado',
            'renew': 'Renovado',
            'cancel': 'Cancelado'
        }

        for result in results:
            result['label'] = state_labels.get(result['state'], result['state'])

        return results

    def _get_monthly_billing(self, is_salesperson_only=False):
        """Obtiene facturación mensual de contratos"""
        from_date = fields.Date.today().replace(day=1)
        to_date = (from_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        where_clause = f"WHERE ll.date >= '{from_date}' AND ll.date <= '{to_date}'"
        if is_salesperson_only:
            where_clause += f" AND pc.user_id = {self.env.user.id}"

        query = f"""
            SELECT
                ll.date,
                COUNT(*) as invoice_count,
                SUM(ll.amount) as total_amount,
                COUNT(CASE WHEN ll.payment_state = 'paid' THEN 1 END) as paid_count,
                SUM(CASE WHEN ll.payment_state = 'paid' THEN ll.amount ELSE 0 END) as paid_amount
            FROM loan_line ll
            INNER JOIN property_contract pc ON ll.contract_id = pc.id
            {where_clause}
            GROUP BY ll.date
            ORDER BY ll.date
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def _get_payment_collection(self, is_salesperson_only=False):
        """Obtiene información de recaudos y pagos"""
        where_clause = "WHERE pc.state = 'confirmed'"
        if is_salesperson_only:
            where_clause += f" AND pc.user_id = {self.env.user.id}"

        query = f"""
            SELECT
                pc.contract_type,
                COUNT(DISTINCT pc.id) as contract_count,
                COALESCE(SUM(CASE WHEN ll.payment_state = 'paid' THEN ll.amount ELSE 0 END), 0) as total_paid,
                COALESCE(SUM(ll.amount_residual), 0) as total_balance,
                COALESCE(SUM(ll.amount), 0) as total_expected,
                CASE
                    WHEN SUM(ll.amount) > 0
                    THEN (SUM(CASE WHEN ll.payment_state = 'paid' THEN ll.amount ELSE 0 END) / SUM(ll.amount) * 100)
                    ELSE 0
                END as collection_percentage
            FROM property_contract pc
            LEFT JOIN loan_line ll ON ll.contract_id = pc.id
            {where_clause}
            GROUP BY pc.contract_type
        """
        self.env.cr.execute(query)
        return self.env.cr.dictfetchall()

    def _get_new_contracts_month(self, is_salesperson_only=False):
        """Obtiene contratos nuevos del mes actual"""
        from_date = fields.Date.today().replace(day=1)
        to_date = (from_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        where_clause = f"WHERE pc.create_date >= '{from_date}' AND pc.create_date <= '{to_date}'"
        if is_salesperson_only:
            where_clause += f" AND pc.user_id = {self.env.user.id}"

        query = f"""
            SELECT
                pc.id,
                pc.name as contract_number,
                rp.name as partner_name,
                pt.name as property_name,
                pc.contract_type,
                pc.state,
                pc.rental_fee,
                pc.date_from,
                pc.date_to,
                ru.name as salesperson_name
            FROM property_contract pc
            LEFT JOIN res_partner rp ON pc.partner_id = rp.id
            LEFT JOIN product_template pt ON pc.property_id = pt.id
            LEFT JOIN res_users ru ON pc.user_id = ru.id
            {where_clause}
            ORDER BY pc.create_date DESC
            LIMIT 20
        """
        self.env.cr.execute(query)
        results = self.env.cr.dictfetchall()

        # Formatear tipos y estados
        for result in results:
            result['contract_type_label'] = 'Arrendamiento' if result['contract_type'] == 'is_rental' else 'Propiedad'
            result['state_label'] = self._get_contract_state_label(result['state'])

        return results

    def _get_contract_state_label(self, state):
        """Retorna la etiqueta para cada estado de contrato"""
        labels = {
            'draft': 'Borrador',
            'confirmed': 'Confirmado',
            'renew': 'Renovado',
            'cancel': 'Cancelado'
        }
        return labels.get(state, state)

    @api.model
    def get_filtered_contracts_data(self, filters):
        """Obtiene datos de contratos con filtros aplicados"""
        user = self.env.user
        is_salesperson_only = user.has_group('sales_team.group_sale_salesman') and not user.has_group('sales_team.group_sale_salesman_all_leads')

        # Construir cláusula WHERE basada en filtros
        where_conditions = ["1=1"]

        if is_salesperson_only:
            where_conditions.append(f"pc.user_id = {user.id}")

        if filters.get('date_from'):
            where_conditions.append(f"pc.date_from >= '{filters['date_from']}'")

        if filters.get('date_to'):
            where_conditions.append(f"pc.date_to <= '{filters['date_to']}'")

        if filters.get('contract_type'):
            where_conditions.append(f"pc.contract_type = '{filters['contract_type']}'")

        if filters.get('property_type'):
            where_conditions.append(f"pc.type = '{filters['property_type']}'")

        if filters.get('state'):
            where_conditions.append(f"pc.state = '{filters['state']}'")

        if filters.get('salesperson_id') and not is_salesperson_only:
            where_conditions.append(f"pc.user_id = {filters['salesperson_id']}")

        where_clause = "WHERE " + " AND ".join(where_conditions)

        # Query principal para obtener contratos filtrados
        query = f"""
            SELECT
                pc.id,
                pc.name as contract_number,
                pc.contract_type,
                pc.state,
                pc.date_from,
                pc.date_to,
                pc.rental_fee,
                COALESCE(SUM(ll.amount), 0) as amount_total,
                COALESCE(SUM(CASE WHEN ll.payment_state = 'paid' THEN ll.amount ELSE 0 END), 0) as paid,
                COALESCE(SUM(ll.amount_residual), 0) as balance,
                rp.name as partner_name,
                pt.name as property_name,
                ru.name as salesperson_name,
                COUNT(ll.id) as payment_count,
                COUNT(CASE WHEN ll.payment_state = 'paid' THEN 1 END) as paid_installments
            FROM property_contract pc
            LEFT JOIN res_partner rp ON pc.partner_id = rp.id
            LEFT JOIN product_template pt ON pc.property_id = pt.id
            LEFT JOIN res_users ru ON pc.user_id = ru.id
            LEFT JOIN loan_line ll ON ll.contract_id = pc.id
            {where_clause}
            GROUP BY pc.id, pc.name, pc.contract_type, pc.state, pc.date_from, pc.date_to,
                     pc.rental_fee, rp.name, pt.name, ru.name
            ORDER BY pc.date_from DESC
        """

        self.env.cr.execute(query)
        results = self.env.cr.dictfetchall()

        # Formatear resultados
        for result in results:
            result['contract_type_label'] = 'Arrendamiento' if result['contract_type'] == 'is_rental' else 'Propiedad'
            result['state_label'] = self._get_contract_state_label(result['state'])
            result['collection_rate'] = (result['paid'] / result['amount_total'] * 100) if result['amount_total'] > 0 else 0

        # Obtener resumen estadístico
        summary_query = f"""
            SELECT
                COUNT(DISTINCT pc.id) as total_contracts,
                SUM(DISTINCT pc.rental_fee) as total_rental_fee,
                COALESCE(SUM(ll.amount), 0) as total_value,
                COALESCE(SUM(CASE WHEN ll.payment_state = 'paid' THEN ll.amount ELSE 0 END), 0) as total_collected,
                COALESCE(SUM(ll.amount_residual), 0) as total_pending
            FROM property_contract pc
            LEFT JOIN product_template pt ON pc.property_id = pt.id
            LEFT JOIN loan_line ll ON ll.contract_id = pc.id
            {where_clause}
        """

        self.env.cr.execute(summary_query)
        summary = self.env.cr.dictfetchone()

        return {
            'contracts': results,
            'summary': summary,
            'filters_applied': filters
        }
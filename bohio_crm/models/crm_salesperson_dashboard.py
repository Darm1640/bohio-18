# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

try:
    import numpy as np
    import pandas as pd
except ImportError:
    _logger.warning("NumPy y Pandas no están instalados. Las proyecciones financieras no estarán disponibles.")
    np = None
    pd = None


class CRMSalespersonDashboard(models.TransientModel):
    _name = 'crm.salesperson.dashboard'
    _description = 'Dashboard CRM con Proyección Financiera y Análisis de Embudo'

    # =================== MÉTODOS PRINCIPALES ===================

    @api.model
    def get_dashboard_data(self):
        """Obtiene todos los datos del dashboard incluyendo proyecciones"""
        user = self.env.user

        # Determinar si es vendedor individual o gerente
        is_manager = user.has_group('sales_team.group_sale_manager')

        data = {
            'messages': self._get_recent_messages(is_manager),
            'funnel_data': self._get_sales_funnel(is_manager),
            'contracts_by_state': self._get_contracts_by_state(is_manager),
            'properties_associated': self._get_properties_stats(is_manager),
            'calendar_events': self._get_calendar_events(is_manager),
            'forecast_data': self._get_financial_forecast(is_manager),
            'expenses_summary': self._get_expenses_summary(is_manager),
            'income_vs_collection': self._get_income_vs_collection(is_manager),
            'user_info': {
                'name': user.name,
                'is_manager': is_manager,
                'team_id': user.sale_team_id.id if user.sale_team_id else False,
                'team_name': user.sale_team_id.name if user.sale_team_id else '',
            }
        }

        return data

    # =================== MENSAJES Y ACTIVIDAD ===================

    def _get_recent_messages(self, is_manager=False):
        """Obtiene mensajes recientes del chatter de oportunidades"""
        domain = []
        if not is_manager:
            domain.append(('user_id', '=', self.env.user.id))

        # Buscar oportunidades con mensajes recientes
        leads = self.env['crm.lead'].search(domain, limit=20, order='write_date desc')

        messages = []
        for lead in leads:
            # Obtener últimos 3 mensajes del lead
            lead_messages = self.env['mail.message'].search([
                ('model', '=', 'crm.lead'),
                ('res_id', '=', lead.id),
                ('message_type', 'in', ['comment', 'notification'])
            ], limit=3, order='date desc')

            for msg in lead_messages:
                messages.append({
                    'id': msg.id,
                    'lead_id': lead.id,
                    'lead_name': lead.name,
                    'author': msg.author_id.name if msg.author_id else 'Sistema',
                    'body': msg.body,
                    'date': msg.date.isoformat() if msg.date else False,
                    'subtype': msg.subtype_id.name if msg.subtype_id else '',
                })

        # Ordenar por fecha descendente y tomar los últimos 10
        messages = sorted(messages, key=lambda x: x['date'], reverse=True)[:10]

        return messages

    @api.model
    def get_more_messages(self, offset=0, limit=10):
        """Obtiene más mensajes (paginación)"""
        user = self.env.user
        is_manager = user.has_group('sales_team.group_sale_manager')

        domain = []
        if not is_manager:
            domain.append(('user_id', '=', user.id))

        leads = self.env['crm.lead'].search(domain, order='write_date desc')

        messages = []
        for lead in leads:
            lead_messages = self.env['mail.message'].search([
                ('model', '=', 'crm.lead'),
                ('res_id', '=', lead.id),
                ('message_type', 'in', ['comment', 'notification'])
            ], order='date desc')

            for msg in lead_messages:
                messages.append({
                    'id': msg.id,
                    'lead_id': lead.id,
                    'lead_name': lead.name,
                    'author': msg.author_id.name if msg.author_id else 'Sistema',
                    'body': msg.body,
                    'date': msg.date.isoformat() if msg.date else False,
                    'subtype': msg.subtype_id.name if msg.subtype_id else '',
                })

        # Ordenar y paginar
        messages = sorted(messages, key=lambda x: x['date'], reverse=True)
        return messages[offset:offset+limit]

    # =================== EMBUDO DE VENTAS CON ANÁLISIS ===================

    def _get_sales_funnel(self, is_manager=False):
        """
        Obtiene datos del embudo de ventas con análisis de cuellos de botella
        y promedio de días para cierre
        """
        domain = [('type', '=', 'opportunity')]
        if not is_manager:
            domain.append(('user_id', '=', self.env.user.id))

        # Agrupar por etapa
        funnel_data = []
        stages = self.env['crm.stage'].search([], order='sequence')

        # Calcular promedio de cierre (oportunidades ganadas)
        won_opportunities = self.env['crm.lead'].search(
            domain + [('stage_id.is_won', '=', True)],
            order='date_closed desc',
            limit=50
        )

        avg_days_to_close = 0
        if won_opportunities:
            days_list = []
            for opp in won_opportunities:
                if opp.create_date and opp.date_closed:
                    delta = (opp.date_closed - opp.create_date.date()).days
                    days_list.append(delta)

            if days_list:
                avg_days_to_close = sum(days_list) / len(days_list)

        # Analizar cada etapa
        prev_count = None
        bottleneck_stage = None
        max_drop = 0

        for stage in stages:
            stage_domain = domain + [('stage_id', '=', stage.id)]
            opportunities = self.env['crm.lead'].search(stage_domain)

            total_value = sum(opportunities.mapped('expected_revenue'))
            count = len(opportunities)

            # Detectar cuello de botella (mayor caída entre etapas)
            if prev_count is not None and prev_count > 0:
                drop_percentage = ((prev_count - count) / prev_count) * 100
                if drop_percentage > max_drop and not stage.is_won:
                    max_drop = drop_percentage
                    bottleneck_stage = stage.name

            # Calcular días promedio en esta etapa
            stage_opps_with_dates = opportunities.filtered(lambda o: o.date_open)
            avg_days_in_stage = 0
            if stage_opps_with_dates:
                days_in_stage = []
                for opp in stage_opps_with_dates:
                    if opp.date_open:
                        days = (datetime.now().date() - opp.date_open).days
                        days_in_stage.append(days)
                if days_in_stage:
                    avg_days_in_stage = sum(days_in_stage) / len(days_in_stage)

            funnel_data.append({
                'stage_name': stage.name,
                'stage_id': stage.id,
                'count': count,
                'total_value': total_value,
                'probability': stage.probability,
                'is_won': stage.is_won,
                'avg_days_in_stage': round(avg_days_in_stage, 1),
                'conversion_rate': (count / prev_count * 100) if prev_count and prev_count > 0 else 100,
            })

            prev_count = count

        return {
            'stages': funnel_data,
            'bottleneck': bottleneck_stage,
            'avg_days_to_close': round(avg_days_to_close, 1),
            'total_opportunities': sum(s['count'] for s in funnel_data),
            'total_pipeline_value': sum(s['total_value'] for s in funnel_data),
        }

    # =================== CONTRATOS Y PROPIEDADES ===================

    def _get_contracts_by_state(self, is_manager=False):
        """Obtiene cantidad de contratos por estado de firma"""
        domain = []
        if not is_manager:
            domain.append(('user_id', '=', self.env.user.id))

        contracts = self.env['property.contract'].search(domain)

        states_data = {
            'draft': {'label': 'Borrador', 'count': 0, 'value': 0},
            'confirmed': {'label': 'Confirmado', 'count': 0, 'value': 0},
            'renew': {'label': 'Renovado', 'count': 0, 'value': 0},
            'cancel': {'label': 'Cancelado', 'count': 0, 'value': 0},
        }

        for contract in contracts:
            state = contract.state
            if state in states_data:
                states_data[state]['count'] += 1
                # Sumar valor según tipo de contrato
                if contract.contract_type == 'is_rental':
                    states_data[state]['value'] += contract.rent or 0
                else:
                    states_data[state]['value'] += contract.total_sales_price or 0

        return list(states_data.values())

    def _get_properties_stats(self, is_manager=False):
        """Obtiene estadísticas de propiedades asociadas"""
        domain = [('is_property', '=', True)]

        if not is_manager:
            # Propiedades asignadas al vendedor
            user = self.env.user
            domain.append(('exclusive_salesperson_ids', 'in', user.id))

        properties = self.env['product.template'].search(domain)

        # Agrupar por estado
        by_status = {}
        for prop in properties:
            status = prop.property_status or 'sin_estado'
            if status not in by_status:
                by_status[status] = {'count': 0, 'total_value': 0}

            by_status[status]['count'] += 1
            by_status[status]['total_value'] += prop.list_price or 0

        return {
            'total': len(properties),
            'by_status': by_status,
        }

    # =================== CALENDARIO ===================

    def _get_calendar_events(self, is_manager=False):
        """Obtiene eventos del calendario (próximas actividades)"""
        domain = [
            ('res_model', '=', 'crm.lead'),
            ('date_deadline', '>=', fields.Date.today()),
            ('date_deadline', '<=', fields.Date.today() + timedelta(days=30))
        ]

        if not is_manager:
            domain.append(('user_id', '=', self.env.user.id))

        activities = self.env['mail.activity'].search(domain, limit=50, order='date_deadline asc')

        events = []
        for activity in activities:
            events.append({
                'id': activity.id,
                'title': activity.summary or activity.activity_type_id.name,
                'start': activity.date_deadline.isoformat() if activity.date_deadline else False,
                'lead_id': activity.res_id,
                'lead_name': activity.res_name,
                'activity_type': activity.activity_type_id.name,
                'user_name': activity.user_id.name,
            })

        return events

    # =================== PROYECCIONES FINANCIERAS ===================

    def _get_financial_forecast(self, is_manager=False):
        """
        Proyección financiera usando numpy y pandas
        Proyecta ingresos esperados y comisiones para la inmobiliaria
        """
        if not np or not pd:
            return {
                'error': 'NumPy y Pandas no están disponibles',
                'projected_income': [],
                'projected_commissions': [],
            }

        # Obtener contratos activos
        domain = [
            ('state', '=', 'confirmed'),
            ('contract_type', '=', 'is_rental')
        ]

        if not is_manager:
            domain.append(('user_id', '=', self.env.user.id))

        contracts = self.env['property.contract'].search(domain)

        if not contracts:
            return {
                'projected_income': [],
                'projected_commissions': [],
                'summary': {
                    'total_monthly': 0,
                    'total_annual': 0,
                    'avg_commission': 0,
                }
            }

        # Crear DataFrame con datos de contratos
        data = []
        for contract in contracts:
            # Calcular período esperado (en meses)
            if contract.date_from and contract.date_to:
                months = (contract.date_to.year - contract.date_from.year) * 12 + \
                        (contract.date_to.month - contract.date_from.month)
            else:
                months = 12  # Asumir 12 meses si no hay fechas

            monthly_rent = contract.rent or 0
            commission_percentage = contract.channel_partner_commission or 8.0

            data.append({
                'contract_id': contract.id,
                'monthly_rent': monthly_rent,
                'months': max(months, 1),  # Al menos 1 mes
                'commission_percentage': commission_percentage / 100,
            })

        df = pd.DataFrame(data)

        # Calcular proyecciones mensuales (próximos 12 meses)
        today = datetime.today()
        months_ahead = 12

        projected_income = []

        for i in range(months_ahead):
            month_date = today + relativedelta(months=i)

            # Filtrar contratos activos en ese mes
            active_contracts = df.copy()

            # Calcular ingresos basados en comisiones (nuestro ingreso real)
            # Si contrato es $20 y comisión 15%, ingreso = $3
            total_commission = (active_contracts['monthly_rent'] * active_contracts['commission_percentage']).sum()

            projected_income.append({
                'month': month_date.strftime('%Y-%m'),
                'month_label': month_date.strftime('%b %Y'),
                'value': float(total_commission),  # Ingreso = Comisión
            })

        # Calcular métricas de resumen basadas en comisiones
        total_monthly_commission = (df['monthly_rent'] * df['commission_percentage']).sum()
        total_annual_commission = total_monthly_commission * 12
        avg_commission = df['commission_percentage'].mean() * 100
        total_monthly_rent = df['monthly_rent'].sum()

        return {
            'projected_income': projected_income,
            'summary': {
                'total_monthly_commission': float(total_monthly_commission),
                'total_annual_commission': float(total_annual_commission),
                'total_monthly_rent': float(total_monthly_rent),
                'avg_commission': float(avg_commission),
                'active_contracts': len(contracts),
            }
        }

    # =================== INGRESOS VS RECAUDOS ===================

    def _get_income_vs_collection(self, is_manager=False):
        """
        Proyección de ingresos facturados vs recaudados
        Basado en propiedades actuales y sus contratos
        """
        if not np or not pd:
            return {'error': 'NumPy y Pandas no disponibles'}

        domain = [
            ('state', '=', 'confirmed'),
            ('contract_type', '=', 'is_rental')
        ]

        if not is_manager:
            domain.append(('user_id', '=', self.env.user.id))

        contracts = self.env['property.contract'].search(domain)

        # Obtener datos de loan_line (cuotas) para análisis real
        today = datetime.today()
        months_back = 6
        months_ahead = 12

        # Datos históricos y proyectados
        monthly_data = []

        for i in range(-months_back, months_ahead):
            month_date = today + relativedelta(months=i)
            first_day = month_date.replace(day=1)
            last_day = (first_day + relativedelta(months=1)) - timedelta(days=1)

            # Ingresos facturados (loan.line)
            loan_lines = self.env['loan.line'].search([
                ('contract_id', 'in', contracts.ids),
                ('date', '>=', first_day),
                ('date', '<=', last_day)
            ])

            total_invoiced = sum(loan_lines.mapped('amount'))

            # Recaudado (pagos efectivamente realizados)
            paid_lines = loan_lines.filtered(lambda l: l.invoice_id and l.invoice_id.payment_state == 'paid')
            total_collected = sum(paid_lines.mapped('amount'))

            monthly_data.append({
                'month': month_date.strftime('%Y-%m'),
                'month_label': month_date.strftime('%b %Y'),
                'invoiced': float(total_invoiced),
                'collected': float(total_collected),
                'pending': float(total_invoiced - total_collected),
                'is_projection': i >= 0,  # Futuro = proyección
            })

        return {
            'monthly_data': monthly_data,
            'summary': {
                'current_month_invoiced': monthly_data[months_back]['invoiced'] if len(monthly_data) > months_back else 0,
                'current_month_collected': monthly_data[months_back]['collected'] if len(monthly_data) > months_back else 0,
                'collection_rate': (monthly_data[months_back]['collected'] / monthly_data[months_back]['invoiced'] * 100)
                                 if monthly_data[months_back]['invoiced'] > 0 else 0,
            }
        }

    # =================== GASTOS ===================

    def _get_expenses_summary(self, is_manager=False):
        """Obtiene resumen de gastos asociados a oportunidades/leads"""
        domain = [('move_type', '=', 'in_invoice')]

        if not is_manager:
            domain.append(('invoice_user_id', '=', self.env.user.id))

        # Facturas de proveedores (gastos) del mes actual
        today = datetime.today()
        first_day = today.replace(day=1)
        last_day = (first_day + relativedelta(months=1)) - timedelta(days=1)

        domain.extend([
            ('invoice_date', '>=', first_day),
            ('invoice_date', '<=', last_day),
            ('state', '=', 'posted')
        ])

        invoices = self.env['account.move'].search(domain)

        total_expenses = sum(invoices.mapped('amount_total'))
        total_paid = sum(invoices.filtered(lambda inv: inv.payment_state == 'paid').mapped('amount_total'))
        total_pending = total_expenses - total_paid

        return {
            'total_expenses': float(total_expenses),
            'total_paid': float(total_paid),
            'total_pending': float(total_pending),
            'count': len(invoices),
        }

    @api.model
    def create_expense(self, vals):
        """Crea un gasto rápido desde el dashboard"""
        # Validar datos mínimos
        if not vals.get('amount') or not vals.get('description'):
            raise UserError(_("Monto y descripción son requeridos"))

        # Crear factura de proveedor (gasto)
        journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        if not journal:
            raise UserError(_("No se encontró diario de compras configurado"))

        # Buscar cuenta de gastos
        expense_account = self.env['account.account'].search([
            ('account_type', '=', 'expense'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if not expense_account:
            raise UserError(_("No se encontró cuenta de gastos configurada"))

        # Crear proveedor genérico si no se especifica
        partner_id = vals.get('partner_id')
        if not partner_id:
            partner = self.env['res.partner'].search([('name', '=', 'Gastos Varios')], limit=1)
            if not partner:
                partner = self.env['res.partner'].create({'name': 'Gastos Varios', 'supplier_rank': 1})
            partner_id = partner.id

        # Crear factura
        invoice_vals = {
            'move_type': 'in_invoice',
            'partner_id': partner_id,
            'invoice_date': fields.Date.today(),
            'journal_id': journal.id,
            'invoice_user_id': self.env.user.id,
            'ref': vals.get('description'),
            'invoice_line_ids': [(0, 0, {
                'name': vals.get('description'),
                'quantity': 1,
                'price_unit': vals.get('amount'),
                'account_id': expense_account.id,
            })],
        }

        invoice = self.env['account.move'].create(invoice_vals)

        return {
            'success': True,
            'invoice_id': invoice.id,
            'invoice_number': invoice.name,
        }

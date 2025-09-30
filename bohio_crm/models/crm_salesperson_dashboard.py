# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta
import json

class CRMSalespersonDashboard(models.Model):
    _name = 'crm.salesperson.dashboard'
    _description = 'Dashboard del Vendedor CRM'

    name = fields.Char('Nombre', compute='_compute_name')
    user_id = fields.Many2one('res.users', 'Vendedor', required=True, default=lambda self: self.env.user)
    dashboard_data = fields.Json('Datos del Dashboard', compute='_compute_dashboard_data')

    @api.depends('user_id')
    def _compute_name(self):
        for record in self:
            record.name = f"Dashboard - {record.user_id.name}"

    @api.depends('user_id')
    def _compute_dashboard_data(self):
        for record in self:
            user = record.user_id
            today = fields.Date.today()
            start_of_month = today.replace(day=1)

            # KPIs Generales
            total_opportunities = self.env['crm.lead'].search_count([
                ('user_id', '=', user.id),
                ('type', '=', 'opportunity')
            ])

            active_opportunities = self.env['crm.lead'].search_count([
                ('user_id', '=', user.id),
                ('type', '=', 'opportunity'),
                ('active', '=', True),
                ('probability', '>', 0),
                ('probability', '<', 100)
            ])

            total_contacts = self.env['res.partner'].search_count([
                ('user_id', '=', user.id)
            ])

            ongoing_tasks = self.env['mail.activity'].search_count([
                ('user_id', '=', user.id),
                ('date_deadline', '>=', today)
            ])

            # Emails enviados este mes
            emails_sent = self.env['mail.message'].search_count([
                ('author_id', '=', user.partner_id.id),
                ('message_type', '=', 'email'),
                ('date', '>=', start_of_month)
            ])

            # 5 Propuestas Próximas (por fecha deadline)
            upcoming_proposals = self.env['crm.lead'].search([
                ('user_id', '=', user.id),
                ('type', '=', 'opportunity'),
                ('date_deadline', '>=', today),
                ('active', '=', True),
                ('probability', '>', 0),
                ('probability', '<', 100)
            ], order='date_deadline asc', limit=5)

            proposals_data = []
            for lead in upcoming_proposals:
                # Obtener coordenadas de la propiedad principal o del proyecto
                lat, lng = None, None
                if lead.compared_properties_ids:
                    prop = lead.compared_properties_ids[0]
                    if hasattr(prop, 'region_id') and prop.region_id:
                        lat = prop.region_id.latitude
                        lng = prop.region_id.longitude
                elif lead.project_id and hasattr(lead.project_id, 'region_id') and lead.project_id.region_id:
                    lat = lead.project_id.region_id.latitude
                    lng = lead.project_id.region_id.longitude

                proposals_data.append({
                    'id': lead.id,
                    'name': lead.name,
                    'partner_name': lead.partner_id.name if lead.partner_id else 'Sin cliente',
                    'expected_revenue': lead.expected_revenue,
                    'probability': lead.probability,
                    'date_deadline': lead.date_deadline.isoformat() if lead.date_deadline else None,
                    'stage': lead.stage_id.name if lead.stage_id else '',
                    'latitude': lat,
                    'longitude': lng,
                })

            # Últimas 5 Ganadas
            won_opportunities = self.env['crm.lead'].search([
                ('user_id', '=', user.id),
                ('type', '=', 'opportunity'),
                ('probability', '=', 100),
                ('active', '=', True)
            ], order='date_closed desc', limit=5)

            won_data = [{
                'id': lead.id,
                'name': lead.name,
                'partner_name': lead.partner_id.name if lead.partner_id else '',
                'expected_revenue': lead.expected_revenue,
                'date_closed': lead.date_closed.isoformat() if lead.date_closed else None,
            } for lead in won_opportunities]

            # Últimas 5 Perdidas
            lost_opportunities = self.env['crm.lead'].search([
                ('user_id', '=', user.id),
                ('type', '=', 'opportunity'),
                ('active', '=', False),
                ('probability', '=', 0)
            ], order='write_date desc', limit=5)

            lost_data = [{
                'id': lead.id,
                'name': lead.name,
                'partner_name': lead.partner_id.name if lead.partner_id else '',
                'expected_revenue': lead.expected_revenue,
                'lost_reason': lead.lost_reason_id.name if lead.lost_reason_id else 'No especificada',
                'date_lost': lead.write_date.isoformat() if lead.write_date else None,
            } for lead in lost_opportunities]

            # Métricas Financieras
            all_opportunities = self.env['crm.lead'].search([
                ('user_id', '=', user.id),
                ('type', '=', 'opportunity')
            ])

            total_revenue = sum(all_opportunities.mapped('expected_revenue'))
            won_revenue = sum(won_opportunities.mapped('expected_revenue'))

            # Metas (hardcoded por ahora, puedes hacer un modelo separado para metas)
            monthly_goal = 50000.0  # Meta mensual
            monthly_progress = sum(self.env['crm.lead'].search([
                ('user_id', '=', user.id),
                ('type', '=', 'opportunity'),
                ('date_closed', '>=', start_of_month),
                ('probability', '=', 100)
            ]).mapped('expected_revenue'))

            goal_percentage = (monthly_progress / monthly_goal * 100) if monthly_goal > 0 else 0

            # Gráficos - Oportunidades por Etapa
            stages = self.env['crm.stage'].search([])
            opportunities_by_stage = []
            for stage in stages:
                count = self.env['crm.lead'].search_count([
                    ('user_id', '=', user.id),
                    ('type', '=', 'opportunity'),
                    ('stage_id', '=', stage.id),
                    ('active', '=', True)
                ])
                if count > 0:
                    opportunities_by_stage.append({
                        'stage': stage.name,
                        'count': count
                    })

            # Gráficos - Ingresos por Mes (últimos 6 meses)
            revenue_by_month = []
            for i in range(5, -1, -1):
                month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

                month_revenue = sum(self.env['crm.lead'].search([
                    ('user_id', '=', user.id),
                    ('type', '=', 'opportunity'),
                    ('date_closed', '>=', month_start),
                    ('date_closed', '<=', month_end),
                    ('probability', '=', 100)
                ]).mapped('expected_revenue'))

                revenue_by_month.append({
                    'month': month_start.strftime('%B'),
                    'revenue': month_revenue
                })

            record.dashboard_data = {
                'kpis': {
                    'emails_sent': emails_sent,
                    'active_opportunities': active_opportunities,
                    'total_contacts': total_contacts,
                    'ongoing_tasks': ongoing_tasks,
                    'total_opportunities': total_opportunities,
                },
                'upcoming_proposals': proposals_data,
                'won_opportunities': won_data,
                'lost_opportunities': lost_data,
                'financial': {
                    'total_revenue': total_revenue,
                    'won_revenue': won_revenue,
                    'monthly_goal': monthly_goal,
                    'monthly_progress': monthly_progress,
                    'goal_percentage': goal_percentage,
                },
                'charts': {
                    'opportunities_by_stage': opportunities_by_stage,
                    'revenue_by_month': revenue_by_month,
                }
            }
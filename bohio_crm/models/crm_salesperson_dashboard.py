# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta

class CRMSalespersonDashboard(models.Model):
    _name = 'crm.salesperson.dashboard'
    _description = 'Dashboard del Vendedor CRM'

    name = fields.Char('Nombre', compute='_compute_name')
    user_id = fields.Many2one('res.users', 'Vendedor', required=True, default=lambda self: self.env.user)
    dashboard_data = fields.Html('Datos del Dashboard', compute='_compute_dashboard_data', sanitize=False)

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

            emails_sent = self.env['mail.message'].search_count([
                ('author_id', '=', user.partner_id.id),
                ('message_type', '=', 'email'),
                ('date', '>=', start_of_month)
            ])

            # Propuestas Próximas
            upcoming_proposals = self.env['crm.lead'].search([
                ('user_id', '=', user.id),
                ('type', '=', 'opportunity'),
                ('date_deadline', '>=', today),
                ('active', '=', True),
                ('probability', '>', 0),
                ('probability', '<', 100)
            ], order='date_deadline asc', limit=5)

            # Últimas Ganadas
            won_opportunities = self.env['crm.lead'].search([
                ('user_id', '=', user.id),
                ('type', '=', 'opportunity'),
                ('probability', '=', 100),
                ('active', '=', True)
            ], order='date_closed desc', limit=5)

            # Últimas Perdidas
            lost_opportunities = self.env['crm.lead'].search([
                ('user_id', '=', user.id),
                ('type', '=', 'opportunity'),
                ('active', '=', False),
                ('probability', '=', 0)
            ], order='write_date desc', limit=5)

            # Métricas Financieras
            all_opportunities = self.env['crm.lead'].search([
                ('user_id', '=', user.id),
                ('type', '=', 'opportunity')
            ])

            total_revenue = sum(all_opportunities.mapped('expected_revenue'))
            won_revenue = sum(won_opportunities.mapped('expected_revenue'))

            monthly_goal = 50000.0
            monthly_progress = sum(self.env['crm.lead'].search([
                ('user_id', '=', user.id),
                ('type', '=', 'opportunity'),
                ('date_closed', '>=', start_of_month),
                ('probability', '=', 100)
            ]).mapped('expected_revenue'))

            goal_percentage = (monthly_progress / monthly_goal * 100) if monthly_goal > 0 else 0

            # URLs base
            base_url = f"/web#action={self.env.ref('bohio_crm.action_bohio_crm_opportunities').id}"

            # Generar HTML
            html = f'''
            <div class="container-fluid">
                <!-- KPIs Clicables -->
                <div class="row mb-3 g-2">
                    <div class="col-md-2 col-sm-4">
                        <a href="{base_url}&model=crm.lead&view_type=list" class="text-decoration-none">
                            <div class="card text-center bg-gradient-primary text-white p-2 h-100 shadow-sm hover-shadow">
                                <div class="card-body p-2">
                                    <i class="fa fa-envelope fa-2x mb-2"></i>
                                    <h4 class="mb-0 fw-bold">{emails_sent}</h4>
                                    <small>Emails Enviados</small>
                                    <div class="text-white-50 mt-1"><small>Este mes</small></div>
                                </div>
                            </div>
                        </a>
                    </div>
                    <div class="col-md-2 col-sm-4">
                        <a href="{base_url}&model=crm.lead&view_type=kanban" class="text-decoration-none">
                            <div class="card text-center bg-gradient-success text-white p-2 h-100 shadow-sm hover-shadow">
                                <div class="card-body p-2">
                                    <i class="fa fa-star fa-2x mb-2"></i>
                                    <h4 class="mb-0 fw-bold">{active_opportunities}</h4>
                                    <small>Oportunidades</small>
                                    <div class="text-white-50 mt-1"><small>Activas</small></div>
                                </div>
                            </div>
                        </a>
                    </div>
                    <div class="col-md-2 col-sm-4">
                        <a href="/web#action={self.env.ref('contacts.action_contacts').id}&model=res.partner&view_type=kanban" class="text-decoration-none">
                            <div class="card text-center bg-gradient-info text-white p-2 h-100 shadow-sm hover-shadow">
                                <div class="card-body p-2">
                                    <i class="fa fa-users fa-2x mb-2"></i>
                                    <h4 class="mb-0 fw-bold">{total_contacts}</h4>
                                    <small>Contactos</small>
                                    <div class="text-white-50 mt-1"><small>Total</small></div>
                                </div>
                            </div>
                        </a>
                    </div>
                    <div class="col-md-2 col-sm-4">
                        <a href="/web#action={self.env.ref('mail.mail_activity_action').id}&model=mail.activity&view_type=list" class="text-decoration-none">
                            <div class="card text-center bg-gradient-warning text-dark p-2 h-100 shadow-sm hover-shadow">
                                <div class="card-body p-2">
                                    <i class="fa fa-tasks fa-2x mb-2"></i>
                                    <h4 class="mb-0 fw-bold">{ongoing_tasks}</h4>
                                    <small>Tareas</small>
                                    <div class="text-muted mt-1"><small>Pendientes</small></div>
                                </div>
                            </div>
                        </a>
                    </div>
                    <div class="col-md-4 col-sm-8">
                        <div class="card text-center bg-gradient-dark text-white p-2 h-100 shadow">
                            <div class="card-body p-2">
                                <i class="fa fa-trophy fa-2x mb-2"></i>
                                <h6 class="mb-2">Meta Mensual</h6>
                                <div class="progress mb-2" style="height: 25px;">
                                    <div class="progress-bar bg-success progress-bar-striped progress-bar-animated"
                                         style="width: {min(goal_percentage, 100)}%">
                                        <strong class="fs-6">{goal_percentage:.1f}%</strong>
                                    </div>
                                </div>
                                <div class="d-flex justify-content-between px-2">
                                    <small class="text-white-50">Actual: ${monthly_progress:,.0f}</small>
                                    <small class="text-white-50">Meta: ${monthly_goal:,.0f}</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Métricas Financieras -->
                <div class="row mb-3">
                    <div class="col-4">
                        <div class="alert alert-success p-2 mb-0">
                            <strong>Ingresos Totales:</strong> <h5 class="d-inline mb-0">${total_revenue:,.0f}</h5>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="alert alert-primary p-2 mb-0">
                            <strong>Ingresos Ganados:</strong> <h5 class="d-inline mb-0">${won_revenue:,.0f}</h5>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="alert alert-info p-2 mb-0">
                            <strong>Total Oportunidades:</strong> <h5 class="d-inline mb-0">{total_opportunities}</h5>
                        </div>
                    </div>
                </div>

                <!-- Propuestas Próximas -->
                <div class="row mb-3">
                    <div class="col-12">
                        <h5>Proximas Propuestas (Top 5)</h5>
                        <table class="table table-sm table-striped table-hover">
                            <thead class="table-dark">
                                <tr>
                                    <th>Oportunidad</th>
                                    <th>Cliente</th>
                                    <th>Etapa</th>
                                    <th>Prob.</th>
                                    <th>Fecha</th>
                                    <th>Ingreso</th>
                                </tr>
                            </thead>
                            <tbody>
            '''

            if upcoming_proposals:
                for lead in upcoming_proposals:
                    html += f'''
                                <tr>
                                    <td><strong>{lead.name}</strong></td>
                                    <td>{lead.partner_id.name if lead.partner_id else 'Sin cliente'}</td>
                                    <td><span class="badge bg-primary">{lead.stage_id.name if lead.stage_id else 'N/A'}</span></td>
                                    <td>{lead.probability:.0f}%</td>
                                    <td><small>{lead.date_deadline or 'N/A'}</small></td>
                                    <td><strong class="text-success">${lead.expected_revenue:,.0f}</strong></td>
                                </tr>
                    '''
            else:
                html += '<tr><td colspan="6" class="text-center text-muted p-3"><em>No hay propuestas proximas</em></td></tr>'

            html += '''
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Ganadas y Perdidas -->
                <div class="row">
                    <div class="col-6">
                        <h5>Ultimas Ganadas (Top 5)</h5>
                        <table class="table table-sm table-success">
                            <thead class="table-success">
                                <tr>
                                    <th>Oportunidad</th>
                                    <th>Cliente</th>
                                    <th>Ingreso</th>
                                </tr>
                            </thead>
                            <tbody>
            '''

            if won_opportunities:
                for lead in won_opportunities:
                    html += f'''
                                <tr>
                                    <td><strong>{lead.name}</strong></td>
                                    <td>{lead.partner_id.name if lead.partner_id else ''}</td>
                                    <td><strong class="text-success">${lead.expected_revenue:,.0f}</strong></td>
                                </tr>
                    '''
            else:
                html += '<tr><td colspan="3" class="text-center text-muted p-2"><em>No hay ganadas</em></td></tr>'

            html += '''
                            </tbody>
                        </table>
                    </div>
                    <div class="col-6">
                        <h5>Ultimas Perdidas (Top 5)</h5>
                        <table class="table table-sm table-danger">
                            <thead class="table-danger">
                                <tr>
                                    <th>Oportunidad</th>
                                    <th>Cliente</th>
                                    <th>Razon</th>
                                </tr>
                            </thead>
                            <tbody>
            '''

            if lost_opportunities:
                for lead in lost_opportunities:
                    html += f'''
                                <tr>
                                    <td><strong>{lead.name}</strong></td>
                                    <td>{lead.partner_id.name if lead.partner_id else ''}</td>
                                    <td><span class="badge bg-danger">{lead.lost_reason_id.name if lead.lost_reason_id else 'No especificada'}</span></td>
                                </tr>
                    '''
            else:
                html += '<tr><td colspan="3" class="text-center text-muted p-2"><em>No hay perdidas</em></td></tr>'

            html += '''
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            '''

            record.dashboard_data = html

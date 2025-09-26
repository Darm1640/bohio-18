from odoo import api, fields, models, tools
from datetime import datetime, timedelta
import json

class CrmDashboard(models.Model):
    _name = 'bohio.crm.dashboard'
    _description = 'CRM Dashboard Bohio'
    _auto = False
    _order = 'priority desc, id desc'

    name = fields.Char('Nombre')
    stage_id = fields.Many2one('crm.stage', 'Etapa')
    partner_id = fields.Many2one('res.partner', 'Cliente')
    user_id = fields.Many2one('res.users', 'Vendedor')
    property_id = fields.Many2one('product.template', 'Propiedad')
    expected_revenue = fields.Monetary('Ingreso Esperado', currency_field='company_currency_id')
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    company_id = fields.Many2one('res.company', 'Compañía', default=lambda self: self.env.company)
    probability = fields.Float('Probabilidad')
    date_deadline = fields.Date('Fecha Cierre Esperada')
    priority = fields.Selection([
        ('0', 'Baja'),
        ('1', 'Media'),
        ('2', 'Alta'),
        ('3', 'Muy Alta'),
    ], default='1', index=True, string="Prioridad")
    tag_ids = fields.Many2many('crm.tag', 'crm_tag_rel', 'lead_id', 'tag_id', string='Etiquetas')
    lead_type = fields.Selection([
        ('lead', 'Lead'),
        ('opportunity', 'Oportunidad')
    ], string='Tipo')
    active = fields.Boolean('Activo', default=True)

    # Campos calculados para el dashboard
    days_to_close = fields.Integer('Días para Cerrar', compute='_compute_days_to_close')
    stage_color = fields.Integer('Color Etapa', compute='_compute_stage_color')
    property_type = fields.Char('Tipo de Propiedad', compute='_compute_property_type')
    property_location = fields.Char('Ubicación', compute='_compute_property_location')

    @api.depends('date_deadline')
    def _compute_days_to_close(self):
        today = fields.Date.today()
        for record in self:
            if record.date_deadline:
                delta = record.date_deadline - today
                record.days_to_close = delta.days
            else:
                record.days_to_close = 0

    @api.depends('stage_id')
    def _compute_stage_color(self):
        for record in self:
            if record.stage_id:
                if record.stage_id.is_won:
                    record.stage_color = 10  # Verde
                elif not record.stage_id.fold:
                    if record.stage_id.sequence <= 1:
                        record.stage_color = 3  # Amarillo
                    elif record.stage_id.sequence <= 3:
                        record.stage_color = 2  # Azul
                    else:
                        record.stage_color = 4  # Púrpura
                else:
                    record.stage_color = 1  # Gris
            else:
                record.stage_color = 0

    @api.depends('property_id')
    def _compute_property_type(self):
        for record in self:
            if record.property_id and hasattr(record.property_id, 'property_type_id'):
                record.property_type = record.property_id.property_type_id.name or 'Sin tipo'
            else:
                record.property_type = 'Sin tipo'

    @api.depends('property_id')
    def _compute_property_location(self):
        for record in self:
            if record.property_id:
                location_parts = []
                if hasattr(record.property_id, 'neighborhood'):
                    if record.property_id.neighborhood:
                        location_parts.append(record.property_id.neighborhood)
                if hasattr(record.property_id, 'municipality'):
                    if record.property_id.municipality:
                        location_parts.append(record.property_id.municipality)
                record.property_location = ', '.join(location_parts) if location_parts else 'Sin ubicación'
            else:
                record.property_location = 'Sin ubicación'

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    l.id as id,
                    l.name as name,
                    l.stage_id as stage_id,
                    l.partner_id as partner_id,
                    l.user_id as user_id,
                    l.expected_revenue as expected_revenue,
                    l.company_id as company_id,
                    l.probability as probability,
                    l.date_deadline as date_deadline,
                    l.priority as priority,
                    l.type as lead_type,
                    l.active as active,
                    pt.id as property_id
                FROM crm_lead l
                LEFT JOIN product_template pt ON pt.partner_id = l.partner_id
                WHERE l.active = true
            )
        """ % self._table)

    @api.model
    def get_dashboard_data(self):
        """Obtener datos del dashboard para vista JavaScript"""
        # Leads por etapa
        stage_data = self.env['crm.lead'].read_group(
            [('active', '=', True)],
            ['stage_id', 'expected_revenue'],
            ['stage_id']
        )

        # Top vendedores
        user_data = self.env['crm.lead'].read_group(
            [('active', '=', True), ('user_id', '!=', False)],
            ['user_id', 'expected_revenue'],
            ['user_id'],
            limit=5,
            orderby='expected_revenue desc'
        )

        # Propiedades más vistas
        property_data = []
        if 'property_id' in self.env['crm.lead']._fields:
            property_data = self.env['crm.lead'].read_group(
                [('active', '=', True)],
                ['property_id', 'expected_revenue'],
                ['property_id'],
                limit=5,
                orderby='expected_revenue desc'
            )

        # Actividades próximas
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'crm.lead'),
            ('date_deadline', '>=', fields.Date.today()),
            ('date_deadline', '<=', fields.Date.today() + timedelta(days=7))
        ], limit=10)

        # Métricas generales
        leads = self.env['crm.lead'].search([('active', '=', True)])
        total_expected = sum(leads.mapped('expected_revenue'))
        won_leads = leads.filtered(lambda l: l.stage_id.is_won)
        total_won = sum(won_leads.mapped('expected_revenue'))

        return {
            'stages': stage_data,
            'top_sellers': user_data,
            'top_properties': property_data,
            'upcoming_activities': activities.read(['res_name', 'date_deadline', 'user_id', 'activity_type_id']),
            'metrics': {
                'total_leads': len(leads),
                'total_expected': total_expected,
                'total_won': total_won,
                'conversion_rate': (len(won_leads) / len(leads) * 100) if leads else 0,
                'avg_revenue': total_expected / len(leads) if leads else 0,
            }
        }
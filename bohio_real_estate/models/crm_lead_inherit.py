from odoo import models, fields, api
from datetime import timedelta


class CrmLeadBohio(models.Model):
    _inherit = 'crm.lead'

    # Campos adicionales para solicitudes inmobiliarias
    request_source = fields.Selection([
        ('website', 'Sitio Web'),
        ('contact_form', 'Formulario Contacto'),
        ('pqrs', 'PQRS'),
        ('property_inquiry', 'Consulta Propiedad'),
        ('whatsapp', 'WhatsApp'),
        ('phone', 'Teléfono'),
    ], string='Origen de Solicitud', tracking=True)

    client_type = fields.Selection([
        ('owner', 'Propietario'),
        ('tenant', 'Arrendatario'),
        ('buyer', 'Comprador'),
        ('seller', 'Vendedor'),
        ('investor', 'Inversionista'),
        ('other', 'Otro'),
    ], string='Tipo de Cliente', tracking=True)

    service_interested = fields.Selection([
        ('sale', 'Venta'),
        ('rent', 'Arriendo'),
        ('consign', 'Consignar Inmueble'),
        ('legal', 'Servicios Jurídicos'),
        ('marketing', 'Marketing Inmobiliario'),
        ('corporate', 'Negocios Corporativos'),
        ('valuation', 'Avalúos'),
    ], string='Servicio de Interés', tracking=True)

    property_ids = fields.Many2many(
        'product.template',
        string='Propiedades de Interés',
        domain=[('is_property', '=', True)],
        help='Propiedades consultadas por el cliente'
    )

    budget_min = fields.Monetary('Presupuesto Mínimo', currency_field='company_currency', tracking=True)
    budget_max = fields.Monetary('Presupuesto Máximo', currency_field='company_currency', tracking=True)

    desired_location = fields.Char('Ubicación Deseada', tracking=True)
    num_bedrooms_desired = fields.Integer('Habitaciones Deseadas', tracking=True)
    num_bathrooms_desired = fields.Integer('Baños Deseados', tracking=True)

    # PQRS específico
    pqrs_type = fields.Selection([
        ('petition', 'Petición'),
        ('complaint', 'Queja'),
        ('claim', 'Reclamo'),
        ('suggestion', 'Sugerencia'),
    ], string='Tipo PQRS')

    pqrs_status = fields.Selection([
        ('received', 'Recibido'),
        ('processing', 'En Proceso'),
        ('resolved', 'Resuelto'),
        ('closed', 'Cerrado'),
    ], string='Estado PQRS', default='received')

    response_deadline = fields.Datetime('Fecha Límite Respuesta', compute='_compute_response_deadline', store=True)

    # Campo computado para el contador de propiedades
    property_count = fields.Integer('Número de Propiedades', compute='_compute_property_count')

    properties_won_count = fields.Integer('Propiedades Ganadas', compute='_compute_properties_metrics', store=True)
    properties_lost_count = fields.Integer('Propiedades Perdidas', compute='_compute_properties_metrics', store=True)
    total_invoiced = fields.Monetary('Total Facturado', currency_field='company_currency', default=0.0)
    total_paid = fields.Monetary('Total Recaudado', currency_field='company_currency', default=0.0)
    total_pending = fields.Monetary('Total Pendiente', currency_field='company_currency', default=0.0)
    days_open = fields.Integer('Días Abierto', compute='_compute_days_open', store=True)
    monthly_target = fields.Monetary('Meta Mensual', currency_field='company_currency', default=0.0)
    monthly_revenue = fields.Monetary('Ingresos del Mes', currency_field='company_currency', default=0.0)
    monthly_progress = fields.Float('Progreso Mensual %', default=0.0)


    portal_visible = fields.Boolean(
        string='Visible en Portal Cliente',
        default=True,
        tracking=True,
        help='Si está marcado, el cliente podrá ver esta oportunidad en su portal'
    )

    portal_stage_name = fields.Char(
        string='Nombre de Etapa para Cliente',
        help='Nombre personalizado de la etapa que verá el cliente en el portal'
    )

    show_in_portal = fields.Boolean(
        string='Mostrar en Portal',
        compute='_compute_show_in_portal',
        store=True,
        help='Se calcula automáticamente según la etapa y visibilidad'
    )

    @api.depends('stage_id', 'portal_visible')
    def _compute_show_in_portal(self):
        for lead in self:
            if not lead.portal_visible:
                lead.show_in_portal = False
            elif lead.stage_id:
                portal_stages = ['new', 'qualified', 'proposition']
                lead.show_in_portal = lead.stage_id.fold == False and not lead.stage_id.is_won
            else:
                lead.show_in_portal = lead.portal_visible


    # Auto-asignación a equipo inmobiliario
    @api.model
    def create(self, vals):
        # Si viene del sitio web, no asignar vendedor específico
        if vals.get('request_source') in ['website', 'contact_form', 'pqrs', 'property_inquiry']:
            # Buscar equipo de ventas inmobiliario
            real_estate_team = self.env['crm.team'].search([
                '|',
                ('name', 'ilike', 'inmobiliaria'),
                ('name', 'ilike', 'real estate')
            ], limit=1)

            if real_estate_team:
                vals['team_id'] = real_estate_team.id
                # No asignar vendedor específico - queda en pool del equipo
                vals['user_id'] = False

        # Establecer tipo como oportunidad si es una consulta de propiedad
        if vals.get('request_source') == 'property_inquiry':
            vals['type'] = 'opportunity'

        return super().create(vals)

    @api.depends('pqrs_type', 'create_date')
    def _compute_response_deadline(self):
        for lead in self:
            if lead.pqrs_type and lead.create_date:
                # Plazos según tipo de PQRS (días hábiles)
                deadlines = {
                    'petition': 15,
                    'complaint': 15,
                    'claim': 15,
                    'suggestion': 30,
                }
                days = deadlines.get(lead.pqrs_type, 15)
                lead.response_deadline = fields.Datetime.from_string(lead.create_date) + timedelta(days=days)
            else:
                lead.response_deadline = False

    @api.depends('property_ids')
    def _compute_property_count(self):
        for lead in self:
            lead.property_count = len(lead.property_ids)

    @api.depends('property_ids', 'stage_id')
    def _compute_properties_metrics(self):
        for lead in self:
            if lead.stage_id and lead.stage_id.is_won:
                lead.properties_won_count = len(lead.property_ids)
                lead.properties_lost_count = 0
            elif lead.stage_id and lead.stage_id.fold:
                lead.properties_won_count = 0
                lead.properties_lost_count = len(lead.property_ids)
            else:
                lead.properties_won_count = 0
                lead.properties_lost_count = 0

    def update_invoiced_amounts(self):
        self.ensure_one()
        if self.partner_id:
            self.env.cr.execute("""
                SELECT
                    COALESCE(SUM(CASE WHEN state = 'posted' THEN amount_total ELSE 0 END), 0) as invoiced,
                    COALESCE(SUM(CASE WHEN payment_state = 'paid' THEN amount_total ELSE 0 END), 0) as paid
                FROM account_move
                WHERE partner_id = %s
                  AND move_type IN ('out_invoice', 'out_refund')
                  AND state != 'cancel'
            """, (self.partner_id.id,))
            result = self.env.cr.fetchone()
            self.total_invoiced = result[0] if result else 0.0
            self.total_paid = result[1] if result else 0.0
            self.total_pending = self.total_invoiced - self.total_paid

    @api.depends('create_date')
    def _compute_days_open(self):
        today = fields.Datetime.now()
        for lead in self:
            if lead.create_date:
                delta = today - lead.create_date
                lead.days_open = delta.days
            else:
                lead.days_open = 0

    def update_monthly_metrics(self):
        self.ensure_one()
        if self.team_id:
            self.monthly_target = self.team_id.invoiced_target or 0.0

            today = fields.Date.today()
            first_day = today.replace(day=1)

            self.env.cr.execute("""
                SELECT COALESCE(SUM(l.expected_revenue), 0)
                FROM crm_lead l
                INNER JOIN crm_stage s ON l.stage_id = s.id
                WHERE l.team_id = %s
                  AND s.is_won = true
                  AND l.date_closed >= %s
                  AND l.date_closed <= %s
            """, (self.team_id.id, first_day, today))
            result = self.env.cr.fetchone()
            self.monthly_revenue = result[0] if result else 0.0

            if self.monthly_target > 0:
                self.monthly_progress = (self.monthly_revenue / self.monthly_target) * 100
            else:
                self.monthly_progress = 0.0

    def action_view_properties(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Propiedades de Interés',
            'view_mode': 'kanban,list,form',
            'res_model': 'product.template',
            'domain': [('id', 'in', self.property_ids.ids)],
            'context': {'create': False}
        }

    @api.model
    def _read_group(self, domain, groupby=(), aggregates=(), having=(), offset=0, limit=None, order=None):
        result = super()._read_group(domain, groupby, aggregates, having, offset, limit, order)

        groupby_list = list(groupby)
        if not groupby_list:
            return result

        first_groupby = groupby_list[0]
        groupby_field = first_groupby.fname if hasattr(first_groupby, 'fname') else str(first_groupby)

        if groupby_field == 'stage_id':
            for group_data in result:
                if isinstance(group_data, dict):
                    stage_value = group_data.get('stage_id')
                    stage_id = stage_value[0] if isinstance(stage_value, tuple) else stage_value

                    if not stage_id:
                        continue

                    stage_domain = [('stage_id', '=', stage_id)] + domain
                    leads_in_stage = self.search(stage_domain)

                    group_data['__kanban_dashboard'] = {
                        'properties_won': sum(leads_in_stage.mapped('properties_won_count')),
                        'properties_lost': sum(leads_in_stage.mapped('properties_lost_count')),
                        'total_invoiced': sum(leads_in_stage.mapped('total_invoiced')),
                        'total_paid': sum(leads_in_stage.mapped('total_paid')),
                        'monthly_target': leads_in_stage[0].monthly_target if leads_in_stage else 0.0,
                        'monthly_revenue': leads_in_stage[0].monthly_revenue if leads_in_stage else 0.0,
                        'monthly_progress': leads_in_stage[0].monthly_progress if leads_in_stage else 0.0,
                    }

        return result
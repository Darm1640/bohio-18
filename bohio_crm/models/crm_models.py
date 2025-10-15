from odoo import models, fields, api, _, tools
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json


class CrmLead(models.Model):
    """CRM Lead con extensiones para negocio inmobiliario"""
    _inherit = 'crm.lead'

    # ===============================
    # CAMPOS PRINCIPALES
    # ===============================

    # Campo Virtual para Toggle de Mapa
    show_map_location = fields.Boolean(
        string='Mostrar Ubicación en Mapa',
        default=True,
        help='Controla la visualización de la ubicación genérica en el mapa'
    )

    # Origen de solicitud (de bohio_real_estate)
    request_source = fields.Selection([
        ('website', 'Sitio Web'),
        ('contact_form', 'Formulario Contacto'),
        ('pqrs', 'PQRS'),
        ('property_inquiry', 'Consulta Propiedad'),
        ('whatsapp', 'WhatsApp'),
        ('phone', 'Teléfono'),
    ], string='Origen de Solicitud', tracking=True)

    # Información del cliente
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
        ('projects', 'Proyectos'),
        ('consign', 'Consignar Inmueble'),
        ('legal', 'Servicios Jurídicos'),
        ('marketing', 'Marketing Inmobiliario'),
        ('corporate', 'Negocios Corporativos'),
        ('valuation', 'Avalúos'),
    ], string='Servicio de Interés', tracking=True)

    referred_by_partner_id = fields.Many2one('res.partner', 'Referido Por', tracking=True)
    project_id = fields.Many2one('project.worksite', 'Proyecto Inmobiliario', tracking=True)

    # Propiedades
    compared_properties_ids = fields.Many2many(
        'product.template', 'crm_lead_property_compare_rel', 'lead_id', 'property_id',
        string='Propiedades a Comparar', domain="[('is_property', '=', True), ('state', '=', 'free')]",
        help='Máximo 4 propiedades para comparar'
    )
    property_ids = fields.Many2many(
        'product.template', 'crm_lead_property_interest_rel', 'lead_id', 'property_id',
        string='Propiedades de Interés', domain=[('is_property', '=', True)]
    )

    # Preferencias de búsqueda
    budget_min = fields.Monetary('Presupuesto Mínimo', currency_field='company_currency', tracking=True)
    budget_max = fields.Monetary('Presupuesto Máximo', currency_field='company_currency', tracking=True)
    desired_neighborhood = fields.Char('Barrio Deseado', tracking=True)
    desired_city = fields.Char('Ciudad Deseada', tracking=True)
    desired_property_type_id = fields.Many2one('property.type', 'Tipo de Propiedad Deseada', tracking=True)

    # Habitaciones
    min_bedrooms = fields.Integer('Habitaciones Mínimas', tracking=True)
    max_bedrooms = fields.Integer('Habitaciones Máximas', tracking=True)
    ideal_bedrooms = fields.Integer('Habitaciones Ideales', tracking=True)

    # Baños
    min_bathrooms = fields.Integer('Baños Mínimos', tracking=True)
    max_bathrooms = fields.Integer('Baños Máximos', tracking=True)

    # Área
    min_area = fields.Float('Área Mínima (m²)', tracking=True)
    max_area = fields.Float('Área Máxima (m²)', tracking=True)

    # Información adicional
    number_of_occupants = fields.Integer('Número de Ocupantes', tracking=True)
    has_pets = fields.Boolean('Tiene Mascotas', tracking=True)
    pet_type = fields.Selection([
        ('dog', 'Perro'), ('cat', 'Gato'), ('both', 'Perro y Gato'), ('other', 'Otra Mascota')
    ], string='Tipo de Mascota', tracking=True)
    requires_parking = fields.Boolean('Requiere Parqueadero', tracking=True)
    parking_spots = fields.Integer('Número de Parqueaderos', tracking=True, default=1)
    occupation = fields.Char('Ocupación', tracking=True)
    monthly_income = fields.Monetary('Ingresos Mensuales', tracking=True, currency_field='company_currency')

    # Amenidades
    requires_common_areas = fields.Boolean('Requiere Zonas Comunes', tracking=True)
    requires_gym = fields.Boolean('Requiere Gimnasio', tracking=True)
    requires_pool = fields.Boolean('Requiere Piscina', tracking=True)
    requires_security = fields.Boolean('Requiere Seguridad 24/7', tracking=True)
    requires_elevator = fields.Boolean('Requiere Ascensor', tracking=True)

    property_purpose = fields.Selection([
        ('residence', 'Vivienda Permanente'),
        ('office', 'Oficina/Comercial'),
        ('vacation', 'Vacacional'),
        ('investment', 'Inversión'),
    ], string='Propósito del Inmueble', tracking=True)
    is_for_office = fields.Boolean('Para Uso Comercial/Oficina', tracking=True)
    is_for_vacation = fields.Boolean('Para Uso Vacacional', tracking=True)

    # ===============================
    # CAMPOS DE MARKETING
    # ===============================
    marketing_campaign_type = fields.Selection([
        ('social_media', 'Redes Sociales'),
        ('google_ads', 'Google Ads'),
        ('facebook_ads', 'Facebook Ads'),
        ('instagram_ads', 'Instagram Ads'),
        ('email_marketing', 'Email Marketing'),
        ('print_media', 'Medios Impresos'),
        ('outdoor', 'Publicidad Exterior (Vallas)'),
        ('radio_tv', 'Radio/TV'),
        ('property_portals', 'Portales Inmobiliarios'),
        ('event', 'Eventos/Ferias'),
        ('other', 'Otro'),
    ], string='Tipo de Campaña', tracking=True)

    marketing_quantity = fields.Integer('Cantidad de Publicaciones/Anuncios', tracking=True,
                                       help='Número de publicaciones, anuncios o impresiones')

    marketing_schedule = fields.Selection([
        ('morning', 'Mañana (6am - 12pm)'),
        ('afternoon', 'Tarde (12pm - 6pm)'),
        ('evening', 'Noche (6pm - 12am)'),
        ('full_day', 'Todo el día'),
        ('weekend', 'Fin de semana'),
        ('business_hours', 'Horario laboral'),
    ], string='Horario Preferido para Publicidad', tracking=True)

    marketing_estimated_reach = fields.Integer('Personas Estimadas a Alcanzar', tracking=True,
                                              help='Estimación de audiencia o alcance')

    marketing_budget_allocated = fields.Monetary('Presupuesto Asignado al Marketing',
                                                 currency_field='company_currency', tracking=True)

    marketing_start_date = fields.Date('Fecha Inicio de Campaña', tracking=True)
    marketing_end_date = fields.Date('Fecha Fin de Campaña', tracking=True)

    marketing_description = fields.Text('Descripción de la Campaña',
                                       help='Objetivos, público objetivo, mensaje clave, etc.')

    # ===============================
    # CAMPOS DE CAPTACIÓN (CONSIGNACIÓN)
    # ===============================
    captured_by_id = fields.Many2one('res.users', 'Captado Por', tracking=True,
                                    help='Vendedor o asesor que consiguió el inmueble')

    capture_date = fields.Date('Fecha de Captación', tracking=True,
                              default=fields.Date.context_today)

    capture_source = fields.Selection([
        ('referral', 'Referido'),
        ('cold_call', 'Llamada en Frío'),
        ('door_to_door', 'Puerta a Puerta'),
        ('website', 'Sitio Web'),
        ('social_media', 'Redes Sociales'),
        ('advertising', 'Publicidad'),
        ('existing_client', 'Cliente Existente'),
        ('other', 'Otro'),
    ], string='Fuente de Captación', tracking=True)

    capture_commission_rate = fields.Float('% Comisión de Captación', tracking=True,
                                          default=2.0,
                                          help='Porcentaje de comisión para quien captó')

    capture_commission_amount = fields.Monetary('Monto Comisión Captación',
                                               currency_field='company_currency',
                                               compute='_compute_capture_commission',
                                               store=True)

    # ===============================
    # CAMPOS DE PRÉSTAMO/FINANCIACIÓN
    # ===============================
    requires_financing = fields.Boolean('Requiere Financiación', tracking=True)

    loan_type = fields.Selection([
        ('bank_mortgage', 'Hipoteca Bancaria'),
        ('developer_financing', 'Financiación Constructora'),
        ('leasing', 'Leasing Habitacional'),
        ('subsidized', 'Vivienda Subsidiada'),
        ('other', 'Otro'),
    ], string='Tipo de Préstamo/Financiación', tracking=True)

    loan_amount = fields.Monetary('Monto del Préstamo', currency_field='company_currency', tracking=True)

    loan_bank_id = fields.Many2one('res.partner', 'Entidad Financiera',
                                   domain=[('is_company', '=', True)],
                                   tracking=True)

    loan_approval_status = fields.Selection([
        ('not_applied', 'No Solicitado'),
        ('pending', 'En Estudio'),
        ('pre_approved', 'Pre-aprobado'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
    ], string='Estado de Aprobación', default='not_applied', tracking=True)

    loan_document_ids = fields.Many2many('ir.attachment', 'crm_lead_loan_doc_rel',
                                        'lead_id', 'attachment_id',
                                        string='Documentos para Estudio',
                                        help='Certificados laborales, extractos, declaraciones, etc.')

    # ===============================
    # CAMPOS DE RESERVA
    # ===============================
    reservation_id = fields.Many2one('property.reservation', 'Reserva Asociada',
                                    tracking=True, readonly=True)

    reservation_count = fields.Integer('# Reservas', compute='_compute_reservation_count')

    ideal_visit_date = fields.Datetime('Fecha Ideal para Visita', tracking=True)

    visit_notes = fields.Text('Notas de Visita',
                             help='Preferencias de horario, personas que asistirán, etc.')

    has_conflicting_visit = fields.Boolean('Hay Otra Visita', compute='_compute_conflicting_visit',
                                          help='Indica si hay otra visita programada para la misma propiedad')

    conflicting_visit_info = fields.Char('Información de Conflicto', compute='_compute_conflicting_visit')

    # ===============================
    # TEMPLATE DE CONTRATO
    # ===============================
    contract_template_id = fields.Many2one('property.contract.type', 'Template de Contrato',
                                          tracking=True,
                                          help='Tipo de contrato a usar para esta oportunidad')

    # Información contractual
    contract_start_date = fields.Date('Fecha Inicio Estimada', tracking=True)
    contract_duration_months = fields.Integer('Duración Estimada (meses)', tracking=True)
    contract_end_date = fields.Date('Fecha Fin Estimada', compute='_compute_contract_end_date', store=True)
    commission_percentage = fields.Float('% Comisión', default=10.0)

    # Geolocalización (basado en propiedades de interés)
    partner_latitude = fields.Float(string='Latitud', compute='_compute_location', store=True)
    partner_longitude = fields.Float(string='Longitud', compute='_compute_location', store=True)

    # ===============================
    # MÉTODOS COMPUTADOS
    # ===============================

    @api.depends('property_ids', 'property_ids.latitude', 'property_ids.longitude')
    def _compute_location(self):
        """Calcular ubicación promedio basada en propiedades de interés"""
        for lead in self:
            properties_with_location = lead.property_ids.filtered(lambda p: p.latitude and p.longitude)

            if properties_with_location:
                # Calcular promedio de latitud y longitud
                lead.partner_latitude = sum(p.latitude for p in properties_with_location) / len(properties_with_location)
                lead.partner_longitude = sum(p.longitude for p in properties_with_location) / len(properties_with_location)
            else:
                # Si no hay propiedades, usar ubicación del partner si existe
                lead.partner_latitude = lead.partner_id.partner_latitude if lead.partner_id else 0.0
                lead.partner_longitude = lead.partner_id.partner_longitude if lead.partner_id else 0.0

    # ===============================
    # MÉTODOS PARA TIMELINE VIEW
    # ===============================

    def action_open_timeline_view(self):
        """Abrir vista timeline para esta oportunidad"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'bohio_timeline_view',
            'name': f'Timeline - {self.name}',
            'context': {
                'active_id': self.id,
                'active_model': 'crm.lead',
            },
            'target': 'current',
        }

    def get_timeline_view_data(self):
        """Obtener datos para la vista timeline"""
        self.ensure_one()

        # Obtener historial de etapas
        stage_history = self._get_stage_history()

        # Obtener propiedades recomendadas
        recommended_properties = self._get_ai_recommendations()

        # Obtener propiedades en comparación
        comparison_properties = self._get_comparison_properties()

        # Obtener actividades pendientes
        activities = self._get_pending_activities()

        # Calcular métricas
        recurring_revenue = self.recurring_revenue if hasattr(self, 'recurring_revenue') else 0
        total_revenue = self.expected_revenue + (recurring_revenue * 12)
        commission_amount = total_revenue * (self.commission_percentage / 100)

        return {
            'id': self.id,
            'name': self.name,
            'partner_id': [self.partner_id.id, self.partner_id.name] if self.partner_id else [False, ''],
            'partner_name': self.partner_name or self.partner_id.name or '',
            'partner_initials': self._get_partner_initials(),
            'phone': self.phone or self.partner_id.phone or '',
            'partner_phone': self.partner_id.phone or '',
            'email': self.email_from or self.partner_id.email or '',
            'partner_vat': self.partner_id.vat or '',

            # Tipo de cliente y servicio
            'client_type': self.client_type or '',
            'customer_type': dict(self._fields['client_type'].selection).get(self.client_type, ''),
            'service_interested': self.service_interested or '',
            'referral_partner': self.referred_by_partner_id.name if self.referred_by_partner_id else '',
            'user_name': self.user_id.name if self.user_id else '',

            # Información completa del cliente
            'client_info': {
                'is_company': self.partner_id.is_company if self.partner_id else False,
                'street': self.partner_id.street or '',
                'street2': self.partner_id.street2 or '',
                'city': self.partner_id.city or '',
                'state_id': self.partner_id.state_id.name if self.partner_id and self.partner_id.state_id else '',
                'country_id': self.partner_id.country_id.name if self.partner_id and self.partner_id.country_id else '',
                'zip': self.partner_id.zip or '',
                # Contactos secundarios si es empresa
                'contacts': [
                    {
                        'id': contact.id,
                        'name': contact.name,
                        'function': contact.function or '',
                        'phone': contact.phone or contact.mobile or '',
                        'email': contact.email or '',
                    }
                    for contact in self.partner_id.child_ids[:5]
                ] if self.partner_id and self.partner_id.is_company else [],
            },

            # Presupuesto
            'min_budget': self.budget_min or 0,
            'max_budget': self.budget_max or 0,
            'min_budget_formatted': self._format_currency(self.budget_min),
            'max_budget_formatted': self._format_currency(self.budget_max),

            # Preferencias de propiedad
            'desired_city': self.desired_city or '',
            'desired_neighborhood': self.desired_neighborhood or '',
            'desired_property_type': self.desired_property_type_id.name if self.desired_property_type_id else '',
            'min_bedrooms': self.min_bedrooms or 0,
            'ideal_bedrooms': self.ideal_bedrooms or 0,
            'min_bathrooms': self.min_bathrooms or 0,
            'min_area': self.min_area or 0,
            'max_area': self.max_area or 0,
            'project_name': self.project_id.name if self.project_id else '',

            # Información adicional
            'number_of_occupants': self.number_of_occupants or 0,
            'has_pets': self.has_pets,
            'pet_type': self.pet_type or '',
            'requires_parking': self.requires_parking,
            'parking_spots': self.parking_spots or 1,
            'occupation': self.occupation or '',
            'monthly_income': self.monthly_income or 0,
            'monthly_income_formatted': self._format_currency(self.monthly_income),

            # Amenidades
            'requires_common_areas': self.requires_common_areas,
            'requires_gym': self.requires_gym,
            'requires_pool': self.requires_pool,
            'requires_security': self.requires_security,
            'requires_elevator': self.requires_elevator,
            'property_purpose': self.property_purpose or '',

            # Información contractual
            'contract_start_date': self.contract_start_date.strftime('%Y-%m-%d') if self.contract_start_date else '',
            'contract_duration_months': self.contract_duration_months or 0,
            'commission_percentage': self.commission_percentage or 10.0,

            # Métricas
            'expected_revenue': self.expected_revenue,
            'expected_revenue_formatted': self._format_currency(self.expected_revenue),
            'recurring_revenue': recurring_revenue,
            'recurring_revenue_formatted': self._format_currency(recurring_revenue),
            'total_revenue': total_revenue,
            'commission_percent': self.commission_percentage,
            'commission_amount': commission_amount,
            'probability': self.probability,
            'days_in_pipeline': self._compute_days_in_pipeline(),
            'ai_score': self._calculate_ai_score(),

            # Estado
            'stage_is_won': self.stage_id.is_won if self.stage_id else False,
            'stage_history': stage_history,
            'recommended_properties': recommended_properties,
            'comparison_properties': comparison_properties,
            'activities': activities,
        }

    def _get_partner_initials(self):
        """Obtener iniciales del contacto"""
        if not self.partner_name and not self.partner_id:
            return 'NN'
        name = self.partner_name or self.partner_id.name
        parts = name.split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        return name[0:2].upper()

    def _format_currency(self, amount):
        """Formatear moneda"""
        if not amount:
            return '$0'
        return f"${amount:,.0f}"

    def _get_stage_history(self):
        """Obtener historial de etapas con iconos y tiempos"""
        stages = self.env['crm.stage'].search([('team_id', '=', False)], order='sequence')
        current_stage_sequence = self.stage_id.sequence if self.stage_id else 0

        history = []
        for stage in stages:
            # Calcular días en esta etapa (simplificado)
            days_in_stage = 0
            days_label = '-'

            is_completed = stage.sequence < current_stage_sequence
            is_current = stage.id == self.stage_id.id

            if is_completed:
                days_label = f"{days_in_stage or 3} días"
            elif is_current:
                days_label = f"{days_in_stage or 7} días actual"

            # Mapeo de iconos por etapa
            icon_map = {
                'new': 'star',
                'qualified': 'check-circle',
                'proposition': 'file-text',
                'negotiation': 'handshake',
                'won': 'trophy',
            }

            history.append({
                'id': stage.id,
                'name': stage.name,
                'sequence': stage.sequence,
                'is_completed': is_completed,
                'is_current': is_current,
                'days_label': days_label,
                'days_remaining': 3 if is_current else None,
                'icon': icon_map.get(stage.fold, 'circle'),
            })

        return history

    def _get_property_price_info(self, prop):
        """Obtener precio de propiedad según tipo de servicio"""
        if self.service_interested == 'rent':
            price = prop.rent_value_from if hasattr(prop, 'rent_value_from') else prop.list_price
            return {
                'price': price,
                'price_formatted': self._format_currency(price),
                'price_label': 'Arriendo/mes',
                'price_field': 'rent_value_from',
            }
        elif self.service_interested == 'sale':
            price = prop.sale_value_from if hasattr(prop, 'sale_value_from') else prop.list_price
            return {
                'price': price,
                'price_formatted': self._format_currency(price),
                'price_label': 'Venta',
                'price_field': 'sale_value_from',
            }
        else:
            return {
                'price': prop.list_price,
                'price_formatted': self._format_currency(prop.list_price),
                'price_label': 'Precio',
                'price_field': 'list_price',
            }

    def _get_ai_recommendations(self):
        """Obtener propiedades recomendadas por IA (simplificado)"""
        properties = self.env['product.template'].search([
            ('is_property', '=', True),
            ('state', '=', 'free'),
        ], limit=4)

        result = []
        for idx, prop in enumerate(properties):
            # Score simulado (en producción sería calculado por IA)
            match_score = 95 - (idx * 3)

            # Obtener precio según tipo de servicio
            price_info = self._get_property_price_info(prop)

            result.append({
                'id': prop.id,
                'name': prop.name,
                'area': prop.property_area if hasattr(prop, 'property_area') else 0,
                'price': price_info['price'],
                'price_formatted': price_info['price_formatted'],
                'price_label': price_info['price_label'],
                'bedrooms': prop.bedroom_count if hasattr(prop, 'bedroom_count') else 0,
                'bathrooms': prop.bathroom_count if hasattr(prop, 'bathroom_count') else 0,
                'neighborhood': prop.neighborhood if hasattr(prop, 'neighborhood') else '',
                'view_type': 'Vista Mar',
                'match_score': match_score,
            })

        return result

    def _get_comparison_properties(self):
        """Obtener propiedades en comparación"""
        result = []
        for prop in self.compared_properties_ids:
            # Obtener precio según tipo de servicio
            price_info = self._get_property_price_info(prop)

            result.append({
                'id': prop.id,
                'name': prop.name,
                'area': prop.property_area if hasattr(prop, 'property_area') else 0,
                'price': price_info['price'],
                'price_formatted': price_info['price_formatted'],
                'price_label': price_info['price_label'],
                'bedrooms': prop.bedroom_count if hasattr(prop, 'bedroom_count') else 0,
                'bathrooms': prop.bathroom_count if hasattr(prop, 'bathroom_count') else 0,
                'floor': 'Piso 5',
                'view_type': 'Vista mar',
                'is_selected': prop == self.compared_properties_ids[0] if self.compared_properties_ids else False,
            })
        return result

    def _get_pending_activities(self):
        """Obtener actividades pendientes"""
        activities = self.env['mail.activity'].search([
            ('res_id', '=', self.id),
            ('res_model', '=', 'crm.lead'),
        ], order='date_deadline')

        result = []
        for activity in activities:
            result.append({
                'id': activity.id,
                'summary': activity.summary or activity.activity_type_id.name,
                'user_name': activity.user_id.name,
                'date_deadline': activity.date_deadline.strftime('%d/%m/%Y') if activity.date_deadline else '',
                'activity_state': activity.state,
            })
        return result

    def _compute_days_in_pipeline(self):
        """Calcular días en el pipeline"""
        if not self.create_date:
            return 0
        delta = datetime.now() - self.create_date
        return delta.days

    def _calculate_ai_score(self):
        """Calcular score de IA (simplificado)"""
        score = 50
        if self.probability:
            score += self.probability * 0.3
        if self.expected_revenue:
            score += 10
        if self.partner_id:
            score += 10
        return min(int(score), 100)

    def get_ai_recommendations(self):
        """Actualizar recomendaciones de IA"""
        self.ensure_one()
        return self._get_ai_recommendations()

    def add_property_to_comparison(self, property_id):
        """Agregar propiedad a comparación"""
        self.ensure_one()
        if len(self.compared_properties_ids) >= 4:
            raise ValidationError(_('Solo se pueden comparar hasta 4 propiedades'))

        property_obj = self.env['product.template'].browse(property_id)
        self.compared_properties_ids = [(4, property_obj.id)]
        return True

    def remove_property_from_comparison(self, property_id):
        """Remover propiedad de comparación"""
        self.ensure_one()
        self.compared_properties_ids = [(3, property_id)]
        return True

    # PQRS
    pqrs_type = fields.Selection([
        ('petition', 'Petición'), ('complaint', 'Queja'), ('claim', 'Reclamo'), ('suggestion', 'Sugerencia')
    ], string='Tipo PQRS')
    pqrs_description = fields.Text('Descripción PQRS', tracking=True)
    pqrs_status = fields.Selection([
        ('received', 'Recibido'), ('processing', 'En Proceso'), ('resolved', 'Resuelto'), ('closed', 'Cerrado')
    ], string='Estado PQRS', default='received')
    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket Helpdesk')
    response_deadline = fields.Datetime('Fecha Límite Respuesta', compute='_compute_response_deadline', store=True)

    # Portal
    portal_visible = fields.Boolean('Visible en Portal', default=True, tracking=True)
    show_in_portal = fields.Boolean('Mostrar en Portal', compute='_compute_show_in_portal', store=True)

    # Recomendaciones
    recommended_properties_ids = fields.Many2many(
        'product.template',
        'crm_lead_property_recommended_rel',
        'lead_id',
        'property_id',
        string='Propiedades Recomendadas',
        compute='_compute_recommended_properties',
        store=False
    )
    recommendation_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('generated', 'Generadas'),
        ('viewed', 'Vistas por Cliente'),
        ('selected', 'Cliente Seleccionó'),
    ], string='Estado Recomendaciones', default='pending', tracking=True)
    recommendation_count = fields.Integer('Número de Recomendaciones', compute='_compute_recommendation_count', store=True)

    # ===============================
    # CAMPOS CALCULADOS
    # ===============================

    compared_properties_count = fields.Integer('Cantidad en Comparación', compute='_compute_compared_properties_count', store=True)
    can_add_property = fields.Boolean('Puede Agregar Propiedad', compute='_compute_compared_properties_count', store=True)
    estimated_monthly_rent = fields.Monetary('Canon Mensual Estimado', currency_field='company_currency', compute='_compute_estimated_amounts', store=True)
    estimated_total_amount = fields.Monetary('Monto Total Estimado', compute='_compute_estimated_amounts', currency_field='company_currency', store=True)
    estimated_commission = fields.Monetary('Comisión Estimada', compute='_compute_estimated_amounts', currency_field='company_currency', store=True)

    # Métricas financieras
    contract_id = fields.Many2one('property.contract', 'Contrato Generado', readonly=True)
    total_invoiced = fields.Monetary('Total Facturado', currency_field='company_currency', compute='_compute_financial_metrics', store=True)
    total_credit_notes = fields.Monetary('Notas de Crédito', currency_field='company_currency', compute='_compute_financial_metrics', store=True)
    net_invoiced = fields.Monetary('Facturación Neta', currency_field='company_currency', compute='_compute_financial_metrics', store=True)
    total_paid = fields.Monetary('Total Pagado', currency_field='company_currency', compute='_compute_financial_metrics', store=True)
    total_pending = fields.Monetary('Total Pendiente', currency_field='company_currency', compute='_compute_financial_metrics', store=True)
    payment_percentage = fields.Float('% Pagado', compute='_compute_financial_metrics', store=True)

    # Dashboard
    kanban_dashboard = fields.Text(compute='_compute_kanban_dashboard')
    dashboard_data = fields.Json('Dashboard Data', compute='_compute_dashboard_data')
    property_recommendations_data = fields.Json('Recommendations Data', compute='_compute_property_recommendations_data')
    comparison_data = fields.Json('Comparison Data', compute='_compute_comparison_data')

    # Campos adicionales para métricas
    partner_contracts_count = fields.Integer('Cantidad de Contratos', compute='_compute_partner_contracts_count', store=True)
    partner_active_contracts_count = fields.Integer('Contratos Activos', compute='_compute_partner_contracts_count', store=True)
    days_to_close = fields.Integer('Días para Cierre', compute='_compute_days_to_close', store=True)
    days_open = fields.Integer('Días Abierto', compute='_compute_days_open', store=True)

    # ===============================
    # MÉTODOS CALCULADOS
    # ===============================

    @api.depends('compared_properties_ids')
    def _compute_compared_properties_count(self):
        for lead in self:
            count = len(lead.compared_properties_ids)
            lead.compared_properties_count = count
            lead.can_add_property = count < 4

    @api.depends('contract_start_date', 'contract_duration_months')
    def _compute_contract_end_date(self):
        for lead in self:
            if lead.contract_start_date and lead.contract_duration_months:
                lead.contract_end_date = lead.contract_start_date + relativedelta(months=lead.contract_duration_months)
            else:
                lead.contract_end_date = False

    @api.depends('budget_min', 'budget_max', 'contract_duration_months', 'commission_percentage', 'service_interested')
    def _compute_estimated_amounts(self):
        for lead in self:
            if lead.service_interested == 'rent':
                budget_avg = ((lead.budget_min or 0) + (lead.budget_max or 0)) / 2 if lead.budget_max else lead.budget_min or 0
                lead.estimated_monthly_rent = budget_avg
                if lead.contract_duration_months:
                    lead.estimated_total_amount = budget_avg * lead.contract_duration_months
                    lead.estimated_commission = lead.estimated_total_amount * (lead.commission_percentage / 100)
                else:
                    lead.estimated_total_amount = budget_avg
                    lead.estimated_commission = 0.0
            elif lead.service_interested == 'sale':
                budget_avg = ((lead.budget_min or 0) + (lead.budget_max or 0)) / 2 if lead.budget_max else lead.budget_min or 0
                lead.estimated_monthly_rent = 0.0
                lead.estimated_total_amount = budget_avg
                lead.estimated_commission = budget_avg * (lead.commission_percentage / 100)
            else:
                lead.estimated_monthly_rent = 0.0
                lead.estimated_total_amount = 0.0
                lead.estimated_commission = 0.0

    @api.depends('stage_id', 'portal_visible')
    def _compute_show_in_portal(self):
        for lead in self:
            if not lead.portal_visible:
                lead.show_in_portal = False
            elif lead.stage_id:
                lead.show_in_portal = lead.stage_id.fold == False and not lead.stage_id.is_won
            else:
                lead.show_in_portal = lead.portal_visible

    @api.depends('pqrs_type', 'create_date')
    def _compute_response_deadline(self):
        for lead in self:
            if lead.pqrs_type and lead.create_date:
                deadlines = {'petition': 15, 'complaint': 15, 'claim': 15, 'suggestion': 30}
                days = deadlines.get(lead.pqrs_type, 15)
                lead.response_deadline = fields.Datetime.from_string(lead.create_date) + timedelta(days=days)
            else:
                lead.response_deadline = False

    @api.depends('partner_id', 'contract_id')
    def _compute_financial_metrics(self):
        AccountMove = self.env['account.move']
        for lead in self:
            if not lead.partner_id:
                lead.update({
                    'total_invoiced': 0.0, 'total_credit_notes': 0.0, 'net_invoiced': 0.0,
                    'total_paid': 0.0, 'total_pending': 0.0, 'payment_percentage': 0.0
                })
                continue

            invoices = AccountMove.search_read(
                domain=[('partner_id', '=', lead.partner_id.id), ('state', '=', 'posted')],
                fields=['amount_total', 'amount_residual', 'move_type', 'payment_state']
            )

            total_inv = sum(inv['amount_total'] for inv in invoices if inv['move_type'] == 'out_invoice')
            total_credit = sum(inv['amount_total'] for inv in invoices if inv['move_type'] == 'out_refund')
            net_inv = total_inv - total_credit
            total_pending = sum(inv['amount_residual'] for inv in invoices if inv['move_type'] == 'out_invoice')
            total_paid = total_inv - total_pending

            lead.update({
                'total_invoiced': total_inv,
                'total_credit_notes': total_credit,
                'net_invoiced': net_inv,
                'total_paid': total_paid,
                'total_pending': total_pending,
                'payment_percentage': (total_paid / total_inv * 100) if total_inv > 0 else 0.0
            })

    def _compute_kanban_dashboard(self):
        for lead in self:
            dashboard_data = self.get_crm_dashboard_data(show_all=False, period='month', service_filter='all')
            lead.kanban_dashboard = json.dumps(dashboard_data)

    @api.depends('partner_id', 'service_interested', 'estimated_total_amount', 'days_open', 'compared_properties_count')
    def _compute_dashboard_data(self):
        """Calcular datos para dashboard estilizado"""
        for lead in self:
            # Datos principales del lead
            lead_data = {
                'client_info': {
                    'name': lead.partner_id.name if lead.partner_id else 'Cliente Potencial',
                    'type': dict(lead._fields['client_type'].selection).get(lead.client_type, 'No definido') if lead.client_type else 'No definido',
                    'service': dict(lead._fields['service_interested'].selection).get(lead.service_interested, 'No definido') if lead.service_interested else 'No definido',
                },
                'financial_info': {
                    'estimated_amount': lead.estimated_total_amount or 0,
                    'estimated_commission': lead.estimated_commission or 0,
                    'budget_range': f"${lead.budget_min:,.0f} - ${lead.budget_max:,.0f}" if lead.budget_min and lead.budget_max else 'No definido',
                },
                'metrics': {
                    'days_open': lead.days_open,
                    'days_to_close': lead.days_to_close,
                    'probability': lead.probability,
                    'contracts_count': lead.partner_contracts_count,
                    'compared_properties': lead.compared_properties_count,
                },
                'preferences': {
                    'neighborhood': lead.desired_neighborhood or 'Cualquiera',
                    'property_type': lead.desired_property_type_id.name if lead.desired_property_type_id else 'Cualquiera',
                    'bedrooms': f"{lead.num_bedrooms_min}-{lead.num_bedrooms_max}" if lead.num_bedrooms_min and lead.num_bedrooms_max else 'Flexible',
                    'area': f"{lead.property_area_min}-{lead.property_area_max} m²" if lead.property_area_min and lead.property_area_max else 'Flexible',
                }
            }
            lead.dashboard_data = lead_data

    @api.depends('captured_by_id', 'expected_revenue', 'capture_commission_rate')
    def _compute_capture_commission(self):
        """Calcular comisión de captación"""
        for lead in self:
            if lead.captured_by_id and lead.expected_revenue and lead.capture_commission_rate:
                lead.capture_commission_amount = lead.expected_revenue * (lead.capture_commission_rate / 100)
            else:
                lead.capture_commission_amount = 0.0

    def _compute_reservation_count(self):
        """Contar reservas relacionadas al lead"""
        for lead in self:
            # Buscar reservas vinculadas por cliente y propiedades de interés
            reservation_count = 0
            if lead.partner_id:
                reservation_count = self.env['property.reservation'].search_count([
                    ('partner_id', '=', lead.partner_id.id)
                ])
            lead.reservation_count = reservation_count

    def _compute_conflicting_visit(self):
        """Verificar si hay visitas conflictivas para la misma propiedad"""
        for lead in self:
            if not lead.ideal_visit_date or not lead.property_ids:
                lead.has_conflicting_visit = False
                lead.conflicting_visit_info = ''
                continue

            # Buscar otros leads con visita en la misma fecha y mismas propiedades
            date_start = lead.ideal_visit_date - timedelta(hours=2)
            date_end = lead.ideal_visit_date + timedelta(hours=2)

            conflicting_leads = self.search([
                ('id', '!=', lead.id),
                ('ideal_visit_date', '>=', date_start),
                ('ideal_visit_date', '<=', date_end),
                ('property_ids', 'in', lead.property_ids.ids),
            ], limit=1)

            if conflicting_leads:
                lead.has_conflicting_visit = True
                lead.conflicting_visit_info = f"⚠️ {conflicting_leads.user_id.name} tiene visita programada"
            else:
                lead.has_conflicting_visit = False
                lead.conflicting_visit_info = ''

    @api.depends('compared_properties_ids')
    def _compute_property_recommendations_data(self):
        """Calcular datos de recomendaciones"""
        for lead in self:
            if not lead.service_interested or lead.service_interested not in ['rent', 'sale']:
                lead.property_recommendations_data = {'recommendations': [], 'count': 0}
                continue

            # Generar recomendaciones basadas en criterios
            domain = [('is_property', '=', True), ('state', '=', 'free')]

            if lead.service_interested == 'rent':
                domain.append(('type_service', '=', 'for_tenancy'))
            elif lead.service_interested == 'sale':
                domain.append(('type_service', '=', 'for_sale'))

            if lead.desired_property_type_id:
                domain.append(('property_type_id', '=', lead.desired_property_type_id.id))

            properties = self.env['product.template'].search(domain, limit=10)

            recommendations = []
            for prop in properties:
                score = 0
                # Cálculo de score basado en criterios
                if lead.desired_neighborhood and prop.neighborhood:
                    if lead.desired_neighborhood.lower() in prop.neighborhood.lower():
                        score += 50

                if lead.budget_min and lead.budget_max:
                    budget_avg = (lead.budget_min + lead.budget_max) / 2
                    prop_price = prop.rent_value_from if lead.service_interested == 'rent' else prop.sale_value_from
                    if prop_price and abs(prop_price - budget_avg) / budget_avg < 0.2:
                        score += 30

                recommendations.append({
                    'id': prop.id,
                    'name': prop.name,
                    'score': score,
                    'price': prop.rent_value_from if lead.service_interested == 'rent' else prop.sale_value_from,
                    'neighborhood': prop.neighborhood or 'No especificado',
                    'bedrooms': prop.num_bedrooms or 0,
                    'area': prop.property_area or 0,
                    'image_url': f'/web/image/product.template/{prop.id}/image_1920' if prop.image_1920 else None,
                })

            # Ordenar por score
            recommendations.sort(key=lambda x: x['score'], reverse=True)

            lead.property_recommendations_data = {
                'recommendations': recommendations[:6],  # Top 6
                'count': len(recommendations),
                'criteria_match': {
                    'neighborhood_match': bool(lead.desired_neighborhood),
                    'budget_defined': bool(lead.budget_min and lead.budget_max),
                    'type_defined': bool(lead.desired_property_type_id),
                }
            }

    @api.depends('compared_properties_ids')
    def _compute_comparison_data(self):
        """Calcular datos para comparador de propiedades"""
        for lead in self:
            compared_props = []
            for prop in lead.compared_properties_ids:
                prop_data = {
                    'id': prop.id,
                    'name': prop.name,
                    'price': prop.rent_value_from if lead.service_interested == 'rent' else prop.sale_value_from,
                    'neighborhood': prop.neighborhood or 'No especificado',
                    'bedrooms': prop.num_bedrooms or 0,
                    'bathrooms': prop.num_bathrooms or 0,
                    'area': prop.property_area or 0,
                    'parking': prop.num_parking or 0,
                    'latitude': prop.latitude,
                    'longitude': prop.longitude,
                    'address': prop.street or '',
                    'municipality': prop.municipality or '',
                    'image_url': f'/web/image/product.template/{prop.id}/image_1920' if prop.image_1920 else None,
                    'features': {
                        'pool': bool(prop.pools),
                        'gym': bool(prop.gym),
                        'security': bool(prop.security),
                        'elevator': bool(prop.elevator),
                    }
                }
                compared_props.append(prop_data)

            lead.comparison_data = {
                'properties': compared_props,
                'count': len(compared_props),
                'can_add_more': len(compared_props) < 4,
                'comparison_ready': len(compared_props) >= 2,
            }

    @api.depends('partner_id')
    def _compute_partner_contracts_count(self):
        for lead in self:
            if lead.partner_id:
                contracts = self.env['property.contract'].search([('partner_id', '=', lead.partner_id.id)])
                lead.partner_contracts_count = len(contracts)
                lead.partner_active_contracts_count = len(contracts.filtered(lambda c: c.state == 'active'))
            else:
                lead.partner_contracts_count = 0
                lead.partner_active_contracts_count = 0

    @api.depends('date_deadline')
    def _compute_days_to_close(self):
        today = fields.Date.today()
        for lead in self:
            if lead.date_deadline:
                delta = lead.date_deadline - today
                lead.days_to_close = delta.days
            else:
                lead.days_to_close = 0

    @api.depends('create_date')
    def _compute_days_open(self):
        today = fields.Datetime.now()
        for lead in self:
            if lead.create_date:
                delta = today - lead.create_date
                lead.days_open = delta.days
            else:
                lead.days_open = 0

    @api.depends('desired_neighborhood', 'desired_property_type_id', 'budget_min', 'budget_max',
                 'num_bedrooms_min', 'num_bedrooms_max', 'num_bathrooms_min', 'property_area_min',
                 'property_area_max', 'has_pets', 'requires_common_areas', 'property_purpose', 'service_interested')
    def _compute_recommended_properties(self):
        """Calcular propiedades recomendadas"""
        for lead in self:
            if not lead.service_interested or lead.service_interested not in ['rent', 'sale']:
                lead.recommended_properties_ids = [(5, 0, 0)]
                continue

            domain = [('is_property', '=', True), ('state', '=', 'free')]

            if lead.service_interested == 'rent':
                domain.append(('type_service', '=', 'for_tenancy'))
            elif lead.service_interested == 'sale':
                domain.append(('type_service', '=', 'for_sale'))

            if lead.desired_property_type_id:
                domain.append(('property_type_id', '=', lead.desired_property_type_id.id))

            if lead.desired_neighborhood:
                domain.append(('neighborhood', 'ilike', lead.desired_neighborhood))

            properties = self.env['product.template'].search(domain, limit=50)

            # Algoritmo de scoring
            scored_properties = []
            for prop in properties:
                score = 0

                if lead.desired_neighborhood and prop.neighborhood and \
                   lead.desired_neighborhood.lower() in prop.neighborhood.lower():
                    score += 50

                if lead.desired_property_type_id and prop.property_type_id == lead.desired_property_type_id:
                    score += 40

                if lead.budget_min and lead.budget_max:
                    budget_avg = (lead.budget_min + lead.budget_max) / 2
                    prop_price = prop.rent_value_from if lead.service_interested == 'rent' else prop.sale_value_from
                    if prop_price:
                        price_diff_pct = abs(prop_price - budget_avg) / budget_avg * 100
                        if price_diff_pct < 10:
                            score += 30
                        elif price_diff_pct < 20:
                            score += 20

                scored_properties.append((prop.id, score))

            scored_properties.sort(key=lambda x: x[1], reverse=True)
            top_4_ids = [p[0] for p in scored_properties[:4]]

            lead.recommended_properties_ids = [(6, 0, top_4_ids)]

    @api.depends('recommended_properties_ids')
    def _compute_recommendation_count(self):
        """Calcular número de recomendaciones"""
        for lead in self:
            lead.recommendation_count = len(lead.recommended_properties_ids)

    # ===============================
    # VALIDACIONES
    # ===============================

    @api.constrains('compared_properties_ids')
    def _check_compared_properties_limit(self):
        for lead in self:
            if len(lead.compared_properties_ids) > 4:
                raise ValidationError(_('Solo puede comparar un máximo de 4 propiedades a la vez.'))

    # ===============================
    # MÉTODOS DE NEGOCIO
    # ===============================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Asignación automática a equipo inmobiliario
            if vals.get('service_interested') in ['rent', 'sale', 'projects']:
                real_estate_team = self.env['crm.team'].search([
                    '|', ('name', 'ilike', 'inmobiliaria'), ('name', 'ilike', 'real estate')
                ], limit=1)
                if real_estate_team:
                    vals['team_id'] = real_estate_team.id

            # Creación automática de ticket PQRS
            if vals.get('pqrs_type') and 'helpdesk.ticket' in self.env:
                helpdesk_vals = {
                    'name': vals.get('name', 'PQRS'),
                    'partner_id': vals.get('partner_id'),
                    'description': vals.get('description', ''),
                    'priority': '2' if vals.get('pqrs_type') in ['complaint', 'claim'] else '1',
                }
                ticket = self.env['helpdesk.ticket'].sudo().create(helpdesk_vals)
                vals['helpdesk_ticket_id'] = ticket.id

        return super().create(vals_list)

    def action_close_lead_with_contract(self):
        """Cerrar oportunidad creando contrato"""
        self.ensure_one()
        if not self.compared_properties_ids:
            raise ValidationError(_('Debe seleccionar la propiedad para generar el contrato.'))

        property_selected = self.compared_properties_ids[0]
        contract_vals = {
            'name': f'Contrato - {self.name}',
            'partner_id': self.partner_id.id if self.partner_id else False,
            'property_id': property_selected.id,
            'contract_type': 'is_rental' if self.service_interested == 'rent' else 'is_ownership',
            'date_from': self.contract_start_date or fields.Date.today(),
            'date_to': self.contract_end_date or fields.Date.today(),
            'rental_fee': self.estimated_monthly_rent if self.service_interested == 'rent' else 0.0,
        }

        contract = self.env['property.contract'].create(contract_vals)
        self.write({
            'contract_id': contract.id,
            'stage_id': self.env.ref('crm.stage_lead4', raise_if_not_found=False).id or self.stage_id.id,
            'probability': 100,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Contrato Creado',
            'view_mode': 'form',
            'res_model': 'property.contract',
            'res_id': contract.id,
            'target': 'current',
        }

    def action_view_compared_properties(self):
        """Ver propiedades en comparación"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Propiedades en Comparación',
            'view_mode': 'kanban,list,form',
            'res_model': 'product.template',
            'domain': [('id', 'in', self.compared_properties_ids.ids)],
            'context': {'default_is_property': True},
            'target': 'current',
        }

    def action_view_partner_contracts(self):
        """Ver contratos del cliente"""
        self.ensure_one()
        if not self.partner_id:
            return {'type': 'ir.actions.act_window_close'}

        return {
            'type': 'ir.actions.act_window',
            'name': f'Contratos de {self.partner_id.name}',
            'view_mode': 'list,form',
            'res_model': 'property.contract',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'context': {'default_partner_id': self.partner_id.id},
            'target': 'current',
        }

    def action_view_recommended_properties(self):
        """Ver propiedades recomendadas"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Propiedades Recomendadas ({len(self.property_ids)})',
            'view_mode': 'kanban,list,form',
            'res_model': 'product.template',
            'domain': [('id', 'in', self.property_ids.ids)],
            'context': {'create': False},
            'target': 'current',
        }

    def action_add_to_comparison(self, property_id=None):
        """Agregar propiedad al comparador"""
        self.ensure_one()

        # Si no viene property_id como parámetro, buscar en contexto
        if not property_id:
            property_id = self.env.context.get('property_to_add')

        if not property_id:
            raise ValidationError(_('No se especificó la propiedad a agregar.'))

        if len(self.compared_properties_ids) >= 4:
            raise ValidationError(_('Ya tiene 4 propiedades en comparación. Elimine una para agregar otra.'))

        prop = self.env['product.template'].browse(property_id)

        # Validar que no esté ya agregada
        if prop.id in self.compared_properties_ids.ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Ya Agregada'),
                    'message': _('Esta propiedad ya está en la comparación.'),
                    'type': 'info',
                    'sticky': False,
                }
            }

        self.compared_properties_ids = [(4, prop.id)]

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Propiedad Agregada'),
                'message': _('Propiedad "%s" agregada al comparador (%d/4)') % (prop.name, len(self.compared_properties_ids)),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_print_comparison(self):
        """Imprimir comparación de propiedades"""
        self.ensure_one()
        if not self.compared_properties_ids:
            raise ValidationError(_('Debe seleccionar al menos 2 propiedades para comparar.'))

        return self.env.ref('bohio_crm.property_comparison_report').report_action(self)

    def action_schedule_activity(self):
        """Programar nueva actividad"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nueva Actividad',
            'res_model': 'mail.activity',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': 'crm.lead',
                'default_res_id': self.id,
                'default_user_id': self.user_id.id,
            }
        }

    def action_schedule_call(self):
        """Programar llamada"""
        self.ensure_one()
        activity_type = self.env.ref('mail.mail_activity_data_call', raise_if_not_found=False)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Programar Llamada',
            'res_model': 'mail.activity',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': 'crm.lead',
                'default_res_id': self.id,
                'default_activity_type_id': activity_type.id if activity_type else 1,
                'default_summary': f'Llamada a {self.partner_id.name if self.partner_id else self.name}',
                'default_user_id': self.user_id.id,
            }
        }

    def action_schedule_meeting(self):
        """Programar reunión"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Agendar Cita',
            'res_model': 'calendar.event',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_ids': [[6, 0, [self.partner_id.id]]] if self.partner_id else [],
                'default_name': f'Cita - {self.name}',
                'default_user_id': self.user_id.id,
            }
        }

    def action_send_email(self):
        """Enviar email"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Enviar Email',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_model': 'crm.lead',
                'default_res_id': self.id,
                'default_composition_mode': 'comment',
                'default_partner_ids': [[6, 0, [self.partner_id.id]]] if self.partner_id else [],
            }
        }

    def action_share_whatsapp(self):
        """Compartir por WhatsApp"""
        self.ensure_one()
        if not self.partner_id:
            raise ValidationError(_('No hay cliente asociado para enviar WhatsApp.'))

        phone = self.phone or self.mobile
        if not phone:
            raise ValidationError(_('El cliente no tiene teléfono registrado.'))

        message = f'Hola {self.partner_id.name}, te contacto sobre la oportunidad {self.name}'
        whatsapp_url = f'https://wa.me/{phone.replace("+", "").replace(" ", "")}?text={message}'

        return {
            'type': 'ir.actions.act_url',
            'url': whatsapp_url,
            'target': 'new',
        }

    def action_generate_contract(self):
        """Generar contrato - usar método existente"""
        return self.action_close_lead_with_contract()

    def action_print_timeline(self):
        """Imprimir vista timeline"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Timeline'),
                'message': _('Función de impresión del timeline en desarrollo'),
                'type': 'info',
                'sticky': False,
            }
        }

    def action_expand_comparison(self):
        """Expandir comparación - usar método existente"""
        return self.action_view_compared_properties()

    def action_create_task(self):
        """Crear nueva tarea"""
        self.ensure_one()
        task_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nueva Tarea',
            'res_model': 'mail.activity',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': 'crm.lead',
                'default_res_id': self.id,
                'default_activity_type_id': task_type.id if task_type else 1,
                'default_user_id': self.user_id.id,
            }
        }

    def action_generate_comparison_report(self):
        """Generar reporte de comparación de propiedades"""
        self.ensure_one()
        if not self.compared_properties_ids:
            raise ValidationError(_('No hay propiedades para comparar.'))

        return self.env.ref('bohio_crm.property_comparison_report').report_action(self)

    def action_create_property_from_lead(self):
        """
        Crear ficha de inmueble desde oportunidad de captación
        Usado desde quick_create cuando service_interested='consign'
        """
        self.ensure_one()

        if self.service_interested != 'consign':
            raise ValidationError(_('Esta acción solo está disponible para oportunidades de consignación.'))

        # Preparar valores para la nueva propiedad
        property_vals = {
            'name': f'[CAPTACIÓN] {self.name}',
            'is_property': True,
            'active': True,
            'state': 'draft',  # Estado inicial
            'type_service': 'sale',  # Por defecto venta

            # Información del propietario
            'owner_id': self.partner_id.id if self.partner_id else False,

            # Ubicación
            'city': self.desired_city or '',
            'neighborhood': self.desired_neighborhood or '',

            # Tipo de propiedad
            'property_type_id': self.desired_property_type_id.id if self.desired_property_type_id else False,

            # Precio
            'list_price': self.expected_revenue or 0,
            'net_price': self.expected_revenue or 0,

            # Área
            'property_area': self.property_area_min or 0,

            # Notas
            'description': f'''
Propiedad creada desde oportunidad CRM: {self.name}

Cliente: {self.partner_id.name if self.partner_id else 'No especificado'}
Teléfono: {self.phone or 'No especificado'}
Email: {self.email_from or 'No especificado'}

Observaciones:
{self.description or 'Sin observaciones adicionales'}
            '''.strip(),

            # Responsable
            'user_id': self.user_id.id if self.user_id else False,
        }

        # Crear la propiedad
        new_property = self.env['product.template'].create(property_vals)

        # Vincular la propiedad con el lead
        self.write({
            'property_ids': [(4, new_property.id)],
        })

        # Registrar captación si hay usuario captador
        if self.captured_by_id:
            self.message_post(
                body=f'📝 Propiedad captada por: {self.captured_by_id.name}<br/>Comisión estimada: {self.capture_commission_amount:,.0f} COP',
                subject='Comisión de Captación'
            )

        # Mensaje en el chatter
        self.message_post(
            body=f'✅ Se creó la ficha de inmueble: <a href="/web#id={new_property.id}&model=product.template">{new_property.name}</a>',
            subject='Ficha de Inmueble Creada'
        )

        # Abrir la ficha creada
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ficha de Inmueble Creada',
            'res_model': 'product.template',
            'res_id': new_property.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_is_property': True,
                'crm_lead_id': self.id,
            }
        }

    def action_create_reservation(self):
        """Crear reserva desde oportunidad"""
        self.ensure_one()

        if not self.property_ids:
            raise ValidationError(_('Debe seleccionar al menos una propiedad para crear la reserva.'))

        if not self.partner_id:
            raise ValidationError(_('Debe asignar un cliente antes de crear la reserva.'))

        # Tomar la primera propiedad si hay varias
        property_id = self.property_ids[0]

        # Determinar tipo de reserva según servicio
        booking_type = 'is_ownership' if self.service_interested in ['sale', 'projects'] else 'is_rental'

        # Valores para la reserva
        reservation_vals = {
            'partner_id': self.partner_id.id,
            'property_id': property_id.id,
            'booking_type': booking_type,
            'user_id': self.user_id.id,
            'date': fields.Datetime.now(),
            'net_price': self.expected_revenue or property_id.net_price,
            'project_id': self.project_id.id if self.project_id else property_id.project_worksite_id.id,
        }

        # Crear reserva
        reservation = self.env['property.reservation'].create(reservation_vals)

        # Vincular con el lead
        self.write({'reservation_id': reservation.id})

        # Mensaje en chatter
        self.message_post(
            body=f'📋 Se creó la reserva: <a href="/web#id={reservation.id}&model=property.reservation">{reservation.name}</a>',
            subject='Reserva Creada'
        )

        return {
            'type': 'ir.actions.act_window',
            'name': 'Reserva Creada',
            'res_model': 'property.reservation',
            'res_id': reservation.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_reservations(self):
        """Ver reservas del cliente"""
        self.ensure_one()

        if not self.partner_id:
            raise ValidationError(_('No hay cliente asignado.'))

        reservations = self.env['property.reservation'].search([
            ('partner_id', '=', self.partner_id.id)
        ])

        return {
            'name': f'Reservas de {self.partner_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'property.reservation',
            'view_mode': 'list,form',
            'domain': [('id', 'in', reservations.ids)],
            'context': {'default_partner_id': self.partner_id.id}
        }

    def action_view_loan_documents(self):
        """Ver documentos de préstamo"""
        self.ensure_one()

        return {
            'name': 'Documentos para Estudio de Crédito',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.loan_document_ids.ids)],
            'context': {
                'default_res_model': 'crm.lead',
                'default_res_id': self.id,
            }
        }

    def action_upload_loan_document(self):
        """Subir documento para estudio de crédito"""
        self.ensure_one()

        return {
            'name': 'Subir Documento',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': 'crm.lead',
                'default_res_id': self.id,
                'default_name': 'Documento para estudio de crédito',
            }
        }

    def action_schedule_visit(self):
        """Programar visita a propiedad"""
        self.ensure_one()

        # Verificar si hay conflictos
        if self.has_conflicting_visit:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('⚠️ Conflicto de Visitas'),
                    'message': self.conflicting_visit_info,
                    'type': 'warning',
                    'sticky': True,
                }
            }

        # Crear actividad de visita
        activity_type = self.env.ref('mail.mail_activity_data_meeting', raise_if_not_found=False)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Programar Visita',
            'res_model': 'mail.activity',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': 'crm.lead',
                'default_res_id': self.id,
                'default_activity_type_id': activity_type.id if activity_type else 1,
                'default_summary': f'Visita a propiedad - {self.name}',
                'default_date_deadline': self.ideal_visit_date.date() if self.ideal_visit_date else fields.Date.today(),
                'default_note': self.visit_notes or '',
                'default_user_id': self.user_id.id,
            }
        }

    @api.model
    def get_smart_suggestions(self):
        """
        Obtener sugerencias inteligentes basadas en estadísticas de uso
        Llamado desde JavaScript para autocompletar campos
        """
        # Obtener usuario actual
        user_id = self.env.user.id

        # Estadísticas de los últimos 30 días
        date_limit = fields.Datetime.now() - timedelta(days=30)

        # Servicios más usados
        service_stats = self.read_group(
            [('user_id', '=', user_id), ('create_date', '>=', date_limit)],
            ['service_interested'],
            ['service_interested']
        )

        # Tipos de cliente más comunes
        client_type_stats = self.read_group(
            [('user_id', '=', user_id), ('create_date', '>=', date_limit)],
            ['client_type'],
            ['client_type']
        )

        # Fuentes de solicitud más comunes
        source_stats = self.read_group(
            [('user_id', '=', user_id), ('create_date', '>=', date_limit)],
            ['request_source'],
            ['request_source']
        )

        # Proyectos más usados
        project_stats = self.read_group(
            [('user_id', '=', user_id), ('create_date', '>=', date_limit), ('project_id', '!=', False)],
            ['project_id'],
            ['project_id']
        )

        # Tags más usados
        tag_stats = self.env['crm.tag'].search_read(
            [],
            ['id', 'name', 'color'],
            order='id desc',
            limit=10
        )

        return {
            'most_used_services': [
                {'value': item['service_interested'], 'count': item['service_interested_count']}
                for item in service_stats if item['service_interested']
            ],
            'most_used_client_types': [
                {'value': item['client_type'], 'count': item['client_type_count']}
                for item in client_type_stats if item['client_type']
            ],
            'most_used_sources': [
                {'value': item['request_source'], 'count': item['request_source_count']}
                for item in source_stats if item['request_source']
            ],
            'frequent_projects': [
                {'id': item['project_id'][0], 'name': item['project_id'][1], 'count': item['project_id_count']}
                for item in project_stats if item['project_id']
            ],
            'suggested_tags': tag_stats,
        }

    def action_view_recommended_properties(self):
        """Ver propiedades recomendadas generadas"""
        self.ensure_one()
        self._compute_recommended_properties()

        if not self.recommended_properties_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sin Recomendaciones'),
                    'message': _('No se encontraron propiedades que coincidan con los criterios especificados.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        self.recommendation_status = 'generated'

        return {
            'type': 'ir.actions.act_window',
            'name': f'Propiedades Recomendadas ({len(self.recommended_properties_ids)})',
            'view_mode': 'kanban,list,form',
            'res_model': 'product.template',
            'domain': [('id', 'in', self.recommended_properties_ids.ids)],
            'context': {
                'create': False,
                'default_type_service': 'for_tenancy' if self.service_interested == 'rent' else 'for_sale',
            }
        }

    def action_generate_recommendations(self):
        """Generar recomendaciones de propiedades"""
        self.ensure_one()
        self._compute_recommended_properties()
        self.write({'recommendation_status': 'generated'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Se generaron {self.recommendation_count} recomendaciones',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_refresh_recommendations(self):
        """Actualizar recomendaciones de propiedades (alias de action_generate_recommendations)"""
        return self.action_generate_recommendations()

    def action_set_won(self):
        """Marcar oportunidad como ganada"""
        self.ensure_one()
        won_stage = self.env['crm.stage'].search([
            ('is_won', '=', True),
            '|', ('team_id', '=', False), ('team_id', '=', self.team_id.id)
        ], limit=1)

        if won_stage:
            self.write({
                'stage_id': won_stage.id,
                'probability': 100,
                'active': True,
            })

        return {'type': 'ir.actions.act_window_close'}

    def action_set_lost(self):
        """Marcar oportunidad como perdida"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Marcar como Perdida'),
            'res_model': 'crm.lead.lost',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
            }
        }

    # ===============================
    # MÉTODOS DE DASHBOARD
    # ===============================

    @api.model
    def retrieve_dashboard(self):
        """Obtener datos del dashboard para vista kanban"""
        user = self.env.user
        today = fields.Date.today()
        seven_days_ago = today - timedelta(days=7)

        # Todas las oportunidades
        all_new = self.search_count([
            ('type', '=', 'opportunity'),
            ('stage_id.is_won', '=', False),
            ('probability', '<', 20)
        ])
        all_qualified = self.search_count([
            ('type', '=', 'opportunity'),
            ('stage_id.is_won', '=', False),
            ('probability', '>=', 20),
            ('probability', '<', 70)
        ])
        all_proposal = self.search_count([
            ('type', '=', 'opportunity'),
            ('stage_id.is_won', '=', False),
            ('probability', '>=', 70)
        ])

        # Mis oportunidades
        my_new = self.search_count([
            ('type', '=', 'opportunity'),
            ('user_id', '=', user.id),
            ('stage_id.is_won', '=', False),
            ('probability', '<', 20)
        ])
        my_qualified = self.search_count([
            ('type', '=', 'opportunity'),
            ('user_id', '=', user.id),
            ('stage_id.is_won', '=', False),
            ('probability', '>=', 20),
            ('probability', '<', 70)
        ])
        my_proposal = self.search_count([
            ('type', '=', 'opportunity'),
            ('user_id', '=', user.id),
            ('stage_id.is_won', '=', False),
            ('probability', '>=', 70)
        ])

        # Valor promedio de negocios
        all_opps = self.search([
            ('type', '=', 'opportunity'),
            ('stage_id.is_won', '=', False)
        ])
        avg_deal = sum(all_opps.mapped('expected_revenue')) / len(all_opps) if all_opps else 0
        company = self.env.company
        avg_deal_value = f"{company.currency_id.symbol}{avg_deal:,.0f}"

        # Ganadas últimos 7 días
        won_last_7_days = self.search_count([
            ('type', '=', 'opportunity'),
            ('stage_id.is_won', '=', True),
            ('date_closed', '>=', seven_days_ago),
            ('date_closed', '<=', today)
        ])

        # Días promedio para cierre
        won_opps = self.search([
            ('type', '=', 'opportunity'),
            ('stage_id.is_won', '=', True),
            ('date_closed', '!=', False)
        ], limit=50)

        days_list = []
        for opp in won_opps:
            if opp.create_date and opp.date_closed:
                delta = opp.date_closed - opp.create_date.date()
                days_list.append(delta.days)

        avg_days = sum(days_list) / len(days_list) if days_list else 0
        avg_days_to_close = f"{int(avg_days)} días"

        # Oportunidades activas
        active_opportunities = self.search_count([
            ('type', '=', 'opportunity'),
            ('stage_id.is_won', '=', False),
            ('active', '=', True)
        ])

        # Calcular comisión estimada BOHIO (todas las oportunidades activas)
        total_commission = 0
        for opp in all_opps:
            # Usar commission_percentage del lead (default 10%)
            commission_percent = opp.commission_percentage or 10.0
            commission = (opp.expected_revenue * commission_percent) / 100
            total_commission += commission

        estimated_commission = f"{company.currency_id.symbol}{total_commission:,.0f}"

        return {
            'all_new': all_new,
            'all_qualified': all_qualified,
            'all_proposal': all_proposal,
            'my_new': my_new,
            'my_qualified': my_qualified,
            'my_proposal': my_proposal,
            'avg_deal_value': avg_deal_value,
            'estimated_commission': estimated_commission,
            'avg_days_to_close': avg_days_to_close,
            'active_opportunities': active_opportunities,
            'user_id': user.id,
        }

    @api.model
    def get_crm_dashboard_data(self, show_all=True, period='month', service_filter='all'):
        """Obtener datos del dashboard CRM"""
        company = self.env.company
        currency = company.currency_id
        user = self.env.user

        today = fields.Date.today()
        if period == 'week':
            start_date = today - timedelta(days=today.weekday())
            prev_start = start_date - timedelta(days=7)
        elif period == 'month':
            start_date = today.replace(day=1)
            prev_start = (start_date - timedelta(days=1)).replace(day=1)
        elif period == 'quarter':
            quarter = (today.month - 1) // 3
            start_date = today.replace(month=quarter * 3 + 1, day=1)
            prev_start = (start_date - timedelta(days=1)).replace(day=1)
            prev_start = prev_start.replace(month=((prev_start.month - 1) // 3) * 3 + 1, day=1)
        else:
            start_date = today.replace(month=1, day=1)
            prev_start = start_date.replace(year=start_date.year - 1)

        domain = [('type', '=', 'opportunity')]
        if not show_all:
            domain.append(('user_id', '=', user.id))
        if service_filter and service_filter != 'all':
            domain.append(('service_interested', '=', service_filter))

        # Métricas de contratos
        PropertyContract = self.env['property.contract']
        contract_domain = [('state', '=', 'active')]
        if not show_all:
            contract_domain.append(('user_id', '=', user.id))

        active_contracts = PropertyContract.search_count(contract_domain)
        active_contract_records = PropertyContract.search(contract_domain)
        recurring_revenue = sum(active_contract_records.mapped('rental_fee'))

        # Métricas de oportunidades
        new_opportunities = self.search_count(domain + [
            ('create_date', '>=', start_date),
            ('create_date', '<=', datetime.combine(today, datetime.max.time()))
        ])

        # Métricas de propiedades
        Product = self.env['product.template']
        property_domain = [('is_property', '=', True)]
        properties_available = Product.search_count(property_domain + [('state', '=', 'free')])
        properties_rented = Product.search_count(property_domain + [('state', '=', 'on_lease')])
        properties_total = Product.search_count(property_domain)

        # Actividades y citas
        CalendarEvent = self.env['calendar.event']
        appointment_domain = [('start', '>=', datetime.now())]
        if not show_all:
            appointment_domain.append(('user_id', '=', user.id))
        pending_appointments = CalendarEvent.search_count(appointment_domain)

        Activity = self.env['mail.activity']
        activity_domain = []
        if not show_all:
            activity_domain.append(('user_id', '=', user.id))
        pending_activities = Activity.search_count(activity_domain)

        return {
            'metrics': {
                'active_contracts': active_contracts,
                'recurring_revenue': recurring_revenue,
                'new_opportunities': new_opportunities,
                'properties_available': properties_available,
                'properties_rented': properties_rented,
                'properties_total': properties_total,
                'pending_appointments': pending_appointments,
                'pending_activities': pending_activities,
                'currency_id': currency.id,
                'occupancy_rate': f"{round((properties_rented / properties_total * 100) if properties_total else 0)}%",
            },
            'user_info': {
                'name': user.name,
                'title': user.function or '',
                'avatar': f'/web/image?model=res.users&id={user.id}&field=avatar_128'
            }
        }

    def _calculate_growth(self, current, previous):
        """Calcular porcentaje de crecimiento"""
        if previous == 0:
            return '+100%' if current > 0 else '0%'
        growth = ((current - previous) / previous) * 100
        sign = '+' if growth > 0 else ''
        return f"{sign}{round(growth)}%"


class CrmTeam(models.Model):
    """Equipos CRM con métricas de recaudo"""
    _inherit = 'crm.team'

    show_payment_metrics = fields.Boolean('Mostrar Métricas de Pagos', default=False)
    total_invoiced_month = fields.Monetary('Facturado del Mes', currency_field='currency_id', compute='_compute_invoice_metrics')
    total_credit_notes_month = fields.Monetary('Notas Crédito del Mes', currency_field='currency_id', compute='_compute_invoice_metrics')
    net_invoiced_month = fields.Monetary('Facturación Neta del Mes', currency_field='currency_id', compute='_compute_invoice_metrics')
    total_collected_month = fields.Monetary('Recaudo del Mes', currency_field='currency_id', compute='_compute_payment_metrics')
    expected_collection_month = fields.Monetary('Recaudo Esperado', currency_field='currency_id', compute='_compute_payment_metrics')
    collection_vs_expected = fields.Float('% Recaudo vs Esperado', compute='_compute_payment_metrics')
    total_paid_owners_month = fields.Monetary('Pagado a Propietarios', currency_field='currency_id', compute='_compute_payment_metrics')
    pending_owner_payments = fields.Monetary('Pendiente Pagar Propietarios', currency_field='currency_id', compute='_compute_payment_metrics')

    @api.depends('member_ids')
    def _compute_invoice_metrics(self):
        """Calcular métricas de facturación"""
        AccountMove = self.env['account.move']
        today = fields.Date.today()
        first_day = today.replace(day=1)

        for team in self:
            if not team.show_payment_metrics or not team.member_ids:
                team.update({'total_invoiced_month': 0.0, 'total_credit_notes_month': 0.0, 'net_invoiced_month': 0.0})
                continue

            invoices = AccountMove.search_read(
                domain=[
                    ('invoice_user_id', 'in', team.member_ids.ids),
                    ('invoice_date', '>=', first_day),
                    ('invoice_date', '<=', today),
                    ('state', '=', 'posted'),
                    ('move_type', 'in', ['out_invoice', 'out_refund'])
                ],
                fields=['amount_total', 'move_type']
            )

            total_inv = sum(inv['amount_total'] for inv in invoices if inv['move_type'] == 'out_invoice')
            total_credit = sum(inv['amount_total'] for inv in invoices if inv['move_type'] == 'out_refund')

            team.update({
                'total_invoiced_month': total_inv,
                'total_credit_notes_month': total_credit,
                'net_invoiced_month': total_inv - total_credit
            })

    @api.depends('member_ids')
    def _compute_payment_metrics(self):
        """Calcular métricas de recaudo"""
        AccountPayment = self.env['account.payment']
        PropertyContract = self.env['property.contract']
        today = fields.Date.today()
        first_day = today.replace(day=1)

        for team in self:
            if not team.show_payment_metrics or not team.member_ids:
                team.update({
                    'total_collected_month': 0.0, 'expected_collection_month': 0.0,
                    'collection_vs_expected': 0.0, 'total_paid_owners_month': 0.0, 'pending_owner_payments': 0.0
                })
                continue

            # Recaudo esperado
            active_contracts = PropertyContract.search_read(
                domain=[('user_id', 'in', team.member_ids.ids), ('state', '=', 'active'), ('contract_type', '=', 'is_rental')],
                fields=['rental_fee']
            )
            expected_collection = sum(c['rental_fee'] for c in active_contracts)

            # Recaudo real
            collected_payments = AccountPayment.search_read(
                domain=[('payment_type', '=', 'inbound'), ('state', '=', 'posted'), ('date', '>=', first_day), ('date', '<=', today)],
                fields=['amount']
            )
            total_collected = sum(p['amount'] for p in collected_payments)

            # Pagos a propietarios
            owner_payments = AccountPayment.search_read(
                domain=[('payment_type', '=', 'outbound'), ('state', '=', 'posted'), ('date', '>=', first_day), ('date', '<=', today)],
                fields=['amount']
            )
            total_paid_owners = sum(p['amount'] for p in owner_payments)

            team.update({
                'total_collected_month': total_collected,
                'expected_collection_month': expected_collection,
                'collection_vs_expected': (total_collected / expected_collection * 100) if expected_collection > 0 else 0.0,
                'total_paid_owners_month': total_paid_owners,
                'pending_owner_payments': total_collected - total_paid_owners
            })


# ELIMINADO: CrmDashboard - usar crm.salesperson.dashboard en su lugar


# ELIMINADO: CrmAnalytics - funcionalidad incompleta, usar crm.salesperson.dashboard


# Agregar métodos del timeline al CrmLead
CrmLead.get_timeline_data = lambda self: self._get_timeline_data_impl()
CrmLead.action_search_more_properties = lambda self: self._action_search_more_properties_impl()

def _get_timeline_data_impl(self):
    """Obtener datos del timeline para la vista"""
    self.ensure_one()

    timeline_items = []

    # Obtener actividades
    activities = self.env['mail.activity'].search([
        ('res_model', '=', 'crm.lead'),
        ('res_id', '=', self.id)
    ], order='date_deadline desc')

    for activity in activities:
        timeline_items.append({
            'type': 'activity',
            'icon': 'calendar',
            'color': '#9b59b6',
            'title': f'Actividad: {activity.activity_type_id.name}',
            'content': activity.summary or 'Sin descripción',
            'time': activity.date_deadline.strftime('%d %b, %H:%M') if activity.date_deadline else '-',
            'user': activity.user_id.name,
        })

    # Obtener mensajes
    messages = self.env['mail.message'].search([
        ('model', '=', 'crm.lead'),
        ('res_id', '=', self.id),
        ('message_type', 'in', ['email', 'comment'])
    ], limit=10, order='date desc')

    for message in messages:
        msg_type = 'email' if message.message_type == 'email' else 'note'
        timeline_items.append({
            'type': msg_type,
            'icon': 'envelope' if msg_type == 'email' else 'comment',
            'color': '#e74c3c' if msg_type == 'email' else '#3498db',
            'title': f'{msg_type.title()}: {message.subject or "Sin asunto"}',
            'content': message.body or 'Sin contenido',
            'time': message.date.strftime('%d %b, %H:%M') if message.date else '-',
            'user': message.author_id.name if message.author_id else 'Sistema',
        })

    # Ordenar por fecha
    timeline_items.sort(key=lambda x: x['time'], reverse=True)
    return timeline_items[:15]

def _action_search_more_properties_impl(self):
    """Buscar más propiedades"""
    self.ensure_one()

    domain = [('is_property', '=', True), ('state', '=', 'free')]

    if self.service_interested == 'rent':
        domain.append(('type_service', '=', 'for_tenancy'))
    elif self.service_interested == 'sale':
        domain.append(('type_service', '=', 'for_sale'))

    if self.desired_property_type_id:
        domain.append(('property_type_id', '=', self.desired_property_type_id.id))

    return {
        'type': 'ir.actions.act_window',
        'name': 'Propiedades Disponibles',
        'view_mode': 'kanban,list,form',
        'res_model': 'product.template',
        'domain': domain,
        'context': {
            'search_default_available': 1,
            'lead_id': self.id,
        },
        'target': 'current',
    }

# ===============================
# MÉTODOS PARA MÉTRICAS
# ===============================


def _log_stage_change_impl(self, new_stage_id):
    """Log cambio de etapa para analytics"""
    self.ensure_one()
    # Crear log de cambio de etapa (silencioso)
    try:
        old_stage = self.stage_id.name if self.stage_id else 'Unknown'
        new_stage = self.env['crm.stage'].browse(new_stage_id).name if new_stage_id else 'Unknown'

        self.message_post(
            body=f"Stage changed from {old_stage} to {new_stage}",
            message_type='notification',
            subtype_id=self.env.ref('mail.mt_note').id,
        )
    except:
        # Silent fail for logging
        pass

def _get_metrics_summary_impl(self, domain=None):
    """Obtener resumen de métricas"""
    if not domain:
        domain = [('type', '=', 'opportunity')]

    # Verificar permisos de usuario
    if not self.env.user.has_group('sales_team.group_sale_salesman'):
        domain.append(('user_id', '=', self.env.user.id))

    leads = self.search(domain)

    total_revenue = sum(leads.mapped('expected_revenue'))
    total_recurring = sum(leads.mapped('recurring_revenue'))
    avg_probability = sum(leads.mapped('probability')) / len(leads) if leads else 0
    won_leads = leads.filtered(lambda l: l.stage_id.is_won)
    conversion_rate = (len(won_leads) / len(leads) * 100) if leads else 0

    return {
        'total_opportunities': len(leads),
        'total_revenue': total_revenue,
        'total_recurring': total_recurring,
        'avg_probability': avg_probability,
        'conversion_rate': conversion_rate,
        'won_opportunities': len(won_leads),
    }

def _get_user_accessible_domain_impl(self):
    """Obtener dominio accesible para el usuario"""
    base_domain = [('type', '=', 'opportunity')]

    # Si no es manager, solo ver sus propias oportunidades
    if not self.env.user.has_group('sales_team.group_sale_manager'):
        if self.env.user.has_group('sales_team.group_sale_salesman'):
            # Vendedor: sus oportunidades + las de su equipo si es líder
            user_teams = self.env['crm.team'].search([
                '|',
                ('user_id', '=', self.env.user.id),  # Es líder del equipo
                ('member_ids', 'in', self.env.user.id)  # Es miembro del equipo
            ])
            if user_teams:
                base_domain.append('|')
                base_domain.append(('user_id', '=', self.env.user.id))
                base_domain.append(('team_id', 'in', user_teams.ids))
            else:
                base_domain.append(('user_id', '=', self.env.user.id))
        else:
            # Usuario sin permisos de ventas: solo sus registros
            base_domain.append(('user_id', '=', self.env.user.id))

    return base_domain

def _search_read_with_permissions_impl(self, domain=None, fields=None, offset=0, limit=None, order=None):
    """Search read respetando permisos de usuario"""
    if domain is None:
        domain = []

    # Combinar dominio con restricciones de usuario
    user_domain = self._get_user_accessible_domain()
    combined_domain = user_domain + domain

    return super(CrmLead, self).search_read(combined_domain, fields, offset, limit, order)

def _action_make_call_impl(self):
    """Acción para realizar una llamada telefónica"""
    self.ensure_one()

    # Crear actividad de llamada
    activity_type = self.env.ref('mail.mail_activity_data_call', raise_if_not_found=False)
    if not activity_type:
        activity_type = self.env['mail.activity.type'].search([('category', '=', 'phonecall')], limit=1)

    if activity_type:
        return {
            'type': 'ir.actions.act_window',
            'name': _('Programar Llamada'),
            'res_model': 'mail.activity',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
                'default_activity_type_id': activity_type.id,
                'default_summary': f'Llamar a {self.partner_id.name or self.email_from}',
                'default_phone': self.phone or self.mobile,
            }
        }

    # Si no hay tipo de actividad, mostrar mensaje
    return {
        'type': 'ir.actions.client',
        'tag': 'display_notification',
        'params': {
            'title': _('Llamar'),
            'message': _('Teléfono: %s') % (self.phone or self.mobile or _('No disponible')),
            'type': 'info',
            'sticky': False,
        }
    }

def _action_send_email_impl(self):
    """Acción para enviar un email"""
    self.ensure_one()

    template_id = self.env.ref('crm.crm_lead_mail_template', raise_if_not_found=False)

    return {
        'type': 'ir.actions.act_window',
        'name': _('Enviar Email'),
        'res_model': 'mail.compose.message',
        'view_mode': 'form',
        'views': [(False, 'form')],
        'target': 'new',
        'context': {
            'default_model': self._name,
            'default_res_ids': self.ids,
            'default_template_id': template_id.id if template_id else False,
            'default_composition_mode': 'comment',
            'default_email_from': self.user_id.email,
            'default_partner_ids': [(4, self.partner_id.id)] if self.partner_id else [],
            'force_email': True,
        }
    }

# Asignar implementaciones
CrmLead._get_timeline_data_impl = _get_timeline_data_impl
CrmLead._action_search_more_properties_impl = _action_search_more_properties_impl
CrmLead.log_stage_change = _log_stage_change_impl
CrmLead.get_metrics_summary = _get_metrics_summary_impl
CrmLead._get_user_accessible_domain = _get_user_accessible_domain_impl
CrmLead.search_read_with_permissions = _search_read_with_permissions_impl
CrmLead.action_make_call = _action_make_call_impl
CrmLead.action_send_email = _action_send_email_impl
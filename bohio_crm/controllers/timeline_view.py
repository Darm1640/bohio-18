from odoo import http
from odoo.http import request

import json

class BohioTimelineController(http.Controller):

    @http.route('/crm/timeline/<int:lead_id>', type='http', auth='user', website=True)
    def crm_timeline_view(self, lead_id, **kwargs):
        """Vista timeline personalizada para CRM"""

        # Verificar acceso al lead
        lead = request.env['crm.lead'].sudo().browse(lead_id)
        if not lead.exists():
            return request.redirect('/web#action=crm.crm_lead_action_pipeline')

        # Cargar datos del lead
        lead_data = {
            'id': lead.id,
            'name': lead.name,
            'partner_id': lead.partner_id,
            'stage_id': lead.stage_id,
            'user_id': lead.user_id,
            'expected_revenue': lead.expected_revenue,
            'probability': lead.probability,
            'email_from': lead.email_from,
            'phone': lead.phone,
            'create_date': lead.create_date,
            'date_deadline': lead.date_deadline,
        }

        # Cargar etapas del CRM
        stages = request.env['crm.stage'].sudo().search([], order='sequence')
        stage_data = []
        for i, stage in enumerate(stages):
            is_completed = lead.stage_id.sequence >= stage.sequence
            is_active = lead.stage_id.id == stage.id

            stage_data.append({
                'id': stage.id,
                'name': stage.name,
                'sequence': stage.sequence,
                'is_completed': is_completed,
                'is_active': is_active,
                'days': i * 3 + 2  # Simulated days
            })

        # Cargar actividades del timeline
        activities = request.env['mail.activity'].sudo().search([
            ('res_id', '=', lead_id),
            ('res_model', '=', 'crm.lead')
        ], order='date_deadline desc', limit=50)

        activity_data = []
        for activity in activities:
            activity_data.append({
                'id': activity.id,
                'summary': activity.summary,
                'date_deadline': activity.date_deadline.strftime('%d/%m/%Y %H:%M') if activity.date_deadline else '',
                'user_id': activity.user_id.name if activity.user_id else '',
                'note': activity.note or '',
                'state': activity.state,
                'type': 'activity'
            })

        # Cargar mensajes/notas
        messages = request.env['mail.message'].sudo().search([
            ('res_id', '=', lead_id),
            ('model', '=', 'crm.lead'),
            ('message_type', '!=', 'notification')
        ], order='date desc', limit=30)

        message_data = []
        for message in messages:
            message_data.append({
                'id': message.id,
                'subject': message.subject or '',
                'body': message.body or '',
                'date': message.date.strftime('%d/%m/%Y %H:%M') if message.date else '',
                'author': message.author_id.name if message.author_id else '',
                'type': 'note'
            })

        # Cargar propiedades recomendadas
        recommended_properties = []
        if 'recommended_properties_ids' in lead._fields:
            for prop in lead.recommended_properties_ids[:4]:
                recommended_properties.append({
                    'id': prop.id,
                    'name': prop.name,
                    'list_price': prop.list_price,
                    'property_area': prop.property_area,
                    'num_bedrooms': prop.num_bedrooms,
                    'num_bathrooms': prop.num_bathrooms,
                    'neighborhood': prop.neighborhood or '',
                    'match_score': 95 - (len(recommended_properties) * 3)  # Simulated score
                })

        # Cargar propiedades en comparación
        compared_properties = []
        if 'compared_properties_ids' in lead._fields:
            for prop in lead.compared_properties_ids[:4]:
                compared_properties.append({
                    'id': prop.id,
                    'name': prop.name,
                    'list_price': prop.list_price,
                    'property_area': prop.property_area,
                    'num_bedrooms': prop.num_bedrooms,
                    'num_bathrooms': prop.num_bathrooms,
                    'neighborhood': prop.neighborhood or '',
                    'selected': prop.id == (lead.compared_properties_ids[:1].id if lead.compared_properties_ids else 0)
                })

        # Valores del template
        values = {
            'lead': lead_data,
            'stages': stage_data,
            'activities': activity_data,
            'messages': message_data,
            'recommended_properties': recommended_properties,
            'compared_properties': compared_properties,
            'timeline_items': activity_data + message_data,
        }

        return request.render('bohio_crm.timeline_full_view', values)

    @http.route('/crm/timeline/<int:lead_id>/update_stage', type='json', auth='user')
    def update_stage(self, lead_id, stage_id, **kwargs):
        """Actualizar etapa del lead"""
        try:
            lead = request.env['crm.lead'].browse(lead_id)
            lead.sudo().write({'stage_id': stage_id})
            return {'success': True, 'message': 'Etapa actualizada'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @http.route('/crm/timeline/<int:lead_id>/update_metric', type='json', auth='user')
    def update_metric(self, lead_id, field, value, **kwargs):
        """Actualizar métrica del lead"""
        try:
            lead = request.env['crm.lead'].browse(lead_id)
            lead.sudo().write({field: value})
            return {'success': True, 'message': 'Métrica actualizada'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @http.route('/crm/timeline/<int:lead_id>/add_property', type='json', auth='user')
    def add_property_to_comparison(self, lead_id, property_id, **kwargs):
        """Agregar propiedad a comparación"""
        try:
            lead = request.env['crm.lead'].browse(lead_id)
            current_ids = lead.compared_properties_ids.ids if 'compared_properties_ids' in lead._fields else []

            if len(current_ids) >= 4:
                return {'success': False, 'message': 'Máximo 4 propiedades en comparación'}

            if property_id not in current_ids:
                current_ids.append(property_id)
                lead.sudo().write({'compared_properties_ids': [(6, 0, current_ids)]})

            return {'success': True, 'message': 'Propiedad agregada'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @http.route('/crm/timeline/<int:lead_id>/create_activity', type='json', auth='user')
    def create_activity(self, lead_id, activity_data, **kwargs):
        """Crear nueva actividad"""
        try:
            vals = {
                'res_id': lead_id,
                'res_model': 'crm.lead',
                'summary': activity_data.get('summary', ''),
                'note': activity_data.get('note', ''),
                'date_deadline': activity_data.get('date_deadline'),
                'user_id': request.env.user.id,
            }

            # Determinar tipo de actividad
            activity_type = activity_data.get('type', 'todo')
            if activity_type == 'call':
                vals['activity_type_id'] = request.env.ref('mail.mail_activity_data_call').id
            elif activity_type == 'email':
                vals['activity_type_id'] = request.env.ref('mail.mail_activity_data_email').id
            else:
                vals['activity_type_id'] = request.env.ref('mail.mail_activity_data_todo').id

            request.env['mail.activity'].sudo().create(vals)
            return {'success': True, 'message': 'Actividad creada'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
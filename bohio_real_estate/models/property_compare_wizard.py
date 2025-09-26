from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import base64
import datetime


class PropertyCompareWizard(models.TransientModel):
    _name = 'property.compare.wizard'
    _description = 'Asistente de Comparación de Propiedades BOHÍO'

    property_ids = fields.Many2many(
        'product.template',
        string='Propiedades a Comparar',
        required=True,
        domain=[('is_property', '=', True)]
    )

    # Información del cliente
    client_name = fields.Char('Nombre del Cliente')
    client_email = fields.Char('Email del Cliente')
    client_phone = fields.Char('Teléfono del Cliente')
    client_id = fields.Many2one('res.partner', string='Cliente')

    # Opciones de comparación
    include_images = fields.Boolean('Incluir Imágenes', default=True)
    include_amenities = fields.Boolean('Incluir Amenidades', default=True)
    include_price_details = fields.Boolean('Incluir Detalles de Precio', default=True)
    include_location_map = fields.Boolean('Incluir Mapa de Ubicación', default=False)

    notes = fields.Text('Notas Adicionales')

    # Formato de salida
    output_format = fields.Selection([
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('html', 'HTML')
    ], string='Formato de Salida', default='pdf', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        # Si viene desde una selección múltiple, cargar las propiedades
        if self._context.get('active_model') == 'product.template' and self._context.get('active_ids'):
            res['property_ids'] = [(6, 0, self._context.get('active_ids'))]

        # Si viene desde CRM, intentar obtener datos del cliente
        if self._context.get('active_model') == 'crm.lead' and self._context.get('active_id'):
            lead = self.env['crm.lead'].browse(self._context.get('active_id'))
            if lead.partner_id:
                res.update({
                    'client_id': lead.partner_id.id,
                    'client_name': lead.partner_id.name,
                    'client_email': lead.partner_id.email,
                    'client_phone': lead.partner_id.phone or lead.partner_id.mobile,
                })
            # Si el lead tiene propiedades asociadas
            if hasattr(lead, 'property_ids') and lead.property_ids:
                res['property_ids'] = [(6, 0, lead.property_ids.ids)]

        return res

    @api.onchange('client_id')
    def _onchange_client_id(self):
        if self.client_id:
            self.client_name = self.client_id.name
            self.client_email = self.client_id.email
            self.client_phone = self.client_id.phone or self.client_id.mobile

    @api.constrains('property_ids')
    def _check_properties_limit(self):
        for record in self:
            if len(record.property_ids) > 6:
                raise ValidationError('Solo puede comparar hasta 6 propiedades a la vez.')
            if len(record.property_ids) < 2:
                raise ValidationError('Debe seleccionar al menos 2 propiedades para comparar.')

    def _prepare_report_data(self):
        """Preparar datos estructurados para el reporte"""
        self.ensure_one()

        data = {
            'doc': {
                'client_name': self.client_name,
                'client_email': self.client_email,
                'client_phone': self.client_phone,
                'notes': self.notes,
                'date': datetime.datetime.now(),
                'include_images': self.include_images,
                'include_amenities': self.include_amenities,
                'include_price_details': self.include_price_details,
            },
            'properties': [],
        }

        # Recopilar datos de cada propiedad
        for property in self.property_ids:
            prop_data = {
                'id': property.id,
                'name': property.name,
                'default_code': property.default_code,
                'image_1920': property.image_1920 if self.include_images else False,

                # Información básica
                'property_type': property.property_type if hasattr(property, 'property_type') else False,
                'transaction_type': property.transaction_type if hasattr(property, 'transaction_type') else False,
                'property_status': property.property_status if hasattr(property, 'property_status') else False,

                # Precios
                'list_price': property.list_price,
                'administration_fee': property.administration_fee if hasattr(property, 'administration_fee') else 0,

                # Ubicación
                'city_id': property.city_id if hasattr(property, 'city_id') else False,
                'state_id': property.state_id if hasattr(property, 'state_id') else False,
                'neighborhood': property.neighborhood if hasattr(property, 'neighborhood') else False,
                'address': property.address if hasattr(property, 'address') else False,
                'stratum': property.stratum if hasattr(property, 'stratum') else False,

                # Características físicas
                'built_area': property.built_area if hasattr(property, 'built_area') else 0,
                'land_area': property.land_area if hasattr(property, 'land_area') else 0,
                'num_bedrooms': property.num_bedrooms if hasattr(property, 'num_bedrooms') else 0,
                'num_bathrooms': property.num_bathrooms if hasattr(property, 'num_bathrooms') else 0,
                'parking_spaces': property.parking_spaces if hasattr(property, 'parking_spaces') else 0,
                'year_built': property.year_built if hasattr(property, 'year_built') else False,

                # Amenidades
                'has_pool': property.has_pool if hasattr(property, 'has_pool') else False,
                'has_gym': property.has_gym if hasattr(property, 'has_gym') else False,
                'has_elevator': property.has_elevator if hasattr(property, 'has_elevator') else False,
                'has_security': property.has_security if hasattr(property, 'has_security') else False,
                'has_garden': property.has_garden if hasattr(property, 'has_garden') else False,
                'has_terrace': property.has_terrace if hasattr(property, 'has_terrace') else False,
                'has_balcony': property.has_balcony if hasattr(property, 'has_balcony') else False,
            }

            data['properties'].append(prop_data)

        return data

    def action_print_comparison(self):
        """Generar reporte de comparación"""
        self.ensure_one()

        if self.output_format == 'pdf':
            return self._generate_pdf_report()
        elif self.output_format == 'excel':
            return self._generate_excel_report()
        elif self.output_format == 'html':
            return self._generate_html_report()

    def _generate_pdf_report(self):
        """Generar reporte PDF"""
        # Preparar datos para el reporte
        data = self._prepare_report_data()

        # Retornar la acción del reporte
        return self.env.ref('bohio_real_estate.report_property_comparison').report_action(
            self.property_ids,
            data=data
        )

    def _generate_excel_report(self):
        """Generar reporte Excel"""
        # TODO: Implementar generación de Excel
        raise UserError('La exportación a Excel estará disponible próximamente.')

    def _generate_html_report(self):
        """Generar reporte HTML"""
        # TODO: Implementar generación de HTML
        raise UserError('La exportación a HTML estará disponible próximamente.')

    def action_send_by_email(self):
        """Enviar comparación por email"""
        self.ensure_one()

        if not self.client_email:
            raise UserError('Por favor ingrese un email del cliente.')

        # Generar el PDF
        pdf = self.env.ref('bohio_real_estate.report_property_comparison')._render_qweb_pdf(
            self.property_ids.ids,
            data=self._prepare_report_data()
        )[0]

        # Crear adjunto
        attachment = self.env['ir.attachment'].create({
            'name': f'Comparacion_Propiedades_{fields.Date.today()}.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf),
            'mimetype': 'application/pdf',
        })

        # Preparar valores del email
        mail_values = {
            'subject': f'Comparación de Propiedades - BOHÍO Inmobiliaria',
            'body_html': f'''
                <p>Estimado/a {self.client_name or 'Cliente'},</p>
                <p>Adjunto encontrará la comparación de propiedades solicitada.</p>
                <p>Las propiedades comparadas son:</p>
                <ul>
                    {''.join([f'<li>{prop.name}</li>' for prop in self.property_ids])}
                </ul>
                <p>Si tiene alguna pregunta o desea programar una visita, no dude en contactarnos.</p>
                <br/>
                <p>Saludos cordiales,</p>
                <p><strong>BOHÍO Inmobiliaria</strong><br/>
                "Tu hogar, nuestra pasión"<br/>
                Tel: (+57) 300 123 4567<br/>
                Email: info@bohio.com.co<br/>
                Web: www.bohio.com.co</p>
            ''',
            'email_to': self.client_email,
            'attachment_ids': [(4, attachment.id)],
        }

        # Crear y enviar el email
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Email Enviado',
                'message': f'La comparación ha sido enviada a {self.client_email}',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_create_lead(self):
        """Crear un lead en CRM desde la comparación"""
        self.ensure_one()

        if not self.client_name:
            raise UserError('Por favor ingrese el nombre del cliente para crear el lead.')

        # Crear o buscar el partner
        partner = self.client_id
        if not partner and (self.client_email or self.client_phone):
            partner = self.env['res.partner'].create({
                'name': self.client_name,
                'email': self.client_email,
                'phone': self.client_phone,
                'is_company': False,
            })

        # Crear el lead
        lead = self.env['crm.lead'].create({
            'name': f'Interés en propiedades - {self.client_name}',
            'partner_id': partner.id if partner else False,
            'contact_name': self.client_name,
            'email_from': self.client_email,
            'phone': self.client_phone,
            'description': f'''
                Cliente interesado en las siguientes propiedades:
                {chr(10).join([f"- {prop.name} (Ref: {prop.default_code or 'N/A'})" for prop in self.property_ids])}

                Notas adicionales:
                {self.notes or 'N/A'}
            ''',
            'property_ids': [(6, 0, self.property_ids.ids)] if hasattr(self.env['crm.lead'], 'property_ids') else False,
            'type': 'opportunity',
            'request_source': 'property_inquiry',
        })

        # Retornar acción para abrir el lead creado
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'res_id': lead.id,
            'view_mode': 'form',
            'target': 'current',
        }
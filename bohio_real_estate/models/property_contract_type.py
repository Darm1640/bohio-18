# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PropertyDocumentCategory(models.Model):
    """Categorías de documentos"""
    _name = 'property.document.category'
    _description = 'Categoría de Documento'
    _order = 'sequence, name'

    name = fields.Char('Nombre', required=True, translate=True)
    code = fields.Char('Código', required=True, index=True)
    sequence = fields.Integer('Secuencia', default=10)
    active = fields.Boolean(default=True)
    description = fields.Text('Descripción', translate=True)
    color = fields.Integer('Color', default=0)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'El código de la categoría debe ser único!')
    ]


class PropertyContractType(models.Model):
    """Tipos de contratos inmobiliarios (Arrendamiento, Venta, etc.)"""
    _name = 'property.contract.type'
    _description = 'Tipo de Contrato Inmobiliario'
    _order = 'sequence, name'

    name = fields.Char('Nombre', required=True, translate=True)
    code = fields.Char('Código', required=True, index=True)
    sequence = fields.Integer('Secuencia', default=10)
    active = fields.Boolean(default=True)

    description = fields.Text('Descripción', translate=True)

    # Configuración de documentos
    document_line_ids = fields.One2many(
        'property.contract.type.document',
        'contract_type_id',
        string='Documentos Requeridos'
    )

    # Template de contrato para firma
    contract_template_id = fields.Many2one(
        'ir.attachment',
        string='Plantilla de Contrato PDF',
        help='Plantilla PDF que se usará para generar el contrato a firmar',
        domain=[('mimetype', '=', 'application/pdf')]
    )

    # Configuración según Ley 820/2003
    applies_to_rent = fields.Boolean('Aplica a Arrendamiento', default=False)
    applies_to_sale = fields.Boolean('Aplica a Venta', default=False)

    # Tipo de arrendatario/comprador
    default_employment_type = fields.Selection([
        ('employee', 'Empleado'),
        ('independent', 'Independiente'),
        ('pensioner', 'Pensionado'),
        ('legal_entity', 'Persona Jurídica'),
    ], string='Tipo de Empleo por Defecto')

    color = fields.Integer('Color', default=0)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'El código del tipo de contrato debe ser único!')
    ]

    def action_view_documents(self):
        """Ver documentos configurados para este tipo de contrato"""
        return {
            'name': _('Documentos: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'property.contract.type.document',
            'view_mode': 'tree,form',
            'domain': [('contract_type_id', '=', self.id)],
            'context': {'default_contract_type_id': self.id}
        }


class PropertyContractTypeDocument(models.Model):
    """Documentos requeridos por tipo de contrato"""
    _name = 'property.contract.type.document'
    _description = 'Documento por Tipo de Contrato'
    _order = 'contract_type_id, sequence, name'

    contract_type_id = fields.Many2one(
        'property.contract.type',
        'Tipo de Contrato',
        required=True,
        ondelete='cascade'
    )

    sequence = fields.Integer('Secuencia', default=10)
    name = fields.Char('Nombre del Documento', required=True, translate=True)
    code = fields.Char('Código')

    # Clasificación según Ley 820/2003 Colombia
    document_category_id = fields.Many2one(
        'property.document.category',
        string='Categoría',
        required=True,
        ondelete='restrict'
    )

    # Configuración del requisito
    is_required = fields.Boolean(
        'Requerido por Defecto',
        default=False,
        help='Si está marcado, este documento será obligatorio en todos los contratos de este tipo'
    )

    is_optional = fields.Boolean(
        'Opcional',
        default=True,
        help='Si está marcado, el documento es opcional (no obligatorio)'
    )

    is_allowed_by_law = fields.Boolean(
        'Permitido por Ley 820/2003',
        default=True,
        help='Indica si este documento puede ser exigido legalmente en Colombia'
    )

    # Aplicabilidad según tipo de persona
    applies_to_employee = fields.Boolean('Aplica a Empleados')
    applies_to_independent = fields.Boolean('Aplica a Independientes')
    applies_to_pensioner = fields.Boolean('Aplica a Pensionados')
    applies_to_legal_entity = fields.Boolean('Aplica a Personas Jurídicas')
    applies_to_foreigner = fields.Boolean('Aplica a Extranjeros')

    description = fields.Text('Descripción/Instrucciones', translate=True)
    legal_reference = fields.Char('Referencia Legal')

    # Ejemplo de documento (para ayuda visual)
    example_attachment_id = fields.Many2one(
        'ir.attachment',
        string='Ejemplo de Documento',
        help='Documento de ejemplo/plantilla para guiar al usuario'
    )

    active = fields.Boolean(default=True)

    @api.constrains('is_required', 'is_optional')
    def _check_required_optional(self):
        for doc in self:
            if doc.is_required and doc.is_optional:
                raise ValidationError(_(
                    'Un documento no puede ser Requerido y Opcional al mismo tiempo.'
                ))

    @api.constrains('is_allowed_by_law', 'is_required')
    def _check_legal_compliance(self):
        for doc in self:
            if doc.is_required and not doc.is_allowed_by_law:
                raise ValidationError(_(
                    'No puede hacer requerido un documento que la ley no permite exigir: %s'
                ) % doc.name)


class PropertyContract(models.Model):
    """
    Extensión de property.contract con gestión de documentos y tipos de contrato.

    NOTA: Este modelo NO hereda de documents.mixin por defecto.
    Si el módulo 'documents' está instalado, los métodos relacionados
    funcionarán automáticamente. Si no está instalado, simplemente
    se omitirán las funcionalidades de documents.
    """
    _inherit = 'property.contract'

    # Tipo de contrato
    contract_type_id = fields.Many2one(
        'property.contract.type',
        string='Tipo de Contrato',
        tracking=True,
        index=True
    )

    # Líneas de documentos generadas desde el tipo
    document_checklist_ids = fields.One2many(
        'property.contract.document.checklist',
        'contract_id',
        string='Checklist de Documentos'
    )

    # Template de contrato (desde el tipo)
    contract_template_id = fields.Many2one(
        'ir.attachment',
        related='contract_type_id.contract_template_id',
        string='Plantilla de Contrato',
        readonly=True
    )

    # Documento de contrato generado (para firma)
    generated_contract_id = fields.Many2one(
        'ir.attachment',
        string='Contrato Generado',
        help='Documento PDF del contrato generado desde la plantilla'
    )

    # Nota: signature_state y signature_date ya existen en real_estate_bits.property_contract
    # No redefinir aquí para evitar duplicación

    # Tipo de arrendatario/comprador (para filtrar documentos)
    tenant_employment_type = fields.Selection([
        ('employee', 'Empleado'),
        ('independent', 'Independiente'),
        ('pensioner', 'Pensionado'),
        ('legal_entity', 'Persona Jurídica'),
    ], string='Tipo de Empleo')

    tenant_is_foreigner = fields.Boolean('Es Extranjero')

    # Progreso de documentos
    document_progress = fields.Float(
        'Progreso de Documentos (%)',
        compute='_compute_document_progress',
        store=True
    )

    required_docs_count = fields.Integer(
        'Docs Requeridos',
        compute='_compute_document_counts'
    )

    received_docs_count = fields.Integer(
        'Docs Recibidos',
        compute='_compute_document_counts'
    )

    @api.depends('document_checklist_ids.is_required', 'document_checklist_ids.is_received')
    def _compute_document_progress(self):
        for contract in self:
            required = contract.document_checklist_ids.filtered('is_required')
            if required:
                received = len(required.filtered('is_received'))
                contract.document_progress = (received / len(required)) * 100
            else:
                contract.document_progress = 0.0

    @api.depends('document_checklist_ids')
    def _compute_document_counts(self):
        for contract in self:
            contract.required_docs_count = len(contract.document_checklist_ids.filtered('is_required'))
            contract.received_docs_count = len(contract.document_checklist_ids.filtered('is_received'))

    @api.onchange('contract_type_id')
    def _onchange_contract_type(self):
        """Al cambiar tipo de contrato, regenerar checklist"""
        if self.contract_type_id:
            # Establecer tipo de empleo por defecto del tipo de contrato
            if self.contract_type_id.default_employment_type:
                self.tenant_employment_type = self.contract_type_id.default_employment_type

            # Generar checklist automáticamente
            if not self.document_checklist_ids:
                self.action_generate_document_checklist()

    @api.onchange('tenant_employment_type', 'tenant_is_foreigner')
    def _onchange_tenant_info(self):
        """Al cambiar info del arrendatario, filtrar documentos aplicables"""
        if self.contract_type_id and (self.tenant_employment_type or self.tenant_is_foreigner):
            self.action_generate_document_checklist()

    def action_generate_document_checklist(self):
        """Genera checklist de documentos desde el tipo de contrato"""
        self.ensure_one()

        if not self.contract_type_id:
            return

        # Limpiar checklist anterior
        self.document_checklist_ids.unlink()

        # Obtener documentos del tipo de contrato
        documents = self.contract_type_id.document_line_ids.filtered('active')

        # Filtrar por tipo de empleo
        if self.tenant_employment_type:
            field_name = f'applies_to_{self.tenant_employment_type}'
            documents = documents.filtered(lambda d: d[field_name] or (not any([
                d.applies_to_employee,
                d.applies_to_independent,
                d.applies_to_pensioner,
                d.applies_to_legal_entity
            ])))

        # Agregar documentos de extranjero si aplica
        if self.tenant_is_foreigner:
            foreigner_docs = self.contract_type_id.document_line_ids.filtered(
                lambda d: d.applies_to_foreigner and d.active
            )
            documents |= foreigner_docs

        # Crear líneas de checklist
        checklist_vals = []
        for doc in documents:
            checklist_vals.append({
                'contract_id': self.id,
                'document_type_line_id': doc.id,
                'name': doc.name,
                'is_required': doc.is_required,
                'is_optional': doc.is_optional,
            })

        if checklist_vals:
            self.env['property.contract.document.checklist'].create(checklist_vals)

    # ======================================
    # INTEGRACIÓN CON DOCUMENTS (Odoo Enterprise)
    # ======================================

    def _get_document_folder(self):
        """Define la carpeta donde se guardarán los documentos del contrato"""
        if not self._check_create_documents():
            return self.env['documents.document']

        # Buscar o crear carpeta "Contratos"
        Folder = self.env['documents.document'].sudo()
        folder = Folder.search([
            ('name', '=', 'Contratos'),
            ('type', '=', 'folder'),
            ('parent_folder_id', '=', False)
        ], limit=1)

        if not folder:
            workspace = self.env['documents.workspace'].sudo().search([], limit=1)
            if workspace:
                folder = Folder.create({
                    'name': 'Contratos',
                    'type': 'folder',
                    'workspace_id': workspace.id,
                })

        return folder

    def _get_document_owner(self):
        """Define el propietario de los documentos (vendedor/agente)"""
        return self.user_id if self.user_id else self.env.user

    def _get_document_partner(self):
        """Define el partner relacionado (inquilino)"""
        return self.partner_id

    def _get_document_tags(self):
        """Define los tags para categorizar documentos"""
        if not self._check_create_documents():
            return self.env['documents.tag']

        tags = self.env['documents.tag'].sudo()
        result = self.env['documents.tag']

        # Tag por estado del contrato
        if self.state:
            state_tag = tags.search([('name', '=', f'Contrato {self.state}')], limit=1)
            if not state_tag:
                state_tag = tags.create({'name': f'Contrato {self.state}'})
            result |= state_tag

        # Tag por tipo de contrato
        if self.contract_type_id:
            type_tag = tags.search([('name', '=', self.contract_type_id.name)], limit=1)
            if not type_tag:
                type_tag = tags.create({'name': self.contract_type_id.name})
            result |= type_tag

        return result

    def _check_create_documents(self):
        """Solo crear documentos si existe el módulo documents instalado"""
        documents_installed = self.env['ir.module.module'].sudo().search([
            ('name', '=', 'documents'),
            ('state', '=', 'installed')
        ], limit=1)
        return bool(documents_installed)

    # ======================================
    # PREPARACIÓN DE DATOS PARA CONTRATO
    # ======================================

    def _prepare_contract_data(self):
        """
        Prepara todos los datos del contrato para insertar en el template PDF.
        Retorna un diccionario con todos los campos necesarios para el contrato.
        """
        self.ensure_one()

        # Obtener propietario(s)
        owners_data = []
        if self.contract_line_ids:
            for line in self.contract_line_ids.filtered(lambda l: l.state == 'active'):
                if line.property_id and line.property_id.partner_id:
                    owners_data.append({
                        'name': line.property_id.partner_id.name,
                        'vat': line.property_id.partner_id.vat or '',
                        'property_code': line.property_id.default_code or '',
                    })

        if not owners_data and self.property_id and self.property_id.partner_id:
            owners_data.append({
                'name': self.property_id.partner_id.name,
                'vat': self.property_id.partner_id.vat or '',
                'property_code': self.property_id.default_code or '',
            })

        # Datos detallados de la propiedad
        property_data = {
            'code': self.property_code,
            'address': self.address,
            'city': self.property_id.city if self.property_id else '',
            'state': self.property_id.state_id.name if self.property_id and self.property_id.state_id else '',
            'neighborhood': self.property_id.neighborhood if self.property_id else '',
            'area': self.property_area,
            'area_formatted': f"{self.property_area:,.2f} m²",
            'floor': self.floor,
            'stratum': dict(self.property_id._fields['stratum'].selection).get(self.property_id.stratum) if self.property_id and self.property_id.stratum else '',
            'type': dict(self.property_id._fields['property_type'].selection).get(self.property_id.property_type) if self.property_id and self.property_id.property_type else '',
            'num_bedrooms': self.property_id.num_bedrooms if self.property_id else 0,
            'num_bathrooms': self.property_id.num_bathrooms if self.property_id else 0,
            'garage': self.property_id.garage if self.property_id else False,
            'n_garage': self.property_id.n_garage if self.property_id else 0,
            'furnished': self.property_id.furnished if self.property_id else False,
        }

        return {
            'contract': {'number': self.name, 'type': self.contract_type_id.name if self.contract_type_id else ''},
            'tenant': {'name': self.partner_id.name, 'vat': self.partner_id.vat or ''},
            'owners': owners_data,
            'financial': {
                'rental_fee': self.rental_fee,
                'rental_fee_formatted': f"${self.rental_fee:,.2f}",
                'amount_total': self.amount_total,
                'amount_total_formatted': f"${self.amount_total:,.2f}",
            },
            'dates': {
                'date_from': self.date_from.strftime('%d/%m/%Y') if self.date_from else '',
                'date_to': self.date_to.strftime('%d/%m/%Y') if self.date_to else '',
                'contract_duration_months': self.rent,
            },
            'property': property_data,
        }

    # ======================================
    # FIRMA ELECTRÓNICA
    # ======================================

    def action_request_contract_signature(self):
        """Genera el contrato desde la plantilla y lo marca como enviado para firma"""
        self.ensure_one()

        if not self.contract_type_id or not self.contract_type_id.contract_template_id:
            raise ValidationError(_('Debe configurar una plantilla de contrato en el tipo de contrato'))

        template = self.contract_type_id.contract_template_id
        contract_name = f'Contrato_{self.name}_{self.partner_id.name}.pdf'
        contract_data = self._prepare_contract_data()

        # Crear attachment con descripción
        new_attachment = template.copy({
            'name': contract_name,
            'res_model': 'property.contract',
            'res_id': self.id,
            'description': f"""Contrato: {contract_data['contract']['number']}
Arrendatario: {contract_data['tenant']['name']}
Valor: {contract_data['financial']['rental_fee_formatted']}
Período: {contract_data['dates']['date_from']} - {contract_data['dates']['date_to']}""",
        })

        # Si documents está instalado, crear documento
        if self._check_create_documents():
            self.env['documents.document'].sudo().create({
                'name': contract_name,
                'attachment_id': new_attachment.id,
                'folder_id': self._get_document_folder().id,
                'owner_id': self._get_document_owner().id,
                'partner_id': self._get_document_partner().id,
                'tag_ids': [(6, 0, self._get_document_tags().ids)],
            })

        # Actualizar contrato (usar 'pending' del signature_state existente)
        self.write({'generated_contract_id': new_attachment.id, 'signature_state': 'pending'})

        # Registrar en chatter
        self.message_post(
            body=f"""<p><strong>Contrato generado para firma</strong></p>
<ul>
    <li>Arrendatario: {contract_data['tenant']['name']}</li>
    <li>Propietario(s): {', '.join([o['name'] for o in contract_data['owners']])}</li>
    <li>Valor mensual: {contract_data['financial']['rental_fee_formatted']}</li>
    <li>Período: {contract_data['dates']['date_from']} - {contract_data['dates']['date_to']}</li>
</ul>""",
            subject='Contrato Generado'
        )

        # Si sign está instalado, abrir wizard de firma
        sign_installed = self.env['ir.module.module'].sudo().search([('name', '=', 'sign'), ('state', '=', 'installed')], limit=1)

        if sign_installed:
            # Preparar firmantes
            signers = [(0, 0, {'partner_id': self.partner_id.id})]
            for owner in contract_data['owners']:
                owner_partner = self.env['res.partner'].sudo().search([('name', '=', owner['name'])], limit=1)
                if owner_partner:
                    signers.append((0, 0, {'partner_id': owner_partner.id}))

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'sign.send.request',
                'view_mode': 'form',
                'context': {
                    'default_attachment_ids': [(6, 0, [new_attachment.id])],
                    'default_signer_ids': signers,
                    'default_subject': f"Firma de Contrato {self.name}",
                },
                'target': 'new',
            }

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': _('Contrato Generado'), 'message': _('Descárguelo desde "Ver Contrato"'), 'type': 'success'},
        }

    def action_open_generated_contract(self):
        """Abrir documento de contrato generado"""
        self.ensure_one()
        if not self.generated_contract_id:
            raise ValidationError(_('No hay contrato generado.'))

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self.generated_contract_id.id}?download=true',
            'target': 'new',
        }


class PropertyContractDocumentChecklist(models.Model):
    """Checklist de documentos por contrato individual"""
    _name = 'property.contract.document.checklist'
    _description = 'Checklist de Documentos del Contrato'
    _order = 'sequence, name'

    contract_id = fields.Many2one(
        'property.contract',
        'Contrato',
        required=True,
        ondelete='cascade',
        index=True
    )

    document_type_line_id = fields.Many2one(
        'property.contract.type.document',
        'Tipo de Documento',
        ondelete='restrict'
    )

    sequence = fields.Integer('Secuencia', related='document_type_line_id.sequence', store=True)
    name = fields.Char('Documento', required=True)

    # Estados
    is_required = fields.Boolean('Requerido', default=False)
    is_optional = fields.Boolean('Opcional', default=True)
    is_received = fields.Boolean('Recibido', default=False, tracking=True)
    is_verified = fields.Boolean('Verificado', default=False, tracking=True)

    # Fechas
    received_date = fields.Date('Fecha Recepción')
    verified_date = fields.Date('Fecha Verificación')
    verified_by_id = fields.Many2one('res.users', 'Verificado Por')

    # Archivos adjuntos
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'contract_checklist_attachment_rel',
        'checklist_id',
        'attachment_id',
        string='Archivos',
        domain="[('res_model', '=', 'property.contract'), ('res_id', '=', contract_id)]"
    )

    attachment_count = fields.Integer(
        'N° Archivos',
        compute='_compute_attachment_count'
    )

    notes = fields.Text('Observaciones')

    # Campos relacionados
    document_category_id = fields.Many2one(
        related='document_type_line_id.document_category_id',
        string='Categoría',
        store=True
    )

    is_allowed_by_law = fields.Boolean(
        related='document_type_line_id.is_allowed_by_law',
        string='Permitido por Ley'
    )

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = len(rec.attachment_ids)

    @api.onchange('is_received')
    def _onchange_is_received(self):
        if self.is_received and not self.received_date:
            self.received_date = fields.Date.today()

    @api.onchange('is_verified')
    def _onchange_is_verified(self):
        if self.is_verified:
            if not self.verified_date:
                self.verified_date = fields.Date.today()
            if not self.verified_by_id:
                self.verified_by_id = self.env.user

    def action_mark_received(self):
        """Marcar como recibido"""
        self.write({
            'is_received': True,
            'received_date': fields.Date.today(),
        })

    def action_mark_verified(self):
        """Marcar como verificado"""
        self.write({
            'is_verified': True,
            'verified_date': fields.Date.today(),
            'verified_by_id': self.env.user.id,
        })

    def action_upload_document(self):
        """Abrir wizard para subir documento"""
        return {
            'name': _('Subir Documento: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': 'property.contract',
                'default_res_id': self.contract_id.id,
                'default_name': self.name,
            }
        }

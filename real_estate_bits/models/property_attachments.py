from odoo import api, fields, models, _


class IrAttachment(models.Model):
    """Extensión de ir.attachment para propiedades inmobiliarias"""
    _inherit = 'ir.attachment'

    document_type = fields.Selection([
        ('legal', 'Legal'),
        ('technical', 'Técnico'),
        ('commercial', 'Comercial'),
        ('photo', 'Fotografía'),
        ('plan', 'Plano'),
        ('certificate', 'Certificado'),
        ('contract', 'Contrato'),
        ('brochure', 'Folleto'),
        ('video', 'Video'),
        ('other', 'Otro')
    ], string='Tipo Documento', default='other')

    is_property_document = fields.Boolean('Es Documento de Propiedad', default=False, index=True)
    is_brochure = fields.Boolean('Es Folleto', default=False)
    document_sequence = fields.Integer('Secuencia', default=10)
    video_url = fields.Char('URL Video', help='URL de video para mostrar la propiedad')

    expiration_date = fields.Date('Fecha Vencimiento')
    is_expired = fields.Boolean('Vencido', compute='_compute_is_expired', store=True)

    @api.depends('expiration_date')
    def _compute_is_expired(self):
        today = fields.Date.today()
        for doc in self:
            doc.is_expired = doc.expiration_date and doc.expiration_date < today if doc.expiration_date else False


class ProjectWorksite(models.Model):
    _inherit = 'project.worksite'

    property_plan_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        domain=lambda self: [('res_model', '=', 'project.worksite'), ('document_type', '=', 'plan')],
        string='Floor Plans',
        context={'default_res_model': 'project.worksite', 'default_document_type': 'plan', 'default_is_property_document': True}
    )

    project_attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        domain=lambda self: [('res_model', '=', 'project.worksite'), ('is_property_document', '=', True)],
        string='Documentos del Proyecto'
    )

    project_document_count = fields.Integer('Cant. Documentos', compute='_compute_project_document_count')

    def _compute_project_document_count(self):
        for record in self:
            record.project_document_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', 'project.worksite'),
                ('res_id', '=', record.id),
                ('is_property_document', '=', True)
            ])


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    property_attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        domain=lambda self: [('res_model', '=', 'product.template'), ('is_property_document', '=', True)],
        string='Documentos de Propiedad',
        help='Documentos asociados a esta propiedad'
    )

    document_count = fields.Integer('Cant. Documentos', compute='_compute_document_count')

    def _compute_document_count(self):
        for record in self:
            record.document_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', 'product.template'),
                ('res_id', '=', record.id),
                ('is_property_document', '=', True)
            ])

    def action_view_documents(self):
        self.ensure_one()
        return {
            'name': _('Documentos de Propiedad'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'list,form',
            'domain': [
                ('res_model', '=', 'product.template'),
                ('res_id', '=', self.id),
                ('is_property_document', '=', True)
            ],
            'context': {
                'default_res_model': 'product.template',
                'default_res_id': self.id,
                'default_is_property_document': True
            }
        }


class PropertyContract(models.Model):
    _inherit = 'property.contract'

    contract_attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        domain=lambda self: [('res_model', '=', 'property.contract'), ('is_property_document', '=', True)],
        string='Documentos del Contrato'
    )

    contract_document_count = fields.Integer('Cant. Documentos', compute='_compute_contract_document_count')

    def _compute_contract_document_count(self):
        for record in self:
            record.contract_document_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', 'property.contract'),
                ('res_id', '=', record.id),
                ('is_property_document', '=', True)
            ])
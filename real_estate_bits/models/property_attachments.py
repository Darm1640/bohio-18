from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


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
        ('invoice', 'Factura'),
        ('payment', 'Comprobante de Pago'),
        ('receipt', 'Recibo'),
        ('tax_document', 'Documento Tributario'),
        ('identification', 'Identificación'),
        ('insurance', 'Seguro'),
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


class PropertyImage(models.Model):
    """Galería de imágenes para propiedades"""
    _name = 'property.image'
    _description = 'Imagen de Propiedad'
    _inherit = ['image.mixin']
    _order = 'sequence, id'

    name = fields.Char('Nombre', required=True)
    sequence = fields.Integer('Secuencia', default=10)

    property_id = fields.Many2one('product.template', 'Propiedad', required=True, ondelete='cascade', index=True)

    image_1920 = fields.Image('Imagen', max_width=1920, max_height=1920)

    image_type = fields.Selection([
        ('main', 'Principal'),
        ('exterior', 'Exterior'),
        ('interior', 'Interior'),
        ('bathroom', 'Baño'),
        ('kitchen', 'Cocina'),
        ('bedroom', 'Habitación'),
        ('amenity', 'Amenidad'),
        ('view', 'Vista'),
        ('floor_plan', 'Plano'),
        ('other', 'Otra')
    ], string='Tipo', default='other', required=True)

    is_cover = fields.Boolean('Portada', default=False, help='Usar como imagen principal')
    is_public = fields.Boolean('Pública', default=True, help='Visible en portal y website')

    description = fields.Char('Descripción')

    @api.constrains('is_cover', 'property_id')
    def _check_single_cover(self):
        for image in self:
            if image.is_cover:
                other_covers = self.search([
                    ('property_id', '=', image.property_id.id),
                    ('is_cover', '=', True),
                    ('id', '!=', image.id)
                ])
                if other_covers:
                    raise ValidationError(_('Solo puede haber una imagen de portada por propiedad.'))

    @api.model_create_multi
    def create(self, vals_list):
        results = super().create(vals_list)
        for result in results:
            if result.is_cover and result.property_id:
                result.property_id.image_1920 = result.image_1920
        return results

    def write(self, vals):
        result = super().write(vals)
        if 'is_cover' in vals and vals['is_cover']:
            for image in self:
                if image.property_id:
                    image.property_id.image_1920 = image.image_1920
        return result


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

    property_image_ids = fields.One2many('property.image', 'property_id', 'Galería de Imágenes')
    property_attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        domain=lambda self: [('res_model', '=', 'product.template'), ('is_property_document', '=', True)],
        string='Documentos de Propiedad',
        context={'default_res_model': 'product.template', 'default_is_property_document': True}
    )

    document_count = fields.Integer('Documentos', compute='_compute_document_count')
    image_count = fields.Integer('Imágenes', compute='_compute_image_count')

    def _compute_document_count(self):
        for record in self:
            record.document_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', 'product.template'),
                ('res_id', '=', record.id),
                ('is_property_document', '=', True)
            ])

    @api.depends('property_image_ids')
    def _compute_image_count(self):
        for record in self:
            record.image_count = len(record.property_image_ids)

    def action_view_documents(self):
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

    def action_view_images(self):
        return {
            'name': _('Galería de Imágenes'),
            'type': 'ir.actions.act_window',
            'res_model': 'property.image',
            'view_mode': 'kanban,list,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id}
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
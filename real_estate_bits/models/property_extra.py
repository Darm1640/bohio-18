from odoo import api, fields, models, _
from odoo.exceptions import UserError



class PropertyType(models.Model):
    _name = "property.type"
    _description = "Tipo de Propiedad"
    _parent_name = "parent_id"
    _parent_store = True
    _order = "name"
    _rec_name = "name"
    _inherit = ["website.published.mixin"]
    
    @api.depends("name", "parent_id")
    def _compute_display_name(self):
        """Forms complete name of property type from parent to child."""
        for rec in self:
            if rec.parent_id:
                rec.display_name = f"{rec.parent_id.display_name} / {rec.name}"
            else:
                rec.display_name = rec.name

    name = fields.Char(string="Nombre del Tipo", required=True)
    display_name = fields.Char("Nombre Completo", compute="_compute_display_name", recursive=True, store=True)
    parent_id = fields.Many2one("property.type", "Tipo Padre", ondelete="cascade")
    child_ids = fields.One2many("property.type", "parent_id", "Tipos Hijos")
    parent_left = fields.Integer("Left Parent", index=True)
    parent_right = fields.Integer("Right Parent", index=True)
    parent_path = fields.Char(index=True)
    property_type = fields.Selection([
        ('bodega', 'Bodega'),
        ('local', 'Local'),
        ('apartment', 'Apartamento'),
        ('house', 'Casa'),
        ('studio', 'Apartaestudio'),
        ('office', 'Oficina'),
        ('finca', 'Finca'),
        ('lot', 'Lote'),
        ('hotel', 'Hotel'),
        ('cabin', 'Cabaña'),
        ('building', 'Edificio'),
        ('country_lot', 'Lote Campestre'),
        ('blueprint', 'Sobre Plano'),
        ('plot', 'Parcela'),
        ('project', 'Proyecto')
    ], string='Tipo de Inmueble', required=True)
    product_category_id = fields.Many2one("product.category", "Categoría de Producto", readonly=True)
    
    visible_characteristics = fields.Text("Características Visibles", 
                                        help="JSON con las características que se muestran para este tipo")
    
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-crear categoría de producto al crear tipo de propiedad"""
        records = super().create(vals_list)
        for record in records:
            record._create_product_category()
        return records
    
    def write(self, vals):
        """Actualizar categoría de producto al modificar tipo"""
        result = super().write(vals)
        if 'name' in vals or 'parent_id' in vals:
            for rec in self:
                rec._update_product_category()
        return result
    
    def _create_product_category(self):
        """Crear categoría de producto asociada"""
        self.ensure_one()

        # Buscar o crear categoría padre "Tipos de Propiedades"
        parent_category = self.env['product.category'].search([
            ('name', '=', 'Tipos de Propiedades'),
            ('parent_id', '=', False)
        ], limit=1)

        if not parent_category:
            parent_category = self.env['product.category'].create({
                'name': 'Tipos de Propiedades'
            })

        # Determinar categoría padre para este tipo
        category_parent_id = parent_category.id
        if self.parent_id and self.parent_id.product_category_id:
            category_parent_id = self.parent_id.product_category_id.id

        # Crear categoría
        category = self.env['product.category'].create({
            'name': self.name,
            'parent_id': category_parent_id,
            #'property_type': 'product'
        })

        self.product_category_id = category.id
    
    def _update_product_category(self):
        """Actualizar categoría de producto existente"""
        self.ensure_one()
        if self.product_category_id:
            vals = {'name': self.name}
            if self.parent_id and self.parent_id.product_category_id:
                vals['parent_id'] = self.parent_id.product_category_id.id
            self.product_category_id.write(vals)


class ProductCategory(models.Model):
    _inherit = "product.category"


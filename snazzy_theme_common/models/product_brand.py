# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.addons.website_sale.controllers import main
import logging
_logger = logging.getLogger(__name__)

class ProductBrand(models.Model):
    _name = "product.brand"
    _description = "Product Brand"
    _rec_name = "display_name"

    @api.depends("name", "parent_id", "parent_id.name")
    def _get_display_name(self):
        for obj in self:
            display_name = obj.name
            parent_id = obj.parent_id
            while parent_id:
                display_name = parent_id.name + " / " + display_name
                parent_id = parent_id.parent_id
            obj.display_name = display_name

    def get_product_brand_count(self):
        for obj in self:
            domain = [('brand_id', '=', obj.id), ('is_published', '=', True)]
            if not obj.env.user.has_group('base.group_system'):
                domain.append(("website_published", '=', True))
            ctx = self.env.context or {}
            if 'product_brand_search' in ctx and ctx['product_brand_search']:
                domain.append(("name", 'ilike', ctx['product_brand_search'].strip()))
            product_template = self.env['product.template'].search(domain)
            obj.brand_count = len(product_template.ids)

    name = fields.Char("Name")
    brand_decription = fields.Text("Description")
    parent_id = fields.Many2one("product.brand", "Parent Brand")
    sequence = fields.Integer("Sequence", default=1)
    display_name = fields.Char("Dispaly Name", compute="_get_display_name", store=True)
    image = fields.Binary(
        attachment=True, help="This field holds the image used as image for the Brand, limited to 1024x1024px.")
    brand_count = fields.Integer("Total Product", compute="get_product_brand_count")
    product_ids = fields.One2many(
        'product.template',
        'brand_id',
        string='Product Brands',
    )
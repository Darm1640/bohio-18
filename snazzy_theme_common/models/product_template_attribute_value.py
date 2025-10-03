# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api

class ProductAttributeInherit(models.Model):

    _inherit = 'product.attribute.value'

    def get_product_attribute_count(self):
        for obj in self:
            domain = [('attribute_line_ids.value_ids', '=', obj.id), ('is_published', '=', True)]
            if not obj.env.user.has_group('base.group_system'):
                domain.append(("website_published", '=', True))
            ctx = self.env.context or {}
            if 'product_attribute_search' in ctx and ctx['product_attribute_search']:
                domain.append(("name", 'ilike', ctx['product_attribute_search'].strip()))
            product_template = self.env['product.template'].search(domain)
            obj.attribute_count = len(product_template.ids)

    attribute_count = fields.Integer("Total Product", compute="get_product_attribute_count")
class ProductTemplateAttributeValue(models.Model):

    _inherit = "product.template.attribute.value"

    color_attrib_img = fields.Image("Variant Color Image", max_width=1024, max_height=1024, store=True)
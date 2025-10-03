# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.addons.website_sale.controllers import main
import logging
_logger = logging.getLogger(__name__)
class ProductPublicCategory(models.Model):
    _inherit = "product.public.category"

    @api.depends('parents_and_self')
    def _compute_display_name(self):
        for category in self:
            if category.parents_and_self.mapped('name'):
                category.display_name = " / ".join(str(c) for c in category.parents_and_self.mapped('name') if c)
            else:
                category.display_name = ""

    def get_product_category_count(self):
        for obj in self:
            categ_ids = [obj.id]
            sub_ids = [obj.id]
            while sub_ids:
                sub_ids = obj.env['product.public.category'].sudo().search([('parent_id', 'in', sub_ids)]).ids
                categ_ids = categ_ids + sub_ids
            domain = [('public_categ_ids', 'in', list(set(categ_ids))),('is_published', '=', True)]
            if not obj.env.user.has_group('base.group_system'):
                domain.append(("website_published", '=', True))
            ctx = obj.env.context or {}
            if 'product_categ_search' in ctx and ctx['product_categ_search']:
                domain.append(("name", 'ilike', ctx['product_categ_search'].strip()))
            product_template = self.env['product.template'].search(domain)
            obj.product_tmpl_count = len(product_template.ids)

    product_tmpl_count = fields.Integer(string="Total Product", compute="get_product_category_count")
    auto_assign = fields.Boolean("Auto Assign")
    quick_categ = fields.Boolean("Quick Category for Mobile", help='Categories visible on mobile view for Quick Search')
    category_bg_image = fields.Binary('Category Background Image', readonly=False)
    category_icon = fields.Binary('Category Icon', readonly=False)
    category_in_header = fields.Boolean("Show Category in Header", help='Boolean to Show Category in Header')
    
    def get_all_parent_category(self):
        website = self.env['website'].get_current_website()
        domain = [('parent_id','=',False)] + website.website_domain()
        category = self.env['product.public.category'].search(domain)
        return category
    
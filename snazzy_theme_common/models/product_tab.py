# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
from odoo.tools.translate import html_translate

class ProductTab(models.Model):
    _name = 'product.tab'
    _description = 'Product Tab'
    _rec_name = 'name'

    def _default_content(self):
        return '''
            <div class="oe_structure oe_empty" data-editor-message="WRITE HERE OR DRAG BUILDING BLOCKS">
            <p class="o_default_snippet_text">''' + _("Start writing here...") + '''</p></div>
        '''

    name = fields.Char(string="Name")
    sequence = fields.Integer(string="Sequence", default=1)
    content = fields.Html(string="Content",translate=html_translate,
        sanitize_overridable=True,
        sanitize_attributes=False,
        sanitize_form=False)
    product_ids = fields.Many2many('product.template','product_tab_table','product_ids','tab_ids', string="product")

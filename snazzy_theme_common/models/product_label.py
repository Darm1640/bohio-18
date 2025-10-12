# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api

class ProductLabelBizople (models.Model):
   _name = 'product.label.bizople'
   _description = 'Product Label'
   
   _SELECTION_STYLE = [
      ('rounded', 'Rounded'),
      ('outlinesquare', 'Outline Square'),
      ('outlineround', 'Outline Rounded'),
      ('flat', 'Flat'),
   ]
     
   name = fields.Char(string="Name", translate=True, required=True)
   label_bg_color = fields.Char(string="Label Background Color", required=True,default="#f6513b")
   label_font_color = fields.Char(string="Label Font Color", required=True, default="#ffffff")
   label_style = fields.Selection(
      string='Label Style', selection=_SELECTION_STYLE, default='rounded')
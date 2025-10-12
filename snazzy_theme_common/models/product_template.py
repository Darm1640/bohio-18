# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo import models, fields, api, tools
from odoo import http , _
from odoo.http import request
import pytz
import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    biz_is_discounted_product = fields.Boolean(compute="_compute_biz_is_discounted_product", search="_search_biz_is_discounted_product")

    biz_total_sale_count = fields.Integer('Total Sale Count')
    brand_id = fields.Many2one("product.brand", "Brand")
    tab_ids = fields.Many2many('product.tab','product_tab_table','tab_ids','product_ids',string="Tab")
    product_label_id = fields.Many2one('product.label.bizople',string="Product Label")
    service_ids = fields.Many2many("product.service",string="Website Services")
    highlights_ids = fields.Many2many("product.highlights",string="Website Highlights")
    hover_image = fields.Image(string="Product Hover Image")

    def write(self, vals):
        for obj in self:
            vals['biz_total_sale_count'] = int(obj.sales_count)
            res = super(ProductTemplate, self).write(vals)
        return res

    @api.model
    def _search_get_detail(self, website, order, options):
        res = super(ProductTemplate, self)._search_get_detail(website=website, order=order, options=options)
        res.update({
            'requires_sudo': True
        })
        brand = options.get('brand')
        stock_avail = options.get('show_instock')
        old_domain = res['base_domain']
        if brand:
            old_domain.append([('brand_id', 'in', brand)])
        if stock_avail:
            old_domain.append([('type', '=', 'consu'),('is_storable', '=', True),('product_variant_ids.free_qty','>',1)])
        if options.get('search_term'):
            search_fields = res['search_fields']
            search_fields.append('attribute_line_ids.value_ids.name')
            mapping = res['mapping']
            mapping['attribute_line_ids.value_ids.name'] = {'name': 'name', 'type': 'text', 'match': True}
        return res

    # [T2515] Fix - Discount Filter
    def _search_biz_is_discounted_product(self, operator, value):
        website = request.env['website'].sudo().search([('id', '=', self._context.get('website_id'))])
        pricelist = website._get_current_pricelist()
        if pricelist:
            products = request.env['product.template'].sudo().search([
                ('sale_ok', '=', True),
                ('is_published', '=', True),
                '|',
                ('website_id', '=', website.id),
                ('website_id', '=', False),
                '|',
                ('company_id', '=', request.env.company.id),
                ('company_id', '=', False),
            ])
            discounted_products = []
            for product in products:
                pricelist_data = product._get_combination_info(only_template=True)
                if pricelist_data.get('has_discounted_price'):
                    discounted_products.append(product.id)
            operator = 'in' if operator == '!=' else 'not in'
            return [('id', operator, discounted_products)]
        return []

    def _compute_biz_is_discounted_product(self):
        for product in self:
            product.biz_is_discounted_product = False
    
    def _get_combination_info(self, combination=False, product_id=False, add_qty=1, parent_combination=False, only_template=False):
        rec = super(ProductTemplate, self)._get_combination_info(combination=combination, product_id=product_id, add_qty=add_qty, parent_combination=parent_combination, only_template=only_template)    
        counter = 0
        discount  = 0
        days = 0
        seconds = 0
        hours = 0
        minutes = 0
        end_date = 0
        time_diff = 0
        show_before_days = 0
        website = self.env['website'].get_current_website()
        pricelist = website.pricelist_id
        if pricelist:
            for items in pricelist.item_ids:
                if len(items.product_id) > 0 and items.date_end:
                    product_ids = items.product_id.id

                    if product_ids == rec['product_id']:
                        if items.percent_price > discount and items.date_start <= datetime.now() and items.date_end >= datetime.now():
                            counter = items.date_end - datetime.now()
                            discount = items.percent_price
                            end_date = items.date_end
                
                elif items.product_tmpl_id.id == rec['product_template_id'] and items.date_end:
                    if items.percent_price > discount and items.date_start <= datetime.now() and items.date_end >= datetime.now():
                        discount = items.percent_price
                        counter = items.date_end - datetime.now()
                        end_date = items.date_end
                elif items.applied_on == '2_product_category' and items.date_end:
                    product_obj = self.env['product.product'].sudo().search([('id','=',product_id)])
                    if product_obj:
                        if items.categ_id.id == product_obj.categ_id.id:
                            counter = items.date_end - datetime.now()
                            discount = items.percent_price
                            end_date = items.date_end
                elif items.applied_on == '3_global' and discount == 0 and items.date_end:
                    counter = items.date_end - datetime.now()
                    discount = items.percent_price
                    end_date = items.date_end
            show_before_days = pricelist.show_before_days
        if counter != 0:
            hours = counter.seconds//3600
            minutes = (counter.seconds//60)%60
            days = counter.days
            seconds = (counter.seconds) - (minutes * 60) - (hours * 3600)
            
        if end_date != 0:
            user = self.env.user
            if user and user.tz:
                end_date = datetime.strptime(str(end_date), '%Y-%m-%d %H:%M:%S')
                old_tz = pytz.timezone('UTC')
                new_tz = pytz.timezone(user.tz)
                end_date = old_tz.localize(end_date).astimezone(new_tz)
                show_time = end_date.date()-datetime.today().date()
                time_diff = show_time.days
            else:
                show_time = end_date.date()-datetime.today().date()
                time_diff = show_time.days

        product = self.env['product.product'].browse(rec['product_id']) or self
        rec.update({'days' :days,
                    'hours':hours,
                    'minutes':minutes,
                    'seconds':seconds,
                    'end_date':end_date,
                    'time':time_diff,
                    'counter_show_time': show_before_days,
                    'default_code':product.default_code,
                    })
        return rec
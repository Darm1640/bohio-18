# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

from odoo import models,fields,api

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'
    
    show_before_days = fields.Integer("Show Before Time")
    auto_assign = fields.Boolean("Auto Assign Category")
class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"
    
    @api.model
    def add_auto_product_category(self):
        category_ids = self.env['product.public.category'].search([('auto_assign', '=', True)]).ids
        for obj in self:
            if obj.product_id:
                ecom_category_ids = obj.product_id.public_categ_ids.ids
                ecom_category_ids = list(set(ecom_category_ids + category_ids))
                obj.product_id.public_categ_ids = [[6, 0, ecom_category_ids]]
            elif obj.product_tmpl_id:
                ecom_category_ids = obj.product_tmpl_id.public_categ_ids.ids
                ecom_category_ids = list(set(ecom_category_ids + category_ids))
                obj.product_tmpl_id.public_categ_ids = [[6, 0, ecom_category_ids]]
            elif obj.categ_id:
                product_ids = self.env['product.product'].search([('categ_id', '=', obj.categ_id.id)])
                for product_id in product_ids:
                    ecom_category_ids = product_id.public_categ_ids.ids
                    ecom_category_ids = list(set(ecom_category_ids + category_ids))
                    product_id.public_categ_ids = [[6, 0, ecom_category_ids]]
            elif obj.applied_on == '3_global':
                product_ids = self.env['product.product'].search([])
                for product_id in product_ids:
                    ecom_category_ids = product_id.public_categ_ids.ids
                    ecom_category_ids = list(set(ecom_category_ids + category_ids))
                    product_id.public_categ_ids = [[6, 0, ecom_category_ids]]
    
    @api.model
    def delete_auto_product_category(self):
        category_ids = self.env['product.public.category'].search([('auto_assign', '=', True)]).ids
        for obj in self:
            if obj.product_id:
                ecom_category_ids = obj.product_id.public_categ_ids.ids
                ecom_category_ids = [categ_id for categ_id in ecom_category_ids if categ_id not in category_ids]
                obj.product_id.sudo().public_categ_ids = [[6, 0, ecom_category_ids]]
            elif obj.product_tmpl_id:
                ecom_category_ids = obj.product_tmpl_id.public_categ_ids.ids
                ecom_category_ids = [categ_id for categ_id in ecom_category_ids if categ_id not in category_ids]
                obj.product_tmpl_id.sudo().public_categ_ids = [[6, 0, ecom_category_ids]]
            elif obj.categ_id:
                product_ids = self.env['product.product'].search([('categ_id', '=', obj.categ_id.id)])
                for product_id in product_ids:
                    ecom_category_ids = product_id.public_categ_ids.ids
                    ecom_category_ids = [categ_id for categ_id in ecom_category_ids if categ_id not in category_ids]
                    product_id.sudo().public_categ_ids = [[6, 0, ecom_category_ids]]
            elif obj.applied_on == '3_global':
                product_ids = self.env['product.product'].search([])
                for product_id in product_ids:
                    ecom_category_ids = product_id.public_categ_ids.ids
                    ecom_category_ids = [categ_id for categ_id in ecom_category_ids if categ_id not in category_ids]
                    product_id.sudo().public_categ_ids = [[6, 0, ecom_category_ids]]
    
    @api.model
    def get_update_category(self, pricelist_id):
        pricelist = False
        if pricelist_id:
            pricelist = self.env['product.pricelist'].browse(pricelist_id)
        for obj in self:
            if not pricelist_id and obj.product_id.pricelist_id:
                pricelist = obj.product_id.pricelist_id
            elif not pricelist_id and obj.product_tmpl_id.pricelist_id:
                pricelist = obj.product_tmpl_id.pricelist_id
            if pricelist:
                if pricelist.auto_assign:
                    obj.add_auto_product_category()
                else:
                    obj.delete_auto_product_category()
    
    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            res = super(ProductPricelistItem, self).create(values)
            if 'pricelist_id' in values and values['pricelist_id']:
                res.get_update_category(values['pricelist_id'])
        return res
    
    def write(self, values):
        res = super(ProductPricelistItem, self).write(values)
        if 'pricelist_id' in values:
            for obj in self:
                obj.get_update_category(values['pricelist_id'])
        elif 'product_id' in self:
            for obj in self:
                obj.get_update_category(obj.pricelist_id.id)
        elif 'product_tmpl_id' in values:
            for obj in self:
                obj.get_update_category(obj.pricelist_id.id)
        return res

    def unlink(self):
        self.delete_auto_product_category()
        res = super(ProductPricelistItem, self).unlink()
        return res    
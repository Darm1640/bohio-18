/** @odoo-module */

import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";
import "@website_sale/js/website_sale";
import wSaleUtils from "@website_sale/js/website_sale_utils";
import { Component } from "@odoo/owl";
var timeout;
publicWidget.registry.WebsiteSale.include({
    onChangeVariant: function (ev) {
        this._super.apply(this, arguments);
        var $parent = $(ev.target).closest('.js_product');
        var qty = $parent.find('input[name="add_qty"]').val();
        var combination = this.getSelectedVariantValues($parent);
        var parentCombination = $parent.find('ul[data-attribute_exclusions]').data('attribute_exclusions').parent_combination;
        var productTemplateId = parseInt($parent.find('.product_template_id').val());
        return rpc('/product_code/get_combination_info', {
            'product_template_id': productTemplateId,
            'product_id': this._getProductId($parent),
            'combination': combination,
            'add_qty': parseInt(qty),
            'pricelist_id': this.pricelistId || false,
            'parent_combination': parentCombination,
        }).then(function (data) {
            if (data){
                $('.product_internal_reference').html(data)
                $('.product_internal_reference').removeClass('d-none');
            } else {
                $('.product_internal_reference').addClass('d-none');
            }
            // $('.product_ref_code').html(data)
        });
    }
})

// ajax cart modal js start

publicWidget.registry.WebsiteSale.include({
    _onClickSubmit: function (ev) {
        
        var self = this
        var type_add = "add"
      
        if ($(ev.currentTarget).is('#add_to_cart, #products_grid .a-submit:not(.ajax-cart-btn)')) {
            // self._add_to_cart_button_toast()
            return;
        }
       
        var $aSubmit = $(ev.currentTarget);
   
        if  (!ev.defaultPrevented && !$aSubmit.is(".disabled")) {
            ev.preventDefault();
            if ($aSubmit.parents('.ajax_cart_modal_tools').length) {
                var frm = $aSubmit.closest('form');
                var product_product = frm.find('input[name="product_id"]').val();
                var quantity = frm.find('.quantity').val();
                if(!quantity) {
                    quantity = 1;
                }

                var biz_closest_form = $(ev.target).closest('form')
                var biz_product_id = biz_closest_form.find('input[name="product_id"]').val();
                var biz_rootProduct = {
                    product_id: parseInt(biz_product_id),
                    // quantity: parseInt(biz_closest_form.find('input[name="add_qty"]').val() || 1),
                    add_qty: parseInt(biz_closest_form.find('input[name="add_qty"]').val() || 1),
                    product_custom_attribute_values: this.getCustomVariantValues($(ev.target).find('.js_product')),
                    variant_values: this.getSelectedVariantValues($(ev.target).find('.js_product')),
                    no_variant_attribute_values: this.getNoVariantAttributeValues($(ev.target).find('.js_product'))
                };
                this.addToCart(biz_rootProduct);

                setTimeout(function () {
                    $(".select-modal-backdrop").remove();
                    $(".select-modal").remove();
                    $(".quick-modal-backdrop").remove();
                    $(".quick-modal").remove();
                }, 1000);
            } else {
                $aSubmit.closest('form').submit();
                // self._add_to_cart_button_toast(type_add)
            }
        }
     
        if ($aSubmit.hasClass('a-submit-disable')){
            $aSubmit.addClass("disabled");
        
        }
  
        if ($aSubmit.hasClass('a-submit-loading')){
            var loading = '<span class="fa fa-cog fa-spin"/>';
            var fa_span = $aSubmit.find('span[class*="fa"]');
            if (fa_span.length){
                fa_span.replaceWith(loading);
            } else {
                $aSubmit.append(loading);
            }
        }
    },
    /**
     * @override
     */
    _changeCartQuantity: function ($input, value, $dom_optional, line_id, productIDs) {
        this._super.apply(this, arguments);
        var self = this;
        rpc("/update/cartsidebar", {
        }).then(function (data) {
            $("#wrapwrap #cart_sidebar .cart-content").first().before(data).end().remove();
        });
    },
});

// publicWidget.registry.accesorycart.include({
publicWidget.registry.accesorycart = publicWidget.Widget.extend({
    selector: '.alternative_and_accessory_products',
    events:{
        "click .js_add_accesory_products":"_acccart"
    },
    _acccart: function (ev) {
        $(ev.currentTarget).prev('input').val(1).trigger('change');
    },
});

// ajax cart modal js ends
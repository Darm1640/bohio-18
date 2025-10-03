/** @odoo-module */

// -*- coding: utf-8 -*-
// Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
// See LICENSE file for full copyright and licensing details.

import VariantMixin from "@website_sale/js/sale_variant_mixin";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.WebsiteSale.include({
    /**
     * @override
     */
    _onChangeCombination: function (ev, $parent, combination) {
        this._super.apply(this, arguments);
        var self = this;
        var $counter_hour = $parent.find(".counter_hour");
        $counter_hour.text(parseInt(self._priceToStr(combination.hours)));

        var $counter_day = $parent.find(".counter_day");
        $counter_day.text(parseInt(self._priceToStr(combination.days)));

        var $counter_min = $parent.find(".counter_min");
        $counter_min.text(parseInt(self._priceToStr(combination.minutes)));

        var $counter_sec = $parent.find(".counter_sec");
        $counter_sec.text(parseInt(self._priceToStr(combination.seconds)));

        var $counter_end_date = $parent.find(".end_date");
        $counter_end_date.text(combination.end_date);

        if (combination.has_discounted_price) {
            $('.counter_data').removeClass('d-none');
        } else {
            $('.counter_data').addClass('d-none');
        }
        // if (combination.type === 'consu' && combination.is_strorable) {
        //     if()
        //     $('#product_detail .stock_available_badge').remove();
        //     $('<div class="stock_available_badge bg-danger"></div>').appendTo("#product_detail .productpage_stock_availability_badge");
        // } else {
        //     $('#product_detail .stock_available_badge').remove();
        //     $('<div class="stock_available_badge bg-success"></div>').appendTo("#product_detail .productpage_stock_availability_badge");
        // }
        if (combination.free_qty < 1) {
            $('#product_detail .stock_available_badge').remove();
            $('<div class="stock_available_badge bg-danger"></div>').appendTo("#product_detail .productpage_stock_availability_badge");
        } else {
            $('#product_detail .stock_available_badge').remove();
            $('<div class="stock_available_badge bg-success"></div>').appendTo("#product_detail .productpage_stock_availability_badge");
        }
       
        if (combination.type === 'consu' && !combination.allow_out_of_stock_order ) {
            if (combination.free_qty < 1) {
                $('#product_detail .cart_product_sticky_details').addClass('d-none');
            } else {
                $('#product_detail .cart_product_sticky_details').removeClass('d-none');
            }
        }
        $parent
            .find('.counter_day')
            .first()
            .val(combination.days || 0)
            .trigger('change');

        $parent
            .find('.counter_hour')
            .first()
            .val(combination.hours || 0)
            .trigger('change');

        $parent
            .find('.counter_min')
            .first()
            .val(combination.minutes || 0)
            .trigger('change');

        $parent
            .find('.counter_sec')
            .first()
            .val(combination.seconds || 0)
            .trigger('change');

        $parent
            .find('.end_date')
            .first()
            .val(parseInt(combination.end_date) || 0)
            .trigger('change');

        this.handleCustomValues($(ev.target));

        var product_page_sticky_cart = $('.cart_product_sticky_section')
        if ($(product_page_sticky_cart).length) {
            var changeprice = $('div#product_details .js_product.js_main_product .product_price').html();
            var cartheight = $('#wrapwrap').height() / 2 - 100;
            var quantity = $('form .js_product:first input[name="add_qty"]').val()
            if ($(this).scrollTop() > cartheight) {
                $('.cart_product_sticky_section').addClass('d-block');
            } else {
                $('.cart_product_sticky_section').removeClass('d-block');
            }
            if ($(".js_product.js_main_product").hasClass("css_not_available")) {
                $('div#wrapwrap .cart_prod_name_price').html('');
                $(".cart_product_sticky_details .sticky_cart_button#add_to_cart, .cart_product_sticky_details .sticky_cart_button#buy_now").addClass('disabled');
            }
            else {
                $('div#wrapwrap .cart_prod_name_price').html(changeprice);
                $(".cart_product_sticky_details .sticky_cart_button#add_to_cart, .cart_product_sticky_details .sticky_cart_button#buy_now").removeClass('disabled');
            }
            $(".cart_product_sticky_details .sticky_cart_button #add_to_cart").click(function () {
                $("div#cart_product_sticky_details .js_product.js_main_product #add_to_cart").trigger("click");
                return false;
            });
            $(".product_details_sticky .sticky_cart_button #buy_now").click(function () {
                $("div#cart_product_sticky_details .js_product.js_main_product #buy_now").trigger("click");
                return false;
            });
            $('.quantity.update_product_page_qv.second_qv').val(quantity)
        }
    },
})
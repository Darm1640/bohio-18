/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import '@website_sale_wishlist/js/website_sale_wishlist';
import '@website_sale_comparison/js/website_sale_comparison';
import wSaleUtils from "@website_sale/js/website_sale_utils";
import { rpc, RPCError } from "@web/core/network/rpc";

publicWidget.registry.ProductWishlist.include({
    
    events: Object.assign({}, publicWidget.registry.ProductWishlist.prototype.events || {}, {
        'click .wishlist_product_select_all': '_select_all',
        'click .wishlist_product_remove_selected': '_remove_selected',
        'click .wishlist_product_add_selected_to_cart': '_add_selected_to_cart',
        'click .wishlist_product_add_all_to_cart': '_add_all_to_cart',
        'click #remove_to_wishlist_button': '_remove_to_wishlist_button',
        'click .form-check-input': '_show_btn_on_check_input',
    }),
    /**
     * @override
     */
    willStart: function () {
        var self = this;
        var def = this._super.apply(this, arguments);
        var wishDef;
        if (this.wishlistProductIDs.length != +$('header .my_wish_quantity').text()) {
            wishDef = $.get('/shop/wishlist', {
                count: 1,
            }).then(function (res) {
                self.wishlistProductIDs = JSON.parse(res);
                sessionStorage.setItem('website_sale_wishlist_product_ids', res);
            });

        }
        return Promise.all([def, wishDef]);
    },
    /**
     * Fixed the wishlist count was not updating when products were added from different configurators.
     *
     * @override
     */
    _addNewProducts: function ($el) {
        var self = this;
        var productID = $el.data('product-product-id');
        if ($el.hasClass('o_add_wishlist_dyn')) {
            productID = parseInt($el.closest('.js_product').find('.product_id:checked').val());;
        }
        var $form = $el.closest('form');
        var templateId = $form.find('.product_template_id').val();
        if (!templateId) {
            templateId = $el.data('product-template-id');
        }
        $el.prop("disabled", true).addClass('disabled');
        var productReady = this.selectOrCreateProduct(
            $el.closest('form'),
            productID,
            templateId,
        );
        productReady.then(function (productId) {
            productId = parseInt(productId, 10);
            if (productId && !self.wishlistProductIDs.includes(productId)) {
                return rpc('/shop/wishlist/add', {
                    product_id: productId,
                }).then(function (res) {
                    var $navButton = $('header .o_wsale_my_wish').first();
                    self.wishlistProductIDs.push(productId);
                    sessionStorage.setItem('website_sale_wishlist_product_ids', JSON.stringify(self.wishlistProductIDs));
                    self._updateWishlistView(res.new_count);
                    wSaleUtils.animateClone($navButton, $el.closest('form'), 25, 40);
                    let currentProductId = $el.data('product-product-id');
                    if ($el.hasClass('o_add_wishlist_dyn')) {
                        currentProductId = parseInt($el.closest('.js_product').find('.product_id:checked').val());
                    }
                    if (productId === currentProductId) {
                        $el.prop("disabled", true).addClass('disabled');
                    }
                    $('button.o_add_wishlist[data-product-product-id="' + productId + '"]').each(function () {
                        $(this).prop("disabled", true).addClass('disabled');
                    });
                }).catch(function (e) {
                    $el.prop("disabled", false).removeClass('disabled');
                    if (!(e instanceof RPCError)) {
                        return Promise.reject(e);
                    }
                });
            }
        }).catch(function (e) {
            $el.prop("disabled", false).removeClass('disabled');
            if (!(e instanceof RPCError)) {
                return Promise.reject(e);
            }
        });
    },
    /**
     * @override
     */
    _updateWishlistView: function (newCount) {
        const $wishButton = $('.o_wsale_my_wish');
        if ($wishButton.hasClass('o_wsale_my_wish_hide_empty')) {
            $wishButton.toggleClass('d-none', !this.wishlistProductIDs.length);
        }
        $wishButton.find('.my_wish_quantity').text(newCount);
    },
    _removeWish: function (e, deferred_redirect) {
        var tr = $(e.currentTarget).parents('tr');
        var wish = tr.data('wish-id');
        var product = tr.data('product-id');
        var self = this;

        rpc('/shop/wishlist/remove/' + wish).then(function () {
            $(tr).hide();
        });

        this.wishlistProductIDs = this.wishlistProductIDs.filter((p) => p !== product);
        sessionStorage.setItem('website_sale_wishlist_product_ids', JSON.stringify(this.wishlistProductIDs));
        if (this.wishlistProductIDs.length === 0) {
            if (deferred_redirect) {
                deferred_redirect.then(function () {
                    self._redirectNoWish();
                });
            }
        }
        this._updateWishlistView(this.wishlistProductIDs.length);
    },

    _show_btn_on_check_input: function(){
        var checkedRadio = this.$('.wishlist-section tbody input[type="checkbox"]:checked');
        if (checkedRadio.length > 0){
            $('.form-check-input').parents('#snazzy_wishlist_page_section').find('.wishlist_product_remove_selected').removeClass('d-none');
            $('.form-check-input').parents('#snazzy_wishlist_page_section').find('.wishlist_product_add_selected_to_cart').removeClass('d-none');
        } else {
            $('.form-check-input').parents('#snazzy_wishlist_page_section').find('.wishlist_product_remove_selected').addClass('d-none');
            $('.form-check-input').parents('#snazzy_wishlist_page_section').find('.wishlist_product_add_selected_to_cart').addClass('d-none');
        }
    },

    _select_all: function () {
        if($('.form-check-input').prop("checked") == true){
            $('tbody .form-check-input').prop('checked', true).attr('checked', 'checked');
        }
        else {
            $('tbody .form-check-input').prop('checked', false).removeAttr('checked');
        }
    },
    /**
     * @override
     */
    _onClickWishAdd: function (ev) {
        var self = this;
        this._addOrMoveWish(ev).then(function () {
            self.$('.wishlist-section .o_wish_add').removeClass('disabled');
        });
    },

    _remove_selected: function (ev) {
        $('.form-check-input:checked').parents('tr').find('.o_wish_rm').addClass('product_remove');
        $(ev.currentTarget).parents('.wishlist-section').find('.product_remove').click();
        $(ev.currentTarget).parents('.wishlist-section').find('.wishlist_page_toast').addClass("show").fadeIn().delay(2000).fadeOut();
        $(ev.currentTarget).parents('.wishlist-section').find('.toast-body').removeClass("add_product");
        $(ev.currentTarget).parents('.wishlist-section').find('.toast-body').addClass("remove_product");
        $(ev.currentTarget).parents('.wishlist-section').find('.wishlist_toast_text_content').text("Product remove from wishlist");
    },

    _add_selected_to_cart: async function (ev) {
        const $section = $(ev.currentTarget).closest('.wishlist-section');
        $('.form-check-input:checked').parents('tr').find('.o_wish_add').addClass('product_add');
        const $selectedButtons = $section.find('.product_add');

        for (let i = 0; i < $selectedButtons.length; i++) {
            await $selectedButtons.eq(i).click();
            await new Promise(resolve => setTimeout(resolve, 300));
        }

        $section.find('.wishlist_page_toast').addClass("show").fadeIn().delay(2000).fadeOut();
        $section.find('.toast-body').removeClass("remove_product").addClass("add_product");
        $section.find('.wishlist_toast_text_content').text("Product(s) added to cart");
    },

    _add_all_to_cart: async function (ev) {
        const $section = $(ev.currentTarget).closest('.wishlist-section');
        const $buttons = $section.find('.o_wish_add:visible');

        for (let i = 0; i < $buttons.length; i++) {
            await $buttons.eq(i).click(); 
            await new Promise(resolve => setTimeout(resolve, 300)); 
        }

        $section.find('.wishlist_page_toast').addClass("show").fadeIn().delay(2000).fadeOut();
        $section.find('.toast-body').removeClass("remove_product").addClass("add_product");
        $section.find('.wishlist_toast_text_content').text("All products added to cart");
    },

    _remove_to_wishlist_button: function (ev) {
        const $row = $(ev.currentTarget).closest('tr');
        const $checkbox = $row.find('input[type="checkbox"]');
        if ($checkbox.prop('checked')) {
            $checkbox.prop('checked', false);
        }
        this._removeWish(ev, false);
        $row.remove();  

        const $section = $(ev.currentTarget).closest('.wishlist-section');
        $section.find('.wishlist_page_toast').addClass("show").fadeIn().delay(2000).fadeOut();
        $section.find('.toast-body').removeClass("add_product");
        $section.find('.toast-body').addClass("remove_product");
        $section.find('.wishlist_toast_text_content').text("Product removed from wishlist");
    },
})    

// Fixed the product compare list 
publicWidget.registry.ProductComparison.include({
    selector: '#wrap',

    _updateComparelistView: function () {
        const count = this.comparelist_product_ids.length;
        $('.o_product_circle').text(count);
        this.$('.o_comparelist_button').removeClass('d-md-block');
        if (Object.keys(this.comparelist_product_ids || {}).length === 0) {
            $('.o_product_feature_panel').removeClass('d-md-block');
        } else {
            $('.o_product_feature_panel').addClass('d-md-block');
            this.$('.o_comparelist_products').addClass('d-md-block');
            if (count >= 2) {
                this.$('.o_comparelist_button').addClass('d-md-block');
                this.$('.o_comparelist_button a').attr('href',
                    '/shop/compare?products=' + encodeURIComponent(this.comparelist_product_ids));
            }
        }
    },
})
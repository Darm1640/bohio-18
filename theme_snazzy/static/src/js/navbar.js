/** @odoo-module */

import publicWidget from "@web/legacy/js/public/public_widget";
import { queryFirst } from '@odoo/hoot-dom';
// import core from "@web/legacy/js/services/core";
// import dom from "@web/legacy/js/core/dom";
// import { deserializeDateTime } from "@web/core/l10n/dates";
import { serializeDateTime } from '@web/core/l10n/dates';
const { DateTime } = luxon;
// import portalComposer from "@portal/js/portal_composer";

// import { markup } from "@odoo/owl";
// import PortalChatter from "@portal/js/portal_chatter";

// import { PortalChatter } from "@portal/chatter/frontend/portal_chatter";
import { App } from "@odoo/owl";
import { getBundle } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { getTemplate } from "@web/core/templates";

// const { DateTime } = luxon;
// var qweb = core.qweb;

import { debounce } from "@web/core/utils/timing";
// var _t = core._t;
publicWidget.registry.SnazzyHeaderSidebarsJS = publicWidget.Widget.extend({
    selector: "#wrapwrap",
    events: {
        'click header .bizople-add-to-cart a.show_cart_sidebar,.header-search-popup .bizople-add-to-cart a.show_cart_sidebar': '_OpenCartSidebar',
        'click #close_cart_sidebar,.cart_sidebar_backdrop': '_CloseCartSidebar',
        'click .shop-collection-cart-main .remove-cart-btn a': '_RightCartDeleteProduct',
        'click #sidebar #top_menu .dropdown-menu.o_mega_menu': '_megamenudropdown',
        'click .s_mega_menu_five_snippet .nav-pills .nav-item .nav-link': '_megamenutabs',
        'click .sticky_cart_button': '_OpenSticktCartSidebar',
    },
    _OpenCartSidebar: function (ev) {
        $("#cart_sidebar").addClass("toggled oe_website_sale");
        this.trigger_up('widgets_start_request', {
            $target: $("#cart_sidebar")
        });
        ev.stopPropagation()
    },

    _CloseCartSidebar: function (e) {
        $("#cart_sidebar").removeClass("toggled oe_website_sale");
        e.stopPropagation()
    },

    _RightCartDeleteProduct: function (ev) {
        ev.preventDefault();
        $(ev.currentTarget).closest('.cart_line').find('.js_quantity').val(0).trigger('change');
    },
    _megamenudropdown: function (e) {
        e.stopPropagation();
    }, 
    _megamenutabs: function (ev) {
        $(ev.currentTarget).parents('.s_tabs_main').find('.tab-pane').removeClass('active show');
        var tabid = $(ev.currentTarget).attr('id')
        $(ev.currentTarget).parents('.s_tabs_main').find('.tab-pane[aria-labelledby="'+tabid+'"]').addClass('show active');
    }, 

    _OpenSticktCartSidebar: function (ev) {
        setTimeout(function () {
            $('.show_cart_sidebar').click();
        }, 1000);
    }
});

publicWidget.registry.SnazzyHeaderJS = publicWidget.Widget.extend({
    selector: "header",
    events: {
        'mouseover .s_mega_menu_five_snippet .nav-pills > li > a': '_MegaMenuTabs',
    },
    start: function () {
        var self = this
        $("body").addClass("blured-bg");
        var size = $(window).width();
        if (size <= 992) {
            $(function () {

                /*show bottom bar start*/
                $('#wrapwrap').scroll(function () {
                    if ($(this).scrollTop() > 100) {
                        $('.bizople-mbl-bottom-bar').addClass('show-bottom-bar');
                        $('#wrapwrap').addClass('pb88');
                    } else {
                        $('.bizople-mbl-bottom-bar').removeClass('show-bottom-bar');
                        $('#wrapwrap').removeClass('pb88');
                    }
                });
                /*show bottom bar end*/

                /*shop page hide shop menu from bottom bar start*/
                if ($('.snazzy_shop').hasClass('snazzy_shop')) {
                    $('.bottom-bar-filter').removeClass('d-none p-0');
                    $('.bottom-bar-shop').addClass('d-none p-0');
                } else {
                    $('.bottom-bar-filter').addClass('d-none p-0');
                    $('.bottom-bar-shop').removeClass('d-none p-0');
                }
                /*shop page hide shop menu from bottom bar end*/
            });
        }

        /* header category menu start*/
        $(function () {
            var categ_target = $(".snazzy-header-category > li.dropdown-submenu > .nav-link > i.ri");
            var parent_categ = $(categ_target).parent().parent();
            if ($(categ_target).hasClass("ri")) {
                $(parent_categ).addClass('dropend');
            }
        });
        /* header category menu end*/

        /*header 2 search js start*/
        if (size <= 1400 && size > 992) {
            $(function () {
                var to_toggle = $(".header-search-btn .search-bar");
                $(".header-search-btn > button").click(function () {
                    if ($(to_toggle).hasClass('toggled')) {
                        $(to_toggle).removeClass("toggled");
                    } else {
                        $(to_toggle).addClass("toggled");
                    }
                });
            });
        }
        /*header 2 search js end*/
        $(".show_cart_sidebar, .show_cart_sidebar_mbl, .show_cart_sidebar_btm_bar").on("click", function (e) {
            rpc("/update/cartsidebar", {
            }).then(function (data) {
                $("#wrapwrap #cart_sidebar .cart-content").first().before(data).end().remove();
            });
        });
        // // Mega Menu
        // $('.mega_menu_five_snippet .nav-pills > li > a').hover(function() {
        //     $(this).tab('show');
        // });
    },
    /**
     * @constructor
     */
    init: function () {
        this._super.apply(this, arguments);

        this._MegaMenuTabs = debounce(this._MegaMenuTabs, 300);
    },
    _MegaMenuTabs: function (ev) {
        $(ev.currentTarget).tab('show');
    },

});
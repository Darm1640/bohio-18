/** @odoo-module */

// -*- coding: utf-8 -*-
// Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
// See LICENSE file for full copyright and licensing details.

import { rpc } from "@web/core/network/rpc";

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.websiteSaleCategoryMobile = publicWidget.Widget.extend({
    selector: '#o_shop_collapse_category_mobile',
    events: {
        'click .fa-chevron-down': '_onOpenClick',
        'click .fa-chevron-up': '_onCloseClick',
    },
    _onOpenClick: function (ev) {
        var $fa = $(ev.currentTarget);
        $fa.parent().siblings().find('.fa-chevron-up:first').click();
        $fa.parents('li').find('ul:first').show('normal');
        $fa.toggleClass('fa-chevron-up fa-chevron-down');
    },
    _onCloseClick: function (ev) {
        var $fa = $(ev.currentTarget);
        $fa.parent().find('ul:first').hide('normal');
        $fa.toggleClass('fa-chevron-up fa-chevron-down');
    },
});

publicWidget.registry.mblheaderjs = publicWidget.Widget.extend({
    selector: ".sidebar-content,.bizople-mbl-bottom-bar,.snazzy_header",
    events: {
        'click #close_mbl_sidebar': '_CloseMblSideBar',
        'click .bottom-show-sidebar': '_ShowBottomSideBar',
        'click #show-sidebar': '_ShowSideBar',
    },
    _CloseMblSideBar: function (e) {
        $(".sidebar-wrapper").parents(".blured-bg").removeClass("active");
        $(".sidebar-wrapper").removeClass("toggled");
        e.stopPropagation()
    },
    _ShowBottomSideBar: function (e) {
        $(".sidebar-wrapper").parents(".blured-bg").addClass("active");
        $(".sidebar-wrapper").addClass("toggled");
        e.stopPropagation()
    },
    _ShowSideBar: function (e) {
        $(".sidebar-wrapper").parents(".blured-bg").addClass("active");
        $(".sidebar-wrapper").addClass("toggled");
        e.stopPropagation()
    },
})
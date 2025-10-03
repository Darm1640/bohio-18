/** @odoo-module */

// -*- coding: utf-8 -*-
// Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
// See LICENSE file for full copyright and licensing details.

import { rpc } from "@web/core/network/rpc";

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.infinite_load = publicWidget.Widget.extend({
    selector: ".infinite_loader_div",
    events: {
        'click .infinite_load_button': 'startLoadMoreNextClick',
        'click .infinite_load_button_top': 'startLoadMorePrevClick',
    },
    start: function () {
        var self = this;
        self.startLoadMore();
        var total_product_count = $(".infinite_load_next_page").attr('all-products');
    },
    startLoadMore: function () {
        var next_call = true;
        var prev_call = true;
        var self = this;
        $('#wrapwrap').scroll(function () {
            var scrollTop = $('#wrapwrap').scrollTop();
            var page_url = $(".infinite_load_next_page").attr('next-page-url');
            var prev_page_url = $(".infinite_load_next_page").attr('prev-page-url');
            var first_page_url = $(".infinite_load_next_page").attr('first-page-url');
            var last_page_url = $(".infinite_load_next_page").attr('last-page-url');
            var current_url = $(".infinite_load_next_page").attr('current-page-url');
            var next_page_num = $(".infinite_load_next_page").attr('next-page-num');
            var prev_page_num = $(".infinite_load_next_page").attr('prev-page-num');
            var total_page = $(".infinite_load_next_page").attr('total-page');
            if ($(".snazzy_shop").hasClass("snazzy_shop")) {
                var trigger_element = document.querySelector('.snazzy_bottom_pager');
                var position = trigger_element.getBoundingClientRect();
            } else {
                var position = -1;
            }


            if (position.top >= 0 && position.bottom <= window.innerHeight) {
                if (next_call && current_url != last_page_url) {
                    next_call = false;
                    $.ajax({
                        url: page_url,
                        type: 'GET',
                        beforeSend: function () {
                            $(".infinite_loader_div_next").removeClass("d-none");
                        },
                        success: function (data) {
                            $(".infinite_loader_div_next").addClass("d-none");
                            var data_replace = null;

                            var new_page_url = $(data).find('.infinite_load_next_page').attr('next-page-url');
                            $(".infinite_load_next_page").attr('next-page-url', new_page_url);

                            var next_page_num = $(data).find('.infinite_load_next_page').attr('next-page-num');
                            $(".infinite_load_next_page").attr('next-page-num', next_page_num);

                            data_replace = $(data).find("#products_grid .o_wsale_products_grid_table_wrapper .oe_product");
                            if (data_replace) {
                                $("#products_grid #o_wsale_products_grid").append(data_replace);
                            }
                            if (last_page_url != page_url) {
                                $("ul.pagination li:last").removeClass("disabled");
                                next_call = true;
                            } else {
                                $("ul.pagination li:last").addClass("disabled");
                            }
                            $("ul.pagination li:first-child").removeClass("disabled");
                            var update_pre_page = $(data).find('.infinite_load_next_page').attr('prev-page-url');
                            $("ul.pagination li:first-child a").attr("href", update_pre_page);
                            $("ul.pagination li:last a").attr("href", new_page_url);

                            var active_page = $(data).find(".infinite_load_next_page").attr('page-number');
                            $("ul.pagination li").removeClass("active");
                            $("ul.pagination li:contains(" + active_page + ")").addClass("active");

                            var current_page_num = $(data).find(".infinite_load_next_page").attr('current-page-number');
                            $(".infinite_load_next_page").attr('current-page-number', current_page_num);

                            var current_page = $(data).find(".infinite_load_next_page").attr('current-page-url');
                            window.history.replaceState(null, null, current_page);

                            if (current_page_num >= total_page) {
                                $('.infinite_load_button').removeClass('active');
                            }
                            $('.lazyload').lazyload();
                        }
                    });
                }
            }
            if ($("#products_grid #o_wsale_products_grid div:first").length && scrollTop <= 0) {
                if (prev_call && current_url != first_page_url) {
                    prev_call = false;
                    $.ajax({
                        url: prev_page_url,
                        type: 'GET',
                        beforeSend: function () {
                            $(".infinite_loader_div").removeClass("d-none");
                        },
                        success: function (data) {
                            $(window).scrollTop(100);
                            $(".infinite_loader_div").addClass("d-none");
                            var data_replace = null;

                            var new_prev_page_url = $(data).find('.infinite_load_next_page').attr('prev-page-url');
                            $(".infinite_load_next_page").attr('prev-page-url', new_prev_page_url);

                            var new_prev_page_num = $(data).find('.infinite_load_next_page').attr('prev-page-num');
                            $(".infinite_load_next_page").attr('prev-page-num', new_prev_page_num);

                            data_replace = $(data).find("#products_grid .o_wsale_products_grid_table_wrapper .oe_product");
                            if (data_replace) {
                                $("#products_grid #o_wsale_products_grid").prepend(data_replace);
                            }

                            var active_page = $(data).find(".infinite_load_next_page").attr('page-number');
                            var current_page_num = $(data).find(".infinite_load_next_page").attr('current-page-number');
                            $(".infinite_load_next_page").attr('current-page-number', current_page_num);
                            $("ul.pagination li").removeClass("active");
                            $("ul.pagination li:contains(" + active_page + ")").addClass("active");

                            var current_page = $(data).find(".infinite_load_next_page").attr('current-page-url');
                            window.history.replaceState(null, null, current_page);
                            if (first_page_url != prev_page_url) {
                                $("ul.pagination li:first-child").removeClass("disabled");
                                prev_call = true;
                            } else {
                                $("ul.pagination li:first-child").addClass("disabled");
                            }
                            $("ul.pagination li:last-child").removeClass("disabled");
                            var update_next_page = $(data).find('.infinite_load_next_page').attr('next-page-url');
                            $("ul.pagination li:first-child a").attr("href", update_next_page);

                            $("ul.pagination li:last-child a").attr("href", new_prev_page_url);

                            if (current_page_num < 2) {
                                $('.infinite_load_button_top').removeClass('active');
                            }
                            $('.lazyload').lazyload();
                        }
                    });
                }
            }
        });
    },

});
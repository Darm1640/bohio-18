/** @odoo-module */

// -*- coding: utf-8 -*-
// Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
// See LICENSE file for full copyright and licensing details.

import { rpc } from "@web/core/network/rpc";

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.SnazzyModalPopups = publicWidget.Widget.extend({
    selector: "#wrapwrap",
    events: {
        "click .lpopen": "_openSignuppopup",
        "click .lpresetpass": "_resetPassword",
        "click .lploginbtn": "_oauth",
        "click .lpalreadyuser": "_backToLogin",
        "click .lpsignupbtn": "_userSignup",
        "click .lpcreatebtn": "_createAcc",
        "click a.quick_btn,button.quick_btn": "_prodqvopen",
        "click a.select_btn": "_prodsvopen",
        "click a.similar_btn": "_prodspopen",
        'click .header-search .open-popup': '_OpenSearchPopup',
        'click .close-search': '_CloseSearchPopup',
        'click .header-search-popup .search-popup-backdrop': '_SearchBackdrop',
        'click header .header-search .search-query-bizople': '_SearchModalFocus',
    },

    _prodqvopen: function (ev) {
        var self = this;
        var pid = $(ev.currentTarget).attr('data-product_template_id');
        window.quick_btn = $(ev.currentTarget);
        var domain_url = encodeURIComponent(window.location.origin);
        setTimeout(function(){ 
            $(".quick_modal_product_details").css("z-index", "0"); 
        }, 1500);

        rpc('/get_prod_quick_view_details', { 'prod_id': pid, 'href': domain_url }).then(function (data) {
            $(".quick_modal_wrap").append(data);
            self.trigger_up('widgets_start_request', {
                $target: $(".quick_modal_wrap")
            });
            $(".quick-modal-backdrop").fadeIn();
            $(".quick_modal_wrap").css("display", "block");
            $(".quick-popout #product_details").css("transform", "translateX(0)");
            $("[data-attribute_exclusions]").trigger('change');
            $("[data-attribute_exclusions]").on('change', function (event) {
                setTimeout(function () {
                    $('.lazyload').lazyload();
                }, 1000);
            });

            $(".quick_close").click(function () {
                setTimeout(function () {
                    $('.quick_modal_wrap').empty(data); 
                }, 500);
                $(".quick-popout #product_details").css("transform", "translateX(-100%)","z-index", "-1");
            });
            setTimeout(function () {
                $('.lazyload').lazyload();
            }, 1000);
        });
    },
    _prodsvopen: function (ev) {
        var self = this;
        var shoppageqtydiv = $(ev.currentTarget).parents('form').find('.shop_page_quantity')
        if ($(shoppageqtydiv).length) {
            var shoppageqty = $(shoppageqtydiv).find('input.quantity').val()
        }
        var pid = $(ev.currentTarget).attr('data-product_template_id');
        window.select_btn = $(ev.currentTarget);
        rpc('/get_prod_select_option_details', {'prod_id':pid}).then(function(data) 
        {
            $(".quick_modal_wrap").append(data);
            self.trigger_up('widgets_start_request', {
                $target: $(".quick_modal_wrap")
            });
            if (parseInt(shoppageqty) > 1) {
                $(".quick_modal_wrap").find('.css_quantity input.quantity').val(parseInt(shoppageqty)).change()
            }
            $(".select-modal-backdrop").fadeIn();
            $(".quick_modal_wrap").css("display", "block");
            $("[data-attribute_exclusions]").trigger('change');
            $("[data-attribute_exclusions]").on('change', function(event) {
                setTimeout(function(){
                    $('.lazyload').lazyload();
                }, 1000);
            });
            $(".css_attribute_color input").click(function(event){   
                setTimeout(function(){
                    $('.lazyload').lazyload();
                }, 1000);
            });

            $(".select_close").click(function() {
                $('.quick_modal_wrap').empty(data);
            });
            $(".select-modal #add_to_cart").click(function() {
                setTimeout(function () {
                    $(".select_close").click()
                }, 1000);
            });
            setTimeout(function () {
                $('.lazyload').lazyload();
            }, 1000);
        });
    },
    _prodspopen: function (ev) {
        var pid = $(ev.currentTarget).attr('data-product_template_id');
        window.similar_btn = $(ev.currentTarget);
        var domain_url = encodeURIComponent(window.location.origin);

        rpc('/get_prod_similar_view_details', { 'prod_id': pid, 'href': domain_url }).then(function (data) {
            $(".quick_modal_wrap").append(data);
            $(".similar-modal-backdrop").fadeIn();
            $(".quick_modal_wrap").css("display", "block");
            $("[data-attribute_exclusions]").trigger('change');
            $("[data-attribute_exclusions]").on('change', function (event) {
                setTimeout(function () {
                    $('.lazyload').lazyload();
                }, 1000);
            });

            $(".similar_close").click(function () {
                $('.quick_modal_wrap').empty(data);
            });

            $(".quick_modal_wrap").find('#snazzy_similar_popup').owlCarousel({

                autoPlay: 3000, //Set AutoPlay to 3 seconds
                responsiveClass: true,
                items : 4,
                loop: true,
                dots:true,
                margin: 30,
                nav:true,
                navText: [
                    '<i class="fa fa-long-arrow-left"></i>',
                    '<i class="fa fa-long-arrow-right"></i>'
                ],
                responsive: {
                    0: {
                        items: 1,
                    },
                    420: {
                        items: 1,
                    },
                    768: {
                        items: 2,
                    },
                    1024: {
                        items: 2,
                    },
                    1200: {
                        items: 3,
                    },
                    1400: {
                        items: 3,
                    },
                },
            });
            $('.lazyload').lazyload();
        });
    },

    _resetPassword: function (ev) {
        $("#nav-reset-tab").click();
        if ($("#resetlogin").val().trim() != "") {
            ev.preventDefault();
            return rpc('/ajax/web/reset_password',
                {
                    "login": $("#resetlogin").val(),
                }
            ).then(function (result) {
                if ("error" in result) {
                    $("#error").css("display", "block").empty().append(result["error"]);
                }
                else if ("message" in result) {
                    $("#reset_form").css("display", "none");
                    $("#msgbox").css("display", "block");
                    $("#messager").empty().append(result["message"]);
                }
            });
        }
    },
    _createAcc: function () {
        $("#nav-register-tab").click();
    },
    _userSignup: function (ev) {
        if ($("#logins").val().trim() != "" && $("#passwords").val().trim() != ""
            && $("#confirm_passwords").val().trim() != "" && $("#names").val().trim() != "") {
            ev.preventDefault();
            return rpc('/ajax/signup/',
                {
                    "login": $("#logins").val(),
                    "name": $("#names").val(),
                    "password": $("#passwords").val(),
                    "confirm_password": $("#confirm_passwords").val(),
                    "token": $("#token").val()
                }
            )
            .then(function (result) {
                if ("error" in result) {
                    $("#errors").css("display", "block").empty().append(result["error"])
                }
                else if (result["signup_success"] == true) {
                    window.location.reload();
                }
            });
        }
    },
    _backToLogin: function () {
        $("#nav-login-tab").click();
    },
    _openSignuppopup: function (evt) {
        var theme_name = $(evt.currentTarget).attr('data-theme_name');
        return rpc('/ajax/login/',
                {
                    'theme_name': theme_name
                }
            ).then(function (result) {
            $("#nav-login").empty().append(result["loginview"]);
            $("#nav-login-tab").click();
            // $(".blured-bg").addClass("active");
            if ("signupview" in result) {
                $("#nav-register").empty().append(result["signupview"]);
            }
            if ("resetview" in result) {
                $("#nav-reset").empty().append(result["resetview"]);
            }

        });
    },
    _oauth: function (ev) {
        if ($("#login").val().trim() != "" && $("#password").val().trim() != "") {
            ev.preventDefault();
            return rpc('/ajax/web/login/',
                {
                    "login": $("#login").val(),
                    "password": $("#password").val()
                }
            )
            .then(function (result) {
                if (result["login_success"] == true) {
                    window.location.reload();
                }
                else if ("error" in result) {
                    $("#errormsg").css("display", "block").empty().append(result["error"]);
                }
            });
        }
    },

    _OpenSearchPopup: function () {
        $(".search-box").addClass("open");
        $(".search-popup-backdrop").addClass("active");
    },
    _CloseSearchPopup: function () {
        $(".search-box").removeClass("open");
        $(".search-popup-backdrop").removeClass("active");
    },

    _SearchBackdrop: function (ev) {
        $(ev.currentTarget).parents(".header-search-popup").find(".search-box").removeClass('open');
        setTimeout(function () {
            $(ev.currentTarget).parents(".header-search-popup").find(".search-popup-backdrop").removeClass('active');
        }, 500);
    },

    _SearchModalFocus: function () { 
        setTimeout(() => $('.search-query-bizople.oe_search_box').focus(), 100);
    },

});
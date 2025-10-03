/** @odoo-module **/

// -*- coding: utf-8 -*-
// Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
// See LICENSE file for full copyright and licensing details.

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PricelistCount = publicWidget.Widget.extend({
    selector: '.counter_data',
    /**
     * @constructor
     */
    init: function () {    
        this._super.apply(this, arguments);
        var self = this
        this.dealCounter = setInterval(function() {
            var counter_time = self.$target.find('.counter_time')[0].innerText
            var time = self.$target.find('.time')[0].innerText
            if (parseInt(counter_time) >= parseInt(time)){
                var end_date = self.$target.find('.end_date')[0].innerText
                var now = new Date().getTime();
                var lastdate = new Date(end_date).getTime()
                var distance = lastdate - now
                
                var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                var seconds = Math.floor((distance % (1000 * 60)) / 1000);
                var days = Math.floor((distance / (1000 * 3600 * 24)))
            
                self.$target.find(".counter_day").text(days);
                self.$target.find(".counter_hour").text(hours);
                self.$target.find(".counter_min").text(minutes);
                self.$target.find(".counter_sec").text(seconds);
            }
            if (distance <= 0) {
                clearInterval(self.dealCounter);
                distance -= 1
            }
        }, 1000);
    }
})
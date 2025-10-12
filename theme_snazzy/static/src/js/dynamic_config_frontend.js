/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";


publicWidget.registry.DynamicConfigFrontend = publicWidget.Widget.extend({
    selector: ".bizople_dynamic_config_tool",
    start: function() {
        var self = this;
        if (this.editableMode) {
        }
        if (!this.editableMode) {
            self.showLoading();
            var model = self.$target.data('model')
            var mode = self.$target.data('designmode')
            var style = self.$target.data('designstyle')
            var idlist = self.$target.data('recordids')
            var item_per_row = self.$target.data('itemperrow')
            var design_params = self.$target.data('designactionbutton')
            var domain_list = self.$target.data('domain_list')
            var record_match = self.$target.data('record_match')
            var sortby = self.$target.data('sortby')
            var orderby = self.$target.data('orderby')
            var record_limit = self.$target.data('record_limit')
            
            if (item_per_row > 2) {
                var new_item_per_row = 3
            }
            else{
                var new_item_per_row = 1
            }
            
            rpc('/get/dynamic/config', {
                'idlist': idlist,
                'model': model,
                'style': style,
                'mode': mode,
                'design_params': design_params,
                'item_per_row': item_per_row,
                'domain_list': domain_list,
                'record_match': record_match,
                'record_limit': parseInt(record_limit),
                'sortby': sortby,
                'orderby': orderby,
            }).then(function(data) {
                self.$target.find('[class*=container]').empty()
                self.$target.find('[class*=container]').append(data['dynamic_config_template'])
                self.$target.find('.lazyload').lazyload();
                if (mode == 'slider') {
                    self.$target.find('div#configurator-slider').owlCarousel({
                        margin: 30,
                        responsiveClass: true,
                        items: parseInt(item_per_row),
                        loop: false,
                        dots:false,
                        rows: true,
                        rowsCount: 2,
                        rewind:true,
                        nav:true,
                        navText: [
                            '<i class="fa fa-angle-left"></i>',
                            '<i class="fa fa-angle-right"></i>'
                        ],
                        autoplay: true,
                        autoplayTimeout: 5000,
                        autoplayHoverPause:true,
                        responsive: {
                            0: {
                                items: 1,
                            },
                            420: {
                                items: 1,
                            },
                            768: {
                                // items: 3,
                                items: new_item_per_row,
                            },
                            1000: {
                                items: parseInt(item_per_row),
                            },
                            1500: {
                                items: parseInt(item_per_row),
                            },
                        },
                    });
                    
                }
                self._counterTime()
                self.stopLoading();
            })
        }
    },

    _counterTime: function(ev) {
        var self = this
        var counter_data = this.$target.find('.counter_data')
        $(counter_data).each(function(){
            var self_counter = $(this)
            this.dealCounter = setInterval(function() {
                var counter_time = self_counter.find('.counter_time')[0].innerText
                var time = self_counter.find('.time')[0].innerText
                if (parseInt(counter_time) >= parseInt(time)){
                    var end_date = self_counter.find('.end_date')[0].innerText
                    var now = new Date().getTime();
                    var lastdate = new Date(end_date).getTime()
                    var distance = lastdate - now
                    
                    var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                    var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                    var seconds = Math.floor((distance % (1000 * 60)) / 1000);
                    var days = Math.floor((distance / (1000 * 3600 * 24)))
                
                    self_counter.find(".counter_day").text(days);
                    self_counter.find(".counter_hour").text(hours);
                    self_counter.find(".counter_min").text(minutes);
                    self_counter.find(".counter_sec").text(seconds);
                }
                if (distance <= 0) {
                    clearInterval(self_counter.dealCounter);
                    distance -= 1
                }
            }, 1000);
        })
        
    },

    showLoading: function(){
        this.$target.addClass("loading-dynamic-content");
        this.$target.append('<div class="lds-ellipsis"><div></div><div></div><div></div><div></div></div>');
        if (this.$target.data('designmode') != 'slider'){
            this.$target.find('[class*=container]').addClass('d-none')
        }
    },
    stopLoading: function(){
        this.$target.removeClass("loading-dynamic-content");
        this.$target.find('.lds-ellipsis').remove();
        if (this.$target.data('designmode') != 'slider'){
            this.$target.find('[class*=container]').removeClass('d-none')
        }
    },
});
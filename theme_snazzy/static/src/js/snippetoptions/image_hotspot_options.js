/** @odoo-module **/
import { renderToElement } from "@web/core/utils/render";
import options from "@web_editor/js/editor/snippets.options";
import { rpc } from "@web/core/network/rpc";

options.registry.add_hotshpot = options.Class.extend({
    events:{
        'click we-button.biz_add_hotspot':'_addHotspot',
    },

    _addHotspot: function () {
        var spot = '<div class="image_hotspot" data-prod-select-id="" style="margin-bottom:0; position: absolute; z-index: 1; top:50%;left: 50%;transform: translate(-50%, -50%);"><button class="btn hotspot_info p-0 shadow-none" type="button" data-container="body" data-bs-toggle="popover"  data-bs-placement="bottom" data-bs-content="product_info" data-bs-html="true"><i class="fa fa-circle text-primary"></i></button></div>';
        this.$target.after(spot);
        this.$target.parent().addClass('position-relative');
    }
});

options.registry.hotspot_posi = options.Class.extend({
    events:{
        'change we-range.horizontal_posi':'_horizontalposi',
        'change we-range.vertical_posi':'_verticalposi',
        'click we-select.hotspot_info_type':'_hotspotinfotype',
        'click we-button.show_preview':'_showstaticpreview',
        'click we-button.select_hotspot_product':'_selectproductoption',
    },

    _horizontalposi: function () {
        var horizontal_posi = this.$target.attr('data-horizontal_posi');
        var horizontal_posi = horizontal_posi+'%';
        this.$target.css('left', horizontal_posi);
    },

    _verticalposi: function () {
        var vertical_posi = this.$target.attr('data-vertical_posi');
        var vertical_posi = vertical_posi+'%';
        this.$target.css('top', vertical_posi);
    },

    _hotspotinfotype: function () {
        if (this.$target.hasClass("hotspot_static")) {
            var static_info = $(renderToElement("theme_snazzy.static_image_hotspot_info"));
            this.$target.find('.static_image_hotspot_info').remove();
            static_info.appendTo(this.$target);
            var initial_static_data = this.$target.find(".static_image_hotspot_info").html();
            this.$target.find('.static_image_hotspot_info').attr('data-bs-content', '<div class="static_image_hotspot_info">'+initial_static_data+'</div>');
        }
    },

    _showstaticpreview: function () {
        if (this.$target.find(".static_image_hotspot_info").hasClass('show_edit')) {
            this.$target.find(".static_image_hotspot_info").removeClass('show_edit')
            var hotspot_btn = this.$target.find('.static_image_hotspot_info .hotspot-link > a');
            var hotspot_btn_style = this.$target.find('.static_image_hotspot_info .hotspot-link > a').attr('style');
            if($(hotspot_btn).find('font').length > 0){
                var font_text = $(hotspot_btn).find('font').text();
                var font_style = $(hotspot_btn).find('font').attr('style');
                $(hotspot_btn).text(font_text);
                if (hotspot_btn_style == undefined){
                    $(hotspot_btn).attr('style',font_style);
                } else{
                    $(hotspot_btn).attr('style',hotspot_btn_style + font_style);
                }
            }
            var static_data = this.$target.find(".static_image_hotspot_info").html();
            var static_data_bgcolor = this.$target.find(".static_image_hotspot_info").css('background-color');
            this.$target.find('.hotspot_info').attr('data-bs-content', '<div class="static_image_hotspot_info" style="background-color: '+static_data_bgcolor+'">'+static_data+'</div>');
        } else {
            this.$target.find(".static_image_hotspot_info").addClass('show_edit')
        }
    },

        _selectproductoption: function () {
        var self = this.$target;
        self.$modal = $(renderToElement("theme_snazzy.dynamic_image_hotspot_product_select"));
        self.$modal.appendTo('body');
        self.$modal.modal('show');
        var $dynamic_hotspot_product = self.$modal.find("#dynamic_hotspot_product"),
            $product_slider_cancel = self.$modal.find("#cancel"),
            $pro_sub_data = self.$modal.find("#prod_sub_data");

            rpc('/theme_snazzy/hotspot_product_select', {}).then(function(res) {
            $('#dynamic_hotspot_product option[value!="0"]').remove();
            res.forEach((y) => {
                $("select[id='dynamic_hotspot_product']").append($('<option>', {
                    value: y["id"],
                    text: y["name"]
                }));
            });
        });

        $pro_sub_data.on('click', function() {
            var target = this.$target;
            self.attr('data-prod-select-id', $dynamic_hotspot_product.val());
            var product_id = self.attr('data-prod-select-id');
            self.find('.static_image_hotspot_info').remove();
            self.find('.hotspot_info').removeAttr('data-bs-toggle');
            self.find('.hotspot_info').removeAttr('data-container');
            self.find('.hotspot_info').removeAttr('data-bs-placement');
            self.find('.hotspot_info').removeAttr('data-bs-content');
            self.find('.hotspot_info').removeAttr('data-bs-html');
            self.find('.hotspot_info').attr('data-product_template_id', product_id)
        });
        $product_slider_cancel.on('click', function() {
            self.getParent()._onRemoveClick($.Event("click"))
        });
    },

});    

/** @odoo-module **/
import { renderToElement } from "@web/core/utils/render";
import options from "@web_editor/js/editor/snippets.options";
import { rpc } from "@web/core/network/rpc";

// [T2515] Fix - theme options selection
options.registry.add_product_banner = options.Class.extend({
    
    events: Object.assign({}, options.Class.prototype.events || {}, {
      'click we-button.biz_add_product':'_addproductsection',
    }),

    _addproductsection: function () {
        var self = this.$target;
        self.$modal = $(renderToElement("theme_snazzy.select_product_banner"));
        self.$modal.appendTo('body');
        self.$modal.modal('show');
        var $select_product_banner = self.$modal.find("#select_product_banner"),
            $product_slider_cancel = self.$modal.find("#cancel"),
            $pro_sub_data = self.$modal.find("#prod_sub_data");
        rpc('/theme_snazzy/hotspot_product_select').then(function(res) {
            $('#select_product_banner option[value!="0"]').remove();
            res.forEach((y) => {
                $("select[id='select_product_banner']").append($('<option>', {
                    value: y["id"],
                    text: y["name"]
                }));
            });
            
        });

        $pro_sub_data.on('click', function() {
            var target = this.$target;
            self.attr('data-prod-select-id', $select_product_banner.val());
            var product_id = self.attr('data-prod-select-id');
            rpc('/theme_snazzy/get_product_banner_details_js', {
                'product_id': product_id
            }).then(function(res) {
                if (res) {
                    var demo_section = $(renderToElement("theme_snazzy.edit_mode_product_banner"));
                    self.find('.no-product-text').remove();
                    self.find('.edit_mode_product_banner').remove();
                    $(demo_section).appendTo(self.find('.container'));
                    self.find('.edit_mode_product_banner .product-name').text(res.product_name);
                    if (res.product_description != false) {
                        self.find('.edit_mode_product_banner .description').text(res.product_description);
                    } else{
                        self.find('.edit_mode_product_banner .description').text('product description');
                    }
                    self.find('.edit_mode_product_banner .edit_mode_product_image').attr('src', '/web/image/product.template/'+res.product_id+'/image_1920');
                }
            });
        });
        $product_slider_cancel.on('click', function() {
            self.getParent()._onRemoveClick($.Event("click"))
        });
    }
});   
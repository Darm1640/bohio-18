/** @odoo-module */
import animations from "@website/js/content/snippets.animation";

animations.registry.theme_snazzy_product_banner = animations.Class.extend({
    selector: ".bizople_product_banner",
    disabledInEditableMode: false,
    start: function() {
        var self = this.$target;
        if (this.editableMode) {
            self.find('.edit_mode_product_banner').removeClass('d-none');
            self.find('.product_banner_main_section').remove();
        }
        if (!this.editableMode) {
            self.find('.edit_mode_product_banner').addClass('d-none');
            var product_id = self.attr('data-prod-select-id');
            $.get("/theme_snazzy/get_product_banner_details_xml", {
                'product_id': self.attr('data-prod-select-id') || '',
            }).then(function(data) {
                if (data) {
                    self.find('.product_banner_main_section').remove();
                    $(data).appendTo(self.find('.container'));

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
                    $('.lazyload').lazyload();
                }
            });
        }
    }
});
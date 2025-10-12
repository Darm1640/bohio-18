/** @odoo-module */
	
import { rpc } from "@web/core/network/rpc";

import publicWidget from "@web/legacy/js/public/public_widget";
publicWidget.registry.Colorvariant = publicWidget.Widget.extend({
	selector: ".product_color_attribute, .dynamic_config_main_section, .bizople_dynamic_config_tool .product_info_wrapper,.alternative_and_accessory_products,#products_grid .o_wsale_product_information",
	events: {
		'mouseenter .css_attribute_color': 'onHoverChange',
		'click .css_attribute_color input': 'onClickChange',
		'mouseleave .css_attribute_color': 'onChangeLeave',
	},

	onHoverChange: function (ev) {
		var selected_color_val = $(ev.target).find('input').val()
		var product_id = $(ev.target).find('input').attr('product_id')
		rpc("/get/selected_color_image", {
			'selected_color_val': selected_color_val,
			'product_id': product_id,
		}).then(function(data){
			if (data){
				var varinat_id = data['varinat_id']
				var product_name = data['product_name']
				$(ev.currentTarget).parents('.o_wsale_product_grid_wrapper').find('img').attr('src', '/web/image/product.product/'+varinat_id+'/image_1024/'+product_name)
			}
		})
	},

	onClickChange: function (ev) {
		var selected_color_val = $(ev.target).val()
		var product_id = $(ev.target).attr('product_id')
		rpc("/get/selected_color_image", {
			'selected_color_val': selected_color_val,
			'product_id': product_id,
		}).then(function(data){
			if (data){
				var varinat_id = data['varinat_id']
				var product_name = data['product_name']
				var product_price = data['variant_price']
				var variant_discount = data['variant_discount']
				$(ev.currentTarget).parents('.product_colors').find('.css_attribute_color.active')
				.removeClass("active")
				$(ev.currentTarget).parent('.css_attribute_color').addClass("active")
				$(ev.currentTarget).parents('.o_wsale_product_grid_wrapper').find('img').attr('src', '/web/image/product.product/'+varinat_id+'/image_1024/'+product_name)
				// $(ev.currentTarget).parents('.o_wsale_product_grid_wrapper').find('.o_wsale_product_btn input').attr('value', varinat_id)
				$(ev.currentTarget).parents('.o_wsale_product_grid_wrapper').find('.product_price .extra_price span').text(parseFloat(product_price).toFixed(2))
				if(variant_discount){
					var base_price = data['variant_list_price']
					$(ev.currentTarget).parents('.o_wsale_product_grid_wrapper').find('.product_price .extra_discount').removeClass('d-none')
					$(ev.currentTarget).parents('.o_wsale_product_grid_wrapper').find('.product_price .extra_discount span').text(parseFloat(base_price).toFixed(2))
				}else{
					$(ev.currentTarget).parents('.o_wsale_product_grid_wrapper').find('.product_price .extra_discount').addClass('d-none')

				}
			}
		})
	},

	onChangeLeave: function(ev) {
		var defualt_product_id = $(ev.currentTarget).parents('.o_wsale_product_grid_wrapper').find('.css_attribute_color input').attr('product_id')
		var defualt_product_name = $(ev.currentTarget).parents('.o_wsale_product_grid_wrapper').find('.css_attribute_color input').attr('product_name')
		var active_label = $(ev.currentTarget).parents('.product_color_attribute').find('.active')

		if (active_label.length){
			var selected_variant_id = active_label.parents('.o_wsale_product_grid_wrapper').find('.active input').attr('value')
			var selected_product_id = active_label.parents('.o_wsale_product_grid_wrapper').find('.active input').attr('product_id')
			rpc("/get/selected_color_image", {
				'selected_color_val': selected_variant_id,
				'product_id': selected_product_id,
			}).then(function(data){
				if (data){
					var varinat_id = data['varinat_id']
					var product_name = data['product_name']
					$(ev.currentTarget).parents('.o_wsale_product_grid_wrapper').find('img').attr('src', '/web/image/product.product/'+varinat_id+'/image_1024/'+product_name)
				}
			})
		}else{
			$(ev.currentTarget).parents('.o_wsale_product_grid_wrapper').find('img').attr('src', '/web/image/product.template/'+defualt_product_id+'/image_1024/'+defualt_product_name)
		}
	}
});
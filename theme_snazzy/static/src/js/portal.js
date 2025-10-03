/** @odoo-module */	
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.SnazzyPortalAddress = publicWidget.Widget.extend({
	selector: ".oe_portal_address",
	events: {
		'change #country_id': '_get_related_state',
	},
	start: function() {
		var country = ''
		if ($('#country_id').length && $('#country_id').val()) {
			var country = $('#country_id').val();
			if(country){
				rpc('/get-related-state', {'country_id': country}).then(function(data){
					if(data.state_ids){
						$("#div_state").show();
						$("#state_id").html(data.state_vals)
					}else{
						$("#div_state").hide();
					}
				});
			}
		}
		else{
			$("#div_state").hide();
		}
	},
	_get_related_state: function(ev) {
		if ($('#country_id').length && $('#country_id').val()){
			var country = $('#country_id').val();
			if(country){
				rpc('/get-related-state', {'country_id': country}).then(function(data){
					if(data.state_ids){
						$("#div_state").show();
						$("#state_id").html(data.state_vals)
					}else{
						$("#div_state").hide();
					}
				});
			}
		}
	},
});
publicWidget.registry.SnazzyUserImage = publicWidget.Widget.extend({
	selector: ".o_portal_wrap",
	events: {
		'change .user_image .image_loaded': '_update_user_image',
	},
	
	_update_user_image: function(ev) {
		var image_input = null;
		var image = document.querySelector('.image_loaded').files[0];
		if (image) {
			var reader1 = new FileReader();
			reader1.readAsDataURL(image);
			reader1.onload = function(e){
				image_input = e.target.result;
				rpc('/update-image',{'img_attachment':image_input}).then(function(data){
					if(data){
						$("#user_image_load").html(data)
					}
				});
			}
		}
	},
});
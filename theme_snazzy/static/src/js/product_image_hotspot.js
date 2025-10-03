/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.imghotspotpopover = publicWidget.Widget.extend({
	selector: ".image_hotspot",
	events: {
		'click .hotspot_info': '_openhotspotpopover',
	},
	/**
     * @constructor
     */
	init: function () {
		this._super.apply(this, arguments);
		this._popoverRPC = null;
	},
	start: function () {
		var self = this.$target;
		var popover_bg = this.$el.find(".static_image_hotspot_info").css('background-color');
		this.$el.find('.hotspot_info').popover({
			trigger: 'manual',
			animation: true,
			html: true,
			container: 'body',
			placement: 'bottom',
			trigger: 'focus',
			template: '<div class="popover hotspot-popover" style="background-color: '+popover_bg+'; border-color: '+popover_bg+'" role="tooltip"><div class="arrow" style="border-color: '+popover_bg+'"></div><h3 class="popover-header"></h3><div class="popover-body"></div></div>'
		});
		$("body").addClass("image_hotspot_active");

		if (self.hasClass("hotspot_dynamic")) {
			if (this.editableMode) {
				self.find('.hotspot_info').removeClass('quick_btn')
			}
			if (!this.editableMode) {
				self.find('.hotspot_info').addClass('quick_btn')
			}   
		}
	},
	
	_openhotspotpopover: function (ev) {
		var self = this;
		$(this.selector).not(ev.currentTarget).popover('hide');
		self.$el.find('.hotspot_info').popover("show");
	}
});
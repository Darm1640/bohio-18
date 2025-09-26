/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.BohioRealEstate = publicWidget.Widget.extend({
    selector: '.bohio-properties-map, .bohio-homepage',

    start() {
        console.log('BOHIO Real Estate module loaded');
        return this._super.apply(this, arguments);
    },
});
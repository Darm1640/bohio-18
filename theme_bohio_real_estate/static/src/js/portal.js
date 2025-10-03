/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.BohioPortal = publicWidget.Widget.extend({
    selector: '.o_portal',
    events: {
        // Portal specific events can be added here
    },

    /**
     * @override
     */
    start: function () {
        this._super.apply(this, arguments);
        console.log('Bohio Portal initialized');
    },
});

export default publicWidget.registry.BohioPortal;

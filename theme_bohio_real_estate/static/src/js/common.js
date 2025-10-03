/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.BohioCommon = publicWidget.Widget.extend({
    selector: 'body',
    events: {
        'click .property-card': '_onPropertyCardClick',
    },

    /**
     * @override
     */
    start: function () {
        this._super.apply(this, arguments);
        this._initLazyLoading();
    },

    /**
     * Initialize lazy loading for images
     * @private
     */
    _initLazyLoading: function () {
        if ('loading' in HTMLImageElement.prototype) {
            const images = document.querySelectorAll('img[loading="lazy"]');
            images.forEach(img => {
                img.src = img.dataset.src || img.src;
            });
        } else {
            // Fallback for browsers that don't support lazy loading
            console.log('Lazy loading not supported, loading all images');
        }
    },

    /**
     * Handle property card clicks for analytics
     * @private
     * @param {Event} ev
     */
    _onPropertyCardClick: function (ev) {
        const $card = $(ev.currentTarget);
        const propertyId = $card.data('property-id');

        if (propertyId) {
            console.log('Property card clicked:', propertyId);
            // Analytics tracking can be added here
        }
    },
});

export default publicWidget.registry.BohioCommon;

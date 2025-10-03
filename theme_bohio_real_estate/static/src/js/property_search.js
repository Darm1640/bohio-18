/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PropertySearch = publicWidget.Widget.extend({
    selector: '.bohio-search-container',
    events: {
        'submit .bohio-search-form': '_onSearchSubmit',
        'click .toggle-advanced-link': '_toggleAdvancedSearch',
    },

    /**
     * @override
     */
    start: function () {
        this._super.apply(this, arguments);
        this._initAutocomplete();
    },

    /**
     * Initialize autocomplete for neighborhood field
     * @private
     */
    _initAutocomplete: function () {
        const $neighborhoodInput = this.$('.search-location input[name="neighborhood"]');
        if ($neighborhoodInput.length) {
            // TODO: Implementar autocomplete con barrios desde backend
            console.log('Autocomplete initialized for neighborhood field');
        }
    },

    /**
     * Handle search form submission
     * @private
     * @param {Event} ev
     */
    _onSearchSubmit: function (ev) {
        // Allow normal form submission
        // Additional validation or tracking can be added here
        const formData = new FormData(ev.currentTarget);
        console.log('Search submitted:', Object.fromEntries(formData));
    },

    /**
     * Toggle advanced search panel
     * @private
     * @param {Event} ev
     */
    _toggleAdvancedSearch: function (ev) {
        ev.preventDefault();
        const $link = $(ev.currentTarget);
        const $icon = $link.find('i');

        // Toggle icon rotation
        $icon.toggleClass('rotate-180');
    },
});

export default publicWidget.registry.PropertySearch;

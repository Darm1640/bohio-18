/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * BOHIO Service Type Selector Widget
 * Manages the service type button toggle (Arrendar/Comprar/Todo)
 * Updates hidden input value for form submission
 */
const ServiceTypeSelectorWidget = publicWidget.Widget.extend({
    selector: '.service-type-selector',
    xmlDependencies: [],

    events: {
        'click .service-type-btn': '_onServiceButtonClick',
    },

    /**
     * Initialize widget
     */
    start: function () {
        this._super.apply(this, arguments);

        this.serviceButtons = this.el.querySelectorAll('.service-type-btn');
        this.selectedServiceInput = document.getElementById('selectedServiceType');

        if (!this.selectedServiceInput) {
            console.warn('[ServiceTypeSelector] Hidden input #selectedServiceType not found');
            return Promise.resolve();
        }

        console.log('[ServiceTypeSelector] Widget initialized');
        return Promise.resolve();
    },

    /**
     * Handle service button click
     */
    _onServiceButtonClick: function (ev) {
        ev.preventDefault();
        const clickedButton = ev.currentTarget;

        // Get service type from data attribute
        const serviceType = clickedButton.getAttribute('data-service');

        if (!serviceType) {
            console.warn('[ServiceTypeSelector] Button missing data-service attribute');
            return;
        }

        // Remove active class from all buttons and apply inactive styles
        this.serviceButtons.forEach(btn => {
            btn.classList.remove('active');
        });

        // Add active class to clicked button
        clickedButton.classList.add('active');

        // Update hidden input value
        if (this.selectedServiceInput) {
            this.selectedServiceInput.value = serviceType;
            console.log('[ServiceTypeSelector] Service type selected:', serviceType);
        }
    },

    /**
     * Cleanup
     */
    destroy: function () {
        this._super.apply(this, arguments);
    }
});

publicWidget.registry.ServiceTypeSelectorWidget = ServiceTypeSelectorWidget;

export default ServiceTypeSelectorWidget;

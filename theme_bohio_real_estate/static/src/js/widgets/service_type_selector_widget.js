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

        // Remove active class from all buttons
        this.serviceButtons.forEach(btn => {
            btn.classList.remove('active');
        });

        // Add active class to clicked button
        clickedButton.classList.add('active');

        // Update hidden input value
        if (this.selectedServiceInput) {
            this.selectedServiceInput.value = serviceType;
            console.log('[ServiceTypeSelector] Service type selected:', serviceType);

            // Disparar evento personalizado para notificar el cambio
            const changeEvent = new CustomEvent('serviceTypeChanged', {
                detail: { serviceType: serviceType },
                bubbles: true,
                cancelable: true
            });
            this.el.dispatchEvent(changeEvent);

            // También disparar evento change en el input oculto
            const inputChangeEvent = new Event('change', { bubbles: true });
            this.selectedServiceInput.dispatchEvent(inputChangeEvent);
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

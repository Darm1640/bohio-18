/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import DynamicSnippetCarousel from "@website/snippets/s_dynamic_snippet_carousel/000";

/**
 * Dynamic Snippet para Propiedades
 * Extiende DynamicSnippetCarousel para soportar filtros específicos de properties
 */
const DynamicSnippetProperties = DynamicSnippetCarousel.extend({
    selector: '.s_dynamic_snippet_properties',

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Override para la URL principal de propiedades
     * @override
     * @private
     */
    _getMainPageUrl() {
        return "/properties";
    },
});

/**
 * Widget para las tarjetas individuales de propiedades
 * Maneja eventos de click y acciones específicas
 */
const DynamicSnippetPropertiesCard = publicWidget.Widget.extend({
    selector: '.o_carousel_property_card',
    events: {
        'click': '_onClickCard',
        'mouseenter': '_onMouseEnter',
        'mouseleave': '_onMouseLeave',
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    start: function () {
        // Validar que el elemento existe antes de inicializar
        if (!this.$el || !this.$el.length) {
            return Promise.resolve();
        }
        return this._super.apply(this, arguments);
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Handler para el click en la tarjeta
     * @private
     */
    _onClickCard(ev) {
        if (!this.$el || !this.$el.length) {
            return;
        }

        // Si el click es en un link o botón, no hacer nada
        if ($(ev.target).is('a, button') || $(ev.target).closest('a, button').length) {
            return;
        }

        // Si no, navegar a la página de detalle
        const propertyUrl = this.$el.find('a').first().attr('href');
        if (propertyUrl) {
            window.location.href = propertyUrl;
        }
    },

    /**
     * Handler para mouse enter
     * @private
     */
    _onMouseEnter(ev) {
        if (this.$el && this.$el.length) {
            this.$el.addClass('shadow');
        }
    },

    /**
     * Handler para mouse leave
     * @private
     */
    _onMouseLeave(ev) {
        if (this.$el && this.$el.length) {
            this.$el.removeClass('shadow');
        }
    },
});

// Registrar los widgets
publicWidget.registry.dynamic_snippet_properties = DynamicSnippetProperties;
publicWidget.registry.dynamic_snippet_properties_card = DynamicSnippetPropertiesCard;

export default DynamicSnippetProperties;

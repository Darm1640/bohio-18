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
     * Obtiene el dominio de búsqueda para tipo de servicio (rent/sale)
     * @private
     */
    _getTypeServiceSearchDomain() {
        const searchDomain = [];
        const typeService = this.$el.get(0).dataset.typeService;

        if (typeService && typeService !== 'all') {
            if (typeService === 'rent') {
                searchDomain.push(['type_service', 'in', ['rent', 'sale_rent']]);
            } else if (typeService === 'sale') {
                searchDomain.push(['type_service', 'in', ['sale', 'sale_rent']]);
            } else if (typeService === 'sale_used') {
                // Venta sin proyecto (usadas)
                searchDomain.push(['type_service', 'in', ['sale', 'sale_rent']]);
                searchDomain.push(['project_worksite_id', '=', false]);
            } else if (typeService === 'projects') {
                // Venta con proyecto (nuevas)
                searchDomain.push(['type_service', 'in', ['sale', 'sale_rent']]);
                searchDomain.push(['project_worksite_id', '!=', false]);
            }
        }

        return searchDomain;
    },

    /**
     * Obtiene el dominio de búsqueda para tipo de propiedad (apartment/house/office)
     * @private
     */
    _getPropertyTypeSearchDomain() {
        const searchDomain = [];
        const propertyType = this.$el.get(0).dataset.propertyType;

        if (propertyType && propertyType !== 'all') {
            searchDomain.push(['property_type', '=', propertyType]);
        }

        return searchDomain;
    },

    /**
     * Obtiene el dominio de búsqueda para ciudad
     * @private
     */
    _getCitySearchDomain() {
        const searchDomain = [];
        const cityId = this.$el.get(0).dataset.cityId;

        if (cityId && cityId !== 'all') {
            searchDomain.push(['city_id', '=', parseInt(cityId)]);
        }

        return searchDomain;
    },

    /**
     * Obtiene el dominio de búsqueda para región/barrio
     * @private
     */
    _getRegionSearchDomain() {
        const searchDomain = [];
        const regionId = this.$el.get(0).dataset.regionId;

        if (regionId && regionId !== 'all') {
            searchDomain.push(['region_id', '=', parseInt(regionId)]);
        }

        return searchDomain;
    },

    /**
     * Obtiene el dominio de búsqueda para rango de precios
     * @private
     */
    _getPriceRangeSearchDomain() {
        const searchDomain = [];
        const priceMin = this.$el.get(0).dataset.priceMin;
        const priceMax = this.$el.get(0).dataset.priceMax;

        if (priceMin) {
            searchDomain.push(['list_price', '>=', parseFloat(priceMin)]);
        }

        if (priceMax) {
            searchDomain.push(['list_price', '<=', parseFloat(priceMax)]);
        }

        return searchDomain;
    },

    /**
     * Obtiene el dominio de búsqueda para características
     * @private
     */
    _getFeaturesSearchDomain() {
        const searchDomain = [];
        const minBedrooms = this.$el.get(0).dataset.minBedrooms;
        const minBathrooms = this.$el.get(0).dataset.minBathrooms;
        const minArea = this.$el.get(0).dataset.minArea;

        if (minBedrooms) {
            searchDomain.push(['bedrooms', '>=', parseInt(minBedrooms)]);
        }

        if (minBathrooms) {
            searchDomain.push(['bathrooms', '>=', parseInt(minBathrooms)]);
        }

        if (minArea) {
            searchDomain.push(['area', '>=', parseFloat(minArea)]);
        }

        return searchDomain;
    },

    /**
     * Override del método _getSearchDomain para agregar filtros de propiedades
     * @override
     * @private
     */
    _getSearchDomain: function () {
        const searchDomain = this._super.apply(this, arguments);

        // Agregar dominio base de propiedades
        searchDomain.push(['is_property', '=', true]);
        searchDomain.push(['active', '=', true]);
        searchDomain.push(['state', '=', 'free']);

        // Agregar filtros específicos de propiedades
        searchDomain.push(...this._getTypeServiceSearchDomain());
        searchDomain.push(...this._getPropertyTypeSearchDomain());
        searchDomain.push(...this._getCitySearchDomain());
        searchDomain.push(...this._getRegionSearchDomain());
        searchDomain.push(...this._getPriceRangeSearchDomain());
        searchDomain.push(...this._getFeaturesSearchDomain());

        return searchDomain;
    },

    /**
     * Override para la URL principal de propiedades
     * @override
     * @private
     */
    _getMainPageUrl() {
        return "/properties";
    },

    /**
     * Obtiene parámetros RPC adicionales para propiedades
     * @override
     * @private
     */
    _getRpcParameters: function () {
        const params = this._super.apply(this, arguments);

        // Agregar parámetros específicos de propiedades si es necesario
        return Object.assign(params, {
            // Aquí podrías agregar parámetros adicionales si los necesitas
        });
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
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Handler para el click en la tarjeta
     * @private
     */
    _onClickCard(ev) {
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
        this.$el.addClass('shadow');
    },

    /**
     * Handler para mouse leave
     * @private
     */
    _onMouseLeave(ev) {
        this.$el.removeClass('shadow');
    },
});

// Registrar los widgets
publicWidget.registry.dynamic_snippet_properties = DynamicSnippetProperties;
publicWidget.registry.dynamic_snippet_properties_card = DynamicSnippetPropertiesCard;

export default DynamicSnippetProperties;

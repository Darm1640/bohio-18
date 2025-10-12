/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";
import s_dynamic_snippet_carousel_options from "@website/snippets/s_dynamic_snippet_carousel/options";
import wUtils from "@website/js/utils";

/**
 * Opciones del snippet dinámico de propiedades
 * Define los controles disponibles en el Website Builder
 */
const dynamicSnippetPropertiesOptions = s_dynamic_snippet_carousel_options.extend({

    /**
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
        this.modelNameFilter = 'product.template';  // Usar product.template para propiedades

        // Dominio base: solo propiedades
        this.contextualFilterDomain.push(['is_property', '=', true]);
        this.contextualFilterDomain.push(['active', '=', true]);
        this.contextualFilterDomain.push(['state', '=', 'free']);

        // Inicializar colecciones
        this.propertyCities = {};
        this.propertyRegions = {};

        // Obtener servicio ORM
        this.orm = this.bindService("orm");
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * Obtiene las ciudades disponibles
     * @private
     * @returns {Promise}
     */
    _fetchPropertyCities: function () {
        return this.orm.searchRead(
            "res.city",
            wUtils.websiteDomain(this),
            ["id", "name"],
            {
                order: "name ASC",
                limit: 100,
            }
        );
    },

    /**
     * Obtiene las regiones/barrios disponibles
     * @private
     * @returns {Promise}
     */
    _fetchPropertyRegions: function () {
        return this.orm.searchRead(
            "property.region",
            wUtils.websiteDomain(this),
            ["id", "name", "city_id"],
            {
                order: "name ASC",
                limit: 200,
            }
        );
    },

    /**
     * @override
     * @private
     */
    _renderCustomXML: async function (uiFragment) {
        await this._super.apply(this, arguments);
        await this._renderPropertyCitySelector(uiFragment);
        await this._renderPropertyRegionSelector(uiFragment);
    },

    /**
     * Renderiza el selector de ciudades
     * @private
     * @param {HTMLElement} uiFragment
     */
    _renderPropertyCitySelector: async function (uiFragment) {
        const cities = await this._fetchPropertyCities();
        for (let city of cities) {
            this.propertyCities[city.id] = city;
        }
        const citySelectorEl = uiFragment.querySelector('[data-name="property_city_opt"]');
        if (citySelectorEl) {
            return this._renderSelectUserValueWidgetButtons(citySelectorEl, this.propertyCities);
        }
    },

    /**
     * Renderiza el selector de regiones
     * @private
     * @param {HTMLElement} uiFragment
     */
    _renderPropertyRegionSelector: async function (uiFragment) {
        const regions = await this._fetchPropertyRegions();
        for (let region of regions) {
            this.propertyRegions[region.id] = region;
        }
        const regionSelectorEl = uiFragment.querySelector('[data-name="property_region_opt"]');
        if (regionSelectorEl) {
            return this._renderSelectUserValueWidgetButtons(regionSelectorEl, this.propertyRegions);
        }
    },

    /**
     * Establece valores por defecto de las opciones
     * @override
     * @private
     */
    _setOptionsDefaultValues: function () {
        this._setOptionValue('typeService', 'all');
        this._setOptionValue('propertyType', 'all');
        this._setOptionValue('cityId', 'all');
        this._setOptionValue('regionId', 'all');
        this._super.apply(this, arguments);
    },
});

// Registrar las opciones
options.registry.dynamic_snippet_properties = dynamicSnippetPropertiesOptions;

export default dynamicSnippetPropertiesOptions;

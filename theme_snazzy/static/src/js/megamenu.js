/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";

options.registry.MegaMenuLayout = options.registry.MegaMenuLayout.extend({
    _getCurrentTemplateXMLID: function () {
        let currentTemplateXMLID = this._super();

        const templateName = (currentTemplateXMLID || '').split('.')[1];
        if ([
            's_mega_menu_four_snippet',
            's_mega_menu_five_snippet',
            's_mega_menu_dynamic_snippet',
        ].includes(templateName)) {
            this.$el.find('.hasCategoriesToggle').hide();
        } else {
            this.$el.find('.hasCategoriesToggle').show();
        }

        const templateDefiningClass = this.containerEl.querySelector('section')
            .classList.value.split(' ').filter(cl => cl.startsWith('s_mega_menu'))[0];

        var className = this.containerEl.querySelector('section').classList.value;
        if (className.includes('snazzy_mega_menu')) {
            
            if (this.fetchEcomCategories) {
                let categoryTemplateClass = templateDefiningClass;
                if (!templateDefiningClass.includes('s_mega_menu_category')) {
                    categoryTemplateClass = templateDefiningClass.replace(
                        /^s_mega_menu(_\w+)(_snippet)$/,
                        's_mega_menu_category$1$2'
                    );
                }
                currentTemplateXMLID = `snazzy_theme_common.${categoryTemplateClass}`;
                return currentTemplateXMLID;
            }
            else{
                const categoryTemplateClass = templateDefiningClass.replace(
                    /^s_mega_menu_category(_\w+)(_snippet)$/,
                    's_mega_menu$1$2'
                );
                currentTemplateXMLID = `snazzy_theme_common.${categoryTemplateClass}`;
                return currentTemplateXMLID;
            }
        } else {
            if (this.fetchEcomCategories) {
                currentTemplateXMLID = currentTemplateXMLID.replace('website.', 'website_sale.');
                return currentTemplateXMLID;
            }
            else{
                return `website.${templateDefiningClass}`;
            }
        }
    },
});
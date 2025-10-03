/** @odoo-module */


import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ProductBrandSearch = publicWidget.Widget.extend({
    selector: ".shopby-brand",
    events: {
        'click .alphabetic-search a.alphabet_letter': '_BrandFilter',
    },
    _BrandFilter: function (ev) {
        var brand_alphabet = $(ev.currentTarget).text();
        if ($(ev.currentTarget).hasClass('view-all')) {
            $('a.alphabet_letter').removeClass('active')
            $(ev.currentTarget).addClass('active')
            $('#brand-alphabetic-filter .list-header').removeClass('d-none')
        } else {
            $('a.alphabet_letter').removeClass('active')
            $(ev.currentTarget).addClass('active')
            var data_name = $(ev.currentTarget).data('name')
            $('#brand-alphabetic-filter .list-header').addClass('d-none')
            $('#brand-alphabetic-filter .list-header[data-name="'+data_name+'"]').removeClass('d-none')
        }
    },
});
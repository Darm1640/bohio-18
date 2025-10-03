/** @odoo-module **/
import { renderToElement } from "@web/core/utils/render";
import options from "@web_editor/js/editor/snippets.options";
import { rpc } from "@web/core/network/rpc";
import { debounce } from "@web/core/utils/timing";

var config_action_buttons = {
    'show_cart': 'on',
    'show_wishlist': 'on',
    'show_compare': 'on',
    'show_quickview': 'on',
    'show_label': 'on',
    'show_price': 'on',
    'show_ratings': 'on',
    'show_description': 'on',
    'img_bg_color': 'on',
    'show_similar_products': 'on',
}

options.registry.dynamic_config_tool = options.Class.extend({
    events:{
        'click we-button.biz_change_product':'prod_config',
        'click li.nav_item_right':'_active_btn_parent_class_bg',
    },
    /**
     * @override
     */
    init(parent, params) {
  
        this._super.apply(this, arguments);
        this.do_action = this.bindService("action");
        this._searchRecord = debounce(this._searchRecord, 400);
        this._searchMultipleRecord = debounce(this._searchMultipleRecord, 400);
        this.model = this.$bsTarget.data('model') || "product.template";
        this.idlist = this.$bsTarget.data('recordids') || []
        this.designmode = this.$bsTarget.data('designmode') || 'grid'
        this.designstyle = this.$bsTarget.data('designstyle') || 'style_1'
        this.designactionbutton = this.$bsTarget.data('designactionbutton') || config_action_buttons
        this.itemperrow = this.$bsTarget.data('itemperrow') || 4
        this.domain_list = this.$bsTarget.data('domain_list') || []
        this.record_match = this.$bsTarget.data('record_match') || 'and'
        this.recordselectionmode = this.$bsTarget.data('recordselectionmode') || 'manual'
        this.record_limit = this.$bsTarget.data('record_limit') || 6
        this.sortby = this.$bsTarget.data('sortby') || 'default'
        this.orderby = this.$bsTarget.data('orderby') || 'default'

        this.domainField = {
            'name': {'type': "text", 'label': 'Name'},
            'public_categ_ids': {'type': "many2many", 'label': 'Category', 'model': 'product.public.category'},
            'brand_id.id': {'type': "many2one", 'label': 'Brand', 'model': 'product.brand'},
            'attribute_line_ids.value_ids': {'type': "many2one", 'label': 'Attributes', 'model': 'product.attribute.value'},
            'list_price': {'type': "integer", 'label': 'Price'},
            'biz_is_discounted_product': {'type': "boolean", 'label': 'Discount'}
        };
        this.domainOperators = {
            'text': { 'ilike': "contains", 'not ilike': "doesn't contain", '=': "is equal to", '!=': "is not equal to" },
            'many2many': { 'in': "in", 'not in': "not in", 'child_of': "in child category of" },
            'many2one': { 'in': "in", 'not in': "not in" },
            'integer': { '=': "equals", '!=': "not in", '>': 'greater than', '<': 'less then' },
            'boolean': { '!=': 'is set', '=': 'is not set' }
        };
    },
    /**
     * @override
     */
    async start(editMode) {
        var self = this;
        this._super();
        if (!editMode) {
            self.$el.find(".container").on("click", self.prod_config.bind(self));
        }
    },

    _active_btn_parent_class_bg: function() {
        self.$modal.find('.active.nav_link_right').parent().addClass("li_bg_color")
    },

    biz_dialog_events: function() {
        var self = this;
        self.$modal.find('input[name="config_type"]').unbind().on('change', function(ev) {self._changeConfigType(ev);})
        self.$modal.find('input[name="search_record"]').unbind().on('input', function(ev) {self._searchRecord(ev)})
        self.$modal.find('.searched_results .dropdown-item').unbind().on('click', function(ev) {self._selectRecord(ev)})
        self.$modal.find('.remove_product .remove-btn').unbind().on('click', function(ev) {self._removeSeletedRecord(ev)})
        self.$modal.find('.edit_product .edit-btn').unbind().on('click', function(ev) {self._openRecord(ev)})

        self.$modal.find('select[name="record_selection_mode"]').unbind().on('change', function(ev) {self._changeRecordSelectionMode(ev)})
        self.$modal.find('select[name="record_selection_match"]').unbind().on('change', function(ev) {self._changeRecordSelectionMatch(ev)})

        self.$modal.find('select[name="custom_domain_field"]').unbind().on('change', function(ev) {self._changeDomainField(ev)})
        self.$modal.find('select[name="custom_domain_operator"]').unbind().on('change', function(ev) {self._changeDomainOperator(ev)})
        self.$modal.find('.form-control.multiple-select').unbind().on('input', function(ev) {self._searchMultipleRecord(ev)})
        self.$modal.find('.domain_record_list p').unbind().on('click', function(ev) {self._selectMultipleRecord(ev)})
        self.$modal.find('.selected_domain_record_list .remove_record').unbind().on('click', function(ev) {self._removerecord(ev)})

        self.$modal.find('.apply_rule').unbind().on('click', function(ev) {self._addDomain(ev)})

        self.$modal.find('.edit_custom_domain').unbind().on('click', function(ev) {self._editDomain(ev)})
        self.$modal.find('.delete_custom_domain').unbind().on('click', function(ev) {self._deleteDomain(ev)})

        self.$modal.find('.add_new_rule .add_rule').unbind().on('click', function(ev) {self._addNewDomain(ev)})

        self.$modal.find('input#record_limit').unbind().on('change', function(ev) {self._changerecordlimit(ev)})
        self.$modal.find('select[name="record_sortby"]').unbind().on('change', function(ev) {self._changeSortBy(ev)})
        self.$modal.find('select[name="record_orderby"]').unbind().on('change', function(ev) {self._changeOrderBy(ev)})


        // design events
        self.$modal.find('.display_options .btn').unbind().on('click', function(ev) {self._updateActionButtons(ev)})
        self.$modal.find('select#mode_selection').unbind().on('change', function(ev) {self._changeDesignMode(ev)})
        self.$modal.find('select#layout_selection').unbind().on('change', function(ev) {self._changeDesignLayout(ev)})
        self.$modal.find('input#item_per_row').unbind().on('change', function(ev) {self._changeItemPerRow(ev)})



        self.$modal.find('.setting-wrapper .save-discard .save_config').unbind().on('click', function(ev) {self._saveDynamicConfig(ev)})

        self.$modal.find('.setting-wrapper .save-discard .discard_config').unbind().on('click', function(ev) {self._discardDynamicConfig(ev)})

        self.$modal.find('.setting-wrapper .next-back .back_tab').unbind().on('click', function(ev) {self._backtab(ev)})

        self.$modal.find('.setting-wrapper .next-back .next_tab').unbind().on('click', function(ev) {self._nexttab(ev)})
    },

    async onBuilt() {
        var self = this;
        this._super();
        if (this.prod_config()) {
            this.prod_config().fail(function() {
                self.getParent()._removeSnippet();
            });
        }
    },

    prod_config: function(type, value) {
        var self = this;
        var values = {
            'model': this.model,
            'style': this.designstyle,
            'mode': this.designmode,
            'record_match': this.record_match,
            'actionbutton': this.designactionbutton,
            'item_per_row': this.itemperrow,
            'record_limit': this.record_limit,
            'sortby': this.sortby,
            'orderby': this.orderby,
        }
        if (type != undefined && type.type == "click" || type == undefined) {
            self.$modal = $(renderToElement("theme_snazzy.dynamic_config_modal", values));
            self.$modal.appendTo('body');
            self.$modal.modal('show');
            self.biz_dialog_events();
            self._showConfigPreview()
            self._loadSelectedRecordLine()
            self.$modal.find('input[name="search_record"]').attr('data-model',self.model)
            self.$modal.find('select[name="record_selection_mode"]').val(self.recordselectionmode)
            self.$modal.find('select[name="record_selection_mode"]').change()

            if (self.model == 'product.public.category' || self.model == 'product.brand') {
                self.$modal.find('select[name="mode_selection"] option.list_layout').addClass('d-none')
            } else {
                self.$modal.find('select[name="mode_selection"] option.list_layout').removeClass('d-none')
            }

            if (self.model != 'product.template') {
                self.$modal.find('.record_sortby select').val('default')
                self.$modal.find('.record_sortby').addClass('d-none')
                self.$modal.find('.record_orderby select').val('default')
                self.$modal.find('.record_orderby').addClass('d-none')
            } else {
                self.$modal.find('.record_sortby').removeClass('d-none')
                self.$modal.find('.record_orderby').removeClass('d-none')
            }

            if (self.designmode == "list") {
                this.$modal.find('.item_limit').addClass('d-none')
            } else {
                this.$modal.find('.item_limit').removeClass('d-none')
            }

            if (self.model == "product.public.category") {
                this.$modal.find('.only_categ').removeClass('d-none')
            } else {
                this.$modal.find('.only_categ').addClass('d-none')
            }
        } else {
            return;
        }
    },

    _changeConfigType: function(ev) {
        var self = this
        this.model = $(ev.currentTarget).data('model')
        var model = $(ev.currentTarget).data('model')

        var has_custom_domain = $(ev.currentTarget).attr('has_custom_domain')
        if (has_custom_domain == 'true') {
            this.$modal.find('.record_selection_mode').removeClass('d-none')
            this.$modal.find('.display_options').addClass('d-flex').removeClass('d-none')
        } else {
            this.$modal.find('select[name="record_selection_mode"]').val('manual')
            this.$modal.find('select[name="record_selection_mode"]').change()
            this.$modal.find('.record_selection_mode').addClass('d-none')
            this.$modal.find('.display_options').addClass('d-none').removeClass('d-flex')
        }

        if (self.model == 'product.public.category' || self.model == 'product.brand') {
            self.$modal.find('select[name="mode_selection"] option.list_layout').addClass('d-none')
        } else {
            self.$modal.find('select[name="mode_selection"] option.list_layout').removeClass('d-none')
        }

        if (self.model == "product.public.category") {
            self.$modal.find('.only_categ').removeClass('d-none')
        } else {
            self.$modal.find('.only_categ').addClass('d-none')
            self.$modal.find('select[name="layout_selection"]').val('style_1')
            self.$modal.find('select[name="layout_selection"]').change()
        }

        if (self.model == 'product.template') {
            self.$modal.find('.record_sortby').removeClass('d-none')
            self.$modal.find('.record_orderby').removeClass('d-none')
        } else {
            self.$modal.find('.record_sortby select').val('default')
            self.$modal.find('.record_sortby').addClass('d-none')
            self.$modal.find('.record_orderby select').val('default')
            self.$modal.find('.record_orderby').addClass('d-none')
        }

        this.$modal.find('#search_record').attr('data-model', model)
        this.$modal.find('.searched_results').remove()
        this.$modal.find('.selected_results').empty()
        this.idlist = []
        this.domain_list = []
        this._showConfigPreview()
        this.biz_dialog_events();
    },

    _searchRecord: function(ev) {
        var self = this;
        var search = $(ev.currentTarget).val()
        var model = $(ev.currentTarget).attr('data-model')
        self.$modal.find('.searched_results').remove()
        if ($.isEmptyObject(self.idlist)) {
            
        }
        if(search) {
            if (model == 'product.template') {
                rpc('/config/product/data', {
                    'search': search,
                    'model': model,
                    'selectedlist': self.idlist,
                }).then(function(data) {
                    self.$modal.find('.search-section').append(data['searched_products_line_template'])
                    self.biz_dialog_events();
                })
            }
            if (model == 'product.public.category') {
                rpc('/config/category/data', {
                    'search': search,
                    'model': model,
                    'selectedlist': self.idlist,
                }).then(function(data) {
                    self.$modal.find('.search-section').append(data['searched_category_line_template'])
                    self.biz_dialog_events();
                })
            }
            if (model == 'product.brand') {
                rpc('/config/brand/data', {
                    'search': search,
                    'model': model,
                    'selectedlist': self.idlist,
                }).then(function(data) {
                    self.$modal.find('.search-section').append(data['searched_brand_line_template'])
                    self.biz_dialog_events();
                })
            }
            if (model == 'blog.post') {
                rpc('/config/blog/data', {
                    'search': search,
                    'model': model,
                    'selectedlist': self.idlist,
                }).then(function(data) {
                    self.$modal.find('.search-section').append(data['searched_blog_line_template'])
                    self.biz_dialog_events();
                })
            }
        }
    },

    _selectRecord: function (ev) {
        var self = this
        var product_id = $(ev.currentTarget).attr('id')
        var model = this.model
        self.idlist.push(parseInt(product_id))

        self.$modal.find('.searched_results').remove()
        self.$modal.find('input[name="search_record"]').val("")

        self._loadSelectedRecordLine()
        this.domain_list = []
    },

    _loadSelectedRecordLine: function() {
        var self = this

        if (this.idlist.length > 0) {
            rpc('/get/dynamic/config/selected/line', {
                'idlist': this.idlist,
                'model': this.model,
            }).then(function(data) {
                self.$modal.find('.selected_results').empty()
                self.$modal.find('.selected_results').append(data['selected_line_template'])
                self.biz_dialog_events();
                self._showConfigPreview();
            })
        }
    },

    _removeSeletedRecord: function(ev) {
        var product_id = $(ev.currentTarget).parents('.selected_item').attr('id')
        this.idlist = jQuery.grep(this.idlist, function(value) {
            return value != product_id;
        });
        if (this.model == 'product.template') {
            $(ev.currentTarget).parents('.selected_item').parent().remove()
        } else {
            $(ev.currentTarget).parents('.selected_item').remove()
        }
        this._showConfigPreview();
    },

    _showConfigPreview: function(ev) {
        var self = this
        var model = this.model
        if (this.idlist.length > 0 || this.domain_list.length > 0) {
            rpc('/get/dynamic/config',{
                'idlist': this.idlist,
                'model': this.model,
                'style': this.designstyle,
                'mode': this.designmode,
                'design_params': this.designactionbutton,
                'item_per_row': parseInt(this.itemperrow),
                'domain_list': this.domain_list,
                'record_match': this.record_match,
                'record_limit': parseInt(this.record_limit),
                'sortby': this.sortby,
                'orderby': this.orderby,
            }).then(function(data) {
                self.$modal.find('.preview-container .container-fluid').empty()
                self.$modal.find('.preview-container .container-fluid').append(data['dynamic_config_template'])
                self.$modal.find('.preview-container .lazyload').lazyload();
                if (self.designmode == 'slider') {
                    self.$modal.find('div#configurator-slider').owlCarousel({
                        margin: 30,
                        responsiveClass: true,
                        items: parseInt(self.itemperrow),
                        loop: false,
                        dots:false,
                        rows: true,
                        rowsCount: 2,
                        rewind:true,
                        nav:true,
                        navText: [
                            '<i class="fa fa-angle-left"></i>',
                            '<i class="fa fa-angle-right"></i>'
                        ],
                        autoplay: true,
                        autoplayTimeout: 5000,
                        autoplayHoverPause:true,
                        responsive: {
                            0: {
                                items: 1,
                            },
                            420: {
                                items: 1,
                            },
                            768: {
                                items: 3,
                            },
                            1000: {
                                items: parseInt(self.itemperrow),
                            },
                            1500: {
                                items: parseInt(self.itemperrow),
                            },
                        },
                    });
                }
            })
        } else {
            self.$modal.find('.preview-container .container-fluid').empty()
        }
    },

    _changeRecordSelectionMode: function(ev) {
        var self = this
        if ($(ev.currentTarget).val() == 'manual') {
            this.$modal.find('.search-section').show()
            this.$modal.find('.custom_domain_selector').remove()
            this.$modal.find('.add_new_rule').addClass('d-none')
            this.$modal.find('.record_selection_match').addClass('d-none')
            this.domain_list = []
        } else {
            this.$modal.find('.searched_results').remove()
            this.$modal.find('.selected_results').empty()
            this.$modal.find('.search-section').hide()
            this.$modal.find('.record_selection_match').removeClass('d-none')
            self._getCustomDomain();
        }
        this.recordselectionmode = $(ev.currentTarget).val()
        
    },
    _changeRecordSelectionMatch: function(ev) {
        var self = this
        this.record_match = $(ev.currentTarget).val()
        if (this.record_match == 'and') {
            self.$modal.find('.condition_match_label span').text('AND')
        } else {
            self.$modal.find('.condition_match_label span').text('OR')
        }
        this._showConfigPreview();
    },

    _getCustomDomain: function(ev) {
        var self = this
        var domain_list = this.domain_list
        $.each( domain_list, function( key, value ) {
            var field_label = self.domainField[value[0]].label
            var field_type = self.domainField[value[0]].type
            var field_operator = self.domainOperators[field_type][value[1]]
            if (field_type == 'many2many' || field_type == 'many2one' || field_type == 'one2many') {
                var domain_value = []
                var field_model = self.domainField[value[0]].model
                var record_ids = value[2]
                rpc('/get/selected/record/data', {
                    'model': field_model,
                    'record_ids': record_ids,
                }).then(function(data) {
                    var domain_value = data
                    var multi_record = true
                    var data = {
                        'name': field_label,
                        'operator': field_operator,
                        'value': domain_value,
                        'field_name': value[0],
                        'operator_value': value[1],
                        'multi_record': multi_record,
                        'record_match': self.record_match
                    }
                    var domain_selector =  $(renderToElement("theme_snazzy.selected_domain_text", data));
                    self.$modal.find('#record_selection').find('.add_new_rule').before(domain_selector)
                    self.biz_dialog_events();
                })
            } else {
                var domain_value = value[2]
                var multi_record = false
                var data = {
                    'name': field_label,
                    'operator': field_operator,
                    'value': domain_value,
                    'field_name': value[0],
                    'operator_value': value[1],
                    'multi_record': multi_record,
                    'record_match': self.record_match
                }
                var domain_selector =  $(renderToElement("theme_snazzy.selected_domain_text", data));
                self.$modal.find('#record_selection').find('.add_new_rule').before(domain_selector)
                self.biz_dialog_events();
            }
        })
        if (domain_list.length < 1) {
            var values = {
                'record_match': self.record_match
            }
            var domain_selector =  $(renderToElement("theme_snazzy.custom_domain_selector", values));
            this.$modal.find('#record_selection').find('.add_new_rule').before(domain_selector)
        }
        
        this.$modal.find('.add_new_rule').removeClass('d-none')
        self.biz_dialog_events();
    },

    _changeDomainField: function(ev) {
        var self = this;
        var field_name = $(ev.currentTarget).val()
        var field_type = $($(ev.currentTarget)[0].selectedOptions[0]).attr('type')
        var field_model = $($(ev.currentTarget)[0].selectedOptions[0]).attr('model')
        var field_operator = this.domainOperators[field_type]
        
        $(ev.currentTarget).parents('.custom_domain_selector').find('select[name="custom_domain_operator"]').empty()
        $.each( field_operator, function( key, value ) {
            var option_line = '<option value="' + key + '">' + value + '</option>'
            self.$modal.find('select[name="custom_domain_operator"]').append($(option_line))
        });

        if (field_type == 'many2many' || field_type == 'many2one') {
            $(ev.currentTarget).parents('.custom_domain_selector').find('#custom_domain_value').addClass('multiple-select')
            $(ev.currentTarget).parents('.custom_domain_selector').find('#custom_domain_value').attr('data-model', field_model)
            $(ev.currentTarget).parents('.custom_domain_selector').find('#custom_domain_value').show()
        } else if (field_type == 'text' || field_type == 'integer') {
            $(ev.currentTarget).parents('.custom_domain_selector').find('#custom_domain_value').removeClass('multiple-select')
            $(ev.currentTarget).parents('.custom_domain_selector').find('#custom_domain_value').removeAttr('data-model')
            $(ev.currentTarget).parents('.custom_domain_selector').find('#custom_domain_value').show()
        } else {
            $(ev.currentTarget).parents('.custom_domain_selector').find('#custom_domain_value').hide()
        }
        self.biz_dialog_events();

    },

    _addDomain: function(ev) {
        var self = this
        this.idlist = []
        
        var operator_name = $($(ev.currentTarget).parents('.custom_domain_selector').find('select[name="custom_domain_operator"]')[0].selectedOptions[0]).text()
        var operator_value = $(ev.currentTarget).parents('.custom_domain_selector').find('select[name="custom_domain_operator"]').val()

        var field_label = $($(ev.currentTarget).parents('.custom_domain_selector').find('select[name="custom_domain_field"]')[0].selectedOptions[0]).text()
        var field_value = $(ev.currentTarget).parents('.custom_domain_selector').find('select[name="custom_domain_field"]').val()

        if ($(ev.currentTarget).parents('.custom_domain_selector').find('#custom_domain_value').hasClass('multiple-select')) {
            var domain_value =[]
            var selected_badges = $(ev.currentTarget).parents('.custom_domain_selector').find('.selected_domain_record_list .selected_record')
            $(selected_badges).each(function(){
                var badgeData = {
                    'id': $(this).attr('id'),
                    'name': $(this).attr('name'),
                }
                var badgeid = $(this).attr('id');
                domain_value.push(badgeData);
            });
            var multi_record = true
        } else {
            var domain_value = $(ev.currentTarget).parents('.custom_domain_selector').find('#custom_domain_value').val()
            var multi_record = false
        }

        var data = {
            'name': field_label,
            'operator': operator_name,
            'value': domain_value,
            'field_name': field_value,
            'operator_value': operator_value,
            'multi_record': multi_record,
            'record_match': self.record_match
        }
        var domain_selector =  $(renderToElement("theme_snazzy.selected_domain_text", data));
        $(ev.currentTarget).parents('.custom_domain_selector').remove()
        self.$modal.find('#record_selection').find('.add_new_rule').before(domain_selector)
        this._makedomain()
        this._showConfigPreview();
        self.biz_dialog_events();
    },
    _discardDomain: function(ev) {
        $(ev.currentTarget).parents('.custom_domain_selector')
    },

    _editDomain: function(ev) {
        var self = this
        var field_name = $(ev.currentTarget).parents('.custom_domain_selector').find('span.field').attr('field_value')
        var operator_value = $(ev.currentTarget).parents('.custom_domain_selector').find('span.operator').attr('operator_value')

        if ($(ev.currentTarget).parents('.custom_domain_selector').find('.selected_record').length > 0) {
            var domain_value = []
            var selected_records = $(ev.currentTarget).parents('.custom_domain_selector').find('.selected_record')
            $(selected_records).each(function(){
                var badgeData = {
                    'id': $(this).attr('id'),
                    'name': $(this).attr('name'),
                }
                domain_value.push(badgeData);
            })
            var multiple_record = true
        } else {
            var domain_value = $(ev.currentTarget).parents('.custom_domain_selector').find('span.value').text()
            var multiple_record = false
        }
        var data = {
            'field_name': field_name,
            'value': domain_value,
            'multiple_record': multiple_record,
            'record_match': self.record_match
        }
        var domain_selector =  $(renderToElement("theme_snazzy.custom_domain_selector", data));

        $(ev.currentTarget).parents('.custom_domain_selector').before(domain_selector).remove()
        this.biz_dialog_events();
        $(domain_selector).find('.custom_domain_field').change()
        
    },
    _deleteDomain: function(ev) {
        $(ev.currentTarget).parents('.custom_domain_selector').remove()
        this._makedomain()
        this._showConfigPreview();
    },

    _addNewDomain: function (ev) {
        var self = this
        var values = {
            'record_match': self.record_match
        }
        var domain_selector =  $(renderToElement("theme_snazzy.custom_domain_selector", values));
        this.$modal.find('#record_selection').find('.add_new_rule').before(domain_selector)
        this.biz_dialog_events();
    },

    _changerecordlimit: function(ev) {
        this.record_limit = $(ev.currentTarget).val()
        $(ev.currentTarget).parent().find('label .current_record_limit').text($(ev.currentTarget).val())
        this._showConfigPreview()
    },
    _changeSortBy: function(ev){
        this.sortby = $(ev.currentTarget).val()
        this._showConfigPreview()
    },

    _changeOrderBy: function(ev){
        this.orderby = $(ev.currentTarget).val()
        this._showConfigPreview()
    },


    _makedomain: function () {
        var self = this;
        this.domain_list = []
        var selected_domains = this.$modal.find('.custom_domain_selector')
        $(selected_domains).each(function(){
            var field = $(this).find('.field').attr('field_value')
            var operator = $(this).find('.operator').attr('operator_value')

            if (field == 'biz_is_discounted_product') {
                var value = false
            } else {
                if ($(this).find('.selected_record').length > 0) {
                    var value = []
                    var selected_records = $(this).find('.selected_record')
                    $(selected_records).each(function(){
                        var recordId = $(this).attr('id')
                        value.push(recordId);
                    })
                } else {
                    var value = $(this).find('.value').text()
                }
            }

            var tuple = [field, operator, value]
            self.domain_list.push(tuple)
        })
    },


    _changeDomainOperator: function(ev) {},

    _searchMultipleRecord: function(ev) {
        var self = this;
        var model = $(ev.currentTarget).attr('data-model')

        var value = $(ev.currentTarget).val()
        var selected_records = []
        if ($(ev.currentTarget).parent().find('.selected_record').length > 0) {
            $(ev.currentTarget).parent().find('.selected_record').each(function(){
                var recordId = $(this).attr('id')
                selected_records.push(recordId);
            })
        }
        if (value) {
            rpc('/get/domain/record', {
                'value': value,
                'model': model,
                'selected_records': selected_records,
            }).then(function(data) {
                $(ev.currentTarget).parent().find('.domain_record_list').remove()
                $(ev.currentTarget).parent().find('.selected_domain_record_list').before(data['domain_record_list'])
                self.biz_dialog_events();
            })
        } else {
            $(ev.currentTarget).parent().find('.domain_record_list').remove()
        }
    },
    _selectMultipleRecord: function(ev) {
        var recordId = $(ev.currentTarget).attr('id')
        var recordName = $(ev.currentTarget).attr('name')
        var recordBadge = "<span class='selected_record d-inline-block p-2 border' id='"+recordId+"' name='"+recordName+"'>"+recordName+" <span class='remove_record ms-3'>x</span></span>"
        this.$modal.find('.selected_domain_record_list').append(recordBadge)
        $(ev.currentTarget).remove();
        this.biz_dialog_events();
    },
    _removerecord: function(ev) {
        $(ev.currentTarget).parent().remove();
        this.biz_dialog_events();
    },
    _openRecord: function(ev) {
        var self = this
        var prodid = parseInt($(ev.currentTarget).parents('.selected_item').attr('id'))
        self.do_action.doAction({
            "type": "ir.actions.act_window",
            "res_model": self.model,
            "views": [[false, "form"]],
            "res_id": prodid,
            "target": "new",
        }, {
            on_close: () => {
                self._showConfigPreview();
                self._loadSelectedRecordLine()
            }
        });
    },

    _updateActionButtons: function (ev) {
        if ($(ev.currentTarget).hasClass('on')) {
            $(ev.currentTarget).removeClass('on')
            this.designactionbutton[$(ev.currentTarget).attr('display_options')] = 'off'
        } else {
            $(ev.currentTarget).addClass('on')
            this.designactionbutton[$(ev.currentTarget).attr('display_options')] = 'on'
        }
        this._showConfigPreview()
    },
    _changeDesignMode: function (ev) {
        this.designmode = $(ev.currentTarget).val()
        this.$modal.find('select#layout_selection').val('style_1').change()
        if (this.designmode == 'list') {
            this.$modal.find('select#layout_selection .no_list').addClass('d-none')
            this.$modal.find('.item_limit').addClass('d-none')
        } else {
            this.$modal.find('select#layout_selection .no_list').removeClass('d-none')
            this.$modal.find('.item_limit').removeClass('d-none')
        }
        this._showConfigPreview()
    },
    _changeDesignLayout: function (ev) {
        this.designstyle = $(ev.currentTarget).val()
        this._showConfigPreview()
    },
    _changeItemPerRow: function (ev) {
        this.itemperrow = $(ev.currentTarget).val()
        $(ev.currentTarget).parent().find('label .current_item_limit').text($(ev.currentTarget).val())
        this._showConfigPreview()
    },

    _saveDynamicConfig: function (ev) {
        var self = this
        
        this.$bsTarget.attr('data-model', this.model)
        this.$bsTarget.attr('data-designmode', this.designmode)
        this.$bsTarget.attr('data-designstyle', this.designstyle)
        this.$bsTarget.attr('data-itemperrow', this.itemperrow)
        this.$bsTarget.attr('data-recordselectionmode', this.recordselectionmode)
        this.$bsTarget.attr('data-record_match', this.record_match)
        this.$bsTarget.attr('data-recordids', JSON.stringify(this.idlist))
        this.$bsTarget.attr('data-designactionbutton', JSON.stringify(this.designactionbutton))
        this.$bsTarget.attr('data-record_limit', this.record_limit)
        this.$bsTarget.attr('data-sortby', this.sortby)
        this.$bsTarget.attr('data-orderby', this.orderby)

        if (this.domain_list.length > 0) {
            this.$bsTarget.attr('data-domain_list', JSON.stringify(this.domain_list))
            this.$bsTarget.attr('data-recordids', "")
        } else {
            this.$bsTarget.removeAttr('data-domain_list')
        }

        this.$modal.remove()
    },

    _discardDynamicConfig: function(ev) {
        this.$modal.remove()
    },

    _backtab: function(ev) {
        var self = this
        var active_tab = self.$modal.find('.tab-section .nav-pills .nav_link_right.active')
        if ($(active_tab).hasClass('record_selection_tab')) {
            self.$modal.find('.type_selection_tab')[0].click()
            $(active_tab).parents('.nav-pills').find('.nav_item_right').removeClass('li_bg_color')
            $('.type_selection_tab').parent().addClass('li_bg_color')
        } else if ($(active_tab).hasClass('design_selection_tab')) {
            self.$modal.find('.record_selection_tab')[0].click()
            $(active_tab).parents('.nav-pills').find('.nav_item_right').removeClass('li_bg_color')
            $('.record_selection_tab').parent().addClass('li_bg_color')
        }
    },
    _nexttab: function(ev) {
        var self = this
        var active_tab = self.$modal.find('.tab-section .nav-pills .nav_link_right.active')
        if ($(active_tab).hasClass('type_selection_tab')) {
            self.$modal.find('.record_selection_tab')[0].click()
            $(active_tab).parents('.nav-pills').find('.nav_item_right').removeClass('li_bg_color')
            $('.record_selection_tab').parent().addClass('li_bg_color')
        } else if ($(active_tab).hasClass('record_selection_tab')) {
            self.$modal.find('.design_selection_tab')[0].click()
            $(active_tab).parents('.nav-pills').find('.nav_item_right').removeClass('li_bg_color')
            $('.design_selection_tab').parent().addClass('li_bg_color')
        }
    },
});

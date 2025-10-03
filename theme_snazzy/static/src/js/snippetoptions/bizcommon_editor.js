/** @odoo-module **/
import snippetsEditor from "@web_editor/js/editor/snippets.editor";
import { patch } from "@web/core/utils/patch";

patch(snippetsEditor.SnippetsMenu.prototype, {
     /**
     * @override
     */
    _onSaveRequest: function (ev) {
       
        const data = ev.data || {};
        if (data.invalidateSnippetCache) {
            this.invalidateSnippetCache = true;
        }
 
    
        ev.stopped = true;
        this._buttonClick(async (after) => {
          
            return this._execWithLoadingEffect(() => {
                const oldOnFailure = data.onFailure;
                data.onFailure = () => {
                    if (oldOnFailure) {
                        oldOnFailure();
                    }
                    after();
                };
                this.props.trigger_up({
                    name: 'request_save',
                    data
                });
            }, true);
        }, this.$el[0].querySelector('button[data-action=save]'));
        $(this.$body).find('#wrapwrap').find('.bizople_dynamic_config_tool [class*=container]').empty();
       


    },
    // ...other functions and properties
});

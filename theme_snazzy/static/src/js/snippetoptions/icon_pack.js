/** @odoo-module **/

import { Wysiwyg } from "@web_editor/js/wysiwyg/wysiwyg";
import * as OdooEditorLib from "@web_editor/js/editor/odoo-editor/src/OdooEditor";
import { patch } from "@web/core/utils/patch";

const closestElement = OdooEditorLib.closestElement;
const newmediaSelector = '.ri';
const OdooEditor = OdooEditorLib.OdooEditor;
const isProtected = OdooEditorLib.isProtected;

patch(Wysiwyg.prototype, {
    /**
     * @override
     */
    async startEdition() {
        await super.startEdition();
        this.$editable.on('dblclick', newmediaSelector, ev => {
            const targetEl = ev.currentTarget;
            let isEditable =
                // TODO that first check is probably useless/wrong: checking if
                // the media itself has editable content should not be relevant.
                // In fact the content of all media should be marked as non
                // editable anyway.
                targetEl.isContentEditable ||
                // For a media to be editable, the base case is to be in a
                // container whose content is editable.
                (targetEl.parentElement && targetEl.parentElement.isContentEditable);

            if (!isEditable && targetEl.classList.contains('o_editable_media')) {
                isEditable = weUtils.shouldEditableMediaBeEditable(targetEl);
            }

            if (isEditable) {
                this.showTooltip = false;

                if (!isProtected(this.odooEditor.document.getSelection().anchorNode)) {
                    if (this.options.onDblClickEditableMedia && targetEl.nodeName === 'IMG' && targetEl.src) {
                        this.options.onDblClickEditableMedia(ev);
                    } else {
                        this._onDblClickEditableMedia(ev);
                    }
                }
            }
        });
    }
});
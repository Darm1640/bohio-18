/** @odoo-module **/

import fonts from '@web_editor/js/wysiwyg/fonts';
/**
 * @override
 */
fonts.fontIcons = [
    {base: 'fa', parser: /\.(fa-(?:\w|-)+)::?before/i},
    {base: 'ri', parser: /\.(ri-(?:\w|-)+)::?before/i},
],

console.log()
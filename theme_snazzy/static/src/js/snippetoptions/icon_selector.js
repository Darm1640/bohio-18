/** @odoo-module */

import { MediaDialog } from '@web_editor/components/media_dialog/media_dialog';
import { patch } from "@web/core/utils/patch";
import { ImageSelector } from '@web_editor/components/media_dialog/image_selector';
import { DocumentSelector } from '@web_editor/components/media_dialog/document_selector';
import { IconSelector } from '@web_editor/components/media_dialog/icon_selector';
import { VideoSelector } from '@web_editor/components/media_dialog/video_selector';

export const TABS = {
    IMAGES: {
        id: 'IMAGES',
        title: "Images",
        Component: ImageSelector,
    },
    DOCUMENTS: {
        id: 'DOCUMENTS',
        title: "Documents",
        Component: DocumentSelector,
    },
    ICONS: {
        id: 'ICONS',
        title: "Icons",
        Component: IconSelector,
    },
    VIDEOS: {
        id: 'VIDEOS',
        title: "Videos",
        Component: VideoSelector,
    },
};

patch(MediaDialog.prototype, {
    async save() {
        if (this.errorMessages[this.state.activeTab]) {
            this.notificationService.add(this.errorMessages[this.state.activeTab], {
                type: 'danger',
            });
            return;
        }
        const selectedMedia = this.selectedMedia[this.state.activeTab];
        // TODO In master: clean the save method so it performs the specific
        // adaptation before saving from the active media selector and find a
        // way to simply close the dialog if the media element remains the same.
        const saveSelectedMedia = selectedMedia.length
            && (this.state.activeTab !== TABS.ICONS.id || selectedMedia[0].initialIconChanged || !this.props.media);
        if (saveSelectedMedia) {
            const elements = await TABS[this.state.activeTab].Component.createElements(selectedMedia, { rpc: this.rpc, orm: this.orm });
            elements.forEach(element => {
                if (this.props.media) {
                    element.classList.add(...this.props.media.classList);
                    const style = this.props.media.getAttribute('style');
                    if (style) {
                        element.setAttribute('style', style);
                    }
                    if (this.props.media.dataset.shape) {
                        element.dataset.shape = this.props.media.dataset.shape;
                    }
                    if (this.props.media.dataset.shapeColors) {
                        element.dataset.shapeColors = this.props.media.dataset.shapeColors;
                    }
                    if (this.props.media.dataset.shapeFlip) {
                        element.dataset.shapeFlip = this.props.media.dataset.shapeFlip;
                    }
                    if (this.props.media.dataset.shapeRotate) {
                        element.dataset.shapeRotate = this.props.media.dataset.shapeRotate;
                    }
                    if (this.props.media.dataset.hoverEffect) {
                        element.dataset.hoverEffect = this.props.media.dataset.hoverEffect;
                    }
                    if (this.props.media.dataset.hoverEffectColor) {
                        element.dataset.hoverEffectColor = this.props.media.dataset.hoverEffectColor;
                    }
                    if (this.props.media.dataset.hoverEffectStrokeWidth) {
                        element.dataset.hoverEffectStrokeWidth = this.props.media.dataset.hoverEffectStrokeWidth;
                    }
                    if (this.props.media.dataset.hoverEffectIntensity) {
                        element.dataset.hoverEffectIntensity = this.props.media.dataset.hoverEffectIntensity;
                    }
                }
                for (const otherTab of Object.keys(TABS).filter(key => key !== this.state.activeTab)) {
                    for (const property of TABS[otherTab].Component.mediaSpecificStyles) {
                        element.style.removeProperty(property);
                    }
                    element.classList.remove(...TABS[otherTab].Component.mediaSpecificClasses);
                    const extraClassesToRemove = [];
                    for (const name of TABS[otherTab].Component.mediaExtraClasses) {
                        if (typeof(name) === 'string') {
                            extraClassesToRemove.push(name);
                        } else { // Regex
                            for (const className of element.classList) {
                                if (className.match(name)) {
                                    extraClassesToRemove.push(className);
                                }
                            }
                        }
                    }
                    // Remove classes that do not also exist in the target type.
                    element.classList.remove(...extraClassesToRemove.filter(candidateName => {
                        for (const name of TABS[this.state.activeTab].Component.mediaExtraClasses) {
                            if (typeof(name) === 'string') {
                                if (candidateName === name) {
                                    return false;
                                }
                            } else { // Regex
                                for (const className of element.classList) {
                                    if (className.match(candidateName)) {
                                        return false;
                                    }
                                }
                            }
                        }
                        return true;
                    }));
                }
                element.classList.remove(...this.initialIconClasses);
                element.classList.remove('o_modified_image_to_save');
                element.classList.remove('oe_edited_link');
                element.classList.add(...TABS[this.state.activeTab].Component.mediaSpecificClasses);
                if (this.state.activeTab == 'ICONS') {

                    var selectediconbase = selectedMedia[0].fontBase

                    if (selectediconbase == "ri"){
                        element.classList.remove(...['fa'])
                    }
                    if (selectediconbase == "fa"){
                        element.classList.remove(...['ri'])
                    }
                }
            });
            if (this.props.multiImages) {
                this.props.save(elements);
            } else {
                this.props.save(elements[0]);
            }
        }
        this.props.close();
    }
});
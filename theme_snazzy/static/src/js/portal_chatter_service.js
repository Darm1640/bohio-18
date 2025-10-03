/** @odoo-module */

import { PortalChatter } from "@portal/chatter/frontend/portal_chatter";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { ChatterComposer } from "./chatter_composer";
import { ChatterMessageCounter } from "./chatter_message_counter";
import { ChatterMessages } from "./chatter_messages";
import { ChatterPager } from "./chatter_pager";
import { Component, markup, onWillStart, useState, onWillUpdateProps } from "@odoo/owl";
// Review Publish Date Formate

PortalChatter.extend({
    /**
     * @override
     */
    preprocessMessages(messages) {
        messages.forEach((m) => {
            m['body'] = markup(m.body);
        });
        return messages;
    },
});

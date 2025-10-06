# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
import base64


class BohioPortalController(http.Controller):
    """Controlador para portal de clientes - Bohío Real Estate"""

    @http.route('/my/opportunities', type='http', auth='user', website=True)
    def portal_my_opportunities(self, **kw):
        partner = request.env.user.partner_id

        opportunities = request.env['crm.lead'].search([
            ('partner_id', '=', partner.id),
            ('show_in_portal', '=', True),
            ('type', '=', 'opportunity')
        ], order='create_date desc')

        return request.render('bohio_real_estate.portal_my_opportunities', {
            'opportunities': opportunities,
            'page_name': 'opportunities',
        })

    @http.route('/my/opportunity/<int:opportunity_id>', type='http', auth='user', website=True)
    def portal_opportunity_detail(self, opportunity_id, **kw):
        opportunity = request.env['crm.lead'].search([
            ('id', '=', opportunity_id),
            ('partner_id', '=', request.env.user.partner_id.id),
            ('show_in_portal', '=', True)
        ], limit=1)

        if not opportunity:
            return request.redirect('/my/opportunities')

        return request.render('bohio_real_estate.portal_opportunity_detail', {
            'opportunity': opportunity,
            'page_name': 'opportunity_detail',
        })

    @http.route('/my/properties', type='http', auth='user', website=True)
    def portal_my_properties(self, **kw):
        partner = request.env.user.partner_id

        properties = request.env['product.template'].sudo().search([
            ('is_property', '=', True),
            '|',
            ('partner_id', '=', partner.id),
            ('owners_lines.partner_id', '=', partner.id)
        ], order='create_date desc')

        contracts = request.env['property.contract'].search([
            ('partner_id', '=', partner.id),
            ('state', '!=', 'cancel')
        ], order='date_from desc')

        tenant_properties = contracts.mapped('property_id')

        return request.render('bohio_real_estate.portal_my_properties', {
            'properties': properties,
            'tenant_properties': tenant_properties,
            'page_name': 'my_properties',
        })

    @http.route('/my/contracts', type='http', auth='user', website=True)
    def portal_my_contracts(self, **kw):
        partner = request.env.user.partner_id

        contracts = request.env['property.contract'].search([
            ('partner_id', '=', partner.id)
        ], order='date_from desc')

        return request.render('bohio_real_estate.portal_my_contracts', {
            'contracts': contracts,
            'page_name': 'contracts',
        })

    @http.route('/my/contract/<int:contract_id>', type='http', auth='user', website=True)
    def portal_contract_detail(self, contract_id, **kw):
        contract = request.env['property.contract'].search([
            ('id', '=', contract_id),
            ('partner_id', '=', request.env.user.partner_id.id)
        ], limit=1)

        if not contract:
            return request.redirect('/my/contracts')

        return request.render('bohio_real_estate.portal_contract_detail', {
            'contract': contract,
            'page_name': 'contract_detail',
        })

    @http.route('/my/payments', type='http', auth='user', website=True)
    def portal_my_payments(self, **kw):
        partner = request.env.user.partner_id

        payments = request.env['recaudo.news.payment'].search([
            ('partner_id', '=', partner.id)
        ], order='create_date desc')

        return request.render('bohio_real_estate.portal_my_payments', {
            'payments': payments,
            'page_name': 'payments',
        })

    @http.route('/my/tickets', type='http', auth='user', website=True)
    def portal_my_tickets(self, page=1, **kw):
        partner = request.env.user.partner_id
        Ticket = request.env['helpdesk.ticket']

        ticket_count = Ticket.search_count([
            ('partner_id', '=', partner.id)
        ])

        pager = portal_pager(
            url='/my/tickets',
            total=ticket_count,
            page=page,
            step=10
        )

        tickets = Ticket.search([
            ('partner_id', '=', partner.id)
        ], order='create_date desc', limit=10, offset=pager['offset'])

        return request.render('bohio_real_estate.portal_my_tickets', {
            'tickets': tickets,
            'page_name': 'tickets',
            'pager': pager,
        })

    @http.route('/my/ticket/<int:ticket_id>', type='http', auth='user', website=True)
    def portal_ticket_detail(self, ticket_id, **kw):
        ticket = request.env['helpdesk.ticket'].search([
            ('id', '=', ticket_id),
            ('partner_id', '=', request.env.user.partner_id.id)
        ], limit=1)

        if not ticket:
            return request.redirect('/my/tickets')

        return request.render('bohio_real_estate.portal_ticket_detail', {
            'ticket': ticket,
            'page_name': 'ticket_detail',
        })

    @http.route('/my/ticket/<int:ticket_id>/add_message', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def portal_ticket_add_message(self, ticket_id, **post):
        ticket = request.env['helpdesk.ticket'].search([
            ('id', '=', ticket_id),
            ('partner_id', '=', request.env.user.partner_id.id)
        ], limit=1)

        if not ticket:
            return request.redirect('/my/tickets')

        message = post.get('message', '').strip()

        if message:
            ticket.message_post(
                body=message,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                author_id=request.env.user.partner_id.id
            )

        if post.get('attachment'):
            attachment_file = post.get('attachment')
            attachment_vals = {
                'name': attachment_file.filename,
                'datas': base64.b64encode(attachment_file.read()),
                'res_model': 'helpdesk.ticket',
                'res_id': ticket.id,
            }
            request.env['ir.attachment'].sudo().create(attachment_vals)

        return request.redirect(f'/my/ticket/{ticket_id}')

    @http.route('/my', type='http', auth='user', website=True)
    def portal_my_home(self, **kw):
        partner = request.env.user.partner_id

        properties_count = request.env['product.template'].sudo().search_count([
            ('is_property', '=', True),
            '|',
            ('partner_id', '=', partner.id),
            ('owners_lines.partner_id', '=', partner.id)
        ])

        contracts_count = request.env['property.contract'].search_count([
            ('partner_id', '=', partner.id),
            ('state', '!=', 'cancel')
        ])

        tickets_count = request.env['helpdesk.ticket'].search_count([
            ('partner_id', '=', partner.id)
        ])

        opportunities_count = request.env['crm.lead'].search_count([
            ('partner_id', '=', partner.id),
            ('type', '=', 'opportunity'),
            ('show_in_portal', '=', True)
        ])

        return request.render('bohio_real_estate.portal_my_home', {
            'properties_count': properties_count,
            'contracts_count': contracts_count,
            'tickets_count': tickets_count,
            'opportunities_count': opportunities_count,
            'page_name': 'home',
        })

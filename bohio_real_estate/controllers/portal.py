from odoo import http, fields
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
import base64
import logging

_logger = logging.getLogger(__name__)


class BohioPortal(CustomerPortal):
    """
    Portal personalizado BOHIO dividido por roles:
    - Propietario: puede tener múltiples propiedades
    - Arrendatario: es inquilino de propiedades
    - Ambos: tiene propiedades Y es inquilino de otras
    """

    def _get_user_role(self, partner):
        """
        Determina el rol del usuario en el portal
        Returns: dict con is_owner, is_tenant, properties_count, tenant_contracts_count
        """
        # Verificar si es propietario
        owned_properties = request.env['product.template'].sudo().search([
            ('is_property', '=', True),
            '|',
            ('partner_id', '=', partner.id),
            ('owners_lines.partner_id', '=', partner.id)
        ])

        _logger.info(f"Portal Owner Debug - Partner ID: {partner.id}, Partner Name: {partner.name}")
        _logger.info(f"Portal Owner Debug - Properties found: {len(owned_properties)}")
        _logger.info(f"Portal Owner Debug - Property IDs: {owned_properties.ids}")

        # Verificar total de propiedades en el sistema
        total_properties = request.env['product.template'].sudo().search_count([('is_property', '=', True)])
        _logger.info(f"Portal Owner Debug - Total properties in system: {total_properties}")

        # Verificar si es arrendatario
        tenant_contracts = request.env['property.contract'].search([
            ('partner_id', '=', partner.id),
            ('contract_type', '=', 'is_rental'),
            ('state', 'not in', ['draft', 'cancel'])
        ])

        return {
            'is_owner': len(owned_properties) > 0,
            'is_tenant': len(tenant_contracts) > 0,
            'properties_count': len(owned_properties),
            'tenant_contracts_count': len(tenant_contracts),
            'owned_properties': owned_properties,
            'tenant_contracts': tenant_contracts,
        }

    @http.route('/mybohio', type='http', auth='user', website=True)
    def mybohio_home(self, **kw):
        """Dashboard principal - redirige según rol"""
        partner = request.env.user.partner_id
        role_info = self._get_user_role(partner)

        # Si solo es arrendatario, mostrar dashboard de arrendatario
        if role_info['is_tenant'] and not role_info['is_owner']:
            return self.mybohio_tenant_dashboard(**kw)

        # Si es propietario (solo o con propiedades arrendadas), mostrar dashboard de propietario
        if role_info['is_owner']:
            return self.mybohio_owner_dashboard(**kw)

        # Si no tiene ningún rol, mostrar página básica
        return request.render('bohio_real_estate.mybohio_no_role', {
            'page_name': 'mybohio_home',
            'partner': partner,
        })

    # =================== SECCIÓN PROPIETARIOS ===================

    @http.route('/mybohio/owner', type='http', auth='user', website=True)
    def mybohio_owner_dashboard(self, **kw):
        """Dashboard para propietarios"""
        partner = request.env.user.partner_id
        role_info = self._get_user_role(partner)

        if not role_info['is_owner']:
            return request.redirect('/mybohio')

        properties = role_info['owned_properties']

        # Contratos donde el usuario es el propietario
        owner_contracts = request.env['property.contract'].sudo().search([
            ('property_id', 'in', properties.ids),
            ('contract_type', '=', 'is_rental'),
            ('state', 'not in', ['draft', 'cancel'])
        ])

        metrics = self._calculate_owner_metrics(partner, properties, owner_contracts)

        # Préstamos del propietario (si el módulo está instalado)
        loans = False
        if 'account.loan' in request.env:
            loans = request.env['account.loan'].sudo().search([
                ('partner_id', '=', partner.id)
            ])

        # Oportunidades visibles en portal (solo nombre y etapa)
        opportunities = request.env['crm.lead'].search([
            ('partner_id', '=', partner.id),
            ('type', '=', 'opportunity'),
            ('show_in_portal', '=', True)
        ], limit=5, order='create_date desc')

        has_credit_limit = partner.credit_limit > 0

        values = {
            'page_name': 'mybohio_owner',
            'role_info': role_info,
            'properties': properties,
            'contracts': owner_contracts,
            'metrics': metrics,
            'loans': loans,
            'opportunities': opportunities,
            'has_credit_limit': has_credit_limit,
            'partner': partner,
        }

        return request.render('bohio_real_estate.mybohio_owner_dashboard', values)

    def _calculate_owner_metrics(self, partner, properties, contracts):
        """Métricas financieras para propietarios"""
        today = datetime.today()
        first_day_month = today.replace(day=1)
        last_day_month = (first_day_month + relativedelta(months=1)) - timedelta(days=1)

        active_contracts = contracts.filtered(lambda c: c.state in ['confirmed', 'renew'])
        occupied_properties = active_contracts.mapped('property_id')
        total_properties = len(properties)
        occupied_count = len(occupied_properties)

        occupancy_rate = (occupied_count / total_properties * 100) if total_properties > 0 else 0

        # Ingresos mensuales esperados (suma de todas las rentas)
        monthly_income = sum(contract.rent or 0 for contract in active_contracts)

        # Pagos recibidos este mes (propios del partner + de contratos)
        Payment = request.env['account.payment'].sudo()

        # Pagos directos al propietario
        owner_payments_month = Payment.search([
            ('partner_id', '=', partner.id),
            ('date', '>=', first_day_month),
            ('date', '<=', last_day_month),
            ('state', '=', 'posted'),
            ('payment_type', '=', 'inbound')
        ])

        # Pagos de arrendatarios (contratos)
        tenant_payments_month = Payment.search([
            ('contract_id', 'in', active_contracts.ids),
            ('date', '>=', first_day_month),
            ('date', '<=', last_day_month),
            ('state', '=', 'posted'),
            ('payment_type', '=', 'inbound')
        ])

        all_payments_month = owner_payments_month | tenant_payments_month
        income_received = sum(all_payments_month.mapped('amount'))

        # Pagos pendientes (facturas sin pagar)
        pending_invoices = request.env['account.move'].sudo().search([
            '|',
            ('partner_id', '=', partner.id),
            ('contract_id', 'in', active_contracts.ids),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial'])
        ])
        pending_amount = sum(pending_invoices.mapped('amount_residual'))

        # Facturas de comisiones
        invoices = request.env['account.move'].sudo().search([
            ('partner_id', '=', partner.id),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('destinatario', '=', 'propietario')
        ])
        commission_total = sum(invoices.mapped('amount_total'))

        # Ingresos por tipo de propiedad
        income_by_type = {}
        for contract in active_contracts:
            prop = contract.property_id
            if prop and prop.property_type_id:
                type_name = prop.property_type_id.name
                if type_name not in income_by_type:
                    income_by_type[type_name] = {
                        'count': 0,
                        'total_income': 0.0
                    }
                income_by_type[type_name]['count'] += 1
                income_by_type[type_name]['total_income'] += contract.rent or 0

        # Promedio de pagos
        avg_payment = income_received / len(all_payments_month) if len(all_payments_month) > 0 else 0

        return {
            'total_properties': total_properties,
            'occupied_properties': occupied_count,
            'vacant_properties': total_properties - occupied_count,
            'occupancy_rate': round(occupancy_rate, 2),
            'monthly_income': monthly_income,
            'income_received': income_received,
            'pending_amount': pending_amount,
            'active_contracts': len(active_contracts),
            'commission_total': commission_total,
            'payments_this_month': len(all_payments_month),
            'income_by_type': income_by_type,
            'avg_payment': avg_payment,
        }

    @http.route('/mybohio/owner/properties', type='http', auth='user', website=True)
    def mybohio_owner_properties(self, **kw):
        """Lista de propiedades del propietario"""
        partner = request.env.user.partner_id
        role_info = self._get_user_role(partner)

        if not role_info['is_owner']:
            return request.redirect('/mybohio')

        properties = role_info['owned_properties']
        managed_by_bohio = properties.filtered(lambda p: p.managed_by_bohio)

        values = {
            'page_name': 'mybohio_owner_properties',
            'role_info': role_info,
            'properties': properties,
            'managed_by_bohio': managed_by_bohio,
        }

        return request.render('bohio_real_estate.mybohio_owner_properties', values)

    @http.route('/mybohio/owner/property/<int:property_id>', type='http', auth='user', website=True)
    def mybohio_owner_property_detail(self, property_id, **kw):
        """Detalle de propiedad del propietario"""
        partner = request.env.user.partner_id

        prop = request.env['product.template'].sudo().search([
            ('id', '=', property_id),
            ('is_property', '=', True),
            '|',
            ('partner_id', '=', partner.id),
            ('owners_lines.partner_id', '=', partner.id)
        ], limit=1)

        if not prop:
            return request.redirect('/mybohio/owner/properties')

        can_edit = not prop.managed_by_bohio

        contract = request.env['property.contract'].sudo().search([
            ('property_id', '=', prop.id),
            ('contract_type', '=', 'is_rental'),
            ('state', 'in', ['confirmed', 'renew'])
        ], limit=1)

        # Pagos recibidos de esta propiedad (del contrato)
        payments = request.env['account.payment'].sudo().search([
            ('contract_id', '=', contract.id),
            ('payment_type', '=', 'inbound'),
            ('state', '=', 'posted')
        ], order='date desc', limit=20) if contract else []

        role_info = self._get_user_role(partner)

        values = {
            'page_name': 'mybohio_owner_property_detail',
            'role_info': role_info,
            'property': prop,
            'can_edit': can_edit,
            'contract': contract,
            'payments': payments,
        }

        return request.render('bohio_real_estate.mybohio_owner_property_detail', values)

    @http.route('/mybohio/owner/property/<int:property_id>/update', type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def mybohio_owner_property_update(self, property_id, **post):
        """Actualiza características de la propiedad desde el portal"""
        partner = request.env.user.partner_id

        # Verificar que la propiedad pertenece al usuario
        prop = request.env['product.template'].sudo().search([
            ('id', '=', property_id),
            ('is_property', '=', True),
            '|',
            ('partner_id', '=', partner.id),
            ('owners_lines.partner_id', '=', partner.id)
        ], limit=1)

        if not prop:
            return request.redirect('/mybohio/owner/properties')

        # Verificar que NO esté administrada por BOHIO
        if prop.managed_by_bohio:
            request.session['error_message'] = 'No puede editar una propiedad administrada por BOHIO'
            return request.redirect(f'/mybohio/owner/property/{property_id}')

        try:
            # Campos permitidos para editar desde portal
            allowed_fields = {
                'property_description': str,
                'property_internal_notes': str,
                'property_highlight_text': str,
                'property_alarm_code': str,
                'property_admin_percentage': float,
                'parking_spaces': int,
                'property_stratum': int,
            }

            # Actualizar solo campos permitidos
            vals = {}
            for field, field_type in allowed_fields.items():
                if field in post and post.get(field):
                    try:
                        if field_type == float:
                            vals[field] = float(post[field])
                        elif field_type == int:
                            vals[field] = int(post[field])
                        else:
                            vals[field] = post[field]
                    except (ValueError, TypeError):
                        continue

            if vals:
                prop.sudo().write(vals)
                request.session['success_message'] = 'Propiedad actualizada exitosamente'
            else:
                request.session['info_message'] = 'No se realizaron cambios'

        except Exception as e:
            request.session['error_message'] = f'Error al actualizar: {str(e)}'

        return request.redirect(f'/mybohio/owner/property/{property_id}')
    @http.route('/mybohio/owner/payments', type='http', auth='user', website=True)
    def mybohio_owner_payments(self, page=1, **kw):
        """Pagos recibidos: propios del tercero + de arrendatarios"""
        partner = request.env.user.partner_id
        role_info = self._get_user_role(partner)

        if not role_info['is_owner']:
            return request.redirect('/mybohio')

        properties = role_info['owned_properties']
        contracts = request.env['property.contract'].sudo().search([
            ('property_id', 'in', properties.ids),
            ('contract_type', '=', 'is_rental')
        ])

        Payment = request.env['account.payment'].sudo()

        # Pagos directos al propietario (tercero)
        owner_payments = Payment.search([
            ('partner_id', '=', partner.id),
            ('payment_type', '=', 'inbound'),
            ('state', '=', 'posted')
        ])

        # Pagos de arrendatarios (contratos)
        tenant_payments = Payment.search([
            ('contract_id', 'in', contracts.ids),
            ('payment_type', '=', 'inbound'),
            ('state', '=', 'posted')
        ])

        all_payments = owner_payments | tenant_payments
        payment_count = len(all_payments)

        pager = portal_pager(
            url='/mybohio/owner/payments',
            total=payment_count,
            page=page,
            step=20
        )

        # Ordenar y paginar
        payments_sorted = all_payments.sorted(key=lambda p: p.date, reverse=True)
        offset = pager['offset']
        payments = payments_sorted[offset:offset + 20]

        values = {
            'page_name': 'mybohio_owner_payments',
            'role_info': role_info,
            'payments': payments,
            'pager': pager,
        }

        return request.render('bohio_real_estate.mybohio_owner_payments', values)

    @http.route('/mybohio/owner/invoices', type='http', auth='user', website=True)
    def mybohio_owner_invoices(self, page=1, **kw):
        """Facturas del propietario (comisiones, etc)"""
        partner = request.env.user.partner_id
        role_info = self._get_user_role(partner)

        if not role_info['is_owner']:
            return request.redirect('/mybohio')

        Invoice = request.env['account.move'].sudo()

        invoice_count = Invoice.search_count([
            ('partner_id', '=', partner.id),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('destinatario', '=', 'propietario')
        ])

        pager = portal_pager(
            url='/mybohio/owner/invoices',
            total=invoice_count,
            page=page,
            step=20
        )

        invoices = Invoice.search([
            ('partner_id', '=', partner.id),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('destinatario', '=', 'propietario')
        ], order='invoice_date desc', limit=20, offset=pager['offset'])

        values = {
            'page_name': 'mybohio_owner_invoices',
            'role_info': role_info,
            'invoices': invoices,
            'pager': pager,
        }

        return request.render('bohio_real_estate.mybohio_owner_invoices', values)

    @http.route('/mybohio/owner/opportunities', type='http', auth='user', website=True)
    def mybohio_owner_opportunities(self, page=1, **kw):
        """Oportunidades CRM del propietario"""
        partner = request.env.user.partner_id
        role_info = self._get_user_role(partner)

        if not role_info['is_owner']:
            return request.redirect('/mybohio')

        Opportunity = request.env['crm.lead']

        opp_count = Opportunity.search_count([
            ('partner_id', '=', partner.id),
            ('type', '=', 'opportunity'),
            ('show_in_portal', '=', True)
        ])

        pager = portal_pager(
            url='/mybohio/owner/opportunities',
            total=opp_count,
            page=page,
            step=10
        )

        opportunities = Opportunity.search([
            ('partner_id', '=', partner.id),
            ('type', '=', 'opportunity'),
            ('show_in_portal', '=', True)
        ], order='create_date desc', limit=10, offset=pager['offset'])

        values = {
            'page_name': 'mybohio_owner_opportunities',
            'role_info': role_info,
            'opportunities': opportunities,
            'pager': pager,
        }

        return request.render('bohio_real_estate.mybohio_owner_opportunities', values)

    @http.route('/mybohio/owner/opportunity/<int:opportunity_id>', type='http', auth='user', website=True)
    def mybohio_owner_opportunity_detail(self, opportunity_id, **kw):
        """Detalle de oportunidad (solo nombre y etapa, sin datos sensibles)"""
        partner = request.env.user.partner_id
        role_info = self._get_user_role(partner)

        opportunity = request.env['crm.lead'].search([
            ('id', '=', opportunity_id),
            ('partner_id', '=', partner.id),
            ('type', '=', 'opportunity'),
            ('show_in_portal', '=', True)
        ], limit=1)

        if not opportunity:
            return request.redirect('/mybohio/owner/opportunities')

        values = {
            'page_name': 'mybohio_owner_opportunity_detail',
            'role_info': role_info,
            'opportunity': opportunity,
        }

        return request.render('bohio_real_estate.mybohio_owner_opportunity_detail', values)

    @http.route('/mybohio/owner/tickets', type='http', auth='user', website=True)
    def mybohio_owner_tickets(self, page=1, **kw):
        """PQRS del propietario"""
        partner = request.env.user.partner_id
        role_info = self._get_user_role(partner)

        if not role_info['is_owner']:
            return request.redirect('/mybohio')

        Ticket = request.env['helpdesk.ticket']

        ticket_count = Ticket.search_count([
            ('partner_id', '=', partner.id)
        ])

        pager = portal_pager(
            url='/mybohio/owner/tickets',
            total=ticket_count,
            page=page,
            step=10
        )

        tickets = Ticket.search([
            ('partner_id', '=', partner.id)
        ], order='create_date desc', limit=10, offset=pager['offset'])

        values = {
            'page_name': 'mybohio_owner_tickets',
            'role_info': role_info,
            'tickets': tickets,
            'pager': pager,
        }

        return request.render('bohio_real_estate.mybohio_owner_tickets', values)

    @http.route('/mybohio/owner/ticket/<int:ticket_id>', type='http', auth='user', website=True)
    def mybohio_owner_ticket_detail(self, ticket_id, **kw):
        """Detalle PQRS del propietario"""
        partner = request.env.user.partner_id
        role_info = self._get_user_role(partner)

        ticket = request.env['helpdesk.ticket'].search([
            ('id', '=', ticket_id),
            ('partner_id', '=', partner.id)
        ], limit=1)

        if not ticket:
            return request.redirect('/mybohio/owner/tickets')

        values = {
            'page_name': 'mybohio_owner_ticket_detail',
            'role_info': role_info,
            'ticket': ticket,
        }

        return request.render('bohio_real_estate.mybohio_owner_ticket_detail', values)

    @http.route('/mybohio/owner/documents', type='http', auth='user', website=True)
    def mybohio_owner_documents(self, **kw):
        """Documentos del propietario"""
        partner = request.env.user.partner_id
        role_info = self._get_user_role(partner)

        if not role_info['is_owner']:
            return request.redirect('/mybohio')

        properties = role_info['owned_properties']

        # Documentos de las propiedades
        property_documents = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'product.template'),
            ('res_id', 'in', properties.ids),
            ('is_property_document', '=', True)
        ], order='create_date desc')

        # Documentos de contratos
        contracts = request.env['property.contract'].sudo().search([
            ('property_id', 'in', properties.ids)
        ])
        contract_documents = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'property.contract'),
            ('res_id', 'in', contracts.ids),
            ('is_property_document', '=', True)
        ], order='create_date desc')

        values = {
            'page_name': 'mybohio_owner_documents',
            'role_info': role_info,
            'property_documents': property_documents,
            'contract_documents': contract_documents,
        }

        return request.render('bohio_real_estate.mybohio_owner_documents', values)

    # =================== SECCIÓN ARRENDATARIOS ===================

    @http.route('/mybohio/tenant', type='http', auth='user', website=True)
    def mybohio_tenant_dashboard(self, **kw):
        """Dashboard para arrendatarios"""
        partner = request.env.user.partner_id
        role_info = self._get_user_role(partner)

        if not role_info['is_tenant']:
            return request.redirect('/mybohio')

        contracts = role_info['tenant_contracts']
        active_contracts = contracts.filtered(lambda c: c.state in ['confirmed', 'renew'])

        metrics = self._calculate_tenant_metrics(partner, contracts)

        # Facturas del arrendatario
        invoices = request.env['account.move'].sudo().search([
            ('partner_id', '=', partner.id),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('destinatario', '=', 'arrendatario')
        ], limit=5, order='invoice_date desc')

        tickets = request.env['helpdesk.ticket'].search([
            ('partner_id', '=', partner.id)
        ], limit=5, order='create_date desc')

        values = {
            'page_name': 'mybohio_tenant',
            'role_info': role_info,
            'contracts': active_contracts,
            'metrics': metrics,
            'invoices': invoices,
            'tickets': tickets,
            'partner': partner,
        }

        return request.render('bohio_real_estate.mybohio_tenant_dashboard', values)

    def _calculate_tenant_metrics(self, partner, contracts):
        """Métricas financieras para arrendatarios"""
        today = datetime.today()
        first_day_month = today.replace(day=1)
        last_day_month = (first_day_month + relativedelta(months=1)) - timedelta(days=1)

        active_contracts = contracts.filtered(lambda c: c.state in ['confirmed', 'renew'])

        # Pagos mensuales totales
        monthly_rent = sum(contract.rent or 0 for contract in active_contracts)

        # Pagos realizados este mes
        Payment = request.env['account.payment'].sudo()

        payments_this_month = Payment.search([
            ('partner_id', '=', partner.id),
            ('date', '>=', first_day_month),
            ('date', '<=', last_day_month),
            ('state', '=', 'posted'),
            ('payment_type', '=', 'outbound')
        ])
        paid_this_month = sum(payments_this_month.mapped('amount'))

        # Facturas pendientes (sin pagar completamente)
        pending_invoices = request.env['account.move'].sudo().search([
            ('partner_id', '=', partner.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('destinatario', '=', 'arrendatario')
        ])
        pending_amount = sum(pending_invoices.mapped('amount_residual'))
        invoices_pending = pending_amount

        return {
            'active_contracts': len(active_contracts),
            'monthly_rent': monthly_rent,
            'paid_this_month': paid_this_month,
            'pending_amount': pending_amount,
            'invoices_pending': invoices_pending,
            'payments_this_month': len(payments_this_month),
        }

    @http.route('/mybohio/tenant/contracts', type='http', auth='user', website=True)
    def mybohio_tenant_contracts(self, **kw):
        """Contratos del arrendatario"""
        partner = request.env.user.partner_id
        role_info = self._get_user_role(partner)

        if not role_info['is_tenant']:
            return request.redirect('/mybohio')

        active_contracts = role_info['tenant_contracts'].filtered(
            lambda c: c.state in ['confirmed', 'renew']
        )

        historical_contracts = role_info['tenant_contracts'].filtered(
            lambda c: c.state not in ['confirmed', 'renew', 'draft']
        )

        values = {
            'page_name': 'mybohio_tenant_contracts',
            'role_info': role_info,
            'active_contracts': active_contracts,
            'historical_contracts': historical_contracts,
        }

        return request.render('bohio_real_estate.mybohio_tenant_contracts', values)

    @http.route('/mybohio/tenant/contract/<int:contract_id>', type='http', auth='user', website=True)
    def mybohio_tenant_contract_detail(self, contract_id, **kw):
        """Detalle del contrato (arrendatario)"""
        partner = request.env.user.partner_id

        contract = request.env['property.contract'].search([
            ('id', '=', contract_id),
            ('partner_id', '=', partner.id),
            ('contract_type', '=', 'is_rental')
        ], limit=1)

        if not contract:
            return request.redirect('/mybohio/tenant/contracts')

        # Pagos del contrato
        payments = request.env['account.payment'].sudo().search([
            ('contract_id', '=', contract.id),
            ('partner_id', '=', partner.id),
            ('state', '=', 'posted')
        ], order='date desc')

        total_paid = sum(payments.filtered(lambda p: p.payment_type == 'outbound').mapped('amount'))

        # Facturas pendientes del contrato
        pending_invoices = request.env['account.move'].sudo().search([
            ('partner_id', '=', partner.id),
            ('contract_id', '=', contract.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial'])
        ])
        total_pending = sum(pending_invoices.mapped('amount_residual'))

        role_info = self._get_user_role(partner)

        values = {
            'page_name': 'mybohio_tenant_contract_detail',
            'role_info': role_info,
            'contract': contract,
            'payments': payments,
            'total_paid': total_paid,
            'total_pending': total_pending,
        }

        return request.render('bohio_real_estate.mybohio_tenant_contract_detail', values)

    @http.route('/mybohio/tenant/payments', type='http', auth='user', website=True)
    def mybohio_tenant_payments(self, page=1, **kw):
        """Pagos realizados (como arrendatario)"""
        partner = request.env.user.partner_id
        role_info = self._get_user_role(partner)

        if not role_info['is_tenant']:
            return request.redirect('/mybohio')

        Payment = request.env['account.payment'].sudo()

        # Pagos realizados por el arrendatario
        payment_count = Payment.search_count([
            ('partner_id', '=', partner.id),
            ('payment_type', '=', 'outbound'),
            ('state', '=', 'posted')
        ])

        pager = portal_pager(
            url='/mybohio/tenant/payments',
            total=payment_count,
            page=page,
            step=20
        )

        payments = Payment.search([
            ('partner_id', '=', partner.id),
            ('payment_type', '=', 'outbound'),
            ('state', '=', 'posted')
        ], order='date desc', limit=20, offset=pager['offset'])

        values = {
            'page_name': 'mybohio_tenant_payments',
            'role_info': role_info,
            'payments': payments,
            'pager': pager,
        }

        return request.render('bohio_real_estate.mybohio_tenant_payments', values)

    @http.route('/mybohio/tenant/invoices', type='http', auth='user', website=True)
    def mybohio_tenant_invoices(self, page=1, **kw):
        """Facturas del arrendatario"""
        partner = request.env.user.partner_id
        role_info = self._get_user_role(partner)

        if not role_info['is_tenant']:
            return request.redirect('/mybohio')

        Invoice = request.env['account.move'].sudo()

        invoice_count = Invoice.search_count([
            ('partner_id', '=', partner.id),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('destinatario', '=', 'arrendatario')
        ])

        pager = portal_pager(
            url='/mybohio/tenant/invoices',
            total=invoice_count,
            page=page,
            step=20
        )

        invoices = Invoice.search([
            ('partner_id', '=', partner.id),
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('destinatario', '=', 'arrendatario')
        ], order='invoice_date desc', limit=20, offset=pager['offset'])

        values = {
            'page_name': 'mybohio_tenant_invoices',
            'role_info': role_info,
            'invoices': invoices,
            'pager': pager,
        }

        return request.render('bohio_real_estate.mybohio_tenant_invoices', values)

    @http.route('/mybohio/tenant/tickets', type='http', auth='user', website=True)
    def mybohio_tenant_tickets(self, page=1, **kw):
        """PQRS del arrendatario"""
        partner = request.env.user.partner_id
        role_info = self._get_user_role(partner)

        if not role_info['is_tenant']:
            return request.redirect('/mybohio')

        Ticket = request.env['helpdesk.ticket']

        ticket_count = Ticket.search_count([
            ('partner_id', '=', partner.id)
        ])

        pager = portal_pager(
            url='/mybohio/tenant/tickets',
            total=ticket_count,
            page=page,
            step=10
        )

        tickets = Ticket.search([
            ('partner_id', '=', partner.id)
        ], order='create_date desc', limit=10, offset=pager['offset'])

        values = {
            'page_name': 'mybohio_tenant_tickets',
            'role_info': role_info,
            'tickets': tickets,
            'pager': pager,
        }

        return request.render('bohio_real_estate.mybohio_tenant_tickets', values)

    @http.route('/mybohio/tenant/ticket/<int:ticket_id>', type='http', auth='user', website=True)
    def mybohio_tenant_ticket_detail(self, ticket_id, **kw):
        """Detalle PQRS del arrendatario"""
        partner = request.env.user.partner_id
        role_info = self._get_user_role(partner)

        ticket = request.env['helpdesk.ticket'].search([
            ('id', '=', ticket_id),
            ('partner_id', '=', partner.id)
        ], limit=1)

        if not ticket:
            return request.redirect('/mybohio/tenant/tickets')

        values = {
            'page_name': 'mybohio_tenant_ticket_detail',
            'role_info': role_info,
            'ticket': ticket,
        }

        return request.render('bohio_real_estate.mybohio_tenant_ticket_detail', values)

    @http.route('/mybohio/tenant/documents', type='http', auth='user', website=True)
    def mybohio_tenant_documents(self, **kw):
        """Documentos del arrendatario"""
        partner = request.env.user.partner_id
        role_info = self._get_user_role(partner)

        if not role_info['is_tenant']:
            return request.redirect('/mybohio')

        contracts = role_info['tenant_contracts']

        # Documentos de contratos del arrendatario
        contract_documents = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'property.contract'),
            ('res_id', 'in', contracts.ids),
            ('is_property_document', '=', True)
        ], order='create_date desc')

        values = {
            'page_name': 'mybohio_tenant_documents',
            'role_info': role_info,
            'contract_documents': contract_documents,
        }

        return request.render('bohio_real_estate.mybohio_tenant_documents', values)

    # =================== SECCIÓN COMÚN ===================

    @http.route('/mybohio/tickets', type='http', auth='user', website=True)
    def mybohio_tickets(self, page=1, **kw):
        """PQRS/Tickets (común para ambos roles)"""
        partner = request.env.user.partner_id
        role_info = self._get_user_role(partner)

        Ticket = request.env['helpdesk.ticket']

        ticket_count = Ticket.search_count([
            ('partner_id', '=', partner.id)
        ])

        pager = portal_pager(
            url='/mybohio/tickets',
            total=ticket_count,
            page=page,
            step=10
        )

        tickets = Ticket.search([
            ('partner_id', '=', partner.id)
        ], order='create_date desc', limit=10, offset=pager['offset'])

        values = {
            'page_name': 'mybohio_tickets',
            'role_info': role_info,
            'tickets': tickets,
            'pager': pager,
        }

        return request.render('bohio_real_estate.mybohio_tickets', values)

    @http.route('/mybohio/ticket/<int:ticket_id>', type='http', auth='user', website=True)
    def mybohio_ticket_detail(self, ticket_id, **kw):
        """Detalle de ticket"""
        partner = request.env.user.partner_id
        role_info = self._get_user_role(partner)

        ticket = request.env['helpdesk.ticket'].search([
            ('id', '=', ticket_id),
            ('partner_id', '=', partner.id)
        ], limit=1)

        if not ticket:
            return request.redirect('/mybohio/tickets')

        values = {
            'page_name': 'mybohio_ticket_detail',
            'role_info': role_info,
            'ticket': ticket,
        }

        return request.render('bohio_real_estate.mybohio_ticket_detail', values)

    @http.route('/mybohio/ticket/<int:ticket_id>/message', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def mybohio_ticket_add_message(self, ticket_id, **post):
        """Agregar mensaje o archivo a ticket"""
        partner = request.env.user.partner_id

        ticket = request.env['helpdesk.ticket'].search([
            ('id', '=', ticket_id),
            ('partner_id', '=', partner.id)
        ], limit=1)

        if not ticket:
            return request.redirect('/mybohio/tickets')

        message = post.get('message', '').strip()

        if message:
            ticket.message_post(
                body=message,
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
                author_id=partner.id
            )

        if post.get('attachment'):
            attachment_file = post.get('attachment')
            attachment = request.env['ir.attachment'].sudo().create({
                'name': attachment_file.filename,
                'datas': base64.b64encode(attachment_file.read()),
                'res_model': 'helpdesk.ticket',
                'res_id': ticket.id,
            })

            ticket.message_post(
                body=f'Archivo adjunto: {attachment_file.filename}',
                message_type='notification',
                attachment_ids=[attachment.id]
            )

        return request.redirect(f'/mybohio/ticket/{ticket_id}')

    @http.route('/mybohio/create_ticket', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def mybohio_create_ticket(self, **post):
        """Crear nuevo ticket PQRS desde portal"""
        partner = request.env.user.partner_id

        pqrs_type = post.get('pqrs_type', 'petition')
        subject = post.get('subject', '')
        message = post.get('message', '')

        if not subject or not message:
            return request.redirect('/mybohio?error=missing_fields')

        pqrs_type_labels = {
            'petition': 'Petición',
            'complaint': 'Queja',
            'claim': 'Reclamo',
            'suggestion': 'Sugerencia'
        }

        pqrs_team = request.env['helpdesk.team'].sudo().search([
            '|',
            ('name', 'ilike', 'pqrs'),
            ('name', 'ilike', 'servicio')
        ], limit=1)

        ticket = request.env['helpdesk.ticket'].sudo().create({
            'name': f"{pqrs_type_labels.get(pqrs_type, 'Solicitud')} - {subject}",
            'partner_id': partner.id,
            'description': message,
            'team_id': pqrs_team.id if pqrs_team else False,
            'priority': '2' if pqrs_type in ['complaint', 'claim'] else '1',
        })

        if post.get('attachment'):
            attachment_file = post.get('attachment')
            request.env['ir.attachment'].sudo().create({
                'name': attachment_file.filename,
                'datas': base64.b64encode(attachment_file.read()),
                'res_model': 'helpdesk.ticket',
                'res_id': ticket.id,
            })

        return request.redirect(f'/mybohio/ticket/{ticket.id}')

    @http.route('/mybohio/request_credit', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def mybohio_request_credit(self, **post):
        """Solicitar crédito - Crea oportunidad en CRM"""
        partner = request.env.user.partner_id

        if not partner.credit_limit or partner.credit_limit <= 0:
            return request.redirect('/mybohio?error=no_credit_limit')

        amount = float(post.get('amount', 0))
        purpose = post.get('purpose', '')

        if amount <= 0 or amount > partner.credit_limit:
            return request.redirect('/mybohio?error=invalid_amount')

        real_estate_team = request.env['crm.team'].sudo().search([
            '|',
            ('name', 'ilike', 'inmobiliaria'),
            ('name', 'ilike', 'real estate')
        ], limit=1)

        opportunity = request.env['crm.lead'].sudo().create({
            'name': f"Solicitud de Crédito - {partner.name}",
            'partner_id': partner.id,
            'type': 'opportunity',
            'expected_revenue': amount,
            'description': f"Monto solicitado: ${amount:,.2f}\nPropósito: {purpose}",
            'team_id': real_estate_team.id if real_estate_team else False,
            'user_id': request.env.user.id,
        })

        return request.redirect(f'/mybohio?credit_request_created={opportunity.id}')

    # =================== VISTA ADMINISTRATIVA (USUARIOS INTERNOS) ===================

    @http.route('/mybohio/admin', type='http', auth='user', website=True)
    def mybohio_admin_portal(self, **kw):
        """Vista general del portal para usuarios internos"""
        if not request.env.user.has_group('base.group_user'):
            return request.redirect('/mybohio')

        # Propietarios
        owners = request.env['res.partner'].sudo().search([
            ('id', 'in', request.env['product.template'].sudo().search([
                ('is_property', '=', True)
            ]).mapped('partner_id').ids +
            request.env['contract.owner.partner'].sudo().search([]).mapped('partner_id').ids)
        ])

        owner_stats = {}
        total_properties = 0
        total_monthly_income = 0
        total_occupancy = 0

        for owner in owners:
            props = request.env['product.template'].sudo().search([
                ('is_property', '=', True),
                '|',
                ('partner_id', '=', owner.id),
                ('owners_lines.partner_id', '=', owner.id)
            ])

            contracts = request.env['property.contract'].sudo().search([
                ('property_id', 'in', props.ids),
                ('contract_type', '=', 'is_rental'),
                ('state', 'in', ['confirmed', 'renew'])
            ])

            occupied = len(contracts.mapped('property_id'))
            total = len(props)
            occupancy = (occupied / total * 100) if total > 0 else 0
            monthly = sum(contracts.mapped('rent'))

            owner_stats[owner.id] = {
                'total_properties': total,
                'occupied': occupied,
                'occupancy_rate': occupancy,
                'monthly_income': monthly
            }

            total_properties += total
            total_monthly_income += monthly
            total_occupancy += occupancy

        avg_occupancy = (total_occupancy / len(owners)) if owners else 0

        # Arrendatarios
        tenants = request.env['res.partner'].sudo().search([
            ('id', 'in', request.env['property.contract'].sudo().search([
                ('contract_type', '=', 'is_rental'),
                ('state', 'in', ['confirmed', 'renew'])
            ]).mapped('partner_id').ids)
        ])

        tenant_stats = {}
        active_tenant_contracts = 0
        tenants_up_to_date = 0
        total_overdue = 0

        for tenant in tenants:
            contract = request.env['property.contract'].sudo().search([
                ('partner_id', '=', tenant.id),
                ('contract_type', '=', 'is_rental'),
                ('state', 'in', ['confirmed', 'renew'])
            ], limit=1)

            if contract:
                active_tenant_contracts += 1

                overdue_invoices = request.env['account.move'].sudo().search([
                    ('partner_id', '=', tenant.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('payment_state', 'in', ['not_paid', 'partial']),
                    ('invoice_date_due', '<', fields.Date.today())
                ])

                overdue = sum(overdue_invoices.mapped('amount_residual'))
                up_to_date = overdue == 0

                if up_to_date:
                    tenants_up_to_date += 1

                total_overdue += overdue

                tenant_stats[tenant.id] = {
                    'property_name': contract.property_id.name,
                    'rent': contract.rent or 0,
                    'up_to_date': up_to_date,
                    'overdue': overdue
                }

        values = {
            'page_name': 'mybohio_admin',
            'owners': owners,
            'owner_stats': owner_stats,
            'total_properties': total_properties,
            'total_monthly_income': total_monthly_income,
            'avg_occupancy': avg_occupancy,
            'tenants': tenants,
            'tenant_stats': tenant_stats,
            'active_tenant_contracts': active_tenant_contracts,
            'tenants_up_to_date': tenants_up_to_date,
            'total_overdue': total_overdue,
        }

        return request.render('bohio_real_estate.mybohio_admin_portal_home', values)
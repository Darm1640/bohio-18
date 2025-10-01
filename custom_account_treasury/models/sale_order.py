# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    """Extiende sale.order para gestión de anticipos"""
    _inherit = 'sale.order'

    advance_request_ids = fields.One2many(
        'advance.request',
        'sale_order_id',
        string='Solicitudes de Anticipo'
    )

    advance_count = fields.Integer(
        string='# Anticipos',
        compute='_compute_advance_count'
    )

    total_advance_amount = fields.Monetary(
        string='Total Anticipos',
        currency_field='currency_id',
        compute='_compute_advance_amount'
    )

    total_advance_available = fields.Monetary(
        string='Anticipos Disponibles',
        currency_field='currency_id',
        compute='_compute_advance_amount'
    )

    advance_percentage = fields.Float(
        string='% Anticipo',
        default=30,
        help='Porcentaje de anticipo sugerido'
    )

    has_advances = fields.Boolean(
        string='Tiene Anticipos',
        compute='_compute_advance_count'
    )

    @api.depends('advance_request_ids')
    def _compute_advance_count(self):
        """Cuenta solicitudes de anticipo"""
        for order in self:
            order.advance_count = len(order.advance_request_ids)
            order.has_advances = bool(order.advance_request_ids)

    @api.depends('advance_request_ids', 'advance_request_ids.amount_paid', 'advance_request_ids.amount_available')
    def _compute_advance_amount(self):
        """Calcula montos de anticipos"""
        for order in self:
            # Filtrar solicitudes no canceladas (usando el código de etapa)
            requests = order.advance_request_ids.filtered(
                lambda r: not r.stage_id or r.stage_id.code != 'cancelled'
            )
            order.total_advance_amount = sum(requests.mapped('amount_paid'))
            order.total_advance_available = sum(requests.mapped('amount_available'))

    def action_create_advance_request(self):
        """Crea solicitud de anticipo desde orden de venta"""
        self.ensure_one()

        if self.state not in ['sale', 'done']:
            raise UserError(_('La orden debe estar confirmada para solicitar un anticipo'))

        # Buscar tipo de anticipo
        advance_type = self.env['advance.type'].search([
            ('code', '=', 'SALE_ADVANCE')
        ], limit=1)

        if not advance_type:
            # Crear tipo por defecto
            advance_type = self.env['advance.type'].create({
                'name': 'Anticipo de Venta',
                'code': 'SALE_ADVANCE',
                'operation_code': 'ADV_CUST',
                'sequence': 10,
                'default_percentage': 30.0,
                'min_percentage': 10.0,
                'max_percentage': 50.0
            })

        # Calcular monto sugerido
        suggested_amount = self.amount_total * (self.advance_percentage / 100)

        # Preparar distribución analítica si existe cuenta analítica
        analytic_distribution = {}
        if self.analytic_account_id:
            analytic_distribution = {str(self.analytic_account_id.id): 100}

        # Crear solicitud
        request = self.env['advance.request'].create({
            'request_type': 'customer',
            'advance_type_id': advance_type.id,
            'partner_id': self.partner_id.id,
            'sale_order_id': self.id,
            'amount_requested': suggested_amount,
            'description': _('Anticipo para orden de venta %s') % self.name,
            'analytic_distribution': analytic_distribution,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'user_id': self.user_id.id
        })

        # Abrir la solicitud creada
        return {
            'name': _('Solicitud de Anticipo'),
            'type': 'ir.actions.act_window',
            'res_model': 'advance.request',
            'res_id': request.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def action_view_advances(self):
        """Ver anticipos de la orden"""
        self.ensure_one()
        return {
            'name': _('Anticipos'),
            'type': 'ir.actions.act_window',
            'res_model': 'advance.request',
            'view_mode': 'kanban,list,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {
                'default_sale_order_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_request_type': 'customer'
            }
        }

    def action_create_advance_invoice(self):
        """Crea factura de anticipo"""
        self.ensure_one()

        if not self.advance_request_ids:
            raise UserError(_('No hay solicitudes de anticipo para esta orden'))

        # Filtrar anticipos pagados (usando is_paid)
        paid_advances = self.advance_request_ids.filtered(
            lambda r: r.is_paid and r.amount_available > 0
        )

        if not paid_advances:
            raise UserError(_('No hay anticipos pagados disponibles'))

        wizard = self.env['sale.advance.invoice.wizard'].create({
            'sale_order_id': self.id,
            'advance_request_ids': [(6, 0, paid_advances.ids)]
        })

        return {
            'name': _('Crear Factura de Anticipo'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.advance.invoice.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new'
        }
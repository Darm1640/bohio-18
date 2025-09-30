# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    # RELACIÓN CON CONTRATOS
    contract_ids = fields.Many2many(
        'property.contract',
        'payment_contract_rel',
        'payment_id', 'contract_id',
        string='Contratos Relacionados',
        help='Contratos asociados a este pago'
    )

    # FILTROS POR PERSONAS RELACIONADAS
    related_partners = fields.Selection([
        ('owners', 'Solo Propietarios'),
        ('tenants', 'Solo Inquilinos'),
        ('all', 'Todos los Relacionados'),
        ('none', 'Sin Filtro')
    ], string='Filtrar por', default='none')

    recipient_type = fields.Selection([
        ('owner', 'Para Propietario'),
        ('tenant', 'Para Inquilino'),
        ('third_party', 'Para Tercero')
    ], string='Destinatario', default='tenant')

    # PAGOS A TERCEROS
    is_third_party_payment = fields.Boolean('Pago a través de Tercero')
    third_party_partner_id = fields.Many2one(
        'res.partner',
        string='Tercero',
        help='Persona o empresa que realiza el pago en nombre del inquilino/propietario'
    )

    # INFORMACIÓN DE CHEQUE
    check_number = fields.Char('Número de Cheque')
    check_date = fields.Date('Fecha del Cheque')
    check_bank = fields.Char('Banco del Cheque')

    # NUMERACIÓN ÚNICA PARA PAGOS
    payment_sequence = fields.Char(
        string='Número de Pago',
        default='/',
        copy=False,
        readonly=True,
        help='Número único para identificar el pago'
    )

    # INTEGRACIÓN CON VENDEDORES
    sales_person_id = fields.Many2one('res.users', 'Vendedor')
    sales_team_id = fields.Many2one('crm.team', 'Equipo de Ventas')

    @api.model_create_multi
    def create(self, vals_list):
        """Generar numeración única al crear"""
        for vals in vals_list:
            if vals.get('payment_sequence', '/') == '/':
                if vals.get('partner_type') == 'supplier':
                    sequence_code = 'payment.out.sequence'
                else:
                    sequence_code = 'payment.in.sequence'
                vals['payment_sequence'] = self.env['ir.sequence'].next_by_code(sequence_code) or '/'
        return super().create(vals_list)

    @api.onchange('contract_ids')
    def _onchange_contracts(self):
        """Auto-completar campos desde contratos"""
        if self.contract_ids:
            # Auto-completar vendedor y equipo
            if not self.sales_person_id:
                self.sales_person_id = self.contract_ids[0].user_id
            if not self.sales_team_id:
                # Buscar equipo del vendedor
                team = self.env['crm.team'].search([
                    ('member_ids', 'in', [self.sales_person_id.id])
                ], limit=1)
                self.sales_team_id = team

    @api.onchange('related_partners', 'contract_ids')
    def _onchange_related_partners_filter(self):
        """Filtrar partners según selección"""
        if not self.contract_ids or self.related_partners == 'none':
            return {'domain': {'partner_id': []}}

        partner_ids = []
        for contract in self.contract_ids:
            if self.related_partners in ['owners', 'all']:
                if contract.is_multi_propietario:
                    partner_ids.extend(contract.owners_lines.mapped('partner_id.id'))
                else:
                    partner_ids.append(contract.partner_is_owner_id.id)

            if self.related_partners in ['tenants', 'all']:
                partner_ids.append(contract.partner_id.id)

        return {'domain': {'partner_id': [('id', 'in', list(set(partner_ids)))]}}


# NUEVO modelo para tipos de operación
class PaymentOperationType(models.Model):
    _name = 'payment.operation.type'
    _description = 'Tipo de Operación de Pago'

    name = fields.Char('Nombre', required=True)
    code = fields.Char('Código', required=True)
    journal_id = fields.Many2one('account.journal', 'Diario')
    partner_type = fields.Selection([
        ('customer', 'Cliente'),
        ('supplier', 'Proveedor')
    ], string='Tipo de Partner')
    recipient_type = fields.Selection([
        ('owner', 'Propietario'),
        ('tenant', 'Inquilino'),
        ('third_party', 'Tercero')
    ], string='Destinatario')
    is_default = fields.Boolean('Por Defecto')
    allow_third_party = fields.Boolean('Permitir Terceros')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'El código debe ser único'),
    ]
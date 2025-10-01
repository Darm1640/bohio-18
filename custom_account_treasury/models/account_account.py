from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class AccountAccount(models.Model):
    """Extensión de account.account para gestión de anticipos"""
    _inherit = 'account.account'

    used_for_advance_payment = fields.Boolean(
        string='Cuenta de Anticipo',
        company_dependent=True,
        tracking=True,
        help='Marca si esta cuenta se usa para anticipos. Activa reconciliación automática.'
    )
    
    advance_type_ids = fields.One2many(
        'advance.type',
        'advance_account_id',
        string='Tipos de Anticipo',
        help='Tipos de anticipo que usan esta cuenta'
    )
    
    default_advance_type_id = fields.Many2one(
        'advance.type',
        string='Tipo de Anticipo por Defecto',
        compute='_compute_default_advance_type',
        store=True,
        help='Tipo de anticipo por defecto para esta cuenta'
    )
    
    auto_reconcile_advances = fields.Boolean(
        string='Reconciliar Anticipos Automáticamente',
        default=True,
        help='Reconciliar automáticamente los movimientos de anticipo'
    )
    
    advance_balance = fields.Monetary(
        string='Saldo de Anticipos',
        currency_field='currency_id',
        compute='_compute_advance_metrics',
        store=False,
        help='Saldo actual de anticipos en esta cuenta'
    )
    
    pending_advance_count = fields.Integer(
        string='Anticipos Pendientes',
        compute='_compute_advance_metrics',
        store=False
    )
    

    @api.depends('advance_type_ids')
    def _compute_default_advance_type(self):
        """Calcula el tipo de anticipo por defecto"""
        for account in self:
            if account.advance_type_ids:
                account.default_advance_type_id = account.advance_type_ids[0]
            else:
                account.default_advance_type_id = False
    
    def _compute_advance_metrics(self):
        """Calcula métricas de anticipos"""
        for account in self:
            if not account.used_for_advance_payment:
                account.advance_balance = 0.0
                account.pending_advance_count = 0
                continue
            
            domain = [
                ('account_id', '=', account.id),
                ('move_id.state', '=', 'posted'),
                ('reconciled', '=', False),
                ('move_id.is_advance_entry', '=', True)
            ]
            
            lines = self.env['account.move.line'].search(domain)
            account.advance_balance = sum(lines.mapped('amount_residual'))
            account.pending_advance_count = len(lines)
    

    
    @api.onchange('used_for_advance_payment')
    def _onchange_used_for_advance_payment(self):
        """Activa reconciliación automática para cuentas de anticipo"""
        if self.used_for_advance_payment:
            self.reconcile = True
            self.auto_reconcile_advances = True
    
    @api.onchange('account_type')
    def _onchange_account_type(self):
        """Sugiere configuración según tipo de cuenta"""
        if self.account_type in ['asset_current', 'liability_current']:
            self.used_for_advance_payment = True
    

    
    def get_advance_type_for_partner(self, partner):
        """
        Obtiene el tipo de anticipo apropiado para un partner
        
        :param partner: res.partner record
        :return: advance.type record o False
        """
        self.ensure_one()
        
        if not self.used_for_advance_payment:
            return False
        
        if self.default_advance_type_id:
            if self.default_advance_type_id.can_be_used_by_partner(partner):
                return self.default_advance_type_id
        
        for advance_type in self.advance_type_ids:
            if advance_type.can_be_used_by_partner(partner):
                return advance_type
        
        return False
    
    def create_advance_payment(self, partner, amount, payment_type='inbound'):
        """
        Crea un pago de anticipo usando esta cuenta
        
        :param partner: res.partner record
        :param amount: Monto del anticipo
        :param payment_type: 'inbound' o 'outbound'
        :return: account.payment record
        """
        self.ensure_one()
        
        if not self.used_for_advance_payment:
            raise ValidationError(
                _('La cuenta %s no está configurada para anticipos') % self.name
            )
        
        advance_type = self.get_advance_type_for_partner(partner)
        if not advance_type:
            advance_type = self.env['advance.type'].get_default_for_context(
                partner=partner,
                context_type='payment'
            )
        
        if not advance_type:
            raise ValidationError(
                _('No se encontró un tipo de anticipo apropiado para %s') % partner.name
            )
        
        advance_type.validate_amount(amount)
        
        payment_vals = {
            'payment_type': payment_type,
            'partner_type': 'customer' if partner.customer_rank > 0 else 'supplier',
            'partner_id': partner.id,
            'amount': amount,
            'advance': True,
            'advance_type_id': advance_type.id,
            'destination_account_id': self.id,
        }
        
        if advance_type.journal_id:
            payment_vals['journal_id'] = advance_type.journal_id.id
        
        return self.env['account.payment'].create(payment_vals)
    
    # ========================================================================
    # OVERRIDES
    # ========================================================================
    
    def write(self, vals):
        """Override para manejar cambios en configuración de anticipos"""
        if vals.get('used_for_advance_payment'):
            vals['reconcile'] = True
        
        result = super().write(vals)
        
        if 'used_for_advance_payment' in vals and not vals['used_for_advance_payment']:
            for account in self:
                if account.advance_balance != 0:
                    raise ValidationError(
                        _('No se puede desactivar la cuenta %s como anticipo mientras tenga saldo pendiente') % 
                        account.name
                    )
        
        return result
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override para configuración automática"""
        for vals in vals_list:
            if vals.get('used_for_advance_payment'):
                vals['reconcile'] = True
        
        return super().create(vals_list)
    
    def unlink(self):
        """Validar antes de eliminar"""
        for account in self:
            if account.advance_type_ids:
                raise ValidationError(
                    _('No se puede eliminar la cuenta %s porque tiene tipos de anticipo asociados') % 
                    account.name
                )
            
            if account.used_for_advance_payment and account.advance_balance != 0:
                raise ValidationError(
                    _('No se puede eliminar la cuenta %s porque tiene saldo de anticipos pendiente') % 
                    account.name
                )
        
        return super().unlink()
    

    
    @api.constrains('used_for_advance_payment', 'reconcile')
    def _check_advance_reconcile(self):
        """Verifica que las cuentas de anticipo tengan reconciliación activa"""
        for account in self:
            if account.used_for_advance_payment and not account.reconcile:
                raise ValidationError(
                    _('Las cuentas de anticipo deben tener la reconciliación activada')
                )
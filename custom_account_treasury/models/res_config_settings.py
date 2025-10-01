from odoo import fields, models, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # ============ Configuración de Anticipos ============
    treasury_default_customer_advance_account_id = fields.Many2one(
        'account.account',
        string='Cuenta de Anticipos de Clientes',
        related='company_id.default_customer_advance_account_id',
        readonly=False,
        domain="[('account_type', 'in', ['liability_current', 'asset_receivable']), ('company_ids', '=', id)]",
        help='Cuenta por defecto para registrar anticipos de clientes'
    )

    treasury_default_supplier_advance_account_id = fields.Many2one(
        'account.account',
        string='Cuenta de Anticipos a Proveedores',
        related='company_id.default_supplier_advance_account_id',
        readonly=False,
        domain="[('account_type', 'in', ['asset_current', 'liability_payable']), ('company_ids', '=', id)]",
        help='Cuenta por defecto para registrar anticipos a proveedores'
    )

    treasury_auto_apply_advances = fields.Boolean(
        string='Aplicar Anticipos Automáticamente',
        related='company_id.treasury_auto_apply_advances',
        readonly=False,
        help='Aplica automáticamente los anticipos disponibles al confirmar facturas'
    )

    # ============ Configuración Multi-Tercero ============
    treasury_enable_multi_partner = fields.Boolean(
        string='Habilitar Multi-Tercero Global',
        config_parameter='custom_account_treasury.enable_multi_partner',
        help='Permite habilitar la funcionalidad multi-tercero en facturas, notas de crédito y recibos'
    )

    treasury_multi_partner_default = fields.Boolean(
        string='Multi-Tercero por Defecto',
        config_parameter='custom_account_treasury.multi_partner_default',
        help='Activa multi-tercero por defecto en nuevos documentos'
    )

    @api.model
    def get_values(self):
        """Obtiene los valores de configuración desde los parámetros globales."""
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()

        res.update(
            treasury_enable_multi_partner=params.get_param('custom_account_treasury.enable_multi_partner', default=False),
            treasury_multi_partner_default=params.get_param('custom_account_treasury.multi_partner_default', default=False),
        )

        return res

    def set_values(self):
        """Guarda los valores de configuración en los parámetros globales."""
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()

        params.set_param('custom_account_treasury.enable_multi_partner', self.treasury_enable_multi_partner)
        params.set_param('custom_account_treasury.multi_partner_default', self.treasury_multi_partner_default)
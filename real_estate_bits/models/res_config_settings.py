from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    penalty_percent = fields.Float("Penalty Percentage")
    penalty_account = fields.Many2one("account.account", "Late Payments Penalty Account",
                                      config_parameter="real_estate_bits.penalty_account")
    discount_account = fields.Many2one("account.account", "Discount Account",
                                       config_parameter="real_estate_bits.discount_account")
    income_account = fields.Many2one("account.account", "Income Account",
                                     config_parameter="real_estate_bits.income_account")
    expense_account = fields.Many2one("account.account", "Managerial Expenses Account",
                                      config_parameter="real_estate_bits.expense_account")
    security_deposit_account = fields.Many2one("account.account", "Security Deposit Account",
                                               config_parameter="real_estate_bits.security_deposit_account", )
    revenue_account = fields.Many2one("account.account", "Revenue Account",
                                      config_parameter="real_estate_bits.revenue_account", )

    income_journal = fields.Many2one("account.journal", "Income Journal",
                                     config_parameter="real_estate_bits.income_journal", )
    maintenance_journal = fields.Many2one("account.journal", "Maintenance Journal",
                                          config_parameter="real_estate_bits.maintenance_journal", )



class Config(models.TransientModel):
    _name = "gmap.config"
    _description = "Google Config"

    @api.model
    def get_key_api(self):
        return self.env["ir.config_parameter"].sudo().get_param("google_maps_api_key")

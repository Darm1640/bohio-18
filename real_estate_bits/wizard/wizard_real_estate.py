
from odoo import api, fields, models, _, Command


class CancelContractWizard(models.TransientModel):
    _name = 'cancel.contract.wizard'
    _description = 'Cancelar Contrato'

    termination_date = fields.Date(string='Fecha de Finalización', required=True, default=fields.Date.today)
    reason = fields.Text(string='Motivo de Cancelación', required=True)

    def action_cancel_contract(self):
        contract = self.env['property.contract'].browse(self.env.context.get('active_id'))
        contract.write({
            'state': 'cancel',
            'date_end': self.termination_date
        })
        contract.message_post(body=f"Contrato cancelado. Motivo: {self.reason}")
        return {'type': 'ir.actions.act_window_close'}

class ChangeClientWizard(models.TransientModel):
    _name = 'change.client.wizard'
    _description = 'Cambiar Cliente del Contrato'

    new_partner_id = fields.Many2one('res.partner', string='Nuevo Cliente', required=True)

    def action_change_client(self):
        contract = self.env['property.contract'].browse(self.env.context.get('active_id'))
        old_partner = contract.partner_id.name
        contract.write({
            'partner_id': self.new_partner_id.id
        })
        contract.message_post(body=f"Cliente cambiado de {old_partner} a {self.new_partner_id.name}")
        return {'type': 'ir.actions.act_window_close'}

class ReactivateContractWizard(models.TransientModel):
    _name = 'reactivate.contract.wizard'
    _description = 'Reactivar Contrato'

    def action_reactivate_contract(self):
        contract = self.env['property.contract'].browse(self.env.context.get('active_id'))
        contract.write({
            'state': 'draft'
        })
        contract.message_post(body="Contrato reactivado y puesto en estado borrador")
        return {'type': 'ir.actions.act_window_close'}


class ModifyPaymentWizard(models.TransientModel):
    _name = 'modify.payment.wizard'
    _description = 'Modificar Pagos del Contrato'

    new_rental_fee = fields.Float(string='Nueva Cuota Mensual', required=True)
    quota_ids = fields.Many2many('loan.line', string='Cuotas a Modificar')
    
    @api.model
    def default_get(self, fields):
        res = super(ModifyPaymentWizard, self).default_get(fields)
        contract = self.env['property.contract'].browse(self.env.context.get('active_id'))
        res['new_rental_fee'] = contract.rental_fee
        return res

    def action_modify_payment(self):
        contract = self.env['property.contract'].browse(self.env.context.get('active_id'))
        old_fee = contract.rental_fee
        # Recalcular las cuotas y comisiones solo para las cuotas seleccionadas
        for line in self.quota_ids:
            line.write({
                'amount': self.new_rental_fee,
                'commission': self.new_rental_fee * (contract.commission_rate / 100)
            })
        
        modified_quotas = len(self.quota_ids)
        contract.message_post(body=f"Cuota mensual modificada de {old_fee} a {self.new_rental_fee} para {modified_quotas} cuotas.")
        return {'type': 'ir.actions.act_window_close'}


class UpdateTarifaWizard(models.TransientModel):
    _name = 'update.tarifa.wizard'
    _description = 'Actualizar Tarifa'

    new_price = fields.Float(string='Nueva Tarifa', required=True)

    def action_update_tarifa(self):
        contract = self.env['property.contract'].browse(self.env.context.get('active_id'))
        old_price = contract.rental_fee
        contract.rental_fee = self.new_price
        contract.message_post(body=f"Tarifa actualizada de {old_price} a {self.new_price}")
        return {'type': 'ir.actions.act_window_close'}


class RenovarContratoWizard(models.TransientModel):
    _name = 'renovar.contrato.wizard'
    _description = 'Renovar Contrato'

    new_end_date = fields.Date(string='Nueva Fecha de Fin', required=True)
    new_price = fields.Float(string='Nuevo Precio (opcional)')
    num_additional_quotas = fields.Integer(string='Número de Cuotas Adicionales', required=True)

    @api.model
    def default_get(self, fields):
        res = super(RenovarContratoWizard, self).default_get(fields)
        contract = self.env['property.contract'].browse(self.env.context.get('active_id'))
        res['new_end_date'] = contract.date_to + relativedelta(years=1)
        res['new_price'] = contract.rental_fee
        return res

    def action_renovar_contrato(self):
        contract = self.env['property.contract'].browse(self.env.context.get('active_id'))
        old_end_date = contract.date_to
        old_price = contract.rental_fee
        
        contract.date_to = self.new_end_date
        contract.rental_fee = self.new_price

        # Calcular la fecha de inicio para las nuevas cuotas
        last_quota_date = max(contract.loan_line_ids.mapped('date'))
        start_date = last_quota_date + relativedelta(days=1)

        # Agregar nuevas cuotas
        new_quotas = []
        for i in range(self.num_additional_quotas):
            new_date = start_date + relativedelta(months=i)
            new_quotas.append((0, 0, {
                'name': f'Cuota Adicional {i+1}',
                'serial': len(contract.loan_line_ids) + i + 1,
                'amount': self.new_price,
                'date': new_date,
            }))

        contract.write({'loan_line_ids': new_quotas})

        message = f"""
        Contrato renovado:
        - Fecha de fin actualizada de {old_end_date} a {self.new_end_date}
        - Tarifa actualizada de {old_price} a {self.new_price}
        - Se han agregado {self.num_additional_quotas} cuotas adicionales
        """
        
        contract.message_post(body=message)
        return {'type': 'ir.actions.act_window_close'}

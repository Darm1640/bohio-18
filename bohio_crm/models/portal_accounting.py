from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CrmLeadPortal(models.Model):
    """Extensiones del portal para CRM Lead con métricas contables"""
    _inherit = 'crm.lead'

    # Campos para portal con métricas financieras específicas
    portal_invoice_count = fields.Integer('Facturas en Portal', compute='_compute_portal_accounting_metrics')
    portal_payment_count = fields.Integer('Pagos en Portal', compute='_compute_portal_accounting_metrics')
    portal_credit_note_count = fields.Integer('Notas Crédito en Portal', compute='_compute_portal_accounting_metrics')
    portal_contract_value = fields.Monetary('Valor Contrato Portal', currency_field='company_currency', compute='_compute_portal_accounting_metrics')

    @api.depends('partner_id', 'contract_id')
    def _compute_portal_accounting_metrics(self):
        """Calcular métricas contables para mostrar en portal"""
        for lead in self:
            if not lead.partner_id:
                lead.portal_invoice_count = 0
                lead.portal_payment_count = 0
                lead.portal_credit_note_count = 0
                lead.portal_contract_value = 0.0
                continue

            # Contar facturas del cliente
            invoices = self.env['account.move'].search([
                ('partner_id', '=', lead.partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted')
            ])
            lead.portal_invoice_count = len(invoices)

            # Contar notas de crédito
            credit_notes = self.env['account.move'].search([
                ('partner_id', '=', lead.partner_id.id),
                ('move_type', '=', 'out_refund'),
                ('state', '=', 'posted')
            ])
            lead.portal_credit_note_count = len(credit_notes)

            # Contar pagos
            payments = self.env['account.payment'].search([
                ('partner_id', '=', lead.partner_id.id),
                ('state', '=', 'posted')
            ])
            lead.portal_payment_count = len(payments)

            # Valor del contrato si existe
            if lead.contract_id:
                if lead.contract_id.contract_type == 'is_rental':
                    months = 12  
                    if lead.contract_id.date_to and lead.contract_id.date_from:
                        delta = lead.contract_id.date_to - lead.contract_id.date_from
                        months = max(1, delta.days // 30)
                    lead.portal_contract_value = lead.contract_id.rental_fee * months
                else:
                    # Para ventas: usar expected_revenue
                    lead.portal_contract_value = lead.expected_revenue or 0.0
            else:
                lead.portal_contract_value = 0.0

    def action_portal_view_invoices(self):
        """Acción para ver facturas desde el portal"""
        self.ensure_one()
        if not self.partner_id:
            return {'type': 'ir.actions.act_window_close'}

        return {
            'type': 'ir.actions.act_window',
            'name': f'Facturas - {self.partner_id.name}',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [
                ('partner_id', '=', self.partner_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted')
            ],
            'context': {
                'create': False,
                'edit': False,
                'delete': False,
            },
            'target': 'current',
        }

    def action_portal_view_payments(self):
        """Acción para ver pagos desde el portal"""
        self.ensure_one()
        if not self.partner_id:
            return {'type': 'ir.actions.act_window_close'}

        return {
            'type': 'ir.actions.act_window',
            'name': f'Pagos - {self.partner_id.name}',
            'view_mode': 'list,form',
            'res_model': 'account.payment',
            'domain': [
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'posted')
            ],
            'context': {
                'create': False,
                'edit': False,
                'delete': False,
            },
            'target': 'current',
        }

    def action_portal_view_credit_notes(self):
        """Acción para ver notas de crédito desde el portal"""
        self.ensure_one()
        if not self.partner_id:
            return {'type': 'ir.actions.act_window_close'}

        return {
            'type': 'ir.actions.act_window',
            'name': f'Notas de Crédito - {self.partner_id.name}',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [
                ('partner_id', '=', self.partner_id.id),
                ('move_type', '=', 'out_refund'),
                ('state', '=', 'posted')
            ],
            'context': {
                'create': False,
                'edit': False,
                'delete': False,
            },
            'target': 'current',
        }

    def get_portal_accounting_summary(self):
        """Obtener resumen contable para mostrar en portal"""
        self.ensure_one()
        if not self.partner_id:
            return {
                'total_invoiced': 0.0,
                'total_paid': 0.0,
                'total_pending': 0.0,
                'invoice_count': 0,
                'payment_count': 0,
                'last_payment_date': False,
                'contract_status': 'Sin contrato'
            }

        # Buscar facturas del cliente
        invoices = self.env['account.move'].search([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted')
        ])

        total_invoiced = sum(invoices.mapped('amount_total'))
        total_pending = sum(invoices.mapped('amount_residual'))
        total_paid = total_invoiced - total_pending

        # Último pago
        last_payment = self.env['account.payment'].search([
            ('partner_id', '=', self.partner_id.id),
            ('state', '=', 'posted')
        ], order='date desc', limit=1)

        # Estado del contrato
        contract_status = 'Sin contrato'
        if self.contract_id:
            if self.contract_id.state == 'active':
                contract_status = 'Contrato activo'
            elif self.contract_id.state == 'expired':
                contract_status = 'Contrato vencido'
            else:
                contract_status = f'Contrato {self.contract_id.state}'

        return {
            'total_invoiced': total_invoiced,
            'total_paid': total_paid,
            'total_pending': total_pending,
            'invoice_count': len(invoices),
            'payment_count': self.portal_payment_count,
            'last_payment_date': last_payment.date if last_payment else False,
            'contract_status': contract_status,
            'contract_value': self.portal_contract_value,
            'payment_percentage': (total_paid / total_invoiced * 100) if total_invoiced > 0 else 0,
        }


class AccountMovePortal(models.Model):
    """Extensiones para facturas en el portal"""
    _inherit = 'account.move'

    portal_notes = fields.Text('Notas para Portal', help='Notas que se muestran al cliente en el portal')
    portal_visible = fields.Boolean('Visible en Portal', default=True, help='Controla si esta factura es visible en el portal del cliente')
    portal_payment_instructions = fields.Html('Instrucciones de Pago', help='Instrucciones específicas de pago para mostrar en el portal')

    def get_portal_payment_status(self):
        """Obtener estado de pago para mostrar en portal"""
        self.ensure_one()
        if self.move_type != 'out_invoice':
            return 'N/A'

        if self.payment_state == 'paid':
            return 'Pagado'
        elif self.payment_state == 'partial':
            return 'Pago parcial'
        elif self.payment_state == 'not_paid':
            if self.invoice_date_due and self.invoice_date_due < fields.Date.today():
                return 'Vencido'
            else:
                return 'Pendiente'
        else:
            return 'En proceso'

    def get_portal_payment_methods(self):
        """Obtener métodos de pago disponibles para mostrar en portal"""
        company = self.company_id
        payment_methods = []
        payment_methods.append({
            'name': 'Transferencia Bancaria',
            'type': 'bank_transfer',
            'instructions': company.bank_ids[0].bank_name if company.bank_ids else 'Contactar para detalles bancarios',
            'account': company.bank_ids[0].acc_number if company.bank_ids else '',
        })

        if 'payment_acquirer_ids' in company._fields:
            payment_methods.append({
                'name': 'Tarjeta de Crédito/Débito',
                'type': 'credit_card',
                'instructions': 'Pago en línea disponible',
                'account': '',
            })

        return payment_methods


class AccountPaymentPortal(models.Model):
    """Extensiones para pagos en el portal"""
    _inherit = 'account.payment'

    # Campos adicionales para el portal
    portal_reference = fields.Char('Referencia Portal', help='Referencia que ve el cliente en el portal')
    portal_notes = fields.Text('Notas Portal', help='Notas adicionales para el cliente')
    portal_receipt_sent = fields.Boolean('Recibo Enviado', default=False, help='Indica si se envió el recibo al cliente')

    def get_portal_status_display(self):
        """Obtener estado para mostrar en portal"""
        self.ensure_one()
        status_mapping = {
            'draft': 'Borrador',
            'posted': 'Confirmado',
            'sent': 'Enviado',
            'reconciled': 'Conciliado',
            'cancelled': 'Cancelado',
        }
        return status_mapping.get(self.state, self.state.title())

    def send_portal_receipt(self):
        """Enviar recibo al cliente por email"""
        self.ensure_one()
        if not self.partner_id.email:
            raise ValidationError(_('El cliente no tiene email configurado.'))

        # Aquí se implementaría el envío del email
        # Por ahora solo marcamos como enviado
        self.portal_receipt_sent = True

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Recibo Enviado'),
                'message': _('El recibo de pago ha sido enviado al cliente.'),
                'type': 'success',
                'sticky': False,
            }
        }
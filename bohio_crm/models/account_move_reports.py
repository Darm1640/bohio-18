# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Campos adicionales para reportes personalizados
    bohio_document_type = fields.Selection([
        ('comprobante_egreso', 'Comprobante de Egreso'),
        ('recibo_caja', 'Recibo de Caja'),
        ('factura_electronica', 'Factura Electrónica'),
    ], string='Tipo de Documento Bohío', compute='_compute_bohio_document_type', store=True)

    @api.depends('move_type', 'journal_id')
    def _compute_bohio_document_type(self):
        """
        Determina el tipo de documento para reportes Bohío basado en el tipo de movimiento
        """
        for move in self:
            if move.move_type in ('out_invoice', 'out_refund'):
                if move.l10n_co_dian_state == 'invoice_accepted':
                    move.bohio_document_type = 'factura_electronica'
                else:
                    move.bohio_document_type = 'recibo_caja'
            elif move.move_type in ('in_invoice', 'in_refund'):
                move.bohio_document_type = 'comprobante_egreso'
            else:
                move.bohio_document_type = False

    def _get_bohio_report_name(self):
        """
        Retorna el nombre del reporte apropiado según el tipo de documento
        """
        self.ensure_one()

        # Si es factura electrónica aceptada por DIAN, usar reporte DIAN personalizado
        if (self.l10n_co_dian_state == 'invoice_accepted' and
            self.move_type in ('out_invoice', 'out_refund')):
            return 'bohio_crm.report_factura_electronica_bohio'

        # Para facturas de cliente (ingresos) - Recibo de Caja
        if self.move_type in ('out_invoice', 'out_refund'):
            return 'bohio_crm.report_recibo_caja_document'

        # Para facturas de proveedor (egresos) - Comprobante de Egreso
        if self.move_type in ('in_invoice', 'in_refund'):
            return 'bohio_crm.report_comprobante_egreso_document'

        # Si no aplica ninguno, usar el reporte estándar
        return super()._get_name_invoice_report()

    def _get_payment_methods_summary(self):
        """
        Obtiene un resumen de los métodos de pago utilizados en la factura
        """
        self.ensure_one()
        payment_methods = []

        # Buscar pagos relacionados con esta factura
        payments = self.env['account.payment'].search([
            ('reconciled_invoice_ids', 'in', self.id)
        ])

        for payment in payments:
            payment_methods.append({
                'method': payment.journal_id.name,
                'reference': payment.name,
                'amount': payment.amount,
                'currency': payment.currency_id,
            })

        # Si no hay pagos registrados, usar información del diario
        if not payment_methods and self.l10n_co_edi_payment_option_id:
            payment_methods.append({
                'method': self.l10n_co_edi_payment_option_id.name,
                'reference': self.payment_reference or '-',
                'amount': self.amount_total,
                'currency': self.currency_id,
            })

        return payment_methods

    def _get_invoice_observations(self):
        """
        Genera observaciones automáticas para la factura basadas en las líneas
        """
        self.ensure_one()

        if self.narration:
            return self.narration

        # Generar observación automática
        observations = []

        # Agregar referencias de contratos si existen
        contract_refs = self.invoice_line_ids.mapped('name')
        if contract_refs:
            # Buscar números de contratos en las descripciones
            import re
            for line_name in contract_refs:
                contract_match = re.search(r'Contrato\s+(\d+)', line_name)
                if contract_match:
                    observations.append(f"CONTRATO {contract_match.group(1)}")
                    break

        # Agregar tipo de documento
        if self.move_type == 'out_invoice':
            prefix = 'INGRESO'
        elif self.move_type == 'in_invoice':
            prefix = 'EGRESO POR PAGO A'
        else:
            prefix = 'DOCUMENTO'

        if observations:
            return f"{prefix} - {self.partner_id.name} - {' - '.join(observations)}"

        return f"{prefix} - {self.partner_id.name} - FACTURA(S): {self.name}"

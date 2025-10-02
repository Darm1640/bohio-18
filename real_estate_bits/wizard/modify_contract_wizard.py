# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date
from odoo.tools import float_is_zero
from dateutil.relativedelta import relativedelta

class ModifyContractWizard(models.TransientModel):
    _name = 'modify.contract.wizard'
    _description = 'Modificar Contrato - Wizard Unificado'

    # Información básica
    contract_id = fields.Many2one('property.contract', string="Contrato", required=True, ondelete="cascade")
    name = fields.Text(string='Observaciones')

    # Tipo de modificación (como Asset)
    modify_action = fields.Selection(selection="_get_selection_modify_options", string="Acción", required=True)

    # Fechas
    date = fields.Date(default=lambda self: fields.Date.today(), string='Fecha Efectiva')
    effective_date = fields.Date(related='date', string='Fecha Efectiva')

    # Para modificación de fechas
    new_end_date = fields.Date('Nueva Fecha de Fin')
    extend_months = fields.Integer('Extender por Meses', default=12)

    # Para modificación de valores
    new_rental_fee = fields.Float('Nuevo Canon', help="Nuevo valor del canon mensual")
    rental_increase_percentage = fields.Float('Aumento (%)', help="Porcentaje de aumento del canon")

    # Para cancelación
    cancellation_type = fields.Selection([
        ('mutual', 'Mutuo Acuerdo'),
        ('breach_tenant', 'Incumplimiento Inquilino'),
        ('breach_owner', 'Incumplimiento Propietario'),
        ('early_termination', 'Terminación Anticipada'),
        ('property_sale', 'Venta de Propiedad'),
        ('other', 'Otro Motivo')
    ], string='Tipo de Cancelación')

    apply_penalty = fields.Boolean('Aplicar Penalidad')
    penalty_amount = fields.Float('Monto de Penalidad')

    # Para suspensión
    suspension_start = fields.Date('Inicio de Suspensión')
    suspension_end = fields.Date('Fin de Suspensión')

    # Información actual del contrato (como Asset)
    current_end_date = fields.Date(related='contract_id.date_to', readonly=True)
    current_rental_fee = fields.Float(related='contract_id.rental_fee', readonly=True)
    currency_id = fields.Many2one(related='contract_id.company_id.currency_id')
    company_id = fields.Many2one(related='contract_id.company_id')

    # Campos calculados
    pending_amount = fields.Float('Monto Pendiente', compute='_compute_pending_info')
    pending_invoices = fields.Integer('Facturas Pendientes', compute='_compute_pending_info')
    informational_text = fields.Html(compute='_compute_informational_text')

    # Campos para renovación
    copy_conditions = fields.Boolean('Mantener Condiciones Actuales', default=True)
    reason = fields.Text('Motivo/Justificación', required=True)

    @api.model
    def default_get(self, fields_list):
        """Inicializar valores por defecto como Asset"""
        defaults = super().default_get(fields_list)
        if 'contract_id' in fields_list and self.env.context.get('active_id'):
            defaults['contract_id'] = self.env.context.get('active_id')
        return defaults

    @api.model
    def _get_selection_modify_options(self):
        """Opciones de modificación disponibles (como Asset)"""
        return [
            ('extend', _("Extender")),
            ('renew', _("Renovar")),
            ('modify_amount', _("Cambiar Monto")),
            ('modify_dates', _("Cambiar Fechas")),
            ('pause', _("Suspender")),
            ('cancel', _("Cancelar")),
            ('resume', _("Reactivar")),
        ]

    @api.depends('contract_id.loan_line_ids.payment_state', 'contract_id.loan_line_ids.amount')
    def _compute_pending_info(self):
        """Calcular información de pagos pendientes"""
        for wizard in self:
            pending_lines = wizard.contract_id.loan_line_ids.filtered(
                lambda l: l.payment_state != 'paid'
            )
            wizard.pending_invoices = len(pending_lines)
            wizard.pending_amount = sum(pending_lines.mapped('amount'))

    @api.depends('modify_action', 'date', 'new_rental_fee', 'new_end_date', 'cancellation_type')
    def _compute_informational_text(self):
        """Texto informativo según la acción (como Asset)"""
        for wizard in self:
            if wizard.modify_action == 'extend':
                wizard.informational_text = _(
                    "Se extenderá el contrato hasta %(date)s.<br/>"
                    "Se recalcularán las líneas de pago futuras.",
                    date=format_date(self.env, wizard.new_end_date) if wizard.new_end_date else ''
                )
            elif wizard.modify_action == 'renew':
                wizard.informational_text = _(
                    "Se creará un nuevo contrato desde %(date)s.<br/>"
                    "El contrato actual permanecerá como histórico.",
                    date=format_date(self.env, wizard.new_end_date) if wizard.new_end_date else ''
                )
            elif wizard.modify_action == 'modify_amount':
                old_amount = wizard.current_rental_fee
                new_amount = wizard.new_rental_fee
                wizard.informational_text = _(
                    "Se modificará el canon desde %(date)s.<br/>"
                    "Canon actual: <b>$%(old)s</b> → Nuevo canon: <b>$%(new)s</b><br/>"
                    "Se recalcularán las líneas de pago futuras.",
                    date=format_date(self.env, wizard.date),
                    old=f"{old_amount:,.2f}",
                    new=f"{new_amount:,.2f}" if new_amount else "0.00"
                )
            elif wizard.modify_action == 'cancel':
                cancellation_types = dict(wizard._fields['cancellation_type'].selection)
                reason_text = cancellation_types.get(wizard.cancellation_type, 'No especificado')
                penalty_text = f"<br/>Penalidad: <b>${wizard.penalty_amount:,.2f}</b>" if wizard.apply_penalty else ""
                wizard.informational_text = _(
                    "Se cancelará el contrato en la fecha %(date)s.<br/>"
                    "Motivo: <b>%(reason)s</b>%(penalty)s<br/>"
                    "La propiedad quedará disponible para nuevo contrato.",
                    date=format_date(self.env, wizard.date),
                    reason=reason_text,
                    penalty=penalty_text
                )
            elif wizard.modify_action == 'pause':
                wizard.informational_text = _(
                    "Se suspenderá el contrato desde %(start)s hasta %(end)s.<br/>"
                    "Las líneas de pago en este período se pausarán.",
                    start=format_date(self.env, wizard.suspension_start) if wizard.suspension_start else '',
                    end=format_date(self.env, wizard.suspension_end) if wizard.suspension_end else ''
                )
            else:
                wizard.informational_text = _(
                    "Se aplicarán los cambios al contrato desde la fecha %(date)s.<br/>"
                    "Las líneas de pago futuras se recalcularán.",
                    date=format_date(self.env, wizard.date)
                )

    @api.onchange('modify_action')
    def _onchange_action(self):
        """Cambiar campos según acción (como Asset)"""
        if self.modify_action == 'extend' and self.current_end_date:
            self.new_end_date = self.current_end_date + relativedelta(months=self.extend_months)
        elif self.modify_action == 'modify_amount':
            self.new_rental_fee = self.current_rental_fee
        elif self.modify_action == 'cancel' and self.pending_invoices > 0:
            if not self.env.user.has_group('base.group_system'):
                raise UserError(
                    f"No se puede cancelar el contrato con {self.pending_invoices} facturas pendientes "
                    f"por valor de ${self.pending_amount:,.2f}. Contacte al administrador."
                )

    @api.onchange('extend_months')
    def _onchange_extend_months(self):
        """Calcular nueva fecha de fin al cambiar meses"""
        if self.extend_months and self.current_end_date:
            self.new_end_date = self.current_end_date + relativedelta(months=self.extend_months)

    @api.onchange('rental_increase_percentage', 'current_rental_fee')
    def _onchange_rental_increase(self):
        """Calcular nuevo canon por porcentaje"""
        if self.rental_increase_percentage and self.current_rental_fee:
            self.new_rental_fee = self.current_rental_fee * (1 + self.rental_increase_percentage / 100)

    def action_execute_operation(self):
        """Ejecutar la operación seleccionada (como Asset.modify)"""
        self.ensure_one()

        # Validaciones según la acción
        if self.modify_action in ['extend', 'renew'] and not self.new_end_date:
            raise ValidationError(_("Debe especificar la nueva fecha de fin"))

        if self.modify_action == 'modify_amount' and not self.new_rental_fee:
            raise ValidationError(_("Debe especificar el nuevo valor del canon"))

        if self.modify_action == 'cancel' and not self.cancellation_type:
            raise ValidationError(_("Debe especificar el tipo de cancelación"))

        # Ejecutar según tipo
        if self.modify_action in ['extend', 'modify_amount', 'modify_dates']:
            return self._modify_contract()
        elif self.modify_action == 'renew':
            return self._renew_contract()
        elif self.modify_action == 'cancel':
            return self._cancel_contract()
        elif self.modify_action == 'pause':
            return self._pause_contract()
        elif self.modify_action == 'resume':
            return self._resume_contract()

        return {'type': 'ir.actions.act_window_close'}

    def _modify_contract(self):
        """Modificar contrato actual (como Asset.modify)"""
        contract = self.contract_id

        # Validaciones antes de modificar
        if self.date <= fields.Date.today() and self.modify_action == 'modify_amount':
            # Verificar que no hay líneas futuras ya facturadas
            future_invoiced = contract.loan_line_ids.filtered(
                lambda l: l.date >= self.date and l.invoice_id and l.invoice_id.state == 'posted'
            )
            if future_invoiced:
                raise UserError(_('Hay facturas ya emitidas para fechas futuras. No se puede modificar.'))

        # Guardar valores anteriores para tracking
        old_values = {
            'rental_fee': contract.rental_fee,
            'date_to': contract.date_to,
        }

        # Eliminar líneas futuras no pagadas (como Asset)
        future_lines = contract.loan_line_ids.filtered(
            lambda l: l.date >= self.date and l.payment_state != 'paid'
        )
        future_lines.unlink()

        # Aplicar cambios al contrato
        contract_vals = {}

        if self.modify_action == 'extend':
            contract_vals['date_to'] = self.new_end_date
        elif self.modify_action == 'modify_amount':
            contract_vals['rental_fee'] = self.new_rental_fee
        elif self.modify_action == 'modify_dates':
            if self.new_end_date:
                contract_vals['date_to'] = self.new_end_date

        contract.write(contract_vals)

        # Recalcular líneas de pago (como compute_depreciation_board)
        contract.prepare_lines()

        # Log en chatter con tracking (como Asset)
        changes_text = []
        if 'rental_fee' in contract_vals:
            changes_text.append(f"Canon: ${old_values['rental_fee']:,.2f} → ${contract_vals['rental_fee']:,.2f}")
        if 'date_to' in contract_vals:
            changes_text.append(f"Fecha fin: {old_values['date_to']} → {contract_vals['date_to']}")

        contract.message_post(
            body=_(
                "Contrato modificado - %(action)s<br/>"
                "Cambios: %(changes)s<br/>"
                "Motivo: %(reason)s",
                action=dict(self._get_selection_modify_options()).get(self.modify_action),
                changes="<br/>".join(changes_text),
                reason=self.reason
            )
        )

        return {'type': 'ir.actions.act_window_close'}

    def _renew_contract(self):
        """Crear renovación del contrato (como Asset copy)"""
        old_contract = self.contract_id

        # Preparar valores para copia
        copy_values = {
            'name': 'New',
            'date_from': old_contract.date_to + relativedelta(days=1),
            'date_to': self.new_end_date,
            'rental_fee': self.new_rental_fee or old_contract.rental_fee,
            'origin': f"Renovación de {old_contract.name}",
            'state': 'draft'
        }

        # Mantener condiciones según selección
        if not self.copy_conditions:
            copy_values.update({
                'apply_interest': False,
                'increment_percentage': 0,
            })

        new_contract = old_contract.copy(copy_values)
        new_contract.prepare_lines()

        # Log en ambos contratos
        old_contract.message_post(
            body=f"Contrato renovado. Nuevo contrato: {new_contract.name}. Motivo: {self.reason}"
        )
        new_contract.message_post(
            body=f"Contrato creado por renovación de {old_contract.name}. Motivo: {self.reason}"
        )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'property.contract',
            'res_id': new_contract.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def _cancel_contract(self):
        """Cancelar contrato (como Asset sell_dispose)"""
        contract = self.contract_id

        # Aplicar penalidad si corresponde
        if self.apply_penalty and self.penalty_amount:
            # Crear línea de penalidad
            penalty_line = self.env['loan.line'].create({
                'name': f"Penalidad por cancelación - {contract.name}",
                'contract_id': contract.id,
                'amount': self.penalty_amount,
                'date': self.date,
                'serial': 999,  # Número especial para penalidades
            })

        # Cancelar líneas futuras
        future_lines = contract.loan_line_ids.filtered(
            lambda l: l.date > self.date and l.payment_state != 'paid'
        )
        future_lines.unlink()

        # Cambiar estado
        contract.write({
            'state': 'cancel',
            'date_end': self.date
        })

        # Liberar propiedad
        contract.property_id.write({'state': 'free'})

        # Log detallado
        cancellation_types = dict(self._fields['cancellation_type'].selection)
        reason_text = cancellation_types.get(self.cancellation_type, 'No especificado')

        message = f"CONTRATO CANCELADO - {reason_text}"
        if self.apply_penalty:
            message += f" - Penalidad: ${self.penalty_amount:,.2f}"

        contract.message_post(
            body=f"{message}<br/>Motivo: {self.reason}<br/>Ejecutado por: {self.env.user.name}"
        )

        return {'type': 'ir.actions.act_window_close'}

    def _pause_contract(self):
        """Suspender contrato (como Asset.pause)"""
        contract = self.contract_id

        # Pausar líneas en el período de suspensión
        suspended_lines = contract.loan_line_ids.filtered(
            lambda l: self.suspension_start <= l.date <= self.suspension_end and l.payment_state != 'paid'
        )

        # Marcar líneas como pausadas (agregar campo si es necesario)
        suspended_lines.write({'active': False})

        contract.write({'state': 'draft'})  # O crear estado 'suspended' si es necesario

        contract.message_post(
            body=f"Contrato SUSPENDIDO del {self.suspension_start.strftime('%d/%m/%Y')} al {self.suspension_end.strftime('%d/%m/%Y')}.<br/>Motivo: {self.reason}"
        )

        return {'type': 'ir.actions.act_window_close'}

    def _resume_contract(self):
        """Reactivar contrato (como Asset.resume)"""
        contract = self.contract_id

        # Reactivar líneas pausadas
        paused_lines = contract.loan_line_ids.filtered(lambda l: not l.active)
        paused_lines.write({'active': True})

        contract.write({'state': 'confirmed'})

        # Recalcular líneas desde la fecha de reactivación
        contract.prepare_lines()

        contract.message_post(
            body=f"Contrato REACTIVADO desde {self.date.strftime('%d/%m/%Y')}.<br/>Motivo: {self.reason}"
        )

        return {'type': 'ir.actions.act_window_close'}

    @api.model_create_multi
    def create(self, vals_list):
        """Inicializar valores como Asset"""
        for vals in vals_list:
            if 'contract_id' in vals:
                contract = self.env['property.contract'].browse(vals['contract_id'])
                if 'new_rental_fee' not in vals:
                    vals.update({'new_rental_fee': contract.rental_fee})
                if 'new_end_date' not in vals:
                    vals.update({'new_end_date': contract.date_to})
        return super().create(vals_list)

    def modify(self):
        """Método principal de modificación (como Asset)"""
        return self.action_execute_operation()

    def pause(self):
        """Pausar contrato (como Asset)"""
        return self._pause_contract()

    def sell_dispose(self):
        """Cancelar contrato (como Asset)"""
        return self._cancel_contract()
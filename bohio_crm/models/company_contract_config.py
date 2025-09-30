# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta

class CompanyContractConfig(models.Model):
    _name = 'company.contract.config'
    _description = 'Configuración de Contratos por Empresa'
    _rec_name = 'display_name'

    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

    # COMISIONES BASE
    default_commission_percentage = fields.Float(
        'Comisión Base (%)',
        default=8.0,
        help='Porcentaje de comisión por defecto para nuevos contratos'
    )
    commission_calculation_method = fields.Selection([
        ('gross_amount', 'Sobre Monto Bruto'),
        ('net_amount', 'Sobre Monto Neto'),
        ('rental_fee_only', 'Solo Canon (sin seguros)')
    ], string='Método Cálculo Comisión', default='gross_amount')

    # INTERESES BASE
    default_interest_rate = fields.Float(
        'Tasa Interés Base (%)',
        default=1.5,
        help='Tasa de interés mensual por mora por defecto'
    )
    default_grace_days = fields.Integer(
        'Días Gracia Base',
        default=5,
        help='Días de gracia por defecto antes de aplicar intereses'
    )
    auto_calculate_interest = fields.Boolean(
        'Calcular Intereses Automáticamente',
        default=True,
        help='Si está activo, calcula intereses automáticamente al vencer cuotas'
    )

    # INCREMENTOS BASE
    default_increment_percentage = fields.Float(
        'Incremento Anual Base (%)',
        default=4.0,
        help='Porcentaje de incremento anual por defecto'
    )

    # PERIODICIDAD BASE
    default_periodicity = fields.Selection([
        ('1', 'Mensual'),
        ('3', 'Trimestral'),
        ('6', 'Semestral'),
        ('12', 'Anual')
    ], default='1', string='Periodicidad Base')

    # CONFIGURACIONES ADICIONALES
    auto_apply_to_new_contracts = fields.Boolean(
        'Aplicar Automáticamente',
        default=True,
        help='Aplica esta configuración automáticamente a contratos nuevos'
    )

    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('company_id.name', 'default_commission_percentage', 'default_interest_rate')
    def _compute_display_name(self):
        for config in self:
            config.display_name = f"{config.company_id.name} - Com: {config.default_commission_percentage}% - Int: {config.default_interest_rate}%"

    _sql_constraints = [
        ('company_unique', 'unique(company_id)', 'Solo puede haber una configuración por empresa'),
    ]

    @api.model
    def get_company_defaults(self, company_id=None):
        """Obtener configuración por defecto de la empresa"""
        if not company_id:
            company_id = self.env.company.id

        config = self.search([('company_id', '=', company_id)], limit=1)
        if not config:
            # Crear configuración por defecto si no existe
            config = self.create({'company_id': company_id})

        return {
            'commission_percentage': config.default_commission_percentage,
            'interest_rate': config.default_interest_rate,
            'grace_days': config.default_grace_days,
            'increment_percentage': config.default_increment_percentage,
            'periodicity': config.default_periodicity,
            'commission_method': config.commission_calculation_method,
            'auto_interest': config.auto_calculate_interest,
        }

    @api.constrains('default_commission_percentage', 'default_interest_rate')
    def _check_percentages(self):
        for config in self:
            if config.default_commission_percentage < 0 or config.default_commission_percentage > 100:
                raise ValidationError(_('La comisión debe estar entre 0% y 100%'))
            if config.default_interest_rate < 0 or config.default_interest_rate > 50:
                raise ValidationError(_('La tasa de interés debe estar entre 0% y 50%'))

    def action_apply_to_all_contracts(self):
        """Aplicar configuración a todos los contratos de la empresa"""
        self.ensure_one()

        contracts = self.env['property.contract'].search([
            ('company_id', '=', self.company_id.id),
            ('state', 'in', ['draft', 'active'])
        ])

        if not contracts:
            raise UserError(_('No hay contratos activos o en borrador para actualizar.'))

        updated_count = 0
        for contract in contracts:
            contract.write({
                'commission_percentage': self.default_commission_percentage,
                'interest_rate': self.default_interest_rate,
                'grace_days': self.default_grace_days,
            })
            updated_count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Actualización Completada'),
                'message': _('Se actualizaron %s contratos con la nueva configuración.') % updated_count,
                'type': 'success',
                'sticky': False,
            }
        }

class ResCompany(models.Model):
    _inherit = 'res.company'

    contract_config_ids = fields.One2many(
        'company.contract.config',
        'company_id',
        string='Configuración de Contratos'
    )

    def get_contract_defaults(self):
        """Método rápido para obtener defaults de contrato"""
        return self.env['company.contract.config'].get_company_defaults(self.id)

class ModifyContractWizard(models.TransientModel):
    _name = 'modify.contract.wizard'
    _description = 'Modificar Contrato - Wizard Unificado'

    contract_id = fields.Many2one('property.contract', required=True)

    # Tipo de modificación
    operation_type = fields.Selection([
        ('extend', 'Extender Contrato'),
        ('renew', 'Renovar (Nueva Copia)'),
        ('modify_amount', 'Cambiar Monto'),
        ('modify_dates', 'Cambiar Fechas'),
        ('cancel', 'Cancelar Contrato'),
        ('suspend', 'Suspender Temporalmente'),
        ('reactivate', 'Reactivar'),
    ], string='Tipo de Operación', required=True, default='extend')

    # Campos comunes
    reason = fields.Text('Motivo/Observaciones', required=True)
    effective_date = fields.Date('Fecha Efectiva', default=fields.Date.today, required=True)

    # Para extensión/renovación
    new_end_date = fields.Date('Nueva Fecha de Fin')
    extend_months = fields.Integer('Extender por Meses', default=12)
    new_rental_fee = fields.Float('Nuevo Canon')

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

    # Información actual del contrato
    current_end_date = fields.Date(related='contract_id.date_to', readonly=True)
    current_rental_fee = fields.Float(related='contract_id.rental_fee', readonly=True)
    pending_amount = fields.Float('Monto Pendiente', compute='_compute_pending_info')
    pending_invoices = fields.Integer('Facturas Pendientes', compute='_compute_pending_info')

    @api.depends('contract_id.loan_line_ids.payment_state', 'contract_id.loan_line_ids.amount')
    def _compute_pending_info(self):
        for wizard in self:
            pending_lines = wizard.contract_id.loan_line_ids.filtered(
                lambda l: l.payment_state != 'paid'
            )
            wizard.pending_invoices = len(pending_lines)
            wizard.pending_amount = sum(pending_lines.mapped('amount'))

    @api.onchange('operation_type')
    def _onchange_operation_type(self):
        """Limpiar campos según operación seleccionada"""
        if self.operation_type == 'extend':
            self.new_end_date = self.current_end_date + relativedelta(months=self.extend_months)
        elif self.operation_type == 'modify_amount':
            self.new_rental_fee = self.current_rental_fee

    @api.onchange('extend_months')
    def _onchange_extend_months(self):
        if self.extend_months and self.current_end_date:
            self.new_end_date = self.current_end_date + relativedelta(months=self.extend_months)

    def action_execute_operation(self):
        """Ejecutar la operación seleccionada"""
        self.ensure_one()

        # Validaciones generales
        if self.operation_type == 'cancel' and self.pending_invoices > 0:
            if not self.env.user.has_group('base.group_system'):
                raise UserError(
                    f"No se puede cancelar el contrato con {self.pending_invoices} facturas pendientes "
                    f"por valor de ${self.pending_amount:,.2f}. Contacte al administrador."
                )

        # Ejecutar según tipo
        if self.operation_type == 'extend':
            return self._execute_extend()
        elif self.operation_type == 'renew':
            return self._execute_renew()
        elif self.operation_type == 'modify_amount':
            return self._execute_modify_amount()
        elif self.operation_type == 'cancel':
            return self._execute_cancel()

        return {'type': 'ir.actions.act_window_close'}

    def _execute_extend(self):
        """Extender contrato actual"""
        self.contract_id.write({'date_to': self.new_end_date})
        self.contract_id.prepare_lines()

        self.contract_id.message_post(
            body=f"Contrato extendido hasta {self.new_end_date.strftime('%d/%m/%Y')}. Motivo: {self.reason}"
        )

        return {'type': 'ir.actions.act_window_close'}

    def _execute_renew(self):
        """Crear renovación del contrato"""
        old_contract = self.contract_id

        # Crear copia con nuevas fechas
        new_contract = old_contract.copy({
            'name': 'New',
            'date_from': old_contract.date_to + relativedelta(days=1),
            'date_to': self.new_end_date,
            'rental_fee': self.new_rental_fee or old_contract.rental_fee,
            'origin': f"Renovación de {old_contract.name}",
            'state': 'draft'
        })

        new_contract.prepare_lines()

        # Log en ambos contratos
        old_contract.message_post(
            body=f"Contrato renovado. Nuevo contrato: {new_contract.name}. Motivo: {self.reason}"
        )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'property.contract',
            'res_id': new_contract.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def _execute_modify_amount(self):
        """Modificar monto del contrato"""
        old_amount = self.contract_id.rental_fee
        self.contract_id.write({'rental_fee': self.new_rental_fee})

        # Regenerar líneas futuras
        future_lines = self.contract_id.loan_line_ids.filtered(
            lambda l: l.date >= self.effective_date and l.payment_state != 'paid'
        )
        future_lines.unlink()
        self.contract_id.prepare_lines()

        self.contract_id.message_post(
            body=f"Canon modificado: ${old_amount:,.2f} → ${self.new_rental_fee:,.2f} desde {self.effective_date.strftime('%d/%m/%Y')}. Motivo: {self.reason}"
        )

        return {'type': 'ir.actions.act_window_close'}

    def _execute_cancel(self):
        """Cancelar contrato"""
        # Aplicar penalidad si corresponde
        if self.apply_penalty and self.penalty_amount:
            # Crear línea de penalidad
            penalty_line = self.env['loan.line'].create({
                'name': f"Penalidad por cancelación - {self.contract_id.name}",
                'contract_id': self.contract_id.id,
                'amount': self.penalty_amount,
                'date': self.effective_date,
                'serial': 999,  # Número especial para penalidades
            })

        # Cancelar líneas futuras
        future_lines = self.contract_id.loan_line_ids.filtered(
            lambda l: l.date > self.effective_date and l.payment_state != 'paid'
        )
        future_lines.unlink()

        # Cambiar estado
        self.contract_id.write({
            'state': 'cancel',
            'date_end': self.effective_date
        })

        # Liberar propiedad
        self.contract_id.property_id.write({'state': 'free'})

        cancellation_types = dict(self._fields['cancellation_type'].selection)
        reason_text = cancellation_types.get(self.cancellation_type, 'No especificado')

        message = f"CONTRATO CANCELADO - {reason_text}"
        if self.apply_penalty:
            message += f" - Penalidad: ${self.penalty_amount:,.2f}"

        self.contract_id.message_post(
            body=f"{message}<br/>Motivo: {self.reason}"
        )

        return {'type': 'ir.actions.act_window_close'}
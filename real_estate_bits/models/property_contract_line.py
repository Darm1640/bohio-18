from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class PropertyContractLine(models.Model):
    _name = "property.contract.line"
    _description = "Línea de Contrato Multi-Propiedad"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, date_from"

    # INFORMACIÓN BÁSICA
    name = fields.Char('Descripción', compute='_compute_name', store=True)
    sequence = fields.Integer('Secuencia', default=10)
    contract_id = fields.Many2one('property.contract', 'Contrato Principal', required=True, ondelete='cascade')

    # PROPIEDAD Y FECHAS
    property_id = fields.Many2one('product.template', 'Propiedad', required=True,
                                  domain=[("is_property", "=", True)])
    date_from = fields.Date('Fecha Inicio', required=True, tracking=True)
    date_to = fields.Date('Fecha Fin', required=True, tracking=True)
    date_end_real = fields.Date('Fecha Terminación Real',
                               help='Fecha real cuando terminó esta línea de contrato')

    # MONTOS
    rental_fee = fields.Float('Canon Individual', digits='Product Price', required=True)
    rental_fee_percentage = fields.Float('% del Total', compute='_compute_rental_percentage', store=True,
                                        help='Porcentaje que representa del canon total del contrato')

    # ESTADO
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('active', 'Activa'),
        ('terminated', 'Terminada'),
        ('cancelled', 'Cancelada')
    ], string='Estado', default='draft', tracking=True)

    # CONFIGURACIÓN ESPECÍFICA
    apply_increment = fields.Boolean('Aplicar Incrementos', default=True,
                                    help='Si aplicar incrementos anuales a esta línea')
    prorate_on_changes = fields.Boolean('Prorratear Cambios', default=True,
                                       help='Si prorratear cuando hay cambios en fechas')

    # CAMPOS RELACIONADOS PARA FACILIDAD
    project_id = fields.Many2one('project.worksite', related='property_id.project_worksite_id',
                                 string='Proyecto', store=True)
    property_code = fields.Char('Código Propiedad', related='property_id.default_code', store=True)
    property_area = fields.Float('Área m²', related='property_id.property_area', store=True)
    region_id = fields.Many2one('region.region', related='property_id.region_id', store=True)

    # INFORMACIÓN DE TERMINACIÓN
    termination_reason = fields.Selection([
        ('contract_end', 'Fin de Contrato'),
        ('early_termination', 'Terminación Anticipada'),
        ('non_payment', 'Falta de Pago'),
        ('property_sale', 'Venta de Propiedad'),
        ('other', 'Otro Motivo')
    ], string='Motivo de Terminación')
    termination_notes = fields.Text('Notas de Terminación')

    @api.depends('property_id', 'rental_fee', 'date_from', 'date_to')
    def _compute_name(self):
        for line in self:
            if line.property_id:
                line.name = f"{line.property_id.name} ({line.date_from} - {line.date_to})"
            else:
                line.name = "Nueva Línea de Contrato"

    @api.depends('rental_fee', 'contract_id.contract_line_ids.rental_fee')
    def _compute_rental_percentage(self):
        for line in self:
            total_rental = sum(line.contract_id.contract_line_ids.mapped('rental_fee'))
            if total_rental > 0:
                line.rental_fee_percentage = (line.rental_fee / total_rental) * 100
            else:
                line.rental_fee_percentage = 0.0

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for line in self:
            if line.date_from >= line.date_to:
                raise ValidationError(_('La fecha de inicio debe ser menor que la fecha de fin'))

            # Verificar que las fechas estén dentro del rango del contrato principal
            contract = line.contract_id
            if contract.date_from and line.date_from < contract.date_from:
                raise ValidationError(_('La fecha de inicio de la línea no puede ser anterior al inicio del contrato'))

            if contract.date_to and line.date_to > contract.date_to:
                raise ValidationError(_('La fecha de fin de la línea no puede ser posterior al fin del contrato'))

    @api.constrains('rental_fee')
    def _check_rental_fee(self):
        for line in self:
            if line.rental_fee <= 0:
                raise ValidationError(_('El canon debe ser mayor a cero'))

    @api.onchange('property_id')
    def _onchange_property_id(self):
        if self.property_id:
            # Auto-completar con el canon sugerido de la propiedad
            self.rental_fee = self.property_id.rent_value_from or 0.0

            # Auto-completar fechas si están vacías
            if not self.date_from and self.contract_id.date_from:
                self.date_from = self.contract_id.date_from

            if not self.date_to and self.contract_id.date_to:
                self.date_to = self.contract_id.date_to

    def action_terminate_line(self):
        """Terminar esta línea de contrato"""
        self.ensure_one()
        if self.state != 'active':
            raise UserError(_('Solo se pueden terminar líneas activas'))

        return {
            'name': _('Terminar Línea de Contrato'),
            'type': 'ir.actions.act_window',
            'res_model': 'property.contract.line.termination.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_contract_line_id': self.id,
                'default_termination_date': fields.Date.today(),
            }
        }

    def action_extend_line(self):
        """Extender esta línea de contrato"""
        self.ensure_one()
        return {
            'name': _('Extender Línea de Contrato'),
            'type': 'ir.actions.act_window',
            'res_model': 'property.contract.line.extension.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_contract_line_id': self.id,
                'default_new_end_date': self.date_to + relativedelta(months=6),
            }
        }

    def terminate_line(self, termination_date, reason, notes=""):
        """Método para terminar la línea y ajustar cuotas futuras"""
        self.ensure_one()

        if termination_date <= self.date_from:
            raise UserError(_('La fecha de terminación debe ser posterior al inicio de la línea'))

        # Actualizar la línea
        self.write({
            'date_end_real': termination_date,
            'state': 'terminated',
            'termination_reason': reason,
            'termination_notes': notes,
        })

        # Notificar al contrato para recalcular cuotas
        self.contract_id._recalculate_future_installments_on_line_change()

        # Log en el chatter
        self.message_post(
            body=_('Línea terminada el %s. Motivo: %s') % (
                termination_date.strftime('%d/%m/%Y'),
                dict(self._fields['termination_reason'].selection).get(reason, reason)
            )
        )

    @api.model
    def create(self, vals):
        line = super().create(vals)
        # Activar automáticamente si el contrato está confirmado
        if line.contract_id.state == 'confirmed':
            line.state = 'active'
        return line

    def write(self, vals):
        result = super().write(vals)
        # Si se modifica rental_fee, recalcular cuotas del contrato
        if 'rental_fee' in vals and self.contract_id.state == 'confirmed':
            self.contract_id._recalculate_future_installments_on_line_change()
        return result


class PropertyContractLineTerminationWizard(models.TransientModel):
    _name = 'property.contract.line.termination.wizard'
    _description = 'Wizard para Terminar Línea de Contrato'

    contract_line_id = fields.Many2one('property.contract.line', 'Línea de Contrato', required=True)
    termination_date = fields.Date('Fecha de Terminación', required=True, default=fields.Date.today)
    termination_reason = fields.Selection([
        ('contract_end', 'Fin de Contrato'),
        ('early_termination', 'Terminación Anticipada'),
        ('non_payment', 'Falta de Pago'),
        ('property_sale', 'Venta de Propiedad'),
        ('other', 'Otro Motivo')
    ], string='Motivo', required=True)
    notes = fields.Text('Observaciones')

    # INFORMACIÓN CALCULADA
    current_rental_fee = fields.Float('Canon Actual', related='contract_line_id.rental_fee', readonly=True)
    total_contract_rental = fields.Float('Canon Total Contrato', compute='_compute_contract_totals', readonly=True)
    remaining_rental_after = fields.Float('Canon Restante Después', compute='_compute_contract_totals', readonly=True)

    @api.depends('contract_line_id', 'termination_date')
    def _compute_contract_totals(self):
        for wizard in self:
            if wizard.contract_line_id:
                contract = wizard.contract_line_id.contract_id
                wizard.total_contract_rental = sum(contract.contract_line_ids.mapped('rental_fee'))
                wizard.remaining_rental_after = wizard.total_contract_rental - wizard.current_rental_fee
            else:
                wizard.total_contract_rental = 0.0
                wizard.remaining_rental_after = 0.0

    def action_terminate(self):
        """Ejecutar la terminación"""
        self.ensure_one()

        # Validaciones
        if self.termination_date < self.contract_line_id.date_from:
            raise UserError(_('La fecha de terminación no puede ser anterior al inicio de la línea'))

        if self.termination_date > fields.Date.today():
            raise UserError(_('La fecha de terminación no puede ser futura'))

        # Terminar la línea
        self.contract_line_id.terminate_line(
            self.termination_date,
            self.termination_reason,
            self.notes
        )

        return {'type': 'ir.actions.act_window_close'}


class PropertyContractLineExtensionWizard(models.TransientModel):
    _name = 'property.contract.line.extension.wizard'
    _description = 'Wizard para Extender Línea de Contrato'

    contract_line_id = fields.Many2one('property.contract.line', 'Línea de Contrato', required=True)
    new_end_date = fields.Date('Nueva Fecha de Fin', required=True)
    adjust_rental_fee = fields.Boolean('Ajustar Canon', default=False)
    new_rental_fee = fields.Float('Nuevo Canon', digits='Product Price')

    @api.onchange('contract_line_id')
    def _onchange_contract_line(self):
        if self.contract_line_id:
            self.new_rental_fee = self.contract_line_id.rental_fee

    def action_extend(self):
        """Ejecutar la extensión"""
        self.ensure_one()

        if self.new_end_date <= self.contract_line_id.date_to:
            raise UserError(_('La nueva fecha de fin debe ser posterior a la actual'))

        # Actualizar la línea
        update_vals = {'date_to': self.new_end_date}
        if self.adjust_rental_fee:
            update_vals['rental_fee'] = self.new_rental_fee

        self.contract_line_id.write(update_vals)

        # Log en el chatter
        self.contract_line_id.message_post(
            body=_('Línea extendida hasta %s') % self.new_end_date.strftime('%d/%m/%Y')
        )

        return {'type': 'ir.actions.act_window_close'}


class PropertyContract(models.Model):
    _inherit = 'property.contract'

    # NUEVOS CAMPOS PARA MULTI-PROPIEDAD
    is_multi_property = fields.Boolean('Contrato Multi-Propiedad', default=False, tracking=True,
                                      help='Si está activo, el contrato puede manejar múltiples propiedades')
    contract_line_ids = fields.One2many('property.contract.line', 'contract_id',
                                       string='Líneas de Propiedades')

    # TOTALES CALCULADOS
    total_rental_fee = fields.Float('Canon Total Calculado', compute='_compute_multi_totals', store=True,
                                   help='Suma de todos los cánones de las líneas activas')
    active_properties_count = fields.Integer('Propiedades Activas', compute='_compute_multi_totals', store=True)
    terminated_properties_count = fields.Integer('Propiedades Terminadas', compute='_compute_multi_totals', store=True)

    @api.depends('contract_line_ids.rental_fee', 'contract_line_ids.state')
    def _compute_multi_totals(self):
        for contract in self:
            active_lines = contract.contract_line_ids.filtered(lambda l: l.state == 'active')
            contract.total_rental_fee = sum(active_lines.mapped('rental_fee'))
            contract.active_properties_count = len(active_lines)
            contract.terminated_properties_count = len(
                contract.contract_line_ids.filtered(lambda l: l.state == 'terminated')
            )

    @api.depends('is_multi_property', 'total_rental_fee', 'rental_fee')
    def _compute_rental_fee(self):
        """Override del método original para considerar multi-propiedad"""
        for rec in self:
            if rec.is_multi_property:
                # Usar el total calculado de las líneas
                rec.rental_fee = rec.total_rental_fee
            else:
                # Usar el método original
                rec.rental_fee = rec.property_id.rent_value_from

    @api.onchange('is_multi_property')
    def _onchange_is_multi_property(self):
        if self.is_multi_property and not self.contract_line_ids:
            # Si se activa multi-propiedad y hay una propiedad principal, crear primera línea
            if self.property_id:
                self.contract_line_ids = [(0, 0, {
                    'property_id': self.property_id.id,
                    'date_from': self.date_from,
                    'date_to': self.date_to,
                    'rental_fee': self.rental_fee or self.property_id.rent_value_from,
                    'state': 'active' if self.state == 'confirmed' else 'draft',
                })]

    def action_add_property_line(self):
        """Agregar nueva línea de propiedad"""
        self.ensure_one()
        if not self.is_multi_property:
            raise UserError(_('Debe activar "Contrato Multi-Propiedad" primero'))

        return {
            'name': _('Agregar Propiedad al Contrato'),
            'type': 'ir.actions.act_window',
            'res_model': 'property.contract.add.line.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_contract_id': self.id,
                'default_date_from': self.date_from,
                'default_date_to': self.date_to,
            }
        }

    def action_terminate_property_line(self):
        """Terminar línea de propiedad específica"""
        self.ensure_one()
        return {
            'name': _('Terminar Propiedad del Contrato'),
            'type': 'ir.actions.act_window',
            'res_model': 'property.contract.terminate.line.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_contract_id': self.id}
        }

    def _recalculate_future_installments_on_line_change(self):
        """Recalcular cuotas futuras cuando cambia una línea"""
        self.ensure_one()

        if self.state != 'confirmed':
            return

        # Encontrar la fecha de corte (primera cuota no pagada o hoy)
        cutoff_date = fields.Date.today()
        first_unpaid = self.loan_line_ids.filtered(
            lambda l: l.payment_state != 'paid'
        ).sorted('date')

        if first_unpaid:
            cutoff_date = first_unpaid[0].date

        # Eliminar cuotas futuras
        future_lines = self.loan_line_ids.filtered(
            lambda l: l.date >= cutoff_date and l.payment_state != 'paid'
        )
        future_lines.unlink()

        # Recalcular usando el nuevo canon total
        self.prepare_lines()

        # Log del cambio
        self.message_post(
            body=_('Canon recalculado automáticamente. Nuevo total: %s') %
                 self.env.company.currency_id.format(self.total_rental_fee)
        )

    def prepare_lines(self):
        """Override para considerar contratos multi-propiedad"""
        if not self.is_multi_property:
            # Usar el método original
            return super().prepare_lines()

        # Para contratos multi-propiedad, usar el canon total calculado
        original_rental_fee = self.rental_fee
        self.rental_fee = self.total_rental_fee
        result = super().prepare_lines()
        self.rental_fee = original_rental_fee  # Restaurar valor original
        return result

    def action_confirm(self):
        """Override para activar líneas al confirmar"""
        result = super().action_confirm()

        # Activar líneas de contrato
        for line in self.contract_line_ids:
            if line.state == 'draft':
                line.state = 'active'

        return result

    def action_cancel(self):
        """Override para cancelar líneas"""
        result = super().action_cancel()

        # Cancelar líneas de contrato
        self.contract_line_ids.write({'state': 'cancelled'})

        return result


class PropertyContractAddLineWizard(models.TransientModel):
    _name = 'property.contract.add.line.wizard'
    _description = 'Wizard para Agregar Propiedad al Contrato'

    contract_id = fields.Many2one('property.contract', 'Contrato', required=True)
    property_id = fields.Many2one('product.template', 'Propiedad', required=True,
                                  domain=[("is_property", "=", True), ("state", "=", "free")])

    # FECHAS
    date_from = fields.Date('Fecha Inicio', required=True)
    date_to = fields.Date('Fecha Fin', required=True)

    # CONFIGURACIÓN DE CANON
    calculation_method = fields.Selection([
        ('property_default', 'Canon Sugerido de la Propiedad'),
        ('manual_amount', 'Monto Manual'),
        ('percentage_of_contract', 'Porcentaje del Contrato Principal')
    ], string='Método de Cálculo', default='property_default', required=True)

    manual_rental_fee = fields.Float('Canon Manual', digits='Product Price')
    percentage_of_contract = fields.Float('Porcentaje (%)', default=0.0,
                                         help='Porcentaje del canon del contrato principal')

    # CAMPOS CALCULADOS
    suggested_rental_fee = fields.Float('Canon Sugerido', compute='_compute_suggested_rental', readonly=True)
    final_rental_fee = fields.Float('Canon Final', compute='_compute_final_rental', readonly=True)

    @api.depends('property_id')
    def _compute_suggested_rental(self):
        for wizard in self:
            if wizard.property_id:
                wizard.suggested_rental_fee = wizard.property_id.rent_value_from or 0.0
            else:
                wizard.suggested_rental_fee = 0.0

    @api.depends('calculation_method', 'manual_rental_fee', 'percentage_of_contract',
                 'suggested_rental_fee', 'contract_id.rental_fee')
    def _compute_final_rental(self):
        for wizard in self:
            if wizard.calculation_method == 'property_default':
                wizard.final_rental_fee = wizard.suggested_rental_fee
            elif wizard.calculation_method == 'manual_amount':
                wizard.final_rental_fee = wizard.manual_rental_fee
            elif wizard.calculation_method == 'percentage_of_contract':
                base_rental = wizard.contract_id.rental_fee or 0.0
                wizard.final_rental_fee = base_rental * (wizard.percentage_of_contract / 100)
            else:
                wizard.final_rental_fee = 0.0

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for wizard in self:
            if wizard.date_from >= wizard.date_to:
                raise ValidationError(_('La fecha de inicio debe ser menor que la fecha de fin'))

    def action_add_line(self):
        """Agregar la línea al contrato"""
        self.ensure_one()

        # Validar que la propiedad esté disponible
        if self.property_id.state != 'free':
            raise UserError(_('La propiedad seleccionada no está disponible'))

        # Crear la línea
        line_vals = {
            'contract_id': self.contract_id.id,
            'property_id': self.property_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'rental_fee': self.final_rental_fee,
            'state': 'active' if self.contract_id.state == 'confirmed' else 'draft',
        }

        line = self.env['property.contract.line'].create(line_vals)

        # Marcar propiedad como ocupada
        if self.contract_id.state == 'confirmed':
            self.property_id.write({'state': 'on_lease'})

        # Recalcular cuotas del contrato si está confirmado
        if self.contract_id.state == 'confirmed':
            self.contract_id._recalculate_future_installments_on_line_change()

        # Log en el contrato
        self.contract_id.message_post(
            body=_('Nueva propiedad agregada: %s (Canon: %s)') % (
                self.property_id.name,
                self.env.company.currency_id.format(self.final_rental_fee)
            )
        )

        return {'type': 'ir.actions.act_window_close'}


class PropertyContractTerminateLineWizard(models.TransientModel):
    _name = 'property.contract.terminate.line.wizard'
    _description = 'Wizard para Terminar Línea Específica'

    contract_id = fields.Many2one('property.contract', 'Contrato', required=True)
    contract_line_id = fields.Many2one('property.contract.line', 'Línea a Terminar', required=True,
                                       domain="[('contract_id', '=', contract_id), ('state', '=', 'active')]")

    termination_date = fields.Date('Fecha de Terminación', required=True, default=fields.Date.today)
    termination_reason = fields.Selection([
        ('contract_end', 'Fin de Contrato'),
        ('early_termination', 'Terminación Anticipada'),
        ('non_payment', 'Falta de Pago'),
        ('property_sale', 'Venta de Propiedad'),
        ('other', 'Otro Motivo')
    ], string='Motivo', required=True)
    notes = fields.Text('Observaciones')

    # VISTA PREVIA DEL IMPACTO
    current_total_rental = fields.Float('Canon Total Actual', compute='_compute_impact', readonly=True)
    rental_after_termination = fields.Float('Canon Después de Terminación', compute='_compute_impact', readonly=True)
    impact_amount = fields.Float('Impacto en Canon', compute='_compute_impact', readonly=True)
    impact_percentage = fields.Float('% de Impacto', compute='_compute_impact', readonly=True)

    @api.depends('contract_line_id', 'contract_id')
    def _compute_impact(self):
        for wizard in self:
            if wizard.contract_id and wizard.contract_line_id:
                wizard.current_total_rental = wizard.contract_id.total_rental_fee
                wizard.impact_amount = wizard.contract_line_id.rental_fee
                wizard.rental_after_termination = wizard.current_total_rental - wizard.impact_amount

                if wizard.current_total_rental > 0:
                    wizard.impact_percentage = (wizard.impact_amount / wizard.current_total_rental) * 100
                else:
                    wizard.impact_percentage = 0.0
            else:
                wizard.current_total_rental = 0.0
                wizard.rental_after_termination = 0.0
                wizard.impact_amount = 0.0
                wizard.impact_percentage = 0.0

    def action_terminate_line(self):
        """Terminar la línea seleccionada"""
        self.ensure_one()

        # Ejecutar terminación
        self.contract_line_id.terminate_line(
            self.termination_date,
            self.termination_reason,
            self.notes
        )

        # Liberar la propiedad
        self.contract_line_id.property_id.write({'state': 'free'})

        return {'type': 'ir.actions.act_window_close'}
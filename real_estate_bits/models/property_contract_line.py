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

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        # Activar automáticamente si el contrato está confirmado
        for line in lines:
            if line.contract_id.state == 'confirmed':
                line.state = 'active'
        return lines

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


# ==================================================================================
# CLASES PropertyContract Y WIZARDS MOVIDAS A property_contract.py
# Para mantener un archivo único por modelo principal
# ==================================================================================
# Las siguientes clases ahora están en property_contract.py:
# - PropertyContractMultiProperty (herencia de property.contract)
# - PropertyContractAddLineWizard
# - PropertyContractTerminateLineWizard
# ==================================================================================
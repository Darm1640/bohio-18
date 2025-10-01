# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError
from odoo.tools.misc import format_date
from odoo.tools import float_is_zero
from dateutil.relativedelta import relativedelta


class AssetModify(models.TransientModel):
    _inherit = 'asset.modify'
    
    # ============================================================
    # CAMPOS DE CONTROL DUAL
    # ============================================================
    
    accounting_framework = fields.Selection(
        related='asset_id.accounting_framework',
        string='Marco Contable'
    )
    
    # Control de qué sistema modificar
    modify_scope = fields.Selection([
        ('both', 'LOCAL y NIIF'),
        ('local', 'Solo LOCAL'),
        ('niif', 'Solo NIIF')
    ], string='Aplicar a', default='both')
    
    # Estado NIIF
    state_niif = fields.Selection(
        related='asset_id.state_niif',
        string='Estado NIIF'
    )
    
    # ============================================================
    # CAMPOS DE DEPRECIACIÓN NIIF
    # ============================================================
    
    method_niif = fields.Selection([
        ('linear', 'Lineal'),
        ('degressive', 'Decreciente'),
        ('degressive_then_linear', 'Decreciente luego Lineal')
    ], string='Método NIIF')
    
    method_number_niif = fields.Integer(
        string='Duración NIIF'
    )
    
    method_period_niif = fields.Selection([
        ('1', 'Meses'),
        ('12', 'Años')
    ], string='Período NIIF')
    
    method_progress_factor_niif = fields.Float(
        string='Factor Decreciente NIIF'
    )
    
    value_residual_niif = fields.Monetary(
        string="Monto Depreciable NIIF",
        compute="_compute_value_residual_niif",
        store=True,
        readonly=False
    )
    
    salvage_value_niif = fields.Monetary(
        string="Valor Salvamento NIIF"
    )
    
    # ============================================================
    # CUENTAS CONTABLES NIIF
    # ============================================================
    
    account_asset_niif_id = fields.Many2one(
        'account.account',
        string="Cuenta Activo NIIF",
        check_company=True,
        domain="[('deprecated', '=', False), ('niif', '=', True)]"
    )
    
    account_asset_counterpart_niif_id = fields.Many2one(
        'account.account',
        check_company=True,
        domain="[('deprecated', '=', False), ('niif', '=', True)]",
        string="Contraparte NIIF"
    )
    
    account_depreciation_niif_id = fields.Many2one(
        'account.account',
        check_company=True,
        domain="[('deprecated', '=', False), ('niif', '=', True)]",
        string="Depreciación NIIF"
    )
    
    account_expense_niif_id = fields.Many2one(
        'account.account',
        check_company=True,
        domain="[('deprecated', '=', False), ('niif', '=', True)]",
        string="Gasto NIIF"
    )
    
    journal_niif_id = fields.Many2one(
        'account.journal',
        string='Diario NIIF',
        check_company=True,
        domain="[('type', '=', 'general'), ('niif', '=', True)]"
    )
    
    # ============================================================
    # CONTROL DE INCREMENTO DE VALOR NIIF
    # ============================================================
    
    gain_value_niif = fields.Boolean(
        compute="_compute_gain_value_niif",
        string="Hay Incremento NIIF"
    )
    
    # ============================================================
    # CUENTAS PARA VENTA/DISPOSICIÓN NIIF
    # ============================================================
    
    gain_account_niif_id = fields.Many2one(
        comodel_name='account.account',
        string='Cuenta Ganancia NIIF',
        check_company=True,
        domain="[('deprecated', '=', False), ('niif', '=', True)]"
    )
    
    loss_account_niif_id = fields.Many2one(
        comodel_name='account.account',
        string='Cuenta Pérdida NIIF',
        check_company=True,
        domain="[('deprecated', '=', False), ('niif', '=', True)]"
    )
    
    # ============================================================
    # MÉTODOS EXTENDIDOS DE SELECCIÓN
    # ============================================================
    
    @api.depends('asset_id')
    def _get_selection_modify_options(self):
        """Extiende las opciones de modificación para incluir opciones NIIF"""
        options = super()._get_selection_modify_options()
        
        # Si es activo dual y no estamos en modo resume, agregar opciones específicas
        if (self.asset_id.accounting_framework == 'dual' and 
            not self.env.context.get('resume_after_pause')):
            
            # Buscar si ya existe 'dispose' para insertar después
            base_options = list(options)
            extended_options = []
            
            for opt in base_options:
                extended_options.append(opt)
                # Agregar opciones NIIF después de cada opción base
                if opt[0] == 'dispose':
                    extended_options.extend([
                        ('dispose_local', _("Dar de Baja solo LOCAL")),
                        ('dispose_niif', _("Dar de Baja solo NIIF")),
                    ])
                elif opt[0] == 'sell':
                    extended_options.extend([
                        ('sell_local', _("Vender solo LOCAL")),
                        ('sell_niif', _("Vender solo NIIF")),
                    ])
                elif opt[0] == 'pause':
                    extended_options.extend([
                        ('pause_local', _("Pausar solo LOCAL")),
                        ('pause_niif', _("Pausar solo NIIF")),
                    ])
            
            return extended_options
        
        return options
    
    # ============================================================
    # MÉTODOS COMPUTADOS NIIF
    # ============================================================
    
    @api.depends('date', 'asset_id')
    def _compute_value_residual_niif(self):
        for record in self:
            if (record.asset_id.accounting_framework in ('niif', 'dual') and 
                record.modify_scope in ('both', 'niif')):
                # Usar método NIIF si existe, sino usar el método base con datos NIIF
                if hasattr(record.asset_id, '_get_residual_value_niif_at_date'):
                    record.value_residual_niif = record.asset_id._get_residual_value_niif_at_date(record.date)
                else:
                    # Fallback al cálculo básico
                    record.value_residual_niif = record.asset_id.value_residual_niif
            else:
                record.value_residual_niif = 0
    
    @api.depends('asset_id', 'value_residual_niif', 'salvage_value_niif')
    def _compute_gain_value_niif(self):
        for record in self:
            if not record.asset_id.accounting_framework in ('niif', 'dual'):
                record.gain_value_niif = False
                continue
                
            if record.modify_scope not in ('both', 'niif'):
                record.gain_value_niif = False
                continue
                
            current_value = record._get_current_book_value_niif()
            new_value = record._get_own_book_value_niif()
            record.gain_value_niif = record.currency_id.compare_amounts(new_value, current_value) > 0
    
    # ============================================================
    # OVERRIDE DEL MÉTODO _compute_informational_text
    # ============================================================
    
    @api.depends('loss_account_id', 'gain_account_id', 'gain_or_loss', 'modify_action', 
                 'date', 'value_residual', 'salvage_value', 'value_residual_niif', 'salvage_value_niif')
    def _compute_informational_text(self):
        """Extiende el texto informativo para incluir información NIIF"""
        super()._compute_informational_text()
        
        for wizard in self:
            # Agregar información NIIF si aplica
            if wizard.accounting_framework in ('niif', 'dual'):
                additional_text = wizard._get_niif_informational_text()
                if additional_text:
                    current_text = wizard.informational_text or ''
                    wizard.informational_text = current_text + '<br/><br/>' + additional_text if current_text else additional_text
    
    def _get_niif_informational_text(self):
        """Genera texto informativo específico para NIIF"""
        text = ""
        
        if self.modify_action == 'dispose_niif':
            text = _("<b>NIIF:</b> Se dará de baja el activo en el sistema NIIF en la fecha %s.") % format_date(self.env, self.date)
        elif self.modify_action == 'sell_niif':
            text = _("<b>NIIF:</b> Se venderá el activo en el sistema NIIF en la fecha %s.") % format_date(self.env, self.date)
        elif self.modify_action == 'pause_niif':
            text = _("<b>NIIF:</b> Se pausará el activo en el sistema NIIF en la fecha %s.") % format_date(self.env, self.date)
        elif self.modify_action == 'modify' and self.modify_scope in ('both', 'niif'):
            if self.gain_value_niif:
                text = _("<b>NIIF:</b> Se registrará una revaluación del activo.")
            elif self.value_residual_niif < self._get_current_book_value_niif():
                text = _("<b>NIIF:</b> Se registrará un deterioro del activo.")
        
        return text
    
    # ============================================================
    # OVERRIDE DEL MÉTODO CREATE
    # ============================================================
    
    @api.model_create_multi
    def create(self, vals_list):
        """Extiende create para incluir valores NIIF"""
        for vals in vals_list:
            if 'asset_id' in vals:
                asset = self.env['account.asset'].browse(vals['asset_id'])
                
                # Cargar valores NIIF si el activo es dual o NIIF
                if asset.accounting_framework in ('niif', 'dual'):
                    if 'method_niif' not in vals and hasattr(asset, 'method_niif'):
                        vals['method_niif'] = asset.method_niif
                    if 'method_number_niif' not in vals and hasattr(asset, 'method_number_niif'):
                        vals['method_number_niif'] = asset.method_number_niif
                    if 'method_period_niif' not in vals and hasattr(asset, 'method_period_niif'):
                        vals['method_period_niif'] = asset.method_period_niif
                    if 'method_progress_factor_niif' not in vals and hasattr(asset, 'method_progress_factor_niif'):
                        vals['method_progress_factor_niif'] = asset.method_progress_factor_niif
                    if 'salvage_value_niif' not in vals and hasattr(asset, 'salvage_value_niif'):
                        vals['salvage_value_niif'] = asset.salvage_value_niif
                    
                    # Cargar cuentas NIIF
                    if 'account_asset_niif_id' not in vals and hasattr(asset, 'account_asset_niif_id') and asset.account_asset_niif_id:
                        vals['account_asset_niif_id'] = asset.account_asset_niif_id.id
                    if 'account_depreciation_niif_id' not in vals and hasattr(asset, 'account_depreciation_niif_id') and asset.account_depreciation_niif_id:
                        vals['account_depreciation_niif_id'] = asset.account_depreciation_niif_id.id
                    if 'account_expense_niif_id' not in vals and hasattr(asset, 'account_expense_niif_id') and asset.account_expense_niif_id:
                        vals['account_expense_niif_id'] = asset.account_expense_niif_id.id
                    if 'journal_niif_id' not in vals and hasattr(asset, 'journal_niif_id') and asset.journal_niif_id:
                        vals['journal_niif_id'] = asset.journal_niif_id.id
        
        return super().create(vals_list)
    
    # ============================================================
    # OVERRIDE DEL MÉTODO MODIFY
    # ============================================================
    
    def modify(self):
        """Extiende modify para manejar LOCAL y NIIF"""
        
        # Si no es dual/NIIF, usar el método original
        if self.asset_id.accounting_framework not in ('niif', 'dual'):
            return super().modify()
        
        # Si es modify_scope = 'local', usar el método original
        if self.modify_scope == 'local':
            return super().modify()
        
        # Si es modify_scope = 'niif', modificar solo NIIF
        if self.modify_scope == 'niif':
            return self._modify_niif_only()
        
        # Si es modify_scope = 'both', modificar ambos
        if self.modify_scope == 'both':
            # Primero modificar LOCAL usando el método base
            super().modify()
            # Luego modificar NIIF
            self._modify_niif_parallel()
        
        return {'type': 'ir.actions.act_window_close'}
    
    def _modify_niif_only(self):
        """Modifica solo el sistema NIIF"""
        
        # Validar que el activo tenga configuración NIIF
        if self.asset_id.accounting_framework not in ('niif', 'dual'):
            raise UserError(_("Este activo no tiene configuración NIIF"))
        
        # Validar fecha contra bloqueo fiscal
        if self.date <= self.asset_id.company_id._get_user_fiscal_lock_date(self.journal_niif_id or self.asset_id.journal_id):
            raise UserError(_("No puede reevaluar el activo NIIF antes de la fecha de bloqueo."))
        
        old_values = {
            'method_number_niif': self.asset_id.method_number_niif,
            'method_period_niif': self.asset_id.method_period_niif,
            'value_residual_niif': self.asset_id.value_residual_niif,
            'salvage_value_niif': self.asset_id.salvage_value_niif,
        }
        
        asset_vals = {
            'method_niif': self.method_niif,
            'method_number_niif': self.method_number_niif,
            'method_period_niif': self.method_period_niif,
            'salvage_value_niif': self.salvage_value_niif,
        }
        
        # Agregar cuentas si están definidas
        if self.account_asset_niif_id:
            asset_vals['account_asset_niif_id'] = self.account_asset_niif_id
        if self.account_depreciation_niif_id:
            asset_vals['account_depreciation_niif_id'] = self.account_depreciation_niif_id
        if self.account_expense_niif_id:
            asset_vals['account_expense_niif_id'] = self.account_expense_niif_id
        if self.journal_niif_id:
            asset_vals['journal_niif_id'] = self.journal_niif_id
        
        # Manejar reanudación NIIF
        if self.env.context.get('resume_after_pause'):
            asset_vals.update({'state_niif': 'open'})
            self.asset_id.message_post(body=_("Activo NIIF reanudado. %s", self.name))
        
        # Calcular incremento/decremento NIIF
        current_book = self._get_current_book_value_niif()
        after_book = self._get_own_book_value_niif()
        increase = after_book - current_book
        
        # Manejar cambios de valor NIIF
        if increase > 0:
            self._handle_value_increase_niif(increase)
        elif increase < 0:
            self._handle_value_decrease_niif(increase)
        
        # Crear movimiento antes de la fecha si es necesario
        if not self.env.context.get('resume_after_pause'):
            if hasattr(self.asset_id, '_create_move_before_date_niif'):
                self.asset_id._create_move_before_date_niif(self.date)
        
        # Actualizar el activo
        self.asset_id.write(asset_vals)
        
        # Recalcular tabla de depreciación NIIF
        restart_date = self.date if self.env.context.get('resume_after_pause') else self.date + relativedelta(days=1)
        
        if hasattr(self.asset_id, 'compute_depreciation_board_niif'):
            self.asset_id.compute_depreciation_board_niif(restart_date)
        
        # Tracking de cambios
        tracked_fields = self.env['account.asset'].fields_get(old_values.keys())
        changes, tracking_value_ids = self.asset_id._mail_track(tracked_fields, old_values)
        if changes:
            self.asset_id.message_post(
                body=_('Tabla de depreciación NIIF modificada %s', self.name),
                tracking_value_ids=tracking_value_ids
            )
        
        return {'type': 'ir.actions.act_window_close'}
    
    def _modify_niif_parallel(self):
        """Modifica NIIF en paralelo con LOCAL (ya modificado)"""
        
        # Similar a _modify_niif_only pero sin validaciones ya hechas
        asset_vals = {}
        
        if self.method_niif:
            asset_vals['method_niif'] = self.method_niif
        if self.method_number_niif:
            asset_vals['method_number_niif'] = self.method_number_niif
        if self.method_period_niif:
            asset_vals['method_period_niif'] = self.method_period_niif
        if self.salvage_value_niif is not False:
            asset_vals['salvage_value_niif'] = self.salvage_value_niif
        
        if asset_vals:
            self.asset_id.write(asset_vals)
        
        # Recalcular tabla NIIF si existe el método
        if hasattr(self.asset_id, 'compute_depreciation_board_niif'):
            restart_date = self.date + relativedelta(days=1)
            self.asset_id.compute_depreciation_board_niif(restart_date)
    
    # ============================================================
    # MÉTODOS PARA ACCIONES ESPECÍFICAS
    # ============================================================
    
    def pause(self):
        """Extiende pause para manejar scope"""
        if self.modify_action == 'pause_local':
            return self._pause_local()
        elif self.modify_action == 'pause_niif':
            return self._pause_niif()
        else:
            # Pausar ambos sistemas
            super().pause()
            if self.asset_id.accounting_framework in ('niif', 'dual'):
                self._pause_niif_internal()
    
    def _pause_local(self):
        """Pausa solo el sistema LOCAL"""
        self.asset_id.pause(pause_date=self.date, message=self.name)
    
    def _pause_niif(self):
        """Pausa solo el sistema NIIF"""
        if self.asset_id.accounting_framework not in ('niif', 'dual'):
            raise UserError(_("Este activo no tiene configuración NIIF"))
        
        self._pause_niif_internal()
    
    def _pause_niif_internal(self):
        """Lógica interna para pausar NIIF"""
        # Crear movimiento NIIF antes de la fecha si existe el método
        if hasattr(self.asset_id, '_create_move_before_date_niif'):
            self.asset_id._create_move_before_date_niif(self.date)
        
        self.asset_id.write({'state_niif': 'paused'})
        self.asset_id.message_post(body=_("Activo NIIF pausado. %s", self.name if self.name else ""))
    
    def sell_dispose(self):
        """Extiende sell_dispose para manejar acciones específicas"""
        
        # Manejar acciones específicas de LOCAL/NIIF
        if self.modify_action in ('dispose_local', 'sell_local'):
            return self._sell_dispose_local()
        elif self.modify_action in ('dispose_niif', 'sell_niif'):
            return self._sell_dispose_niif()
        else:
            # Comportamiento original para ambos sistemas
            return super().sell_dispose()
    
    def _sell_dispose_local(self):
        """Vende o da de baja solo en LOCAL"""
        self.ensure_one()
        
        # Validar cuentas
        if self.gain_account_id == self.asset_id.account_depreciation_id:
            raise UserError(_("No puede seleccionar la misma cuenta que la Cuenta de Depreciación"))
        if self.loss_account_id == self.asset_id.account_depreciation_id:
            raise UserError(_("No puede seleccionar la misma cuenta que la Cuenta de Depreciación"))
        
        invoice_lines = self.env['account.move.line'] if self.modify_action == 'dispose_local' else self.invoice_line_ids
        
        # Llamar al método set_to_close del activo (solo LOCAL)
        return self.asset_id.set_to_close(
            invoice_line_ids=invoice_lines,
            date=self.date,
            message=self.name
        )
    
    def _sell_dispose_niif(self):
        """Vende o da de baja solo en NIIF"""
        self.ensure_one()
        
        if self.asset_id.accounting_framework not in ('niif', 'dual'):
            raise UserError(_("Este activo no tiene configuración NIIF"))
        
        # Validar cuentas NIIF
        if self.gain_account_niif_id and self.gain_account_niif_id == self.asset_id.account_depreciation_niif_id:
            raise UserError(_("No puede seleccionar la misma cuenta que la Cuenta de Depreciación NIIF"))
        if self.loss_account_niif_id and self.loss_account_niif_id == self.asset_id.account_depreciation_niif_id:
            raise UserError(_("No puede seleccionar la misma cuenta que la Cuenta de Depreciación NIIF"))
        
        invoice_lines = self.env['account.move.line'] if self.modify_action == 'dispose_niif' else self.invoice_line_ids
        
        # Llamar al método set_to_close_niif si existe
        if hasattr(self.asset_id, 'set_to_close_niif'):
            return self.asset_id.set_to_close_niif(
                invoice_line_ids=invoice_lines,
                date=self.date,
                message=self.name
            )
        else:
            raise UserError(_("El método de cierre NIIF no está implementado"))
    
    # ============================================================
    # MÉTODOS AUXILIARES NIIF
    # ============================================================
    
    def _get_own_book_value(self):
        """Mantiene el método original para LOCAL"""
        return super()._get_own_book_value()
    
    def _get_own_book_value_niif(self):
        """Obtiene el valor en libros NIIF después de la modificación"""
        return self.value_residual_niif + self.salvage_value_niif
    
    def _get_current_book_value_niif(self):
        """Obtiene el valor en libros NIIF actual del activo"""
        if hasattr(self.asset_id, '_get_own_book_value_niif'):
            return self.asset_id._get_own_book_value_niif(self.date)
        else:
            # Fallback
            return self.asset_id.value_residual_niif + self.asset_id.salvage_value_niif
    
    def _handle_value_increase_niif(self, increase):
        """Maneja incremento de valor NIIF (revaluación)"""
        
        # Crear asiento de revaluación NIIF
        journal = self.journal_niif_id or self.asset_id.journal_niif_id or self.asset_id.journal_id
        
        move_vals = {
            'journal_id': journal.id,
            'date': self.date,
            'ref': _('Revaluación NIIF: %(asset)s', asset=self.asset_id.name),
            'move_type': 'entry',
            'line_ids': [
                Command.create({
                    'account_id': (self.account_asset_niif_id or self.asset_id.account_asset_niif_id).id,
                    'name': _('Revaluación NIIF de %(asset)s', asset=self.asset_id.name),
                    'debit': increase,
                    'credit': 0,
                }),
                Command.create({
                    'account_id': (self.account_asset_counterpart_niif_id or self.company_id.gain_account_id).id,
                    'name': _('Revaluación NIIF de %(asset)s', asset=self.asset_id.name),
                    'debit': 0,
                    'credit': increase,
                }),
            ],
        }
        
        move = self.env['account.move'].create(move_vals)
        move._post()
        
        # Actualizar revaluación acumulada si el campo existe
        if hasattr(self.asset_id, 'revaluation_amount'):
            self.asset_id.revaluation_amount += increase
        
        # Mensaje en el chatter
        self.asset_id.message_post(
            body=_('Revaluación NIIF registrada: %(amount)s', 
                  amount=format_date(self.env, increase))
        )
    
    def _handle_value_decrease_niif(self, decrease):
        """Maneja decremento de valor NIIF (deterioro)"""
        
        # Crear asiento de deterioro NIIF
        journal = self.journal_niif_id or self.asset_id.journal_niif_id or self.asset_id.journal_id
        
        move_vals = {
            'journal_id': journal.id,
            'date': self.date,
            'ref': _('Deterioro NIIF: %(asset)s', asset=self.asset_id.name),
            'move_type': 'entry',
            'line_ids': [
                Command.create({
                    'account_id': (self.account_expense_niif_id or self.asset_id.account_expense_niif_id).id,
                    'name': _('Deterioro NIIF de %(asset)s', asset=self.asset_id.name),
                    'debit': abs(decrease),
                    'credit': 0,
                }),
                Command.create({
                    'account_id': (self.account_depreciation_niif_id or self.asset_id.account_depreciation_niif_id).id,
                    'name': _('Deterioro NIIF de %(asset)s', asset=self.asset_id.name),
                    'debit': 0,
                    'credit': abs(decrease),
                }),
            ],
        }
        
        move = self.env['account.move'].create(move_vals)
        move._post()
        
        if hasattr(self.asset_id, 'impairment_amount'):
            self.asset_id.impairment_amount += abs(decrease)
        
        self.asset_id.message_post(
            body=_('Deterioro NIIF registrado: %(amount)s', 
                  amount=format_date(self.env, abs(decrease)))
        )
    
    def _get_new_asset_values(self, current_asset_book):
        """Mantiene el método original para LOCAL"""
        return super()._get_new_asset_values(current_asset_book)
    
    def _get_new_asset_values_niif(self, current_asset_book):
        """Calcula los nuevos valores del activo NIIF"""
        self.ensure_one()
        new_residual = min(
            current_asset_book - min(self.salvage_value_niif, self.asset_id.salvage_value_niif),
            self.value_residual_niif
        )
        new_salvage = min(current_asset_book - new_residual, self.salvage_value_niif)
        return new_residual, new_salvage
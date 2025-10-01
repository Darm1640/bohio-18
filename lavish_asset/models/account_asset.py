from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from math import copysign
from odoo.tools import float_compare, float_is_zero, formatLang, date_utils

import logging

_logger = logging.getLogger(__name__)

DAYS_PER_MONTH = 30
DAYS_PER_YEAR = DAYS_PER_MONTH * 12


class AccountAsset(models.Model):
    _inherit = 'account.asset'
    
    asset_type_niif = fields.Selection([
        ('tangible', 'Propiedad, Planta y Equipo'),
        ('intangible', 'Activo Intangible'),
        ('investment', 'Propiedad de Inversión'),
        ('biological', 'Activo Biológico'),
    ], string='Clasificación NIIF', default='tangible', tracking=True)
    total_depreciation_entries_count_niif = fields.Integer(
        string='Total Entradas de Depreciación NIIF',
        compute='_compute_total_depreciation_entries_count_niif',
        store=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        tracking=True
    )
    
    serial_number = fields.Char(
        string='Número de Serie',
        tracking=True
    )

    
    accounting_framework = fields.Selection([
        ('local', 'LOCAL (Fiscal)'),
        ('niif', 'NIIF/IFRS'),
        ('dual', 'DUAL (Local + NIIF)')
    ], string='Marco Contable', default='dual', tracking=True, required=True)
    

    
    state_niif = fields.Selection([
        ('model', 'Modelo'),
        ('draft', 'Borrador'),
        ('open', 'En Ejecución'),
        ('paused', 'En Pausa'),
        ('close', 'Cerrado'),
        ('cancelled', 'Cancelado')
    ], string='Estado NIIF', default='draft', tracking=True, copy=False)
    

    
    uvt_value = fields.Float(
        string='Valor UVT',
        default=47065,  # Valor 2024
        help='Valor UVT a la fecha de adquisición'
    )
    
    uvt_threshold = fields.Float(
        string='UVTs para Activo Menor',
        default=50.0
    )
    
    is_minor_asset = fields.Boolean(
        string='Activo Menor (UVT)',
        compute='_compute_is_minor_asset',
        store=True
    )

    
    tax_ids = fields.Many2many(
        'account.tax',
        'asset_tax_rel',
        'asset_id',
        'tax_id',
        string='Impuestos en Costo'
    )
    
    tax_value = fields.Monetary(
        string='Valor Impuestos',
        compute='_compute_tax_value',
        store=True
    )
    

    
    original_value_niif = fields.Monetary(
        string="Valor Original NIIF",
        tracking=True
    )
    
    salvage_value_niif = fields.Monetary(
        string="Valor Salvamento NIIF",
        tracking=True
    )
    
    method_niif = fields.Selection([
        ('linear', 'Lineal'),
        ('degressive', 'Decreciente'),
        ('degressive_then_linear', 'Decreciente luego Lineal')
    ], string='Método NIIF', default='linear')
    
    method_number_niif = fields.Integer(
        string='Duración NIIF',
        default=10,
        help="Número de depreciaciones necesarias para depreciar el activo"
    )
    
    method_period_niif = fields.Selection([
        ('1', 'Mensual'),
        ('12', 'Anual')
    ], string='Periodo NIIF', default='12',
        help="Cantidad de tiempo entre dos depreciaciones"
    )
    
    method_progress_factor_niif = fields.Float(
        string='Factor Decreciente NIIF',
        default=0.3
    )
    
    prorata_computation_type_niif = fields.Selection([
        ('none', 'Sin Prorrateo'),
        ('constant_periods', 'Períodos Constantes'),
        ('daily_computation', 'Basado en días')
    ], string='Cómputo NIIF', default='constant_periods', required=True)
    
   
    acquisition_date_niif = fields.Date(
        string='Fecha Adquisición NIIF',
        compute='_compute_acquisition_date_niif',
        store=True,
        readonly=False,
        copy=True,
        help='Fecha de adquisición para efectos NIIF'
    )
    
    prorata_date_niif = fields.Date(
        string='Fecha Prorrateo NIIF',
        compute='_compute_prorata_date_niif',
        store=True,
        readonly=False,
        help='Fecha inicial del período usado en el cálculo del prorrateo de la primera depreciación NIIF',
        precompute=True,
        copy=True
    )
    
    disposal_date_niif = fields.Date(
        string='Fecha Disposición NIIF',
        readonly=False,
        compute="_compute_disposal_date_niif",
        store=True
    )
    
    paused_prorata_date_niif = fields.Date(
        compute='_compute_paused_prorata_date_niif'
    )
    

    
    depreciation_move_niif_ids = fields.One2many(
        'account.move',
        'asset_niif_id',
        string='Depreciación NIIF',
        domain=[('is_niif_depreciation', '=', True)],
        copy=False
    )
    

    value_residual_niif = fields.Monetary(
        string='Valor Residual NIIF',
        compute='_compute_value_residual_niif',
        store=True
    )
    
    book_value_niif = fields.Monetary(
        string='Valor en Libros NIIF',
        compute='_compute_book_value_niif',
        store=True,
        recursive=True
    )

    asset_depreciated_value_niif = fields.Monetary(
        string='Valor Depreciado NIIF',
        compute='_compute_depreciated_value_niif',
        store=True,
        currency_field='currency_id'
    )

    impairment_amount = fields.Monetary(
        string='Deterioro Acumulado',
        tracking=True
    )
    
    revaluation_amount = fields.Monetary(
        string='Revaluación Acumulada',
        tracking=True
    )
    

    
    account_asset_niif_id = fields.Many2one(
        'account.account',
        string='Cuenta Activo NIIF',
        check_company=True,
        domain="[('account_type', '!=', 'off_balance'), ('niif', '=', True)]"
    )
    
    account_depreciation_niif_id = fields.Many2one(
        'account.account',
        string='Depreciación Acumulada NIIF',
        check_company=True,
        domain="[('account_type', 'not in', ('asset_receivable', 'liability_payable', 'asset_cash', 'liability_credit_card', 'off_balance')), ('deprecated', '=', False), ('niif', '=', True)]"
    )
    
    account_expense_niif_id = fields.Many2one(
        'account.account',
        string='Gasto Depreciación NIIF',
        check_company=True,
        domain="[('account_type', 'not in', ('asset_receivable', 'liability_payable', 'asset_cash', 'liability_credit_card', 'off_balance')), ('deprecated', '=', False), ('niif', '=', True)]"
    )
    
    journal_niif_id = fields.Many2one(
        'account.journal',
        string='Diario NIIF',
        check_company=True,
        domain="[('type', '=', 'general'), ('niif', '=', True)]"
    )
    
    # Control de días para NIIF
    asset_lifetime_days_niif = fields.Float(
        compute="_compute_lifetime_days_niif",
        recursive=True
    )
    
    asset_paused_days_niif = fields.Float(
        copy=False,
        string='Días Pausados NIIF'
    )
    
    already_depreciated_amount_import_niif = fields.Monetary(
        string='Monto ya Depreciado NIIF',
        help="En caso de importación desde otro software, puede usar este campo para tener el reporte de tabla de depreciación correcto."
    )
    depreciation_entries_count_niif = fields.Integer(
        string='Entradas de Depreciación NIIF',
        compute='_compute_depreciation_entries_count_niif',
        store=True
    )
    last_depreciation_date_niif = fields.Date(  
        string='Última Fecha de Depreciación NIIF',
        compute='_compute_last_depreciation_date_niif',
        store=True
    )

    def _get_last_day_asset_niif(self):
        """Obtiene la última fecha del activo NIIF"""
        self.ensure_one()
        
        if self.accounting_framework not in ('niif', 'dual'):
            return False
        
        if self.method_period_niif == '1':  # Mensual
            return self.prorata_date_niif + relativedelta(
                months=int(self.method_number_niif) * 1 - 1,
                days=date_utils.end_of(
                    self.prorata_date_niif + relativedelta(
                        months=int(self.method_number_niif) * 1 - 1
                    ), 'month'
                ).day - 1
            )
        else:  # Anual
            return self.prorata_date_niif + relativedelta(
                years=int(self.method_number_niif) * 1 - 1,
                months=11,
                days=date_utils.end_of(
                    self.prorata_date_niif + relativedelta(
                        years=int(self.method_number_niif) * 1 - 1,
                        months=11
                    ), 'month'
                ).day - 1
            )

    def open_entries_niif(self):
        """Abre las entradas de depreciación NIIF"""
        self.ensure_one()
        return {
            'name': _('Depreciaciones NIIF del Activo %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.depreciation_move_niif_ids.ids)],
            'context': {'default_asset_niif_id': self.id, 'default_is_niif_depreciation': True}
        }

    def action_view_depreciated_values_niif(self):
        """Muestra información detallada de valores depreciados NIIF"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Valores Depreciados NIIF'),
                'message': _('Valor Original: %s\nValor Depreciado: %s\nValor Residual: %s\nValor Salvamento: %s') % (
                    self.currency_id.format(self.original_value_niif),
                    self.currency_id.format(self.asset_depreciated_value_niif),
                    self.currency_id.format(self.value_residual_niif),
                    self.currency_id.format(self.salvage_value_niif)
                ),
                'sticky': False,
                'type': 'info'
            }
        }

    def action_view_book_value_niif(self):
        """Muestra información del valor en libros NIIF"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Valor en Libros NIIF'),
                'message': _('Valor en Libros: %s\nValor Residual: %s\nValor Salvamento: %s') % (
                    self.currency_id.format(self.book_value_niif),
                    self.currency_id.format(self.value_residual_niif),
                    self.currency_id.format(self.salvage_value_niif)
                ),
                'sticky': False,
                'type': 'info'
            }
        }

    def validate_niif(self):
        """Valida y confirma el activo NIIF"""
        self.write({'state_niif': 'open'})
        self.compute_depreciation_board_niif()
        return True

    def compute_depreciation_board_niif(self, date=False):
        """Computa la tabla de depreciación NIIF"""
        self.ensure_one()
        depreciation_moves = self.env['account.move']
        amount_to_depreciate = self.value_residual_niif

        if self.method_niif == 'linear':
            amount = amount_to_depreciate / self.method_number_niif
        elif self.method_niif == 'degressive':
            amount = amount_to_depreciate * self.method_progress_factor_niif
        else:
            amount = 0

        for x in range(len(self.depreciation_move_niif_ids), int(self.method_number_niif)):
            sequence = x + 1
            date = date or self.acquisition_date_niif

            if self.method_period_niif == '1':
                date = date + relativedelta(months=+sequence)
            else:
                date = date + relativedelta(years=+sequence)

            vals = {
                'asset_id': self.id,
                'asset_niif_id': self.id,
                'is_niif_depreciation': True,
                'date': date,
                'journal_id': self.journal_niif_id.id,
                'currency_id': self.currency_id.id,
                'move_type': 'entry',
                'ref': self.name + ' - ' + str(sequence),
                'line_ids': [
                    (0, 0, {
                        'account_id': self.account_expense_niif_id.id,
                        'debit': amount if amount > 0 else 0,
                        'credit': -amount if amount < 0 else 0,
                        'analytic_distribution': self.analytic_distribution,
                    }),
                    (0, 0, {
                        'account_id': self.account_depreciation_niif_id.id,
                        'credit': amount if amount > 0 else 0,
                        'debit': -amount if amount < 0 else 0,
                    })
                ]
            }
            move = self.env['account.move'].create(vals)
            self.depreciation_move_niif_ids |= move

        return True

    def set_to_draft_niif(self):
        """Establece el activo NIIF en borrador"""
        self.write({'state_niif': 'draft'})

    def set_to_running_niif(self):
        """Reactiva el activo NIIF"""
        if self.state_niif == 'close':
            self.write({'state_niif': 'open'})

    def resume_after_pause_niif(self):
        """Reanuda el activo NIIF después de pausado"""
        if self.state_niif == 'paused':
            self.write({'state_niif': 'open'})

    def action_asset_modify_niif(self):
        """Abre el wizard de modificación NIIF"""
        self.ensure_one()
        return {
            'name': _('Modificar Activo NIIF'),
            'type': 'ir.actions.act_window',
            'res_model': 'asset.modify',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_asset_id': self.id,
                'default_modify_scope': 'niif' if self.accounting_framework == 'niif' else 'both',
                'default_accounting_framework': self.accounting_framework,
                'default_method_number_niif': self.method_number_niif,
                'default_method_niif': self.method_niif,
                'default_method_period_niif': self.method_period_niif,
                'default_salvage_value_niif': self.salvage_value_niif,
            }
        }

    def set_to_cancelled_niif(self):
        """Cancela el activo NIIF"""
        self.write({'state_niif': 'cancelled'})

    @api.depends('depreciation_move_niif_ids', 'depreciation_move_niif_ids.state')
    def _compute_total_depreciation_entries_count_niif(self):
        for asset in self:
            asset.total_depreciation_entries_count_niif = len(asset.depreciation_move_niif_ids) + len(asset.depreciation_move_niif_ids.filtered(lambda m: m.state == 'draft'))  


    @api.depends('depreciation_move_niif_ids', 'depreciation_move_niif_ids.date')
    def _compute_last_depreciation_date_niif(self):
        for asset in self:
            asset.last_depreciation_date_niif = asset._get_last_day_asset_niif()

    @api.depends('depreciation_move_niif_ids', 'depreciation_move_niif_ids.date')
    def _compute_depreciation_entries_count_niif(self):
        for asset in self:
            asset.depreciation_entries_count_niif = len(asset.depreciation_move_niif_ids)

    @api.depends('original_value_niif', 'salvage_value_niif', 'already_depreciated_amount_import_niif', 'depreciation_move_niif_ids', 'depreciation_move_niif_ids.state')
    def _compute_depreciated_value_niif(self):
        """Calcula el valor depreciado acumulado NIIF"""
        for asset in self:
            if not asset.depreciation_move_niif_ids:
                asset.asset_depreciated_value_niif = asset.already_depreciated_amount_import_niif
            else:
                posted_moves = asset.depreciation_move_niif_ids.filtered(lambda m: m.state == 'posted')
                depreciated_value = sum(posted_moves.mapped('depreciation_value'))
                asset.asset_depreciated_value_niif = depreciated_value + asset.already_depreciated_amount_import_niif

    @api.depends('original_value', 'tax_value', 'uvt_value', 'uvt_threshold')
    def _compute_is_minor_asset(self):
        """Determina si es activo menor según UVT"""
        for asset in self:
            total_value = asset.original_value + asset.tax_value
            threshold = asset.uvt_value * asset.uvt_threshold
            asset.is_minor_asset = total_value <= threshold
    
    @api.depends('tax_ids', 'original_value')
    def _compute_tax_value(self):
        """Calcula el valor de impuestos"""
        for asset in self:
            if asset.tax_ids:
                taxes_data = asset.tax_ids.compute_all(
                    asset.original_value,
                    currency=asset.currency_id,
                    quantity=1.0
                )
                asset.tax_value = sum(t['amount'] for t in taxes_data['taxes'])
            else:
                asset.tax_value = 0
    
    @api.depends('acquisition_date')
    def _compute_acquisition_date_niif(self):
        """Calcula fecha de adquisición NIIF"""
        for asset in self:
            if asset.accounting_framework in ('niif', 'dual'):
                asset.acquisition_date_niif = asset.acquisition_date_niif or asset.acquisition_date or fields.Date.today()
            else:
                asset.acquisition_date_niif = False
    
    @api.depends('acquisition_date_niif', 'company_id', 'prorata_computation_type_niif')
    def _compute_prorata_date_niif(self):
        """Calcula fecha de prorrateo NIIF"""
        for asset in self:
            if asset.accounting_framework in ('niif', 'dual'):
                if asset.prorata_computation_type_niif == 'none' and asset.acquisition_date_niif:
                    fiscalyear_date = asset.company_id.compute_fiscalyear_dates(asset.acquisition_date_niif).get('date_from')
                    asset.prorata_date_niif = fiscalyear_date
                else:
                    asset.prorata_date_niif = asset.acquisition_date_niif
            else:
                asset.prorata_date_niif = False
    
    @api.depends('depreciation_move_niif_ids.date', 'state_niif')
    def _compute_disposal_date_niif(self):
        """Calcula fecha de disposición NIIF"""
        for asset in self:
            if asset.state_niif == 'close':
                dates = asset.depreciation_move_niif_ids.filtered(lambda m: m.date).mapped('date')
                asset.disposal_date_niif = dates and max(dates)
            else:
                asset.disposal_date_niif = False
    
    @api.depends('prorata_date_niif', 'prorata_computation_type_niif', 'asset_paused_days_niif')
    def _compute_paused_prorata_date_niif(self):
        """Calcula fecha de prorrateo pausada NIIF"""
        for asset in self:
            if not asset.prorata_date_niif:
                asset.paused_prorata_date_niif = False
                continue
                
            if asset.prorata_computation_type_niif == 'daily_computation':
                asset.paused_prorata_date_niif = asset.prorata_date_niif + relativedelta(days=int(asset.asset_paused_days_niif))
            else:
                asset.paused_prorata_date_niif = asset.prorata_date_niif + relativedelta(
                    months=int(asset.asset_paused_days_niif / DAYS_PER_MONTH),
                    days=int(asset.asset_paused_days_niif % DAYS_PER_MONTH)
                )
    
    @api.depends('method_number_niif', 'method_period_niif', 'prorata_computation_type_niif', 'prorata_date_niif')
    def _compute_lifetime_days_niif(self):
        """Calcula días de vida útil NIIF"""
        for asset in self:
            if asset.accounting_framework not in ('niif', 'dual'):
                asset.asset_lifetime_days_niif = 0
                continue
                
            if not asset.parent_id:
                if asset.prorata_computation_type_niif == 'daily_computation' and asset.prorata_date_niif:
                    end_date = asset.prorata_date_niif + relativedelta(
                        years=asset.method_number_niif,
                        days=-1
                    )
                    asset.asset_lifetime_days_niif = (end_date - asset.prorata_date_niif).days
                else:
                    asset.asset_lifetime_days_niif = int(asset.method_period_niif) * asset.method_number_niif * DAYS_PER_MONTH
            else:
                # Si tiene padre, usar días restantes del padre
                if asset.prorata_computation_type_niif == 'daily_computation':
                    parent_end_date = asset.parent_id.paused_prorata_date_niif + relativedelta(
                        days=int(asset.parent_id.asset_lifetime_days_niif - 1)
                    )
                else:
                    parent_end_date = asset.parent_id.paused_prorata_date_niif + relativedelta(
                        months=int(asset.parent_id.asset_lifetime_days_niif / DAYS_PER_MONTH),
                        days=int(asset.parent_id.asset_lifetime_days_niif % DAYS_PER_MONTH) - 1
                    )
                asset.asset_lifetime_days_niif = asset._get_delta_days_niif(asset.prorata_date_niif, parent_end_date)
    
    @api.depends(
        'original_value_niif',
        'salvage_value_niif',
        'already_depreciated_amount_import_niif',
        'depreciation_move_niif_ids.state',
        'depreciation_move_niif_ids.depreciation_value'
    )
    def _compute_value_residual_niif(self):
        """Calcula valor residual NIIF"""
        for record in self:
            if record.accounting_framework not in ('niif', 'dual'):
                record.value_residual_niif = 0
                continue
                
            posted_depreciation_moves = record.depreciation_move_niif_ids.filtered(
                lambda mv: mv.state == 'posted' and not mv.asset_value_change
            )
            record.value_residual_niif = (
                record.original_value_niif
                - record.salvage_value_niif
                - record.already_depreciated_amount_import_niif
                - sum(posted_depreciation_moves.mapped('depreciation_value'))
            )
    
    @api.depends('value_residual_niif', 'salvage_value_niif', 'impairment_amount', 'revaluation_amount', 'children_ids.book_value_niif')
    def _compute_book_value_niif(self):
        """Calcula valor en libros NIIF"""
        for record in self:
            if record.accounting_framework not in ('niif', 'dual'):
                record.book_value_niif = 0
                continue
                
            # Valor base
            book_value = record.value_residual_niif + record.salvage_value_niif
            
            # Agregar valores de hijos
            if record.children_ids:
                book_value += sum(record.children_ids.mapped('book_value_niif'))
            
            # Aplicar ajustes
            book_value -= record.impairment_amount
            book_value += record.revaluation_amount
            
            # Si está cerrado y todo está publicado, restar salvamento
            if record.state_niif == 'close' and all(move.state == 'posted' for move in record.depreciation_move_niif_ids):
                book_value -= record.salvage_value_niif
            
            record.book_value_niif = book_value
    
    # ============================================================
    # MÉTODOS ONCHANGE
    # ============================================================
    
    @api.onchange('accounting_framework')
    def _onchange_accounting_framework(self):
        """Ajusta valores cuando cambia el marco contable"""
        if self.accounting_framework in ('niif', 'dual'):
            if not self.original_value_niif:
                self.original_value_niif = self.original_value
            if not self.salvage_value_niif:
                self.salvage_value_niif = self.salvage_value
            if not self.acquisition_date_niif:
                self.acquisition_date_niif = self.acquisition_date
            if not self.method_niif:
                self.method_niif = self.method
            if not self.method_number_niif:
                self.method_number_niif = self.method_number
            if not self.method_period_niif:
                self.method_period_niif = self.method_period
    
    @api.onchange('original_value_niif', 'salvage_value_niif', 'acquisition_date_niif', 'method_niif',
                  'method_progress_factor_niif', 'method_period_niif', 'method_number_niif',
                  'prorata_computation_type_niif', 'already_depreciated_amount_import_niif', 'prorata_date_niif')
    def onchange_consistent_board_niif(self):
        """Cuando cambian los campos NIIF, desvinculamos las entradas NIIF"""
        if self.accounting_framework in ('niif', 'dual'):
            self.depreciation_move_niif_ids = [(5, 0, 0)]
    
    # ============================================================
    # MÉTODOS DE NEGOCIO PRINCIPALES
    # ============================================================
    
    def validate(self):
        """Override para validar también NIIF cuando aplica"""
        # Validación LOCAL original
        super().validate()
        
        # Si es dual o NIIF, validar también NIIF
        for asset in self:
            if asset.accounting_framework in ('niif', 'dual') and asset.state_niif == 'draft':
                asset.validate_niif()
    
    def validate_niif(self):
        """Valida activo NIIF"""
        for asset in self:
            if asset.state_niif not in ('draft', 'model'):
                continue
                
            # Cambiar estado
            asset.state_niif = 'open'
            
            # Crear tabla de depreciación NIIF si no existe
            if not asset.depreciation_move_niif_ids:
                asset.compute_depreciation_board_niif()
            
            # Verificar depreciaciones
            asset._check_depreciations_niif()
            
            # Publicar movimientos pendientes
            moves_to_post = asset.depreciation_move_niif_ids.filtered(
                lambda m: m.date <= fields.Date.today() and m.state == 'draft'
            )
            if moves_to_post:
                moves_to_post._post()
            
            # Mensaje en chatter
            asset.message_post(
                body=_('Activo NIIF validado'),
                subtype_xmlid='mail.mt_note'
            )
    
    def compute_depreciation_board(self, date=False):
        """Override para computar también NIIF cuando aplica"""
        # Computar LOCAL original
        super().compute_depreciation_board(date)
        
        # Si es dual o NIIF, computar también NIIF
        for asset in self:
            if asset.accounting_framework in ('niif', 'dual'):
                asset.compute_depreciation_board_niif(date)
    
    def compute_depreciation_board_niif(self, date=False):
        """Calcula tabla de depreciación NIIF"""
        # Eliminar movimientos draft
        self.depreciation_move_niif_ids.filtered(
            lambda mv: mv.state == 'draft' and (mv.date >= date if date else True)
        ).unlink()
        
        new_depreciation_moves_data = []
        for asset in self:
            if asset.accounting_framework in ('niif', 'dual'):
                new_depreciation_moves_data.extend(asset._recompute_board_niif(date))
        
        if new_depreciation_moves_data:
            new_depreciation_moves = self.env['account.move'].create(new_depreciation_moves_data)
            
            # Publicar si el activo está en ejecución
            new_depreciation_moves_to_post = new_depreciation_moves.filtered(
                lambda move: move.asset_niif_id.state_niif == 'open' and move.date <= fields.Date.today()
            )
            if new_depreciation_moves_to_post:
                new_depreciation_moves_to_post._post()
    
    def _recompute_board_niif(self, start_depreciation_date=False):
        """Recalcula la tabla de depreciación NIIF"""
        self.ensure_one()
        
        if self.accounting_framework not in ('niif', 'dual'):
            return []
        
        # Movimientos publicados
        posted_depreciation_move_ids = self.depreciation_move_niif_ids.filtered(
            lambda mv: mv.state == 'posted' and not mv.asset_value_change
        ).sorted(key=lambda mv: (mv.date, mv.id))
        
        imported_amount = self.already_depreciated_amount_import_niif
        residual_amount = self.value_residual_niif
        
        if not posted_depreciation_move_ids:
            residual_amount += imported_amount
        
        residual_declining = residual_at_compute = residual_amount
        start_recompute_date = start_depreciation_date = start_yearly_period = start_depreciation_date or self.paused_prorata_date_niif or self.prorata_date_niif
        
        if not start_depreciation_date:
            return []
        
        last_day_asset = self._get_last_day_asset_niif()
        final_depreciation_date = self._get_end_period_date_niif(last_day_asset)
        total_lifetime_left = self._get_delta_days_niif(start_depreciation_date, last_day_asset)
        
        depreciation_move_values = []
        
        if not float_is_zero(self.value_residual_niif, precision_rounding=self.currency_id.rounding):
            while not self.currency_id.is_zero(residual_amount) and start_depreciation_date < final_depreciation_date:
                period_end_depreciation_date = self._get_end_period_date_niif(start_depreciation_date)
                period_end_fiscalyear_date = self.company_id.compute_fiscalyear_dates(period_end_depreciation_date).get('date_to')
                lifetime_left = self._get_delta_days_niif(start_depreciation_date, last_day_asset)
                
                days, amount = self._compute_board_amount_niif(
                    residual_amount, start_depreciation_date, period_end_depreciation_date,
                    False, lifetime_left, residual_declining, start_yearly_period,
                    total_lifetime_left, residual_at_compute, start_recompute_date
                )
                
                residual_amount -= amount
                
                # Manejar imported_amount
                if not posted_depreciation_move_ids:
                    if abs(imported_amount) <= abs(amount):
                        amount -= imported_amount
                        imported_amount = 0
                    else:
                        imported_amount -= amount
                        amount = 0
                
                if self.method_niif == 'degressive_then_linear' and final_depreciation_date < period_end_depreciation_date:
                    period_end_depreciation_date = final_depreciation_date
                
                if not float_is_zero(amount, precision_rounding=self.currency_id.rounding):
                    depreciation_move_values.append(self._prepare_move_for_asset_depreciation_niif({
                        'amount': amount,
                        'asset_id': self,
                        'depreciation_beginning_date': start_depreciation_date,
                        'date': period_end_depreciation_date,
                        'asset_number_days': days,
                    }))
                
                if period_end_depreciation_date == period_end_fiscalyear_date:
                    start_yearly_period = self.company_id.compute_fiscalyear_dates(
                        period_end_depreciation_date
                    ).get('date_from') + relativedelta(years=1)
                    residual_declining = residual_amount
                
                start_depreciation_date = period_end_depreciation_date + relativedelta(days=1)
        
        return depreciation_move_values
    
    def _compute_board_amount_niif(self, residual_amount, period_start_date, period_end_date,
                                   days_already_depreciated, days_left_to_depreciated, residual_declining,
                                   start_yearly_period=None, total_lifetime_left=None,
                                   residual_at_compute=None, start_recompute_date=None):
        """Calcula el monto de depreciación NIIF para un período"""
        
        if float_is_zero(self.asset_lifetime_days_niif, 2) or float_is_zero(residual_amount, 2):
            return 0, 0
        
        days_until_period_end = self._get_delta_days_niif(self.paused_prorata_date_niif or self.prorata_date_niif, period_end_date)
        days_before_period = self._get_delta_days_niif(
            self.paused_prorata_date_niif or self.prorata_date_niif,
            period_start_date + relativedelta(days=-1)
        )
        days_before_period = max(days_before_period, 0)
        number_days = days_until_period_end - days_before_period
        
        total_depreciable_value_niif = self.original_value_niif - self.salvage_value_niif
        
        # Cálculo según método
        if self.method_niif == 'linear':
            if total_lifetime_left and float_compare(total_lifetime_left, 0, 2) > 0:
                computed_linear_amount = residual_amount - residual_at_compute * (
                    1 - self._get_delta_days_niif(start_recompute_date, period_end_date) / total_lifetime_left
                )
            else:
                computed_linear_amount = self._get_linear_amount_niif(
                    days_before_period, days_until_period_end, total_depreciable_value_niif
                )
            amount = min(computed_linear_amount, residual_amount, key=abs)
            
        elif self.method_niif in ('degressive', 'degressive_then_linear'):
            # Similar al método original pero con parámetros NIIF
            effective_start_date = max(start_yearly_period, self.paused_prorata_date_niif or self.prorata_date_niif) if start_yearly_period else (self.paused_prorata_date_niif or self.prorata_date_niif)
            
            # Calcular monto lineal
            days_left_from_beginning_of_year = self._get_delta_days_niif(
                effective_start_date, 
                period_start_date - relativedelta(days=1)
            ) + days_left_to_depreciated
            
            expected_remaining_value_with_linear = residual_declining - residual_declining * self._get_delta_days_niif(
                effective_start_date, period_end_date
            ) / days_left_from_beginning_of_year
            
            linear_amount = residual_amount - expected_remaining_value_with_linear
            
            # Calcular monto decreciente
            fiscalyear_dates = self.company_id.compute_fiscalyear_dates(period_end_date)
            days_in_fiscalyear = self._get_delta_days_niif(fiscalyear_dates['date_from'], fiscalyear_dates['date_to'])
            
            degressive_total_value = residual_declining * (
                1 - self.method_progress_factor_niif * 
                self._get_delta_days_niif(effective_start_date, period_end_date) / days_in_fiscalyear
            )
            degressive_amount = residual_amount - degressive_total_value
            
            # Elegir el mayor
            amount = self._degressive_linear_amount_niif(residual_amount, degressive_amount, linear_amount)
        
        # Asegurar que el monto tenga el signo correcto
        amount = max(amount, 0) if self.currency_id.compare_amounts(residual_amount, 0) > 0 else min(amount, 0)
        
        # Ajustar al final de la vida útil
        if abs(residual_amount) < abs(amount) or days_until_period_end >= self.asset_lifetime_days_niif:
            amount = residual_amount
        
        return number_days, self.currency_id.round(amount)
    
    def _get_linear_amount_niif(self, days_before_period, days_until_period_end, total_depreciable_value):
        """Calcula el monto lineal NIIF"""
        amount_expected_previous_period = total_depreciable_value * days_before_period / self.asset_lifetime_days_niif
        amount_after_expected = total_depreciable_value * days_until_period_end / self.asset_lifetime_days_niif
        
        # Considerar decrementos de valor
        amount_of_decrease = sum([
            (days_until_period_end - days_before_period) * mv.depreciation_value / 
            (self.asset_lifetime_days_niif - self._get_delta_days_niif(
                self.paused_prorata_date_niif or self.prorata_date_niif, 
                mv.asset_depreciation_beginning_date
            ))
            for mv in self.depreciation_move_niif_ids.filtered(lambda mv: mv.asset_value_change)
        ])
        
        computed_linear_amount = self.currency_id.round(
            amount_after_expected - 
            self.currency_id.round(amount_expected_previous_period) - 
            amount_of_decrease
        )
        
        return computed_linear_amount
    
    def _degressive_linear_amount_niif(self, residual_amount, degressive_amount, linear_amount):
        """Determina el monto entre decreciente y lineal NIIF"""
        if self.currency_id.compare_amounts(residual_amount, 0) > 0:
            return max(degressive_amount, linear_amount)
        else:
            return min(degressive_amount, linear_amount)
    
    def _get_end_period_date_niif(self, start_depreciation_date):
        """Obtiene el final del período NIIF"""
        self.ensure_one()
        
        if not start_depreciation_date:
            return False
        
        fiscalyear_date = self.company_id.compute_fiscalyear_dates(start_depreciation_date).get('date_to')
        period_end_depreciation_date = (
            fiscalyear_date if start_depreciation_date <= fiscalyear_date 
            else fiscalyear_date + relativedelta(years=1)
        )
        
        if self.method_period_niif == '1':  # Si el período es mensual
            max_day_in_month = date_utils.end_of(
                datetime(start_depreciation_date.year, start_depreciation_date.month, 1), 
                'month'
            ).day
            period_end_depreciation_date = min(
                start_depreciation_date.replace(day=max_day_in_month), 
                period_end_depreciation_date
            )
        
        return period_end_depreciation_date
    
    def _get_delta_days_niif(self, start_date, end_date):
        """Calcula días entre 2 fechas para NIIF"""
        self.ensure_one()
        
        if not start_date or not end_date:
            return 0
            
        if self.prorata_computation_type_niif == 'daily_computation':
            return (end_date - start_date).days + 1
        else:
            # Cálculo con 30 días por mes
            start_date_days_month = date_utils.end_of(start_date, 'month').day
            start_prorata = (start_date_days_month - start_date.day + 1) / start_date_days_month
            end_prorata = end_date.day / date_utils.end_of(end_date, 'month').day

            return sum((
                start_prorata * DAYS_PER_MONTH,
                end_prorata * DAYS_PER_MONTH,
                (end_date.year - start_date.year) * DAYS_PER_YEAR,
                (end_date.month - start_date.month - 1) * DAYS_PER_MONTH
            ))
    
    def _get_last_day_asset_niif(self):
        """Obtiene el último día del activo NIIF"""
        if not self.prorata_date_niif:
            return False
            
        this = self.parent_id if self.parent_id else self
        return (
            (this.paused_prorata_date_niif or this.prorata_date_niif) + 
            relativedelta(months=int(this.method_period_niif) * this.method_number_niif, days=-1)
        )
    
    def _prepare_move_for_asset_depreciation_niif(self, vals):
        """Prepara el movimiento de depreciación NIIF"""
        self.ensure_one()
        
        missing_fields = {'amount', 'asset_id', 'depreciation_beginning_date', 'date', 'asset_number_days'} - set(vals)
        if missing_fields:
            raise UserError(_('Faltan campos requeridos: %s') % ', '.join(missing_fields))
        
        amount = vals['amount']
        
        # Usar cuentas NIIF si están configuradas, sino usar las normales
        depreciation_account = self.account_depreciation_niif_id or self.account_depreciation_id
        expense_account = self.account_expense_niif_id or self.account_depreciation_expense_id
        journal = self.journal_niif_id or self.journal_id
        
        if not depreciation_account or not expense_account:
            raise UserError(
                _('Configure las cuentas NIIF para el activo %s') % self.name
            )
        
        # Analytic distribution
        analytic_distribution = {}
        if self.analytic_distribution:
            analytic_distribution = self.analytic_distribution
        
        # Partner de las líneas originales
        partner = self.original_move_line_ids.mapped('partner_id')
        partner = partner[:1] if len(partner) <= 1 else self.env['res.partner']
        
        move_line_1 = {
            'name': self.name + ' (NIIF)',
            'partner_id': partner.id,
            'account_id': expense_account.id,
            'debit': amount if amount > 0 else 0.0,
            'credit': -amount if amount < 0 else 0.0,
            'analytic_distribution': analytic_distribution,
        }
        
        move_line_2 = {
            'name': self.name + ' (NIIF)',
            'partner_id': partner.id,
            'account_id': depreciation_account.id,
            'debit': -amount if amount < 0 else 0.0,
            'credit': amount if amount > 0 else 0.0,
        }
        
        move_vals = {
            'asset_niif_id': self.id,
            'ref': f"NIIF: {self.name}",
            'partner_id': partner.id,
            'is_niif_depreciation': True,
            'asset_depreciation_beginning_date': vals['depreciation_beginning_date'],
            'asset_number_days': vals.get('asset_number_days', 0),
            'date': vals['date'],
            'journal_id': journal.id,
            'move_type': 'entry',
            'currency_id': self.currency_id.id,
            'depreciation_value': amount,
            'asset_move_type': 'depreciation',
            'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
        }
        
        return move_vals
    
    def set_to_close(self, invoice_line_ids=None, date=None, message=None):
        """Override para cerrar también NIIF cuando aplica"""
        result = super().set_to_close(invoice_line_ids, date, message)
        
        # Si es dual, cerrar también NIIF
        for asset in self:
            if asset.accounting_framework == 'dual' and asset.state_niif == 'open':
                asset.set_to_close_niif(date, message)
        
        return result
    
    def set_to_close_niif(self, date=None, message=None):
        """Cierra el activo NIIF"""
        for asset in self:
            if asset.state_niif != 'open':
                continue
                
            disposal_date = date or fields.Date.today()
            
            # Crear movimiento hasta la fecha de disposición
            asset._create_move_before_date_niif(disposal_date)
            
            # Cambiar estado
            asset.state_niif = 'close'
            asset.disposal_date_niif = disposal_date
            
            # Mensaje en chatter
            asset.message_post(
                body=_('Activo NIIF cerrado. %s') % (message if message else ""),
                subtype_xmlid='mail.mt_note'
            )
    
    def _create_move_before_date_niif(self, date):
        """Crea movimiento NIIF antes de una fecha específica"""
        if not self.prorata_date_niif:
            return
            
        all_move_dates_before_date = (
            self.depreciation_move_niif_ids.filtered(
                lambda x: x.date <= date and 
                not x.reversal_move_ids and 
                not x.reversed_entry_id and 
                x.state == 'posted'
            ).sorted('date')
        ).mapped('date')
        
        if all_move_dates_before_date:
            last_move_date = max(all_move_dates_before_date)
            beginning_depreciation_date = last_move_date + relativedelta(days=1)
        else:
            beginning_depreciation_date = self.paused_prorata_date_niif or self.prorata_date_niif
        
        # Cancelar movimientos futuros
        self._cancel_future_moves_niif(date)
        
        # Calcular y crear el movimiento parcial si es necesario
        if beginning_depreciation_date <= date:
            residual_amount = self.value_residual_niif
            if not float_is_zero(residual_amount, precision_rounding=self.currency_id.rounding):
                last_day_asset = self._get_last_day_asset_niif()
                lifetime_left = self._get_delta_days_niif(beginning_depreciation_date, last_day_asset)
                
                days, amount = self._compute_board_amount_niif(
                    residual_amount, beginning_depreciation_date, date,
                    False, lifetime_left, residual_amount, beginning_depreciation_date,
                    lifetime_left, residual_amount, beginning_depreciation_date
                )
                
                if not float_is_zero(amount, precision_rounding=self.currency_id.rounding):
                    move_vals = self._prepare_move_for_asset_depreciation_niif({
                        'amount': amount,
                        'asset_id': self,
                        'depreciation_beginning_date': beginning_depreciation_date,
                        'date': date,
                        'asset_number_days': days,
                    })
                    new_move = self.env['account.move'].create(move_vals)
                    new_move._post()
    
    def _cancel_future_moves_niif(self, date):
        """Cancela movimientos NIIF futuros"""
        for asset in self:
            obsolete_moves = asset.depreciation_move_niif_ids.filtered(
                lambda m: m.state == 'draft' or (
                    not m.reversal_move_ids and
                    not m.reversed_entry_id and
                    m.state == 'posted' and
                    m.date > date
                )
            )
            obsolete_moves._unlink_or_reverse()
    
    def set_to_cancelled(self):
        """Override para cancelar también NIIF"""
        super().set_to_cancelled()
        
        for asset in self:
            if asset.accounting_framework in ('niif', 'dual'):
                asset.set_to_cancelled_niif()
    
    def set_to_cancelled_niif(self):
        """Cancela el activo NIIF"""
        for asset in self:
            posted_moves = asset.depreciation_move_niif_ids.filtered(
                lambda m: (
                    not m.reversal_move_ids and
                    not m.reversed_entry_id and
                    m.state == 'posted'
                )
            )
            
            if posted_moves:
                # Cancelar todos los movimientos futuros
                asset._cancel_future_moves_niif(datetime.min)
                msg = _('Activo NIIF Cancelado')
                asset.message_post(body=msg, subtype_xmlid='mail.mt_note')
            
            # Eliminar movimientos draft
            asset.depreciation_move_niif_ids.filtered(
                lambda m: m.state == 'draft'
            ).with_context(force_delete=True).unlink()
            
            # Cambiar estado
            asset.asset_paused_days_niif = 0
            asset.state_niif = 'cancelled'
    
    def _check_depreciations_niif(self):
        """Verifica que las depreciaciones NIIF sean correctas"""
        for asset in self:
            if (
                asset.state_niif == 'open'
                and asset.depreciation_move_niif_ids
                and not asset.currency_id.is_zero(
                    asset.depreciation_move_niif_ids.sorted(lambda x: (x.date, x.id))[-1].asset_remaining_value
                )
            ):
                raise UserError(_("El valor restante en la última línea de depreciación NIIF debe ser 0"))
    
    def _get_own_book_value_niif(self, date=None):
        """Obtiene el valor en libros NIIF"""
        self.ensure_one()
        if date:
            return self._get_residual_value_niif_at_date(date) + self.salvage_value_niif
        else:
            return self.value_residual_niif + self.salvage_value_niif
    
    def _get_residual_value_niif_at_date(self, date):
        """Obtiene el valor residual NIIF en una fecha específica"""
        self.ensure_one()
        
        if not date or not self.prorata_date_niif:
            return 0
        
        # Depreciaciones anteriores a la fecha
        current_and_previous_depreciation = self.depreciation_move_niif_ids.filtered(
            lambda mv: mv.asset_depreciation_beginning_date < date and not mv.reversed_entry_id
        ).sorted('asset_depreciation_beginning_date', reverse=True)
        
        if not current_and_previous_depreciation:
            return self.original_value_niif - self.salvage_value_niif - self.already_depreciated_amount_import_niif
        
        if len(current_and_previous_depreciation) > 1:
            previous_value_residual = current_and_previous_depreciation[1].asset_remaining_value
        else:
            previous_value_residual = self.original_value_niif - self.salvage_value_niif - self.already_depreciated_amount_import_niif
        
        # Calcular proporción del período
        cur_depr_end_date = self._get_end_period_date_niif(date)
        current_depreciation = current_and_previous_depreciation[0]
        cur_depr_beg_date = current_depreciation.asset_depreciation_beginning_date
        
        rate = self._get_delta_days_niif(cur_depr_beg_date, date) / self._get_delta_days_niif(cur_depr_beg_date, cur_depr_end_date)
        lost_value_at_date = (previous_value_residual - current_depreciation.asset_remaining_value) * rate
        residual_value_at_date = self.currency_id.round(previous_value_residual - lost_value_at_date)
        
        if self.currency_id.compare_amounts(self.original_value_niif, 0) > 0:
            return max(residual_value_at_date, 0)
        else:
            return min(residual_value_at_date, 0)
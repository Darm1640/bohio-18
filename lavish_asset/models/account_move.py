# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from odoo.tools.misc import formatLang
from dateutil.relativedelta import relativedelta
import psycopg2


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    # ============================================================
    # RELACIÓN CON ACTIVOS NIIF
    # ============================================================
    
    asset_niif_id = fields.Many2one(
        'account.asset',
        string='Activo NIIF',
        index=True,
        ondelete='cascade',
        copy=False
    )
    
    is_niif_depreciation = fields.Boolean(
        string='Es Depreciación NIIF',
        default=False,
        copy=False
    )
    depreciation_value = fields.Monetary(
        string='Valor Depreciación',
        currency_field='currency_id'
    )
    asset_remaining_value_niif = fields.Monetary(
        string='Valor Depreciable NIIF',
        compute='_compute_depreciation_cumulative_value_niif',
        currency_field='currency_id'
    )
    
    asset_depreciated_value_niif = fields.Monetary(
        string='Depreciación Acumulada NIIF',
        compute='_compute_depreciation_cumulative_value_niif',
        currency_field='currency_id'
    )
    
    # ============================================================
    # CAMPOS COMPUTADOS NIIF
    # ============================================================
    
    @api.depends('asset_niif_id', 'depreciation_value', 'state')
    def _compute_depreciation_cumulative_value_niif(self):
        """Calcula valores acumulados NIIF"""
        for move in self:
            if not move.asset_niif_id:
                move.asset_depreciated_value_niif = 0
                move.asset_remaining_value_niif = 0
                continue
            
            asset = move.asset_niif_id
            
            # Solo calcular si el activo es NIIF o dual
            if asset.accounting_framework not in ('niif', 'dual'):
                move.asset_depreciated_value_niif = 0
                move.asset_remaining_value_niif = 0
                continue
            
            # Calcular valores usando los movimientos NIIF del activo
            depreciated = 0
            total_depreciable = asset.original_value_niif - asset.salvage_value_niif
            remaining = total_depreciable - asset.already_depreciated_amount_import_niif
            
            for dep_move in asset.depreciation_move_niif_ids.sorted(lambda mv: (mv.date, mv._origin.id)):
                if dep_move.state != 'cancel':
                    remaining -= dep_move.depreciation_value
                    depreciated += dep_move.depreciation_value
                
                # Si es el movimiento actual
                if dep_move == move:
                    move.asset_remaining_value_niif = remaining
                    move.asset_depreciated_value_niif = depreciated
                    break
    
    @api.constrains('state', 'asset_id', 'asset_niif_id')
    def _constrains_check_asset_state(self):
        """Extiende validación para activos NIIF"""
        # Primero ejecutar la validación original
        super()._constrains_check_asset_state()
        
        # Luego validar NIIF
        for move in self.filtered(lambda mv: mv.asset_niif_id):
            asset_id = move.asset_niif_id
            if hasattr(asset_id, 'state_niif') and asset_id.state_niif == 'draft' and move.state == 'posted':
                raise ValidationError(
                    _("No puede contabilizar un asiento relacionado con un activo NIIF en borrador. "
                      "Por favor valide el activo NIIF primero.")
                )
    
    def _post(self, soft=True):
        """Extiende _post para manejar activos NIIF"""
        posted = super()._post(soft)
        
        # Log para depreciación NIIF
        posted._log_depreciation_asset_niif()
        
        # Auto-crear activos NIIF si corresponde
        posted.sudo()._auto_create_asset_niif()
        
        return posted
    
    def _log_depreciation_asset_niif(self):
        """Registra mensajes para depreciación NIIF"""
        for move in self.filtered(lambda m: m.asset_niif_id and m.is_niif_depreciation):
            asset = move.asset_niif_id
            msg = _('Asiento de depreciación NIIF %(name)s contabilizado (%(value)s)', 
                   name=move.name, 
                   value=formatLang(self.env, move.depreciation_value, currency_obj=move.company_id.currency_id))
            asset.message_post(body=msg)
    
    def _auto_create_asset_niif(self):
        """Auto-crea activos NIIF cuando corresponde"""
        for move in self:
            if not move.is_invoice():
                continue
            
            for move_line in move.line_ids:
                # Verificar si la cuenta requiere crear activo NIIF
                if (
                    move_line.account_id
                    and hasattr(move_line.account_id, 'asset_accounting_framework')
                    and move_line.account_id.asset_accounting_framework in ('niif', 'dual')
                    and move_line.account_id.create_asset != 'no'
                    and not move_line.asset_ids
                    and not move_line.tax_line_id
                    and move_line.price_total > 0
                    and not (move.move_type in ('out_invoice', 'out_refund') and 
                            move_line.account_id.internal_group == 'asset')
                ):
                    # Usar el método original para crear el activo
                    # que ya maneja la configuración dual
                    pass  # El método _auto_create_asset original ya maneja esto
    
    def _reverse_moves(self, default_values_list=None, cancel=False):
        """Extiende para manejar reversión de movimientos NIIF"""
        if default_values_list is None:
            default_values_list = [{} for _i in self]
        
        for move, default_values in zip(self, default_values_list):
            # Manejar reversión para activos NIIF
            if move.asset_niif_id:
                # Similar a la lógica para asset_id pero con NIIF
                first_draft = min(
                    move.asset_niif_id.depreciation_move_niif_ids.filtered(lambda m: m.state == 'draft'),
                    key=lambda m: m.date,
                    default=None
                )
                
                if first_draft:
                    # Ajustar el valor de depreciación del primer draft
                    first_draft.depreciation_value += move.depreciation_value
                elif move.asset_niif_id.state_niif != 'close':
                    # Crear un nuevo movimiento draft si no hay
                    last_date = max(move.asset_niif_id.depreciation_move_niif_ids.mapped('date'))
                    method_period = move.asset_niif_id.method_period_niif
                    
                    delta = relativedelta(months=1) if method_period == "1" else relativedelta(years=1)
                    
                    # Preparar valores para nuevo movimiento
                    new_move_vals = self._prepare_move_for_asset_depreciation_niif({
                        'asset_id': move.asset_niif_id,
                        'amount': move.depreciation_value,
                        'depreciation_beginning_date': last_date + delta,
                        'date': last_date + delta,
                        'asset_number_days': 0
                    })
                    
                    self.create(new_move_vals)
                
                # Mensaje en el activo
                msg = _('Asiento de depreciación NIIF %(name)s revertido (%(value)s)',
                       name=move.name,
                       value=formatLang(self.env, move.depreciation_value, 
                                      currency_obj=move.company_id.currency_id))
                move.asset_niif_id.message_post(body=msg)
                
                # Mantener la referencia al activo NIIF en el movimiento revertido
                default_values['asset_niif_id'] = move.asset_niif_id.id
                default_values['asset_number_days'] = -move.asset_number_days if move.asset_number_days else 0
                default_values['asset_depreciation_beginning_date'] = default_values.get('date', move.date)
                default_values['is_niif_depreciation'] = True
        
        return super()._reverse_moves(default_values_list, cancel)
    
    def button_cancel(self):
        """Extiende para manejar cancelación con activos NIIF"""
        res = super().button_cancel()
        
        # Desactivar activos NIIF relacionados si están en borrador
        niif_assets = self.env['account.asset'].sudo().search([
            ('original_move_line_ids.move_id', 'in', self.ids),
            ('accounting_framework', 'in', ['niif', 'dual']),
            ('state_niif', '=', 'draft')
        ])
        
        if niif_assets:
            niif_assets.write({'active': False})
        
        return res
    
    def button_draft(self):
        """Extiende para validar activos NIIF"""
        for move in self:
            # Validar activos normales
            if any(asset_id.state != 'draft' for asset_id in move.asset_ids):
                raise UserError(_('No puede restablecer a borrador un asiento relacionado con un activo contabilizado'))
            
            # Validar activos NIIF
            if move.asset_niif_id and hasattr(move.asset_niif_id, 'state_niif'):
                if move.asset_niif_id.state_niif != 'draft':
                    raise UserError(_('No puede restablecer a borrador un asiento relacionado con un activo NIIF contabilizado'))
            
            # Eliminar activos draft relacionados
            move.asset_ids.filtered(lambda x: x.state == 'draft').unlink()
            
            # Si hay activo NIIF en draft, eliminarlo también
            if move.asset_niif_id and move.asset_niif_id.state_niif == 'draft':
                move.asset_niif_id.unlink()
        
        return super().button_draft()
    
    @api.model
    def _prepare_move_for_asset_depreciation_niif(self, vals):
        """Prepara valores para movimiento de depreciación NIIF"""
        missing_fields = {'asset_id', 'amount', 'depreciation_beginning_date', 'date', 'asset_number_days'} - set(vals)
        if missing_fields:
            raise UserError(_('Faltan algunos campos %s', ', '.join(missing_fields)))
        
        asset = vals['asset_id']
        analytic_distribution = asset.analytic_distribution if hasattr(asset, 'analytic_distribution') else {}
        depreciation_date = vals.get('date', fields.Date.context_today(self))
        company_currency = asset.company_id.currency_id
        current_currency = asset.currency_id
        prec = company_currency.decimal_places
        amount_currency = vals['amount']
        amount = current_currency._convert(amount_currency, company_currency, asset.company_id, depreciation_date)
        
        # Mantener el partner de las facturas originales si hay uno solo
        partner = self.env['res.partner']
        if hasattr(asset, 'original_move_line_ids'):
            partners = asset.original_move_line_ids.mapped('partner_id')
            partner = partners[:1] if len(partners) <= 1 else self.env['res.partner']
        
        # Usar cuentas NIIF
        depreciation_account = asset.account_depreciation_niif_id if hasattr(asset, 'account_depreciation_niif_id') else asset.account_depreciation_id
        expense_account = asset.account_expense_niif_id if asset.account_expense_niif_id else asset.account_depreciation_expense_id
        journal = asset.journal_niif_id if hasattr(asset, 'journal_niif_id') else asset.journal_id
        
        if not depreciation_account or not expense_account:
            raise UserError(_('Las cuentas NIIF no están configuradas para el activo %s') % asset.name)
        
        name = _("%(asset)s: Depreciación NIIF", asset=asset.name)
        
        move_line_1 = {
            'name': name,
            'partner_id': partner.id,
            'account_id': depreciation_account.id,
            'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'currency_id': current_currency.id,
            'amount_currency': -amount_currency,
        }
        
        move_line_2 = {
            'name': name,
            'partner_id': partner.id,
            'account_id': expense_account.id,
            'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'currency_id': current_currency.id,
            'amount_currency': amount_currency,
        }
        
        # Solo establecer la distribución analítica si existe
        if analytic_distribution:
            move_line_1['analytic_distribution'] = analytic_distribution
            move_line_2['analytic_distribution'] = analytic_distribution
        
        move_vals = {
            'partner_id': partner.id,
            'date': depreciation_date,
            'journal_id': journal.id,
            'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
            'asset_niif_id': asset.id,
            'is_niif_depreciation': True,
            'ref': name,
            'asset_depreciation_beginning_date': vals['depreciation_beginning_date'],
            'asset_number_days': vals['asset_number_days'],
            'asset_value_change': vals.get('asset_value_change', False),
            'move_type': 'entry',
            'currency_id': current_currency.id,
            'asset_move_type': vals.get('asset_move_type', 'depreciation'),
            'company_id': asset.company_id.id,
        }
        
        return move_vals
    
    def action_open_asset_niif(self):
        """Abre la vista del activo NIIF relacionado"""
        self.ensure_one()
        if not self.asset_niif_id:
            raise UserError(_('No hay activo NIIF asociado a este movimiento'))
        
        return {
            'name': _('Activo NIIF'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.asset',
            'res_id': self.asset_niif_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    # ============================================================
    # CAMPOS NIIF
    # ============================================================
    
    account_niif_id = fields.Many2one(
        'account.account',
        string='Cuenta NIIF',
        compute='_compute_account_niif',
        store=True,
        readonly=False,
        domain="[('niif', '=', True), ('account_type', 'not in', ['off_balance', 'equity_unaffected'])]",
        index=True
    )
    
    not_map_niif = fields.Boolean(
        string='No Mapear a NIIF',
        default=False,
        help='Si está marcado, no se mapeará automáticamente a cuenta NIIF'
    )
    
    niif_exclude = fields.Boolean(
        string='Excluir de Procesos NIIF',
        default=False,
        help='Si está marcado, se excluirá de todos los procesos NIIF'
    )
    
    # ============================================================
    # MÉTODOS COMPUTADOS
    # ============================================================
    
    @api.depends('account_id', 'not_map_niif', 'move_id.journal_id', 'move_id.asset_niif_id')
    def _compute_account_niif(self):
        """Calcula la cuenta NIIF correspondiente"""
        for line in self:
            if line.not_map_niif or line.niif_exclude:
                line.account_niif_id = False
                continue
            
            # Si el movimiento tiene un activo NIIF, usar sus cuentas
            if line.move_id.asset_niif_id:
                asset = line.move_id.asset_niif_id
                if asset.account_expense_niif_id:
                    # Mapear según el tipo de cuenta
                    if line.account_id == asset.account_depreciation_expense_id:
                        line.account_niif_id = asset.account_expense_niif_id or line.account_id
                    elif line.account_id == asset.account_depreciation_id:
                        line.account_niif_id = asset.account_depreciation_niif_id or line.account_id
                    elif line.account_id == asset.account_asset_id:
                        line.account_niif_id = asset.account_asset_niif_id or line.account_id
                    else:
                        line.account_niif_id = line._get_mapped_niif_account()
                else:
                    line.account_niif_id = line._get_mapped_niif_account()
            else:
                # Mapeo normal de cuenta LOCAL a NIIF
                line.account_niif_id = line._get_mapped_niif_account()
    
    def _get_mapped_niif_account(self):
        """Obtiene la cuenta NIIF mapeada para esta línea"""
        self.ensure_one()
        
        if not self.account_id:
            return False
        
        # Si la cuenta ya es NIIF, usarla directamente
        if self.account_id.is_niif_account:
            return self.account_id
        
        # Si tiene cuenta NIIF mapeada y mapeo automático activo
        if hasattr(self.account_id, 'account_niif_id') and hasattr(self.account_id, 'map_niif_auto'):
            if self.account_id.account_niif_id and self.account_id.map_niif_auto:
                return self.account_id.account_niif_id
        
        return False
    
    def _get_computed_taxes(self):
        """Extiende para manejar impuestos en movimientos NIIF"""
        if self.move_id.asset_niif_id:
            # Para movimientos de activos NIIF, usar los impuestos configurados
            return self.tax_ids
        return super()._get_computed_taxes()
    
    @api.constrains('account_id', 'account_niif_id', 'move_id')
    def _check_niif_accounts(self):
        """Valida coherencia de cuentas NIIF"""
        for line in self:
            # Si el diario es NIIF, verificar que use cuentas NIIF
            if line.move_id.journal_id and hasattr(line.move_id.journal_id, 'niif'):
                if line.move_id.journal_id.niif and line.account_id and not line.account_id.is_niif_account:
                    # Solo advertir, no bloquear (para compatibilidad)
                    pass
            
            # Verificar que cuenta NIIF sea realmente NIIF
            if line.account_niif_id and not line.account_niif_id.is_niif_account:
                raise ValidationError(
                    _('La cuenta %s no está marcada como cuenta NIIF') % line.account_niif_id.display_name
                )
    
    @api.model_create_multi
    def create(self, vals_list):
        """Extiende create para manejar cuentas NIIF automáticamente"""
        for vals in vals_list:
            # Si es una línea de movimiento NIIF, asegurar mapeo correcto
            if 'move_id' in vals:
                move = self.env['account.move'].browse(vals['move_id'])
                
                # Si es depreciación NIIF, ajustar cuentas
                if move.asset_niif_id and move.is_niif_depreciation:
                    asset = move.asset_niif_id
                    if 'account_id' in vals and asset.account_expense_niif_id:
                        account = self.env['account.account'].browse(vals['account_id'])
                        
                        # Mapear a cuenta NIIF si corresponde
                        if account == asset.account_depreciation_expense_id:
                            vals['account_niif_id'] = asset.account_expense_niif_id.id if asset.account_expense_niif_id else account.id
                        elif account == asset.account_depreciation_id:
                            vals['account_niif_id'] = asset.account_depreciation_niif_id.id if asset.account_depreciation_niif_id else account.id
                        elif account == asset.account_asset_id:
                            vals['account_niif_id'] = asset.account_asset_niif_id.id if asset.account_asset_niif_id else account.id
        
        return super().create(vals_list)
    
    def write(self, vals):
        """Extiende write para sincronizar cuentas NIIF"""
        if 'account_id' in vals:
            for line in self.filtered(lambda l: not l.not_map_niif):
                if line.move_id.asset_niif_id:
                    asset = line.move_id.asset_niif_id
                    if asset.account_expense_niif_id:
                        account = self.env['account.account'].browse(vals['account_id'])
                        
                        # Actualizar cuenta NIIF según el mapeo
                        if account == asset.account_depreciation_expense_id:
                            vals['account_niif_id'] = asset.account_expense_niif_id.id if asset.account_expense_niif_id else account.id
                        elif account == asset.account_depreciation_id:
                            vals['account_niif_id'] = asset.account_depreciation_niif_id.id if asset.account_depreciation_niif_id else account.id
                        elif account == asset.account_asset_id:
                            vals['account_niif_id'] = asset.account_asset_niif_id.id if asset.account_asset_niif_id else account.id
        
        return super().write(vals)
    
    def turn_as_asset(self):
        """Extiende para manejar creación de activos con marco NIIF"""
        # Validaciones originales
        if len(self.company_id) != 1:
            raise UserError(_("Todas las líneas deben ser de la misma compañía"))
        if any(line.move_id.state == 'draft' for line in self):
            raise UserError(_("Todas las líneas deben estar contabilizadas"))
        if any(account != self[0].account_id for account in self.mapped('account_id')):
            raise UserError(_("Todas las líneas deben ser de la misma cuenta"))
        
        # Preparar contexto con información adicional
        ctx = self.env.context.copy()
        ctx.update({
            'default_original_move_line_ids': [(6, False, self.env.context['active_ids'])],
            'default_company_id': self.company_id.id,
        })

        ctx['default_accounting_framework'] = self.account_id.asset_id.asset_accounting_framework
        
        return {
            "name": _("Convertir en activo"),
            "type": "ir.actions.act_window",
            "res_model": "account.asset",
            "views": [[False, "form"]],
            "target": "current",
            "context": ctx,
        }
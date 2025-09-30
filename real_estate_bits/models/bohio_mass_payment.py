from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import logging

_logger = logging.getLogger(__name__)


class BohioMassPayment(models.Model):
    _name = 'bohio.mass.payment'
    _description = 'Bohio - Pago Masivo con Simulación'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char('Número', default='/', readonly=True, copy=False)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    # FILTROS DE SELECCIÓN
    date = fields.Date('Fecha de Proceso', default=fields.Date.today, required=True, tracking=True)
    simulation_month = fields.Date('Mes de Simulación', required=True, tracking=True,
                                  help='Mes para el cual se simularán los pagos')

    # FILTROS GEOGRÁFICOS
    region_ids = fields.Many2many('region.region', string='Regiones')
    city_ids = fields.Many2many('res.city', string='Ciudades')
    project_ids = fields.Many2many('project.worksite', string='Proyectos')

    # FILTROS POR TIPO DE TERCERO Y TAGS
    partner_tag_ids = fields.Many2many('res.partner.category', string='Etiquetas de Terceros')
    partner_type_filter = fields.Selection([
        ('all', 'Todos'),
        ('customer', 'Solo Clientes'),
        ('supplier', 'Solo Proveedores'),
        ('owner', 'Solo Propietarios')
    ], string='Tipo de Tercero', default='all')

    # FILTROS DE CONTRATO
    contract_ids = fields.Many2many('property.contract', string='Contratos Específicos')
    include_overdue = fields.Boolean('Incluir Morosos', default=True)
    include_novelties = fields.Boolean('Incluir Novedades', default=True)
    include_loans = fields.Boolean('Incluir Préstamos', default=True)

    # ESTADO DEL PROCESO
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('simulated', 'Simulado'),
        ('confirmed', 'Confirmado'),
        ('processed', 'Procesado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft', tracking=True)

    # LÍNEAS DE SIMULACIÓN
    simulation_line_ids = fields.One2many('bohio.mass.payment.line', 'mass_payment_id',
                                          string='Líneas de Simulación')
    debit_note_ids = fields.One2many('bohio.debit.note', 'mass_payment_id',
                                     string='Notas Débito')
    payment_ids = fields.One2many('account.payment', 'bohio_mass_payment_id',
                                  string='Pagos Creados')

    # TOTALES CALCULADOS
    total_canon = fields.Monetary('Total Canon', compute='_compute_totals', store=True)
    total_commission = fields.Monetary('Total Comisión', compute='_compute_totals', store=True)
    total_taxes = fields.Monetary('Total Impuestos', compute='_compute_totals', store=True)
    total_novelties = fields.Monetary('Total Novedades', compute='_compute_totals', store=True)
    total_loans = fields.Monetary('Total Préstamos', compute='_compute_totals', store=True)
    total_interest = fields.Monetary('Total Intereses', compute='_compute_totals', store=True)
    total_to_pay = fields.Monetary('Total a Pagar', compute='_compute_totals', store=True)
    total_received = fields.Monetary('Total Recibido', compute='_compute_totals', store=True)

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    # CONFIGURACIÓN
    journal_id = fields.Many2one('account.journal', string='Diario de Pagos',
                                 domain=[('type', 'in', ['bank', 'cash'])], required=True)
    auto_post = fields.Boolean('Auto-confirmar Pagos', default=False)
    separate_payments = fields.Boolean('Pagos Separados por Propietario',
                                       default=True, help='Crear un pago separado por cada propietario')

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('bohio.mass.payment') or '/'
        return super().create(vals)

    @api.depends('simulation_line_ids.canon_amount', 'simulation_line_ids.commission_amount',
                 'simulation_line_ids.tax_amount', 'simulation_line_ids.novelty_amount',
                 'simulation_line_ids.loan_amount', 'simulation_line_ids.interest_amount',
                 'simulation_line_ids.net_to_pay')
    def _compute_totals(self):
        for record in self:
            lines = record.simulation_line_ids.filtered(lambda l: not l.skip_payment)
            record.total_canon = sum(lines.mapped('canon_amount'))
            record.total_commission = sum(lines.mapped('commission_amount'))
            record.total_taxes = sum(lines.mapped('tax_amount'))
            record.total_novelties = sum(lines.mapped('novelty_amount'))
            record.total_loans = sum(lines.mapped('loan_amount'))
            record.total_interest = sum(lines.mapped('interest_amount'))
            record.total_to_pay = sum(lines.mapped('net_to_pay'))
            record.total_received = sum(lines.mapped('canon_amount'))

    def action_simulate(self):
        """Simular pagos para el mes especificado"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Solo se pueden simular pagos en estado borrador'))

        # Limpiar líneas existentes
        self.simulation_line_ids.unlink()

        # Obtener contratos filtrados
        contracts = self._get_filtered_contracts()
        if not contracts:
            raise UserError(_('No se encontraron contratos que cumplan los filtros especificados'))

        # Generar líneas de simulación
        lines_to_create = []
        for contract in contracts:
            lines = self._generate_simulation_lines(contract)
            lines_to_create.extend(lines)

        # Crear las líneas
        if lines_to_create:
            self.simulation_line_ids = [(0, 0, line) for line in lines_to_create]

        # Cambiar estado
        self.state = 'simulated'

        # Mensaje de confirmación
        self.message_post(
            body=_('Simulación completada. Se generaron %d líneas para %d contratos.') %
                 (len(lines_to_create), len(contracts))
        )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bohio.mass.payment',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _get_filtered_contracts(self):
        """Obtener contratos según los filtros aplicados"""
        domain = [('state', '=', 'confirmed')]

        # Filtros geográficos
        if self.region_ids:
            domain.append(('region_id', 'in', self.region_ids.ids))
        if self.project_ids:
            domain.append(('project_id', 'in', self.project_ids.ids))

        # Filtros por etiquetas de partner
        if self.partner_tag_ids:
            if self.partner_type_filter == 'owner':
                domain.append(('partner_is_owner_id.category_id', 'in', self.partner_tag_ids.ids))
            else:
                domain.append(('partner_id.category_id', 'in', self.partner_tag_ids.ids))

        # Contratos específicos
        if self.contract_ids:
            domain.append(('id', 'in', self.contract_ids.ids))

        return self.env['property.contract'].search(domain)

    def _generate_simulation_lines(self, contract):
        """Generar líneas de simulación para un contrato"""
        lines = []

        # Obtener cuotas del mes especificado
        month_start = self.simulation_month.replace(day=1)
        month_end = month_start + relativedelta(months=1, days=-1)

        loan_lines = contract.loan_line_ids.filtered(
            lambda l: month_start <= l.date <= month_end
        )

        if not loan_lines:
            return lines

        # Procesar cada propietario
        if contract.is_multi_propietario and contract.property_id.owners_lines:
            for owner_line in contract.property_id.owners_lines:
                owner_data = self._calculate_owner_amounts(
                    contract, owner_line.partner_id, owner_line.percentage, loan_lines
                )
                if owner_data['net_to_pay'] != 0:
                    lines.append(owner_data)
        else:
            # Un solo propietario
            owner_data = self._calculate_owner_amounts(
                contract, contract.partner_is_owner_id, 100.0, loan_lines
            )
            if owner_data['net_to_pay'] != 0:
                lines.append(owner_data)

        return lines

    def _calculate_owner_amounts(self, contract, partner, percentage, loan_lines):
        """Calcular montos para un propietario específico"""
        percentage_decimal = percentage / 100.0

        # Calcular monto base del canon
        canon_total = sum(loan_lines.mapped('amount'))
        canon_amount = canon_total * percentage_decimal

        # Calcular comisión
        commission_rate = contract.commission_percentage / 100.0
        commission_amount = canon_amount * commission_rate

        # Calcular impuestos sobre comisión
        tax_amount = 0.0
        if contract.apply_tax and self.env.company.account_sale_tax_id:
            tax_result = contract.env.company.account_sale_tax_id.compute_all(
                commission_amount, currency=contract.company_id.currency_id
            )
            tax_amount = sum(tax['amount'] for tax in tax_result['taxes'])

        # Calcular novedades
        novelty_amount = 0.0
        if self.include_novelties:
            novelties = contract.novedad_ids.filtered(
                lambda n: n.state in ['confirmed', 'done'] and
                         n.destinatario in ['propietario', 'all'] and
                         n.fecha_cobro and
                         self.simulation_month.replace(day=1) <= n.fecha_cobro <=
                         (self.simulation_month + relativedelta(months=1, days=-1))
            )
            for novelty in novelties:
                if novelty.destinatario == 'propietario':
                    novelty_amount += novelty.valor_total * percentage_decimal
                elif novelty.destinatario == 'all':
                    novelty_amount += novelty.valor_total * (novelty.percentage_propietario / 100) * percentage_decimal

        # Calcular préstamos (buscar en custom_account_treasury si existe)
        loan_amount = 0.0
        if self.include_loans:
            # Buscar préstamos pendientes del propietario
            advance_payments = self.env['account.move.line'].search([
                ('partner_id', '=', partner.id),
                ('account_id.code', 'like', '13%'),  # Cuentas de préstamos
                ('amount_residual', '>', 0),
                ('move_id.state', '=', 'posted')
            ])
            loan_amount = sum(advance_payments.mapped('amount_residual')) * percentage_decimal

        # Calcular intereses por mora
        interest_amount = 0.0
        if self.include_overdue and contract.apply_interest:
            for loan_line in loan_lines.filtered('is_overdue'):
                days_overdue = (self.date - loan_line.date).days
                if days_overdue > contract.interest_days_grace:
                    line_interest = contract.compute_interest(
                        loan_line.amount * percentage_decimal, days_overdue
                    )
                    interest_amount += line_interest

        # Calcular neto a pagar
        net_to_pay = canon_amount - commission_amount - tax_amount - novelty_amount - loan_amount + interest_amount

        return {
            'mass_payment_id': self.id,
            'contract_id': contract.id,
            'partner_id': partner.id,
            'partner_percentage': percentage,
            'canon_amount': canon_amount,
            'commission_amount': commission_amount,
            'tax_amount': tax_amount,
            'novelty_amount': novelty_amount,
            'loan_amount': loan_amount,
            'interest_amount': interest_amount,
            'net_to_pay': net_to_pay,
            'skip_payment': False,
            'notes': '',
        }

    def action_confirm(self):
        """Confirmar la simulación"""
        self.ensure_one()
        if self.state != 'simulated':
            raise UserError(_('Solo se pueden confirmar simulaciones ya calculadas'))

        if not self.simulation_line_ids.filtered(lambda l: not l.skip_payment):
            raise UserError(_('No hay líneas válidas para procesar'))

        self.state = 'confirmed'

    def action_process_payments(self):
        """Procesar los pagos reales"""
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_('Solo se pueden procesar pagos confirmados'))

        created_payments = []

        if self.separate_payments:
            # Crear un pago separado por cada propietario
            grouped_lines = {}
            for line in self.simulation_line_ids.filtered(lambda l: not l.skip_payment):
                if line.partner_id not in grouped_lines:
                    grouped_lines[line.partner_id] = []
                grouped_lines[line.partner_id].append(line)

            for partner, lines in grouped_lines.items():
                payment = self._create_payment_for_partner(partner, lines)
                if payment:
                    created_payments.append(payment)
        else:
            # Crear un solo pago consolidado (no recomendado por privacidad)
            payment = self._create_consolidated_payment()
            if payment:
                created_payments.append(payment)

        # Auto-confirmar si está habilitado
        if self.auto_post:
            for payment in created_payments:
                payment.action_post()

        # Actualizar estado
        self.state = 'processed'

        # Mensaje de confirmación
        self.message_post(
            body=_('Procesamiento completado. Se crearon %d pagos.') % len(created_payments)
        )

        return {
            'name': _('Pagos Creados'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created_payments)],
            'target': 'current',
        }

    def _create_payment_for_partner(self, partner, lines):
        """Crear pago individual para un propietario"""
        total_amount = sum(line.net_to_pay for line in lines)

        if total_amount <= 0:
            return None

        payment_vals = {
            'bohio_mass_payment_id': self.id,
            'partner_id': partner.id,
            'amount': abs(total_amount),
            'currency_id': self.currency_id.id,
            'payment_type': 'outbound' if total_amount > 0 else 'inbound',
            'partner_type': 'supplier' if total_amount > 0 else 'customer',
            'journal_id': self.journal_id.id,
            'date': self.date,
            'ref': f'{self.name} - {partner.name} - Mes {self.simulation_month.strftime("%m/%Y")}',
        }

        payment = self.env['account.payment'].create(payment_vals)

        # Crear líneas de detalle usando custom_account_treasury
        self._create_payment_detail_lines(payment, lines)

        return payment.id

    def _create_payment_detail_lines(self, payment, lines):
        """Crear líneas de detalle del pago"""
        for line in lines:
            # Línea del canon (cuenta 28 - pasivo)
            if line.canon_amount != 0:
                self.env['account.payment.detail'].create({
                    'payment_id': payment.id,
                    'name': f'Canon - {line.contract_id.name}',
                    'payment_amount': line.canon_amount,
                    'partner_id': line.partner_id.id,
                    'account_id': self._get_owner_payable_account(line.partner_id).id,
                })

            # Línea de comisión (rebaja del pasivo)
            if line.commission_amount != 0:
                self.env['account.payment.detail'].create({
                    'payment_id': payment.id,
                    'name': f'Comisión - {line.contract_id.name}',
                    'payment_amount': -line.commission_amount,  # Negativo porque es rebaja
                    'partner_id': line.partner_id.id,
                    'account_id': self._get_owner_payable_account(line.partner_id).id,
                })

            # Línea de impuestos (rebaja del pasivo)
            if line.tax_amount != 0:
                self.env['account.payment.detail'].create({
                    'payment_id': payment.id,
                    'name': f'IVA Comisión - {line.contract_id.name}',
                    'payment_amount': -line.tax_amount,  # Negativo porque es rebaja
                    'partner_id': line.partner_id.id,
                    'account_id': self._get_owner_payable_account(line.partner_id).id,
                })

            # Líneas de novedades
            if line.novelty_amount != 0:
                self.env['account.payment.detail'].create({
                    'payment_id': payment.id,
                    'name': f'Novedades - {line.contract_id.name}',
                    'payment_amount': -line.novelty_amount,  # Negativo porque es descuento
                    'partner_id': line.partner_id.id,
                    'account_id': self._get_owner_payable_account(line.partner_id).id,
                })

            # Líneas de préstamos
            if line.loan_amount != 0:
                self.env['account.payment.detail'].create({
                    'payment_id': payment.id,
                    'name': f'Préstamos - {line.contract_id.name}',
                    'payment_amount': -line.loan_amount,  # Negativo porque es descuento
                    'partner_id': line.partner_id.id,
                    'account_id': self._get_loans_account().id,
                })

            # Líneas de intereses
            if line.interest_amount != 0:
                self.env['account.payment.detail'].create({
                    'payment_id': payment.id,
                    'name': f'Intereses por Mora - {line.contract_id.name}',
                    'payment_amount': line.interest_amount,  # Positivo porque es cargo adicional
                    'partner_id': line.partner_id.id,
                    'account_id': self._get_interest_income_account().id,
                })

    def _get_owner_payable_account(self, partner):
        """Obtener cuenta por pagar del propietario (cuenta 28)"""
        # Buscar cuenta específica para propietarios o usar la del partner
        account = self.env['account.account'].search([
            ('code', 'like', '28%'),
            ('account_type', '=', 'liability_payable'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        if not account:
            account = partner.property_account_payable_id

        return account

    def _get_loans_account(self):
        """Obtener cuenta de préstamos (cuenta 13)"""
        account = self.env['account.account'].search([
            ('code', 'like', '13%'),
            ('account_type', 'in', ['asset_receivable', 'asset_current']),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        if not account:
            raise UserError(_('No se encontró cuenta para préstamos (13xxx)'))

        return account

    def _get_interest_income_account(self):
        """Obtener cuenta de ingresos por intereses"""
        account = self.env['account.account'].search([
            ('code', 'like', '42%'),
            ('account_type', '=', 'income'),
            ('name', 'ilike', 'interes'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        if not account:
            # Usar cuenta de otros ingresos
            account = self.env['account.account'].search([
                ('code', 'like', '42%'),
                ('account_type', '=', 'income'),
                ('company_id', '=', self.company_id.id)
            ], limit=1)

        if not account:
            raise UserError(_('No se encontró cuenta de ingresos por intereses'))

        return account

    def action_cancel(self):
        """Cancelar el proceso"""
        self.ensure_one()
        if self.state == 'processed':
            raise UserError(_('No se puede cancelar un proceso ya ejecutado'))

        self.state = 'cancelled'

    def action_reset_to_draft(self):
        """Volver a borrador"""
        self.ensure_one()
        self.state = 'draft'
        self.simulation_line_ids.unlink()

    def action_postpone_month(self):
        """Aplazar al mes siguiente"""
        self.ensure_one()
        new_month = self.simulation_month + relativedelta(months=1)

        # Actualizar líneas que no hayan sido procesadas
        for line in self.simulation_line_ids.filtered('skip_payment'):
            line.notes = (line.notes or '') + f' | Aplazado de {self.simulation_month.strftime("%m/%Y")} a {new_month.strftime("%m/%Y")}'

        self.simulation_month = new_month
        self.state = 'draft'

    def action_create_payment_from_selection(self):
        """Crear pago solo para líneas seleccionadas"""
        self.ensure_one()

        selected_lines = self.simulation_line_ids.filtered(lambda l: l.selected and not l.skip_payment)
        if not selected_lines:
            raise UserError(_('Debe seleccionar al menos una línea para procesar'))

        created_payments = []

        if self.separate_payments:
            # Agrupar por propietario
            grouped_lines = {}
            for line in selected_lines:
                if line.partner_id not in grouped_lines:
                    grouped_lines[line.partner_id] = []
                grouped_lines[line.partner_id].append(line)

            for partner, lines in grouped_lines.items():
                payment = self._create_payment_for_partner(partner, lines)
                if payment:
                    created_payments.append(payment)
        else:
            # Un solo pago consolidado
            payment = self._create_consolidated_payment(selected_lines)
            if payment:
                created_payments.append(payment)

        # Marcar líneas como procesadas
        selected_lines.write({'processed': True})

        return {
            'name': _('Pagos Creados desde Selección'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created_payments)],
            'target': 'current',
        }

    def action_show_tax_income_balance(self):
        """Mostrar balance de impuestos e ingresos"""
        self.ensure_one()

        return {
            'name': _('Balance de Impuestos e Ingresos'),
            'type': 'ir.actions.act_window',
            'res_model': 'bohio.tax.income.balance.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_mass_payment_id': self.id,
                'default_period_month': self.simulation_month,
            }
        }

    def action_create_debit_note(self):
        """Crear nueva nota débito"""
        self.ensure_one()

        return {
            'name': _('Crear Nota Débito'),
            'type': 'ir.actions.act_window',
            'res_model': 'bohio.debit.note.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_mass_payment_id': self.id,
                'default_period_month': self.simulation_month,
                'default_contracts_domain': self._get_contracts_domain(),
            }
        }

    def _get_contracts_domain(self):
        """Obtener dominio de contratos para filtrar"""
        domain = [('state', '=', 'confirmed')]

        if self.region_ids:
            domain.append(('region_id', 'in', self.region_ids.ids))
        if self.project_ids:
            domain.append(('project_id', 'in', self.project_ids.ids))
        if self.contract_ids:
            domain.append(('id', 'in', self.contract_ids.ids))

        return domain


class BohioMassPaymentLine(models.Model):
    _name = 'bohio.mass.payment.line'
    _description = 'Línea de Simulación de Pago Masivo'
    _order = 'partner_id, contract_id'

    mass_payment_id = fields.Many2one('bohio.mass.payment', required=True, ondelete='cascade')
    contract_id = fields.Many2one('property.contract', 'Contrato', required=True)
    partner_id = fields.Many2one('res.partner', 'Propietario', required=True)
    partner_percentage = fields.Float('% Participación', digits=(5, 2))

    # MONTOS DETALLADOS
    canon_amount = fields.Monetary('Canon', currency_field='currency_id')
    commission_amount = fields.Monetary('Comisión', currency_field='currency_id')
    tax_amount = fields.Monetary('Impuestos', currency_field='currency_id')
    novelty_amount = fields.Monetary('Novedades', currency_field='currency_id')
    loan_amount = fields.Monetary('Préstamos', currency_field='currency_id')
    interest_amount = fields.Monetary('Intereses', currency_field='currency_id')
    net_to_pay = fields.Monetary('Neto a Pagar', currency_field='currency_id')

    # CONTROL
    skip_payment = fields.Boolean('Omitir Pago', default=False,
                                 help='Marcar para omitir esta línea en el pago')
    selected = fields.Boolean('Seleccionar', default=False,
                             help='Seleccionar para procesamiento individual')
    processed = fields.Boolean('Procesado', default=False, readonly=True,
                              help='Indica si ya se procesó esta línea')
    notes = fields.Text('Observaciones')

    # BALANCE DE PAGOS PARCIALES
    paid_canon = fields.Monetary('Canon Pagado', currency_field='currency_id', default=0.0,
                                help='Monto de canon ya pagado por el inquilino')
    paid_percentage = fields.Float('% Pagado', compute='_compute_paid_percentage', store=True,
                                  help='Porcentaje del canon pagado')

    currency_id = fields.Many2one('res.currency', related='mass_payment_id.currency_id')

    # CAMPOS RELACIONADOS PARA FILTROS
    region_id = fields.Many2one('region.region', related='contract_id.region_id', store=True)
    project_id = fields.Many2one('project.worksite', related='contract_id.project_id', store=True)
    city = fields.Char('Ciudad', related='contract_id.property_id.city', store=True)

    @api.depends('partner_id', 'contract_id', 'net_to_pay')
    def name_get(self):
        result = []
        for line in self:
            name = f'{line.partner_id.name} - {line.contract_id.property_id.name} ({line.currency_id.symbol}{line.net_to_pay:,.2f})'
            result.append((line.id, name))
        return result

    @api.depends('canon_amount', 'paid_canon')
    def _compute_paid_percentage(self):
        for line in self:
            if line.canon_amount > 0:
                line.paid_percentage = (line.paid_canon / line.canon_amount) * 100
            else:
                line.paid_percentage = 0.0

    def action_update_paid_canon(self):
        """Actualizar canon pagado desde facturas reales"""
        self.ensure_one()

        # Buscar facturas del contrato para el período
        month_start = self.mass_payment_id.simulation_month.replace(day=1)
        month_end = month_start + relativedelta(months=1, days=-1)

        contract_invoices = self.env['account.move'].search([
            ('partner_id', '=', self.contract_id.partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', month_start),
            ('invoice_date', '<=', month_end),
            ('line_ids.product_id.product_tmpl_id', '=', self.contract_id.property_id.id)
        ])

        total_paid = sum(
            invoice.amount_total - invoice.amount_residual
            for invoice in contract_invoices
        )

        # Distribuir según porcentaje del propietario
        owner_paid = total_paid * (self.partner_percentage / 100)
        self.paid_canon = owner_paid

    def action_mark_tax_reconciled(self):
        """Marcar impuestos como conciliados/no conciliables"""
        self.ensure_one()
        return {
            'name': _('Marcar Estado de Conciliación'),
            'type': 'ir.actions.act_window',
            'res_model': 'bohio.tax.reconcile.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_line_id': self.id,
                'default_tax_amount': self.tax_amount,
            }
        }


class BohioDebitNote(models.Model):
    _name = 'bohio.debit.note'
    _description = 'Nota Débito'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char('Número', default='/', readonly=True, copy=False)
    mass_payment_id = fields.Many2one('bohio.mass.payment', 'Pago Masivo', required=True, ondelete='cascade')

    # INFORMACIÓN BÁSICA
    date = fields.Date('Fecha', default=fields.Date.today, required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', 'Cliente', required=True)
    contract_id = fields.Many2one('property.contract', 'Contrato', required=True)

    # CONFIGURACIÓN
    concept = fields.Char('Concepto', required=True, default='Interés por Mora')
    description = fields.Text('Descripción Detallada')

    # MONTOS
    base_amount = fields.Monetary('Monto Base', currency_field='currency_id', required=True)
    rate = fields.Float('Tasa (%)', default=0.0, help='Tasa de interés o porcentaje a aplicar')
    amount = fields.Monetary('Monto Total', currency_field='currency_id', compute='_compute_amount', store=True, readonly=False)

    # IMPUESTOS
    tax_ids = fields.Many2many('account.tax', string='Impuestos')
    tax_amount = fields.Monetary('Impuestos', currency_field='currency_id', compute='_compute_tax_amount', store=True)
    amount_total = fields.Monetary('Total con Impuestos', currency_field='currency_id', compute='_compute_amount_total', store=True)

    # CONTROL
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmada'),
        ('invoiced', 'Facturada'),
        ('cancelled', 'Cancelada')
    ], string='Estado', default='draft', tracking=True)

    # FACTURACIÓN
    invoice_id = fields.Many2one('account.move', 'Factura Generada', readonly=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('bohio.debit.note') or '/'
        return super().create(vals)

    @api.depends('base_amount', 'rate')
    def _compute_amount(self):
        for record in self:
            if record.rate > 0:
                record.amount = record.base_amount * (record.rate / 100)
            else:
                record.amount = record.base_amount

    @api.depends('amount', 'tax_ids')
    def _compute_tax_amount(self):
        for record in self:
            if record.tax_ids and record.amount:
                tax_result = record.tax_ids.compute_all(
                    record.amount,
                    currency=record.currency_id,
                    quantity=1.0,
                    partner=record.partner_id
                )
                record.tax_amount = sum(tax['amount'] for tax in tax_result['taxes'])
            else:
                record.tax_amount = 0.0

    @api.depends('amount', 'tax_amount')
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = record.amount + record.tax_amount

    def action_confirm(self):
        """Confirmar la nota débito"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Solo se pueden confirmar notas débito en borrador'))

        self.state = 'confirmed'

        # Añadir línea a la simulación de pago masivo
        self._add_to_mass_payment_simulation()

    def _add_to_mass_payment_simulation(self):
        """Agregar esta nota débito a la simulación de pago masivo"""
        # Buscar línea existente del mismo contrato/partner
        existing_line = self.mass_payment_id.simulation_line_ids.filtered(
            lambda l: l.contract_id == self.contract_id and l.partner_id == self.partner_id
        )

        if existing_line:
            # Actualizar línea existente
            existing_line.novelty_amount += self.amount_total
            existing_line.net_to_pay = (
                existing_line.canon_amount -
                existing_line.commission_amount -
                existing_line.tax_amount -
                existing_line.novelty_amount -
                existing_line.loan_amount +
                existing_line.interest_amount
            )
            existing_line.notes = (existing_line.notes or '') + f'\n+ Nota Débito {self.name}: {self.amount_total}'
        else:
            # Crear nueva línea
            self.env['bohio.mass.payment.line'].create({
                'mass_payment_id': self.mass_payment_id.id,
                'contract_id': self.contract_id.id,
                'partner_id': self.partner_id.id,
                'partner_percentage': 100.0,  # Por defecto, ajustar según necesidad
                'canon_amount': 0.0,
                'commission_amount': 0.0,
                'tax_amount': 0.0,
                'novelty_amount': self.amount_total,
                'loan_amount': 0.0,
                'interest_amount': 0.0,
                'net_to_pay': -self.amount_total,  # Negativo porque es un cargo
                'notes': f'Nota Débito {self.name}: {self.concept}',
            })

    def action_create_invoice(self):
        """Crear factura de la nota débito"""
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_('Solo se pueden facturar notas débito confirmadas'))

        if self.invoice_id:
            raise UserError(_('Ya existe una factura para esta nota débito'))

        # Crear factura
        journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
        if not journal:
            raise UserError(_('No se encontró diario de ventas'))

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'journal_id': journal.id,
            'invoice_date': self.date,
            'ref': f'Nota Débito {self.name} - {self.concept}',
            'bohio_debit_note_id': self.id,
            'invoice_line_ids': [(0, 0, {
                'name': f'{self.concept} - {self.description or ""}',
                'quantity': 1,
                'price_unit': self.amount,
                'tax_ids': [(6, 0, self.tax_ids.ids)],
                'account_id': self._get_debit_note_account().id,
            })]
        }

        invoice = self.env['account.move'].create(invoice_vals)
        self.write({
            'invoice_id': invoice.id,
            'state': 'invoiced'
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _get_debit_note_account(self):
        """Obtener cuenta contable para nota débito"""
        # Buscar cuenta de otros ingresos
        account = self.env['account.account'].search([
            ('code', 'like', '42%'),
            ('account_type', '=', 'income'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        if not account:
            raise UserError(_('No se encontró cuenta contable para notas débito'))

        return account

    def action_cancel(self):
        """Cancelar nota débito"""
        self.ensure_one()
        if self.invoice_id and self.invoice_id.state == 'posted':
            raise UserError(_('No se puede cancelar una nota débito con factura contabilizada'))

        self.state = 'cancelled'


class BohioDebitNoteWizard(models.TransientModel):
    _name = 'bohio.debit.note.wizard'
    _description = 'Wizard para Crear Nota Débito'

    mass_payment_id = fields.Many2one('bohio.mass.payment', 'Pago Masivo', required=True)
    period_month = fields.Date('Mes del Período', required=True)

    # FILTROS
    contract_ids = fields.Many2many('property.contract', string='Contratos')
    partner_ids = fields.Many2many('res.partner', string='Clientes')

    # CONFIGURACIÓN DE LA NOTA
    concept = fields.Char('Concepto', required=True, default='Interés por Mora')
    description = fields.Text('Descripción')
    calculation_method = fields.Selection([
        ('fixed_amount', 'Monto Fijo'),
        ('percentage', 'Porcentaje del Canon'),
        ('interest_rate', 'Tasa de Interés')
    ], string='Método de Cálculo', default='interest_rate', required=True)

    # VALORES
    fixed_amount = fields.Float('Monto Fijo', digits='Product Price')
    percentage = fields.Float('Porcentaje (%)', default=0.0)
    interest_rate = fields.Float('Tasa de Interés (%)', default=1.5)
    days_base = fields.Integer('Días Base', default=30, help='Días para el cálculo de interés')

    # IMPUESTOS
    apply_taxes = fields.Boolean('Aplicar Impuestos', default=False)
    tax_ids = fields.Many2many('account.tax', string='Impuestos')

    def action_create_debit_notes(self):
        """Crear múltiples notas débito"""
        self.ensure_one()

        contracts = self.contract_ids or self._get_default_contracts()
        created_notes = []

        for contract in contracts:
            # Calcular monto según método
            base_amount = self._calculate_base_amount(contract)
            if base_amount <= 0:
                continue

            # Crear nota débito por cada propietario
            if contract.is_multi_propietario and contract.property_id.owners_lines:
                for owner_line in contract.property_id.owners_lines:
                    owner_amount = base_amount * (owner_line.percentage / 100)
                    note_vals = self._prepare_debit_note_vals(contract, owner_line.partner_id, owner_amount)
                    note = self.env['bohio.debit.note'].create(note_vals)
                    created_notes.append(note.id)
            else:
                # Un solo propietario
                note_vals = self._prepare_debit_note_vals(contract, contract.partner_id, base_amount)
                note = self.env['bohio.debit.note'].create(note_vals)
                created_notes.append(note.id)

        if not created_notes:
            raise UserError(_('No se crearon notas débito. Verifique los filtros y configuración.'))

        # Mostrar notas créadas
        return {
            'name': _('Notas Débito Creadas'),
            'type': 'ir.actions.act_window',
            'res_model': 'bohio.debit.note',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created_notes)],
            'target': 'current',
        }

    def _get_default_contracts(self):
        """Obtener contratos por defecto según filtros del mass payment"""
        domain = [('state', '=', 'confirmed')]

        # Aplicar filtros del mass payment
        if self.mass_payment_id.region_ids:
            domain.append(('region_id', 'in', self.mass_payment_id.region_ids.ids))
        if self.mass_payment_id.project_ids:
            domain.append(('project_id', 'in', self.mass_payment_id.project_ids.ids))

        return self.env['property.contract'].search(domain)

    def _calculate_base_amount(self, contract):
        """Calcular monto base según método seleccionado"""
        if self.calculation_method == 'fixed_amount':
            return self.fixed_amount

        elif self.calculation_method == 'percentage':
            # Porcentaje del canon del mes
            month_start = self.period_month.replace(day=1)
            month_end = month_start + relativedelta(months=1, days=-1)

            month_lines = contract.loan_line_ids.filtered(
                lambda l: month_start <= l.date <= month_end
            )
            canon_total = sum(month_lines.mapped('amount'))
            return canon_total * (self.percentage / 100)

        elif self.calculation_method == 'interest_rate':
            # Tasa de interés sobre cuotas vencidas
            overdue_lines = contract.loan_line_ids.filtered(
                lambda l: l.is_overdue and l.payment_state != 'paid'
            )
            total_overdue = sum(overdue_lines.mapped('amount'))
            return total_overdue * (self.interest_rate / 100) * (self.days_base / 30)

        return 0.0

    def _prepare_debit_note_vals(self, contract, partner, amount):
        """Preparar valores para crear nota débito"""
        return {
            'mass_payment_id': self.mass_payment_id.id,
            'partner_id': partner.id,
            'contract_id': contract.id,
            'concept': self.concept,
            'description': self.description,
            'base_amount': amount,
            'amount': amount,
            'tax_ids': [(6, 0, self.tax_ids.ids)] if self.apply_taxes else [],
            'date': self.period_month,
        }


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    bohio_mass_payment_id = fields.Many2one('bohio.mass.payment', string='Pago Masivo Origen')


class BohioTaxIncomeBalanceWizard(models.TransientModel):
    _name = 'bohio.tax.income.balance.wizard'
    _description = 'Wizard Balance de Impuestos e Ingresos'

    mass_payment_id = fields.Many2one('bohio.mass.payment', 'Pago Masivo', required=True)
    period_month = fields.Date('Mes del Período', required=True)

    # FILTROS
    only_partial_payments = fields.Boolean('Solo Pagos Parciales', default=False,
                                          help='Mostrar solo contratos con pagos parciales')
    filter_by_reconciliation = fields.Selection([
        ('all', 'Todos'),
        ('reconciled', 'Solo Conciliados'),
        ('not_reconciled', 'Solo No Conciliados'),
        ('problematic', 'Solo Problemáticos')
    ], string='Filtrar por Conciliación', default='all')

    # TOTALES CALCULADOS
    total_expected_canon = fields.Monetary('Canon Esperado Total', compute='_compute_balance_totals',
                                          currency_field='currency_id')
    total_received_canon = fields.Monetary('Canon Recibido Total', compute='_compute_balance_totals',
                                          currency_field='currency_id')
    total_expected_commission = fields.Monetary('Comisión Esperada Total', compute='_compute_balance_totals',
                                               currency_field='currency_id')
    total_expected_taxes = fields.Monetary('Impuestos Esperados Total', compute='_compute_balance_totals',
                                          currency_field='currency_id')
    total_to_owners = fields.Monetary('Total a Propietarios', compute='_compute_balance_totals',
                                     currency_field='currency_id')

    # LÍNEAS DE DETALLE
    balance_line_ids = fields.One2many('bohio.tax.income.balance.line', 'wizard_id', 'Líneas de Balance')
    currency_id = fields.Many2one('res.currency', related='mass_payment_id.currency_id')

    @api.depends('balance_line_ids.canon_expected', 'balance_line_ids.canon_received',
                 'balance_line_ids.commission_amount', 'balance_line_ids.tax_amount')
    def _compute_balance_totals(self):
        for wizard in self:
            lines = wizard.balance_line_ids
            wizard.total_expected_canon = sum(lines.mapped('canon_expected'))
            wizard.total_received_canon = sum(lines.mapped('canon_received'))
            wizard.total_expected_commission = sum(lines.mapped('commission_amount'))
            wizard.total_expected_taxes = sum(lines.mapped('tax_amount'))
            wizard.total_to_owners = sum(lines.mapped('net_to_owner'))

    def action_load_balance_data(self):
        """Cargar datos de balance"""
        self.ensure_one()
        self.balance_line_ids.unlink()

        # Obtener líneas de simulación
        simulation_lines = self.mass_payment_id.simulation_line_ids

        if self.only_partial_payments:
            simulation_lines = simulation_lines.filtered(lambda l: l.paid_percentage < 100)

        balance_lines = []
        for sim_line in simulation_lines:
            # Calcular datos reales desde facturas
            real_data = self._get_real_invoice_data(sim_line)

            balance_lines.append((0, 0, {
                'wizard_id': self.id,
                'simulation_line_id': sim_line.id,
                'contract_id': sim_line.contract_id.id,
                'partner_id': sim_line.partner_id.id,
                'canon_expected': sim_line.canon_amount,
                'canon_received': real_data['canon_received'],
                'commission_amount': sim_line.commission_amount,
                'tax_amount': sim_line.tax_amount,
                'net_to_owner': sim_line.net_to_pay,
                'is_reconciled': real_data['is_reconciled'],
                'has_issues': real_data['has_issues'],
                'issue_description': real_data['issue_description'],
            }))

        self.balance_line_ids = balance_lines

    def _get_real_invoice_data(self, simulation_line):
        """Obtener datos reales de facturas para una línea de simulación"""
        month_start = self.period_month.replace(day=1)
        month_end = month_start + relativedelta(months=1, days=-1)

        # Buscar facturas del inquilino (canon)
        tenant_invoices = self.env['account.move'].search([
            ('partner_id', '=', simulation_line.contract_id.partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', month_start),
            ('invoice_date', '<=', month_end),
        ])

        # Buscar facturas del propietario (comisión)
        owner_invoices = self.env['account.move'].search([
            ('partner_id', '=', simulation_line.partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', month_start),
            ('invoice_date', '<=', month_end),
        ])

        canon_received = sum(
            (invoice.amount_total - invoice.amount_residual) * (simulation_line.partner_percentage / 100)
            for invoice in tenant_invoices
        )

        # Verificar conciliación
        is_reconciled = True
        has_issues = False
        issue_description = ""

        if canon_received < simulation_line.canon_amount * 0.95:  # Tolerancia del 5%
            has_issues = True
            issue_description += f"Canon incompleto: recibido {canon_received} de {simulation_line.canon_amount}. "

        if not owner_invoices:
            has_issues = True
            issue_description += "No se encontró factura de comisión. "
            is_reconciled = False

        return {
            'canon_received': canon_received,
            'is_reconciled': is_reconciled,
            'has_issues': has_issues,
            'issue_description': issue_description.strip(),
        }

    def action_reconcile_selected(self):
        """Conciliar líneas seleccionadas"""
        selected_lines = self.balance_line_ids.filtered('selected')
        if not selected_lines:
            raise UserError(_('Debe seleccionar al menos una línea'))

        reconciled_count = 0
        for line in selected_lines:
            if line.action_auto_reconcile():
                reconciled_count += 1

        self.env.user.notify_info(
            message=_('Se conciliaron %d de %d líneas seleccionadas') % (reconciled_count, len(selected_lines))
        )

        # Recargar datos
        self.action_load_balance_data()


class BohioTaxIncomeBalanceLine(models.TransientModel):
    _name = 'bohio.tax.income.balance.line'
    _description = 'Línea de Balance de Impuestos e Ingresos'

    wizard_id = fields.Many2one('bohio.tax.income.balance.wizard', required=True, ondelete='cascade')
    simulation_line_id = fields.Many2one('bohio.mass.payment.line', 'Línea de Simulación')
    contract_id = fields.Many2one('property.contract', 'Contrato', required=True)
    partner_id = fields.Many2one('res.partner', 'Propietario', required=True)

    # MONTOS
    canon_expected = fields.Monetary('Canon Esperado', currency_field='currency_id')
    canon_received = fields.Monetary('Canon Recibido', currency_field='currency_id')
    commission_amount = fields.Monetary('Comisión', currency_field='currency_id')
    tax_amount = fields.Monetary('Impuestos', currency_field='currency_id')
    net_to_owner = fields.Monetary('Neto a Propietario', currency_field='currency_id')

    # ESTADO
    is_reconciled = fields.Boolean('Conciliado', default=False)
    has_issues = fields.Boolean('Tiene Problemas', default=False)
    issue_description = fields.Text('Descripción de Problemas')
    selected = fields.Boolean('Seleccionar', default=False)

    # DIFERENCIAS
    canon_difference = fields.Monetary('Diferencia Canon', compute='_compute_differences',
                                      currency_field='currency_id')
    difference_percentage = fields.Float('% Diferencia', compute='_compute_differences')

    currency_id = fields.Many2one('res.currency', related='wizard_id.currency_id')

    @api.depends('canon_expected', 'canon_received')
    def _compute_differences(self):
        for line in self:
            line.canon_difference = line.canon_received - line.canon_expected
            if line.canon_expected > 0:
                line.difference_percentage = (line.canon_difference / line.canon_expected) * 100
            else:
                line.difference_percentage = 0.0

    def action_auto_reconcile(self):
        """Intentar conciliar automáticamente"""
        self.ensure_one()
        # Implementar lógica de conciliación automática
        # Por ahora, marcar como conciliado si no hay problemas grandes
        if abs(self.difference_percentage) < 5:  # Tolerancia del 5%
            self.write({
                'is_reconciled': True,
                'has_issues': False,
            })
            return True
        return False


class BohioTaxReconcileWizard(models.TransientModel):
    _name = 'bohio.tax.reconcile.wizard'
    _description = 'Wizard para Conciliación de Impuestos'

    line_id = fields.Many2one('bohio.mass.payment.line', 'Línea', required=True)
    tax_amount = fields.Monetary('Monto de Impuestos', currency_field='currency_id', required=True)

    # OPCIONES DE CONCILIACIÓN
    reconcile_option = fields.Selection([
        ('auto', 'Conciliación Automática'),
        ('manual', 'Ajuste Manual'),
        ('skip', 'Saltar (No Conciliable)')
    ], string='Opción', default='auto', required=True)

    manual_adjustment = fields.Monetary('Ajuste Manual', currency_field='currency_id', default=0.0)
    reason = fields.Text('Motivo del Ajuste')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    def action_apply_reconciliation(self):
        """Aplicar la conciliación seleccionada"""
        self.ensure_one()

        if self.reconcile_option == 'auto':
            # Intentar conciliación automática
            self.line_id.write({
                'notes': (self.line_id.notes or '') + '\nConciliación automática aplicada.'
            })

        elif self.reconcile_option == 'manual':
            # Aplicar ajuste manual
            adjusted_tax = self.tax_amount + self.manual_adjustment
            self.line_id.write({
                'tax_amount': adjusted_tax,
                'notes': (self.line_id.notes or '') + f'\nAjuste manual: {self.manual_adjustment}. Motivo: {self.reason}'
            })

        elif self.reconcile_option == 'skip':
            # Marcar como no conciliable
            self.line_id.write({
                'skip_payment': True,
                'notes': (self.line_id.notes or '') + f'\nMarcado como no conciliable. Motivo: {self.reason}'
            })

        return {'type': 'ir.actions.act_window_close'}


class AccountMove(models.Model):
    _inherit = 'account.move'

    bohio_debit_note_id = fields.Many2one('bohio.debit.note', string='Nota Débito Origen')
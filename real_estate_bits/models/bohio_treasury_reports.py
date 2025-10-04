# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BohioCommissionReport(models.Model):
    """Reporte de Comisiones - Genera provisiones de gasto por comisiones"""
    _name = 'bohio.commission.report'
    _description = 'Reporte de Comisiones'
    _auto = False
    _order = 'date desc'

    # IDENTIFICACIÓN
    date = fields.Date('Fecha', readonly=True)
    period_month = fields.Char('Mes', readonly=True)
    user_id = fields.Many2one('res.users', 'Vendedor', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Vendedor (Partner)', readonly=True)

    # PROYECTO
    project_id = fields.Many2one('project.worksite', 'Proyecto', readonly=True)
    region_id = fields.Many2one('region.region', 'Región', readonly=True)

    # CONTRATO
    contract_id = fields.Many2one('property.contract', 'Contrato', readonly=True)
    property_id = fields.Many2one('product.template', 'Propiedad', readonly=True)

    # MONTOS
    sale_amount = fields.Monetary('Monto Venta', readonly=True, currency_field='currency_id')
    commission_rate = fields.Float('% Comisión', readonly=True)
    commission_amount = fields.Monetary('Comisión', readonly=True, currency_field='currency_id')

    # PROVISIÓN (Gasto de la empresa)
    provision_amount = fields.Monetary('Provisión Gasto', readonly=True, currency_field='currency_id',
                                      help='Monto a provisionar como gasto de la empresa')

    # ESTADO
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('invoiced', 'Facturado'),
        ('paid', 'Pagado')
    ], string='Estado', readonly=True)

    invoice_id = fields.Many2one('account.move', 'Factura Comisión', readonly=True)
    payment_state = fields.Selection([
        ('not_paid', 'Sin Pagar'),
        ('partial', 'Pago Parcial'),
        ('paid', 'Pagado')
    ], string='Estado Pago', readonly=True)

    currency_id = fields.Many2one('res.currency', 'Moneda', readonly=True)
    company_id = fields.Many2one('res.company', 'Compañía', readonly=True)

    def init(self):
        """Vista SQL para reporte de comisiones"""
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW bohio_commission_report AS (
                SELECT
                    row_number() OVER () AS id,
                    pc.date_from AS date,
                    TO_CHAR(pc.date_from, 'YYYY-MM') AS period_month,
                    pc.user_id,
                    pc.partner_id,
                    pc.project_id,
                    pc.region_id,
                    pc.id AS contract_id,
                    pc.property_id,
                    COALESCE(pc.amount_total, 0) AS sale_amount,
                    0.0 AS commission_rate,
                    COALESCE(pc.total_commission, 0) AS commission_amount,
                    COALESCE(pc.total_commission, 0) AS provision_amount,
                    pc.state,
                    NULL::integer AS invoice_id,
                    'not_paid' AS payment_state,
                    pc.currency_id,
                    pc.company_id
                FROM property_contract pc
                WHERE COALESCE(pc.total_commission, 0) > 0
                    AND pc.state IN ('confirmed', 'renew')
            )
        """)

    @api.model
    def action_create_provision(self):
        """Crear asiento de provisión de comisiones"""
        self.ensure_one()

        if not self.provision_amount:
            raise UserError(_('No hay monto de provisión para este registro'))

        # Buscar cuentas contables
        expense_account = self.env['account.account'].search([
            ('code', 'like', '51%'),  # Gastos de ventas
            ('account_type', '=', 'expense'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        if not expense_account:
            raise UserError(_('No se encontró cuenta de gastos de ventas'))

        provision_account = self.env['account.account'].search([
            ('code', 'like', '25%'),  # Provisiones
            ('account_type', '=', 'liability_current'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        if not provision_account:
            raise UserError(_('No se encontró cuenta de provisiones'))

        # Crear asiento contable
        journal = self.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        if not journal:
            raise UserError(_('No se encontró diario contable'))

        move_vals = {
            'journal_id': journal.id,
            'date': fields.Date.today(),
            'ref': f'Provisión Comisión - {self.contract_id.name}',
            'line_ids': [
                (0, 0, {
                    'name': f'Gasto por comisión - {self.partner_id.name}',
                    'account_id': expense_account.id,
                    'debit': self.provision_amount,
                    'credit': 0.0,
                    'partner_id': self.partner_id.id,
                }),
                (0, 0, {
                    'name': f'Provisión comisión por pagar - {self.partner_id.name}',
                    'account_id': provision_account.id,
                    'debit': 0.0,
                    'credit': self.provision_amount,
                    'partner_id': self.partner_id.id,
                })
            ]
        }

        move = self.env['account.move'].create(move_vals)
        move.action_post()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Asiento de Provisión'),
            'res_model': 'account.move',
            'res_id': move.id,
            'view_mode': 'form',
            'target': 'current',
        }


class BohioCollectionReport(models.Model):
    """Reporte de Recaudo vs Esperado"""
    _name = 'bohio.collection.report'
    _description = 'Reporte de Recaudo'
    _auto = False
    _order = 'period_month desc, project_id'

    # PERIODO
    period_month = fields.Date('Mes', readonly=True)
    period_year = fields.Char('Año', readonly=True)

    # PROYECTO
    project_id = fields.Many2one('project.worksite', 'Proyecto', readonly=True)
    region_id = fields.Many2one('region.region', 'Región', readonly=True)

    # MONTOS ESPERADOS
    expected_amount = fields.Monetary('Recaudo Esperado', readonly=True, currency_field='currency_id',
                                     help='Suma de cuotas vencidas en el periodo')

    # MONTOS REALES
    collected_amount = fields.Monetary('Recaudo Real', readonly=True, currency_field='currency_id',
                                      help='Pagos recibidos en el periodo')

    # ANÁLISIS
    difference = fields.Monetary('Diferencia', readonly=True, currency_field='currency_id',
                                compute='_compute_difference', store=True)
    collection_rate = fields.Float('% Recaudo', readonly=True, compute='_compute_collection_rate', store=True)

    currency_id = fields.Many2one('res.currency', 'Moneda', readonly=True)
    company_id = fields.Many2one('res.company', 'Compañía', readonly=True)

    @api.depends('expected_amount', 'collected_amount')
    def _compute_difference(self):
        for record in self:
            record.difference = record.collected_amount - record.expected_amount

    @api.depends('expected_amount', 'collected_amount')
    def _compute_collection_rate(self):
        for record in self:
            if record.expected_amount:
                record.collection_rate = (record.collected_amount / record.expected_amount) * 100
            else:
                record.collection_rate = 0.0

    def init(self):
        """Vista SQL para reporte de recaudo"""
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW bohio_collection_report AS (
                SELECT
                    row_number() OVER () AS id,
                    DATE_TRUNC('month', pll.date)::date AS period_month,
                    TO_CHAR(pll.date, 'YYYY') AS period_year,
                    pc.project_id,
                    pc.region_id,
                    SUM(pll.amount) AS expected_amount,
                    SUM(CASE WHEN pll.payment_state IN ('paid', 'partial')
                        THEN pll.amount ELSE 0 END) AS collected_amount,
                    pc.currency_id,
                    pc.company_id
                FROM property_loan_line pll
                JOIN property_contract pc ON pll.contract_id = pc.id
                WHERE pll.date <= CURRENT_DATE
                GROUP BY
                    DATE_TRUNC('month', pll.date),
                    TO_CHAR(pll.date, 'YYYY'),
                    pc.project_id,
                    pc.region_id,
                    pc.currency_id,
                    pc.company_id
            )
        """)


class BohioTaxBalanceReport(models.Model):
    """Reporte de Balance de Impuestos"""
    _name = 'bohio.tax.balance.report'
    _description = 'Balance de Impuestos'
    _auto = False
    _order = 'period_month desc, tax_id'

    # PERIODO
    period_month = fields.Date('Mes', readonly=True)
    period_year = fields.Char('Año', readonly=True)

    # IMPUESTO
    tax_id = fields.Many2one('account.tax', 'Impuesto', readonly=True)
    tax_type = fields.Selection([
        ('sale', 'Venta'),
        ('purchase', 'Compra')
    ], string='Tipo', readonly=True)

    # MONTOS
    base_amount = fields.Monetary('Base Imponible', readonly=True, currency_field='currency_id')
    tax_amount = fields.Monetary('Monto Impuesto', readonly=True, currency_field='currency_id')

    # BALANCE
    balance = fields.Monetary('Balance', readonly=True, currency_field='currency_id',
                             help='Positivo = A favor empresa, Negativo = A pagar')

    currency_id = fields.Many2one('res.currency', 'Moneda', readonly=True)
    company_id = fields.Many2one('res.company', 'Compañía', readonly=True)

    def init(self):
        """Vista SQL para balance de impuestos"""
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW bohio_tax_balance_report AS (
                SELECT
                    row_number() OVER () AS id,
                    DATE_TRUNC('month', am.date)::date AS period_month,
                    TO_CHAR(am.date, 'YYYY') AS period_year,
                    aml.tax_line_id AS tax_id,
                    CASE
                        WHEN am.move_type IN ('out_invoice', 'out_refund') THEN 'sale'
                        WHEN am.move_type IN ('in_invoice', 'in_refund') THEN 'purchase'
                    END AS tax_type,
                    SUM(aml.tax_base_amount) AS base_amount,
                    SUM(aml.balance) AS tax_amount,
                    SUM(CASE
                        WHEN am.move_type IN ('out_invoice', 'out_refund') THEN -aml.balance
                        ELSE aml.balance
                    END) AS balance,
                    am.currency_id,
                    am.company_id
                FROM account_move_line aml
                JOIN account_move am ON aml.move_id = am.id
                WHERE aml.tax_line_id IS NOT NULL
                    AND am.state = 'posted'
                GROUP BY
                    DATE_TRUNC('month', am.date),
                    TO_CHAR(am.date, 'YYYY'),
                    aml.tax_line_id,
                    CASE
                        WHEN am.move_type IN ('out_invoice', 'out_refund') THEN 'sale'
                        WHEN am.move_type IN ('in_invoice', 'in_refund') THEN 'purchase'
                    END,
                    am.currency_id,
                    am.company_id
            )
        """)

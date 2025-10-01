# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    advance_excess_as_advance = fields.Boolean(
        string='Excedentes como Anticipos',
        default=True,
        help='Convertir excedentes de pago en anticipos automáticamente'
    )
    advance_payment_journal_id = fields.Many2one(
        'account.journal',
        string='Diario de Anticipos',
        domain="[('type', '=', 'bank'), ('company_id', '=', id)]",
        help='Diario utilizado para registrar los anticipos'
    )
    default_customer_advance_account_id = fields.Many2one(
        'account.account',
        string='Cuenta de Anticipos de Clientes',
        domain="[('account_type', '=', 'liability_current'), ('deprecated', '=', False)]",
        help='Cuenta por defecto para anticipos de clientes'
    )
    treasury_auto_apply_advances = fields.Boolean(
        string='Aplicar Anticipos Automáticamente', 
        default=True,
        help='Aplica automáticamente los anticipos disponibles al confirmar facturas'
    )
    default_supplier_advance_account_id = fields.Many2one(
        'account.account',
        string='Cuenta de Anticipos de Proveedores',
        domain="[('account_type', '=', 'asset_current'), ('deprecated', '=', False)]",
        help='Cuenta por defecto para anticipos de proveedores'
    )

    default_employee_advance_account_id = fields.Many2one(
        'account.account',
        string='Cuenta de Anticipos de Empleados',
        domain="[('account_type', '=', 'asset_current'), ('deprecated', '=', False)]",
        help='Cuenta por defecto para anticipos de empleados'
    )

    third_party_advance_account_id = fields.Many2one(
        'account.account',
        string='Cuenta Global de Anticipos de Terceros',
        domain="[('deprecated', '=', False)]",
        help='Cuenta global para anticipos cuando no se especifica tipo'
    )
    treasury_multi_partner_default = fields.Boolean(
        string='Multi-Tercero por Defecto', 
        default=False,
        help='Activa multi-tercero por defecto en nuevos documentos'
    )
    auto_create_exchange_diff = fields.Boolean(
        string='Crear Diferencias de Cambio Automáticamente',
        default=True,
        help='Crear asientos de diferencia de cambio automáticamente en transferencias'
    )

    exchange_diff_threshold = fields.Float(
        string='Umbral de Diferencia de Cambio',
        default=0.01,
        help='Umbral mínimo para crear asientos de diferencia de cambio'
    )
# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PaymentOperationType(models.Model):
    _name = 'payment.operation.type'
    _description = 'Tipo de Operación de Pago'
    _order = 'sequence, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre del tipo de operación'
    )

    code = fields.Char(
        string='Código',
        required=True,
        size=10,
        help='Código corto para identificar el tipo de operación'
    )

    sequence_id = fields.Many2one(
        'ir.sequence',
        string='Secuencia',
        required=True,
        ondelete='restrict',
        help='Secuencia para generar números consecutivos'
    )

    payment_type = fields.Selection([
        ('outbound', 'Pago/Salida'),
        ('inbound', 'Cobro/Entrada'),
        ('transfer', 'Transferencia Interna')
    ], string='Tipo de Pago',
       required=True,
       default='outbound',
       help='Tipo de movimiento de pago asociado'
    )

    company_ids = fields.Many2many(
        'res.company',
        'operation_type_company_rel',
        'operation_type_id',
        'company_id',
        string='Compañías',
        default=lambda self: [(6, 0, [self.env.company.id])],
        help='Compañías donde aplica este tipo de operación'
    )

    account_ids = fields.Many2many(
        'account.account',
        'operation_type_account_rel',
        'operation_type_id',
        'account_id',
        string='Cuentas Permitidas',
        domain="[('deprecated', '=', False)]",
        help='Cuentas contables permitidas para este tipo de operación'
    )

    journal_ids = fields.Many2many(
        'account.journal',
        'operation_type_journal_rel',
        'operation_type_id',
        'journal_id',
        string='Diarios Permitidos',
        help='Diarios permitidos para este tipo de operación'
    )

    active = fields.Boolean(
        string='Activo',
        default=True
    )

    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de visualización'
    )

    description = fields.Text(
        string='Descripción',
        help='Descripción detallada del tipo de operación'
    )

    require_approval = fields.Boolean(
        string='Requiere Aprobación',
        default=False,
        help='Indica si los pagos de este tipo requieren aprobación'
    )

    approval_amount = fields.Float(
        string='Monto Aprobación',
        default=0.0,
        help='Monto a partir del cual se requiere aprobación (0 = siempre)'
    )

    color = fields.Integer(
        string='Color',
        default=0,
        help='Color para identificar visualmente en vistas kanban'
    )

    @api.constrains('code')
    def _check_code(self):
        for record in self:
            if self.search_count([
                ('code', '=', record.code),
                ('id', '!=', record.id),
                ('company_ids', 'in', record.company_ids.ids)
            ]) > 0:
                raise ValidationError(_('El código %s ya existe para alguna de las compañías seleccionadas.') % record.code)

    def get_next_number(self, date=None):
        """Obtiene el siguiente número de la secuencia"""
        self.ensure_one()
        if not self.sequence_id:
            raise ValidationError(_('No hay secuencia configurada para el tipo de operación %s') % self.name)

        context = {}
        if date:
            context['ir_sequence_date'] = date

        return self.sequence_id.with_context(**context).next_by_id()

    @api.model
    def create(self, vals):
        """Al crear, si no hay secuencia, crear una automáticamente"""
        if 'sequence_id' not in vals:
            # Crear secuencia automática
            code = vals.get('code', 'OP')
            sequence_vals = {
                'name': _('Secuencia %s') % vals.get('name', 'Operación'),
                'code': 'payment.operation.%s' % code.lower(),
                'prefix': '%s/%%(year)s/' % code.upper(),
                'padding': 5,
                'use_date_range': True,
                'company_id': False,  # Global para multi-compañía
            }
            sequence = self.env['ir.sequence'].create(sequence_vals)
            vals['sequence_id'] = sequence.id

        return super(PaymentOperationType, self).create(vals)

    def unlink(self):
        """Al eliminar, verificar que no haya pagos usando este tipo"""
        payments = self.env['account.payment'].search([
            ('operation_type_id', 'in', self.ids)
        ])
        if payments:
            raise ValidationError(_('No se puede eliminar el tipo de operación porque hay pagos que lo utilizan.'))
        return super(PaymentOperationType, self).unlink()

    def name_get(self):
        """Mostrar código y nombre"""
        result = []
        for record in self:
            name = '[%s] %s' % (record.code, record.name)
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100):
        """Buscar por código o nombre"""
        args = args or []
        if name:
            domain = ['|', ('code', operator, name), ('name', operator, name)]
            return self._search(domain + args, limit=limit)
        return self._search(args, limit=limit)
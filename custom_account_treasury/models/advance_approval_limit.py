# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AdvanceApprovalLimit(models.Model):
    """Límites de aprobación por usuario para anticipos"""
    _name = 'advance.approval.limit'
    _description = 'Límite de Aprobación de Anticipos'
    _order = 'sequence, id'
    _rec_name = 'user_id'

    # Configuración básica
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de evaluación de los límites'
    )

    active = fields.Boolean(
        string='Activo',
        default=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='company_id.currency_id',
        readonly=True
    )

    # Identificación
    name = fields.Char(
        string='Nombre',
        compute='_compute_name',
        store=True
    )

    code = fields.Char(
        string='Código',
        help='Código de referencia del límite de aprobación'
    )

    # Usuario aprobador
    user_id = fields.Many2one(
        'res.users',
        string='Usuario Aprobador',
        required=True,
        help='Usuario que puede aprobar anticipos'
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string='Empleado',
        compute='_compute_employee_id',
        store=True,
        help='Empleado asociado al usuario'
    )

    department_id = fields.Many2one(
        'hr.department',
        string='Departamento',
        related='employee_id.department_id',
        store=True
    )

    job_id = fields.Many2one(
        'hr.job',
        string='Puesto de Trabajo',
        related='employee_id.job_id',
        store=True
    )

    # Tipo de configuración
    approval_mode = fields.Selection([
        ('simple', 'Solo Aprobación'),
        ('amount_limit', 'Con Límite de Monto'),
        ('hierarchical', 'Jerárquico')
    ],
        string='Modo de Aprobación',
        default='amount_limit',
        required=True,
        help='Simple: solo puede aprobar sin límite\n'
             'Con Límite: puede aprobar hasta un monto\n'
             'Jerárquico: aprueba según jerarquía organizacional'
    )

    approval_level = fields.Integer(
        string='Nivel de Aprobación',
        default=1,
        help='Nivel jerárquico de aprobación (1=primer nivel, 2=segundo nivel, etc.)'
    )

    # Límites de monto
    min_amount = fields.Monetary(
        string='Monto Mínimo',
        currency_field='currency_id',
        default=0,
        help='Monto mínimo que puede aprobar (0 = sin mínimo)'
    )

    max_amount = fields.Monetary(
        string='Monto Máximo',
        currency_field='currency_id',
        default=0,
        help='Monto máximo que puede aprobar (0 = sin límite)'
    )

    # Aplicación específica
    advance_type_ids = fields.Many2many(
        'advance.type',
        'approval_limit_type_rel',
        'limit_id',
        'type_id',
        string='Tipos de Anticipo',
        help='Tipos de anticipo a los que aplica este límite. Vacío = todos'
    )

    stage_ids = fields.Many2many(
        'advance.request.stage',
        'approval_limit_stage_rel',
        'limit_id',
        'stage_id',
        string='Etapas',
        help='Etapas donde puede aprobar. Vacío = todas las etapas de aprobación'
    )

    partner_ids = fields.Many2many(
        'res.partner',
        'approval_limit_partner_rel',
        'limit_id',
        'partner_id',
        string='Clientes/Proveedores',
        help='Partners específicos que puede aprobar. Vacío = todos'
    )

    partner_category_ids = fields.Many2many(
        'res.partner.category',
        'approval_limit_category_rel',
        'limit_id',
        'category_id',
        string='Categorías de Partner',
        help='Categorías de partner que puede aprobar. Vacío = todas'
    )

    # Condiciones adicionales
    require_two_approvals = fields.Boolean(
        string='Requiere Doble Aprobación',
        default=False,
        help='Requiere aprobación de otro usuario además de este'
    )

    second_approver_id = fields.Many2one(
        'res.users',
        string='Segundo Aprobador',
        help='Usuario que debe aprobar después de este'
    )

    can_self_approve = fields.Boolean(
        string='Puede Auto-aprobar',
        default=False,
        help='Puede aprobar sus propias solicitudes'
    )

    # Delegación
    delegate_to_id = fields.Many2one(
        'res.users',
        string='Delegar a',
        help='Usuario al que se delegan las aprobaciones temporalmente'
    )

    delegate_user_id = fields.Many2one(
        'res.users',
        string='Usuario Delegado',
        related='delegate_to_id',
        readonly=True
    )

    delegation_date_from = fields.Date(
        string='Delegación desde'
    )

    delegate_from = fields.Date(
        string='Delegar Desde',
        related='delegation_date_from',
        readonly=True
    )

    delegation_date_to = fields.Date(
        string='Delegación hasta'
    )

    delegate_to = fields.Date(
        string='Delegar Hasta',
        related='delegation_date_to',
        readonly=True
    )

    delegate_reason = fields.Text(
        string='Motivo de Delegación',
        help='Razón por la cual se delegan las aprobaciones'
    )

    # Escalamiento
    auto_approve_if_no_response = fields.Boolean(
        string='Auto-aprobar si no responde',
        default=False,
        help='Aprobar automáticamente si no responde en el tiempo establecido'
    )

    escalate_after_days = fields.Integer(
        string='Escalar después de (días)',
        default=3,
        help='Días para escalar si no hay respuesta'
    )

    escalate_to_user_id = fields.Many2one(
        'res.users',
        string='Escalar a Usuario',
        help='Usuario al que se escala si no hay respuesta'
    )

    # Campo de notas adicional
    notes = fields.Text(
        string='Notas',
        help='Notas adicionales sobre este límite de aprobación'
    )

    ref = fields.Char(
        string='Referencia',
        help='Referencia externa'
    )

    # Estadísticas
    approval_count = fields.Integer(
        string='Aprobaciones Realizadas',
        compute='_compute_statistics'
    )

    pending_count = fields.Integer(
        string='Pendientes de Aprobar',
        compute='_compute_statistics'
    )

    avg_approval_time = fields.Float(
        string='Tiempo Promedio (días)',
        compute='_compute_statistics',
        help='Tiempo promedio para aprobar solicitudes'
    )

    @api.depends('user_id', 'code')
    def _compute_name(self):
        """Calcula el nombre del límite de aprobación"""
        for record in self:
            if record.code:
                record.name = f"[{record.code}] {record.user_id.name if record.user_id else ''}"
            else:
                record.name = record.user_id.name if record.user_id else 'Nuevo'

    @api.depends('user_id')
    def _compute_employee_id(self):
        """Obtiene el empleado asociado al usuario"""
        for record in self:
            employee = self.env['hr.employee'].search([
                ('user_id', '=', record.user_id.id)
            ], limit=1)
            record.employee_id = employee

    def _compute_statistics(self):
        """Calcula estadísticas de aprobación"""
        for record in self:
            # Aprobaciones realizadas
            approved = self.env['advance.request'].search_count([
                ('approved_by', '=', record.user_id.id)
            ])
            record.approval_count = approved

            # Pendientes de aprobar
            pending = self.env['advance.request'].search_count([
                ('stage_id.approval_user_ids', 'in', record.user_id.id),
                ('stage_id.can_create_draft_payment', '=', False),
                ('stage_id.can_post_payment', '=', False)
            ])
            record.pending_count = pending

            # Tiempo promedio
            requests = self.env['advance.request'].search([
                ('approved_by', '=', record.user_id.id),
                ('date_approved', '!=', False),
                ('date_request', '!=', False)
            ], limit=100)

            if requests:
                total_days = sum([
                    (r.date_approved - fields.Datetime.from_string(str(r.date_request))).days
                    for r in requests if r.date_approved and r.date_request
                ])
                record.avg_approval_time = total_days / len(requests) if requests else 0
            else:
                record.avg_approval_time = 0

    @api.constrains('min_amount', 'max_amount')
    def _check_amounts(self):
        """Valida que los montos sean coherentes"""
        for record in self:
            if record.approval_mode == 'amount_limit':
                if record.min_amount < 0 or record.max_amount < 0:
                    raise ValidationError(_('Los montos no pueden ser negativos'))

                if record.min_amount > 0 and record.max_amount > 0:
                    if record.min_amount > record.max_amount:
                        raise ValidationError(_('El monto mínimo no puede ser mayor que el máximo'))

    @api.constrains('delegation_date_from', 'delegation_date_to')
    def _check_delegation_dates(self):
        """Valida las fechas de delegación"""
        for record in self:
            if record.delegation_date_from and record.delegation_date_to:
                if record.delegation_date_from > record.delegation_date_to:
                    raise ValidationError(_('La fecha de inicio de delegación debe ser anterior a la fecha fin'))

    def can_approve_amount(self, amount, advance_type=None, partner=None, stage=None):
        """
        Verifica si puede aprobar un monto específico

        :param amount: Monto a aprobar
        :param advance_type: Tipo de anticipo (opcional)
        :param partner: Partner (opcional)
        :param stage: Etapa (opcional)
        :return: Boolean
        """
        self.ensure_one()

        # Si no está activo, no puede aprobar
        if not self.active:
            return False

        # Verificar delegación
        today = fields.Date.today()
        if self.delegate_to_id and self.delegation_date_from and self.delegation_date_to:
            if self.delegation_date_from <= today <= self.delegation_date_to:
                return False  # Está delegado a otro usuario

        # Modo simple - siempre puede aprobar
        if self.approval_mode == 'simple':
            return True

        # Verificar tipo de anticipo
        if self.advance_type_ids and advance_type:
            if advance_type not in self.advance_type_ids:
                return False

        # Verificar etapa
        if self.stage_ids and stage:
            if stage not in self.stage_ids:
                return False

        # Verificar partner
        if partner:
            if self.partner_ids and partner not in self.partner_ids:
                return False

            if self.partner_category_ids:
                if not (partner.category_id & self.partner_category_ids):
                    return False

        # Verificar montos
        if self.approval_mode == 'amount_limit':
            if self.min_amount > 0 and amount < self.min_amount:
                return False

            if self.max_amount > 0 and amount > self.max_amount:
                return False

        return True

    def get_approver_for_amount(self, amount, advance_type=None, partner=None, stage=None):
        """
        Obtiene el aprobador adecuado para un monto

        :param amount: Monto a aprobar
        :param advance_type: Tipo de anticipo (opcional)
        :param partner: Partner (opcional)
        :param stage: Etapa (opcional)
        :return: res.users record o False
        """
        domain = [
            ('active', '=', True),
            ('company_id', '=', self.env.company.id)
        ]

        if advance_type:
            domain += ['|', ('advance_type_ids', '=', False),
                      ('advance_type_ids', 'in', advance_type.id)]

        if stage:
            domain += ['|', ('stage_ids', '=', False),
                      ('stage_ids', 'in', stage.id)]

        limits = self.search(domain, order='sequence')

        for limit in limits:
            if limit.can_approve_amount(amount, advance_type, partner, stage):
                # Verificar delegación
                if limit.delegate_to_id:
                    today = fields.Date.today()
                    if limit.delegation_date_from and limit.delegation_date_to:
                        if limit.delegation_date_from <= today <= limit.delegation_date_to:
                            return limit.delegate_to_id

                return limit.user_id

        return False

    @api.model
    def get_approval_matrix(self, advance_type=None):
        """
        Obtiene la matriz de aprobación para visualización

        :param advance_type: Tipo de anticipo (opcional)
        :return: Lista de diccionarios con información de aprobación
        """
        domain = [('active', '=', True)]

        if advance_type:
            domain += ['|', ('advance_type_ids', '=', False),
                      ('advance_type_ids', 'in', advance_type.id)]

        limits = self.search(domain, order='sequence')

        matrix = []
        for limit in limits:
            matrix.append({
                'user': limit.user_id.name,
                'employee': limit.employee_id.name if limit.employee_id else '',
                'department': limit.department_id.name if limit.department_id else '',
                'job': limit.job_id.name if limit.job_id else '',
                'mode': dict(self._fields['approval_mode'].selection)[limit.approval_mode],
                'min_amount': limit.min_amount,
                'max_amount': limit.max_amount,
                'types': ', '.join(limit.advance_type_ids.mapped('name')) if limit.advance_type_ids else 'Todos',
                'delegated_to': limit.delegate_to_id.name if limit.delegate_to_id else '',
                'pending': limit.pending_count
            })

        return matrix

    def action_view_pending_approvals(self):
        """Ver solicitudes pendientes de aprobación"""
        self.ensure_one()

        return {
            'name': _('Solicitudes Pendientes de Aprobación'),
            'type': 'ir.actions.act_window',
            'res_model': 'advance.request',
            'view_mode': 'list,kanban,form',
            'domain': [
                ('stage_id.approval_user_ids', 'in', self.user_id.id)
            ],
            'context': {
                'search_default_pending': True
            }
        }

    def action_delegate_approvals(self):
        """Abre wizard para delegar aprobaciones"""
        self.ensure_one()

        return {
            'name': _('Delegar Aprobaciones'),
            'type': 'ir.actions.act_window',
            'res_model': 'advance.approval.delegation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_limit_id': self.id,
                'default_user_id': self.user_id.id,
            }
        }

    @api.model
    def create_default_limits(self):
        """Crea límites de aprobación por defecto basados en jerarquía"""
        # Buscar grupos de aprobación
        groups = [
            ('account.group_account_manager', 0, 0),  # Sin límite
            ('account.group_account_user', 100000, 5000000),  # Límites medios
            ('hr.group_hr_manager', 50000, 2000000),  # Para empleados
        ]

        for group_xml_id, min_amt, max_amt in groups:
            group = self.env.ref(group_xml_id, False)
            if group:
                for user in group.users:
                    existing = self.search([
                        ('user_id', '=', user.id),
                        ('company_id', '=', user.company_id.id)
                    ])

                    if not existing:
                        self.create({
                            'user_id': user.id,
                            'company_id': user.company_id.id,
                            'approval_mode': 'amount_limit' if max_amt else 'simple',
                            'min_amount': min_amt,
                            'max_amount': max_amt
                        })

    def name_get(self):
        """Muestra nombre descriptivo"""
        result = []
        for record in self:
            name = record.user_id.name
            if record.approval_mode == 'amount_limit' and record.max_amount:
                name += f' (Hasta {record.max_amount:,.0f})'
            result.append((record.id, name))
        return result
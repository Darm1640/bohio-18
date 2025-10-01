# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AdvanceRequestStageHistory(models.Model):
    """Historial de cambios de etapa para solicitudes de anticipo"""
    _name = 'advance.request.stage.history'
    _description = 'Historial de Etapas de Solicitud de Anticipo'
    _order = 'enter_date desc'
    _rec_name = 'stage_id'

    request_id = fields.Many2one(
        'advance.request',
        string='Solicitud',
        required=True,
        ondelete='cascade',
        index=True
    )

    stage_id = fields.Many2one(
        'advance.request.stage',
        string='Etapa',
        required=True
    )

    enter_date = fields.Datetime(
        string='Fecha Entrada',
        required=True
    )

    exit_date = fields.Datetime(
        string='Fecha Salida'
    )

    duration = fields.Float(
        string='Duración (horas)',
        help='Tiempo que duró en esta etapa'
    )

    duration_formatted = fields.Char(
        string='Duración',
        compute='_compute_duration_formatted'
    )

    user_id = fields.Many2one(
        'res.users',
        string='Usuario',
        help='Usuario que realizó el cambio'
    )

    @api.depends('duration')
    def _compute_duration_formatted(self):
        """Formatea la duración en un formato legible"""
        for record in self:
            if record.duration:
                hours = int(record.duration)
                minutes = int((record.duration - hours) * 60)

                if hours > 24:
                    days = hours // 24
                    hours = hours % 24
                    record.duration_formatted = f"{days}d {hours}h {minutes}m"
                elif hours > 0:
                    record.duration_formatted = f"{hours}h {minutes}m"
                else:
                    record.duration_formatted = f"{minutes}m"
            else:
                record.duration_formatted = '0m'



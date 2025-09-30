# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    """Extensión de product.template para integración con CRM"""
    _inherit = 'product.template'

    def action_add_to_lead_comparison(self):
        """Agregar propiedad a la comparación de un lead desde el contexto o wizard"""
        self.ensure_one()

        lead_id = self.env.context.get('lead_id')

        # Si no viene lead_id en el contexto, abrir wizard para seleccionar oportunidad
        if not lead_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Seleccionar Oportunidad'),
                'res_model': 'crm.lead',
                'view_mode': 'list,form',
                'domain': [('type', '=', 'opportunity'), ('active', '=', True)],
                'context': {
                    'default_type': 'opportunity',
                    'property_to_add': self.id,
                },
                'target': 'new',
            }

        lead = self.env['crm.lead'].browse(lead_id)
        if not lead.exists():
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': _('La oportunidad no existe.'),
                    'type': 'danger',
                    'sticky': False,
                }
            }

        # Validar límite de 4 propiedades
        if len(lead.compared_properties_ids) >= 4:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Límite Alcanzado'),
                    'message': _('Ya tiene 4 propiedades en comparación. Elimine una para agregar otra.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # Validar que no esté ya agregada
        if self.id in lead.compared_properties_ids.ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Ya Agregada'),
                    'message': _('Esta propiedad ya está en la comparación.'),
                    'type': 'info',
                    'sticky': False,
                }
            }

        # Agregar a la comparación
        lead.write({
            'compared_properties_ids': [(4, self.id)]
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Propiedad Agregada'),
                'message': _('Propiedad "%s" agregada al comparador (%d/4)') % (self.name, len(lead.compared_properties_ids)),
                'type': 'success',
                'sticky': False,
            }
        }
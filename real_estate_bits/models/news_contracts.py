from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError, AccessError
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)

class PropertyContractNovedad(models.Model):
    _name = "property.contract.novedad"
    _description = "Novedades de Contrato de Propiedad"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _check_company_auto = True
    name = fields.Char('Código', size=64, readonly=True, default='/')
    contract_id = fields.Many2one('property.contract', 'Contrato de Propiedad', required=True)
    partner_id = fields.Many2one('res.partner', related='contract_id.partner_id', string='Cliente', store=True)
    category_id = fields.Many2one('property.contract.novedad.category', 'Categoría', required=True)
    tipo = fields.Selection([
        ('unico', 'Pago Único'),
        ('cuotas', 'Por Cuotas')
    ], string='Tipo de Novedad', default='unico', required=True)
    aplicacion = fields.Selection([
        ('factura', 'En Factura'),
        ('pago', 'En Pago')
    ], string='Aplicación', required=True, default='factura')
    destinatario = fields.Selection([
        ('propietario', 'Propietario'),
        ('arrendatario', 'Arrendatario'),
        ('all', 'Propietario + Arrendatario'),
    ], string='Destinatario', required=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmada'),
        ('done', 'Procesada'),
        ('paid', 'Pagada'),
        ('cancelled', 'Cancelada'),
    ], string='Estado', default='draft', tracking=True)
    valor_total = fields.Float("Valor Total", digits='Account', required=True)
    numero_cuotas = fields.Integer("Número de Cuotas", default=1)
    fecha_inicio = fields.Date('Fecha de Inicio', required=True, default=fields.Date.today)
    descripcion = fields.Text('Descripción')
    cuota_ids = fields.One2many('property.contract.novedad.cuota', 'novedad_id', 'Cuotas')
    partner_is_owner_id = fields.Many2one(related="contract_id.property_id.partner_id")
    is_multi_propietario = fields.Boolean(related="contract_id.property_id.is_multi_owner")
    owners_lines = fields.One2many(related="contract_id.property_id.owners_lines")
    invoice_id = fields.Many2one('account.move', 'Factura', readonly=True)
    payment_id = fields.Many2one('account.move', 'Pago', readonly=True)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
    journal_bank_id = fields.Many2one('account.journal', 'Diario de Pago',  domain=[('type', 'in', ['bank', 'cash'])])
    pay_date = fields.Date('Fecha de Pago')
    percentage_propietario = fields.Float(string="(%) propietario", required=True)
    percentage_arrendatario = fields.Float(string="(%) Arrendatario", required=True)
    fecha_cobro = fields.Date('Fecha de Cobro', help="Fecha para aplicar el cobro en caso de pago único")
    date_from = fields.Date('Fecha desde')
    date_to = fields.Date('Fecha hasta')
    
    @api.constrains('valor_total')
    def _no_amount(self):
        for advance in self:
            if advance.valor_total == 0.00:
                raise ValidationError(_("El monto no puede ser cero"))

    @api.constrains('percentage_propietario','percentage_arrendatario')
    def _no_amount_porce(self):
        for advance in self:
            if advance.destinatario == "all":
                porc = advance.percentage_propietario + advance.percentage_arrendatario
                if porc != 100:
                    raise ValidationError(_("La distribucion entre el arrendatario y propietario debe ser igual al 100%"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('property.contract.novedad.seq') or '/'
        return super(PropertyContractNovedad, self).create(vals_list)

    def action_confirm(self):
        self.ensure_one()
        if self.tipo == 'cuotas':
            self.generar_cuotas()
        self.state = 'confirmed'

    def action_process(self):
        self.ensure_one()
        if self.aplicacion == 'factura':
            pass
            #self.generar_factura()
        else:
            self.generar_pago()
        self.state = 'done'

    def action_cancel(self):
        self.ensure_one()
        self.state = 'cancelled'

    def generar_cuotas(self):
        self.ensure_one()
        self.cuota_ids.unlink()
        valor_cuota = self.valor_total / self.numero_cuotas
        for i in range(self.numero_cuotas):
            self.env['property.contract.novedad.cuota'].create({
                'novedad_id': self.id,
                'numero_cuota': i + 1,
                'valor': valor_cuota,
                'fecha_vencimiento': self.fecha_inicio + relativedelta(months=i)
            })



    def generar_pago(self):
        for advance in self:
            if not advance.payment_id:
                if  not advance.pay_date:
                    raise ValidationError(_("Falta la fecha de pago"))
                if  not advance.journal_bank_id:
                    raise ValidationError(_("Falta el diario de pago"))
                date = advance.pay_date
                move_vals = {
                    'partner_id': advance.partner_id.id,
                    'journal_id': advance.journal_bank_id.id,
                    'date': date,
                    'ref': advance.name,
                }
                move = self.env['account.move'].create(move_vals)

                amount = advance.valor_total
                line_vals = [
                    {
                        'partner_id': advance.partner_id.id,
                        'account_id': advance.category_id.account_id.id,
                        'debit': amount,
                        'credit': 0,
                        'name': advance.name,
                    },
                    {
                        'partner_id': advance.partner_id.id,
                        'account_id': advance.journal_bank_id.default_account_id.id,
                        'debit': 0,
                        'credit': amount,
                        'name': advance.name,
                    }
                ]
                _logger.error("Line values for payment: %s", line_vals)
                move.write({'line_ids': [(0, 0, line) for line in line_vals]})
                move.action_post()

                advance.write({
                    'payment_id': move.id,
                })

    @api.onchange('tipo')
    def _onchange_tipo(self):
        if self.tipo == 'unico':
            self.fecha_cobro = fields.Date.today()
        else:
            self.fecha_cobro = False



    def generar_factura(self):
        # Implementar la lógica de generación de factura
        pass

    def generar_pago(self):
        self.ensure_one()
        if not self.payment_id:
            if self.tipo == 'unico' and not self.fecha_cobro:
                raise ValidationError(_("Falta la fecha de cobro para el pago único"))
            if not self.journal_bank_id:
                raise ValidationError(_("Falta el diario de pago"))
            
            date = self.fecha_cobro if self.tipo == 'unico' else self.pay_date
            move_vals = {
                'partner_id': self._get_partner_for_accounting().id,
                'journal_id': self.journal_bank_id.id,
                'date': date,
                'ref': self.name,
            }
            move = self.env['account.move'].create(move_vals)

            amount = self.valor_total
            line_vals = self._prepare_payment_line_vals(amount)

            move.write({'line_ids': [(0, 0, line) for line in line_vals]})
            move.action_post()

            self.write({
                'payment_id': move.id,
            })

    def _get_partner_for_accounting(self):
        if self.destinatario == 'propietario':
            return self.partner_is_owner_id
        elif self.destinatario == 'arrendatario':
            return self.partner_id
        elif self.destinatario == 'all':
            # En este caso, podrías decidir a quién facturar primero
            return self.partner_id
        
    def _get_owners_distribution(self):
        self.ensure_one()
        if self.is_multi_propietario:
            return {line.partner_id: line.percentage for line in self.owners_lines}
        return {self.partner_is_owner_id: 100.0}

    def _prepare_payment_line_vals(self, amount):
        if self.destinatario == 'all':
            prop_amount = amount * (self.percentage_propietario / 100)
            arr_amount = amount * (self.percentage_arrendatario / 100)
            lines = []
            
            if self.is_multi_propietario:
                owners_distribution = self._get_owners_distribution()
                for owner, percentage in owners_distribution.items():
                    owner_amount = prop_amount * (percentage / 100)
                    lines.append({
                        'partner_id': owner.id,
                        'account_id': self.category_id.account_id.id,
                        'debit': owner_amount,
                        'credit': 0,
                        'name': f"{self.name} - Propietario {owner.name}",
                    })
            else:
                lines.append({
                    'partner_id': self.partner_is_owner_id.id,
                    'account_id': self.category_id.account_id.id,
                    'debit': prop_amount,
                    'credit': 0,
                    'name': f"{self.name} - Propietario",
                })
            
            lines.append({
                'partner_id': self.partner_id.id,
                'account_id': self.category_id.account_id.id,
                'debit': arr_amount,
                'credit': 0,
                'name': f"{self.name} - Arrendatario",
            })
            
            lines.append({
                'partner_id': self.partner_id.id,
                'account_id': self.journal_bank_id.default_account_id.id,
                'debit': 0,
                'credit': amount,
                'name': self.name,
            })
            
            return lines
        elif self.destinatario == 'propietario':
            lines = []
            if self.is_multi_propietario:
                owners_distribution = self._get_owners_distribution()
                for owner, percentage in owners_distribution.items():
                    owner_amount = amount * (percentage / 100)
                    lines.append({
                        'partner_id': owner.id,
                        'account_id': self.category_id.account_id.id,
                        'debit': owner_amount,
                        'credit': 0,
                        'name': f"{self.name} - Propietario {owner.name}",
                    })
            else:
                lines.append({
                    'partner_id': self.partner_is_owner_id.id,
                    'account_id': self.category_id.account_id.id,
                    'debit': amount,
                    'credit': 0,
                    'name': f"{self.name} - Propietario",
                })
            
            lines.append({
                'partner_id': self.partner_is_owner_id.id,
                'account_id': self.journal_bank_id.default_account_id.id,
                'debit': 0,
                'credit': amount,
                'name': self.name,
            })
            
            return lines
        else:  # arrendatario
            return [
                {
                    'partner_id': self.partner_id.id,
                    'account_id': self.category_id.account_id.id,
                    'debit': amount,
                    'credit': 0,
                    'name': self.name,
                },
                {
                    'partner_id': self.partner_id.id,
                    'account_id': self.journal_bank_id.default_account_id.id,
                    'debit': 0,
                    'credit': amount,
                    'name': self.name,
                }
            ]

    def generar_cuotas(self):
        self.ensure_one()
        self.cuota_ids.unlink()
        valor_cuota = self.valor_total / self.numero_cuotas
        owners_distribution = self._get_owners_distribution()
        
        for i in range(self.numero_cuotas):
            if self.destinatario == 'all':
                valor_propietario = valor_cuota * (self.percentage_propietario / 100)
                valor_arrendatario = valor_cuota * (self.percentage_arrendatario / 100)
            elif self.destinatario == 'propietario':
                valor_propietario = valor_cuota
                valor_arrendatario = 0
            else:  # arrendatario
                valor_propietario = 0
                valor_arrendatario = valor_cuota

            cuota = self.env['property.contract.novedad.cuota'].create({
                'novedad_id': self.id,
                'numero_cuota': i + 1,
                'valor': valor_cuota,
                'fecha_vencimiento': self.fecha_inicio + relativedelta(months=i),
                'valor_propietario': valor_propietario,
                'valor_arrendatario': valor_arrendatario,
            })
            
            if self.is_multi_propietario and self.destinatario in ['propietario', 'all']:
                for owner, percentage in owners_distribution.items():
                    self.env['property.contract.novedad.cuota.owner'].create({
                        'cuota_id': cuota.id,
                        'partner_id': owner.id,
                        'percentage': percentage,
                        'valor': valor_propietario * (percentage / 100),
                    })

    @api.onchange('aplicacion')
    def _onchange_aplicacion(self):
        if self.aplicacion == 'pago':
            self.destinatario = 'propietario'
        else:
            self.destinatario = 'arrendatario'

    def action_unify_quotas(self):
        self.ensure_one()
        if self.state != 'confirmed' or self.tipo != 'cuotas':
            raise UserError(_("Solo se pueden unificar cuotas de novedades confirmadas y de tipo cuotas."))
        
        cuotas_a_unificar = self.cuota_ids.filtered(lambda c: c.unificar and c.estado == 'pendiente')
        if len(cuotas_a_unificar) <= 1:
            raise UserError(_("Debes seleccionar al menos dos cuotas pendientes para unificar."))
        
        total_a_unificar = sum(cuotas_a_unificar.mapped('valor'))
        valor_unificado = total_a_unificar / len(cuotas_a_unificar)
        
        for cuota in cuotas_a_unificar:
            cuota.valor = valor_unificado
            cuota.unificar = False
        
        self.message_post(body=_("Se han unificado %d cuotas seleccionadas." % len(cuotas_a_unificar)))

    def action_postpone_quotas(self):
        self.ensure_one()
        if self.state != 'done' or self.tipo != 'cuotas':
            raise UserError(_("Solo se pueden trasladar cuotas de novedades confirmadas y de tipo cuotas."))
        
        wizard = self.env['postpone.quota.wizard'].create({
            'novedad_id': self.id,
        })
        
        return {
            'name': _('Trasladar Cuotas'),
            'type': 'ir.actions.act_window',
            'res_model': 'postpone.quota.wizard',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }



class PropertyContractNovedadCuota(models.Model):
    _name = "property.contract.novedad.cuota"
    _description = "Cuotas de Novedad de Contrato de Propiedad"

    novedad_id = fields.Many2one('property.contract.novedad', 'Novedad', required=True, ondelete="cascade")
    numero_cuota = fields.Integer("Número de Cuota", required=True)
    valor = fields.Float("Valor", digits='Account', required=True)
    fecha_vencimiento = fields.Date('Fecha de Vencimiento', required=True)
    estado = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada')
    ], string='Estado', default='pendiente')
    unificar = fields.Boolean('Unificar', default=False)
    valor_arrendatario = fields.Float("Valor Arrendatario", digits='Account', required=True)
    valor_propietario = fields.Float("Valor Propietario", digits='Account', required=True)
    owner_ids = fields.One2many('property.contract.novedad.cuota.owner', 'cuota_id', string="Propietarios")

class PropertyContractNovedadCuotaOwner(models.Model):
    _name = "property.contract.novedad.cuota.owner"
    _description = "Distribución de cuota por propietario"

    cuota_id = fields.Many2one('property.contract.novedad.cuota', string="Cuota", required=True, ondelete="cascade")
    partner_id = fields.Many2one('res.partner', string="Propietario", required=True)
    percentage = fields.Float("Porcentaje", digits=(5,2), required=True)
    valor = fields.Float("Valor", digits='Account', required=True)

    @api.depends('partner_id', 'percentage')
    def _compute_display_name(self):
        for template in self:
            partner_name = template.partner_id.name or ''
            percentage = template.valor or 0
            product_name =  ''
            
            if partner_name and percentage:
                template.display_name = f'[{percentage}] {partner_name}' #f'[{partner_name}] {percentage}% {product_name}'
            elif partner_name:
                template.display_name = f'[{partner_name}] {product_name}'
            else:
                template.display_name = product_name

class PropertyContractNovedadCategory(models.Model):
    _name = "property.contract.novedad.category"
    _description = "Categoría de Novedad de Contrato de Propiedad"
    _check_company_auto = True

    name = fields.Char('Nombre', required=True)
    code = fields.Char('Código', required=True)
    account_id = fields.Many2one('account.account',  check_company=True, string="Cuenta Contable", required=True)
    descripcion = fields.Text('Descripción')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company)
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'El Nombre tiene que ser único!'),
        ('code_uniq', 'unique(code)', 'El Código tiene que ser único!'),
    ]

class PostponeQuotaWizard(models.TransientModel):
    _name = 'postpone.quota.wizard'
    _description = 'Wizard para Trasladar Cuotas'

    novedad_id = fields.Many2one('property.contract.novedad', string='Novedad', required=True)
    months_to_postpone = fields.Integer(string='Meses a Trasladar', required=True, default=1)

    def action_postpone(self):
        self.ensure_one()
        if self.months_to_postpone <= 0:
            raise UserError(_("El número de meses a trasladar debe ser positivo."))
        
        for cuota in self.novedad_id.cuota_ids.filtered(lambda c: c.estado == 'pendiente'):
            cuota.fecha_vencimiento = cuota.fecha_vencimiento + relativedelta(months=self.months_to_postpone)
        
        self.novedad_id.message_post(body=_("Las cuotas pendientes han sido trasladadas %d meses." % self.months_to_postpone))
        
        return {'type': 'ir.actions.act_window_close'}

class PropertyContract(models.Model):
    _inherit = 'property.contract'

    novedad_ids = fields.One2many('property.contract.novedad', 'contract_id', string='Novedades')
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from collections import defaultdict
from datetime import date
from dateutil.relativedelta import relativedelta
class Recaudo(models.Model):
    _name = 'recaudo.recaudo'
    _description = 'Recaudo'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nombre', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
    date_from = fields.Date(string='Fecha desde', required=True)
    date_to = fields.Date(string='Fecha hasta', required=True)
    journal_id = fields.Many2one('account.journal', string='Diario', domain=[('type', 'in', ['cash', 'bank'])], required=True)
    reference = fields.Char(string='Referencia')
    notes = fields.Text(string='Notas')
    user_id = fields.Many2one('res.users', string='Creado por', default=lambda self: self.env.user, readonly=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('pending', 'Pendiente'),
        ('paid', 'Pagado'),
        ('reversed', 'Revertido')
    ], string='Estado', default='draft', tracking=True)
    operation_type = fields.Selection([
        ('collect', 'Cobro'),
        ('payment', 'Pago'),
        ('both', 'Ambos')
    ], string='Tipo de operación', required=True)
    contract_ids = fields.Many2many('property.contract', string='Contratos')
    line_ids = fields.One2many('recaudo.line', 'recaudo_id', string='Líneas de recaudo')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('recaudo.recaudo') or _('New')
        return super(Recaudo, self).create(vals)

    def action_pending(self):
        self.state = 'pending'
        self.message_post(body=_("Recaudo marcado como pendiente"), message_type="notification")
        self.notify_accounting_team()

    def action_paid(self):
        if all(line.is_paid for line in self.line_ids):
            self.state = 'paid'
        else:
            raise UserError(_("No todas las líneas están marcadas como pagadas."))

    def process_recaudo(self):
        for line in self.line_ids:
            line.process_line()
        self.state = 'processed'
        
    def action_reverse(self):
        self.state = 'reversed'

    def notify_accounting_team(self):
        accounting_team = self.env.ref('account.group_account_manager')
        message = _(f"El recaudo {self.name} ha sido marcado como pendiente y requiere su atención.")
        self.message_post(body=message, partner_ids=accounting_team.users.mapped('partner_id').ids)

    def action_load_contracts(self):
        return {
            'name': _('Seleccionar Contratos'),
            'type': 'ir.actions.act_window',
            'res_model': 'recaudo.contract.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_recaudo_id': self.id}
        }

    def generate_recaudo_lines(self):
        for contract in self.contract_ids:
            if self.operation_type in ['collect', 'both']:
                # Línea para el arrendatario
                self._create_recaudo_line(contract.partner_id, contract, 100, 'arrendatario')

            if self.operation_type in ['payment', 'both']:
                if contract.partner_is_owner_id and not contract.property_id.owners_lines:
                    # Caso de un solo propietario
                    self._create_recaudo_line(contract.partner_is_owner_id, contract, 100, 'propietario')
                else:
                    # Caso de múltiples propietarios
                    for owner in contract.property_id.owners_lines:
                        self._create_recaudo_line(owner.partner_id, contract, owner.percentage, 'propietario')

    def _create_recaudo_line(self, partner, contract, percentage, destinatario):
        line = self.env['recaudo.line'].create({
            'recaudo_id': self.id,
            'partner_id': partner.id,
            'contract_id': contract.id,
            'percentage': percentage,
            'destinatario': destinatario,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'date': self.date_to,
            'journal_id': self.journal_id.id,
        })
        line.load_invoices()
        line.load_novedades()
        if destinatario == 'propietario':
            line.load_commissions()


class RecaudoLine(models.Model):
    _name = 'recaudo.line'
    _description = 'Línea de Recaudo'

    @api.depends('destinatario')
    def _compute_document_type(self):
        for record in self:
            record.document_type = 'Comprobante de Egreso' if record.destinatario == 'propietario' else 'Recibo de Caja'

    document_type = fields.Char(compute='_compute_document_type', string='Tipo de Documento')
    name = fields.Char(string='Nombre', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
    recaudo_id = fields.Many2one('recaudo.recaudo', string='Recaudo')
    partner_id = fields.Many2one('res.partner', string='Arrendatario/Propietario')
    contract_id = fields.Many2one('property.contract', string='Contrato')
    percentage = fields.Float(string='Porcentaje', default=100, readonly=True)
    is_paid = fields.Boolean(string='Pagado')
    concept_ids = fields.One2many('recaudo.line.concept', 'recaudo_line_id', string='Conceptos')
    destinatario = fields.Selection([
        ('propietario', 'Propietario'),
        ('arrendatario', 'Arrendatario')
    ], string='Destinatario', required=True)
    move_type = fields.Selection([
        ('entry', 'Entrada'),
        ('out', 'Salida')
    ], string='Tipo de Movimiento', compute='_compute_move_type', store=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('pending', 'Pendiente'),
        ('paid', 'Pagado'),
        ('reversed', 'Revertido')
    ], string='Estado', default='draft', tracking=True)
    move_id = fields.Many2one('account.move', string='Asiento Contable', readonly=True)
    contract_partner_ids = fields.Many2many(
        'res.partner', 
        'recaudo_line_partner_rel',  # Nombre explícito de la tabla de relación
        'recaudo_line_id',
        'partner_id',
        compute='_compute_contract_partner_ids', 
        store=True
    )
    date_from = fields.Date(string='Fecha desde', required=True)
    date_to = fields.Date(string='Fecha hasta', required=True)
    date = fields.Date(string='Fecha Publicacion', required=True)
    journal_id = fields.Many2one('account.journal', string='Diario', domain=[('type', 'in', ['cash', 'bank'])], required=True)
    reference = fields.Char(string='Referencia')
    notes = fields.Text(string='Notas')
    resumen_html = fields.Html(compute='_compute_resumen_html', sanitize=False)
    interest_invoice_id = fields.Many2one('account.move', string='Factura de Intereses')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('recaudo.line') or _('New')
        return super(RecaudoLine, self).create(vals)

 
    @api.depends('concept_ids', 'destinatario', 'partner_id')
    def _compute_resumen_html(self):
        for record in self:
            if record.destinatario == 'propietario':
                record.resumen_html = record._get_propietario_resumen()
            else:
                record.resumen_html = record._get_arrendatario_resumen()

    @api.depends('concept_ids', 'destinatario', 'partner_id')
    def _compute_resumen_html(self):
        for record in self:
            if record.destinatario == 'propietario':
                record.resumen_html = record._get_propietario_resumen()
            else:
                record.resumen_html = record._get_arrendatario_resumen()

    def _get_propietario_resumen(self):
        factura_arrendatario = self.concept_ids.filtered(lambda c: c.invoice_id and c.invoice_id.partner_id != self.partner_id)
        monto_factura = sum(factura_arrendatario.filtered(lambda c: not c.tax_line_id).mapped('amount'))
        impuestos = self._get_grouped_taxes(factura_arrendatario)
        comision = self.concept_ids.filtered(lambda c: c.invoice_id and c.invoice_id.partner_id == self.partner_id)
        novedades = self.concept_ids.filtered(lambda c: c.concept == 'novelty')
        
        total_impuestos = sum(impuestos.values())
        total_novedades = sum(novedades.mapped('amount'))
        subtotal = monto_factura + total_impuestos + sum(comision.mapped('amount'))
        total_pagar = subtotal + total_novedades

        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 400px; margin-left: 0;">
            <h3 style="background-color: #a9a9a9; color: white; padding: 10px; margin: 0;">Totales del Egreso</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 5px;">Monto Factura</td>
                    <td style="text-align: right; padding: 5px;">${monto_factura:,.2f}</td>
                </tr>
                {self._generate_tax_rows(impuestos)}
                <tr>
                    <td style="padding: 5px;">Comisión</td>
                    <td style="text-align: right; padding: 5px;">${sum(comision.mapped('amount')):,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 5px;">Novedades</td>
                    <td style="text-align: right; padding: 5px;">${total_novedades:,.2f}</td>
                </tr>
                <tr style="font-weight: bold; background-color: #f2f2f2;">
                    <td style="padding: 5px;">Total a Pagar</td>
                    <td style="text-align: right; padding: 5px;">${total_pagar:,.2f}</td>
                </tr>
            </table>
        </div>
        """
        return html

    def _get_arrendatario_resumen(self):
        facturas = self.concept_ids.filtered(lambda c: c.invoice_id)
        lineas_agrupadas = defaultdict(float)
        impuestos = self._get_grouped_taxes(facturas)
        novedades = self.concept_ids.filtered(lambda c: c.concept == 'novelty')
        total_novedades = sum(novedades.mapped('amount')) *-1
        
        for factura in facturas:
            for linea in factura.invoice_id.invoice_line_ids:
                lineas_agrupadas[linea.name] += linea.price_subtotal

        for nombre, monto in impuestos.items():
            lineas_agrupadas[nombre] += monto

        monto_total = sum(lineas_agrupadas.values())
        total_pagar = monto_total + total_novedades
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 400px; margin-left: 0;">
            <h3 style="background-color: #a9a9a9; color: white; padding: 10px; margin: 0;">Totales del Recibo</h3>
            <table style="width: 100%; border-collapse: collapse;">
                {self._generate_grouped_invoice_rows(lineas_agrupadas)}
                <tr style="font-weight: bold; background-color: #f2f2f2;">
                    <td style="padding: 5px;">Total Factura</td>
                    <td style="text-align: right; padding: 5px;">${monto_total:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 5px;">Novedades</td>
                    <td style="text-align: right; padding: 5px;">${total_novedades:,.2f}</td>
                </tr>
                <tr style="font-weight: bold; background-color: #f2f2f2;">
                    <td style="padding: 5px;">Total a Cobrar</td>
                    <td style="text-align: right; padding: 5px;">${total_pagar:,.2f}</td>
                </tr>
            </table>
        </div>
        """
        return html

    def _get_grouped_taxes(self, conceptos):
        impuestos = defaultdict(float)
        for record in self:
            if record.destinatario == 'propietario':
                for concepto in conceptos:
                    if concepto.invoice_id:
                        for linea in concepto:
                            if linea.tax_line_id:
                                impuestos[linea.tax_line_id.name] += linea.amount
            else:
                for concepto in conceptos:
                    if concepto.invoice_id:
                        for linea in concepto.invoice_id.line_ids:
                            if linea.tax_line_id:
                                impuestos[linea.tax_line_id.name] += linea.balance *-1
        return impuestos

    def _generate_tax_rows(self, impuestos):
        return ''.join([f"""
            <tr>
                <td style="padding: 5px;">{nombre}</td>
                <td style="text-align: right; padding: 5px;">${monto:,.2f}</td>
            </tr>
        """ for nombre, monto in impuestos.items()])

    def _generate_grouped_invoice_rows(self, lineas_agrupadas):
        return ''.join([f"""
            <tr>
                <td style="padding: 5px;">{nombre}</td>
                <td style="text-align: right; padding: 5px;">${monto:,.2f}</td>
            </tr>
        """ for nombre, monto in lineas_agrupadas.items()])

    @api.depends('contract_id', 'contract_id.partner_id', 'contract_id.partner_is_owner_id', 'contract_id.owners_lines.partner_id')
    def _compute_contract_partner_ids(self):
        for record in self:
            partner_ids = set()
            if record.contract_id:
                if record.contract_id.partner_id:
                    partner_ids.add(record.contract_id.partner_id.id)
                if record.contract_id.partner_is_owner_id:
                    partner_ids.add(record.contract_id.partner_is_owner_id.id)
                for owner_line in record.contract_id.owners_lines:
                    if owner_line.partner_id:
                        partner_ids.add(owner_line.partner_id.id)
            record.contract_partner_ids = [(6, 0, list(partner_ids))]

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        self.partner_id = False 


    @api.depends('destinatario')
    def _compute_move_type(self):
        for line in self:
            if line.destinatario == 'arrendatario':
                line.move_type = 'entry'
            else:
                line.move_type = 'out'

    def load_invoices(self):
        """
        Método optimizado para cargar facturas en Odoo 17 usando búsqueda directa de líneas contables
        """
        for line in self:
            line.concept_ids.unlink()
            base_domain = [
                ('move_id.invoice_date', '>=', line.date_from),
                ('move_id.invoice_date', '<=', line.date_to),
                ('move_id.state', '=', 'posted'),
                ('move_id.line_id.contract_id', '=', line.contract_id.id),
                ('amount_residual', '!=', 0),
            ]

            if line.destinatario == 'arrendatario':
                domain = base_domain + [
                    ('partner_id', '=', line.partner_id.id),
                    ('move_id.move_type', 'in', ['out_invoice', 'in_invoice']),
                    ('account_type', 'in', ['asset_receivable', 'liability_payable']),
                ]
                
                move_lines = self.env['account.move.line'].search(domain)
                
                concept_vals = [{
                    'recaudo_line_id': line.id,
                    'invoice_id': move_line.move_id.id,
                    'line_pay': move_line.id,
                    'concept': 'fixed',
                    'account_id': move_line.account_id.id,
                    'amount': move_line.amount_residual * -1,
                } for move_line in move_lines]
                
                if concept_vals:
                    self.env['recaudo.line.concept'].create(concept_vals)

            else:  # Propietario
                # Líneas de factura del arrendatario (productos e impuestos)
                domain = base_domain + [
                    ('move_id.move_type', 'in', ['out_invoice', 'in_invoice']),
                    ('move_id.destinatario', '=', 'arrendatario'),
                    '|',
                    ('tax_line_id', '!=', False),
                    ('product_id', '!=', False),
                ]
                
                move_lines = self.env['account.move.line'].search(domain)
                
                concept_vals = [{
                    'recaudo_line_id': line.id,
                    'invoice_id': move_line.move_id.id,
                    'line_pay': move_line.id,
                    'concept': 'fixed',
                    'account_id': move_line.account_id.id,
                    'amount': move_line.amount_residual * -1,
                    'tax_line_id': move_line.tax_line_id.id,
                    'product_id': move_line.product_id.id,
                } for move_line in move_lines]

                owner_domain = base_domain + [
                    ('partner_id', '=', line.partner_id.id),
                    ('move_id.move_type', 'in', ['out_invoice', 'in_invoice']),
                    ('account_type', 'in', ['asset_receivable', 'liability_payable']),
                ]
                
                owner_lines = self.env['account.move.line'].search(owner_domain)
                
                concept_vals.extend([{
                    'recaudo_line_id': line.id,
                    'invoice_id': move_line.move_id.id,
                    'line_pay': move_line.id,
                    'concept': 'fixed',
                    'account_id': move_line.account_id.id,
                    'amount': move_line.amount_residual * -1,
                } for move_line in owner_lines])

                if concept_vals:
                    self.env['recaudo.line.concept'].create(concept_vals)

    def load_commissions(self):
        pass

    def load_novedades(self):
        for line in self:
            novedades = self.env['property.contract.novedad'].search([
                ('contract_id', '=', line.contract_id.id),
                ('state', 'in', ['confirmed', 'done']),
                ('destinatario', 'in', [line.destinatario, 'all']),
                '|', 
                ('fecha_inicio', '>=', line.recaudo_id.date_from),
                ('fecha_inicio', '<=', line.recaudo_id.date_to)
            ])
            for novedad in novedades:
                if novedad.tipo == 'unico':
                    amount = novedad.valor_total
                    if novedad.destinatario == 'all':
                        amount *= novedad.percentage_propietario / 100 if line.destinatario == 'propietario' else novedad.percentage_arrendatario / 100
                    line.concept_ids.create({
                        'recaudo_line_id': line.id,
                        'novedad_id': novedad.id,
                        'concept': 'novelty',
                        'account_id': novedad.category_id.account_id.id,
                        'amount': amount * (line.percentage / 100) *-1,
                    })
                else:  # cuotas
                    cuotas = novedad.cuota_ids.filtered(lambda c: c.fecha_vencimiento >= line.recaudo_id.date_from and c.fecha_vencimiento <= line.recaudo_id.date_to)
                    for cuota in cuotas:
                        amount = cuota.valor_propietario if line.destinatario == 'propietario' else cuota.valor_arrendatario
                        line.concept_ids.create({
                            'recaudo_line_id': line.id,
                            'novedad_id': novedad.id,
                            'cuota_id': cuota.id,
                            'concept': 'novelty',
                            'account_id': novedad.category_id.account_id.id,
                            'amount': amount * (line.percentage / 100) *-1,
                        })

    def process_line(self):
        for line in self:
            if not line.move_id:
                move = line._create_accounting_entry()
                line.move_id = move.id
            for concept in line.concept_ids:
                if concept.novedad_id:
                    if concept.novedad_id.tipo == 'unico':
                        concept.novedad_id.state = 'paid'
                    elif concept.cuota_id:
                        concept.cuota_id.estado = 'pagada'
                        if all(cuota.estado == 'pagada' for cuota in concept.novedad_id.cuota_ids):
                            concept.novedad_id.state = 'paid'
            line.is_paid = True

    def _create_accounting_entry(self):
        """
        Método para crear asientos contables con nombre de factura cuando corresponda
        """
        self.ensure_one()
        journal = self.recaudo_id.journal_id
        move_lines = []
        total_amount = sum(self.concept_ids.mapped('amount'))
        bank_line = (0, 0, {
            'account_id': journal.default_account_id.id,
            'partner_id': self.partner_id.id,
            'debit': abs(total_amount) if total_amount < 0 else 0.0,
            'credit': abs(total_amount) if total_amount > 0 else 0.0,
            'name': self.name,
        })
        move_lines.append(bank_line)

        for concept in self.concept_ids:
            if concept.invoice_id and not concept.tax_line_id:
                name = concept.invoice_id.name
            else:
                name = concept.name
                
            line_vals = {
                'account_id': concept.account_id.id,
                'partner_id': self.partner_id.id,
                'debit': abs(concept.amount) if concept.amount > 0 else 0.0,
                'credit': abs(concept.amount) if concept.amount < 0 else 0.0,
                'name': name,
                'line_pay': concept.line_pay.id,
            }
            
            move_lines.append((0, 0, line_vals))

        move = self.env['account.move'].create({
            'journal_id': journal.id,
            'date': self.date,
            'ref': self.name,
            'move_type': 'entry',
            'line_ids': move_lines,
        })
        move.action_post()
        for line in move.line_ids:
            invoice_line = line.line_pay
            if line and invoice_line:
                if line.move_id.state != 'posted':
                    raise UserError("El campo 'line_pay' no está publicado para la línea: %s" % line.name)
                if (invoice_line.account_id == line.account_id and
                    invoice_line.partner_id == line.partner_id):
                    if line.reconciled or invoice_line.reconciled:
                        continue
                    (line + invoice_line).with_context(skip_account_move_synchronization=True).reconcile()            
        return move

    def report_get_propietario_resumen(self):
        factura_arrendatario = self.concept_ids.filtered(lambda c: c.invoice_id and c.invoice_id.partner_id != self.partner_id)
        lineas_agrupadas = defaultdict(float)
        
        for concepto in factura_arrendatario:
            key = concepto.invoice_id.name
            lineas_agrupadas[key] += concepto.amount

        impuestos = self.report_get_grouped_taxes(factura_arrendatario)
        comision = self.concept_ids.filtered(lambda c: c.invoice_id and c.invoice_id.partner_id == self.partner_id)
        novedades = self.concept_ids.filtered(lambda c: c.concept == 'novelty')
        
        monto_factura = sum(lineas_agrupadas.values())
        total_impuestos = sum(impuestos.values())
        total_comision = sum(comision.mapped('amount'))
        total_novedades = sum(novedades.mapped('amount'))
        subtotal = monto_factura + total_impuestos + total_comision
        total_pagar = subtotal + total_novedades

        return {
            'lineas_agrupadas': lineas_agrupadas,
            'impuestos': impuestos,
            'comision': total_comision,
            'novedades': total_novedades,
            'subtotal': subtotal,
            'total_pagar': total_pagar
        }

    def report_get_arrendatario_resumen(self):
        facturas = self.concept_ids.filtered(lambda c: c.invoice_id)
        lineas_agrupadas = defaultdict(float)
        
        for factura in facturas:
            for linea in factura.invoice_id.invoice_line_ids:
                lineas_agrupadas[linea.name] += linea.price_subtotal

        impuestos = self.report_get_grouped_taxes(facturas)
        novedades = self.concept_ids.filtered(lambda c: c.concept == 'novelty')
        
        for nombre, monto in impuestos.items():
            lineas_agrupadas[nombre] += monto

        monto_total = sum(lineas_agrupadas.values())
        total_novedades = sum(novedades.mapped('amount')) * -1
        total_pagar = monto_total + total_novedades

        return {
            'lineas_agrupadas': lineas_agrupadas,
            'novedades': total_novedades,
            'total_pagar': total_pagar
        }

    def report_get_grouped_taxes(self, conceptos):
        impuestos = defaultdict(float)
        for record in self:
            if record.destinatario == 'propietario':
                for concepto in conceptos:
                    if concepto.invoice_id:
                        for linea in concepto:
                            if linea.tax_line_id:
                                impuestos[linea.tax_line_id.name] += linea.amount
            else:
                for concepto in conceptos:
                    if concepto.invoice_id:
                        for linea in concepto.invoice_id.line_ids:
                            if linea.tax_line_id:
                                impuestos[linea.tax_line_id.name] += linea.balance *-1
        return impuestos

    def report_get_grouped_concepts(self):
        grouped_concepts = {}
        for concept in self.concept_ids:
            key = (concept.invoice_id.id if concept.invoice_id else None, concept.name)
            if key not in grouped_concepts:
                grouped_concepts[key] = {
                    'name': concept.name,
                    'amount': 0,
                    'invoice_id': concept.invoice_id,
                }
            grouped_concepts[key]['amount'] += concept.amount
        return sorted(grouped_concepts.values(), key=lambda x: (x['invoice_id'].name if x['invoice_id'] else '', x['name']))

    def report_get_grouped_concepts(self):
        invoiced_concepts = {}
        general_concepts = {}

        for concept in self.concept_ids:
            if concept.invoice_id:
                # Conceptos con factura
                key = concept.invoice_id.id
                if key not in invoiced_concepts:
                    invoiced_concepts[key] = {
                        'name': 'Factura' +  concept.invoice_id.name,
                        'amount': 0,
                        'invoice_id': concept.invoice_id,
                        'concept_names': []  
                    }
                invoiced_concepts[key]['amount'] += concept.amount
                invoiced_concepts[key]['concept_names'].append(concept.name)
            else:
                # Conceptos generales sin factura
                key = concept.name
                if key not in general_concepts:
                    general_concepts[key] = {
                        'name': concept.name,
                        'amount': 0
                    }
                general_concepts[key]['amount'] += concept.amount

        # Ordenamos los conceptos con factura por nombre de factura
        sorted_invoiced = sorted(invoiced_concepts.values(), key=lambda x: x['name'])
        
        # Ordenamos los conceptos generales por nombre
        sorted_general = sorted(general_concepts.values(), key=lambda x: x['name'])

        return {
            'invoiced': sorted_invoiced,
            'general': sorted_general
        }
class RecaudoLineConcept(models.Model):
    _name = 'recaudo.line.concept'
    _description = 'Concepto de Línea de Recaudo'

    recaudo_line_id = fields.Many2one('recaudo.line', string='Línea de Recaudo')
    invoice_id = fields.Many2one('account.move', string='Factura')
    line_pay = fields.Many2one('account.move.line', string='line Invoice')
    novedad_id = fields.Many2one('property.contract.novedad', string='Novedad')
    cuota_id = fields.Many2one('property.contract.novedad.cuota', string='Cuota de Novedad')
    cuota_owner_id = fields.Many2one('property.contract.novedad.cuota.owner', string='Cuota de Novedad Owner')
    concept = fields.Selection([('fixed', 'Fijo'), ('novelty', 'Novedad'),('other','Otros')], string='Concepto')
    account_id = fields.Many2one('account.account', string='Cuenta')
    amount = fields.Float(string='Monto')
    product_id = fields.Many2one('product.product', string='Producto')
    name = fields.Char(string='Descripción', compute='_compute_name', store=True, readonly=False)
    tax_line_id = fields.Many2one(
        comodel_name='account.tax',
        string='Impuesto',
        ondelete='restrict',
        help="Indicates that this journal item is a tax line")
    tax_group_id = fields.Many2one(  # used in the widget tax-group-custom-field
        string='Originator tax group',
        related='tax_line_id.tax_group_id', store=True, precompute=True,
    )
    days_overdue = fields.Integer(string='Días de vencimiento', compute='_compute_days_overdue', store=True)
    nota_debito_actual = fields.Text(string='Nota de débito actual', compute='_compute_nota_debito_actual')
    day_inte = fields.Many2one('account.debit.term.line', string='Intereses', store=True, readonly=False)
    amount_intereses = fields.Float(string='Monto Intereses', compute='_compute_amount_intereses', store=True)

    @api.depends('invoice_id.invoice_date_due')
    def _compute_days_overdue(self):
        today = date.today()
        for record in self:
            if record.invoice_id and record.invoice_id.invoice_date_due:
                due_date = fields.Date.from_string(record.invoice_id.invoice_date_due)
                record.days_overdue = (today - due_date).days if today > due_date else 0
            else:
                record.days_overdue = 0

    @api.depends('days_overdue', 'contract_id.debit_line_ids')
    def _compute_day_inte(self):
        for record in self:
            # if record.days_overdue > 0 and record.contract_id:
            #     applicable_lines = record.contract_id.debit_line_ids.filtered(
            #         lambda l: l.nb_days <= record.days_overdue
            #     ).sorted(key=lambda l: l.nb_days, reverse=True)
            #     if applicable_lines:
            #         record.day_inte = applicable_lines[0]
            #     else:
            #         record.day_inte = False
            # else:
            record.day_inte = False

    @api.depends('day_inte', 'amount')
    def _compute_amount_intereses(self):
        for record in self:
            # if record.day_inte and record.amount:
            #     if record.day_inte.value == 'percent':
            #         record.amount_intereses = record.amount * (record.day_inte.value_amount / 100)
            #     else:
            #         record.amount_intereses = record.day_inte.value_amount
            # else:
            record.amount_intereses = 0

    @api.depends('amount_intereses', 'amount')
    def _compute_nota_debito_actual(self):
        for record in self:
            base_amount = record.amount
            interest_amount = record.amount_intereses
            total_amount = base_amount + interest_amount
            record.nota_debito_actual = f"""
            Monto base: ${base_amount:.2f}
            Intereses: ${interest_amount:.2f}
            Total: ${total_amount:.2f}
            """

    @api.depends('invoice_id.invoice_date_due')
    def _compute_day_inte(self):
        for record in self:
            if record.invoice_id and record.invoice_id.invoice_date_due:
                days_past_due = (fields.Date.today() - record.invoice_id.invoice_date_due).days
                record.day_inte = days_past_due if days_past_due > 0 else 0
            else:
                record.day_inte = 0

    @api.depends('invoice_id', 'novedad_id', 'cuota_id', 'concept')
    def _compute_name(self):
        for record in self:
            if record.invoice_id and not record.tax_line_id and not record.product_id and record.recaudo_line_id.destinatario == 'arrendatario':
                record.name = f"Contracto {record.recaudo_line_id.contract_id.name}:  Cobro de Canon por arrendamiento periodo {record.invoice_id.line_id.period_start} - {record.invoice_id.line_id.period_end} de  FV {record.invoice_id.name} Direccion: {record.recaudo_line_id.contract_id.address}"
            elif record.invoice_id and not record.tax_line_id and not record.product_id and record.recaudo_line_id.destinatario == 'propietario':
                record.name = f"Contracto {record.recaudo_line_id.contract_id.name}: Cobro de Comision por arrendamiento periodo {record.invoice_id.line_id.period_start} - {record.invoice_id.line_id.period_end} de FV {record.invoice_id.name} Direccion: {record.recaudo_line_id.contract_id.address}"
            elif record.invoice_id and record.tax_line_id:
                record.name = f"DEV {record.tax_line_id.name}"
            elif record.invoice_id and record.product_id:
                record.name = f"Contracto {record.recaudo_line_id.contract_id.name}: DEV de Canon por arrendamiento {record.invoice_id.line_id.period_start} - {record.invoice_id.line_id.period_end} propiedad {record.product_id.name} de FV {record.invoice_id.name} Direccion: {record.recaudo_line_id.contract_id.address}"
            elif record.novedad_id:
                if record.cuota_id:
                    record.name = f"Novedad {record.novedad_id.category_id.name} - Cuota {record.cuota_id.numero_cuota}"
                else:
                    record.name = f"Novedad {record.novedad_id.name}"
            else:
                record.name = f"Concepto {record.concept}"

class RecaudoContractWizard(models.TransientModel):
    _name = 'recaudo.contract.wizard'
    _description = 'Wizard para seleccionar contratos'

    recaudo_id = fields.Many2one('recaudo.recaudo', string='Recaudo')
    contract_ids = fields.Many2many('property.contract', string='Contratos')

    def action_add_contracts(self):
        self.recaudo_id.write({'contract_ids': [(6, 0, self.contract_ids.ids)]})
        self.recaudo_id.generate_recaudo_lines()
        for line in self.recaudo_id.line_ids:
            line.load_invoices()
            line.load_commissions()
        return {'type': 'ir.actions.act_window_close'}

class GenerateInterestInvoiceWizard(models.TransientModel):
    _name = 'generate.interest.invoice.wizard'
    _description = 'Generar Factura de Intereses'

    journal_id = fields.Many2one('account.journal', string='Diario', required=True, domain=[('type', '=', 'sale')])
    date = fields.Date(string='Fecha', default=fields.Date.context_today, required=True)
    amount = fields.Float(string='Importe', required=True)
    recaudo_line_ids = fields.Many2many('recaudo.line', string='Líneas de Recaudo', domain=[('destinatario', '=', 'arrendatario')])
    tax_ids = fields.Many2many('account.tax', string='Impuestos', domain=[('type_tax_use', '=', 'sale')])

    @api.onchange('recaudo_line_ids')
    def _onchange_recaudo_line_ids(self):
        total_interest = sum(self.recaudo_line_ids.concept_ids.filtered(lambda c: c.day_inte).mapped('amount_intereses'))
        self.amount = abs(total_interest)

    def action_generate_invoice(self):
        self.ensure_one()
        if not self.recaudo_line_ids:
            raise UserError('Debe seleccionar al menos una línea de recaudo.')
        lines = self.env['recaudo.line'].browse(self.env.context.get('active_id'))
        product = self.env['product.product'].search([('default_code', '=', 'INT')], limit=1)
        if not product:
            raise UserError('No se encontró el producto de intereses con código INT.')

        tenant = self.recaudo_line_ids[0].partner_id
        if not all(line.partner_id == tenant for line in self.recaudo_line_ids):
            raise UserError('Todas las líneas de recaudo deben pertenecer al mismo arrendatario.')

        invoice_vals = {
            'partner_id': tenant.id,
            'move_type': 'out_invoice',
            'journal_id': self.journal_id.id,
            'invoice_date': self.date,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'name': 'Intereses',
                'quantity': 1,
                'price_unit': self.amount,
                'tax_ids': [(6, 0, self.tax_ids.ids)],
            })],
        }
        invoice = self.env['account.move'].create(invoice_vals)
        payment_term_lines = invoice.line_ids.filtered(lambda l: l.display_type == 'payment_term')
        # Crear una nueva línea de concepto en las líneas de recaudo
       
        for invoice_line in payment_term_lines:
            for recaudo_line in self.recaudo_line_ids:
                self.env['recaudo.line.concept'].create({
                    'recaudo_line_id': recaudo_line.id,
                    'invoice_id': invoice.id,
                    'line_pay': invoice_line.id,
                    'concept': 'fixed',
                    'account_id': invoice_line.account_id.id,
                    'amount': invoice_line.amount_residual *-1,
                })

        return {
            'name': 'Factura de Intereses',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'type': 'ir.actions.act_window',
        }
# -*- coding: utf-8 -*-
# MÉTODOS MEJORADOS PARA account_payment.py
# Reemplazar desde línea 2183 hasta línea 2605 aproximadamente

def action_post(self):
	"""Publicación con manejo completo de líneas personalizadas y doble moneda"""
	for payment in self:
		# Validaciones previas
		payment._validate_before_post()

		# Actualizar tasa de cambio si es necesario
		if payment.currency_id != payment.company_currency_id:
			payment._update_exchange_rates()

		# Procesar según el tipo
		if payment.payment_line_ids and not payment.paired_internal_transfer_payment_id:
			payment._post_with_custom_lines()
		else:
			super(AccountPayment, payment).action_post()

		# Post-procesamiento
		payment._post_process_after_posting()

	return True

# === VALIDACIONES ===
def _validate_before_post(self):
	"""Validaciones antes de publicar"""
	for payment in self:
		if payment.advance and payment.advance_type_id:
			if payment.destination_account_id != payment.advance_type_id.account_id:
				payment.destination_account_id = payment.advance_type_id.account_id

		if payment.advance and not payment.code_advance:
			payment._generate_advance_number()

		# Validación de cuentas bancarias
		if (
			payment.require_partner_bank_account
			and payment.partner_bank_id
			and not payment.partner_bank_id.allow_out_payment
			and payment.payment_type == 'outbound'
		):
			raise UserError(_(
				"To record payments with %(method_name)s, the recipient bank account must be manually validated. "
				"You should go on the partner bank account of %(partner)s in order to validate it.",
				method_name=payment.payment_method_line_id.name,
				partner=payment.partner_id.display_name,
			))

# === ACTUALIZACIÓN DE TASAS DE CAMBIO ===
def _update_exchange_rates(self):
	"""Actualiza tasas de cambio del día"""
	self.ensure_one()
	if not self.manual_currency_rate_active:
		rate = self.env['res.currency']._get_conversion_rate(
			self.company_currency_id,
			self.currency_id,
			self.company_id,
			self.date or fields.Date.today()
		)
		self.current_exchange_rate = 1 / rate if rate else 1
		self.manual_currency_rate = rate

# === PROCESAMIENTO CON LÍNEAS PERSONALIZADAS ===
def _post_with_custom_lines(self):
	"""Procesa pago con líneas personalizadas y doble moneda"""
	self.ensure_one()

	# Actualizar líneas con tasas de cambio
	self._update_payment_lines_rates()

	# Crear o actualizar asiento
	if self.move_id:
		self._update_existing_move()
	else:
		self._create_new_move()

	# Publicar y reconciliar
	if self.move_id:
		self.move_id.action_post()
		self._reconcile_with_exchange_control()

	# Actualizar estado
	self._update_payment_state()

def _update_payment_lines_rates(self):
	"""Actualiza tasas en líneas de pago"""
	for line in self.payment_line_ids:
		if self.currency_id != self.company_currency_id:
			# Calcular montos en moneda local
			line._compute_debit_credit_balance()

			# Marcar si necesita diferencia cambiaria
			if line.move_line_id and hasattr(self, 'generate_exchange_diff') and self.generate_exchange_diff:
				# Solo marcar como true si hay diferencia significativa
				if line.move_line_id.amount_currency and line.move_line_id.balance:
					original_rate = abs(line.move_line_id.balance / line.move_line_id.amount_currency)
					current_rate = self.current_exchange_rate if self.manual_currency_rate_active else self._get_current_rate()
					if hasattr(line, 'needs_rate_adjustment'):
						line.needs_rate_adjustment = not self.company_currency_id.is_zero(
							line.payment_amount * (current_rate - original_rate)
						)

def _create_new_move(self):
	"""Crea nuevo asiento con todas las líneas"""
	self.ensure_one()

	move_vals = {
		'move_type': 'entry',
		'date': self.date,
		'ref': self.memo,
		'journal_id': self.journal_id.id,
		'company_id': self.company_id.id,
		'partner_id': self.partner_id.id,
		'currency_id': self.currency_id.id if self.currency_id != self.company_currency_id else self.company_currency_id.id,
		'line_ids': self._prepare_all_move_lines(),
	}

	# Agregar campos opcionales si existen
	if hasattr(self, 'partner_bank_id'):
		move_vals['partner_bank_id'] = self.partner_bank_id.id
	if hasattr(self, 'origin_payment_id'):
		move_vals['origin_payment_id'] = self.id

	self.move_id = self.env['account.move'].create(move_vals)

def _update_existing_move(self):
	"""Actualiza asiento existente"""
	self.ensure_one()

	if self.move_id.state == 'posted':
		self.move_id.button_cancel()

	self.move_id.line_ids.unlink()
	self.move_id.write({
		'line_ids': self._prepare_all_move_lines()
	})

# === PREPARACIÓN DE LÍNEAS ===
def _prepare_all_move_lines(self):
	"""Prepara todas las líneas del asiento según el modo"""
	if hasattr(self, 'payment_line_mode') and self.payment_line_mode == 'consolidated':
		return self._prepare_consolidated_lines()
	return self._prepare_detailed_lines()

def _prepare_detailed_lines(self):
	"""Modo detallado con manejo completo de doble moneda"""
	lines = []
	total_balance_company = 0
	total_amount_currency = 0

	# 1. Procesar líneas principales
	for detail in self.payment_line_ids.filtered(lambda l: not l.auto_tax_line and not l.is_counterpart):
		# Línea principal
		line_vals = self._prepare_payment_line_vals(detail)
		lines.append((0, 0, line_vals))
		total_balance_company += line_vals['debit'] - line_vals['credit']
		total_amount_currency += line_vals.get('amount_currency', 0)

		# Diferencia cambiaria si aplica
		if self._should_create_exchange_diff(detail):
			diff_vals = self._prepare_exchange_diff_line_vals(detail)
			if diff_vals:
				lines.append((0, 0, diff_vals))
				total_balance_company += diff_vals['debit'] - diff_vals['credit']

	# 2. Procesar líneas de impuestos
	for tax_line in self.payment_line_ids.filtered('auto_tax_line'):
		tax_vals = self._prepare_tax_line_vals(tax_line)
		lines.append((0, 0, tax_vals))
		total_balance_company += tax_vals['debit'] - tax_vals['credit']
		total_amount_currency += tax_vals.get('amount_currency', 0)

	# 3. Línea de liquidez (banco/caja)
	liquidity_vals = self._prepare_liquidity_line_vals(total_balance_company, total_amount_currency)
	lines.insert(0, (0, 0, liquidity_vals))

	return lines

def _prepare_consolidated_lines(self):
	"""Modo consolidado con agrupación por cuenta y partner"""
	lines = []
	consolidated = {}
	total_balance_company = 0
	total_amount_currency = 0

	# Agrupar líneas por cuenta y partner
	for detail in self.payment_line_ids.filtered(lambda l: not l.auto_tax_line):
		key = (detail.partner_id.id if detail.partner_id else False, detail.account_id.id)

		if key not in consolidated:
			consolidated[key] = {
				'partner_id': detail.partner_id.id if detail.partner_id else self.partner_id.id,
				'account_id': detail.account_id.id,
				'debit': 0,
				'credit': 0,
				'amount_currency': 0,
				'exchange_diff': 0,
				'details': [],
				'analytic_distribution': detail.analytic_distribution if hasattr(detail, 'analytic_distribution') else {},
			}

		# Convertir a moneda local
		amount_company = self._convert_to_company_currency(detail.payment_amount, detail)

		if self.payment_type == 'outbound':
			consolidated[key]['debit'] += abs(amount_company)
		else:
			consolidated[key]['credit'] += abs(amount_company)

		consolidated[key]['amount_currency'] += detail.payment_amount
		consolidated[key]['details'].append(detail)

		# Acumular diferencia cambiaria
		if self._should_create_exchange_diff(detail):
			consolidated[key]['exchange_diff'] += self._calculate_exchange_difference(detail)

	# Crear líneas consolidadas
	for key, vals in consolidated.items():
		# Línea principal consolidada
		line_vals = {
			'name': self._get_consolidated_line_name(vals['details']),
			'partner_id': vals['partner_id'],
			'account_id': vals['account_id'],
			'debit': vals['debit'],
			'credit': vals['credit'],
			'amount_currency': vals['amount_currency'] if self.currency_id != self.company_currency_id else 0,
			'currency_id': self.currency_id.id if self.currency_id != self.company_currency_id else self.company_currency_id.id,
			'analytic_distribution': vals['analytic_distribution'],
		}

		# Agregar referencia a detalles si el modelo lo soporta
		if hasattr(self.env['account.move.line'], 'consolidated_detail_ids'):
			line_vals['consolidated_detail_ids'] = [(6, 0, [d.id for d in vals['details']])]

		lines.append((0, 0, line_vals))
		total_balance_company += vals['debit'] - vals['credit']
		total_amount_currency += vals['amount_currency']

		# Diferencia cambiaria consolidada
		if vals['exchange_diff'] and not self.company_currency_id.is_zero(vals['exchange_diff']):
			diff_vals = {
				'name': f"Diferencia cambiaria consolidada",
				'account_id': self._get_exchange_diff_account(vals['exchange_diff']),
				'partner_id': vals['partner_id'],
				'debit': abs(vals['exchange_diff']) if vals['exchange_diff'] > 0 else 0,
				'credit': abs(vals['exchange_diff']) if vals['exchange_diff'] < 0 else 0,
				'currency_id': self.company_currency_id.id,
			}
			lines.append((0, 0, diff_vals))
			total_balance_company += diff_vals['debit'] - diff_vals['credit']

	# Línea de liquidez
	liquidity_vals = self._prepare_liquidity_line_vals(total_balance_company, total_amount_currency)
	lines.insert(0, (0, 0, liquidity_vals))

	return lines

# === PREPARACIÓN DE LÍNEAS ESPECÍFICAS ===
def _prepare_payment_line_vals(self, detail):
	"""Prepara valores de línea de pago con doble moneda"""
	amount_company = self._convert_to_company_currency(detail.payment_amount, detail)

	vals = {
		'name': detail.name or self.memo or '/',
		'account_id': detail.account_id.id,
		'partner_id': detail.partner_id.id if detail.partner_id else self.partner_id.id,
		'payment_detail_id': detail.id,  # Referencia para reconciliación
	}

	# Agregar distribución analítica si existe
	if hasattr(detail, 'analytic_distribution') and detail.analytic_distribution:
		vals['analytic_distribution'] = detail.analytic_distribution

	# Determinar débito/crédito según tipo de pago
	if self.payment_type == 'outbound':
		vals['debit'] = abs(amount_company)
		vals['credit'] = 0
	else:
		vals['debit'] = 0
		vals['credit'] = abs(amount_company)

	# Moneda extranjera
	if self.currency_id != self.company_currency_id:
		vals['amount_currency'] = detail.payment_amount if self.payment_type == 'inbound' else -detail.payment_amount
		vals['currency_id'] = self.currency_id.id
	else:
		vals['currency_id'] = self.company_currency_id.id
		vals['amount_currency'] = 0

	# Impuestos si no hay líneas automáticas
	if detail.tax_ids and not detail.reverse_tax_ids:
		vals['tax_ids'] = [(6, 0, detail.tax_ids.ids)]
		if hasattr(detail, 'tax_tag_ids'):
			vals['tax_tag_ids'] = [(6, 0, detail.tax_tag_ids.ids)]
		if hasattr(detail, 'tax_base_amount'):
			vals['tax_base_amount'] = detail.tax_base_amount

	return vals

def _prepare_exchange_diff_line_vals(self, detail):
	"""Prepara línea de diferencia cambiaria"""
	diff_amount = self._calculate_exchange_difference(detail)

	if self.company_currency_id.is_zero(diff_amount):
		return False

	return {
		'name': f"Dif. cambiaria - {detail.invoice_id.name if detail.invoice_id else detail.name}",
		'account_id': self._get_exchange_diff_account(diff_amount),
		'partner_id': detail.partner_id.id if detail.partner_id else self.partner_id.id,
		'debit': abs(diff_amount) if diff_amount > 0 else 0,
		'credit': abs(diff_amount) if diff_amount < 0 else 0,
		'currency_id': self.company_currency_id.id,
		'is_exchange_diff': True if hasattr(self.env['account.move.line'], 'is_exchange_diff') else False,
	}

def _prepare_tax_line_vals(self, tax_line):
	"""Prepara línea de impuesto"""
	amount_company = self._convert_to_company_currency(tax_line.payment_amount, tax_line)

	vals = {
		'name': tax_line.name or 'Impuesto',
		'account_id': tax_line.account_id.id,
		'partner_id': tax_line.partner_id.id if tax_line.partner_id else self.partner_id.id,
		'debit': abs(amount_company) if self.payment_type == 'outbound' else 0,
		'credit': abs(amount_company) if self.payment_type == 'inbound' else 0,
		'currency_id': self.currency_id.id if self.currency_id != self.company_currency_id else self.company_currency_id.id,
		'amount_currency': tax_line.payment_amount if self.currency_id != self.company_currency_id else 0,
	}

	# Agregar información de impuesto
	if hasattr(tax_line, 'tax_line_id2') and tax_line.tax_line_id2:
		vals['tax_line_id'] = tax_line.tax_line_id2.id
	if hasattr(tax_line, 'tax_base_amount'):
		vals['tax_base_amount'] = tax_line.tax_base_amount
	if hasattr(tax_line, 'tax_tag_ids'):
		vals['tax_tag_ids'] = [(6, 0, tax_line.tax_tag_ids.ids)]

	return vals

def _prepare_liquidity_line_vals(self, balance_company, amount_currency):
	"""Prepara línea de liquidez (banco/caja)"""
	return {
		'name': self.memo or '/',
		'account_id': self.outstanding_account_id.id,
		'partner_id': self.partner_id.id,
		'debit': abs(balance_company) if balance_company < 0 else 0,
		'credit': abs(balance_company) if balance_company > 0 else 0,
		'amount_currency': -amount_currency if self.currency_id != self.company_currency_id else 0,
		'currency_id': self.currency_id.id if self.currency_id != self.company_currency_id else self.company_currency_id.id,
	}

# === CÁLCULOS DE MONEDA ===
def _convert_to_company_currency(self, amount, detail=None):
	"""Convierte monto a moneda de la compañía"""
	if self.currency_id == self.company_currency_id:
		return amount

	# Usar tasa manual si está activa
	if self.manual_currency_rate_active and self.current_exchange_rate:
		return amount * self.current_exchange_rate

	# Usar tasa del día
	return self.currency_id._convert(
		amount,
		self.company_currency_id,
		self.company_id,
		self.date or fields.Date.today()
	)

def _calculate_exchange_difference(self, detail):
	"""Calcula diferencia cambiaria para una línea"""
	if not detail.move_line_id or self.currency_id == self.company_currency_id:
		return 0.0

	# Obtener tasa original del documento
	if detail.move_line_id.amount_currency and detail.move_line_id.balance:
		original_rate = abs(detail.move_line_id.balance / detail.move_line_id.amount_currency)
	else:
		return 0.0

	# Tasa actual
	current_rate = self.current_exchange_rate if self.manual_currency_rate_active else self._get_current_rate()

	# Diferencia = monto * (tasa_actual - tasa_original)
	diff = detail.payment_amount * (current_rate - original_rate)

	# Invertir signo según tipo de pago
	if self.payment_type == 'outbound':
		diff = -diff

	return diff

def _get_current_rate(self):
	"""Obtiene tasa de cambio del día"""
	if self.currency_id == self.company_currency_id:
		return 1.0

	rate = self.env['res.currency']._get_conversion_rate(
		self.company_currency_id,
		self.currency_id,
		self.company_id,
		self.date or fields.Date.today()
	)
	return 1 / rate if rate else 1.0

def _should_create_exchange_diff(self, detail):
	"""Determina si crear diferencia cambiaria"""
	return (
		hasattr(self, 'generate_exchange_diff') and
		self.generate_exchange_diff and
		hasattr(self, 'exchange_diff_type') and
		self.exchange_diff_type == 'custom' and
		detail.move_line_id and
		self.currency_id != self.company_currency_id and
		hasattr(detail, 'needs_rate_adjustment') and
		detail.needs_rate_adjustment
	)

def _get_exchange_diff_account(self, diff_amount):
	"""Obtiene cuenta de diferencia cambiaria"""
	if hasattr(self, 'writeoff_account_id') and self.writeoff_account_id:
		return self.writeoff_account_id.id

	company = self.company_id
	if diff_amount > 0:
		return company.expense_currency_exchange_account_id.id
	else:
		return company.income_currency_exchange_account_id.id

# === RECONCILIACIÓN ===
def _reconcile_with_exchange_control(self):
	"""Reconcilia con control de diferencias cambiarias"""
	if not self.move_id or self.move_id.state != 'posted':
		return

	if hasattr(self, 'payment_line_mode') and self.payment_line_mode == 'detailed':
		self._reconcile_detailed_lines()
	else:
		self._reconcile_consolidated_lines()

def _reconcile_detailed_lines(self):
	"""Reconcilia en modo detallado"""
	for detail in self.payment_line_ids.filtered(lambda l: l.move_line_id and not l.auto_tax_line):
		# Buscar línea correspondiente en el asiento
		payment_line = self.move_id.line_ids.filtered(
			lambda ml: hasattr(ml, 'payment_detail_id') and
					  ml.payment_detail_id == detail.id and
					  ml.account_id == detail.account_id
		)

		if not payment_line:
			# Fallback: buscar por cuenta y partner
			payment_line = self.move_id.line_ids.filtered(
				lambda ml: ml.account_id == detail.account_id and
						  ml.partner_id == (detail.partner_id or self.partner_id) and
						  ml.account_id.account_type in ('asset_receivable', 'liability_payable')
			)

		if payment_line and detail.move_line_id:
			try:
				lines_to_reconcile = payment_line | detail.move_line_id

				# Reconciliar sin crear diferencia automática
				if hasattr(self, 'exchange_diff_type') and self.exchange_diff_type == 'custom':
					lines_to_reconcile.with_context(
						no_exchange_difference=True,
						skip_account_move_synchronization=True
					).reconcile()
				else:
					lines_to_reconcile.reconcile()

			except Exception as e:
				_logger.warning(f"Error al reconciliar línea {detail.id}: {str(e)}")

def _reconcile_consolidated_lines(self):
	"""Reconcilia en modo consolidado"""
	# Esta función requiere que el modelo tenga el campo consolidated_detail_ids
	# Si no existe, usar reconciliación estándar
	for line in self.move_id.line_ids.filtered(lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable')):
		# Buscar líneas de pago que correspondan
		for detail in self.payment_line_ids.filtered(lambda d: d.move_line_id and d.account_id == line.account_id):
			if detail.move_line_id:
				try:
					(line | detail.move_line_id).with_context(
						no_exchange_difference=True
					).reconcile()
				except Exception as e:
					_logger.warning(f"Error al reconciliar consolidado {detail.id}: {str(e)}")

# === MÉTODOS AUXILIARES ===
def _update_payment_state(self):
	"""Actualiza estado del pago"""
	self.ensure_one()
	if self.outstanding_account_id.account_type == 'asset_cash':
		self.state = 'paid'
	else:
		self.state = 'in_process'

def _post_process_after_posting(self):
	"""Post-procesamiento después de publicar"""
	for payment in self:
		# Actualizar solicitudes de anticipo si existen
		if hasattr(payment, 'advance_request_id') and payment.advance_request_id:
			if hasattr(payment.advance_request_id, 'state') and payment.advance_request_id.state == 'approved':
				payment.advance_request_id.write({
					'state': 'paid',
					'date_paid': fields.Datetime.now()
				})

		# Generar números de tesorería
		if hasattr(payment, 'use_treasury_numbering') and payment.use_treasury_numbering:
			if hasattr(payment, 'treasury_receipt_number') and not payment.treasury_receipt_number:
				payment._generate_treasury_numbers()

		# Procesar cruces de anticipos si corresponde
		if hasattr(payment, 'is_document_cross') and payment.is_document_cross and payment.advance:
			payment._process_advance_reconciliation()

def _get_consolidated_line_name(self, details):
	"""Genera nombre para línea consolidada"""
	count = len(details)
	if count == 1:
		return details[0].name or self.memo
	return f"Pago consolidado - {count} documentos"

def _generate_advance_number(self):
	"""Genera número de anticipo"""
	self.ensure_one()
	if self.advance_type_id:
		self.code_advance = self.advance_type_id.get_next_sequence(date=self.date)
	else:
		mapping = {
			'customer': 'account.payment.advance.customer',
			'supplier': 'account.payment.advance.supplier',
			'employee': 'account.payment.advance.employee',
		}
		sequence_code = mapping.get(self.partner_type)
		if sequence_code:
			self.code_advance = self.env['ir.sequence'].with_context(
				ir_sequence_date=self.date
			).next_by_code(sequence_code)

	if not self.code_advance and self.advance:
		raise UserError(_("No se pudo generar el número de anticipo. Configure una secuencia."))
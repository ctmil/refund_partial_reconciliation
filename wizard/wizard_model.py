from openerp import models, fields, api, _
from openerp.exceptions import except_orm
from openerp.osv import osv
import urllib2, httplib, urlparse, gzip, requests, json
from StringIO import StringIO
import openerp.addons.decimal_precision as dp
from datetime import date
import logging
import ast
from openerp import exceptions
from openerp.exceptions import ValidationError

#Get the logger
_logger = logging.getLogger(__name__)

class refund_add_invoice(models.TransientModel):
        _name = 'refund.add.invoice'

	inv_type = fields.Char(string='Type')
	name = fields.Char(string='Name')
	journal_id = fields.Many2one('account.journal',string='Diario',domain=[('type','=','general')],required=True)
	lines = fields.One2many(comodel_name='refund.add.invoice.line',inverse_name='header_id')
	refund_id = fields.Many2one('account.invoice')
	amount = fields.Float(string='Monto')

        @api.multi
        def confirm_line(self):
		total_amount  = 0
		for line in self.lines:
			if line.amount > line.residual:
				raise exceptions.ValidationError('Monto asignado supera saldo de la factura')
			total_amount += line.amount
		context = self.env.context
		refund = self.env['account.invoice'].browse(context['active_id'])
		if total_amount > refund.residual:
			raise exceptions.ValidationError('No coinciden los totales con el total de la nota de credito')
	
		refund_move_ids = []
		if refund.move_id:
			for move_line in refund.move_id.line_id:
				if self.inv_type == 'out_invoice':
					if move_line.credit > 0:
						refund_move_id = move_line.id
				else:
					if move_line.debit > 0:
						refund_move_id = move_line.id

		if self.inv_type == 'out_invoice':
			credit_account = refund.partner_id.property_account_receivable
		else:
			debit_account = refund.partner_id.property_account_payable
		if refund.invoice_line:
			line = refund.invoice_line[0]
			if self.inv_type == 'out_invoice':
				debit_account = line.account_id
			else:
				credit_account = line.account_id
		else:
                        raise exceptions.ValidationError('No puede determinar cuenta contable')
		if not refund:
                        raise exceptions.ValidationError('No hay NC disponible')
		vals_move = {
			'journal_id': self.journal_id.id,
			'date': str(date.today()),
			'company_id': refund.company_id.id,
			'partner_id': refund.partner_id.id,
			}
		move_id = self.env['account.move'].create(vals_move)
		if not move_id:
                        raise exceptions.ValidationError('No pudo crearse la cabecera del asiento contable')
		rec_ids = []
		for line in self.lines:
			if line.amount > 0:	
				invoice = line.invoice_id
				if invoice.move_id:
					move = invoice.move_id
					for invoice_line in move.line_id:
						if self.inv_type == 'out_invoice':
							if invoice_line.debit > 0:
								invoice_line_id = invoice_line.id
						else:
							if invoice_line.credit > 0:
								invoice_line_id = invoice_line.id
				if self.inv_type == 'out_invoice':
					vals_debit = {
						'name': 'FAC ' + invoice.internal_number,
						'ref': 'NC ' + refund.internal_number,
						'move_id': move_id.id,
						'partner_id': refund.partner_id.id,
						'account_id': credit_account.id,
						'debit': line.amount,
						'credit': 0
						}
				else:
					vals_debit = {
						'name': 'FAC ' + invoice.internal_number,
						'ref': 'NC ' + refund.internal_number,
						'move_id': move_id.id,
						'partner_id': refund.partner_id.id,
						'account_id': debit_account.id,
						'credit': line.amount,
						'debit': 0
						}
				debit_move_id = self.env['account.move.line'].create(vals_debit)
				if self.inv_type == 'out_invoice':
					vals_credit = {
						'name': 'NC ' + refund.number or refund.internal_number,
						'ref': 'NC' ,
						'move_id': move_id.id,
						'partner_id': refund.partner_id.id,
						'account_id': credit_account.id,
						'debit': 0,
						'credit': line.amount
						}
				else:
					vals_credit = {
						'name': 'NC ' + refund.supplier_invoice_number or refund.number,
						'ref': 'NC' ,
						'move_id': move_id.id,
						'partner_id': refund.partner_id.id,
						'account_id': debit_account.id,
						'credit': 0,
						'debit': line.amount
						}
				credit_move_id = self.env['account.move.line'].create(vals_credit)
				rec_ids.append([invoice_line_id,credit_move_id.id])	
				refund_move_ids.append([refund_move_id,debit_move_id.id])
		if move_id and debit_move_id and credit_move_id:
			move_id.post()
		for record_ids in rec_ids:
			#reconcile = self.env['account.move.line'].reconcile_partial(self.env.cr, self.env.uid, record_ids, \
			#	type='auto', context=None, writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False)
			reconcile = self.env['account.move.line'].partial_reconcile(record_ids)
		for record_ids in refund_move_ids:
			reconcile = self.env['account.move.line'].partial_reconcile(record_ids)
			
                return None

class refund_add_invoice_line(models.TransientModel):
	_name = 'refund.add.invoice.line'

	header_id = fields.Many2one('refund.add.invoice')
        invoice_id = fields.Many2one('account.invoice')
        supplier_invoice_number = fields.Char(string='Nro Factura Proveedor',related='invoice_id.supplier_invoice_number')
	date = fields.Date(string='Fecha')
	original_amount = fields.Float('Monto Factura')
	residual = fields.Float('Saldo')
        amount = fields.Float(string='Monto')

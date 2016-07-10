from openerp import models, fields, api, _
from openerp.exceptions import except_orm
from openerp.osv import osv
import urllib2, httplib, urlparse, gzip, requests, json
from StringIO import StringIO
import openerp.addons.decimal_precision as dp
from datetime import date
import logging
import ast
from openerp.exceptions import ValidationError

#Get the logger
_logger = logging.getLogger(__name__)

class refund_add_invoice(models.TransientModel):
        _name = 'refund.add.invoice'

	name = fields.Char(string='Name')
	journal_id = fields.Many2one('account.journal',string='Diario',domain=[('type','=','general')],required=True)
	lines = fields.One2many(comodel_name='refund.add.invoice.line',inverse_name='header_id')
	refund_id = fields.Many2one('account.invoice')

        @api.multi
        def confirm_line(self):
		context = self.env.context
		refund = self.env['account.invoice'].browse(context['active_id'])
		credit_account = refund.partner_id.property_account_receivable
		if refund.invoice_line:
			line = refund.invoice_line[0]
			debit_account = line.account_id
		else:
                        raise exceptions.ValidationError('No pued determinar cuenta contable')
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
				for invoice_line in invoice.move_lines:
					if invoice_line.debit > 0:
						invoice_line_id = invoice_line.id
				vals_debit = {
					'name': 'DEBIT - Partial refund conciliation' + str(move_id.id),
					'move_id': move_id.id,
					'partner_id': refund.partner_id.id,
					'account_id': debit_account.id,
					'debit': line.amount,
					'credit': 0
					}
				debit_move_id = self.env['account.move.line'].create(vals_debit)
				vals_credit = {
					'name': 'CREDIT - Partial refund conciliation' + str(move_id.id),
					'move_id': move_id.id,
					'partner_id': refund.partner_id.id,
					'account_id': credit_account.id,
					'debit': 0,
					'credit': line.amount
					}
				credit_move_id = self.env['account.move.line'].create(vals_credit)
				rec_ids.append([invoice_line_id,credit_move_id.id])	
		if move_id and debit_move_id and credit_move_id:
			move_id.post()
		import pdb;pdb.set_trace()
		# reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)
                return None

class refund_add_invoice_line(models.TransientModel):
	_name = 'refund.add.invoice.line'

	header_id = fields.Many2one('refund.add.invoice')
        invoice_id = fields.Many2one('account.invoice')
	date = fields.Date(string='Fecha')
	original_amount = fields.Float('Monto Factura')
	residual = fields.Float('Saldo')
        amount = fields.Float(string='Monto')

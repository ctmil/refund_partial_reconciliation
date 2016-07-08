from openerp import models, fields, api, _
from openerp.exceptions import except_orm
from openerp.osv import osv
import urllib2, httplib, urlparse, gzip, requests, json
from StringIO import StringIO
import openerp.addons.decimal_precision as dp
from datetime import date
import logging
import ast
#Get the logger
_logger = logging.getLogger(__name__)

class account_cashbox_add_line(models.TransientModel):
	_name = 'account.cashbox.add.line'

	name = fields.Char(string='Concepto',size=30)
	date = fields.Date(string='Fecha')
	amount = fields.Float(string='Monto')
	notes = fields.Text(string='Comentarios')
	issued_check = fields.Integer('Nro de cheque')
	account_checkbook_id = fields.Many2one('account.checkbook',domain="[('state','=','active')]")
	analytic_account_id = fields.Many2one('account.analytic.account')
	account_id = fields.Many2one('account.account')
	period_id = fields.Many2one('account.period')

	@api.multi
	def confirm_line(self):
		if self.issued_check and not self.account_checkbook_id:
                        raise osv.except_osv(('Error'), ('Debe seleccionar la chequera'))
                        return None
		if self.issued_check < self.account_checkbook_id.range_from or self.issued_check > self.account_checkbook_id.range_to:
                        raise osv.except_osv(('Error'), ('Cheque debe encontrarse dentro del rango seleccionado'))
                        return None
		cashbox_id = self.env.context['active_id']
		cashbox = self.env['account.cashbox'].browse(cashbox_id)
		settings = self.env['account.cashbox.settings'].search([])
		if not settings:
                        raise osv.except_osv(('Error'), ('No hay configuracion definida'))
                        return None
		period_id = self.period_id
		if not period_id:
                        raise osv.except_osv(('Error'), ('No hay periodo definido'))
			return None	
		if self.issued_check:
			if self.env['account.check'].search([('type','=','issue_check'),('number','=',self.issued_check)]):
                	        raise osv.except_osv(('Error'), ('Numero de cheque ya emitido'))
				return None	
		vals = {
			'date': self.date,
			'amount': self.amount,
			'name': self.name,
			'cashbox_id': cashbox_id,
			'line_type': 'add',
			}
		line_id = self.env['account.cashbox.lines'].create(vals)
		# Creates accounting move
		vals_account_move = {
			'date': self.date,
			'period_id': self.period_id.id,
			'journal_id': settings.cashbox_journal.id,
			'ref': self.name,
			'narration': self.notes,
			}
		move_id = self.env['account.move'].create(vals_account_move)	
		vals_account_move_line_debit = {
			'account_id': settings.cashbox_account.id,
			'debit': self.amount,
			'credit': 0,
			'date': self.date,
			'journal_id': settings.cashbox_journal.id,
			'name': self.name,
			'narration': self.notes,
			'move_id': move_id.id,
			'period_id': self.period_id.id,
			#'analytic_account_id': self.analytic_account_id.id,
			}
		line_debit_id = self.env['account.move.line'].create(vals_account_move_line_debit)
		vals_account_move_line_credit = {
			'account_id': settings.income_account.id,
			'debit': 0,
			'credit': self.amount,
			'date': self.date,
			'journal_id': settings.cashbox_journal.id,
			'name': self.name,
			'narration': self.notes,
			'move_id': move_id.id,
			'period_id': self.period_id.id,
			'analytic_account_id': self.analytic_account_id.id,
			}
		if not self.issued_check:
			vals_account_move_line_credit['account_id'] = settings.income_account.id
		else:
			vals_account_move_line_credit['account_id'] = settings.bank_account.id
				
		line_credit_id = self.env['account.move.line'].create(vals_account_move_line_credit)
		move_id.button_validate()
		vals = {
			'move_id': move_id.id,
			}
		line_id.write(vals)
		if self.issued_check:
			voucher_id = self.env['account.voucher'].search([('reference','=','CHEQUES PROPIOS')])
			if not voucher_id:
                        	raise osv.except_osv(('Error'), ('No hay voucher_id definido'))
				return None	
			vals_check = {
				'number': self.issued_check,
				'amount': self.amount,
				'voucher_id': voucher_id.id,
				'payment_date': self.date,
				}
			check_id = self.env['account.check'].create(vals_check)
			#if self_idi.checkbook_id.range_from <= check_id.number <= check_id.checkbook_id.range_to:
                        #	raise osv.except_osv(('Error'), ('Numero no definido en la chequera'))
			#	return None	
			check_id.action_debit()
			vals = {
				'check_id': check_id.id
				}
			line_id.write(vals)
		return None

class account_cashbox_substract_line(models.TransientModel):
	_name = 'account.cashbox.substract.line'

	name = fields.Char(string='Concepto',size=30)
	date = fields.Date(string='Fecha')
	amount = fields.Float(string='Monto')
	notes = fields.Text(string='Comentarios')
	analytic_account_id = fields.Many2one('account.analytic.account')
	account_id = fields.Many2one('account.account')
	period_id = fields.Many2one('account.period')

	@api.multi
	def confirm_line(self):
		cashbox_id = self.env.context['active_id']
		cashbox = self.env['account.cashbox'].browse(cashbox_id)
		settings = self.env['account.cashbox.settings'].search([])
		if not settings:
                        raise osv.except_osv(('Error'), ('No hay configuracion definida'))
                        return None
		period_id = self.period_id
		if not period_id:
                        raise osv.except_osv(('Error'), ('No hay periodo definido'))
			return None	
		vals = {
			'date': self.date,
			'amount': self.amount * (-1),
			'name': self.name,
			'cashbox_id': cashbox_id,
			'line_type': 'substract',
			}
		if self.account_id:
			expense_account = self.account_id.id
		else:
			expense_account = settings.expense_account.id
		vals['account_id'] = expense_account
		line_id = self.env['account.cashbox.lines'].create(vals)
		# Creates accounting move
		vals_account_move = {
			'date': self.date,
			'period_id': self.period_id.id,
			'journal_id': settings.cashbox_journal.id,
			'ref': self.name,
			'narration': self.notes,
			}
		move_id = self.env['account.move'].create(vals_account_move)	
		vals_account_move_line_credit = {
			'account_id': settings.cashbox_account.id,
			'credit': self.amount,
			'debit': 0,
			'date': self.date,
			'journal_id': settings.cashbox_journal.id,
			'name': self.name,
			'narration': self.notes,
			'move_id': move_id.id,
			'period_id': self.period_id.id,
			#'analytic_account_id': self.analytic_account_id.id,
			}
		line_credit_id = self.env['account.move.line'].create(vals_account_move_line_credit)
		vals_account_move_line_debit = {
			'account_id': expense_account,
			'debit': self.amount,
			'credit': 0,
			'date': self.date,
			'journal_id': settings.cashbox_journal.id,
			'name': self.name,
			'narration': self.notes,
			'move_id': move_id.id,
			'period_id': self.period_id.id,
			'analytic_account_id': self.analytic_account_id.id,
			}
		line_debit_id = self.env['account.move.line'].create(vals_account_move_line_debit)
		move_id.button_validate()
		vals = {
			'move_id': move_id.id,
			}
		line_id.write(vals)	
		return None


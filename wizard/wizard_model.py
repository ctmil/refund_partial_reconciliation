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
		import pdb;pdb.set_trace()
		vals_move = {
			'journal_id': self.journal_id.id,
			'date': str(date.today()),
			'company_id': 1,
			'partner_id':
			}
		move_id = self.env['account.move'].create(vals_move)
		if not move_id:
                        raise exceptions.ValidationError('No pudo crearse la cabecera del asiento contable')

                return None

class refund_add_invoice_line(models.TransientModel):
	_name = 'refund.add.invoice.line'

	header_id = fields.Many2one('refund.add.invoice')
        invoice_id = fields.Many2one('account.invoice')
	date = fields.Date(string='Fecha')
	original_amount = fields.Float('Monto Factura')
	residual = fields.Float('Saldo')
        amount = fields.Float(string='Monto')

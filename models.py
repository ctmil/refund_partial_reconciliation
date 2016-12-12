# -*- coding: utf-8 -*-
from openerp import models, api, fields, exceptions
from openerp.exceptions import ValidationError
from datetime import date

class account_invoice(models.Model):
	_inherit = "account.invoice"

	@api.multi
	def invoice_partial_conciliation(self):
		journal_id = self.env['account.journal'].search([('code','=','MISC')])
		if not journal_id:
			 raise exceptions.ValidationError('Debe tener creado el journal con codigo MISC')
		
		vals_header = {
			'name': str(self.id) + ' - ' + str(date.today()),
			'refund_id': self.id,
			'journal_id': journal_id.id,
			'amount': self.residual,
			}
		wizard_id = self.env['refund.add.invoice'].create(vals_header)
		if self.type == 'out_refund':
			invoices = self.env['account.invoice'].search([('partner_id','=',self.partner_id.id),\
									('type','=','out_invoice'),\
									('state','=','open')])
		else:
			invoices = self.env['account.invoice'].search([('partner_id','=',self.partner_id.id),\
									('type','=','in_invoice'),\
									('state','=','open')])
		for invoice in invoices:
			if invoice.residual > 0:
				vals_inv = {
					'inv_type': invoice.type,
					'header_id': wizard_id.id,
					'invoice_id': invoice.id,
					'date': invoice.date_invoice,
					'original_amount': invoice.amount_total,
					'residual': invoice.residual,
					'amount': 0,
					}
				line_inv = self.env['refund.add.invoice.line'].create(vals_inv)
		
                return {'type': 'ir.actions.act_window',
                        'name': 'Agregar facturas a conciliacion',
                        'res_model': 'refund.add.invoice',
			'res_id': wizard_id.id,
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target': 'new',
                        'nodestroy': True,
                        }

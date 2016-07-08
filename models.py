# -*- coding: utf-8 -*-
from openerp import models, api, fields, exceptions
from openerp.exceptions import ValidationError
from datetime import date

class account_invoice(models.Model):
	_inherit = "account.invoice"

	@api.multi
	def invoice_partial_conciliation(self):
		vals_header = {
			'name': str(self.id) + ' - ' + str(date.today())
			}
		wizard_id = self.env['refund.add.invoice'].create(vals_header)
		invoices = self.env['account.invoice'].search([('partner_id','=',self.partner_id.id),\
								('state','=','open')])
		for invoice in invoices:
			vals_inv = {
				'header_id': wizard_id.id,
				'invoice_id': invoice.id,
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

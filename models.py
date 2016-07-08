# -*- coding: utf-8 -*-
from openerp import models, api, fields, exceptions
from openerp.exceptions import ValidationError

class account_invoice(models.Model):
	_inherit = "account.invoice"

	@api.multi
	def invoice_partial_conciliation(self):
                return {'type': 'ir.actions.act_window',
                        'name': 'Agregar facturas a conciliacion',
                        'res_model': 'refund.add.invoice',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target': 'new',
                        'nodestroy': True,
                        }

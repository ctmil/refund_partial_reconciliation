# -*- coding: utf-8 -*-
from openerp import models, api, fields, exceptions
from openerp.exceptions import ValidationError

class account_invoice(models.Model):
	_inherit = "sale.order"

	@api.one
	def invoice_partial_conciliation(self):
		import pdb;pdb.set_trace()
		return {}

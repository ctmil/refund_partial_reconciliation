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

class refund_add_invoice(models.TransientModel):
        _name = 'refund.add.invoice'

        invoice_id = fields.Many2one('account.analytic.account')
        amount = fields.Float(string='Monto')

        @api.multi
        def confirm_line(self):
                import pdb;pdb.set_trace()
                return None


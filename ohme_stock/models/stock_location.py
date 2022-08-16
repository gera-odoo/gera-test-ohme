# -*- coding: utf-8 -*-
from odoo import models, fields


class StockLocation(models.Model):
    _inherit = 'stock.location'

    move_qa_passed_location_id = fields.Many2one('stock.location', string="Move QA passed to")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
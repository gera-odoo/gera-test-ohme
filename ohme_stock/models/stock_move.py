# -*- coding: utf-8 -*-
from odoo import models, api, fields
# in case you need to check the attached file's mimetype
# from odoo.tools.mimetypes import guess_mimetype
from xlrd import open_workbook
import base64
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    lot_serial_excel_file = fields.Binary(string='Import file',
                                          help='Upload here your Excel file having the first columns name "Lot/Serial Number"')

    def generate_serial_move_line_excel(self, lot_ids):
        self.ensure_one()

        move_lines = self.env['stock.move.line']
        if self.picking_type_id.show_reserved:
            move_lines = self.move_line_ids.filtered(lambda ml: not ml.lot_id and not ml.lot_name)
        else:
            move_lines = self.move_line_nosuggest_ids.filtered(lambda ml: not ml.lot_id and not ml.lot_name)

        move_line_vals = {
            'picking_id': self.picking_id.id,
            'location_dest_id': self.location_dest_id.id,
            'location_id': self.location_id.id,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_id.uom_id.id,
            'qty_done': 1,
        }

        move_lines_commands = []
        for lot_id in lot_ids:
            if move_lines:
                move_lines_commands.append((1, move_lines[0].id, {
                    'lot_id': lot_id.id,
                    'qty_done': 1,
                }))
                move_lines = move_lines[1:]
            else:
                move_line_cmd = dict(move_line_vals, lot_id=lot_id.id)
                move_lines_commands.append((0, 0, move_line_cmd))
        return move_lines_commands

    def import_lot_serial(self):
        self.ensure_one()
        bio = base64.b64decode(self.lot_serial_excel_file)
        # in case you need to check the attached file's mimetype
        # mimetype = guess_mimetype(bio)
        with open_workbook(file_contents=bio) as wb:
            sh = wb.sheet_by_index(0)
            # First column contain the c
            lot_names = [cell.value for cell in sh.col(0)[1:]]

            if lot_names:
                lot_ids = self.env['stock.production.lot'].search([('name', 'in', lot_names)])
                if not lot_ids:
                    raise ValidationError("One or more serial numbers don't exist in Odoo!")
                move_lines_commands = self.generate_serial_move_line_excel(lot_ids)
                self.write({'move_line_ids': move_lines_commands})

        self.lot_serial_excel_file = False

        return self.action_show_details()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
# -*- coding: utf-8 -*-
from odoo import models, api


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    def write(self, vals):
        res = super(StockProductionLot, self).write(vals)
        if vals.get('x_studio_passed_qa', False):
            # we can add a company filter in domain ('company_id', '=', self.env.company.move_passed_qa)
            picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'internal'),
                                                                     ('company_id', '=', self.env.company.id)], limit=1)
            StockQuant = self.env['stock.quant']

            res_dict = {}

            for each in self.filtered(lambda x: x.x_studio_passed_qa):
                stock_quant_id = StockQuant.search([('lot_id', '=', each._origin.id),
                                                    ('company_id', '=', self.env.company.id)
                                                    ])

                lot_vals = {'lot_id': each.id,
                            'stock_quant_id': stock_quant_id.id,
                            'product_id': each.product_id.id,
                            'product_uom_id': each.product_id.uom_id.id}
                if stock_quant_id and stock_quant_id.location_id.move_qa_passed_location_id:
                    # TODO The code below will create one internal picking for each lot serial number
                    # TODO method 1
                    # vals = {
                    #     'picking_type_id': picking_type_id.id,
                    #     'location_id': stock_quant_id.location_id.id,
                    #     'location_dest_id': stock_quant_id.location_id.move_qa_passed_location_id.id
                    # }
                    # picking_id = self.env['stock.picking'].create(vals)
                    # self.env['stock.move.line'].create({
                    #     'product_id': each.product_id.id,
                    #     'product_uom_id': each.product_id.uom_id.id,
                    #     'lot_id': each._origin.id,
                    #     'location_id': stock_quant_id.location_id.id,
                    #     'location_dest_id': stock_quant_id.location_id.move_qa_passed_location_id.id,
                    #     'product_uom_qty': 1.0,
                    #     'qty_done': 1.0,
                    #     'picking_id': picking_id.id})
                    # picking_id.action_confirm()
                    # picking_id.button_validate()
                    # TODO method 1 ENDS

                    # TODO Below code will group internal picking by locations and create a combined picking
                    # TODO method 2
                    if stock_quant_id.location_id.id not in res_dict:
                        res_dict[stock_quant_id.location_id.id] = {
                            stock_quant_id.location_id.move_qa_passed_location_id.id: [lot_vals]}
                    else:
                        if stock_quant_id.location_id.move_qa_passed_location_id.id not in res_dict[
                                stock_quant_id.location_id.id]:
                            res_dict[stock_quant_id.location_id.id].update({
                                stock_quant_id.location_id.move_qa_passed_location_id.id: [lot_vals]})
                        else:
                            res_dict[stock_quant_id.location_id.id][
                                stock_quant_id.location_id.move_qa_passed_location_id.id].append(lot_vals)

            for src_location_id, dest_loc_dict in res_dict.items():
                for each_dest, picking_vals_list in dest_loc_dict.items():
                    picking_vals = {
                        'picking_type_id': picking_type_id.id,
                        'location_id': src_location_id,
                        'location_dest_id': each_dest
                    }
                    picking_id = self.env['stock.picking'].create(picking_vals)
                    [self.env['stock.move.line'].create({
                            'product_id': each_val['product_id'],
                            'product_uom_id': each_val['product_uom_id'],
                            'lot_id': each_val['lot_id'],
                            'location_id': src_location_id,
                            'location_dest_id': each_dest,
                            'product_uom_qty': 1.0,
                            'qty_done': 1.0,
                            'picking_id': picking_id.id})
                            for each_val in picking_vals_list]
                    picking_id.action_confirm()
                    picking_id.button_validate()
            # TODO method 2 ENDS

        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
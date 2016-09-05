# -*- coding: utf-8 -*-
# Copyright 2016 Lorenzo Battistini - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError
import logging

_logger = logging.getLogger(__name__)


class StockTransferDetails(models.TransientModel):
    _inherit = 'stock.transfer_details'

    @api.one
    def do_detailed_transfer(self):
        res = super(StockTransferDetails, self).do_detailed_transfer()
        picking_model = self.env['stock.picking']
        # reading as admin to read other company's data
        picking = picking_model.sudo().browse(self.picking_id.id)
        if picking.sale_id:
            po = None
            if picking.sale_id.auto_purchase_order_id:
                po = picking.sale_id.auto_purchase_order_id
            else:
                pos = self.env['purchase.order'].sudo().search([
                    ('auto_sale_order_id', '=', picking.sale_id.id)])
                if len(pos) > 1:
                    raise UserError(_(
                        "Too many purchase orders found for sale order "
                        "%s") % picking.sale_id.name)
                if pos:
                    po = pos[0]
            if po:
                if len(po.picking_ids) > 1:
                    _logger.info(
                        "Too many picking for purchase order %s. Skipping"
                        % po.name)
                elif len(po.picking_ids) == 1:
                    other_picking = po.picking_ids[0]
                    if not other_picking.company_id.intercompany_user_id:
                        raise UserError(_(
                            "Please set an Inter Company User for company %s"
                            % other_picking.company_id.name))
                    other_user_id = (
                        other_picking.company_id.intercompany_user_id.id)
                    other_picking = picking_model.sudo(
                        other_user_id
                    ).browse(other_picking.id)
                    wizard_id = other_picking.do_enter_transfer_details()[
                        'res_id']
                    wizard = self.env['stock.transfer_details'].sudo(
                        other_user_id).browse(wizard_id)
                    wizard.item_ids.unlink()
                    line_model = self.env['stock.transfer_details_items']
                    sourceloc_id = other_picking.move_lines[0].location_id.id
                    destinationloc_id = other_picking.move_lines[
                        0].location_dest_id.id
                    for line in self.item_ids:
                        line_model.sudo(other_user_id).create({
                            'transfer_id': wizard_id,
                            'product_id': line.product_id.id,
                            'product_uom_id': line.product_uom_id.id,
                            'quantity': line.quantity,
                            'lot_id': line.lot_id and line.lot_id.id or None,
                            'sourceloc_id': sourceloc_id,
                            'destinationloc_id': destinationloc_id,
                        })
                    wizard.do_detailed_transfer()
        return res

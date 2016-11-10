# -*- coding: utf-8 -*-
# Copyright 2016 Lorenzo Battistini - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    master_picking_id = fields.Many2one(
        'stock.picking', string='Master picking')
    # used like one2one
    slave_picking_ids = fields.One2many(
        'stock.picking', 'master_picking_id', string='Slave picking')


class StockTransferDetails(models.TransientModel):
    _inherit = 'stock.transfer_details'

    def check_slave_picking(self, picking):
        if picking.company_id.prevent_slave_pickings_manual_transfer:
            if not self.env.context.get('inter_company_automation'):
                so_model = self.env['sale.order']
                for move in picking.move_lines:
                    if move.purchase_line_id.order_id:
                        slave_po = move.purchase_line_id.order_id
                        master_so = so_model.sudo().search([
                            ('auto_purchase_order_id', '=', slave_po.id)])
                        if master_so:
                            raise UserError(_(
                                "Can't manually transfer a \"slave\" picking "
                                "[%s] (linked to a master inter company "
                                "picking). Please process the master picking "
                                "of the other company"
                            ) % picking.name)

    @api.one
    def do_detailed_transfer(self):
        res = super(StockTransferDetails, self).do_detailed_transfer()
        picking_model = self.env['stock.picking']
        # reading as admin to read other company's data
        picking = picking_model.sudo().browse(self.picking_id.id)
        self.check_slave_picking(picking)
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
                other_pickings_todo = po.picking_ids.filtered(
                    lambda r: r.state != 'done')
                if len(other_pickings_todo) > 1:
                    _logger.info(
                        "Too many picking for purchase order %s. Skipping"
                        % po.name)
                elif len(other_pickings_todo) == 1:
                    other_picking = other_pickings_todo[0]
                    other_picking.sudo().master_picking_id = picking.id
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
                    wizard.with_context(
                        {'inter_company_automation': True}
                    ).do_detailed_transfer()
        return res

# -*- coding: utf-8 -*-
from openerp import fields, models


class ResCompany(models.Model):

    _inherit = 'res.company'

    prevent_slave_pickings_manual_transfer = fields.Boolean(
        "Prevent slave pickings to be manually transfered",
        help="Company A sells and deliveries goods to company B\n"
             "When company A transfers the delivery order, the corresponding "
             "picking of company B is automatically processed too.\n\n"
             "Setting this flag prevents company B to manually transfer "
             "\"slave\" pickings (linked to company A)"
    )

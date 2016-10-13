# -*- coding: utf-8 -*-
# Copyright 2016 Lorenzo Battistini - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Synchronize inter company pickings",
    "summary": "Extension of Inter Company Module for delivery orders",
    "version": "8.0.1.0.0",
    "website": "https://www.agilebg.com",
    "author": "Agile Business Group, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "inter_company_rules",
    ],
    "data": [
        "views/res_company_view.xml",
    ],
}

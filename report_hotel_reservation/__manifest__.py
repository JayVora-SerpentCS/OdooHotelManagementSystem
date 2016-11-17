# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Hotel Reservation Management - Reporting",
    "version": "0.03",
    "author": "Serpent Consulting Services Pvt. Ltd., OpenERP SA,\
    Odoo Community Association (OCA)",
    "website": "http://www.serpentcs.com",
    "depends": ["hotel_reservation"],
    "license": "",
    "category": "Generic Modules/Hotel Reservation",
    "data": [
        "security/ir.model.access.csv",
        "views/report_hotel_reservation_view.xml",
    ],
    'installable': True,
    'auto_install': False,
}

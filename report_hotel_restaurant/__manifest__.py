# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Restaurant Management - Reporting",
    "version": "0.03",
    "author": "Serpent Consulting Services Pvt. Ltd., OpenERP SA,\
    Odoo Community Association (OCA)",
    "website": "http://www.serpentcs.com, http://www.openerp.com",
    "depends": ["hotel_restaurant","report_hotel_reservation"],
    "license": "",
    "category": "Generic Modules/Hotel Restaurant",
    "data": [
        "security/ir.model.access.csv",
        "views/report_hotel_restaurant_view.xml",
    ],
    'installable': True,
    'auto_install': False,
}

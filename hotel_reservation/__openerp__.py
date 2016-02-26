# -*- coding: utf-8 -*-
#############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://www.serpentcs.com>)
#    Copyright (C) 2004 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
#############################################################################

{
    "name": "Hotel Reservation Management",
    "version": "0.07",
    "author": "Serpent Consulting Services Pvt. Ltd., OpenERP SA,\
    Odoo Community Association (OCA)",
    "images": [],
    "license": "",
    "category": "Generic Modules/Hotel Reservation",
    "website": "http://www.serpentcs.com",
    "depends": ["hotel", "stock", 'mail', "hotel_report_layout",
                'email_template'],
    "demo": [
        "views/hotel_reservation_data.xml",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/hotel_reservation_wizard.xml",
        "report/hotel_reservation_report.xml",
        "views/hotel_reservation_sequence.xml",
        "views/hotel_reservation_workflow.xml",
        "views/hotel_reservation_view.xml",
        "views/hotel_scheduler.xml",
        "views/report_checkin.xml",
        "views/report_checkout.xml",
        "views/max_room.xml",
        "views/room_res.xml",
        "views/room_summ_view.xml",
        "views/email_temp_view.xml",
    ],
    'js': ["static/src/js/hotel_room_summary.js", ],
    'qweb': ['static/src/xml/hotel_room_summary.xml'],
    'css': ["static/src/css/room_summary.css"],
    'installable': True,
    'auto_install': False,
}

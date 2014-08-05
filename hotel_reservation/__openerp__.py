# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>)
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
##############################################################################

{
    "name" : "Hotel Reservation Management",
    "version" : "0.07",
    "author": ["Serpent Consulting Services Pvt. Ltd.", "OpenERP SA" ],
    "category" : "Generic Modules/Hotel Reservation",
    "description": """
    Module for Hotel/Resort/Property management. You can manage:
    * Guest Reservation
    * Group Reservartion
      Different reports are also provided, mainly for hotel statistics.
    """,
    "website": ["http://www.serpentcs.com", "http://www.openerp.com"],
    "depends" : ["hotel", "stock", "report_extended"],
    "data" : [
        "security/ir.model.access.csv",
        "wizard/hotel_reservation_wizard.xml",
        "report/hotel_reservation_report.xml",
        "hotel_reservation_sequence.xml",
        "hotel_reservation_workflow.xml",
        "hotel_reservation_view.xml",
        "hotel_scheduler.xml",
        "views/report_checkin.xml",
        "views/report_checkout.xml",
        "views/max_room.xml",
        "views/room_res.xml",
        "views/room_summ_view.xml",
    ],
    "demo": [
        # 'hotel_reservation_data.xml',
    ],
    'js': ["static/src/js/hotel_room_summary.js", ],
    'qweb': ['static/src/xml/hotel_room_summary.xml'],
    'css': ["static/src/css/room_summary.css"],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

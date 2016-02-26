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
    "name": "Board for Hotel FrontDesk",
    "version": "1.0",
    "author": "Serpent Consulting Services Pvt. Ltd.,\
    Odoo Community Association (OCA)",
    "website": "http://www.serpentcs.com",
    "images": [],
    "license": "",
    "category": "Board/Hotel FrontDesk",
    "depends": [
        "board",
        "report_hotel_restaurant",
        "hotel_pos_restaurant"
        ],
    "data": [
        "views/board_frontdesk_view.xml"
    ],
    "installable": True,
}

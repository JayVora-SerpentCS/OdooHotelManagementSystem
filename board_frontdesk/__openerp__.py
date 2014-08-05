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
    "name":"Board for Hotel FrontDesk",
    "version" : "0.03",
    "author":"Serpent Consulting Services Pvt. Ltd.", "OpenERP SA"
    "category":"Board/Hotel FrontDesk",
    "website": ["http://www.serpentcs.com", "http://www.openerp.com"],
    "depends":[
        "board",
        "hotel_reservation",
    ],
    "description": """
    This module implements a dashboard for hotel FrontDesk that includes:
    * Calendar view of Today's Check-In and Check-Out
    * Calendar view of Weekly Check-In and Check-Out
    * Calendar view of Monthly Check-In and Check-Out
    """,
    "data":[
        "board_frontdesk_view.xml"
    ],
    "auto_install": False,
    "installable": True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
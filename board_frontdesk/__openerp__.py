# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################
{
    "name":"Board for Hotel FrontDesk",
    "version":"1.0",
    "author":"Tiny",
    "category":"Board/Hotel FrontDesk",
    "depends":[
        "board",
        "report_hotel_restaurant"
        ],
    "demo_xml":[],
    "data":[
        "views/board_frontdesk_view.xml"
    ],
    "description": """
This module implements a dashboard for hotel FrontDesk that includes:
    * Calendar view of Today's Check-In and Check-Out
    * Calendar view of Weekly Check-In and Check-Out
    * Calendar view of Monthly Check-In and Check-Out
    """,
    "active":False,
    "installable":True,
}
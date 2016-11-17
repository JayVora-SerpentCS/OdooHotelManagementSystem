# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    "name": "Board for Hotel FrontDesk",
    "version": "0.01",
    "author": "Serpent Consulting Services Pvt. Ltd.,\
    Odoo Community Association (OCA)",
    "website": "http://www.serpentcs.com",
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
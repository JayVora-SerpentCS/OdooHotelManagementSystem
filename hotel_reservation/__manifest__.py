# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Hotel Reservation Management',
    'version': '10.0.1.0.0',
    'author': 'Serpent Consulting Services Pvt. Ltd., OpenERP SA',
    'category': 'Generic Modules/Hotel Reservation',
    'website': 'http://www.serpentcs.com',
    'depends': ['hotel', 'stock', 'mail'],
    'license': 'AGPL-3',
    'demo': [
        'views/hotel_reservation_data.xml',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/hotel_reservation_wizard.xml',
        'report/hotel_reservation_report.xml',
        'views/hotel_reservation_sequence.xml',
        'views/hotel_reservation_view.xml',
        'views/report_checkin.xml',
        'views/report_checkout.xml',
        'views/max_room.xml',
        'views/room_res.xml',
        'views/room_summ_view.xml',
    ],
    'js': ['static/src/js/hotel_room_summary.js', ],
    'qweb': ['static/src/xml/hotel_room_summary.xml'],
    'css': ['static/src/css/room_summary.css'],
    'images': ['static/description/HotelReservation.png'],
    'installable': True,
    'auto_install': False,
}

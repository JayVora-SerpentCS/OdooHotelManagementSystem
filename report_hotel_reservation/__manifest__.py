# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Hotel Reservation Management - Reporting',
    'version': '10.0.1.0.0',
    'author': 'Serpent Consulting Services Pvt. Ltd., OpenERP SA',
    'website': 'http://www.serpentcs.com',
    'depends': ['hotel_reservation'],
    'license': 'AGPL-3',
    'category': 'Generic Modules/Hotel Reservation',
    'data': [
        'security/ir.model.access.csv',
        'views/report_hotel_reservation_view.xml',
    ],
    'images': ['static/description/HotelReservationReporting.png'],
    'installable': True,
    'auto_install': False,
}

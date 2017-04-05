# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Board for Hotel FrontDesk',
    'version': '10.0.1.0.0',
    'author': 'Serpent Consulting Services Pvt. Ltd., OpenERP SA',
    'website': 'http://www.serpentcs.com',
    'category': 'Board/Hotel FrontDesk',
    'depends': [
        'board',
        'report_hotel_restaurant',
        'hotel_pos_restaurant'
        ],
    'license': 'AGPL-3',
    'data': [
        'views/board_frontdesk_view.xml'
    ],
    'installable': True,
}

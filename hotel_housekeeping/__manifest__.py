# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Hotel Housekeeping Management',
    'version': '10.0.1.0.0',
    'author': 'Serpent Consulting Services Pvt. Ltd., OpenERP SA',
    'category': 'Generic Modules/Hotel Housekeeping',
    'website': 'http://www.serpentcs.com',
    'depends': ['hotel'],
    'license': 'AGPL-3',
    'demo': [
        'views/hotel_housekeeping_data.xml',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/hotel_housekeeping_report.xml',
        'views/activity_detail.xml',
        'wizard/hotel_housekeeping_wizard.xml',
        'views/hotel_housekeeping_view.xml',
    ],
    'images': ['static/description/HouseKeeping.png'],
    'installable': True,
    'auto_install': False,
}

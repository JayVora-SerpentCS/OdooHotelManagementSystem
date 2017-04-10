# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Pos Options Bar',
    'version': '10.0.1.0.0',
    'category': 'Point Of Sale',
    'sequence': 6,
    'summary': 'Touchscreen Interface for Shops',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'license': 'AGPL-3',
    'website': 'http://www.serpentcs.com',
    'installable': True,
    'application': True,
    'data': ['security/ir.model.access.csv',
             'view/templates.xml'],
    'depends': ['point_of_sale'],
    'qweb': ['static/src/xml/pos_options.xml'],
    'auto_install': False,
}

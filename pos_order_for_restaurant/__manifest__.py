# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Parcel/Delivery Order For Restaurant',
    'version': '10.0.1.0.0',
    'category': 'Point Of Sale',
    'sequence': 6,
    'summary': 'Touchscreen Interface for Restaurant',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'license': 'AGPL-3',
    'website': 'http://www.serpentcs.com',
    'installable': True,
    'application': True,
    'data': ['security/pos_order_for_restaurant_security.xml',
             'security/ir.model.access.csv',
             'view/templates.xml',
             'view/pos_order_for_restaurant_view.xml',
    ],
    'demo': [
        'view/pos_order_restaurant_demo.xml',
     ],
    'depends': ['point_of_sale', 'pos_restaurant', 'pos_receipt'],
    'qweb': ['static/src/xml/pos_order_for_restaurant.xml'],
    'auto_install': False,
}

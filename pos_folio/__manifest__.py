# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Pos Folio',
    'version': '10.0.1.0.0',
    'category': 'Point Of Sale',
    'sequence': 6,
    'summary': 'Touchscreen Interface for Shops',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'license': 'AGPL-3',
    'website': 'http://www.serpentcs.com',
    'installable': True,
    'application': True,
    'depends': ['hotel', 'pos_order_for_restaurant'],
    'data': ['view/pos_folio_view.xml',
             'view/templates.xml'],
    'qweb': ['static/src/xml/*.xml'],
    'images': ['static/description/pos_folio.png'],
    'auto_install': False,
}

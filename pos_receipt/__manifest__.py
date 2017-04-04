# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Pos Receipt',
    'version': '10.0.1.0.0',
    'category': 'Point Of Sale',
    'sequence': 6,
    'summary': 'Touchscreen Interface for Shops',
    'author': 'Serpent Consulting Services Pvt. Ltd.,\
    Odoo Community Association (OCA)',
    'website': 'http://www.serpentcs.com',
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'data':['security/pos_receipt_security.xml',
            'security/ir.model.access.csv',
            'view/templates.xml',
            'view/pos_receipt_view.xml',
            'view/kitchen_screen_data.xml',
           ],
    'depends': ['point_of_sale', 'pos_options_bar'],
    'qweb': ['static/src/xml/pos_receipt.xml'],
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

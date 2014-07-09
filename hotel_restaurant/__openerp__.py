# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Serpent Consulting Services Pvt. Ltd. (<http://www.serpentcs.com>)
#    Copyright (C) 2004 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    "name" : "Hotel Restaurant Management",
    "version" : "0.05",
    "author": ["Serpent Consulting Services Pvt. Ltd.", "OpenERP SA" ],
    "category" : "Generic Modules/Hotel Restaurant",
    "description": """
    Module for Hotel/Resort/Restaurant management. You can manage:
    * Configure Property
    * Restaurant Configuration
    * table reservation
    * Generate and process Kitchen Order ticket,
    * Payment

    Different reports are also provided, mainly for Restaurant.
    """,
    "website": "http://www.serpentcs.com",
    "depends" : ["hotel", "report_extended"],
    "data" : [
        "security/ir.model.access.csv",
        "report/hotel_restaurant_report.xml",
        "wizard/hotel_restaurant_wizard.xml",
        "views/res_table.xml",
        "views/kot.xml",
        "views/bill.xml",
        "hotel_restaurant_workflow.xml",
        "hotel_restaurant_sequence.xml",
        "hotel_restaurant_view.xml",
    ],
    "active": False,
    "installable": True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

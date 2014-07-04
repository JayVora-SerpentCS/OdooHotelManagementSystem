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
    "name" : "Restaurant Management - Reporting",
    "version" : "0.03",
    "author": ["Serpent Consulting Services Pvt. Ltd.", "OpenERP SA" ],
    "website": ["http://www.serpentcs.com", "http://www.openerp.com"],
    "depends" : ["hotel_restaurant", "report_hotel_reservation"],
    "category" : "Generic Modules/Hotel Restaurant",
    "description": """
    Module shows the status of restaurant reservation
     * Current status of reserved tables
     * List status of tables as draft or done state
    """,
    "data": [
        "security/ir.model.access.csv",
        "report_hotel_restaurant_view.xml",
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
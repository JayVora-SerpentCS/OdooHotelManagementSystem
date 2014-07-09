# -*- encoding: utf-8 -*-
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

import time
from openerp.osv import osv
from openerp.report import report_sxw

class hotel_restaurant_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(hotel_restaurant_report, self).__init__(cr, uid, name, context)
        self.localcontext.update( {
            'time': time,
            'get_res_data':self.get_res_data,
        })
        self.context=context

    def get_res_data(self,date_start,date_end):
        rest_reservation_obj = self.pool.get('hotel.restaurant.reservation')
        tids = rest_reservation_obj.search(self.cr, self.uid, [('start_date', '>=', date_start),('end_date', '<=', date_end)])
        res = rest_reservation_obj.browse(self.cr, self.uid, tids)
        return res

class report_lunchorder(osv.AbstractModel):
    _name = 'report.hotel_restaurant.report_res_table'
    _inherit = 'report.abstract_report'
    _template = 'hotel_restaurant.report_res_table'
    _wrapped_report_class = hotel_restaurant_report
    
class report_kot(osv.AbstractModel):
    _name = 'report.hotel_restaurant.report_hotel_order_kot'
    _inherit = 'report.abstract_report'
    _template = 'hotel_restaurant.report_hotel_order_kot'
    _wrapped_report_class = hotel_restaurant_report
    
class report_bill(osv.AbstractModel):
    _name = 'report.hotel_restaurant.report_hotel_order_kot'
    _inherit = 'report.abstract_report'
    _template = 'hotel_restaurant.report_hotel_order_kot'
    _wrapped_report_class = hotel_restaurant_report
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
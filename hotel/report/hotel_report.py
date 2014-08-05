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

import time
from openerp.osv import osv
from openerp.report import report_sxw

class folio_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(folio_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'get_data': self.get_data,
            'get_Total' : self.getTotal,
            'get_total': self.gettotal,
        })
        self.temp = 0.0

    def get_data(self, date_start, date_end):
        folio_obj = self.pool.get('hotel.folio')
        partner_obj = self.pool.get('res.partner')
        tids = folio_obj.search(self.cr, self.uid, [('checkin_date', '>=', date_start), ('checkout_date', '<=', date_end)])
        res = folio_obj.browse(self.cr, self.uid, 1)
        res1 = partner_obj.browse(self.cr, self.uid, 1)
        return res

    def gettotal(self, total):
        self.temp = self.temp + float(total)
        return total

    def getTotal(self):
        return self.temp
    
class report_lunchorder(osv.AbstractModel):
    _name = 'report.hotel.report_hotel_folio'
    _inherit = 'report.abstract_report'
    _template = 'hotel.report_hotel_folio'
    _wrapped_report_class = folio_report

# report_sxw.report_sxw('report.folio.total', 'hotel.folio', 'addons/hotel/report/total_folio.rml', parser=folio_report)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:                 

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
################################################################################

from openerp.osv import osv, fields

class folio_report_wizard(osv.TransientModel):
    _name = 'folio.report.wizard'
    _rec_name = 'date_start'
    _columns = {
        'date_start':fields.datetime('Start Date'),
        'date_end':fields.datetime('End Date')
    }
    def print_report(self, cr, uid, ids, context=None):
        values = {
            'ids': ids,
            'model': 'hotel.folio',
            'form': self.read(cr, uid, ids, context=context)[0]
        }
        return self.pool['report'].get_action(cr, uid, [], 'hotel.report_hotel_folio', data=values, context=context)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

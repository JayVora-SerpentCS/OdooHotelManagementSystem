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

from openerp.osv import osv, fields

class hotel_reservation_wizard(osv.TransientModel):
    _name = 'hotel.reservation.wizard'
    _columns = {
        'date_start': fields.datetime('Start Date',required=True),
        'date_end': fields.datetime('End Date',required=True),
    }

    def report_reservation_detail(self,cr,uid,ids,context=None):
        values = {
            'ids': ids,
            'model': 'hotel.reservation',
            'form': self.read(cr, uid, ids, context=context)[0]
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'reservation.detail',
            'datas': values,
        }

    def report_checkin_detail(self,cr,uid,ids,context=None):
        values = {
            'ids': ids,
            'model': 'hotel.reservation',
            'form': self.read(cr, uid, ids, context=context)[0]
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'checkin.detail',
            'datas': values,
        }

    def report_checkout_detail(self,cr,uid,ids,context=None):
        values = {
            'ids': ids,
            'model': 'hotel.reservation',
            'form': self.read(cr, uid, ids, context=context)[0]
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'checkout.detail',
            'datas': values,
        }

    def report_maxroom_detail(self,cr,uid,ids,context=None):
        values = {
            'ids': ids,
            'model': 'hotel.reservation',
            'form': self.read(cr, uid, ids, context=context)[0]
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'maxroom.detail',
            'datas': values,
        }

hotel_reservation_wizard()


class make_folio_wizard(osv.TransientModel):
    _name = 'wizard.make.folio'
    _columns = {
        'grouped': fields.boolean('Group the Folios'),
    }
    _defaults = {
        'grouped': False,
    }

    def makeFolios(self, cr, uid, data, context=None):
        order_obj = self.pool.get('hotel.reservation')
        newinv = []
        for order in order_obj.browse(cr, uid, context['active_ids'], context=context):
            for folio in order.folio_id:
                newinv.append(folio.id)
        return {
            'domain': "[('id','in', ["+','.join(map(str, newinv))+"])]",
            'name': 'Folios',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hotel.folio',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }

make_folio_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
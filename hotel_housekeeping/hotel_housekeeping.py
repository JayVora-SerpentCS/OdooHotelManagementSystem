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

from openerp.osv import fields, osv
import time
from openerp import netsvc

class product_category(osv.Model):
    _inherit = "product.category"
    _columns = {
        'isactivitytype': fields.boolean('Is Activity Type'),
    }
    _defaults = {
        'isactivitytype': lambda *a: True,
    }

class hotel_housekeeping_activity_type(osv.Model):
    _name = 'hotel.housekeeping.activity.type'
    _description = 'Activity Type'
    _inherits = {'product.category':'activity_id'}
    _columns = {
        'activity_id': fields.many2one('product.category', 'Category', required=True, ondelete='cascade'),
    }

class hotel_activity(osv.Model):
    _name = 'hotel.activity'
    _inherits = {'product.product': 'h_id'}
    _description = 'Housekeeping Activity'
    _columns = {
        'h_id': fields.many2one('product.product', 'Product', required=True, ondelete='cascade'),
    }

class hotel_housekeeping(osv.Model):

    _name = "hotel.housekeeping"
    _description = "Reservation"
    _columns = {
        'current_date':fields.date("Today's Date", required=True),
        'clean_type':fields.selection([('daily', 'Daily'), ('checkin', 'Check-In'), ('checkout', 'Check-Out')], 'Clean Type', required=True),
        'room_no':fields.many2one('hotel.room', 'Room No', required=True),
        'activity_lines':fields.one2many('hotel.housekeeping.activities', 'a_list', 'Activities', help='Details of housekeeping activities.'),
        'inspector':fields.many2one('res.users', 'Inspector', required=True),
        'inspect_date_time':fields.datetime('Inspect Date Time', required=True),
        'quality':fields.selection([('bad', 'Bad'), ('good', 'Good'), ('ok', 'Ok')], 'Quality', required=True, help='Inspector inspect the room and mark as Bad, Good or Ok. '),
        'state': fields.selection([('dirty', 'Dirty'), ('clean', 'Clean'), ('inspect', 'Inspect'), ('done', 'Done'), ('cancel', 'Cancelled')], 'State', select=True, required=True, readonly=True),
    }
    _defaults = {
        'state': lambda *a: 'dirty',
        'current_date':lambda *a: time.strftime('%Y-%m-%d'),
    }

    def action_set_to_dirty(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'dirty'})
        wf_service = netsvc.LocalService('workflow')
        for id in ids:
            wf_service.trg_create(uid, self._name, id, cr)
        return True

    def room_cancel(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {
            'state':'cancel'
        })
        return True

    def room_done(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {
            'state':'done'
        })
        return True

    def room_inspect(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {
            'state':'inspect'
        })
        return True

    def room_clean(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {
            'state':'clean'
        })
        return True

class hotel_housekeeping_activities(osv.Model):
    _name = "hotel.housekeeping.activities"
    _description = "Housekeeping Activities "
    _columns = {
        'a_list':fields.many2one('hotel.housekeeping', 'Reservation'),
        'room_id':fields.many2one('hotel.room', 'Room No'),
        'today_date':fields.date('Today Date'),
        'activity_name':fields.many2one('hotel.activity', 'Housekeeping Activity'),
        'housekeeper':fields.many2one('res.users', 'Housekeeper', required=True),
        'clean_start_time':fields.datetime('Clean Start Time', required=True),
        'clean_end_time':fields.datetime('Clean End Time', required=True),
        'dirty':fields.boolean('Dirty', help='Checked if the housekeeping activity results as Dirty.'),
        'clean':fields.boolean('Clean', help='Checked if the housekeeping activity results as Clean.'),
    }

    def default_get(self, cr, uid, fields, context=None):
        """ To get default values for the object.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param fields: List of fields for which we want default values 
        @param context: A standard dictionary 
        @return: A dictionary which of fields with values. 
        """ 
        if context is None:
            context = {}
        res = super(hotel_housekeeping_activities, self).default_get(cr, uid, fields, context=context)
        if context.get('room_id', False):
            res.update({'room_id':context['room_id']})
        if context.get('today_date', False):
            res.update({'today_date':context['today_date']})
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

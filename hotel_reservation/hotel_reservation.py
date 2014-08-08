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
import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.translate import _

class hotel_folio(osv.Model):
    _inherit = 'hotel.folio'
    _order = 'reservation_id desc'
    _columns = {
        'reservation_id': fields.many2one('hotel.reservation', 'Reservation Id'),
    }

class hotel_reservation(osv.Model):
    _name = "hotel.reservation"
    _rec_name = "reservation_no"
    _description = "Reservation"
    _order = 'reservation_no desc'
    _columns = {
        'reservation_no': fields.char('Reservation No', size=64, required=True, readonly=True),
        'date_order':fields.datetime('Date Ordered', required=True, readonly=True, states={'draft':[('readonly', False)]}),
        'warehouse_id':fields.many2one('stock.warehouse', 'Hotel', readonly=True, required=True, states={'draft':[('readonly', False)]}),
        'partner_id':fields.many2one('res.partner', 'Guest Name', readonly=True, required=True, states={'draft':[('readonly', False)]}),
        'pricelist_id':fields.many2one('product.pricelist', 'Price List', required=True, readonly=True, states={'draft':[('readonly', False)]}, help="Pricelist for current reservation. "),
        'partner_invoice_id':fields.many2one('res.partner', 'Invoice Address', readonly=True, states={'draft':[('readonly', False)]}, help="Invoice address for current reservation. "),
        'partner_order_id':fields.many2one('res.partner', 'Ordering Contact', readonly=True, states={'draft':[('readonly', False)]}, help="The name and address of the contact that requested the order or quotation."),
        'partner_shipping_id':fields.many2one('res.partner', 'Delivery Address', readonly=True, states={'draft':[('readonly', False)]}, help="Delivery address for current reservation. "),
        'checkin': fields.datetime('Expected-Date-Arrival', required=True, readonly=True, states={'draft':[('readonly', False)]}),
        'checkout': fields.datetime('Expected-Date-Departure', required=True, readonly=True, states={'draft':[('readonly', False)]}),
        'adults':fields.integer('Adults', size=64, readonly=True, states={'draft':[('readonly', False)]}, help='List of adults there in guest list. '),
        'children':fields.integer('Children', size=64, readonly=True, states={'draft':[('readonly', False)]}, help='Number of children there in guest list. '),
        'reservation_line':fields.one2many('hotel_reservation.line', 'line_id', 'Reservation Line', help='Hotel room reservation details. '),
        'state': fields.selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('cancel', 'Cancel'), ('done', 'Done')], 'State', readonly=True),
        'folio_id': fields.many2many('hotel.folio', 'hotel_folio_reservation_rel', 'order_id', 'invoice_id', 'Folio'),
        'dummy': fields.datetime('Dummy'),
    }
    _defaults = {
        'reservation_no': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'hotel.reservation'),
        'state': lambda *a: 'draft',
        'date_order': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }


    def on_change_checkin(self, cr, uid, ids, date_order, checkin_date=time.strftime('%Y-%m-%d %H:%M:%S'), context=None):
        if date_order and checkin_date:
            if checkin_date < date_order:
                raise osv.except_osv(_('Warning'), _('Checkin date should be greater than the current date.'))
        return {'value':{}}

    def on_change_checkout(self, cr, uid, ids, checkin_date=time.strftime('%Y-%m-%d %H:%M:%S'), checkout_date=time.strftime('%Y-%m-%d %H:%M:%S'), context=None):
        if not (checkout_date and checkin_date):
            return {'value':{}}
        if checkout_date < checkin_date:
            raise osv.except_osv(_('Warning'), _('Checkout date should be greater than the Checkin date.'))
        delta = datetime.timedelta(days=1)
        addDays = datetime.datetime(*time.strptime(checkout_date, '%Y-%m-%d %H:%M:%S')[:5]) + delta
        val = {'value':{'dummy':addDays.strftime('%Y-%m-%d %H:%M:%S')}}
        return val

    def onchange_partner_id(self, cr, uid, ids, partner_id):
        if not partner_id:
            return {'value':{'partner_invoice_id': False, 'partner_shipping_id':False, 'partner_order_id':False}}
        partner_obj = self.pool.get('res.partner')
        addr = partner_obj.address_get(cr, uid, [partner_id], ['delivery', 'invoice', 'contact'])
        pricelist = partner_obj.browse(cr, uid, partner_id).property_product_pricelist.id
        return {'value':{'partner_invoice_id': addr['invoice'], 'partner_order_id':addr['contact'], 'partner_shipping_id':addr['delivery'], 'pricelist_id': pricelist}}

    def confirmed_reservation(self, cr, uid, ids, context=None):
        reservation_line_obj = self.pool.get('hotel.room.reservation.line')
        for reservation in self.browse(cr, uid, ids, context=context):
            cr.execute("select count(*) from hotel_reservation as hr " \
                        "inner join hotel_reservation_line as hrl on hrl.line_id = hr.id " \
                        "inner join hotel_reservation_line_room_rel as hrlrr on hrlrr.room_id = hrl.id " \
                        "where (checkin,checkout) overlaps ( timestamp %s , timestamp %s ) " \
                        "and hr.id <> cast(%s as integer) " \
                        "and hr.state = 'confirm' " \
                        "and hrlrr.hotel_reservation_line_id in (" \
                        "select hrlrr.hotel_reservation_line_id from hotel_reservation as hr " \
                        "inner join hotel_reservation_line as hrl on hrl.line_id = hr.id " \
                        "inner join hotel_reservation_line_room_rel as hrlrr on hrlrr.room_id = hrl.id " \
                        "where hr.id = cast(%s as integer) )" \
                        , (reservation.checkin, reservation.checkout, str(reservation.id), str(reservation.id)))
            res = cr.fetchone()
            roomcount = res and res[0] or 0.0
            if roomcount:
                raise osv.except_osv(_('Warning'), _('You tried to confirm reservation with room those already reserved in this reservation period'))
            else:
                self.write(cr, uid, ids, {'state':'confirm'}, context=context)
                for line_id in reservation.reservation_line:
                    line_id = line_id.reserve
                    for room_id in line_id:
                        vals = {
                            'room_id': room_id.id,
                            'check_in': reservation.checkin,
                            'check_out': reservation.checkout,
                            'state': 'assigned',
                            'reservation_id': reservation.id,
                        }
                        reservation_line_obj.create(cr, uid, vals, context=context)
        return True

    def _create_folio(self, cr, uid, ids, context=None):
        hotel_folio_obj = self.pool.get('hotel.folio')
        room_obj = self.pool.get('hotel.room')
        for reservation in self.browse(cr, uid, ids, context=context):
            folio_lines = []
            checkin_date, checkout_date = reservation['checkin'], reservation['checkout']
            if not checkin_date < checkout_date:
                raise osv.except_osv(_('Error'), _('Invalid values in reservation.\nCheckout date should be greater than the Checkin date.'))
            duration_vals = hotel_folio_obj.onchange_dates(cr, uid, [], checkin_date=checkin_date, checkout_date=checkout_date, duration=False)
            duration = duration_vals.get('value', False) and duration_vals['value'].get('duration') or 0.0
            folio_vals = {
                'date_order':reservation.date_order,
                'warehouse_id':reservation.warehouse_id.id,
                'partner_id':reservation.partner_id.id,
                'pricelist_id':reservation.pricelist_id.id,
                'partner_invoice_id':reservation.partner_invoice_id.id,
                'partner_shipping_id':reservation.partner_shipping_id.id,
                'checkin_date': reservation.checkin,
                'checkout_date': reservation.checkout,
                'duration': duration,
                'reservation_id': reservation.id,
                'service_lines':reservation['folio_id']
            }
            for line in reservation.reservation_line:
                for r in line.reserve:
                    folio_lines.append((0, 0, {
                        'checkin_date': checkin_date,
                        'checkout_date': checkout_date,
                        'product_id': r.product_id and r.product_id.id,
                        'name': reservation['reservation_no'],
                        'product_uom': r['uom_id'].id,
                        'price_unit': r['lst_price'],
                        'product_uom_qty': (datetime.datetime(*time.strptime(reservation['checkout'], '%Y-%m-%d %H:%M:%S')[:5]) - datetime.datetime(*time.strptime(reservation['checkin'], '%Y-%m-%d %H:%M:%S')[:5])).days
                    }))
                    room_obj.write(cr, uid, [r.id], {'status': 'occupied'}, context=context)
            folio_vals.update({'room_lines': folio_lines})
            folio = hotel_folio_obj.create(cr, uid, folio_vals, context=context)
            cr.execute('insert into hotel_folio_reservation_rel (order_id, invoice_id) values (%s,%s)', (reservation.id, folio))
            self.write(cr, uid, ids, {'state': 'done'}, context=context)
        return True

class hotel_reservation_line(osv.Model):
    _name = "hotel_reservation.line"
    _description = "Reservation Line"
    _columns = {
         'name':fields.char('Name', size=64),
         'line_id':fields.many2one('hotel.reservation'),
         'reserve':fields.many2many('hotel.room', 'hotel_reservation_line_room_rel', 'room_id', 'hotel_reservation_line_id', domain="[('isroom','=',True),('categ_id','=',categ_id)]"),
         'categ_id': fields.many2one('product.category', 'Room Type', domain="[('isroomtype','=',True)]", change_default=True),
        }

    def on_change_categ(self, cr, uid, ids, categ_ids, checkin, checkout, context=None):
        hotel_room_obj = self.pool.get('hotel.room')
        hotel_room_ids = hotel_room_obj.search(cr, uid, [('categ_id', '=', categ_ids)], context=context)
        assigned = False
        room_ids = []
        if not checkin:
            raise osv.except_osv(_('No Checkin date Defined!'), _('Before choosing a room,\n You have to select a Check in date or a Check out date in the reservation form.'))
        for room in hotel_room_obj.browse(cr, uid, hotel_room_ids, context=context):
            assigned = False
            for line in room.room_reservation_line_ids:
                if line.check_in == checkin and line.check_out == checkout:
                    assigned = True
            if not assigned:
                room_ids.append(room.id)
        domain = {'reserve': [('id', 'in', room_ids)]}
        return {'domain': domain}

class hotel_room_reservation_line(osv.Model):
    _name = 'hotel.room.reservation.line'
    _description = 'Hotel Room Reservation'
    _rec_name = 'room_id'
    _columns = {
        'room_id': fields.many2one('hotel.room', 'Room id'),
        'check_in':fields.datetime('Check In Date', required=True),
        'check_out': fields.datetime('Check Out Date', required=True),
        'state': fields.selection([('assigned', 'Assigned'), ('unassigned', 'Unassigned')], 'Room Status'),
        'reservation_id': fields.many2one('hotel.reservation', 'Reservation'),
    }

hotel_room_reservation_line()


class hotel_room(osv.Model):
    _inherit = 'hotel.room'
    _description = 'Hotel Room'
    _columns = {
        'room_reservation_line_ids': fields.one2many('hotel.room.reservation.line', 'room_id', 'Room Reservation Line'),
    }

    def cron_room_line(self, cr, uid, context=None):
        reservation_line_obj = self.pool.get('hotel.room.reservation.line')
        now = datetime.datetime.now()
        curr_date = now.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        room_ids = self.search(cr, uid, [], context=context)
        for room in self.browse(cr, uid, room_ids, context=context):
            status = {}
            reservation_line_ids = [reservation_line.id for reservation_line in room.room_reservation_line_ids]
            reservation_line_ids = reservation_line_obj.search(cr, uid, [('id', 'in', reservation_line_ids), ('check_in', '<=', curr_date), ('check_out', '>=', curr_date)], context=context)
            if reservation_line_ids:
                status = {'status': 'occupied'}
            else:
                status = {'status': 'available'}
            self.write(cr, uid, [room.id], status, context=context)
        return True

# class room_reservation_summary(osv.Model):
#     _name = 'room.reservation.summary'
#     _description = 'Room reservation summary'
#     _columns = {
#         'date_from':fields.datetime('Date From'),
#         'date_to':fields.datetime('Date To'),
#         'summary_header':fields.text('Summary Header'),
#         'room_summary':fields.text('Room Summary'),
#     }
# 
#     def room_reservation(self, cr, uid, ids, context=None):
#         mod_obj = self.pool.get('ir.model.data')
#         if context is None:
#             context = {}
#         model_data_ids = mod_obj.search(cr, uid, [('model', '=', 'ir.ui.view'), ('name', '=', 'view_hotel_reservation_form')], context=context)
#         resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
#         print model_data_ids, resource_id
#         return {
#             'name': _('Reconcile Write-Off'),
#             'context': context,
#             'view_type': 'form',
#             'view_mode': 'form',
#             'res_model': 'hotel.reservation',
#             'views': [(resource_id, 'form')],
#             'type': 'ir.actions.act_window',
#             'target': 'new',
#         }
# 
#     def get_room_summary(self, cr, uid, ids, date_from, date_to, context=None):
# 
#         res = {}
#         all_detail = []
#         room_obj = self.pool.get('hotel.room')
#         reservation_line_obj = self.pool.get('hotel.room.reservation.line')
#         date_range_list = []
#         main_header = []
#         summary_header_list = ['Rooms']
#         if date_from and date_to:
#             if date_from > date_to:
#                 raise osv.except_osv(_('User Error!'), _('Please Check Time period Date From can\'t be greater than Date To !'))
#             d_frm_obj = datetime.datetime.strptime(date_from, DEFAULT_SERVER_DATETIME_FORMAT)
#             d_to_obj = datetime.datetime.strptime(date_to, DEFAULT_SERVER_DATETIME_FORMAT)
#             temp_date = d_frm_obj
#             while(temp_date <= d_to_obj):
#                 val = ''
#                 val = str(temp_date.strftime("%a")) + ' ' + str(temp_date.strftime("%b")) + ' ' + str(temp_date.strftime("%d"))
#                 summary_header_list.append(val)
#                 date_range_list.append(temp_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT))
#                 temp_date = temp_date + datetime.timedelta(days=1)
#             all_detail.append(summary_header_list)
#             room_ids = room_obj.search(cr, uid, [], context=context)
#             all_room_detail = []
#             for room in room_obj.browse(cr, uid, room_ids, context=context):
#                 room_detail = {}
#                 room_list_stats = []
#                 room_detail.update({'name':room.name or ''})
#                 if not room.room_reservation_line_ids:
#                     for chk_date in date_range_list:
#                         room_list_stats.append({'state':'Free', 'date':chk_date})
#                 else:
#                     for chk_date in date_range_list:
#                         for room_res_line in room.room_reservation_line_ids:
#                             reservation_line_ids = [i.id for i in room.room_reservation_line_ids]
#                             reservation_line_ids = reservation_line_obj.search(cr, uid, [('id', 'in', reservation_line_ids), ('check_in', '<=', chk_date), ('check_out', '>=', chk_date)])
#                             if reservation_line_ids:
#                                 room_list_stats.append({'state':'Reserved', 'date':chk_date, 'room_id':room.id})
#                                 break
#                             else:
#                                 room_list_stats.append({'state':'Free', 'date':chk_date, 'room_id':room.id})
#                                 break
#                 room_detail.update({'value':room_list_stats})
#                 all_room_detail.append(room_detail)
#             main_header.append({'header':summary_header_list})
#             res.update({'value':{'summary_header': str(main_header), 'room_summary':str(all_room_detail)}})
#         return res
# 
# class quick_room_reservation(osv.TransientModel):
#     _name = 'quick.room.reservation'
#     _description = 'Quick Room Reservation'
#     _columns = {
#         'partner_id':fields.many2one('res.partner', string="Customer", required=True),
#         'check_in':fields.datetime('Check In', required=True),
#         'check_out':fields.datetime('Check Out', required=True),
#         'room_id':fields.many2one('hotel.room', 'Room', required=True),
#         'warehouse_id':fields.many2one('stock.warehouse', 'Hotel', required=True),
#         'pricelist_id':fields.many2one('product.pricelist', 'pricelist', required=True)
#     }
# 
#     def default_get(self, cr, uid, fields, context=None):
#         if context is None:
#             context = {}
#         print " contexty s lkal snkja ;;;", context
#         res = super(quick_room_reservation, self).default_get(cr, uid, fields, context=context)
#         if context:
#             keys = context.keys()
#             if 'date' in keys:
#                 res.update({'check_in': context['date']})
#             if 'room_id' in keys:
#                 res.update({'room_id': [context['room_id']]})
#         return res
# 
#     def room_reserve(self, cr, uid, ids, context=None):
#         hotel_res_obj = self.pool.get('hotel.reservation')
#         for room_resv in self.browse(cr, uid, ids, context=context):
#             hotel_res_obj.create(cr, uid, {
#                          'partner_id':room_resv.partner_id.id,
#                          'checkin':room_resv.check_in,
#                          'checkout':room_resv.check_out,
#                          'warehouse_id':room_resv.warehouse.id,
#                          'pricelist_id':room_resv.pricelist_id.id,
#                          'reservation_line':[(0, 0, {
#                          'reserve': [(6, 0, [room_resv.room_id.id])],
#                          'name':room_resv.room_id and room_resv.room_id.name or ''})]
#                         }, context=context)
#         return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

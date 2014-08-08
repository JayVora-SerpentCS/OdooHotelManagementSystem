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

from openerp.osv import fields, osv
import time
from openerp import netsvc
import datetime
from openerp.tools.translate import _

class hotel_floor(osv.Model):
    _name = "hotel.floor"
    _description = "Floor"
    _columns = {
        'name': fields.char('Floor Name', size=64, required=True, select=True),
        'sequence': fields.integer('Sequence', size=64),
    }

class product_category(osv.Model):
    _inherit = "product.category"
    _columns = {
        'isroomtype':fields.boolean('Is Room Type'),
        'isamenitytype':fields.boolean('Is Amenities Type'),
        'isservicetype':fields.boolean('Is Service Type'),
    }

class hotel_room_type(osv.Model):
    _name = "hotel.room.type"
    _inherits = {'product.category': 'cat_id'}
    _description = "Room Type"
    _columns = {
        'cat_id': fields.many2one('product.category', 'category', required=True, select=True, ondelete='cascade'),
    }
    _defaults = {
        'isroomtype': 1,
    }

class product_product(osv.Model):
    _inherit = "product.product"
    _columns = {
        'isroom':fields.boolean('Is Room'),
        'iscategid':fields.boolean('Is categ id'),
        'isservice':fields.boolean('Is Service id'),
    }

class hotel_room_amenities_type(osv.Model):
    _name = 'hotel.room.amenities.type'
    _description = 'amenities Type'
    _inherits = {'product.category':'cat_id'}
    _columns = {
        'cat_id':fields.many2one('product.category', 'category', required=True, ondelete='cascade'),
    }
    _defaults = {
        'isamenitytype': 1,
    }

class hotel_room_amenities(osv.Model):
    _name = 'hotel.room.amenities'
    _description = 'Room amenities'
    _inherits = {'product.product':'room_categ_id'}
    _columns = {
        'room_categ_id':fields.many2one('product.product', 'Product Category', required=True, ondelete='cascade'),
        'rcateg_id':fields.many2one('hotel.room.amenities.type', 'Amenity Catagory'),
    }
    _defaults = {
        'iscategid': 1,
    }


class hotel_room(osv.Model):
    _name = 'hotel.room'
    _inherits = {'product.product': 'product_id'}
    _description = 'Hotel Room'

    _columns = {
        'product_id': fields.many2one('product.product', 'Product_id', required=True, ondelete='cascade'),
        'floor_id':fields.many2one('hotel.floor', 'Floor No', help='At which floor the room is located.'),
        'max_adult':fields.integer('Max Adult'),
        'max_child':fields.integer('Max Child'),
        'room_amenities':fields.many2many('hotel.room.amenities', 'temp_tab', 'room_amenities', 'rcateg_id', 'Room Amenities', help='List of room amenities. '),
        'status':fields.selection([('available', 'Available'), ('occupied', 'Occupied')], 'Status'),
#         'room_rent_ids':fields.one2many('room.rent', 'rent_id', 'Room Rent'),
    }

    _defaults = {
        'isroom': 1,
        'rental': 1,
        'status': 'available',
    }

    def set_room_status_occupied(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'status': 'occupied'}, context=context)

    def set_room_status_available(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'status': 'available'}, context=context)


# class room_rent(osv.Model):
#     _name = 'room.rent'
#     _columns = {
#         'rent_id': fields.many2one('hotel.room', 'Room Rent'),
#         'price': fields.float('Price (Per night)'),
#         'mon': fields.boolean('Monday'),
#         'tue': fields.boolean('Tuesday'),
#         'wed': fields.boolean('Wednesday'),
#         'thu': fields.boolean('Thursday'),
#         'fri': fields.boolean('Friday'),
#         'sat': fields.boolean('Saturday'),
#         'sun': fields.boolean('Sunday'),
#     }

class hotel_folio(osv.Model):

    def copy(self, cr, uid, id, default=None, context=None):
        return self.pool.get('sale.order').copy(cr, uid, id, default=None, context=None)

    def _invoiced(self, cursor, user, ids, name, arg, context=None):
        return self.pool.get('sale.order')._invoiced(cursor, user, ids, name, arg, context=None)

    def _invoiced_search(self, cursor, user, obj, name, args):
        return self.pool.get('sale.order')._invoiced_search(cursor, user, obj, name, args)

    _name = 'hotel.folio'
    _description = 'hotel folio new'
    _inherits = {'sale.order': 'order_id'}
    _rec_name = 'order_id'
    _order = 'id desc'
    _columns = {
      'name': fields.char('Folio Number', size=24, readonly=True),
      'order_id': fields.many2one('sale.order', 'Order', required=True, ondelete='cascade'),
      'checkin_date': fields.datetime('Check In', required=True, readonly=True, states={'draft':[('readonly', False)]}),
      'checkout_date': fields.datetime('Check Out', required=True, readonly=True, states={'draft':[('readonly', False)]}),
      'room_lines': fields.one2many('hotel.folio.line', 'folio_id', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Hotel room reservation detail."),
      'service_lines': fields.one2many('hotel.service.line', 'folio_id', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Hotel services detail provide to customer and it will include in main Invoice."),
      'hotel_policy': fields.selection([('prepaid', 'On Booking'), ('manual', 'On Check In'), ('picking', 'On Checkout')], 'Hotel Policy', help="Hotel policy for payment that either the guest has to payment at booking time or check-in check-out time."),
      'duration': fields.float('Duration in Days', readonly=True, help="Number of days which will automatically count from the check-in and check-out date. "),
    }
    _defaults = {
      'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'hotel.folio'),
      'hotel_policy':'manual'
    }
    _sql_constraints = [
        ('check_in_out', 'CHECK (checkin_date<=checkout_date)', 'Check in Date Should be less than the Check Out Date!'),
    ]

    def _check_room_vacant(self, cr, uid, ids, context=None):
        folio = self.browse(cr, uid, ids[0], context=context)
        rooms = []
        for room in folio.room_lines:
            if room.product_id in rooms:
                return False
            rooms.append(room.product_id)
        return True

    _constraints = [
        (_check_room_vacant, 'You cannot allocate the same room twice!', ['room_lines'])
    ]

    def onchange_dates(self, cr, uid, ids, checkin_date=False, checkout_date=False, duration=False):
        # This mathod gives the duration between check in checkout if customer will leave only for some hour it would be considers as
        # a whole day. If customer will checkin checkout for more or equal hours , which configured in company as additional hours than
        # it would be consider as full day
        value = {}
        company_obj = self.pool.get('res.company')
        configured_addition_hours = 0
        company_ids = company_obj.search(cr, uid, [])
        if company_ids:
            company = company_obj.browse(cr, uid, company_ids[0])
            configured_addition_hours = company.additional_hours
        if not duration:
            duration = 0
            if checkin_date and checkout_date:
                chkin_dt = datetime.datetime.strptime(checkin_date, '%Y-%m-%d %H:%M:%S')
                chkout_dt = datetime.datetime.strptime(checkout_date, '%Y-%m-%d %H:%M:%S')
                dur = chkout_dt - chkin_dt
                duration = dur.days
                if configured_addition_hours > 0:
                    additional_hours = abs((dur.seconds / 60) / 60)
                    if additional_hours >= configured_addition_hours:
                        duration += 1
            value.update({'value':{'duration':duration}})
        else:
            if checkin_date:
                chkin_dt = datetime.datetime.strptime(checkin_date, '%Y-%m-%d %H:%M:%S')
                chkout_dt = chkin_dt + datetime.timedelta(days=duration)
                checkout_date = datetime.datetime.strftime(chkout_dt, '%Y-%m-%d %H:%M:%S')
                value.update({'value':{'checkout_date':checkout_date}})
        return value

    def create(self, cr, uid, vals, context=None, check=True):
        tmp_room_lines = vals.get('room_lines', [])
        vals['order_policy'] = vals.get('hotel_policy', 'manual')
        if not 'service_lines' and 'folio_id' in vals:
                vals.update({'room_lines':[]})
                folio_id = super(hotel_folio, self).create(cr, uid, vals, context=context)
                for line in (tmp_room_lines):
                    line[2].update({'folio_id':folio_id})
                vals.update({'room_lines':tmp_room_lines})
                super(hotel_folio, self).write(cr, uid, [folio_id], vals, context=context)
        else:
            folio_id = super(hotel_folio, self).create(cr, uid, vals, context=context)
        return folio_id

    def onchange_warehouse_id(self, cr, uid, ids, warehouse_id):
        order_ids = [folio.order_id.id for folio in self.browse(cr, uid, ids)]
        return self.pool.get('sale.order').onchange_warehouse_id(cr, uid, order_ids, warehouse_id)

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        res = {}
        if part:
            partner_rec = self.pool.get('res.partner').browse(cr, uid, part, context=context)
            order_ids = [folio.order_id.id for folio in self.browse(cr, uid, ids, context=context)]
            if not order_ids:
                res['value'] = {'partner_invoice_id': partner_rec.id , 'pricelist_id':partner_rec.property_product_pricelist.id}
                res['warning'] = {'title': _('Warning'), 'message': _('Not Any Order For  %s ' % (partner_rec.name))}
            else:
                res['value'] = {'partner_invoice_id': partner_rec.id, 'pricelist_id':partner_rec.property_product_pricelist.id}
        return res

    def button_dummy(self, cr, uid, ids, context=None):
        order_ids = [folio.order_id.id for folio in self.browse(cr, uid, ids)]
        return self.pool.get('sale.order').button_dummy(cr, uid, order_ids, context={})

    def action_invoice_create(self, cr, uid, ids, grouped=False, states=['confirmed', 'done']):
        order_ids = [folio.order_id.id for folio in self.browse(cr, uid, ids)]
        invoice_id = self.pool.get('sale.order').action_invoice_create(cr, uid, order_ids, grouped=False, states=['confirmed', 'done'])
        for line in self.browse(cr, uid, ids):
            values = {
                'invoiced': True,
                'state': 'progress' if grouped else 'progress',
            }
            line.write(values)
        return invoice_id

    def action_invoice_cancel(self, cr, uid, ids, context=None):
        order_ids = [folio.order_id.id for folio in self.browse(cr, uid, ids)]
        res = self.pool.get('sale.order').action_invoice_cancel(cr, uid, order_ids, context=context)
        for sale in self.browse(cr, uid, ids, context=context):
            for line in sale.order_line:
                line.write({'invoiced': 'invoiced'})
        self.write(cr, uid, ids, {'state':'invoice_except'}, context=context)
        return res

    def action_cancel(self, cr, uid, ids, context=None):
        order_ids = [folio.order_id.id for folio in self.browse(cr, uid, ids, context=context)]
        rv = self.pool.get('sale.order').action_cancel(cr, uid, order_ids, context=context)
        wf_service = netsvc.LocalService("workflow")
        for sale in self.browse(cr, uid, ids, context=context):
            for pick in sale.picking_ids:
                wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_cancel', cr)
            for invoice in sale.invoice_ids:
                wf_service.trg_validate(uid, 'account.invoice', invoice.id, 'invoice_cancel', cr)
                sale.write({'state':'cancel'})
        return rv

    def action_wait(self, cr, uid, ids, *args):
        sale_order_obj = self.pool.get('sale.order')
        res = False
        for o in self.browse(cr, uid, ids):
            res = sale_order_obj.action_wait(cr, uid, [o.order_id.id], *args)
            if (o.order_policy == 'manual') and (not o.invoice_ids):
                self.write(cr, uid, [o.id], {'state': 'manual'})
            else:
                self.write(cr, uid, [o.id], {'state': 'progress'})
        return res
#         order_ids = [folio.order_id.id for folio in self.browse(cr, uid, ids)]
#         res = self.pool.get('sale.order').action_wait(cr, uid, order_ids, *args)
#         for order in self.browse(cr, uid, ids):
#             state = ('progress', 'manual')[int(order.order_policy == 'manual' and not order.invoice_ids)]
#             order.write({'state': state})
#         return res

    def test_state(self, cr, uid, ids, mode, *args):
        write_done_ids = []
        write_cancel_ids = []
        # res = self.pool.get('sale.order').test_state(cr, uid, ids, mode, *args)
        if write_done_ids:
            self.pool.get('sale.order.line').write(cr, uid, write_done_ids, {'state': 'done'})
        if write_cancel_ids:
            self.pool.get('sale.order.line').write(cr, uid, write_cancel_ids, {'state': 'cancel'})
        # return res

    def procurement_lines_get(self, cr, uid, ids, *args):
        order_ids = [folio.order_id.id for folio in self.browse(cr, uid, ids)]
        # return self.pool.get('sale.order').procurement_lines_get(cr, uid, order_ids, *args)
        return True
    def action_ship_create(self, cr, uid, ids, context=None):
        order_ids = [folio.order_id.id for folio in self.browse(cr, uid, ids)]
        return self.pool.get('sale.order').action_ship_create(cr, uid, order_ids, context=None)

    def action_ship_end(self, cr, uid, ids, context=None):
        order_ids = [folio.order_id.id for folio in self.browse(cr, uid, ids)]
        # res = self.pool.get('sale.order').action_ship_end(cr, uid, order_ids, context=context)
        for order in self.browse(cr, uid, ids, context=context):
            order.write ({'shipped':True})
        # return res

    def has_stockable_products(self, cr, uid, ids, *args):
        order_ids = [folio.order_id.id for folio in self.browse(cr, uid, ids)]
        return self.pool.get('sale.order').has_stockable_products(cr, uid, order_ids, *args)

    def action_cancel_draft(self, cr, uid, ids, *args):
        if not len(ids):
            return False
        cr.execute('select id from sale_order_line where order_id IN %s and state=%s', (tuple(ids), 'cancel'))
        line_ids = map(lambda x: x[0], cr.fetchall())
        self.write(cr, uid, ids, {'state': 'draft', 'invoice_ids': [], 'shipped': 0})
        self.pool.get('sale.order.line').write(cr, uid, line_ids, {'invoiced': False, 'state': 'draft', 'invoice_lines': [(6, 0, [])]})
        wf_service = netsvc.LocalService("workflow")
        for inv_id in ids:
            # Deleting the existing instance of workflow for SO
            wf_service.trg_delete(uid, 'sale.order', inv_id, cr)
            wf_service.trg_create(uid, 'sale.order', inv_id, cr)
        for (id, name) in self.name_get(cr, uid, ids):
            message = _("The sales order '%s' has been set in draft state.") % (name,)
            self.log(cr, uid, id, message)
        return True

class hotel_folio_line(osv.Model):

    def copy(self, cr, uid, id, default=None, context=None):
        return self.pool.get('sale.order.line').copy(cr, uid, id, default=None, context=context)

    def _amount_line(self, cr, uid, ids, field_name, arg, context):
        return self.pool.get('sale.order.line')._amount_line(cr, uid, ids, field_name, arg, context)

    def _number_packages(self, cr, uid, ids, field_name, arg, context):
        return self.pool.get('sale.order.line')._number_packages(cr, uid, ids, field_name, arg, context)

    def _get_checkin_date(self, cr, uid, context=None):
        if 'checkin_date' in context:
            return context['checkin_date']
        return time.strftime('%Y-%m-%d %H:%M:%S')

    def _get_checkout_date(self, cr, uid, context=None):
        if 'checkin_date' in context:
            return context['checkout_date']
        return time.strftime('%Y-%m-%d %H:%M:%S')

    _name = 'hotel.folio.line'
    _description = 'hotel folio1 room line'
    _inherits = {'sale.order.line':'order_line_id'}
    _columns = {
        'order_line_id': fields.many2one('sale.order.line', 'Order Line', required=True, ondelete='cascade'),
        'folio_id': fields.many2one('hotel.folio', 'Folio', ondelete='cascade'),
        'checkin_date': fields.datetime('Check In', required=True),
        'checkout_date': fields.datetime('Check Out', required=True),
    }
    _defaults = {
        'checkin_date':_get_checkin_date,
        'checkout_date':_get_checkout_date,
    }

    def create(self, cr, uid, vals, context=None, check=True):
        if 'folio_id' in vals:
            folio = self.pool.get("hotel.folio").browse(cr, uid, vals['folio_id'], context=context)
            vals.update({'order_id':folio.order_id.id})
        return super(osv.Model, self).create(cr, uid, vals, context)

    def unlink(self, cr, uid, ids, context=None):
        sale_line_obj = self.pool.get('sale.order.line')
        for line in self.browse(cr, uid, ids, context=context):
            if line.order_line_id:
                sale_line_obj.unlink(cr, uid, [line.order_line_id.id], context=context)
        return super(hotel_folio_line, self).unlink(cr, uid, ids, context=None)

    def uos_change(self, cr, uid, ids, product_uos, product_uos_qty=0, product_id=None):
        line_ids = [folio.order_line_id.id for folio in self.browse(cr, uid, ids)]
        return  self.pool.get('sale.order.line').uos_change(cr, uid, line_ids, product_uos, product_uos_qty=0, product_id=None)

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        line_ids = [folio.order_line_id.id for folio in self.browse(cr, uid, ids)]
        return self.pool.get('sale.order.line').product_id_change(cr, uid, line_ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
            lang=False, update_tax=True, date_order=False)

    def product_uom_change(self, cursor, user, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        return self.product_id_change(cursor, user, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
            lang=False, update_tax=True, date_order=False)

    def on_change_checkout(self, cr, uid, ids, checkin_date=None, checkout_date=None, context=None):
        if not checkin_date:
            checkin_date = time.strftime('%Y-%m-%d %H:%M:%S')
        if not checkout_date:
            checkout_date = time.strftime('%Y-%m-%d %H:%M:%S')
        qty = 1
        if checkout_date < checkin_date:
            raise osv.except_osv(_('Error !'), _('Checkout must be greater or equal checkin date'))
        if checkin_date:
            diffDate = datetime.datetime(*time.strptime(checkout_date, '%Y-%m-%d %H:%M:%S')[:5]) - datetime.datetime(*time.strptime(checkin_date, '%Y-%m-%d %H:%M:%S')[:5])
            qty = diffDate.days
            if qty == 0:
                qty = 1
        return {'value':{'product_uom_qty':qty}}

    def button_confirm(self, cr, uid, ids, context=None):
        line_ids = [folio.order_line_id.id for folio in self.browse(cr, uid, ids)]
        return self.pool.get('sale.order.line').button_confirm(cr, uid, line_ids, context=context)

    def button_done(self, cr, uid, ids, context=None):
        line_ids = [folio.order_line_id.id for folio in self.browse(cr, uid, ids)]
        res = self.pool.get('sale.order.line').button_done(cr, uid, line_ids, context=context)
        wf_service = netsvc.LocalService("workflow")
        res = self.write(cr, uid, ids, {'state':'done'})
        for line in self.browse(cr, uid, ids, context):
            wf_service.trg_write(uid, 'sale.order', line.order_line_id.order_id.id, cr)
        return res

    def copy_data(self, cr, uid, id, default=None, context=None):
        line_id = self.browse(cr, uid, id).order_line_id.id
        return self.pool.get('sale.order.line').copy_data(cr, uid, line_id, default=None, context=context)

class hotel_service_line(osv.Model):

    def copy(self, cr, uid, id, default=None, context=None):
        line_id = self.browse(cr, uid, id).service_line_id.id
        return self.pool.get('sale.order.line').copy(cr, uid, line_id, default=None, context=context)

    def _amount_line(self, cr, uid, ids, field_name, arg, context):
        line_ids = [folio.service_line_id.id for folio in self.browse(cr, uid, ids)]
        return  self.pool.get('sale.order.line')._amount_line(cr, uid, line_ids, field_name, arg, context)

    def _number_packages(self, cr, uid, ids, field_name, arg, context):
        line_ids = [folio.service_line_id.id for folio in self.browse(cr, uid, ids)]
        return self.pool.get('sale.order.line')._number_packages(cr, uid, line_ids, field_name, arg, context)

    _name = 'hotel.service.line'
    _description = 'hotel Service line'
    _inherits = {'sale.order.line':'service_line_id'}
    _columns = {
        'service_line_id': fields.many2one('sale.order.line', 'Service Line', required=True, ondelete='cascade'),
        'folio_id': fields.many2one('hotel.folio', 'Folio', ondelete='cascade'),
    }

    def create(self, cr, uid, vals, context=None, check=True):
        if 'folio_id' in vals:
            folio = self.pool.get("hotel.folio").browse(cr, uid, vals['folio_id'], context=context)
            vals.update({'order_id':folio.order_id.id})
        return super(osv.Model, self).create(cr, uid, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        sale_line_obj = self.pool.get('sale.order.line')
        for line in self.browse(cr, uid, ids, context=context):
            if line.service_line_id:
                sale_line_obj.unlink(cr, uid, [line.service_line_id.id], context=context)
        return super(hotel_service_line, self).unlink(cr, uid, ids, context=None)

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        line_ids = [folio.service_line_id.id for folio in self.browse(cr, uid, ids)]
        return self.pool.get('sale.order.line').product_id_change(cr, uid, line_ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
            lang=False, update_tax=True, date_order=False)

    def product_uom_change(self, cursor, user, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        return self.product_id_change(cursor, user, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
            lang=False, update_tax=True, date_order=False)

    def on_change_checkout(self, cr, uid, ids, checkin_date=None, checkout_date=None, context=None):
        if not checkin_date:
            checkin_date = time.strftime('%Y-%m-%d %H:%M:%S')
        if not checkout_date:
            checkout_date = time.strftime('%Y-%m-%d %H:%M:%S')
        qty = 1
        if checkout_date < checkin_date:
            raise osv.except_osv(_('Error !'), _('Checkout must be greater or equal checkin date'))
        if checkin_date:
            diffDate = datetime.datetime(*time.strptime(checkout_date, '%Y-%m-%d %H:%M:%S')[:5]) - datetime.datetime(*time.strptime(checkin_date, '%Y-%m-%d %H:%M:%S')[:5])
            qty = diffDate.days
        return {'value':{'product_uom_qty':qty}}

    def button_confirm(self, cr, uid, ids, context=None):
        line_ids = [folio.service_line_id.id for folio in self.browse(cr, uid, ids)]
        return self.pool.get('sale.order.line').button_confirm(cr, uid, line_ids, context=context)

    def button_done(self, cr, uid, ids, context=None):
        line_ids = [folio.service_line_id.id for folio in self.browse(cr, uid, ids)]
        return self.pool.get('sale.order.line').button_done(cr, uid, line_ids, context=context)

    def uos_change(self, cr, uid, ids, product_uos, product_uos_qty=0, product_id=None):
        line_ids = [folio.service_line_id.id for folio in self.browse(cr, uid, ids)]
        return self.pool.get('sale.order.line').uos_change(cr, uid, line_ids, product_uos, product_uos_qty=0, product_id=None)

    def copy_data(self, cr, uid, id, default=None, context=None):
        line_id = self.browse(cr, uid, id).service_line_id.id
        return self.pool.get('sale.order.line').copy_data(cr, uid, line_id, default=default, context=context)


class hotel_service_type(osv.Model):
    _name = "hotel.service.type"
    _inherits = {'product.category':'ser_id'}
    _description = "Service Type"
    _columns = {
        'ser_id':fields.many2one('product.category', 'category', required=True, select=True, ondelete='cascade'),
    }
    _defaults = {
        'isservicetype': 1,
    }

class hotel_services(osv.Model):
    _name = 'hotel.services'
    _description = 'Hotel Services and its charges'
    _inherits = {'product.product':'service_id'}
    _columns = {
        'service_id': fields.many2one('product.product', 'Service_id', required=True, ondelete='cascade'),
    }
    _defaults = {
        'isservice': 1,
    }

class res_company(osv.Model):
    _inherit = 'res.company'
    _columns = {
        'additional_hours': fields.integer('Additional Hours', help="Provide the min hours value for check in, checkout days, whatever the hours will be provided here based on that extra days will be calculated."),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

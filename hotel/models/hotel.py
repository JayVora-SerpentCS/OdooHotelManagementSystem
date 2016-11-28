# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Serpent Consulting Services PVT. LTD.
#    (<http://www.serpentcs.com>)
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
# ---------------------------------------------------------------------------

import time
import datetime
import urllib2
from odoo.exceptions import except_orm, ValidationError
from odoo.tools import misc, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import models, fields, api, _
from odoo import workflow
from decimal import Decimal


def _offset_format_timestamp1(src_tstamp_str, src_format, dst_format,
                              ignore_unparsable_time=True, context=None):
    """
    Convert a source timeStamp string into a destination timeStamp string,
    attempting to apply the correct offset if both the server and local
    timeZone are recognized,or no offset at all if they aren't or if
    tz_offset is false (i.e. assuming they are both in the same TZ).

    @param src_tstamp_str: the STR value containing the timeStamp.
    @param src_format: the format to use when parsing the local timeStamp.
    @param dst_format: the format to use when formatting the resulting
     timeStamp.
    @param server_to_client: specify timeZone offset direction (server=src
                             and client=dest if True, or client=src and
                             server=dest if False)
    @param ignore_unparsable_time: if True, return False if src_tstamp_str
                                   cannot be parsed using src_format or
                                   formatted using dst_format.
    @return: destination formatted timestamp, expressed in the destination
             timezone if possible and if tz_offset is true, or src_tstamp_str
             if timezone offset could not be determined.
    """
    if not src_tstamp_str:
        return False
    res = src_tstamp_str
    if src_format and dst_format:
        try:
            # dt_value needs to be a datetime.datetime object\
            # (so notime.struct_time or mx.DateTime.DateTime here!)
            dt_value = datetime.datetime.strptime(src_tstamp_str, src_format)
            if context.get('tz', False):
                try:
                    import pytz
                    src_tz = pytz.timezone(context['tz'])
                    dst_tz = pytz.timezone('UTC')
                    src_dt = src_tz.localize(dt_value, is_dst=True)
                    dt_value = src_dt.astimezone(dst_tz)
                except Exception:
                    pass
            res = dt_value.strftime(dst_format)
        except Exception:
            # Normal ways to end up here are if strptime or strftime failed
            if not ignore_unparsable_time:
                return False
            pass
    return res


class HotelFloor(models.Model):

    _name = "hotel.floor"
    _description = "Floor"

    name = fields.Char('Floor Name', size=64, required=True, select=True)
    sequence = fields.Integer('Sequence', size=64)


class ProductCategory(models.Model):

    _inherit = "product.category"

    isroomtype = fields.Boolean('Is Room Type')
    isamenitytype = fields.Boolean('Is Amenities Type')
    isservicetype = fields.Boolean('Is Service Type')


class HotelRoomType(models.Model):

    _name = "hotel.room.type"
    _description = "Room Type"

    cat_id = fields.Many2one('product.category', 'category', required=True,
                             delegate=True, select=True, ondelete='cascade')


class ProductProduct(models.Model):

    _inherit = "product.product"

    isroom = fields.Boolean('Is Room')
    iscategid = fields.Boolean('Is categ id')
    isservice = fields.Boolean('Is Service id')


class HotelRoomAmenitiesType(models.Model):

    _name = 'hotel.room.amenities.type'
    _description = 'amenities Type'

    cat_id = fields.Many2one('product.category', 'category', required=True,
                             delegate=True, ondelete='cascade')


class HotelRoomAmenities(models.Model):

    _name = 'hotel.room.amenities'
    _description = 'Room amenities'

    room_categ_id = fields.Many2one('product.product', 'Product Category',
                                    required=True, delegate=True,
                                    ondelete='cascade')
    rcateg_id = fields.Many2one('hotel.room.amenities.type',
                                'Amenity Catagory')

    product_manager = fields.Many2one('res.users', string='Product Manager')


class FolioRoomLine(models.Model):

    _name = 'folio.room.line'
    _description = 'Hotel Room Reservation'
    _rec_name = 'room_id'

    room_id = fields.Many2one(comodel_name='hotel.room', string='Room id')
    check_in = fields.Datetime('Check In Date', required=True)
    check_out = fields.Datetime('Check Out Date', required=True)
    folio_id = fields.Many2one('hotel.folio', string='Folio Number')
    status = fields.Selection(string='state', related='folio_id.state')


class HotelRoom(models.Model):

    _name = 'hotel.room'
    _description = 'Hotel Room'

    product_id = fields.Many2one('product.product', 'Product_id',
                                 required=True, delegate=True,
                                 ondelete='cascade')
    floor_id = fields.Many2one('hotel.floor', 'Floor No',
                               help='At which floor the room is located.')
    max_adult = fields.Integer('Max Adult')
    max_child = fields.Integer('Max Child')
    room_amenities = fields.Many2many('hotel.room.amenities', 'temp_tab',
                                      'room_amenities', 'rcateg_id',
                                      string='Room Amenities',
                                      help='List of room amenities. ')
    status = fields.Selection([('available', 'Available'),
                               ('occupied', 'Occupied')],
                              'Status', default='available')
    capacity = fields.Integer('Capacity')
    room_line_ids = fields.One2many('folio.room.line', 'room_id',
                                    string='Room Reservation Line')
    product_manager = fields.Many2one('res.users', string='Product Manager')

    @api.onchange('isroom')
    def isroom_change(self):
        '''
        Based on isroom, status will be updated.
        ----------------------------------------
        @param self: object pointer
        '''
        if self.isroom is False:
            self.status = 'occupied'
        if self.isroom is True:
            self.status = 'available'

    @api.multi
    def write(self, vals):
        """
        Overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if 'isroom' in vals and vals['isroom'] is False:
            vals.update({'color': 2, 'status': 'occupied'})
        if 'isroom'in vals and vals['isroom'] is True:
            vals.update({'color': 5, 'status': 'available'})
        ret_val = super(HotelRoom, self).write(vals)
        return ret_val

    @api.multi
    def set_room_status_occupied(self):
        """
        This method is used to change the state
        to occupied of the hotel room.
        ---------------------------------------
        @param self: object pointer
        """
        return self.write({'isroom': False, 'color': 2})

    @api.multi
    def set_room_status_available(self):
        """
        This method is used to change the state
        to available of the hotel room.
        ---------------------------------------
        @param self: object pointer
        """
        return self.write({'isroom': True, 'color': 5})


class HotelFolio(models.Model):

    @api.multi
    def name_get(self):
        res = []
        disp = ''
        for rec in self:
            if rec.order_id:
                disp = str(rec.name)
                res.append((rec.id, disp))
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        args += ([('name', operator, name)])
        mids = self.search(args, limit=100)
        return mids.name_get()

    @api.model
    def _needaction_count(self, domain=None):
        """
         Show a count of draft state folio on the menu badge.
         @param self: object pointer
        """
        return self.search_count([('state', '=', 'draft')])

    @api.model
    def _get_checkin_date(self):
        if self._context.get('tz'):
            to_zone = self._context.get('tz')
        else:
            to_zone = 'UTC'
        return _offset_format_timestamp1(time.strftime("%Y-%m-%d 12:00:00"),
                                         '%Y-%m-%d %H:%M:%S',
                                         '%Y-%m-%d %H:%M:%S',
                                         ignore_unparsable_time=True,
                                         context={'tz': to_zone})

    @api.model
    def _get_checkout_date(self):
        if self._context.get('tz'):
            to_zone = self._context.get('tz')
        else:
            to_zone = 'UTC'
        tm_delta = datetime.timedelta(days=1)
        return datetime.datetime.strptime(_offset_format_timestamp1
                                          (time.strftime("%Y-%m-%d 12:00:00"),
                                           '%Y-%m-%d %H:%M:%S',
                                           '%Y-%m-%d %H:%M:%S',
                                           ignore_unparsable_time=True,
                                           context={'tz': to_zone}),
                                          '%Y-%m-%d %H:%M:%S') + tm_delta

    @api.multi
    def copy(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''
        return super(HotelFolio, self).copy(default=default)

    @api.multi
    def _invoiced(self, name, arg):
        '''
        @param self: object pointer
        @param name: Names of fields.
        @param arg: User defined arguments
        '''
        return self.env['sale.order']._invoiced(name, arg)

    @api.multi
    def _invoiced_search(self, obj, name, args):
        '''
        @param self: object pointer
        @param name: Names of fields.
        @param arg: User defined arguments
        '''
        return self.env['sale.order']._invoiced_search(obj, name, args)

    _name = 'hotel.folio'
    _description = 'hotel folio new'
    _rec_name = 'order_id'
    _order = 'id'
    _inherit = ['ir.needaction_mixin']

    name = fields.Char('Folio Number', readonly=True, index=True,
                       default='New')
    order_id = fields.Many2one('sale.order', 'Order', delegate=True,
                               required=True, ondelete='cascade')
    checkin_date = fields.Datetime('Check In', required=True, readonly=True,
                                   states={'draft': [('readonly', False)]},
                                   default=_get_checkin_date)
    checkout_date = fields.Datetime('Check Out', required=True, readonly=True,
                                    states={'draft': [('readonly', False)]},
                                    default=_get_checkout_date)
    room_lines = fields.One2many('hotel.folio.line', 'folio_id',
                                 readonly=True,
                                 states={'draft': [('readonly', False)],
                                         'sent': [('readonly', False)]},
                                 help="Hotel room reservation detail.")
    service_lines = fields.One2many('hotel.service.line', 'folio_id',
                                    readonly=True,
                                    states={'draft': [('readonly', False)],
                                            'sent': [('readonly', False)]},
                                    help="Hotel services detail provide to"
                                    "customer and it will include in "
                                    "main Invoice.")
    hotel_policy = fields.Selection([('prepaid', 'On Booking'),
                                     ('manual', 'On Check In'),
                                     ('picking', 'On Checkout')],
                                    'Hotel Policy', default='manual',
                                    help="Hotel policy for payment that "
                                    "either the guest has to payment at "
                                    "booking time or check-in "
                                    "check-out time.")
    duration = fields.Float('Duration in Days',
                            help="Number of days which will automatically "
                            "count from the check-in and check-out date. ")
    currrency_ids = fields.One2many('currency.exchange', 'folio_no',
                                    readonly=True)
    hotel_invoice_id = fields.Many2one('account.invoice', 'Invoice')

    @api.multi
    def go_to_currency_exchange(self):
        '''
         when Money Exchange button is clicked then this method is called.
        -------------------------------------------------------------------
        @param self: object pointer
        '''
        cr, uid, context = self.env.args
        context = dict(context)
        for rec in self:
            if rec.partner_id.id and len(rec.room_lines) != 0:
                context.update({'folioid': rec.id, 'guest': rec.partner_id.id,
                                'room_no': rec.room_lines[0].product_id.name,
                                'hotel': rec.warehouse_id.id})
                self.env.args = cr, uid, misc.frozendict(context)
            else:
                raise except_orm(_('Warning'), _('Please Reserve Any Room.'))
        return {'name': _('Currency Exchange'),
                'res_model': 'currency.exchange',
                'type': 'ir.actions.act_window',
                'view_id': False,
                'view_mode': 'form,tree',
                'view_type': 'form',
                'context': {'default_folio_no': context.get('folioid'),
                            'default_hotel_id': context.get('hotel'),
                            'default_guest_name': context.get('guest'),
                            'default_room_number': context.get('room_no')
                            },
                }

    @api.constrains('room_lines')
    def folio_room_lines(self):
        '''
        This method is used to validate the room_lines.
        ------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        folio_rooms = []
        for room in self[0].room_lines:
            if room.product_id.id in folio_rooms:
                raise ValidationError(_('You Cannot Take Same Room Twice'))
            folio_rooms.append(room.product_id.id)

    @api.constrains('checkin_date', 'checkout_date')
    def check_dates(self):
        '''
        This method is used to validate the checkin_date and checkout_date.
        -------------------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        if self.checkin_date >= self.checkout_date:
                raise ValidationError(_('Check in Date Should be \
                less than the Check Out Date!'))
        if self.date_order and self.checkin_date:
            if self.checkin_date < self.date_order:
                raise ValidationError(_('Check in date should be \
                greater than the current date.'))

    @api.onchange('checkout_date', 'checkin_date')
    def onchange_dates(self):
        '''
        This mathod gives the duration between check in and checkout
        if customer will leave only for some hour it would be considers
        as a whole day.If customer will check in checkout for more or equal
        hours, which configured in company as additional hours than it would
        be consider as full days
        --------------------------------------------------------------------
        @param self: object pointer
        @return: Duration and checkout_date
        '''
        company_obj = self.env['res.company']
        configured_addition_hours = 0
        company_ids = company_obj.search([])
        if company_ids.ids:
            configured_addition_hours = company_ids[0].additional_hours
        myduration = 0
        chckin = self.checkin_date
        chckout = self.checkout_date
        if chckin and chckout:
            server_dt = DEFAULT_SERVER_DATETIME_FORMAT
            chkin_dt = datetime.datetime.strptime(chckin, server_dt)
            chkout_dt = datetime.datetime.strptime(chckout, server_dt)
            dur = chkout_dt - chkin_dt
            sec_dur = dur.seconds
            if (not dur.days and not sec_dur) or (dur.days and not sec_dur):
                myduration = dur.days
            else:
                myduration = dur.days + 1
            if configured_addition_hours > 0:
                additional_hours = abs((dur.seconds / 60) / 60)
                if additional_hours >= configured_addition_hours:
                    myduration += 1
        self.duration = myduration

    @api.model
    def create(self, vals, check=True):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for hotel folio.
        """
        if not 'service_lines' and 'folio_id' in vals:
            tmp_room_lines = vals.get('room_lines', [])
            vals['order_policy'] = vals.get('hotel_policy', 'manual')
            vals.update({'room_lines': []})
            folio_id = super(HotelFolio, self).create(vals)
            for line in (tmp_room_lines):
                line[2].update({'folio_id': folio_id})
            vals.update({'room_lines': tmp_room_lines})
            folio_id.write(vals)
        else:
            if not vals:
                vals = {}
            vals['name'] = self.env['ir.sequence'].next_by_code('hotel.folio')
            folio_id = super(HotelFolio, self).create(vals)
            folio_room_line_obj = self.env['folio.room.line']
            h_room_obj = self.env['hotel.room']
            try:
                for rec in folio_id:
                    if not rec.reservation_id:
                        for room_rec in rec.room_lines:
                            prod = room_rec.product_id.name
                            room_obj = h_room_obj.search([('name', '=', prod)])
                            room_obj.write({'isroom': False})
                            vals = {'room_id': room_obj.id,
                                    'check_in': rec.checkin_date,
                                    'check_out': rec.checkout_date,
                                    'folio_id': rec.id,
                                    }
                            folio_room_line_obj.create(vals)
            except:
                for rec in folio_id:
                    for room_rec in rec.room_lines:
                        prod = room_rec.product_id.name
                        room_obj = h_room_obj.search([('name', '=', prod)])
                        room_obj.write({'isroom': False})
                        vals = {'room_id': room_obj.id,
                                'check_in': rec.checkin_date,
                                'check_out': rec.checkout_date,
                                'folio_id': rec.id,
                                }
                        folio_room_line_obj.create(vals)
        return folio_id

    @api.multi
    def write(self, vals):
        """
        Overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        folio_room_line_obj = self.env['folio.room.line']
        reservation_line_obj = self.env['hotel.room.reservation.line']
        product_obj = self.env['product.product']
        h_room_obj = self.env['hotel.room']
        room_lst1 = []
        for rec in self:
            for res in rec.room_lines:
                room_lst1.append(res.product_id.id)
        folio_write = super(HotelFolio, self).write(vals)
        room_lst = []
        for folio_obj in self:
            for folio_rec in folio_obj.room_lines:
                room_lst.append(folio_rec.product_id.id)
            new_rooms = set(room_lst).difference(set(room_lst1))
            if len(list(new_rooms)) != 0:
                room_list = product_obj.browse(list(new_rooms))
                for rm in room_list:
                    room_obj = h_room_obj.search([('name', '=', rm.name)])
                    room_obj.write({'isroom': False})
                    vals = {'room_id': room_obj.id,
                            'check_in': folio_obj.checkin_date,
                            'check_out': folio_obj.checkout_date,
                            'folio_id': folio_obj.id,
                            }
                    folio_room_line_obj.create(vals)
            if len(list(new_rooms)) == 0:
                room_list_obj = product_obj.browse(room_lst1)
                for rom in room_list_obj:
                    room_obj = h_room_obj.search([('name', '=', rom.name)])
                    room_obj.write({'isroom': False})
                    room_vals = {'room_id': room_obj.id,
                                 'check_in': folio_obj.checkin_date,
                                 'check_out': folio_obj.checkout_date,
                                 'folio_id': folio_obj.id,
                                 }
                    folio_romline_rec = (folio_room_line_obj.search
                                         ([('folio_id', '=', folio_obj.id)]))
                    folio_romline_rec.write(room_vals)
            if folio_obj.reservation_id:
                for reservation in folio_obj.reservation_id:
                    reservation_obj = (reservation_line_obj.search
                                       ([('reservation_id', '=',
                                          reservation.id)]))
                    if len(reservation_obj) == 1:
                        for line_id in reservation.reservation_line:
                            line_id = line_id.reserve
                            for room_id in line_id:
                                vals = {'room_id': room_id.id,
                                        'check_in': folio_obj.checkin_date,
                                        'check_out': folio_obj.checkout_date,
                                        'state': 'assigned',
                                        'reservation_id': reservation.id,
                                        }
                                reservation_obj.write(vals)
        return folio_write

    @api.onchange('warehouse_id')
    def onchange_warehouse_id(self):
        '''
        When you change warehouse it will update the warehouse of
        the hotel folio as well
        ----------------------------------------------------------
        @param self: object pointer
        '''
        return self.order_id._onchange_warehouse_id()

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        '''
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel folio as well
        ---------------------------------------------------------------
        @param self: object pointer
        '''
        if self.partner_id:
            partner_rec = self.env['res.partner'].browse(self.partner_id.id)
            order_ids = [folio.order_id.id for folio in self]
            if not order_ids:
                self.partner_invoice_id = partner_rec.id
                self.partner_shipping_id = partner_rec.id
                self.pricelist_id = partner_rec.property_product_pricelist.id
                raise _('Not Any Order For  %s ' % (partner_rec.name))
            else:
                self.partner_invoice_id = partner_rec.id
                self.partner_shipping_id = partner_rec.id
                self.pricelist_id = partner_rec.property_product_pricelist.id

    @api.multi
    def button_dummy(self):
        '''
        @param self: object pointer
        '''
        for folio in self:
            folio.order_id.button_dummy()
        return True

    @api.multi
    def action_done(self):
        self.write({'state': 'done'})

    @api.multi
    def action_invoice_create(self, grouped=False, states=None):
        '''
        @param self: object pointer
        '''
        if states is None:
            states = ['confirmed', 'done']
        order_ids = [folio.order_id.id for folio in self]
        room_lst = []
        sale_obj = self.env['sale.order'].browse(order_ids)
        invoice_id = (sale_obj.action_invoice_create
                      (grouped=False, states=['confirmed', 'done']))
        for line in self:
            values = {'invoiced': True,
                      'state': 'progress' if grouped else 'progress',
                      'hotel_invoice_id': invoice_id
                      }
            line.write(values)
            for rec in line.room_lines:
                room_lst.append(rec.product_id)
            for room in room_lst:
                room_obj = self.env['hotel.room'
                                    ].search([('name', '=', room.name)])
                room_obj.write({'isroom': True})
        return invoice_id

    @api.multi
    def action_invoice_cancel(self):
        '''
        @param self: object pointer
        '''
        order_ids = [folio.order_id.id for folio in self]
        sale_obj = self.env['sale.order'].browse(order_ids)
        res = sale_obj.action_invoice_cancel()
        for sale in self:
            for line in sale.order_line:
                line.write({'invoiced': 'invoiced'})
        sale.write({'state': 'invoice_except'})
        return res

    @api.multi
    def action_cancel(self):
        '''
        @param self: object pointer
        '''
        order_ids = [folio.order_id.id for folio in self]
        sale_obj = self.env['sale.order'].browse(order_ids)
        rv = sale_obj.action_cancel()
        for sale in self:
            for pick in sale.picking_ids:
                workflow.trg_validate(self._uid, 'stock.picking', pick.id,
                                      'button_cancel', self._cr)
            for invoice in sale.invoice_ids:
                workflow.trg_validate(self._uid, 'account.invoice',
                                      invoice.id, 'invoice_cancel',
                                      self._cr)
                sale.write({'state': 'cancel'})
        return rv

    @api.multi
    def action_confirm(self):
        for order in self.order_id:
            order.state = 'sale'
            order.order_line._action_procurement_create()
            if not order.project_id:
                for line in order.order_line:
                    if line.product_id.invoice_policy == 'cost':
                        order._create_analytic_account()
                        break
        if self.env['ir.values'].get_default('sale.config.settings',
                                             'auto_done_setting'):
            self.order_id.action_done()

    @api.multi
    def test_state(self, mode):
        '''
        @param self: object pointer
        @param mode: state of workflow
        '''
        write_done_ids = []
        write_cancel_ids = []
        if write_done_ids:
            test_obj = self.env['sale.order.line'].browse(write_done_ids)
            test_obj.write({'state': 'done'})
        if write_cancel_ids:
            test_obj = self.env['sale.order.line'].browse(write_cancel_ids)
            test_obj.write({'state': 'cancel'})

    @api.multi
    def action_ship_create(self):
        '''
        @param self: object pointer
        '''
        for folio in self:
            folio.order_id.action_ship_create()
        return True

    @api.multi
    def action_ship_end(self):
        '''
        @param self: object pointer
        '''
        for order in self:
            order.write({'shipped': True})

    @api.multi
    def has_stockable_products(self):
        '''
        @param self: object pointer
        '''
        for folio in self:
            folio.order_id.has_stockable_products()
        return True

    @api.multi
    def action_cancel_draft(self):
        '''
        @param self: object pointer
        '''
        if not len(self._ids):
            return False
        query = "select id from sale_order_line \
        where order_id IN %s and state=%s"
        self._cr.execute(query, (tuple(self._ids), 'cancel'))
        cr1 = self._cr
        line_ids = map(lambda x: x[0], cr1.fetchall())
        self.write({'state': 'draft', 'invoice_ids': [], 'shipped': 0})
        sale_line_obj = self.env['sale.order.line'].browse(line_ids)
        sale_line_obj.write({'invoiced': False, 'state': 'draft',
                             'invoice_lines': [(6, 0, [])]})
        return True


class HotelFolioLine(models.Model):

    @api.multi
    def copy(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''
        return super(HotelFolioLine, self).copy(default=default)

    @api.multi
    def _amount_line(self, field_name, arg):
        '''
        @param self: object pointer
        @param field_name: Names of fields.
        @param arg: User defined arguments
        '''
        return self.env['sale.order.line']._amount_line(field_name, arg)

    @api.multi
    def _number_packages(self, field_name, arg):
        '''
        @param self: object pointer
        @param field_name: Names of fields.
        @param arg: User defined arguments
        '''
        return self.env['sale.order.line']._number_packages(field_name, arg)

    @api.model
    def _get_checkin_date(self):
        if 'checkin' in self._context:
            return self._context['checkin']
        return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _get_checkout_date(self):
        if 'checkout' in self._context:
            return self._context['checkout']
        return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

#   def _get_uom_id(self):
#       try:
#           proxy = self.pool.get('ir.model.data')
#           result = proxy.get_object_reference(self._cr, self._uid,
#              'product','product_uom_unit')
#           return result[1]
#       except Exception:
#           return False

    _name = 'hotel.folio.line'
    _description = 'hotel folio1 room line'

    order_line_id = fields.Many2one('sale.order.line', string='Order Line',
                                    required=True, delegate=True,
                                    ondelete='cascade')
    folio_id = fields.Many2one('hotel.folio', string='Folio',
                               ondelete='cascade')
    checkin_date = fields.Datetime('Check In', required=True,
                                   default=_get_checkin_date)
    checkout_date = fields.Datetime('Check Out', required=True,
                                    default=_get_checkout_date)
    is_reserved = fields.Boolean('Is Reserved',
                                 help='True when folio line created from \
                                 Reservation')
#   product_uom = fields.Many2one('product.uom',string='Unit of Measure',
#                                  required=True, default=_get_uom_id)

    @api.model
    def create(self, vals, check=True):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for hotel folio line.
        """
        if 'folio_id' in vals:
            folio = self.env["hotel.folio"].browse(vals['folio_id'])
            vals.update({'order_id': folio.order_id.id})
        return super(HotelFolioLine, self).create(vals)

    @api.constrains('checkin_date', 'checkout_date')
    def check_dates(self):
        '''
        This method is used to validate the checkin_date and checkout_date.
        -------------------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        if self.checkin_date >= self.checkout_date:
                raise ValidationError(_('Room line Check In Date Should be \
                less than the Check Out Date!'))
        if self.folio_id.date_order and self.checkin_date:
            if self.checkin_date <= self.folio_id.date_order:
                raise ValidationError(_('Room line check in date should be \
                greater than the current date.'))

    @api.multi
    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        sale_line_obj = self.env['sale.order.line']
        fr_obj = self.env['folio.room.line']
        for line in self:
            if line.order_line_id:
                sale_unlink_obj = (sale_line_obj.browse
                                   ([line.order_line_id.id]))
                for rec in sale_unlink_obj:
                    room_obj = self.env['hotel.room'
                                        ].search([('name', '=', rec.name)])
                    if room_obj.id:
                        folio_arg = [('folio_id', '=', line.folio_id.id),
                                     ('room_id', '=', room_obj.id)]
                        folio_room_line_myobj = fr_obj.search(folio_arg)
                        if folio_room_line_myobj.id:
                            folio_room_line_myobj.unlink()
                            room_obj.write({'isroom': True,
                                            'status': 'available'})
                sale_unlink_obj.unlink()
        return super(HotelFolioLine, self).unlink()

#    @api.multi
#    def uos_change(self, product_uos, product_uos_qty=0, product_id=None):
#         '''
#             @param self: object pointer
#         '''
#         for folio in self:
#             line = folio.order_line_id
#             line.uos_change(product_uos, product_uos_qty=0,
#                             product_id=None)
#         return True

    @api.onchange('product_id')
    def product_id_change(self):
        if self.product_id and self.folio_id.partner_id:
            self.name = self.product_id.name
            self.price_unit = self.product_id.lst_price
            self.product_uom = self.product_id.uom_id
            tax_obj = self.env['account.tax']
            prod = self.product_id
            self.price_unit = tax_obj._fix_tax_included_price(prod.price,
                                                              prod.taxes_id,
                                                              self.tax_id)

    @api.onchange('product_uom')
    def product_uom_change(self):
        if not self.product_uom:
            self.price_unit = 0.0
            return
        self.price_unit = self.product_id.lst_price
        if self.folio_id.partner_id:
            prod = self.product_id.with_context(
                lang=self.folio_id.partner_id.lang,
                partner=self.folio_id.partner_id.id,
                quantity=1,
                date_order=self.folio_id.checkin_date,
                pricelist=self.folio_id.pricelist_id.id,
                uom=self.product_uom.id
            )
            tax_obj = self.env['account.tax']
            self.price_unit = tax_obj._fix_tax_included_price(prod.price,
                                                              prod.taxes_id,
                                                              self.tax_id)

    @api.onchange('checkin_date', 'checkout_date')
    def on_change_checkout(self):
        '''
        When you change checkin_date or checkout_date it will checked it
        and update the qty of hotel folio line
        -----------------------------------------------------------------
        @param self: object pointer
        '''
        if not self.checkin_date:
            self.checkin_date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if not self.checkout_date:
            self.checkout_date = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        chckin = self.checkin_date
        chckout = self.checkout_date
        if chckin and chckout:
            server_dt = DEFAULT_SERVER_DATETIME_FORMAT
            chkin_dt = datetime.datetime.strptime(chckin, server_dt)
            chkout_dt = datetime.datetime.strptime(chckout, server_dt)
            dur = chkout_dt - chkin_dt
            sec_dur = dur.seconds
            if (not dur.days and not sec_dur) or (dur.days and not sec_dur):
                myduration = dur.days
            else:
                myduration = dur.days + 1
        self.product_uom_qty = myduration

    @api.multi
    def button_confirm(self):
        '''
        @param self: object pointer
        '''
        for folio in self:
            line = folio.order_line_id
            line.button_confirm()
        return True

    @api.multi
    def button_done(self):
        '''
        @param self: object pointer
        '''
        lines = [folio_line.order_line_id for folio_line in self]
        lines.button_done()
        self.write({'state': 'done'})
        for folio_line in self:
            workflow.trg_write(self._uid, 'sale.order',
                               folio_line.order_line_id.order_id.id,
                               self._cr)
        return True

    @api.multi
    def copy_data(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''
        line_id = self.order_line_id.id
        sale_line_obj = self.env['sale.order.line'].browse(line_id)
        return sale_line_obj.copy_data(default=default)


class HotelServiceLine(models.Model):

    @api.multi
    def copy(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''
        return super(HotelServiceLine, self).copy(default=default)

    @api.multi
    def _amount_line(self, field_name, arg):
        '''
        @param self: object pointer
        @param field_name: Names of fields.
        @param arg: User defined arguments
        '''
        for folio in self:
            line = folio.service_line_id
            x = line._amount_line(field_name, arg)
        return x

    @api.multi
    def _number_packages(self, field_name, arg):
        '''
        @param self: object pointer
        @param field_name: Names of fields.
        @param arg: User defined arguments
        '''
        for folio in self:
            line = folio.service_line_id
            x = line._number_packages(field_name, arg)
        return x

    @api.model
    def _service_checkin_date(self):
        if 'checkin' in self._context:
            return self._context['checkin']
        return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _service_checkout_date(self):
        if 'checkout' in self._context:
            return self._context['checkout']
        return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    _name = 'hotel.service.line'
    _description = 'hotel Service line'

    service_line_id = fields.Many2one('sale.order.line', 'Service Line',
                                      required=True, delegate=True,
                                      ondelete='cascade')
    folio_id = fields.Many2one('hotel.folio', 'Folio', ondelete='cascade')
    ser_checkin_date = fields.Datetime('From Date', required=True,
                                       default=_service_checkin_date)
    ser_checkout_date = fields.Datetime('To Date', required=True,
                                        default=_service_checkout_date)

    @api.model
    def create(self, vals, check=True):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for hotel service line.
        """
        if 'folio_id' in vals:
            folio = self.env['hotel.folio'].browse(vals['folio_id'])
            vals.update({'order_id': folio.order_id.id})
        return super(HotelServiceLine, self).create(vals)

    @api.multi
    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        s_line_obj = self.env['sale.order.line']
        for line in self:
            if line.service_line_id:
                sale_unlink_obj = s_line_obj.browse([line.service_line_id.id])
                sale_unlink_obj.unlink()
        return super(HotelServiceLine, self).unlink()

    @api.onchange('product_id')
    def product_id_change(self):
        '''
        @param self: object pointer
        '''
        if self.product_id and self.folio_id.partner_id:
            self.name = self.product_id.name
            self.price_unit = self.product_id.lst_price
            self.product_uom = self.product_id.uom_id
            tax_obj = self.env['account.tax']
            prod = self.product_id
            self.price_unit = tax_obj._fix_tax_included_price(prod.price,
                                                              prod.taxes_id,
                                                              self.tax_id)

    @api.onchange('product_uom')
    def product_uom_change(self):
        '''
        @param self: object pointer
        '''
        if not self.product_uom:
            self.price_unit = 0.0
            return
        self.price_unit = self.product_id.lst_price
        if self.folio_id.partner_id:
            prod = self.product_id.with_context(
                lang=self.folio_id.partner_id.lang,
                partner=self.folio_id.partner_id.id,
                quantity=1,
                date_order=self.folio_id.checkin_date,
                pricelist=self.folio_id.pricelist_id.id,
                uom=self.product_uom.id
            )
            tax_obj = self.env['account.tax']
            self.price_unit = tax_obj._fix_tax_included_price(prod.price,
                                                              prod.taxes_id,
                                                              self.tax_id)

    @api.onchange('ser_checkin_date', 'ser_checkout_date')
    def on_change_checkout(self):
        '''
        When you change checkin_date or checkout_date it will checked it
        and update the qty of hotel service line
        -----------------------------------------------------------------
        @param self: object pointer
        '''
        if not self.ser_checkin_date:
            time_a = time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            self.ser_checkin_date = time_a
        if not self.ser_checkout_date:
            self.ser_checkout_date = time_a
        if self.ser_checkout_date < self.ser_checkin_date:
            raise _('Checkout must be greater or equal checkin date')
        if self.ser_checkin_date and self.ser_checkout_date:
            date_a = time.strptime(self.ser_checkout_date,
                                   DEFAULT_SERVER_DATETIME_FORMAT)[:5]
            date_b = time.strptime(self.ser_checkin_date,
                                   DEFAULT_SERVER_DATETIME_FORMAT)[:5]
            diffDate = datetime.datetime(*date_a) - datetime.datetime(*date_b)
            qty = diffDate.days + 1
            self.product_uom_qty = qty

    @api.multi
    def button_confirm(self):
        '''
        @param self: object pointer
        '''
        for folio in self:
            line = folio.service_line_id
            x = line.button_confirm()
        return x

    @api.multi
    def button_done(self):
        '''
        @param self: object pointer
        '''
        for folio in self:
            line = folio.service_line_id
            x = line.button_done()
        return x

    @api.multi
    def copy_data(self, default=None):
        '''
        @param self: object pointer
        @param default: dict of default values to be set
        '''
        sale_line_obj = self.env['sale.order.line'
                                 ].browse(self.service_line_id.id)
        return sale_line_obj.copy_data(default=default)


class HotelServiceType(models.Model):

    _name = "hotel.service.type"
    _description = "Service Type"

    ser_id = fields.Many2one('product.category', 'category', required=True,
                             delegate=True, select=True, ondelete='cascade')


class HotelServices(models.Model):

    _name = 'hotel.services'
    _description = 'Hotel Services and its charges'

    service_id = fields.Many2one('product.product', 'Service_id',
                                 required=True, ondelete='cascade',
                                 delegate=True)
    product_manager = fields.Many2one('res.users', string='Product Manager')


class ResCompany(models.Model):

    _inherit = 'res.company'

    additional_hours = fields.Integer('Additional Hours',
                                      help="Provide the min hours value for \
check in, checkout days, whatever the hours will be provided here based \
on that extra days will be calculated.")


class CurrencyExchangeRate(models.Model):

    _name = "currency.exchange"
    _description = "currency"

    name = fields.Char('Reg Number', readonly=True, default='New')
    today_date = fields.Datetime('Date Ordered',
                                 required=True,
                                 default=(lambda *a:
                                          time.strftime
                                          (DEFAULT_SERVER_DATETIME_FORMAT)))
    input_curr = fields.Many2one('res.currency', string='Input Currency',
                                 track_visibility='always')
    in_amount = fields.Float('Amount Taken', size=64, default=1.0)
    out_curr = fields.Many2one('res.currency', string='Output Currency',
                               track_visibility='always')
    out_amount = fields.Float('Subtotal', size=64)
    folio_no = fields.Many2one('hotel.folio', 'Folio Number')
    guest_name = fields.Many2one('res.partner', string='Guest Name')
    room_number = fields.Char(string='Room Number')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'),
                              ('cancel', 'Cancel')], 'State', default='draft')
    rate = fields.Float('Rate(per unit)', size=64)
    hotel_id = fields.Many2one('stock.warehouse', 'Hotel Name')
    type = fields.Selection([('cash', 'Cash')], 'Type', default='cash')
    tax = fields.Selection([('2', '2%'), ('5', '5%'), ('10', '10%')],
                           'Service Tax', default='2')
    total = fields.Float('Amount Given')

    @api.model
    def create(self, vals):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if not vals:
            vals = {}
        if self._context is None:
            self._context = {}
        seq_obj = self.env['ir.sequence']
        vals['name'] = seq_obj.next_by_code('currency.exchange') or 'New'
        return super(CurrencyExchangeRate, self).create(vals)

    @api.onchange('folio_no')
    def get_folio_no(self):
        '''
        When you change folio_no, based on that it will update
        the guest_name,hotel_id and room_number as well
        ---------------------------------------------------------
        @param self: object pointer
        '''
        for rec in self:
            self.guest_name = False
            self.hotel_id = False
            self.room_number = False
            if rec.folio_no and len(rec.folio_no.room_lines) != 0:
                self.guest_name = rec.folio_no.partner_id.id
                self.hotel_id = rec.folio_no.warehouse_id.id
                self.room_number = rec.folio_no.room_lines[0].product_id.name

    @api.multi
    def act_cur_done(self):
        """
        This method is used to change the state
        to done of the currency exchange
        ---------------------------------------
        @param self: object pointer
        """
        self.write({'state': 'done'})
        return True

    @api.multi
    def act_cur_cancel(self):
        """
        This method is used to change the state
        to cancel of the currency exchange
        ---------------------------------------
        @param self: object pointer
        """
        self.write({'state': 'cancel'})
        return True

    @api.multi
    def act_cur_cancel_draft(self):
        """
        This method is used to change the state
        to draft of the currency exchange
        ---------------------------------------
        @param self: object pointer
        """
        self.write({'state': 'draft'})
        return True

    @api.model
    def get_rate(self, a, b):
        '''
        Calculate rate between two currency
        -----------------------------------
        @param self: object pointer
        '''
        try:
            url = 'http://finance.yahoo.com/d/quotes.csv?s=%s%s=X&f=l1' % (a,
                                                                           b)
            rate = urllib2.urlopen(url).read().rstrip()
            return Decimal(rate)
        except:
            return Decimal('-1.00')

    @api.onchange('input_curr', 'out_curr', 'in_amount')
    def get_currency(self):
        '''
        When you change input_curr, out_curr or in_amount
        it will update the out_amount of the currency exchange
        ------------------------------------------------------
        @param self: object pointer
        '''
        self.out_amount = 0.0
        if self.input_curr:
            for rec in self:
                result = rec.get_rate(self.input_curr.name,
                                      self.out_curr.name)
                if self.out_curr:
                    self.rate = result
                    if self.rate == Decimal('-1.00'):
                        raise except_orm(_('Warning'),
                                         _('Please Check Your \
                                         Network Connectivity.'))
                    self.out_amount = (float(result) * float(self.in_amount))

    @api.onchange('out_amount', 'tax')
    def tax_change(self):
        '''
        When you change out_amount or tax
        it will update the total of the currency exchange
        -------------------------------------------------
        @param self: object pointer
        '''
        if self.out_amount:
            ser_tax = ((self.out_amount) * (float(self.tax))) / 100
            self.total = self.out_amount - ser_tax


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.multi
    def confirm_paid(self):
        '''
        This method change pos orders states to done when folio invoice
        is in done.
        ----------------------------------------------------------
        @param self: object pointer
        '''
        pos_order_obj = self.env['pos.order']
        res = super(AccountInvoice, self).confirm_paid()
        pos_odr_rec = pos_order_obj.search([('invoice_id', 'in', self._ids)])
        pos_odr_rec and pos_odr_rec.write({'state': 'done'})
        return res

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
from openerp.exceptions import except_orm, Warning
from openerp import models,fields,api,_
from openerp import netsvc
import datetime
import time

class hotel_floor(models.Model):

    _name = "hotel.floor"
    _description = "Floor"

    name = fields.Char('Floor Name', size=64, required=True, select=True)
    sequence = fields.Integer('Sequence', size=64)

class product_category(models.Model):

    _inherit = "product.category"

    isroomtype = fields.Boolean('Is Room Type')
    isamenitytype = fields.Boolean('Is Amenities Type')
    isservicetype = fields.Boolean('Is Service Type')


class hotel_room_type(models.Model):

    _name = "hotel.room.type"
    _description = "Room Type"

    cat_id = fields.Many2one('product.category','category', required=True, delegate=True, select=True, ondelete='cascade')

class product_product(models.Model):

    _inherit = "product.product"

    isroom = fields.Boolean('Is Room')
    iscategid = fields.Boolean('Is categ id')
    isservice = fields.Boolean('Is Service id')

class hotel_room_amenities_type(models.Model):

    _name = 'hotel.room.amenities.type'
    _description = 'amenities Type'

    cat_id = fields.Many2one('product.category','category', required=True, delegate=True, ondelete='cascade')

class hotel_room_amenities(models.Model):

    _name = 'hotel.room.amenities'
    _description = 'Room amenities'

    room_categ_id = fields.Many2one('product.product','Product Category' ,required=True, delegate=True, ondelete='cascade')
    rcateg_id = fields.Many2one('hotel.room.amenities.type','Amenity Catagory')

class hotel_room(models.Model):

    _name = 'hotel.room'
    _description = 'Hotel Room'

    product_id = fields.Many2one('product.product','Product_id' ,required=True, delegate=True, ondelete='cascade')
    floor_id = fields.Many2one('hotel.floor','Floor No',help='At which floor the room is located.')
    max_adult = fields.Integer('Max Adult')
    max_child = fields.Integer('Max Child')
    room_amenities = fields.Many2many('hotel.room.amenities','temp_tab','room_amenities','rcateg_id',string='Room Amenities',help='List of room amenities. ')
    status = fields.Selection([('available', 'Available'), ('occupied', 'Occupied')], 'Status',default='available')
    capacity = fields.Integer('Capacity')
    @api.multi
    def set_room_status_occupied(self):
        return self.write({'status': 'occupied'})

    @api.multi
    def set_room_status_available(self):
        return self.write({'status': 'available'})


class hotel_folio(models.Model):

    @api.multi
    def copy(self,default=None):
        '''
        @param self : object pointer
        @param default : dict of default values to be set
        '''
        return self.env['sale.order'].copy(default=default)

    @api.multi 
    def _invoiced(self, name, arg):
        '''
        @param self : object pointer
        @param name: Names of fields.
        @param arg: User defined arguments
        '''
        return self.env['sale.order']._invoiced(name, arg)

    @api.multi
    def _invoiced_search(self ,obj, name, args):
        '''
        @param self : object pointer
        @param name: Names of fields.
        @param arg: User defined arguments
        '''
        return self.env['sale.order']._invoiced_search(obj, name, args)

    _name = 'hotel.folio'
    _description = 'hotel folio new'
    _rec_name = 'order_id'
    _order = 'id desc'

    name = fields.Char('Folio Number', size=24,default=lambda obj: obj.env['ir.sequence'].get('hotel.folio'),readonly=True)
    order_id = fields.Many2one('sale.order','Order',  delegate=True, required=True, ondelete='cascade')
    checkin_date = fields.Datetime('Check In', required=True, readonly=True, states={'draft':[('readonly', False)]})
    checkout_date = fields.Datetime('Check Out', required=True, readonly=True, states={'draft':[('readonly', False)]})
    room_lines = fields.One2many('hotel.folio.line','folio_id', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Hotel room reservation detail.")
    service_lines = fields.One2many('hotel.service.line','folio_id', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Hotel services detail provide to customer and it will include in main Invoice.")
    hotel_policy = fields.Selection([('prepaid', 'On Booking'), ('manual', 'On Check In'), ('picking', 'On Checkout')], 'Hotel Policy',default='manual', help="Hotel policy for payment that either the guest has to payment at booking time or check-in check-out time.")
    duration = fields.Float('Duration in Days', help="Number of days which will automatically count from the check-in and check-out date. ")

    @api.constrains('checkin_date','checkout_date')
    def check_dates(self):
        '''
        This method is used to validate the checkin_date and checkout_date.
        -------------------------------------------------------------------
        @param self : object pointer
        @return : raise warning depending on the validation
        '''
        if self.checkin_date >= self.checkout_date:
                raise except_orm(_('Warning'),_('Check in Date Should be less than the Check Out Date!'))

    @api.constrains('room_lines')
    def check_folio_room_line(self):
        '''
        This method is used to validate the room_lines.
        ------------------------------------------------
        @param self : object pointer
        @return : raise warning depending on the validation
        '''
        folio_rooms = []
        for room in self[0].room_lines:
            if room.product_id.id in folio_rooms:
                raise except_orm(_('Warning'),_('You Cannot Take Same Room Twice'))
            folio_rooms.append(room.product_id.id)

    @api.onchange('checkout_date','checkin_date')
    def onchange_dates(self):
        '''
        This mathod gives the duration between check in checkout if customer will leave only for some
        hour it would be considers as a whole day. If customer will checkin checkout for more or equal
        hours , which configured in company as additional hours than it would be consider as full days
        ---------------------------------------------------------------------------------------------
        @param self : object pointer
        @return : Duration and checkout_date
        '''
        company_obj = self.env['res.company']
        configured_addition_hours = 0
        company_ids = company_obj.search([])
        if company_ids.ids:
            configured_addition_hours = company_ids[0].additional_hours
        myduration = 0 
        if self.checkin_date and self.checkout_date:
            chkin_dt = datetime.datetime.strptime(self.checkin_date, '%Y-%m-%d %H:%M:%S')
            chkout_dt = datetime.datetime.strptime(self.checkout_date, '%Y-%m-%d %H:%M:%S')
            dur = chkout_dt - chkin_dt
            myduration = dur.days
            if configured_addition_hours > 0:
                additional_hours = abs((dur.seconds / 60) / 60)
                if additional_hours >= configured_addition_hours:
                    myduration += 1
        self.duration = myduration

    @api.model
    def create(self, vals,check=True):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for hotel folio.
        """
        tmp_room_lines = vals.get('room_lines', [])
        vals['order_policy'] = vals.get('hotel_policy', 'manual')
        if not 'service_lines' and 'folio_id' in vals:
                vals.update({'room_lines':[]})
                folio_id = super(hotel_folio, self).create(vals)
                for line in (tmp_room_lines):
                    line[2].update({'folio_id':folio_id})
                vals.update({'room_lines':tmp_room_lines})
                folio_id.write(vals)
        else:
            folio_id = super(hotel_folio, self).create(vals)
        return folio_id


    @api.onchange('warehouse_id')
    def onchange_warehouse_id(self):
        '''
        When you change warehouse it will update the warehouse of
        the hotel folio as well
        ----------------------------------------------------------
        @param self : object pointer
        '''
        for folio in self:
            order = folio.order_id
            x = order.onchange_warehouse_id(folio.warehouse_id.id)
        return x


    @api.onchange('partner_id')
    def onchange_partner_id(self):
        '''
        When you change partner_id it will update the partner_invoice_id,
        partner_shipping_id and pricelist_id of the hotel folio as well
        ---------------------------------------------------------------
        @param self : object pointer
        '''
        if self.partner_id:
            partner_rec = self.env['res.partner'].browse(self.partner_id.id)
            order_ids = [folio.order_id.id for folio in self]
            if not order_ids:
                self.partner_invoice_id = partner_rec.id
                self.partner_shipping_id = partner_rec.id 
                self.pricelist_id = partner_rec.property_product_pricelist.id
                raise Warning('Not Any Order For  %s ' % (partner_rec.name))
            else:
                self.partner_invoice_id = partner_rec.id
                self.partner_shipping_id = partner_rec.id
                self.pricelist_id = partner_rec.property_product_pricelist.id

    @api.multi   
    def button_dummy(self):
        '''
        @param self : object pointer
        '''
        for folio in self:
            order = folio.order_id
            x = order.button_dummy()
        return x


    @api.multi
    def action_invoice_create(self,grouped=False, states=['confirmed', 'done']):
        '''
        @param self : object pointer
        '''
        order_ids = [folio.order_id.id for folio in self]
        sale_obj = self.env['sale.order'].browse(order_ids)
        invoice_id = sale_obj.action_invoice_create(grouped=False,states=['confirmed', 'done'])
        for line in self:
            values = {
                'invoiced': True,
                'state': 'progress' if grouped else 'progress',
            }
            line.write(values)
        return invoice_id


    @api.multi
    def action_invoice_cancel(self):
        '''
        @param self : object pointer
        '''
        order_ids = [folio.order_id.id for folio in self]
        sale_obj = self.env['sale.order'].browse(order_ids)
        res = sale_obj.action_invoice_cancel()
        for sale in self:
            for line in sale.order_line:
                line.write({'invoiced': 'invoiced'})
        sale.write({'state':'invoice_except'})
        return res

    @api.multi
    def action_cancel(self):
        '''
        @param self : object pointer
        '''
        order_ids = [folio.order_id.id for folio in self]
        sale_obj = self.env['sale.order'].browse(order_ids)
        rv = sale_obj.action_cancel()
        wf_service = netsvc.LocalService("workflow")
        for sale in self:
            for pick in sale.picking_ids:
               wf_service.trg_validate(self._uid, 'stock.picking', pick.id, 'button_cancel', self._cr)
            for invoice in sale.invoice_ids:
                wf_service.trg_validate(self._uid, 'account.invoice', invoice.id, 'invoice_cancel', self._cr)
                sale.write({'state':'cancel'})
        return rv

    @api.multi
    def action_wait(self):
        '''
        @param self : object pointer
        '''
        sale_order_obj = self.env['sale.order']
        res = False
        for o in self:
            sale_obj = sale_order_obj.browse([o.order_id.id])
            res = sale_obj.action_wait()
            if (o.order_policy == 'manual') and (not o.invoice_ids):
                o.write({'state': 'manual'})
            else:
                o.write({'state': 'progress'})
        return res


    @api.multi
    def test_state(self,mode):
        '''
        @param self : object pointer
        @param mode : state of workflow
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
        @param self : object pointer
        '''
        for folio in self:
            order = folio.order_id
            x = order.action_ship_create()
        return x

    @api.multi
    def action_ship_end(self):
        '''
        @param self : object pointer
        '''
        order_ids = [folio.order_id.id for folio in self]
        for order in self:
            order.write ({'shipped':True})

    @api.multi
    def has_stockable_products(self):
        '''
        @param self : object pointer
        '''
        for folio in self:
            order = folio.order_id
            x = order.has_stockable_products()
        return x

    @api.multi
    def action_cancel_draft(self):
        '''
        @param self : object pointer
        '''
        if not len(self._ids):
            return False
        query = "select id from sale_order_line where order_id IN %s and state=%s"
        self._cr.execute(query, (tuple(self._ids), 'cancel'))
        cr1 = self._cr
        line_ids = map(lambda x: x[0],cr1.fetchall())
        self.write({'state': 'draft', 'invoice_ids': [], 'shipped': 0})
        sale_line_obj = self.env['sale.order.line'].browse(line_ids)
        sale_line_obj.write({'invoiced': False, 'state': 'draft', 'invoice_lines': [(6, 0, [])]})
        wf_service = netsvc.LocalService("workflow")
        for inv_id in self._ids:
            # Deleting the existing instance of workflow for SO
            wf_service.trg_delete(self._uid,'sale.order', inv_id,self._cr)
            wf_service.trg_create(self._uid,'sale.order', inv_id,self._cr)
        for (id, name) in self.name_get():
            message = _("The sales order '%s' has been set in draft state.") % (name,)
            self.log(message)
        return True

class hotel_folio_line(models.Model):

    @api.one
    def copy(self,default=None):
        '''
        @param self : object pointer
        @param default : dict of default values to be set
        '''
        return self.env['sale.order.line'].copy(default=default)

    @api.multi
    def _amount_line(self,field_name, arg):
        '''
        @param self : object pointer
        @param field_name: Names of fields.
        @param arg: User defined arguments
        '''
        return self.env['sale.order.line']._amount_line(field_name, arg)

    @api.multi
    def _number_packages(self,field_name, arg):
        '''
        @param self : object pointer
        @param field_name: Names of fields.
        @param arg: User defined arguments
        '''
        return self.env['sale.order.line']._number_packages(field_name, arg)

    @api.model
    def _get_checkin_date(self):
        if 'checkin_date' in self._context:
            return self._context['checkin_date']
        return time.strftime('%Y-%m-%d %H:%M:%S')
#
    @api.model
    def _get_checkout_date(self):
        if 'checkin_date' in self._context:
            return self._context['checkout_date']
        return time.strftime('%Y-%m-%d %H:%M:%S')

    _name = 'hotel.folio.line'
    _description = 'hotel folio1 room line'

    order_line_id = fields.Many2one('sale.order.line',string='Order Line' ,required=True, delegate=True, ondelete='cascade')
    folio_id = fields.Many2one('hotel.folio',string='Folio', ondelete='cascade')
    checkin_date = fields.Datetime('Check In', required=True,default = _get_checkin_date)
    checkout_date = fields.Datetime('Check Out', required=True,default = _get_checkout_date)

    @api.model
    def create(self,vals,check=True):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for hotel folio line.
        """
        if 'folio_id' in vals:
            folio = self.env["hotel.folio"].browse(vals['folio_id'])
            vals.update({'order_id':folio.order_id.id})
        return super(models.Model, self).create(vals)


    @api.multi
    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        sale_line_obj = self.env['sale.order.line']
        for line in self:
            if line.order_line_id:
                sale_unlink_obj = sale_line_obj.browse([line.order_line_id.id])
                sale_unlink_obj.unlink()
        return super(hotel_folio_line, self).unlink()

    @api.multi
    def uos_change(self, product_uos, product_uos_qty=0, product_id=None):
        '''
        @param self : object pointer
        '''
        for folio in self:
            line = folio.order_line_id
            x = line.uos_change(product_uos, product_uos_qty=0, product_id=None)
        return x

    @api.multi
    def product_id_change(self,pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        '''
        @param self : object pointer
        '''
        line_ids = [folio.order_line_id.id for folio in self]
        if product:
            sale_line_obj = self.env['sale.order.line'].browse(line_ids)
            return sale_line_obj.product_id_change(pricelist, product, qty=0,
                uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
                lang=False, update_tax=True, date_order=False)

    @api.multi
    def product_uom_change(self, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        '''
        @param self : object pointer
        '''
        if product:
            return self.product_id_change(pricelist, product, qty=0,
                uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
                lang=False, update_tax=True, date_order=False)


    @api.onchange('checkin_date','checkout_date')
    def on_change_checkout(self):
        '''
        When you change checkin_date or checkout_date it will checked it
        and update the qty of hotel folio line
        -----------------------------------------------------------------
        @param self : object pointer
        '''
        if not self.checkin_date:
            self.checkin_date = time.strftime('%Y-%m-%d %H:%M:%S')
        if not self.checkout_date:
            self.checkout_date = time.strftime('%Y-%m-%d %H:%M:%S')
        qty = 1
        if self.checkout_date < self.checkin_date:
            raise except_orm(_('Warning'),_('Checkout must be greater or equal to checkin date'))
        if self.checkin_date:
            diffDate = datetime.datetime(*time.strptime(self.checkout_date, '%Y-%m-%d %H:%M:%S')[:5]) - datetime.datetime(*time.strptime(self.checkin_date, '%Y-%m-%d %H:%M:%S')[:5])
            qty = diffDate.days
            if qty == 0:
                qty = 1
        self.product_uom_qty = qty


    @api.multi
    def button_confirm(self):
        '''
        @param self : object pointer
        '''
        for folio in self:
            line = folio.order_line_id
            x = line.button_confirm()
        return x

    @api.multi
    def button_done(self):
        '''
        @param self : object pointer
        '''
        line_ids = [folio.order_line_id.id for folio in self]
        sale_line_obj = self.env['sale.order.line'].browse(line_ids)
        res = sale_line_obj.button_done()
        wf_service = netsvc.LocalService("workflow")
        res = self.write({'state':'done'})
        for line in self:
            wf_service.trg_write(self._uid, 'sale.order', line.order_line_id.order_id.id, self._cr)
        return res

    @api.one
    def copy_data(self,default=None):
        '''
        @param self : object pointer
        @param default : dict of default values to be set
        '''
        line_id = self.order_line_id.id 
        sale_line_obj = self.env['sale.order.line'].browse(line_id)
        return sale_line_obj.copy_data(default=default)


class hotel_service_line(models.Model):

    @api.one
    def copy(self, default=None):
        '''
        @param self : object pointer
        @param default : dict of default values to be set
        '''
        line_id = self.service_line_id.id
        sale_line_obj = self.env['sale.order.line'].browse(line_id)
        return sale_line_obj.copy(default=default)

    @api.multi
    def _amount_line(self,field_name, arg):
        '''
        @param self : object pointer
        @param field_name: Names of fields.
        @param arg: User defined arguments
        '''
        for folio in self:
            line = folio.service_line_id
            x = line._amount_line(field_name, arg)
        return x

    @api.multi
    def _number_packages(self,field_name, arg):
        '''
        @param self : object pointer
        @param field_name: Names of fields.
        @param arg: User defined arguments
        '''
        for folio in self:
            line = folio.service_line_id
            x = line._number_packages(field_name, arg)
        return x


    _name = 'hotel.service.line'
    _description = 'hotel Service line'
    
    service_line_id = fields.Many2one('sale.order.line','Service Line', required=True, delegate=True, ondelete='cascade')
    folio_id = fields.Many2one('hotel.folio','Folio',ondelete='cascade')

    @api.model
    def create(self,vals,check=True):
        """
        Overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        @return: new record set for hotel service line.
        """

        if 'folio_id' in vals:
            folio = self.env['hotel.folio'].browse(vals['folio_id'])
            vals.update({'order_id':folio.order_id.id})
        return super(models.Model, self).create(vals)

    @api.multi
    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: Tru/False.
        """
        sale_line_obj = self.env['sale.order.line']
        for line in self:
            if line.service_line_id:
                sale_unlink_obj = sale_line_obj.browse([line.service_line_id.id])
                sale_unlink_obj.unlink()
        return super(hotel_service_line, self).unlink()

    @api.multi
    def product_id_change(self,pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        '''
        @param self : object pointer
        '''
        line_ids = [folio.order_line_id.id for folio in self]
        if product:
            sale_line_obj = self.env['sale.order.line'].browse(line_ids)
            return sale_line_obj.product_id_change(pricelist, product, qty=0,
                uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
                lang=False, update_tax=True, date_order=False)


    @api.multi
    def product_uom_change(self, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False):
        '''
        @param self : object pointer
        '''
        if product:
            return self.product_id_change(pricelist, product, qty=0,
                uom=False, qty_uos=0, uos=False, name='', partner_id=partner_id,
                lang=False, update_tax=True, date_order=False)

    @api.onchange('checkin_date','checkout_date')
    def on_change_checkout(self):
        '''
        When you change checkin_date or checkout_date it will checked it
        and update the qty of hotel service line
        -----------------------------------------------------------------
        @param self : object pointer
        '''

        if not self.checkin_date:
            self.checkin_date = time.strftime('%Y-%m-%d %H:%M:%S')
        if not self.checkout_date:
            self.checkout_date = time.strftime('%Y-%m-%d %H:%M:%S')
        qty = 1
        if self.checkout_date < self.checkin_date:
            raise Warning('Checkout must be greater or equal checkin date')
        if self.checkin_date:
            diffDate = datetime.datetime(*time.strptime(self.checkout_date, '%Y-%m-%d %H:%M:%S')[:5]) - datetime.datetime(*time.strptime(self.checkin_date, '%Y-%m-%d %H:%M:%S')[:5])
            qty = diffDate.days
        self.product_uom_qty = qty

    @api.multi 
    def button_confirm(self):
        '''
        @param self : object pointer
        '''
        for folio in self:
            line = folio.service_line_id
            x = line.button_confirm()
        return x

    @api.multi
    def button_done(self):
        '''
        @param self : object pointer
        '''
        for folio in self:
            line = folio.service_line_id
            x = line.button_done()
        return x

    @api.one
    def copy_data(self,default=None):
        '''
        @param self : object pointer
        @param default : dict of default values to be set
        '''
        line_id = self.service_line_id.id
        sale_line_obj = self.env['sale.order.line'].browse(line_id)
        return sale_line_obj.copy_data(default=default)

class hotel_service_type(models.Model):

    _name = "hotel.service.type"
    _description = "Service Type"

    ser_id = fields.Many2one('product.category','category', required=True, delegate=True, select=True, ondelete='cascade')


class hotel_services(models.Model):

    _name = 'hotel.services'
    _description = 'Hotel Services and its charges'

    service_id = fields.Many2one('product.product','Service_id',required=True, ondelete='cascade', delegate=True)

class res_company(models.Model):

    _inherit = 'res.company'

    additional_hours = fields.Integer('Additional Hours', help="Provide the min hours value for check in, checkout days, whatever the hours will be provided here based on that extra days will be calculated.")

## vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

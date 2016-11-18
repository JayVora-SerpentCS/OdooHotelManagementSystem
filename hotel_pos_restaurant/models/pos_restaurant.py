# -*- coding: utf-8 -*-
#############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Serpent Consulting Services Pvt. Ltd.
#    (<http://www.serpentcs.com>)
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
#############################################################################

from odoo import models, fields, api


class HotelFolio(models.Model):

    _inherit = 'hotel.folio'
    _order = 'folio_pos_order_ids desc'

    folio_pos_order_ids = fields.Many2many('pos.order', 'hotel_pos_rel',
                                           'hotel_folio_id', 'pos_id',
                                           'Orders', readonly=True)

    @api.multi
    def action_invoice_create(self, grouped=False, states=None):
        state = ['confirmed', 'done']
        folio = super(HotelFolio)
        invoice_id = folio.action_invoice_create(grouped=False, states=state)
        for line in self:
            for pos_order in line.folio_pos_order_ids:
                pos_order.write({'invoice_id': invoice_id})
                pos_order.action_invoice_state()
        return invoice_id

    @api.multi
    def action_cancel(self):
        '''
        @param self: object pointer
        '''
        for folio in self:
            for rec in folio.folio_pos_order_ids:
                rec.write({'state': 'cancel'})
        return super(HotelFolio, self).action_cancel()


class PosOrder(models.Model):

    _inherit = "pos.order"

    folio_id = fields.Many2one('hotel.folio', 'Folio Number')
    room_no = fields.Char('Room Number')

    @api.onchange('folio_id')
    def get_folio_partner_id(self):
        '''
        When you change folio_id, based on that it will update
        the guest_name and room_no as well
        ---------------------------------------------------------
        @param self: object pointer
        '''
        for rec in self:
            self.partner_id = False
            self.room_no = False
            if rec.folio_id:
                self.partner_id = rec.folio_id.partner_id.id
                if rec.folio_id.room_lines:
                    self.room_no = rec.folio_id.room_lines[0].product_id.name

    @api.multi
    def action_paid(self):
        '''
        When pos order created this method called,and sale order line
        created for current folio
        --------------------------------------------------------------
        @param self: object pointer
        '''
        hotel_folio_obj = self.env['hotel.folio']
        hsl_obj = self.env['hotel.service.line']
        so_line_obj = self.env['sale.order.line']
        for order_obj in self:
                hotelfolio = order_obj.folio_id.order_id.id
                if order_obj.folio_id:
                    for order1 in order_obj.lines:
                        values = {'order_id': hotelfolio,
                                  'name': order1.product_id.name,
                                  'product_id': order1.product_id.id,
                                  'product_uom_qty': order1.qty,
                                  'price_unit': order1.price_unit,
                                  'price_subtotal': order1.price_subtotal,
                                  }
                        sol_rec = so_line_obj.create(values)
                        hsl_obj.create({'folio_id': order_obj.folio_id.id,
                                        'service_line_id': sol_rec.id})
                        hf_rec = hotel_folio_obj.browse(order_obj.folio_id.id)
                        hf_rec.write({'folio_pos_order_ids':
                                      [(4, order_obj.id)]})
        return super(PosOrder, self).action_paid()

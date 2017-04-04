# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _inherit = "pos.order"

    folio_id = fields.Many2one('hotel.folio', 'Folio Number')
    room_no = fields.Char('Room Number')

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        order_fields['folio_id'] = ui_order.get('folio_id',False)
        table_data = ui_order.get("table_data")
        if table_data:
            if ui_order.get('folio_id',False) :
                restaurant_table_obj = self.env['restaurant.table']
                restaurant_table_obj.sudo().remove_table_order(table_data)
        return order_fields

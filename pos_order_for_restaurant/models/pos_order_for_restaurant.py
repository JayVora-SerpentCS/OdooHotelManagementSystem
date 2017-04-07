# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class pos_config(models.Model):
    _inherit = 'pos.config'

    display_delivery = fields.Boolean("Display Delivery Button", help='''If
                                        Display Delivery Button is true than
                                        pos shows a delivery button''',
                                        default=True)
    display_parcel = fields.Boolean("Display Parcel Button", help='''If Display
                                    Parcel Button is true than pos shows a
                                    parcel button.''',
                                    default=True)


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.depends('reserved_table_ids')
    def get_table_name(self):
        res = {}
        for order in self:
            table_name = ''
            try:
                for table in order.reserved_table_ids:
                    if table.table_id:
                        table_name += table.table_id.name + " "
            except AttributeError:
                table_name = False
            res[order.id] = table_name
            self.table_name = table_name
        return res

    pflag = fields.Boolean('Flag')
    parcel = fields.Char("Parcel Order", size=32)
    driver_name = fields.Many2one('res.users', "Delivery Boy")
    phone = fields.Char("Customer Phone Number", size=128)
    reserved_table_ids = fields.One2many("table.reserverd", "order_id",
                                         "Reserved Table")
    split_order = fields.Boolean('split')
    table_name = fields.Char(compute='get_table_name',
                             string='Parcel Name', store=True)

    @api.multi
    def action_pos_order_paid(self):
        res = super(PosOrder, self).action_pos_order_paid()
        tab_obj = self.env["restaurant.table"]
        for order in self:
            try:
                if not order.split_order and not order.folio_id:
                    for res_table in order.reserved_table_ids:
                        t_ac = res_table.table_id.available_capacities
                        t_rs = res_table.reserver_seat
                        if(t_ac - t_rs) == 0:
                            vals = {
                                    'state': 'available',
                                    'available_capacities': t_rs - t_ac}
                            tab_obj.browse(res_table.table_id.id).write(vals)
                        else:
                            if(t_ac - t_rs) > 0:
                                vals = {'state': 'available',
                                        'available_capacities': t_ac - t_rs}
                                t_id = res_table.table_id.id
                                tab_obj.browse(t_id).write(vals)
            except AttributeError:
                if not order.split_order:
                    for res_table in order.reserved_table_ids:
                        t_ac = res_table.table_id.available_capacities
                        t_rs = res_table.reserver_seat
                        if(t_ac - t_rs) == 0:
                            vals = {'state': 'available',
                                    'available_capacities': t_rs - t_ac}
                            tab_obj.browse(res_table.table_id.id).write(vals)
                        else:
                            if(t_ac - t_rs) > 0:
                                rst_id = res_table.table_id.id
                                val = {
                                        'state': 'available',
                                        'available_capacities': t_rs - t_ac
                                        }
                                tab_obj.browse(rst_id).write(val)

        return res

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        order_fields['driver_name'] = ui_order.get('driver_name', False)
        order_fields['phone'] = ui_order.get('phone', False)
        order_fields['pflag'] = ui_order.get('pflag', False)
        order_fields['parcel'] = ui_order.get('parcel', False)
        order_fields['split_order'] = ui_order.get('split_order', False)
        table_data = ui_order.get("table_data")
        reserve_table_ids = []
        if ui_order.get('id', False) and table_data:
            vals = {'reserved_table_ids': [(5, 0)]}
            self.browse(ui_order.get('id')).write(vals)
            for reserve in table_data:
                reserve.update({"order_id": ui_order.get('id')})
                reserv_id = self.env["table.reserverd"].create(reserve).id
                reserve_table_ids.append((4, reserv_id))
            order_fields['reserved_table_ids'] = reserve_table_ids
        if not ui_order.get('id', False) and  table_data:
            for reserve in table_data:
                reserv_id = self.env["table.reserverd"].create(reserve).id
                reserve_table_ids.append((4, reserv_id))
            order_fields['reserved_table_ids'] = reserve_table_ids
        return order_fields

    @api.model
    def check_group_pos_delivery_boy(self, puser):
        mod_obj = self.env['ir.model.data']
        grp_result = mod_obj.get_object('pos_order_for_restaurant',
                                        'group_pos_delivery_boy')
        user_add = [user.id for user in grp_result.users]
        for user in mod_obj.get_object('point_of_sale',
                                       'group_pos_manager').users:
            if puser in user_add:
                return True
        return False

    @api.model
    def close_order(self, order_id):
        ir_module_module_object = self.env['ir.module.module']
        is_kitchen_screen = ir_module_module_object.search([('state', '=',
                                                             'installed'),
                                                            ('name', '=',
                                                             'pos_receipt')])
        line_ids = []
        if is_kitchen_screen:
            for order in self.browse(order_id):
                for line in order.lines:
                    if (line.order_line_state_id.id == 3 or
                        line.order_line_state_id.id != 1):
                        line_ids.append(line.id)
            if line_ids:
                return False
        if order_id:
            if is_kitchen_screen:
                for order in self.browse(order_id):
                    for res_table in order.reserved_table_ids:
                        rtac = res_table.table_id.available_capacities
                        rtrs = res_table.reserver_seat
                        res_tab_obj = self.env["restaurant.table"]
                        res_id = res_tab_obj.browse(res_table.table_id.id)
                        if(rtac - rtrs) == 0:
                                vals = {
                                        'state': 'available',
                                        'available_capacities': rtac - rtrs
                                }
                                res_id.write(vals)
                        else:
                            if(rtac - rtrs) > 0:
                                vals = {
                                        'state': 'available',
                                        'available_capacities': rtac - rtrs
                                        }
                                res_id.write(vals)
            order_id = order_id[0]
            line_ids = [line.id for line in self.browse(order_id).lines]
            self.env["pos.order.line"].browse(line_ids).write({"order_id":
                                                               order_id})
            self.browse(order_id).action_pos_order_cancel()
        return True

    @api.model
    def reassign_table(self, booked_table):
        tab_obj = self.env['restaurant.table']
        if booked_table and booked_table.split(''):
            for booked in booked_table.split(''):
                if booked:
                    table_id = int(booked.split('/')[0])
                    qty = int(booked.split('/')[1])
                    tab_id = tab_obj.browse(table_id)
                    tac_id = tab_id.available_capacities
                    vals = {
                            'available_capacities': tac_id - int(qty),
                            'state': 'available'}
                    tab_id.write(vals)
        return True

    @api.model
    def remove_order(self, second_order_id=False):
        if self.sudo().ids and second_order_id:
            line_ids = [line.id for line in self.browse(second_order_id).lines]
            self.env["pos.order.line"].browse(line_ids).write({"order_id":
                                                               ids[0]})
            self.browse(second_order_id).action_pos_order_cancel()
        if not ids and second_order_id:
            self.browse(second_order_id).action_pos_order_cancel()
        return True


class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create_customer_from_pos(self, c_name, c_street, c_street2, c_city,
                                 c_zip, c_phone):
        idClient = self.create({
            'name': c_name,
            'street': c_street or False,
            'street2': c_street2 or False,
            'city': c_city or False,
            'zip': c_zip or False,
            'phone': c_phone or False,
            'customer': True,
        })
        return idClient.id


class table_reserved(models.Model):
    _name = "table.reserverd"

    table_id = fields.Many2one("restaurant.table", "Table")
    reserver_seat = fields.Integer("Reserved Seat")
    order_id = fields.Many2one("pos.order", "POS Order")


class restaurant_table(models.Model):
    _inherit = 'restaurant.table'

    capacities = fields.Integer('Capacities')
    state = fields.Selection([('reserved', 'Reserved'), ('available',
                                                         'Available')],
                             'State', required=True,
                             default='available')
    users_ids = fields.Many2many('res.users', 'rel_table_master_users',
                                 'table_id', 'user_id', 'User')
    available_capacities = fields.Integer('Reserved Seat', readonly=True,
                                          default=0)

    @api.model
    def remove_table_order(self, table_ids):
        for table_rec in table_ids:
            table = self.browse(table_rec['table_id'])
            tac = table.available_capacities
            if (int(tac) - int(table_rec['reserver_seat']
                                                      )) == 0:
                table.write({'state': 'available', 'available_capacities':
                             int(tac) - int(table_rec['reserver_seat'])})
            else:
                table.write({'state': 'available', 'available_capacities':
                             int(tac) - int(table_rec['reserver_seat'])})
        return True

    @api.model
    def create_from_ui(self, table):
        """ create or modify a table from the point of sale UI.
            table contains the table's fields. If it contains an
            id, it will modify the existing table. It then
            returns the id of the table.
        """
        if table.get('floor_id'):
            table['floor_id'] = table['floor_id'][0]

        table_id = table.pop('id', False)
        if table_id:
            self.browse(table_id).write(table)
        else:
            table_id = self.create(table).id
        return table_id

    @api.model
    def get_waiter_list(self):
        table_ids = self.search([])
        waiter_list = []
        final_list = []
        if table_ids:
            for table in self:
                for table_user in table.users_ids:
                    if table_user.id not in waiter_list:
                        waiter_list.append(table_user.id)
                        waiter_list_temp = {'id': table_user.id,
                                            'name': table_user.name}
                        final_list.append(waiter_list_temp)
        return final_list

    @api.multi
    def action_available(self):
        if self.id:
            reserve_tab_obj = self.env["table.reserverd"]
            for table in self:
                reserve_ids = reserve_tab_obj.search([('table_id', '=',
                                                         table.id),
                                                        ("order_id.state", "=",
                                                         "draft")])
                if reserve_ids:
                    raise UserError(_("Table is not empty!"))
                else:
                    self.write({'state': 'available',
                                'available_capacities': 0})
        return True


class restaurant_floor(models.Model):
    _inherit = 'restaurant.floor'


class pos_order_line(models.Model):
    _inherit = "pos.order.line"

    note = fields.Text('Product Notes')

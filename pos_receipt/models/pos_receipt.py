# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import time
import logging
from odoo import tools
from odoo.tools.translate import _
from odoo.tools import float_is_zero
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class pos_config(models.Model):
    _inherit = 'pos.config'

    display_send_to_kitchen = fields.Boolean("Display Send To Kitchen Button",
                                             help='''If Display SendTo kitchen/
                                             Button is true than pos shows a/
                                             send to kitchen button.''',
                                             default=True)
    display_kitchen_receipt = fields.Boolean("Display Kitchen Receipt Button",
                                             help='''If DisplayKitchen Receipt/
                                             Button is true than pos shows a/
                                             kitchen receipt button.''',
                                             default=True)
    display_customer_receipt = fields.Boolean("Display CustomerReceipt Button",
                                              help='''If Display Customer/
                                              Receipt Button is true than pos/
                                              shows a Customer receipt/
                                              button.''', default=True)

    @api.model
    def check_is_pos_restaurant(self):
        ir_mod_obj = self.env['ir.module.module']
        ir_module_module_ids = ir_mod_obj.search([('state', '=', 'installed'),
                                                  ('name', '=',
                                                   'pos_restaurant')])
        if ir_module_module_ids:
            return True
        else:
            return False


class PosOrderLineState(models.Model):
    _name = "pos.order.line.state"
    _description = "Pos Order Line State"

    name = fields.Char('Name', size=18)
    sequence = fields.Integer('Sequence')


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    order_name = fields.Char(related='order_id.pos_reference',
                             string="Order Name")
    partner_id = fields.Char(related='order_id.partner_id.name',
                             string="Customer")
    parcel = fields.Char(related='order_id.parcel_name',
                         string="Parcel")
    table = fields.Char(related='order_id.table_name', string="Table")
    order_line_state_id = fields.Many2one('pos.order.line.state',
                                          string="Order Line State",
                                          group_expand='_read_group_stage_ids')
    property_description = fields.Text('Property Description')

    @api.model
    def orderline_state_id(self, pids, order_id):
        pos_obj = self.env['pos.order']
        if pids is not None:
            line_ids = [line.id for line in pos_obj.browse(order_id).lines]
            if pids in line_ids:
                return self.browse(pids).order_line_state_id.id
            else:
                return 'cancel'
        else:
            return True

    def _read_group_stage_ids(self, read_group_order=None,
                              access_rights_uid=None, context=None):
        line_stage_obj = self.env['pos.order.line.state']
        line_stage_ids = line_stage_obj.sudo().search([], order='sequence')
        return line_stage_ids


class PosOrder(models.Model):
    _inherit = 'pos.order'

    global ex_all_prd_ids, ex_4_prd_ids, order_ids
    ex_all_prd_ids = []
    ex_4_prd_ids = []
    order_ids = []

    def get_parcel_name(self):
        res = {}
        for order in self:
            parcel_name = False
            try:
                if order.parcel:
                    parcel_name = order.parcel
            except AttributeError:
                parcel_name = False
            res[order.id] = parcel_name
        return res

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
        order.table_name = table_name
        return res

    def product_line(self):
        res1 = {}
        cnt = 0
        for order in self:
            res = []
            str1 = ""
            if order.state != 'paid':
                for line in order.lines:
                    cnt = cnt + 1
                    cnt1 = cnt <= 4
                    lp_n = line.product_id.name
                    q = line.qty
                    if ex_all_prd_ids == [] and ex_4_prd_ids == [] and cnt1:
                        str1 = (lp_n + "___" + str(q) + "-" + str(line.id) +
                                '-' + str(line.order_line_state_id.id) + '-' +
                                str(line.property_description))
                    if [[order.id]] == ex_all_prd_ids:
                        str1 = (lp_n + "___" + str(q) + "-" + str(line.id) +
                                '-' + str(line.order_line_state_id.id) + '-' +
                                str(line.property_description))
                    if [[order.id]] == ex_4_prd_ids and cnt <= 4:
                        str1 = (lp_n + "___" + str(q) + "-" + str(line.id) +
                                '-' + str(line.order_line_state_id.id) + '-' +
                                (line.property_description))
                    res.append(str1)
                cnt = 0
                if ex_all_prd_ids:
                    ex_all_prd_ids.remove(self.sudo().ids)
                if ex_4_prd_ids:
                    ex_4_prd_ids.remove(self.sudo().ids)
                res1[order.id] = res
                order.product_details = res
        return res1

    def show_all_product(self):
        if self.sudo().ids in order_ids:
            order_ids.remove(self.sudo().ids)
            ex_4_prd_ids.append(self.sudo().ids)
        else:
            order_ids.append(self.sudo().ids)
            ex_all_prd_ids.append(self.sudo().ids)
        return True

    asset_method_time = fields.Char(_compute_='_get_asset_method_time',
                                    string='Asset Method Time', readonly=True)
    order_line_state_id = fields.Many2one('pos.order.line.state',
                                          "Order Line State")
    parcel_name = fields.Char(_compute_='get_parcel_name',
                              string='Parcel Name', store=True)
    table_name = fields.Char(_compute_='get_table_name', string='Table Name',
                             store=True)
    product_details = fields.One2many("pos.order.line",
                                      _compute_='product_line',
                                      string='Product Details')
    order_line_status = fields.Char("Orderline Status", default='draft')

    @api.model
    def get_done_orderline(self, order_ids):
        order_data = []
        for order in self.browse(order_ids):
            line_ids = []
            for line in order.lines:
                if line.order_line_state_id.id == 3:
                    line_ids.append(line.id)
            if line_ids:
                order_data.append({"id": order.id, "line_ids": line_ids})
        if order_data:
            return order_data or False

    @api.model
    def close_order(self, order_id):
        ir_module_module_object = self.env['ir.module.module']
        res_tab = self.env["restaurant.table"]
        a = ('name', '=', 'pos_order_for_restaurant')
        is_restaurant = ir_module_module_object.search([('state', '=',
                                                         'installed'), a])
        line_ids = []
        for order in self.browse(order_id):
            for line in order.lines:
                os_id = line.order_line_state_id.id != 1
                if line.order_line_state_id.id == 3 or os_id:
                    line_ids.append(line.id)
        if line_ids:
            return False
        if order_id:
            if is_restaurant:
                for order in self.browse(order_id):
                    for res_table in order.reserved_table_ids:
                        r_seat = res_table.reserver_seat
                        t_id = res_table.table_id.id
                        a_cap = t_id.available_capacities
                        at_cap = res_table.table_id.available_capacities
                        rv_seat = res_table.reserver_seat
                        if(at_cap - r_seat) == 0:
                            vals = {'state': 'available',
                                    'available_capacities': a_cap - rv_seat}
                            res_tab.browse(t_id).write(vals)
                        else:
                            if(at_cap - r_seat) > 0:
                                vals = {
                                    'state': 'available',
                                    'available_capacities': a_cap - rv_seat}
                                res_tab.browse(t_id).write()
            order_id = order_id[0]
            line_ids = [line.id for line in self.browse(order_id).lines]
            self.env['pos.order.line'].browse(line_ids).write({"order_id":
                                                               order_id})
            self.browse(order_id).action_pos_order_cancel()
        return True

    def _process_order(self, order, kitchen=False):
        session = self.env['pos.session'].browse(order['pos_session_id'])
        pos_obj = self.env['pos.order.line']
        order_id = order.get('id', False)
        if session.state == 'closing_control' or session.state == 'closed':
            session = self._get_valid_session(order)
            order['pos_session_id'] = session.id

        if kitchen and not order.get('id', False):
            order_id = self.create(self._order_fields(order))
            if order.get('folio_id', False):
                so_line_obj = self.env['sale.order.line']
                hsl_obj = self.env['hotel.service.line']
                for order1 in order_id.lines:
                    values = {'order_id': order_id.id,
                              'name': order1.product_id.name,
                              'product_id': order1.product_id.id,
                              'product_uom_qty': order1.qty,
                              'price_unit': order1.price_unit,
                              'price_subtotal': order1.price_subtotal}
                    sol_rec = so_line_obj.sudo().create(values)
                    hsl_obj.sudo().create({'folio_id': order_id.folio_id.id,
                                           'service_line_id': sol_rec.id})
                order_id.folio_id.sudo().write({'folio_pos_order_ids':
                                                [(4, order_id.id)]})
            return [order_id.id, [o.id for o in order_id.lines]]
        if kitchen and order.get('id', False):
            line_ids = [o.id for o in self.browse(order_id).lines]
            line_data = list(order.get('lines'))
            for line in line_data:
                l_id = line[2].get('line_id')
                if l_id in line_ids:
                    pl = pos_obj.browse(l_id)
                    line[2]['order_line_state_id'] = pl.order_line_state_id.id
                    pos_obj.browse(line[2].get('line_id')).write(line[2])
                    order.get('lines').remove(line)
            self.browse(order_id).write(self._order_fields(order))
            if order.get('folio_id', False):
                if order.get('folio_id', False):
                    so_line_obj = self.env['sale.order.line']
                    hsl_obj = self.env['hotel.service.line']
                    for order1 in order_id.lines:
                        values = {'order_id': order_id.id,
                                  'name': order1.product_id.name,
                                  'product_id': order1.product_id.id,
                                  'product_uom_qty': order1.qty,
                                  'price_unit': order1.price_unit,
                                  'price_subtotal': order1.price_subtotal}
                        sol_rec = so_line_obj.sudo().create(values)
                        val = {'folio_id': order_id.folio_id.id,
                               'service_line_id': sol_rec.id}
                        hsl_obj.sudo().create(val)
                order_id.folio_id.sudo().write({'folio_pos_order_ids':
                                                [(4, order_id.id)]})
            return [order_id, [o.id for o in self.browse(order_id).lines]]

        if not kitchen and not order.get('id', False):
            order_id = self.create(self._order_fields(order)).id

        if not kitchen and order.get('id', False):
            line_ids = [o.id for o in self.browse(order_id).lines]
            line_data = list(order.get('lines'))
            for line in line_data:
                l_id = line[2].get('line_id')
                if l_id in line_ids:
                    pl = pos_obj.browse(l_id)
                    line[2]['order_line_state_id'] = pl.order_line_state_id.id
                    pos_obj.browse(line[2].get('line_id')).write(line[2])
                    order.get('lines').remove(line)
            self.browse(order_id).write(self._order_fields(order))
        if not kitchen:
            journal_ids = set()
            dec_pr_obj = self.env['decimal.precision']
            for pt in order['statement_ids']:
                pf = self._payment_fields(pt[2])
                if isinstance(order_id, int):
                    self.browse(order_id).add_payment(pf)
                else:
                    order_id.add_payment(pf)
                journal_ids.add(pt[2]['journal_id'])
            if session.sequence_number <= order['sequence_number']:
                session.write({'sequence_number': order['sequence_number'] +
                               1})
                session.refresh()
            if not float_is_zero(order['amount_return'],
                                 dec_pr_obj.precision_get('Accnt')):
                cash_journal = session.cash_journal_id.id
                if not cash_journal:
                    cash_journal_ids = self.env['accnt.journal'].search([
                        ('type', '=', 'cash'),
                        ('id', 'in', list(journal_ids)),
                    ], limit=1).sudo().ids
                    if not cash_journal_ids:
                        # If none, select for change one of the cash
                        # journals of the POS. This is used for example when a
                        # customer pays by credit card. An amount higher than
                        # total amount of the order and gets cash back
                        cash_journal_ids = [statement.journal_id.id for
                                            statement in session.statement_ids
                                            if statement.journal_id.type ==
                                            'cash']
                        if not cash_journal_ids:
                            raise UserError(_('''No cash statement found for/
                            this session. Unable to record returned cash.'''))
                    cash_journal = cash_journal_ids[0]
                if isinstance(order_id, int):
                    self.browse(order_id).add_payment({
                        'amount': -order['amount_return'],
                        'payment_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'payment_name': _('return'),
                        'journal': cash_journal,
                    })
                else:
                    order_id.add_payment({'amount': -order['amount_return'],
                                          'payment_date':
                                          time.strftime('%Y-%m-%d %H:%M:%S'),
                                          'payment_name': _('return'),
                                          'journal': cash_journal})
            return order_id

    @api.multi
    def write(self, vals):
        vals['name'] = self.name
        res = super(PosOrder, self).write(vals)
        return res

    @api.model
    def create_from_ui(self, orders, kitchen=False):
        # Keep only new orders
        submitted_references = [o['data']['name'] for o in orders]
        existing_order_ids = self.search([('pos_reference', 'in',
                                           submitted_references)]).sudo().ids
        existing_orders = self.browse(existing_order_ids).read(['pos_reference'
                                                                ])
        existing_references = set([o['pos_reference'] for o in existing_orders
                                   ])
        orders_to_save = [o for o in orders if o['data']['name'] not in
                          existing_references]
        kitchen_order = [o for o in orders]
        order_ids = []
        if kitchen:
            for tmp_order in kitchen_order:
                order = tmp_order['data']
                order_id = self._process_order(order, True)
                return order_id
        elif not orders_to_save:
            for tmp_order in kitchen_order:
                to_invoice = tmp_order['to_invoice']
                order = tmp_order['data']
                order_id = self._process_order(order)
                order_ids.append(order_id)
                try:
                    self.browse([order_id]).action_pos_order_paid()
                except Exception as e:
                    _logger.error('Could not fully process the POS Order: %s',
                                  tools.ustr(e))
                if to_invoice:
                    self.action_invoice([order_id])
                    o_id = self.browse(order_id).invoice_id.id
                    ac_iv = self.env['accnt.invoice']
                    ac_iv.sudo().browse([o_id]).sudo().action_invoice_open()
            return order_id
        else:
            for tmp_order in orders_to_save:
                to_invoice = tmp_order['to_invoice']
                order = tmp_order['data']
                order_id = self._process_order(order)
                order_ids.append(order_id)
                try:
                    self.browse([order_id]).action_pos_order_paid()
                except Exception as e:
                    _logger.error('Could not fully process the POS Order: %s',
                                  tools.ustr(e))
                if to_invoice:
                    self.action_invoice([order_id])
                    o_id = self.browse(order_id).invoice_id.id
                    ac_iv = self.env['accnt.invoice']
                    ac_iv.sudo().browse([o_id]).sudo().action_invoice_open()
            return order_ids


class PosCategory(models.Model):
    _inherit = 'pos.category'

    @api.model
    def get_root_of_category(self):
        res = {}
        ids = self.search([])
        for cat in ids:
            pcat = cat.parent_id
            root_category_name = False
            root_category_id = 0
            category_id = cat.id
            while pcat:
                root_category_name = pcat.name
                root_category_id = pcat.id
                pcat = pcat.parent_id
            res[category_id] = {'categ_id': category_id,
                                'categ_name': cat.name,
                                'root_category_name': root_category_name,
                                'root_category_id': root_category_id}
        return res


class pos_session(models.Model):
    _inherit = "pos.session"

    def _confirm_orders(self):
        pos_obj = self.env['pos.order']
        for session in self:
            c_id = session.config_id.journal_id.company_id.id
            orders = session.order_ids.filtered(lambda order: order.state ==
                                                'paid')
            journal_id = self.env['ir.config_parameter'].sudo().get_param(
                'pos.closing.journal_id_%s' % c_id,
                default=session.config_id.journal_id.id)

            move1 = pos_obj.with_context(force_company=c_id)
            move = move1._create_accnt_move(session.start_at, session.name,
                                            int(journal_id), c_id)
            order = orders.with_context(force_company=c_id)
            order._create_accnt_move_line(session, move)
            for order in session.order_ids.filtered(lambda o: o.state not in
                                                    ['done', 'invoiced',
                                                     'cancel']):
                if order.state not in ('paid'):
                    raise UserError(_('''You cannot confirm all orders of this/
                                      session, because they have not the'paid'/
                                      status'''))
                order.action_pos_order_done()

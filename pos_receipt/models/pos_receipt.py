# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import time
import logging
from odoo import netsvc, tools
from odoo.tools.translate import _
from odoo.tools import float_is_zero
from odoo import workflow
from odoo import SUPERUSER_ID
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class pos_config(models.Model):
    _inherit = 'pos.config'

    display_send_to_kitchen = fields.Boolean("Display Send To Kitchen Button", help="If Display Send To kitchen Button is true than pos shows a send to kitchen button.", default=True)
    display_kitchen_receipt = fields.Boolean("Display Kitchen Receipt Button", help="If Display Kitchen Receipt Button is true than pos shows a kitchen receipt button.", default=True)
    display_customer_receipt = fields.Boolean("Display Customer Receipt Button", help="If Display Customer Receipt Button is true than pos shows a Customer receipt button.", default=True)

    @api.model
    def check_is_pos_restaurant(self):
         ir_module_module_object = self.env['ir.module.module']
         ir_module_module_ids = self.env['ir.module.module'].search([('state', '=', 'installed'), ('name', '=', 'pos_restaurant')])
         if ir_module_module_ids :
              return True
         else :
              return False


class PosOrderLineState(models.Model):
    _name = "pos.order.line.state"
    _description = "Pos Order Line State"

    name = fields.Char('Name', size=18)
    sequence = fields.Integer('Sequence')


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    order_name = fields.Char(related='order_id.pos_reference', string="Order Name")
    partner_id = fields.Char(related='order_id.partner_id.name', string="Customer")
    parcel = fields.Char(related='order_id.parcel_name', string="Parcel")
    table = fields.Char(related='order_id.table_name', string="Table")
    order_line_state_id = fields.Many2one('pos.order.line.state', string="Order Line State", group_expand='_read_group_stage_ids')
    property_description = fields.Text('Property Description')

    @api.model
    def orderline_state_id (self,pids, order_id):
        if pids != None:
            line_ids = [line.id for line in self.env['pos.order'].browse(order_id).lines]
            if pids in line_ids :
                return self.browse(pids).order_line_state_id.id
            else :
                return 'cancel'
        else :
            return True

    def _read_group_stage_ids(self, read_group_order=None, access_rights_uid=None, context=None):
        line_stage_obj = self.env['pos.order.line.state']
        result = []
        line_stage_ids = line_stage_obj.sudo().search([], order='sequence')
        return line_stage_ids


class PosOrder(models.Model):
    _inherit = 'pos.order'

    global expand_all_product_ids, expand_four_product_ids, order_ids
    expand_all_product_ids = []
    expand_four_product_ids = []
    order_ids = []

    def get_parcel_name(self):
        res = {}
        for order in self:
            parcel_name = False
            try:
                if order.parcel :
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
                   if table.table_id :
                       table_name += table.table_id.name + " "
            except AttributeError:
                table_name = False
            res[order.id] = table_name
        order.table_name = table_name
        return res

    def product_line(self):
        res1 = {}
        count = 0
        for order in self:
            res = []
            str1 = ""
            if order.state != 'paid' :
                for line in order.lines :
                     count = count + 1
                     if expand_all_product_ids == [] and expand_four_product_ids == []  and count <= 4:
                         str1 = line.product_id.name + "____" + str(line.qty) + "-" + str(line.id) + '-' + str(line.order_line_state_id.id) + '-' + str(line.property_description) 
                     if [[order.id]] == expand_all_product_ids :
                         str1 = line.product_id.name + "____" + str(line.qty) + "-" + str(line.id) + '-' + str(line.order_line_state_id.id) + '-' + str(line.property_description) 
                     if [[order.id]] == expand_four_product_ids and count <= 4 :
                         str1 = line.product_id.name + "____" + str(line.qty) + "-" + str(line.id) + '-' + str(line.order_line_state_id.id) + '-' + str(line.property_description) 
                     res.append(str1)
                count = 0
                if expand_all_product_ids :
                  expand_all_product_ids.remove(self.sudo().ids)
                if expand_four_product_ids :
                  expand_four_product_ids.remove(self.sudo().ids)
                res1[order.id] = res
                order.product_details = res
        return res1

    def show_all_product(self):
       if self.sudo().ids in order_ids:
           order_ids.remove(self.sudo().ids)
           expand_four_product_ids.append(self.sudo().ids)
       else:
           order_ids.append(self.sudo().ids)
           expand_all_product_ids.append(self.sudo().ids)
       return True

    asset_method_time = fields.Char(compute='_get_asset_method_time', string='Asset Method Time', readonly=True)
    pricelist_ids = fields.One2many('product.pricelist', compute="_compute_pricelist_ids",string='Price list available for this Ecommerce/Website')
    order_line_state_id = fields.Many2one('pos.order.line.state', "Order Line State")
    parcel_name = fields.Char(compute='get_parcel_name',string='Parcel Name', store=True)
    table_name = fields.Char(compute='get_table_name', string='Table Name', store=True)
    product_details = fields.One2many("pos.order.line", compute='product_line', string='Product Details')
    order_line_status = fields.Char("Orderline Status", default='draft')

    @api.model
    def get_done_orderline(self,order_ids):
        order_data = []
        for order in self.browse(order_ids):
            line_ids = []
            for line in order.lines:
                if line.order_line_state_id.id == 3:
                    line_ids.append(line.id)
            if line_ids:
                order_data.append({"id":order.id, "line_ids":line_ids})
        if order_data:
            return order_data or False

    @api.model
    def close_order(self, order_id):
        ir_module_module_object = self.env['ir.module.module']
        is_restaurant = ir_module_module_object.search([('state', '=', 'installed'), ('name', '=', 'pos_order_for_restaurant')])
        line_ids = []
        for order in self.browse(order_id):
            for line in order.lines:
                if line.order_line_state_id.id == 3 or line.order_line_state_id.id != 1:
                    line_ids.append(line.id)
        if line_ids:
            return False
        if order_id:
            if is_restaurant :
                for order in self.browse(order_id):
                    for res_table in order.reserved_table_ids:
                        if (res_table.table_id.available_capacities - res_table.reserver_seat) == 0:
                                self.env["restaurant.table"].browse(res_table.table_id.id).write({'state': 'available', 'available_capacities': res_table.table_id.available_capacities - res_table.reserver_seat })
                        else:
                            if (res_table.table_id.available_capacities - res_table.reserver_seat) > 0:
                                self.env["restaurant.table"].browse(res_table.table_id.id).write({'state': 'available', 'available_capacities': res_table.table_id.available_capacities - res_table.reserver_seat })
            order_id = order_id[0]
            line_ids = [line.id for line in self.browse(order_id).lines]
            self.env["pos.order.line"].browse(line_ids).write({"order_id":order_id})
            self.browse(order_id).action_pos_order_cancel()
        return True

    def _process_order(self, order, kitchen=False):
        session = self.env['pos.session'].browse(order['pos_session_id'])
        pos_line_object = self.env['pos.order.line']
        order_id = order.get('id', False)
        if session.state == 'closing_control' or session.state == 'closed':
            session = self._get_valid_session(order)
            order['pos_session_id'] = session.id

        if kitchen and not order.get('id', False) :
            order_id = self.create(self._order_fields(order))
            if order.get('folio_id',False) :
                so_line_obj = self.env['sale.order.line']
                hsl_obj = self.env['hotel.service.line']
                for order1 in order_id.lines :
                    values = {'order_id': order_id.id,
                                  'name': order1.product_id.name,
                                  'product_id': order1.product_id.id,
                                  'product_uom_qty': order1.qty,
                                  'price_unit': order1.price_unit,
                                  'price_subtotal': order1.price_subtotal,
                                  }
                    sol_rec = so_line_obj.sudo().create(values)
                    hsl_obj.sudo().create({'folio_id': order_id.folio_id.id,
                                        'service_line_id': sol_rec.id})
                    
                order_id.folio_id.sudo().write({'folio_pos_order_ids':
                                  [(4, order_id.id)]})
            return [order_id.id, [o.id for o in order_id.lines ]]

        if kitchen and order.get('id', False) :
            line_ids = [o.id for o in self.browse(order_id).lines ]
            line_data = list(order.get('lines'))
            for line in line_data :
                if line[2].get('line_id') in line_ids :
                    line[2]['order_line_state_id'] = pos_line_object.browse(line[2].get('line_id')).order_line_state_id.id
                    pos_line_object.browse(line[2].get('line_id')).write(line[2])
                    order.get('lines').remove(line)
            self.browse(order_id).write(self._order_fields(order))
            if order.get('folio_id',False) :
                if order.get('folio_id',False) :
                    so_line_obj = self.env['sale.order.line']
                    hsl_obj = self.env['hotel.service.line']
                    for order1 in order_id.lines :
                        values = {'order_id': order_id.id,
                                      'name': order1.product_id.name,
                                      'product_id': order1.product_id.id,
                                      'product_uom_qty': order1.qty,
                                      'price_unit': order1.price_unit,
                                      'price_subtotal': order1.price_subtotal,
                                      }
                        sol_rec = so_line_obj.sudo().create(values)
                        hsl_obj.sudo().create({'folio_id': order_id.folio_id.id,
                                            'service_line_id': sol_rec.id})
                    
                order_id.folio_id.sudo().write({'folio_pos_order_ids':
                                  [(4, order_id.id)]})
            return [order_id, [o.id for o in self.browse(order_id).lines]]

        if not kitchen and not order.get('id', False):
            order_id = self.create(self._order_fields(order)).id

        if not kitchen and order.get('id', False) :
            line_ids = [o.id for o in self.browse(order_id).lines]
            line_data = list(order.get('lines'))
            for line in  line_data :
                if line[2].get('line_id')  in line_ids :
                    line[2]['order_line_state_id'] = pos_line_object.browse(line[2].get('line_id')).order_line_state_id.id
                    pos_line_object.browse(line[2].get('line_id')).write(line[2])
                    order.get('lines').remove(line)
            self.browse(order_id).write(self._order_fields(order))

        if not kitchen:
             journal_ids = set()
             for payments in order['statement_ids']:
                if isinstance( order_id, int ):
                    self.browse(order_id).add_payment(self._payment_fields(payments[2]))
                else:
                    order_id.add_payment(self._payment_fields(payments[2]))
                journal_ids.add(payments[2]['journal_id'])
                
             if session.sequence_number <= order['sequence_number']:
                session.write({'sequence_number': order['sequence_number'] + 1})
                session.refresh()
                
             if not float_is_zero(order['amount_return'], self.env['decimal.precision'].precision_get('Account')):
                cash_journal = session.cash_journal_id.id
                if not cash_journal:
                    cash_journal_ids = self.env['account.journal'].search([
                        ('type', '=', 'cash'),
                        ('id', 'in', list(journal_ids)),
                    ], limit=1).sudo().ids
                    if not cash_journal_ids:
                        # If none, select for change one of the cash journals of the POS
                        # This is used for example when a customer pays by credit card
                        # an amount higher than total amount of the order and gets cash back
                        cash_journal_ids = [statement.journal_id.id for statement in session.statement_ids
                                            if statement.journal_id.type == 'cash']
                        if not cash_journal_ids:
                            raise UserError(_("No cash statement found for this session. Unable to record returned cash."))
                    cash_journal = cash_journal_ids[0]
                if isinstance( order_id, int ):
                    self.browse(order_id).add_payment({
                        'amount':-order['amount_return'],
                        'payment_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'payment_name': _('return'),
                        'journal': cash_journal,
                    })
                else:
                    order_id.add_payment({
                       'amount':-order['amount_return'],
                        'payment_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'payment_name': _('return'),
                        'journal': cash_journal,
                    })
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
        existing_order_ids = self.search([('pos_reference', 'in', submitted_references)]).sudo().ids
        existing_orders = self.browse(existing_order_ids).read(['pos_reference'])
        existing_references = set([o['pos_reference'] for o in existing_orders])
        orders_to_save = [o for o in orders if o['data']['name'] not in existing_references]
        kitchen_order = [o for o in orders]
        order_ids = []
        if kitchen :
            for tmp_order in kitchen_order:
                order = tmp_order['data']
                order_id = self._process_order(order, True)
                return order_id
        elif not orders_to_save :
            for tmp_order in kitchen_order:
                to_invoice = tmp_order['to_invoice']
                order = tmp_order['data']
                order_id = self._process_order(order)
                order_ids.append(order_id)
                try:
                    self.browse([order_id]).action_pos_order_paid()
                except Exception as e:
                    _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))
                if to_invoice:
                    self.action_invoice([order_id])
                    order_obj = self.browse(order_id)
                    self.env['account.invoice'].sudo().browse([order_obj.invoice_id.id]).sudo().action_invoice_open()
            return order_id
        else :
            for tmp_order in orders_to_save:
                to_invoice = tmp_order['to_invoice']
                order = tmp_order['data']
                order_id = self._process_order(order)
                order_ids.append(order_id)
                try:
                    self.browse([order_id]).action_pos_order_paid()
                except Exception as e:
                    _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))
                if to_invoice:
                    self.action_invoice([order_id])
                    order_obj = self.browse(order_id)
                    self.env['account.invoice'].sudo().browse([order_obj.invoice_id.id]).sudo().action_invoice_open()
            return order_ids


class PosCategory(models.Model):
    _inherit = 'pos.category'

    @api.model
    def get_root_of_category(self):
        res = {}
        ids = self.search([])
        for cat in ids:
            pcat = cat.parent_id
            root_category_name = False;
            root_category_id = 0;
            category_id = cat.id
            while pcat:
                root_category_name = pcat.name
                root_category_id = pcat.id
                pcat = pcat.parent_id
            res[category_id] = {'categ_id':category_id, 'categ_name':cat.name, 'root_category_name':root_category_name, 'root_category_id':root_category_id};
        return res


class pos_session(models.Model):
    _inherit = "pos.session"

    def _confirm_orders(self):
        for session in self:
            company_id = session.config_id.journal_id.company_id.id
            orders = session.order_ids.filtered(lambda order: order.state == 'paid')
            journal_id = self.env['ir.config_parameter'].sudo().get_param(
                'pos.closing.journal_id_%s' % company_id, default=session.config_id.journal_id.id)

            move = self.env['pos.order'].with_context(force_company=company_id)._create_account_move(session.start_at, session.name, int(journal_id), company_id)
            orders.with_context(force_company=company_id)._create_account_move_line(session, move)
            for order in session.order_ids.filtered(lambda o: o.state not in ['done', 'invoiced', 'cancel']):
                if order.state not in ('paid'):
                    raise UserError(_("You cannot confirm all orders of this session, because they have not the 'paid' status"))
                order.action_pos_order_done()

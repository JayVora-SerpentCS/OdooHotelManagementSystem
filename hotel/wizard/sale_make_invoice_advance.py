# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.model
    def _get_advance_payment(self):
        ctx = self.env.context.copy()
        if self._context.get('active_model') == 'hotel.folio':
            hotel_fol = self.env['hotel.folio']
            hotel = hotel_fol.browse(self._context.get('active_ids',
                                                       []))
            ctx.update({'active_ids': [hotel.order_id.id],
                        'active_id': hotel.order_id.id})
        return super(SaleAdvancePaymentInv,
                     self.with_context(ctx))._get_advance_payment_method()
    advance_payment_method = fields.Selection([('delivered',
                                                'Invoiceable lines'),
                                               ('all',
                                                'Invoiceable lines\
                                                (deduct down payments)'),
                                               ('percentage',
                                                'Down payment (percentage)'),
                                               ('fixed',
                                                'Down payment (fixed\
                                                amount)')],
                                              string='What do you want\
                                              to invoice?',
                                              default=_get_advance_payment,
                                              required=True)

    @api.multi
    def create_invoices(self):
        ctx = self.env.context.copy()
        if self._context.get('active_model') == 'hotel.folio':
            hotel_fol = self.env['hotel.folio']
            hotel = hotel_fol.browse(self._context.get('active_ids',
                                                       []))
            ctx.update({'active_ids': [hotel.order_id.id],
                        'active_id': hotel.order_id.id,
                        'folio_id': hotel.id})
        res = super(SaleAdvancePaymentInv,
                    self.with_context(ctx)).create_invoices()

        return res

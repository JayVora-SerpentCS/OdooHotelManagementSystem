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

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
from odoo import api, fields, models


class ReportLunchorder1(models.AbstractModel):
    _name = 'report.hotel_pos_restaurant.report_folio_pos'

    def get_data(self, date_start, date_end):
        folio_obj = self.env['hotel.folio']
        tids = folio_obj.search([('checkin_date', '>=', date_start),
                                 ('checkout_date', '<=', date_end)])
        folio_ids = []
        for rec in tids:
            if rec.folio_pos_order_ids:
                folio_ids.append(rec)
        return folio_ids

    def get_pos(self, date_start, date_end):
        folio_obj = self.env['hotel.folio']
        tids = folio_obj.search([('checkin_date', '>=', date_start),
                                 ('checkout_date', '<=', date_end)])
        posorder_ids = []
        for rec in tids:
            if rec.folio_pos_order_ids:
                posorder_ids.append(rec.folio_pos_order_ids)
        return posorder_ids

    def gettotal(self, pos_order):
        self.temp = 0.0
        amount = 0.0
        for x in pos_order:
            amount = amount + float(x.amount_total)
        self.temp = self.temp + amount
        return amount

    def getTotal(self):
        self.temp = 0.0
        return self.temp

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids',
                                                                []))
        date_start = data.get('date_start', fields.Date.today())
        date_end = data['form'].get('date_end', str(datetime.now() +
                                    relativedelta(months=+1,
                                                  day=1, days=-1))[:10])
        rm_act = self.with_context(data['form'].get('used_context', {}))
        get_data = rm_act.get_data(date_start, date_end)
        get_pos = rm_act.get_pos(date_start, date_end)
#       gettotal = rm_act.gettotal(pos_order)
        getTotal = rm_act.getTotal()
        docargs = {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_data': get_data,
            'get_pos': get_pos,
            'getTotal': getTotal,
        }
        docargs['data'].update({'date_end':
                                parser.parse(docargs.get('data').
                                             get('date_end')).
                                strftime('%m/%d/%Y')})
        docargs['data'].update({'date_start':
                                parser.parse(docargs.get('data').
                                             get('date_start')).
                                strftime('%m/%d/%Y')})
        render_model = 'hotel_pos_restaurant.report_folio_pos'
        return self.env['report'].render(render_model, docargs)

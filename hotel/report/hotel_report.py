# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta
from dateutil import parser
from odoo import api, fields, models


class FolioReport(models.AbstractModel):
    _name = 'report.hotel.report_hotel_folio'

    def get_data(self, date_start, date_end):
        total_amount = 0.0
        data_folio = []
        folio_obj = self.env['hotel.folio']
        act_domain = [('checkin_date', '>=', date_start),
                      ('checkout_date', '<=', date_end)]
        tids = folio_obj.search(act_domain)
        for data in tids:
            data_folio.append({'name': data.name,
                               'partner': data.partner_id.name,
                               'checkin': parser.parse(data.checkin_date).
                               strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                               'checkout': parser.parse(data.checkout_date).
                               strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                               'amount': data.amount_total})
            total_amount += data.amount_total
        data_folio.append({'total_amount': total_amount})
        return data_folio

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids',
                                                                []))
        date_start = data['form'].get('date_start', fields.Date.today())
        date_end = data['form'].get('date_end', str(datetime.now() +
                                    relativedelta(months=+1,
                                                  day=1, days=-1))[:10])
        rm_act = self.with_context(data['form'].get('used_context', {}))
        data_res = rm_act.get_data(date_start, date_end)
        docargs = {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'folio_data': data_res,
        }
        docargs['data'].update({'date_end':
                                parser.parse(docargs.get('data').
                                             get('date_end')).
                                strftime('%m/%d/%Y')})
        docargs['data'].update({'date_start':
                                parser.parse(docargs.get('data').
                                             get('date_start')).
                                strftime('%m/%d/%Y')})
        render_model = 'hotel.report_hotel_folio'
        return self.env['report'].render(render_model, docargs)

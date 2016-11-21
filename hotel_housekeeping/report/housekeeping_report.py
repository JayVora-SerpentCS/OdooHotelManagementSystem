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
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ActivityReport(models.AbstractModel):
    _name = 'report.hotel_housekeeping.report_housekeeping'

    def get_room_activity_detail(self, date_start, date_end, room_no):
        activity_detail = []
        act_val = {}
        house_keep_act_obj = self.env['hotel.housekeeping.activities']

        activity_line_ids = (house_keep_act_obj.search([
                   ('clean_start_time', '>=', date_start),
                   ('clean_end_time', '<=', date_end),
                   ('a_list', '=', room_no)]))

        for activity in activity_line_ids:
            ss_date = datetime.strptime(activity.clean_start_time,
                                        DEFAULT_SERVER_DATETIME_FORMAT)
            ee_date = datetime.strptime(activity.clean_end_time,
                                        DEFAULT_SERVER_DATETIME_FORMAT)
            diff = ee_date - ss_date

            act_val.update({'current_date': activity.today_date,
                            'activity': (activity.activity_name and
                                         activity.activity_name.name or
                                         ''),
                            'login': (activity.housekeeper and
                                      activity.housekeeper.name or ''),
                            'clean_start_time': activity.clean_start_time,
                            'clean_end_time': activity.clean_end_time,
                            'duration': diff})
            activity_detail.append(act_val)
        return activity_detail

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get(
                                               'active_ids', []))

        date_start = data['form'].get('date_start', fields.Date.today())
        date_end = data['form'].get('date_end', str(datetime.now()
                            + relativedelta(months=+1, day=1, days=-1))[:10])
        room_no = data['form'].get('room_no')[0]
        get_room_activity_detail_res = self.with_context(data['form'].get(
                            'used_context', {})).get_room_activity_detail(
                                            date_start, date_end, room_no)
        docargs = {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_room_activity_detail': get_room_activity_detail_res,
        }
        docargs['data'].update({'date_end': parser.parse(docargs.get(
                    'data').get('date_end')).strftime('%m/%d/%Y')})
        docargs['data'].update({'date_start': parser.parse(docargs.get(
                    'data').get('date_start')).strftime('%m/%d/%Y')})
        return self.env['report'].render(
                'hotel_housekeeping.report_housekeeping', docargs)

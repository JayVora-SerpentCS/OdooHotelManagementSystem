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
from odoo import models, fields, api, _


class ReportTestCheckin(models.AbstractModel):
    _name = "report.hotel_reservation.report_checkin_qweb"

    def _get_room_type(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        room_dom = [('checkin', '>=', date_start),
                    ('checkout', '<=', date_end)]
        tids = reservation_obj.search(room_dom)
        res = reservation_obj.browse(tids)
        return res

    def _get_room_nos(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        tids = reservation_obj.search([('checkin', '>=', date_start),
                                       ('checkout', '<=', date_end)])
        res = reservation_obj.browse(tids)
        return res

    def get_checkin(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        res = reservation_obj.search([('checkin', '>=', date_start), 
                                      ('checkin', '<=', date_end)])
        return res

    @api.multi
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
<<<<<<< HEAD
        act_ids = self.env.context.get('active_ids', [])
        docs = self.env[self.model].browse(act_ids)
        date_start = data.get('date_start', fields.Date.today())
        date_end = data.get('date_end', str(datetime.now() +
                            relativedelta(months=+1, day=1, days=-1))[:10])
=======
        docs = self.env[self.model].browse(
                            self.env.context.get('active_ids', []))
        date_start = data.get('date_start', fields.Date.today())
        date_end = data.get('date_end', str(datetime.now() +
                                relativedelta(months=+1, day=1, days=-1))[:10])
>>>>>>> 7a6b8c07d267c325f1261cd1af4d8274a1874e2a
        _get_room_type = self.with_context(data['form'].get(
                'used_context', {}))._get_room_type(date_start, date_end)
        _get_room_nos = self.with_context(data['form'].get(
                'used_context', {}))._get_room_nos(date_start, date_end)
        get_checkin = self.with_context(data['form'].get(
                'used_context', {})).get_checkin(date_start, date_end)
        docargs = {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_room_type': _get_room_type,
            'get_room_nos': _get_room_nos,
            'get_checkin': get_checkin,
        }
        docargs['data'].update({'date_end': parser.parse(docargs.get(
                            'data').get('date_end')).strftime('%m/%d/%Y')})
        docargs['data'].update({'date_start': parser.parse(docargs.get(
                            'data').get('date_start')).strftime('%m/%d/%Y')})
        return self.env['report'].render(
                        'hotel_reservation.report_checkin_qweb', docargs)


class ReportTestCheckout(models.AbstractModel):
    _name = "report.hotel_reservation.report_checkout_qweb"

    def _get_room_type(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        res = reservation_obj.search([('checkout', '>=', date_start), 
                                      ('checkout', '<=', date_end)])
        return res

    def _get_room_nos(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        res = reservation_obj.search([('checkout', '>=', date_start), 
                                      ('checkout', '<=', date_end)])
        return res

    def get_checkout(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        res = reservation_obj.search([('checkout', '>=', date_start), 
                                      ('checkout', '<=', date_end)])
        return res

    @api.multi
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        date_start = data.get('date_start', fields.Date.today())
        date_end = data.get('date_end', str(datetime.now() + 
                            relativedelta(months=+1, day=1, days=-1))[:10])
        _get_room_type = self.with_context(data['form'].get(
                'used_context', {}))._get_room_type(date_start, date_end)
        _get_room_nos = self.with_context(data['form'].get(
                'used_context', {}))._get_room_nos(date_start, date_end)
        get_checkout = self.with_context(data['form'].get(
                'used_context', {})).get_checkout(date_start, date_end)
        docargs = {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_room_type': _get_room_type,
            'get_room_nos': _get_room_nos,
            'get_checkout': get_checkout,
        }
        docargs['data'].update({'date_end': parser.parse(docargs.get(
                     'data').get('date_end')).strftime('%m/%d/%Y')})
        docargs['data'].update({'date_start': parser.parse(docargs.get(
                     'data').get('date_start')).strftime('%m/%d/%Y')})
        return self.env['report'].render(
                'hotel_reservation.report_checkout_qweb', docargs)


class ReportTestMaxroom(models.AbstractModel):
    _name = "report.hotel_reservation.report_maxroom_qweb"

    def _get_room_type(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        tids = reservation_obj.search([('checkin', '>=', date_start),
                                       ('checkout', '<=', date_end)])
        res = reservation_obj.browse(tids)
        return res

    def _get_room_nos(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        tids = reservation_obj.search([('checkin', '>=', date_start),
                                       ('checkout', '<=', date_end)])
        res = reservation_obj.browse(tids)
        return res

    def get_data(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        res = reservation_obj.search([('checkin', '>=', date_start), 
                                      ('checkout', '<=', date_end)])
        return res

    def _get_room_used_detail(self, date_start, date_end):
        room_used_details = []
        hotel_room_obj = self.env['hotel.room']
        room_ids = hotel_room_obj.search([])
        for room in hotel_room_obj.browse(room_ids.ids):
            counter = 0
            details = {}
            if room.room_reservation_line_ids:
                for room_resv_line in room.room_reservation_line_ids:
                    if(room_resv_line.check_in >= date_start and
                       room_resv_line.check_in <= date_end):
                        counter += 1
            if counter >= 1:
                details.update({'name': room.name or '',
                                'no_of_times_used': counter})
                room_used_details.append(details)
        return room_used_details

    @api.multi
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        act_ids_rm = self.env.context.get('active_ids', [])
        docs = self.env[self.model].browse(act_ids_rm)
        date_start = data.get('date_start', fields.Date.today())
        date_end = data.get('date_end', str(datetime.now() +
                    relativedelta(months=+1, day=1, days=-1))[:10])
        _get_room_type = self.with_context(data['form'].get(
            'used_context', {}))._get_room_type(date_start, date_end)
        _get_room_nos = self.with_context(data['form'].get(
            'used_context', {}))._get_room_nos(date_start, date_end)
        get_data = self.with_context(data['form'].get(
            'used_context', {})).get_data(date_start, date_end)
        _get_room_used_detail = self.with_context(data['form'].get(
           'used_context', {}))._get_room_used_detail(date_start, date_end)
        docargs = {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_room_type': _get_room_type,
            'get_room_nos': _get_room_nos,
            'get_data': get_data,
            '_get_room_used_detail': _get_room_used_detail,

        }
        docargs['data'].update({'date_end': parser.parse(docargs.get(
                        'data').get('date_end')).strftime('%m/%d/%Y')})
        docargs['data'].update({'date_start': parser.parse(docargs.get(
                        'data').get('date_start')).strftime('%m/%d/%Y')})
        return self.env['report'].render(
                    'hotel_reservation.report_maxroom_qweb', docargs)


class ReportTestRoomres(models.AbstractModel):
    _name = "report.hotel_reservation.report_roomres_qweb"

    def _get_room_type(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        tids = reservation_obj.search([('checkin', '>=', date_start),
                                       ('checkout', '<=', date_end)])
        res = reservation_obj.browse(tids)
        return res

    def _get_room_nos(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        tids = reservation_obj.search([('checkin', '>=', date_start),
                                       ('checkout', '<=', date_end)])
        res = reservation_obj.browse(tids)
        return res

    def get_data(self, date_start, date_end):
        reservation_obj = self.env['hotel.reservation']
        res = reservation_obj.search([('checkin', '>=', date_start),
                                      ('checkout', '<=', date_end)])
        return res

    @api.multi
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        act_rmrs = self.env.context.get('active_ids', [])
        docs = self.env[self.model].browse(act_rmrs)

        date_start = data.get('date_start', fields.Date.today())
        date_end = data.get('date_end', str(datetime.now() + 
                             relativedelta(months=+1, day=1, days=-1))[:10])
        _get_room_type = self.with_context(data['form'].get(
                    'used_context', {}))._get_room_type(date_start, date_end)
        _get_room_nos = self.with_context(data['form'].get(
                    'used_context', {}))._get_room_nos(date_start, date_end)
        get_data = self.with_context(data['form'].get(
                    'used_context', {})).get_data(date_start, date_end)
        docargs = {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_room_type': _get_room_type,
            'get_room_nos': _get_room_nos,
            'get_data': get_data,
        }
        docargs['data'].update({'date_end': parser.parse(docargs.get(
                                'data').get('date_end')).strftime('%m/%d/%Y')})
        docargs['data'].update({'date_start': parser.parse(docargs.get(
                         'data').get('date_start')).strftime('%m/%d/%Y')})
        return self.env['report'].render(
                'hotel_reservation.report_roomres_qweb', docargs)

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
from openerp import models
import time
from openerp.report import report_sxw


class ReservationDetailReport(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(ReservationDetailReport, self).__init__(cr, uid, name,
                                                      context)
        self.localcontext.update({
            'time': time,
            'get_data': self.get_data,
            'get_checkin': self.get_checkin,
            'get_checkout': self.get_checkout,
            'get_room_type': self._get_room_type,
            'get_room_nos': self._get_room_nos,
            'get_room_used_detail': self._get_room_used_detail,
        })
        self.context = context

    def _get_room_type(self, reservation_line):
        room_types = ''
        for line in reservation_line:
            if line.categ_id:
                room_types += line.categ_id.name
                room_types += ' '

        return room_types

    def _get_room_nos(self, reservation_line):
        room_nos = ''
        for line in reservation_line:
            for room in line.reserve:
                room_nos += room.name
                room_nos += ' '
        return room_nos

    def get_data(self, date_start, date_end):
        reservation_obj = self.pool.get('hotel.reservation')
        tids = reservation_obj.search(self.cr, self.uid,
                                      [('checkin', '>=', date_start),
                                       ('checkout', '<=', date_end)])
        res = reservation_obj.browse(self.cr, self.uid, tids)
        return res

    def get_checkin(self, date_start, date_end):
        reservation_obj = self.pool.get('hotel.reservation')
        tids = reservation_obj.search(self.cr, self.uid,
                                      [('checkin', '>=', date_start),
                                       ('checkin', '<=', date_end)])
        res = reservation_obj.browse(self.cr, self.uid, tids)
        return res

    def get_checkout(self, date_start, date_end):
        reservation_obj = self.pool.get('hotel.reservation')
        tids = reservation_obj.search(self.cr, self.uid,
                                      [('checkout', '>=', date_start),
                                       ('checkout', '<=', date_end)])
        res = reservation_obj.browse(self.cr, self.uid, tids)
        return res

    def _get_room_used_detail(self, date_start, date_end):

        room_used_details = []
        hotel_room_obj = self.pool.get('hotel.room')
        room_ids = hotel_room_obj.search(self.cr, self.uid, [])
        for room in hotel_room_obj.browse(self.cr, self.uid, room_ids):
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


class ReportTestCheckin(models.AbstractModel):
    _name = "report.hotel_reservation.report_checkin_qweb"
    _inherit = "report.abstract_report"
    _template = "hotel_reservation.report_checkin_qweb"
    _wrapped_report_class = ReservationDetailReport


class ReportTestCheckout(models.AbstractModel):
    _name = "report.hotel_reservation.report_checkout_qweb"
    _inherit = "report.abstract_report"
    _template = "hotel_reservation.report_checkout_qweb"
    _wrapped_report_class = ReservationDetailReport


class ReportTestMaxroom(models.AbstractModel):
    _name = "report.hotel_reservation.report_maxroom_qweb"
    _inherit = "report.abstract_report"
    _template = "hotel_reservation.report_maxroom_qweb"
    _wrapped_report_class = ReservationDetailReport


class ReportTestRoomres(models.AbstractModel):
    _name = "report.hotel_reservation.report_roomres_qweb"
    _inherit = "report.abstract_report"
    _template = "hotel_reservation.report_roomres_qweb"
    _wrapped_report_class = ReservationDetailReport

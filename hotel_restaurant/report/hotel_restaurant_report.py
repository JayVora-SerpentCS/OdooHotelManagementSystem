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
from openerp import models
from openerp.report import report_sxw


class HotelRestaurantReport(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(HotelRestaurantReport, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'get_res_data': self.get_res_data,
        })
        self.context = context

    def get_res_data(self, date_start, date_end):
        rest_reservation_obj = self.pool.get('hotel.restaurant.reservation')
        tids = rest_reservation_obj.search(self.cr, self.uid,
                                           [('start_date', '>=', date_start),
                                            ('end_date', '<=', date_end)])
        res = rest_reservation_obj.browse(self.cr, self.uid, tids)
        return res


class ReportLunchorder(models.AbstractModel):
    _name = 'report.hotel_restaurant.report_res_table'
    _inherit = 'report.abstract_report'
    _template = 'hotel_restaurant.report_res_table'
    _wrapped_report_class = HotelRestaurantReport


class ReportKot(models.AbstractModel):
    _name = 'report.hotel_restaurant.report_hotel_order_kot'
    _inherit = 'report.abstract_report'
    _template = 'hotel_restaurant.report_hotel_order_kot'
    _wrapped_report_class = HotelRestaurantReport


class ReportBill(models.AbstractModel):
    _name = 'report.hotel_restaurant.report_hotel_order_kot'
    _inherit = 'report.abstract_report'
    _template = 'hotel_restaurant.report_hotel_order_kot'
    _wrapped_report_class = HotelRestaurantReport


class FolioRestReport(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(FolioRestReport, self).__init__(cr, uid, name, context)
        self.localcontext.update({'get_data': self.get_data,
                                  'gettotal': self.gettotal,
                                  'getTotal': self.getTotal,
                                  'get_rest': self.get_rest,
                                  })
        self.temp = 0.0

    def get_data(self, date_start, date_end):
        folio_obj = self.pool.get('hotel.folio')
        tids = folio_obj.search(self.cr, self.uid,
                                [('checkin_date', '>=', date_start),
                                 ('checkout_date', '<=', date_end)])
        res = folio_obj.browse(self.cr, self.uid, tids)
        folio_ids = []
        for rec in res:
            if rec.hotel_reservation_order_ids:
                folio_ids.append(rec)
        return folio_ids

    def get_rest(self, date_start, date_end):
        folio_obj = self.pool.get('hotel.folio')
        tids = folio_obj.search(self.cr, self.uid,
                                [('checkin_date', '>=', date_start),
                                 ('checkout_date', '<=', date_end)])
        res = folio_obj.browse(self.cr, self.uid, tids)
        posorder_ids = []
        for rec in res:
            if rec.hotel_reservation_order_ids:
                posorder_ids.append(rec.hotel_reservation_order_ids)
        return posorder_ids

    def gettotal(self, pos_order):
        amount = 0.0
        for x in pos_order:
            amount = amount + float(x.amount_total)
        self.temp = self.temp + amount
        return amount

    def getTotal(self):
        return self.temp


class ReportRestOrder(models.AbstractModel):
    _name = 'report.hotel_restaurant.report_rest_order'
    _inherit = 'report.abstract_report'
    _template = 'hotel_restaurant.report_rest_order'
    _wrapped_report_class = FolioRestReport


class FolioReservReport(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(FolioReservReport, self).__init__(cr, uid, name, context)
        self.localcontext.update({'get_data': self.get_data,
                                  'gettotal': self.gettotal,
                                  'getTotal': self.getTotal,
                                  'get_reserv': self.get_reserv,
                                  })
        self.temp = 0.0

    def get_data(self, date_start, date_end):
        folio_obj = self.pool.get('hotel.folio')
        tids = folio_obj.search(self.cr, self.uid,
                                [('checkin_date', '>=', date_start),
                                 ('checkout_date', '<=', date_end)])
        res = folio_obj.browse(self.cr, self.uid, tids)
        folio_ids = []
        for rec in res:
            if rec.hotel_restaurant_order_ids:
                folio_ids.append(rec)
        return folio_ids

    def get_reserv(self, date_start, date_end):
        folio_obj = self.pool.get('hotel.folio')
        tids = folio_obj.search(self.cr, self.uid,
                                [('checkin_date', '>=', date_start),
                                 ('checkout_date', '<=', date_end)])
        res = folio_obj.browse(self.cr, self.uid, tids)
        posorder_ids = []
        for rec in res:
            if rec.hotel_restaurant_order_ids:
                posorder_ids.append(rec.hotel_restaurant_order_ids)
        return posorder_ids

    def gettotal(self, pos_order):
        amount = 0.0
        for x in pos_order:
            amount = amount + float(x.amount_total)
        self.temp = self.temp + amount
        return amount

    def getTotal(self):
        return self.temp


class ReportReservOrder(models.AbstractModel):
    _name = 'report.hotel_restaurant.report_reserv_order'
    _inherit = 'report.abstract_report'
    _template = 'hotel_restaurant.report_reserv_order'
    _wrapped_report_class = FolioReservReport

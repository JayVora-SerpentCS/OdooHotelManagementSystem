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

from openerp import models, fields, api


class HotelHousekeepingWizard(models.TransientModel):
    _name = 'hotel.housekeeping.wizard'

    date_start = fields.Datetime('Activity Start Date', required=True)
    date_end = fields.Datetime('Activity End Date', required=True)
    room_no = fields.Many2one('hotel.room', 'Room No', required=True)

    @api.multi
    def print_report(self):
        data = {
            'ids': self.ids,
            'model': 'hotel.housekeeping',
            'form': self.read(['date_start', 'date_end', 'room_no'])[0]
        }
        return self.env['report'
                        ].get_action(self,
                                     'hotel_housekeeping.report_housekeeping',
                                     data=data)

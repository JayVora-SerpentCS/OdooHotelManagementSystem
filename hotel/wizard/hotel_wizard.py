# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api


class FolioReportWizard(models.TransientModel):
    _name = 'folio.report.wizard'
    _rec_name = 'date_start'

    date_start = fields.Datetime('Start Date')
    date_end = fields.Datetime('End Date')

    @api.multi
    def print_report(self):
        data = {
            'ids': self.ids,
            'model': 'hotel.folio',
            'form': self.read(['date_start', 'date_end'])[0]
        }
        return self.env['report'].get_action(self, 'hotel.report_hotel_folio',
                                             data=data)

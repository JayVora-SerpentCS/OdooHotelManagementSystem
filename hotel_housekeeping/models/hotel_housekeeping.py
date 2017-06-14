# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import time
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductCategory(models.Model):

    _inherit = "product.category"

    isactivitytype = fields.Boolean('Is Activity Type',
                                    default=lambda *a: True)


class HotelHousekeepingActivityType(models.Model):

    _name = 'hotel.housekeeping.activity.type'
    _description = 'Activity Type'

    activity_id = fields.Many2one('product.category', 'Category',
                                  required=True, delegate=True,
                                  ondelete='cascade', index=True)


class HotelActivity(models.Model):

    _name = 'hotel.activity'
    _description = 'Housekeeping Activity'

    h_id = fields.Many2one('product.product', 'Product', required=True,
                           delegate=True, ondelete='cascade', index=True)


class HotelHousekeeping(models.Model):

    _name = "hotel.housekeeping"
    _description = "Reservation"

    current_date = fields.Date("Today's Date", required=True,
                               index=True,
                               states={'done': [('readonly', True)]},
                               default=(lambda *a:
                                        time.strftime
                                        (DEFAULT_SERVER_DATE_FORMAT)))
    clean_type = fields.Selection([('daily', 'Daily'),
                                   ('checkin', 'Check-In'),
                                   ('checkout', 'Check-Out')],
                                  'Clean Type', required=True,
                                  states={'done': [('readonly', True)]},)
    room_no = fields.Many2one('hotel.room', 'Room No', required=True,
                              states={'done': [('readonly', True)]},
                              index=True)
    activity_lines = fields.One2many('hotel.housekeeping.activities',
                                     'a_list', 'Activities',
                                     help='Detail of housekeeping activities')
    inspector = fields.Many2one('res.users', 'Inspector', required=True,
                                index=True)
    inspect_date_time = fields.Datetime('Inspect Date Time', required=True,
                                        states={'done': [('readonly', True)]})
    quality = fields.Selection([('excellent', 'Excellent'), ('good', 'Good'),
                                ('average', 'Average'), ('bad', 'Bad'),
                                ('ok', 'Ok')], 'Quality', required=True,
                               states={'done': [('readonly', True)]},
                               help="Inspector inspect the room and mark \
                                as Excellent, Average, Bad, Good or Ok. ")
    state = fields.Selection([('dirty', 'Dirty'), ('clean', 'Clean'),
                              ('inspect', 'Inspect'), ('done', 'Done'),
                              ('cancel', 'Cancelled')], 'State',
                             states={'done': [('readonly', True)]},
                             index=True, required=True, readonly=True,
                             default=lambda *a: 'dirty')

    @api.multi
    def action_set_to_dirty(self):
        """
        This method is used to change the state
        to dirty of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self.state = 'dirty'
        for line in self:
            for activity_line in line.activity_lines:
                self.activity_lines.write({'clean': False})
                self.activity_lines.write({'dirty': True})
        return True

    @api.multi
    def room_cancel(self):
        """
        This method is used to change the state
        to cancel of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self.state = 'cancel'
        return True

    @api.multi
    def room_done(self):
        """
        This method is used to change the state
        to done of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self.state = 'done'
        return True

    @api.multi
    def room_inspect(self):
        """
        This method is used to change the state
        to inspect of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self.state = 'inspect'
        return True

    @api.multi
    def room_clean(self):
        """
        This method is used to change the state
        to clean of the hotel housekeeping
        ---------------------------------------
        @param self: object pointer
        """
        self.state = 'clean'
        for line in self:
            for activity_line in line.activity_lines:
                    self.activity_lines.write({'clean': True})
                    self.activity_lines.write({'dirty': False})
        return True


class HotelHousekeepingActivities(models.Model):

    _name = "hotel.housekeeping.activities"
    _description = "Housekeeping Activities "

    a_list = fields.Many2one('hotel.housekeeping', string='Reservation')
    today_date = fields.Date('Today Date')
    activity_name = fields.Many2one('hotel.activity',
                                    string='Housekeeping Activity')
    housekeeper = fields.Many2one('res.users', string='Housekeeper',
                                  required=True)
    clean_start_time = fields.Datetime('Clean Start Time',
                                       required=True)
    clean_end_time = fields.Datetime('Clean End Time', required=True)
    dirty = fields.Boolean('Dirty',
                           help='Checked if the housekeeping activity'
                           'results as Dirty.')
    clean = fields.Boolean('Clean', help='Checked if the housekeeping'
                           'activity results as Clean.')

    @api.constrains('clean_start_time', 'clean_end_time')
    def check_clean_start_time(self):
        '''
        This method is used to validate the clean_start_time and
        clean_end_time.
        ---------------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        '''
        if self.clean_start_time >= self.clean_end_time:
            raise ValidationError(_('Start Date Should be \
            less than the End Date!'))

    @api.model
    def default_get(self, fields):
        """
        To get default values for the object.
        @param self: The object pointer.
        @param fields: List of fields for which we want default values
        @return: A dictionary which of fields with values.
        """
        if self._context is None:
            self._context = {}
        res = super(HotelHousekeepingActivities, self).default_get(fields)
        if self._context.get('room_id', False):
            res.update({'room_id': self._context['room_id']})
        if self._context.get('today_date', False):
            res.update({'today_date': self._context['today_date']})
        return res

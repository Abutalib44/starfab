# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad TK (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from pytz import timezone


class CleaningTeamDuty(models.Model):
    """Creating new model  to retrieve comprehensive details regarding
     the duties assigned to each team."""
    _name = "cleaning.team.duty"
    _description = "Cleaning Team Duty"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))

    team_leader_id = fields.Many2one('hr.employee',
                                     readonly=True,
                                     string="Team Leader",
                                     help="Choose Leader of Corresponding Team")
    team_id = fields.Many2one('cleaning.team', string='Team Name',
                              readonly=True, help="Choose Cleaning team")
    inspection_id = fields.Many2one('cleaning.inspection',
                                    string="Cleaning Inspection",
                                    help="Choose Cleaning Inspection")
    cleaning_id = fields.Many2one('cleaning.booking',
                                  string="Cleaning Booking",
                                  help="Choose Cleaning Booking")
    members_ids = fields.Many2many('hr.employee', string='Members',
                                   readonly=True,
                                   help="Choose Members Of Corresponding Team")
    location_state_id = fields.Many2one('res.country.state',
                                        string="City", readonly=True,
                                        help="Location for Team To Work")
    place = fields.Char(string="Location", readonly=True,
                        help="Enter Place For The Work")
    customer_id = fields.Many2one('res.partner', string='Customer',
                                  readonly=True, help="Choose Customer Name")
    cleaning_time = fields.Selection([('morning', 'Morning'),
                                      ('evening', 'Evening'),
                                      ('night', 'Night')],
                                     string='Shift Time',
                                     readonly=True,
                                     help="Cleaning Time, Booked By Customer")
    cleaning_date = fields.Date(string='Shift Date',
                                readonly=True,
                                help="Cleaning Date That Booked By Customer")
    inspection_boolean = fields.Boolean(string="Is Inspection", compute="_compute_inspection_boolean",
                                        help="Got 'INSPECTION' button in"
                                             " form view")
    rework_inspection_visible = fields.Boolean(string="Rework Inspection Visible", compute="_compute_rework_inspection_visible")
    rework_start_visible = fields.Boolean(string="Rework Start Visible", compute="_compute_rework_start_visible")
    start_time = fields.Char(string="Start Time", readonly=False,
                             help="Real time to complete all cleaning process")
    start_cleaning = fields.Boolean(string="Is Started")
    end_time = fields.Char(string="End Time", readonly=False,
                           help="Real time to complete all cleaning process")
    end_cleaning = fields.Boolean(string="Is Ended",
                                  help="Real time to end all cleaning process")
    duration = fields.Float(string="Duration (Hours)", compute="_compute_duration", store=True,
                            help="Difference between start time and end time in hours")
    rework_start_time = fields.Char(string="Rework Start Time", readonly=False)
    rework_end_time = fields.Char(string="Rework End Time", readonly=False)
    rework_duration = fields.Float(string="Rework Duration (Hours)", compute="_compute_rework_duration", store=True, readonly=True)
    reworked = fields.Boolean(string="Reworked", default=False, readonly=True)
    total_rework_duration = fields.Float(string="Total Rework Duration (Hours)", compute="_compute_total_rework_duration", store=False)
    total_worked_hours = fields.Float(string="Total Worked Hours (Hours)", compute="_compute_total_worked_hours", store=False)
    is_rework_completed = fields.Boolean(string="Rework Completed", compute="_compute_total_rework_duration", store=False)
    state = fields.Selection([('draft', 'Draft'),
                              ('dirty', 'Not Done'),
                              ('cleaned', 'Done'),
                              ('cancelled', 'Cancelled')],
                             default='draft', string='Status',
                             help="Stages For Cleaning Team Duty",
                             tracking=True)
    inspection_count = fields.Integer(compute="_compute_inspection_count",
                                      string='Inspection Count')

    def action_start(self):
        """Function for start cleaning processes"""
        user_tz = self.env.user.tz or 'UTC'
        start_time_utc = fields.Datetime.now()
        start_time_user_tz = fields.Datetime.to_string(
            fields.Datetime.context_timestamp(self, start_time_utc).astimezone(
                timezone(user_tz)))

        self.write({
            'start_time': start_time_user_tz,
            'start_cleaning': True
        })

    def action_finish(self):
        """Function for finish cleaning processes"""
        if self.start_cleaning:
            user_tz = self.env.user.tz or 'UTC'
            end_time_utc = fields.Datetime.now()
            end_time_user_tz = fields.Datetime.to_string(
                fields.Datetime.context_timestamp(self,
                                                  end_time_utc).astimezone(
                    timezone(user_tz)))
            self.write({
                'end_time': end_time_user_tz,
                'end_cleaning': True
            })
            start_time_utc = fields.Datetime.from_string(self.start_time)
            end_time_utc = fields.Datetime.from_string(end_time_user_tz)
            total_hours = (end_time_utc - start_time_utc).total_seconds() / 3600
            self.cleaning_id.total_hour_of_working = total_hours

    def action_inspection(self):
        """Clicking the "Inspection" button will direct the user
        to the inspection page."""
        context = {
            'default_cleaning_team_id': self.team_id.id,
            'default_inspector_name_id': self.env.user.id,
            'default_cleaning_id': self.cleaning_id.id,
            'default_cleaning_team_duty_id': self.id,
            'default_rework': self.reworked,
        }
        if self.reworked:
            context.update({
                'default_date_from': self.rework_start_time,
                'default_date_to': self.rework_end_time,
            })
        else:
            context.update({
                'default_date_from': self.start_time,
                'default_date_to': self.end_time,
            })
        return {
            'name': 'cleaning_team_id',
            'res_model': 'cleaning.inspection',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'context': context
        }

    def action_view_inspection(self):
        """Function for Open Inspection Smart Button"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Inspection',
            'view_mode': 'tree,form',
            'res_model': 'cleaning.inspection',
            'domain': [('cleaning_team_duty_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def _compute_inspection_count(self):
        """Function for getting total count of inspections"""
        for record in self:
            record.inspection_count = self.env['cleaning.inspection'].search_count(
                [('cleaning_team_duty_id', '=', record.id)])

    @api.depends('end_cleaning', 'inspection_count')
    def _compute_inspection_boolean(self):
        for rec in self:
            if not rec.end_cleaning:
                rec.inspection_boolean = True
                continue
            
            # If there's already a non-rework inspection, hide the button (inspection_boolean = True)
            non_rework_inspection = self.env['cleaning.inspection'].search([
                ('cleaning_team_duty_id', '=', rec.id),
                ('rework', '=', False)
            ], limit=1)
            if non_rework_inspection:
                rec.inspection_boolean = True
            else:
                rec.inspection_boolean = False

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                try:
                    start = fields.Datetime.from_string(rec.start_time)
                    end = fields.Datetime.from_string(rec.end_time)
                    if start and end:
                        rec.duration = (end - start).total_seconds() / 3600.0
                    else:
                        rec.duration = 0.0
                except Exception:
                    rec.duration = 0.0
            else:
                rec.duration = 0.0

    @api.depends('rework_start_time', 'rework_end_time')
    def _compute_rework_duration(self):
        for rec in self:
            if rec.rework_start_time and rec.rework_end_time:
                try:
                    start = fields.Datetime.from_string(rec.rework_start_time)
                    end = fields.Datetime.from_string(rec.rework_end_time)
                    if start and end:
                        rec.rework_duration = (end - start).total_seconds() / 3600.0
                    else:
                        rec.rework_duration = 0.0
                except Exception:
                    rec.rework_duration = 0.0
            else:
                rec.rework_duration = 0.0

    def _compute_total_rework_duration(self):
        for rec in self:
            inspections = rec.env['cleaning.inspection'].search([
                ('cleaning_team_duty_id', '=', rec.id),
                ('rework', '=', True),
                ('state', 'in', ['cleaned', 'dirty'])
            ])
            total = sum(inspections.mapped('duration'))
            rec.total_rework_duration = total
            rec.is_rework_completed = bool(total > 0)

    def _compute_total_worked_hours(self):
        for rec in self:
            rec.total_worked_hours = rec.duration + rec.total_rework_duration

    def action_start_rework(self):
        user_tz = self.env.user.tz or 'UTC'
        start_time_utc = fields.Datetime.now()
        start_time_user_tz = fields.Datetime.to_string(
            fields.Datetime.context_timestamp(self, start_time_utc).astimezone(
                timezone(user_tz)))
        self.write({
            'rework_start_time': start_time_user_tz,
            'rework_end_time': False,
            'reworked': True
        })

    def action_finish_rework(self):
        if self.rework_start_time:
            user_tz = self.env.user.tz or 'UTC'
            end_time_utc = fields.Datetime.now()
            end_time_user_tz = fields.Datetime.to_string(
                fields.Datetime.context_timestamp(self,
                                                  end_time_utc).astimezone(
                    timezone(user_tz)))
            self.write({
                'rework_end_time': end_time_user_tz,
            })

    def action_rework_inspection(self):
        # Validate that no inspection already exists with the exact same rework start/end dates
        existing = self.env['cleaning.inspection'].search([
            ('cleaning_team_duty_id', '=', self.id),
            ('date_from', '=', self.rework_start_time),
            ('date_to', '=', self.rework_end_time),
            ('rework', '=', True)
        ], limit=1)
        if existing:
            raise ValidationError("An inspection with the same rework timeframe already exists! Please start and end rework again first to record the new rework time.")

        return {
            'name': 'cleaning_team_id',
            'res_model': 'cleaning.inspection',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'context': {
                'default_cleaning_team_id': self.team_id.id,
                'default_inspector_name_id': self.env.user.id,
                'default_cleaning_id': self.cleaning_id.id,
                'default_cleaning_team_duty_id': self.id,
                'default_rework': True,
                'default_date_from': self.rework_start_time,
                'default_date_to': self.rework_end_time,
            }
        }

    @api.depends('rework_end_time', 'inspection_count')
    def _compute_rework_inspection_visible(self):
        for rec in self:
            if not rec.rework_end_time:
                rec.rework_inspection_visible = False
                continue
            
            # Find all related rework inspections
            rework_inspections = rec.env['cleaning.inspection'].search([
                ('cleaning_team_duty_id', '=', rec.id),
                ('rework', '=', True)
            ])
            
            # Check if there is any inspection in the 'cleaned' (Done) state
            has_done_inspection = any(ins.state == 'cleaned' for ins in rework_inspections)
            
            if has_done_inspection:
                rec.rework_inspection_visible = False
            else:
                rec.rework_inspection_visible = True

    @api.depends('state', 'rework_start_time', 'rework_end_time', 'inspection_count')
    def _compute_rework_start_visible(self):
        for rec in self:
            if rec.state != 'dirty':
                rec.rework_start_visible = False
                continue
            
            # Find related rework inspections
            rework_inspections = rec.env['cleaning.inspection'].search([
                ('cleaning_team_duty_id', '=', rec.id),
                ('rework', '=', True)
            ], order='create_date desc')
            
            # If there's a Done (cleaned) inspection, no more rework is allowed
            if any(ins.state == 'cleaned' for ins in rework_inspections):
                rec.rework_start_visible = False
                continue
            
            # If they haven't started rework at all
            if not rec.rework_start_time:
                rec.rework_start_visible = True
                continue
                
            # If they are currently in an active rework (started but not ended)
            if rec.rework_start_time and not rec.rework_end_time:
                rec.rework_start_visible = False
                continue
                
            # If they started and ended, check if there is an inspection.
            # If they haven't done an inspection yet, they shouldn't start a new rework until they inspect the current one.
            # If there is at least one inspection and all of them are dirty:
            if rework_inspections and all(ins.state == 'dirty' for ins in rework_inspections):
                rec.rework_start_visible = True
            else:
                rec.rework_start_visible = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('cleaning.team.duty') or _('New')
        return super(CleaningTeamDuty, self).create(vals_list)

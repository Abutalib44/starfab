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


class CleaningInspection(models.Model):
    """Create a new model for detailing cleaning inspection specifics.
    The system will incorporate two buttons to indicate the
    cleaning status: "Clean" and "Dirty"."""
    _name = "cleaning.inspection"
    _description = "Cleaning Inspection"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    inspector_name_id = fields.Many2one('res.users',
                                        string='Inspector Name',
                                        required=True,
                                        help="Choose Inspector Name")
    cleaning_id = fields.Many2one('cleaning.booking',
                                  help="Cleaning Management",
                                  string="Select Cleaning Management")
    inspection_date_and_time = fields.Datetime(
        string='Inspection Date and Time',
        required=True,
        help="Choose Inspection date and time")
    cleaning_team_id = fields.Many2one('cleaning.team',
                                       string='Shifting Team',
                                       required=True,
                                       help="Choose Shifting team")
    cleaning_team_duty_id = fields.Many2one('cleaning.team.duty',
                                            string='Team Duty',
                                            required=True,
                                            help="Choose team Duty")
    team_leader_id = fields.Many2one('hr.employee',
                                     string='Team Leader',
                                     help="Choose team leader")
    date_from = fields.Char(string='Start Time',
                            help="Choose Cleaning Start Time", readonly=True)
    date_to = fields.Char(string='End Date',
                          help="Choose Cleaning End Time", readonly=True)
    duration = fields.Float(string="Duration (Hours)", compute="_compute_duration", store=True, readonly=True)
    rework = fields.Boolean(string="Rework", default=False, readonly=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('cleaned', 'Done'),
                              ('dirty', 'Not Done')
                              ], string='Status',
                             default='draft',
                             help="Inspection stages for cleaning")
    dirty_clean = fields.Boolean('Is Dirty or Clean',
                                 help="When the button is disabled,"
                                      " it signifies a Dirty state, "
                                      "while an enabled button signifies"
                                      " a Clean state.")

    def action_clean(self):
        """The button action for "Clean" involves executing a process
         to perform cleaning tasks"""
        self.write({'state': 'cleaned', 'dirty_clean': True})
        self.cleaning_id.write({'state': 'cleaned', 'clean_stage': True,
                                'cleaning_inspection_id': self.id})
        self.cleaning_team_duty_id.write(
            {'state': 'cleaned'})
        if not self.cleaning_id.cancel_stage:
            self.cleaning_id.cancel_stage = True

    def action_dirt(self):
        """The button action for "Dirty" typically
        involves marking task as dirty. """
        self.write({'state': 'dirty', 'dirty_clean': True})
        self.cleaning_team_duty_id.write(
            {'state': 'dirty'})

    def action_reclean(self):
        """Function for Reclean processes"""
        self.write({'state': 'draft'})

    @api.depends('date_from', 'date_to')
    def _compute_duration(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                try:
                    start = fields.Datetime.from_string(rec.date_from)
                    end = fields.Datetime.from_string(rec.date_to)
                    if start and end:
                        rec.duration = (end - start).total_seconds() / 3600.0
                    else:
                        rec.duration = 0.0
                except Exception:
                    rec.duration = 0.0
            else:
                rec.duration = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('cleaning.inspection') or _('New')
        return super(CleaningInspection, self).create(vals_list)

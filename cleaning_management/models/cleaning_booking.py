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
from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class CleaningBooking(models.Model):
    """Create a new model for booking purposes.
    The system will incorporate three buttons to indicate the
    booking and cleaning status: "Confirm", "Clean" and "Cancel"."""
    _name = "cleaning.booking"
    _description = "Cleaning Booking"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))

    def _default_cleaning_team_ids(self):
        """Returns default values for cleaning_team_ids records"""
        return self.env['cleaning.team'].search([]).ids

    customer_name_id = fields.Many2one('res.partner',
                                       string='Name of Customer',
                                       required=True,
                                       help="Choose customer name")
    address = fields.Char(string='Address',
                          required=True,
                          help="Enter address of customer")
    building_type_id = fields.Many2one('building.type',
                                       string='Facility Type',
                                       required=True,
                                       help="Choose facility type")
    service_type_ids = fields.Many2many('cleaning.service.type',
                                        string='Service Types',
                                        help="Choose Service Types under the selected Facility Type",
                                        domain="[('facility_type_id', '=', building_type_id)]")
    raw_material_line_ids = fields.One2many('cleaning.booking.raw.material.line', 'booking_id', string="Raw Material Costs")
    labor_cost_line_ids = fields.One2many('cleaning.booking.labor.cost.line', 'booking_id', string="Labor Costs")
    total_raw_material_cost = fields.Float(string="Total Raw Material Cost", compute='_compute_total_costs')
    total_labor_cost = fields.Float(string="Total Labor Cost", compute='_compute_total_costs')
    booking_date = fields.Date(help="Choose the booking date",
                               string='SO Date')
    cleaning_team_ids = fields.Many2many('cleaning.team',
                                         string='Work Order Teams',
                                         help="Store work order team based on "
                                              "cleaning_time",
                                              default=_default_cleaning_team_ids
                                         )
    cleaning_team_id = fields.Many2one('cleaning.team',
                                       string='Shifting Team',
                                       help="Choose work order team",
                                       required=False,)
    cleaning_inspection_id = fields.Many2one('cleaning.inspection',
                                             string="Cleaning Inspection",
                                             help="Choose Cleaning Inspection")
    cleaning_team_duty_id = fields.Many2one('cleaning.team.duty',
                                            string="Cleaning Team Duty",
                                            help="Choose Cleaning Team Duty")
    cleaning_date = fields.Date(string='Work Order Date',
                                required=False,
                                help="Choose Date for work order")
    cleaning_time = fields.Selection([('morning', 'Morning'),
                                      ('evening', 'Evening'),
                                      ('night', 'Night')],
                                     string='Shift Time',
                                     help="Choose Time for work order",
                                     required=False)
    sale_order_id = fields.Many2one('sale.order', string="Sales Order", readonly=True)
    description = fields.Char(string='Description',
                              help="Enter Description For Booking")
    duration = fields.Selection([('forever', 'Forever'),
                                 ('fixed', 'Fixed')],
                                default='forever', string='Duration',
                                help="Choose Duration For Cleaning")
    end_after = fields.Integer(string='End After',
                               help="Choose End of cleaning management")
    end_duration = fields.Selection([('months', 'Months'),
                                     ('years', 'Years')],
                                    string="End Duration",
                                    help="Choose End duration of booking")
    cleaning_shift_id = fields.Many2one("cleaning.shift",
                                        help="Cleaning Shift",
                                        string="Choose Cleaning Shift")
    self_closable = fields.Boolean(string='Is Self Closable',
                                   help="When checked reservations will"
                                        "be automatically closed.")
    automatic_closing = fields.Integer(string='Automatic Closing',
                                       help="Automatic Closing Chooser")
    location_state_id = fields.Many2one('res.country.state',
                                        string="City",
                                        required=False,
                                        help="Choose City For Cleaning")
    place = fields.Char(string="Location", help="Enter Place of Customer")
    state = fields.Selection([('draft', 'Draft'),
                              ('booked', 'WO Running'),
                              ('cleaned', 'Team Done'),
                              ('done', 'WO Done'),
                              ('cancelled', 'Cancelled')],
                             default='draft', string='Status',
                             help="Stages For Cleaning Processes",
                             tracking=True)
    confirm_stage = fields.Boolean(string="Is Confirm", default=True,
                                   help="When checked,the status" ""
                                        "will be 'Confirm'.")
    clean_stage = fields.Boolean(string="Clean", default=True,
                                 help="When checked,the status will be 'Clean'")
    cancel_stage = fields.Boolean(string="Cancel", default=True,
                                  help="When checked,the status"
                                       "will be 'Cancel'.")
    unit_price = fields.Float(string="Unit Price", default=0.0, required=True,
                              help="Uit Price for an hour")
    total_hour_of_working = fields.Char(string="Total working hours",
                                        help="Total working hours done by Team")
    invoice_count = fields.Integer(compute="_compute_invoice_count",
                                   string='Invoice Count')
    total_man_hours = fields.Float(string="Total Man-Hours", compute='_compute_total_costs')
    total_overhead_cost = fields.Float(string="Total Overhead Cost", compute='_compute_total_costs')
    total_wo_cost = fields.Float(string="Total WO Cost", compute='_compute_total_costs')
    entry_count = fields.Integer(compute="_compute_entry_count", string='Entry Count')
    all_inspection_count = fields.Integer(compute="_compute_all_inspection_count", string='Inspection Count')

    @api.onchange('cleaning_time')
    def _onchange_cleaning_time(self):
        """The team leader will appear at the scheduled cleaning time."""
        domain = []
        if self.cleaning_time:
            res = self.env['cleaning.team.duty'].search(
                [('cleaning_date', '=', self.cleaning_date),
                 ('cleaning_time', '=', self.cleaning_time),
                 ('state', 'not in', ['cancelled', 'cleaned'])])
            if res:
                domain = [('duty_type', '=', self.cleaning_time),
                          ('id', 'not in', [duty.team_id.id for duty in res])]
            else:
                domain.append(('duty_type', '=', self.cleaning_time))
            self.write({'cleaning_team_ids': [(6, 0, self.env
                ['cleaning.team'].search(domain).ids)]})

    @api.onchange('cleaning_team_id')
    def _onchange_cleaning_team_id(self):
        """The team leader's time will appear when changing the leader and populate labor lines."""
        self.cleaning_time = self.cleaning_team_id.duty_type
        if self.cleaning_team_id:
            labor_lines = []
            for member in self.cleaning_team_id.members_ids:
                employee = member.employee_name_id._origin or member.employee_name_id
                if employee and employee.id and isinstance(employee.id, int):
                    labor_lines.append((0, 0, {
                        'employee_id': employee.id,
                        'cost_per_hour': member.cost_per_hour,
                    }))
            self.labor_cost_line_ids = [(5, 0, 0)] + labor_lines
        else:
            self.labor_cost_line_ids = [(5, 0, 0)]

    @api.onchange('building_type_id')
    def _onchange_building_type_id(self):
        """Reset service type selection if the Facility Type changes."""
        self.service_type_ids = [(5, 0, 0)]

    def action_booking(self):
        """The button action for "Confirm" typically involves
        finalizing and saving the booking details entered
        by the user."""
        duty_ids_to_add = []
        for rec in self:
            if not rec.cleaning_team_id:
                raise UserError(_("Please select a Shifting Team before confirming the Work Order."))
            if not rec.cleaning_time:
                raise UserError(_("Please select a Shift Time before confirming the Work Order."))
            
            cleaning_team_duty = rec.cleaning_team_duty_id.create({
                "team_id": rec.cleaning_team_id.id if rec.cleaning_team_id else False,
                "team_leader_id": rec.cleaning_team_id.team_leader_id.employee_name_id.id if rec.cleaning_team_id and rec.cleaning_team_id.team_leader_id else False,
                "members_ids": rec.cleaning_team_id.members_ids.ids if rec.cleaning_team_id else [],
                "location_state_id": rec.location_state_id.id if rec.location_state_id else False,
                "place": rec.place or '',
                "customer_id": rec.customer_name_id.id if rec.customer_name_id else False,
                "cleaning_date": rec.cleaning_date or False,
                "cleaning_time": rec.cleaning_time or False,
                "cleaning_id": rec.id
            })
            rec.write(
                {'state': 'booked', 'confirm_stage': False,
                 'clean_stage': False,
                 'cancel_stage': False,
                 'cleaning_team_duty_id': cleaning_team_duty.id})
            duty_ids_to_add.append((4, cleaning_team_duty.id))
            
            # Confirm the linked Sales Order
            if rec.sale_order_id and rec.sale_order_id.state in ['draft', 'sent', 'wo_running']:
                rec.sale_order_id.action_confirm()

    def action_cancel(self):
        """The button action for "Cancel" typically involves canceling
         and removing a booking that was previously confirmed or reserved."""
        for rec in self:
            rec.cleaning_team_duty_id.write({'state': 'cancelled'})
            rec.write(
                {'state': 'cancelled', 'confirm_stage': False,
                 'cancel_stage': True,
                 'clean_stage': True})

    def action_create_invoice(self):
        """Function for create an invoice for cleaning processes"""
        for rec in self:
            if rec.unit_price > 0.0:
                invoice = rec.env['account.move'].create({
                    'move_type': 'out_invoice',
                    'partner_id': rec.customer_name_id.id,
                    'invoice_date': date.today(),
                    'payment_reference': rec.cleaning_date,
                    'cleaning_id': rec.id,
                    'invoice_line_ids': [(0, 0, {
                        'name': f"{rec.cleaning_team_id.name} ({rec.cleaning_inspection_id.inspection_date_and_time})",
                        'price_unit': float(rec.unit_price) * float(
                            rec.total_hour_of_working),
                    })],
                })
                return {
                    'name': 'account.move.form',
                    'res_model': 'account.move',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'view_id': rec.env.ref("account.view_move_form").id,
                    'res_id': invoice.id,
                    'target': 'current'
                }
            else:
                raise ValidationError(_("Specify the Unit Price for a hour"))

    def action_view_invoice(self):
        """Function for open Invoice Smart Button"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('cleaning_id', '=', self.id), ('move_type', 'in', ('out_invoice', 'out_refund'))],
            'context': "{'create': False}"
        }

    def action_view_entries(self):
        """Function for open Journal Entries Smart Button"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Journal Entries',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('cleaning_id', '=', self.id), ('move_type', '=', 'entry')],
            'context': "{'create': False}"
        }

    def action_view_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Order'),
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
            'target': 'current',
        }

    def action_view_team_duty(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Team Duty'),
            'res_model': 'cleaning.team.duty',
            'view_mode': 'form',
            'res_id': self.cleaning_team_duty_id.id,
            'target': 'current',
        }

    def action_view_all_inspections(self):
        """Show all inspections related to this Work Order"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Inspections',
            'view_mode': 'tree,form',
            'res_model': 'cleaning.inspection',
            'domain': [('cleaning_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def _compute_invoice_count(self):
        """Function for count number of Invoices"""
        for record in self:
            record.invoice_count = self.env['account.move'].search_count(
                [('cleaning_id', '=', record.id), ('move_type', 'in', ('out_invoice', 'out_refund'))])

    def _compute_entry_count(self):
        """Function for count number of Journal Entries"""
        for record in self:
            record.entry_count = self.env['account.move'].search_count(
                [('cleaning_id', '=', record.id), ('move_type', '=', 'entry')])

    def _compute_all_inspection_count(self):
        """Function for count number of Inspections"""
        for record in self:
            record.all_inspection_count = self.env['cleaning.inspection'].search_count(
                [('cleaning_id', '=', record.id)])

    @api.depends('raw_material_line_ids.total_cost', 'labor_cost_line_ids.total_cost', 'cleaning_team_duty_id.total_worked_hours', 'labor_cost_line_ids')
    def _compute_total_costs(self):
        overhead_unit_cost = float(self.env['ir.config_parameter'].sudo().get_param('cleaning_management.overhead_unit_cost', 0.0))
        for rec in self:
            rec.total_raw_material_cost = sum(rec.raw_material_line_ids.mapped('total_cost') or [0.0])
            rec.total_labor_cost = sum(rec.labor_cost_line_ids.mapped('total_cost') or [0.0])
            
            # Man-Hours = Total Worked Hours * Number of Employees
            total_worked_hours = rec.cleaning_team_duty_id.total_worked_hours or 0.0
            num_employees = len(rec.labor_cost_line_ids)
            rec.total_man_hours = total_worked_hours * num_employees
            
            rec.total_overhead_cost = rec.total_man_hours * overhead_unit_cost
            rec.total_wo_cost = rec.total_raw_material_cost + rec.total_labor_cost + rec.total_overhead_cost

    def action_done(self):
        """Action button to create 4 journal entries and set state to Done"""
        self.ensure_one()
        if self.state != 'cleaned':
            raise UserError(_("Work Order must be in 'Team Done' state to finalize."))

        # Get accounts from settings
        config = self.env['ir.config_parameter'].sudo()
        wip_account_id = int(config.get_param('cleaning_management.wip_account_id', 0))
        cogs_account_id = int(config.get_param('cleaning_management.cogs_account_id', 0))
        valuation_account_id = int(config.get_param('cleaning_management.valuation_account_id', 0))
        labor_cost_account_id = int(config.get_param('cleaning_management.labor_cost_account_id', 0))
        overhead_cost_account_id = int(config.get_param('cleaning_management.overhead_cost_account_id', 0))

        if not all([wip_account_id, cogs_account_id, valuation_account_id, labor_cost_account_id, overhead_cost_account_id]):
            raise UserError(_("Please configure all accounting accounts in Settings > Service Management."))

        wo_journal_id = int(config.get_param('cleaning_management.wo_journal_id', 0))
        if not wo_journal_id:
            raise UserError(_("Please configure the Service Journal in Settings > Service Management."))
        journal = self.env['account.journal'].browse(wo_journal_id)
        if not journal.exists():
            raise UserError(_("The configured Service Journal does not exist."))

        # Entry 1: Raw Material (WIP Debit, Valuation Credit)
        if self.total_raw_material_cost > 0:
            self._create_journal_entry(
                journal, wip_account_id, valuation_account_id, 
                self.total_raw_material_cost, f"Raw Material Cost - {self.description or ''} - {self.customer_name_id.name}"
            )

        # Entry 2: Labor Cost (WIP Debit, Labor Cost Credit)
        if self.total_labor_cost > 0:
            self._create_journal_entry(
                journal, wip_account_id, labor_cost_account_id, 
                self.total_labor_cost, f"Labor Cost - {self.description or ''} - {self.customer_name_id.name}"
            )

        # Entry 3: Overhead Cost (WIP Debit, Overhead Cost Credit)
        if self.total_overhead_cost > 0:
            self._create_journal_entry(
                journal, wip_account_id, overhead_cost_account_id, 
                self.total_overhead_cost, f"Overhead Cost - {self.description or ''} - {self.customer_name_id.name}"
            )

        # Entry 4: Total WO Cost (COGS Debit, WIP Credit)
        if self.total_wo_cost > 0:
            self._create_journal_entry(
                journal, cogs_account_id, wip_account_id, 
                self.total_wo_cost, f"Total WO Cost - {self.description or ''} - {self.customer_name_id.name}"
            )

        self.write({'state': 'done'})
        if self.sale_order_id and self.sale_order_id.state == 'wo_running':
            self.sale_order_id.write({'state': 'sale'})

    def _create_journal_entry(self, journal, debit_account, credit_account, amount, ref):
        move = self.env['account.move'].create({
            'journal_id': journal.id,
            'ref': ref,
            'move_type': 'entry',
            'cleaning_id': self.id,
            'line_ids': [
                (0, 0, {
                    'name': ref,
                    'account_id': debit_account,
                    'debit': amount,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': ref,
                    'account_id': credit_account,
                    'debit': 0.0,
                    'credit': amount,
                }),
            ]
        })
        move.action_post()
        return move

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('cleaning.booking') or _('New')
        return super(CleaningBooking, self).create(vals_list)


class CleaningBookingRawMaterialLine(models.Model):
    _name = 'cleaning.booking.raw.material.line'
    _description = 'Raw Material Cost Line'

    booking_id = fields.Many2one('cleaning.booking', string="Booking", ondelete='cascade')
    product_id = fields.Many2one('product.product', string="Product", required=True)
    qty = fields.Float(string="Quantity", default=1.0)
    unit_cost = fields.Float(string="Unit Cost", related='product_id.standard_price', readonly=True, store=True)
    total_cost = fields.Float(string="Total Cost", compute='_compute_total_cost')

    @api.depends('qty', 'unit_cost')
    def _compute_total_cost(self):
        for rec in self:
            qty = rec.qty or 0.0
            unit_cost = rec.unit_cost or 0.0
            rec.total_cost = qty * unit_cost


class CleaningBookingLaborCostLine(models.Model):
    _name = 'cleaning.booking.labor.cost.line'
    _description = 'Labor Cost Line'

    booking_id = fields.Many2one('cleaning.booking', string="Booking", ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    worked_hours = fields.Float(string="Worked Hours", compute='_compute_worked_hours', readonly=True)
    cost_per_hour = fields.Float(string="Cost per Hour", compute='_compute_cost_per_hour', readonly=False)
    total_cost = fields.Float(string="Total Cost", compute='_compute_total_cost')

    @api.depends('booking_id.cleaning_team_duty_id.total_worked_hours')
    def _compute_worked_hours(self):
        for rec in self:
            rec.worked_hours = rec.booking_id.cleaning_team_duty_id.total_worked_hours or 0.0

    @api.depends('employee_id')
    def _compute_cost_per_hour(self):
        for rec in self:
            employee = rec.employee_id._origin or rec.employee_id
            if employee and employee.id and isinstance(employee.id, int):
                emp_detail = self.env['employee.details'].search([('employee_name_id', '=', employee.id)], limit=1)
                rec.cost_per_hour = emp_detail.cost_per_hour if emp_detail else 0.0
            else:
                rec.cost_per_hour = 0.0

    @api.depends('worked_hours', 'cost_per_hour')
    def _compute_total_cost(self):
        for rec in self:
            worked_hours = rec.worked_hours or 0.0
            cost_per_hour = rec.cost_per_hour or 0.0
            rec.total_cost = worked_hours * cost_per_hour

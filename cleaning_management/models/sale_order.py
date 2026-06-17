# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(
        selection=[
            ('draft', "Quotation"),
            ('sent', "Quotation Sent"),
            ('wo_running', "WO Running"),
            ('sale', "WO Done"),
            ('cancel', "Cancelled"),
        ],
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft'
    )

    booking_address = fields.Char(string='Address')
    building_type_id = fields.Many2one('building.type', string='Facility Type')
    description = fields.Char(string='Description')
    work_order_date = fields.Date(string='Work Order Date')
    location_state_id = fields.Many2one('res.country.state', string='City')
    place = fields.Char(string='Location')

    booking_ids = fields.One2many('cleaning.booking', 'sale_order_id', string='Work Orders')
    booking_count = fields.Integer(compute='_compute_booking_count', string='Work Order Count')

    @api.depends('booking_ids')
    def _compute_booking_count(self):
        for order in self:
            order.booking_count = len(order.booking_ids)

    def action_create_work_order(self):
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("Please select a Customer first."))
        if not self.booking_address:
            # Fallback to partner address if not explicitly filled
            self.booking_address = self.partner_id.street
        
        booking_obj = self.env['cleaning.booking']
        booking_vals = {
            'customer_name_id': self.partner_id.id,
            'address': self.booking_address or '',
            'booking_date': self.date_order,
            'building_type_id': self.building_type_id.id if self.building_type_id else False,
            'description': self.description or '',
            'cleaning_date': self.work_order_date,
            'location_state_id': self.location_state_id.id if self.location_state_id else False,
            'place': self.place or '',
            'sale_order_id': self.id,
        }
        booking = booking_obj.create(booking_vals)
        self.write({'state': 'wo_running'})
        
        return {
            'name': _('Work Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'cleaning.booking',
            'view_mode': 'form',
            'res_id': booking.id,
            'target': 'current',
        }

    def action_view_work_orders(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Work Orders'),
            'res_model': 'cleaning.booking',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'default_sale_order_id': self.id},
        }
        if len(self.booking_ids) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = self.booking_ids[0].id
        else:
            action['view_mode'] = 'tree,form'
        return action



    def _can_be_confirmed(self):
        self.ensure_one()
        return self.state in {'draft', 'sent','wo_running'}
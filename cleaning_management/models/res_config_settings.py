# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    overhead_unit_cost = fields.Float(string="Overhead Unit Cost",
                                      config_parameter='cleaning_management.overhead_unit_cost')
    wip_account_id = fields.Many2one('account.account', string="WIP Account",
                                     domain=[('account_type', '=', 'asset_current')])
    cogs_account_id = fields.Many2one('account.account', string="Cost of Goods Sold Account")
    valuation_account_id = fields.Many2one('account.account', string="Valuation Account (Evaluate)",
                                            domain=[('account_type', '=', 'asset_current')])
    labor_cost_account_id = fields.Many2one('account.account', string="Labor Cost Account",
                                             domain=[('account_type', '=', 'expense')])
    overhead_cost_account_id = fields.Many2one('account.account', string="Overhead Cost Account",
                                                domain=[('account_type', '=', 'expense')])
    wo_journal_id = fields.Many2one('account.journal', string="Journal")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            wip_account_id=int(params.get_param('cleaning_management.wip_account_id', 0)) or False,
            cogs_account_id=int(params.get_param('cleaning_management.cogs_account_id', 0)) or False,
            valuation_account_id=int(params.get_param('cleaning_management.valuation_account_id', 0)) or False,
            labor_cost_account_id=int(params.get_param('cleaning_management.labor_cost_account_id', 0)) or False,
            overhead_cost_account_id=int(params.get_param('cleaning_management.overhead_cost_account_id', 0)) or False,
            wo_journal_id=int(params.get_param('cleaning_management.wo_journal_id', 0)) or False,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('cleaning_management.wip_account_id', self.wip_account_id.id or 0)
        params.set_param('cleaning_management.cogs_account_id', self.cogs_account_id.id or 0)
        params.set_param('cleaning_management.valuation_account_id', self.valuation_account_id.id or 0)
        params.set_param('cleaning_management.labor_cost_account_id', self.labor_cost_account_id.id or 0)
        params.set_param('cleaning_management.overhead_cost_account_id', self.overhead_cost_account_id.id or 0)
        params.set_param('cleaning_management.wo_journal_id', self.wo_journal_id.id or 0)

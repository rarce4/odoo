# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    mrp_production_count = fields.Integer(
        "Count of MO generated",
        compute='_compute_mrp_production_ids',
        groups='mrp.group_mrp_user')
    mrp_production_ids = fields.Many2many(
        'mrp.production',
        compute='_compute_mrp_production_ids',
        string='Manufacturing orders associated with this sales order.',
        groups='mrp.group_mrp_user')

    @api.depends('procurement_group_id.stock_move_ids.created_production_id.procurement_group_id.mrp_production_ids')
    def _compute_mrp_production_ids(self):
        data = self.env['procurement.group']._read_group([('sale_id', 'in', self.ids)], ['sale_id'], ['id:recordset'])
        production_order_by_sale_line = self.env['mrp.production']._read_group([('sale_line_id', 'in', self.order_line.ids)], ['sale_line_id'], ['id:recordset'])
        mrp_productions = defaultdict(self.env['mrp.production'].browse)
        for sale, procurement_groups in data:
            mrp_productions[sale.id] |= procurement_groups.stock_move_ids.created_production_id.procurement_group_id.mrp_production_ids | procurement_groups.mrp_production_ids
        for sale_line, production_id in production_order_by_sale_line:
            mrp_productions[sale_line.order_id.id] |= production_id
        for sale in self:
            mrp_production_ids = mrp_productions[sale.id]
            sale.mrp_production_count = len(mrp_production_ids)
            sale.mrp_production_ids = mrp_production_ids

    def action_view_mrp_production(self):
        self.ensure_one()
        action = {
            'res_model': 'mrp.production',
            'type': 'ir.actions.act_window',
        }
        if len(self.mrp_production_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': self.mrp_production_ids.id,
            })
        else:
            action.update({
                'name': _("Manufacturing Orders Generated by %s", self.name),
                'domain': [('id', 'in', self.mrp_production_ids.ids)],
                'view_mode': 'list,form',
            })
        return action

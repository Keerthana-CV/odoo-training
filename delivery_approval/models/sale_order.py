from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):
        res = super()._action_confirm()
        # deliveries exist now, so create the approval lines
        self.picking_ids._create_approval_lines()
        return res
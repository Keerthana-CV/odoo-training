from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    auto_confirm = fields.Boolean(string="Auto Confirm")

    def action_confirm(self):
        res = super().action_confirm()

        for order in self:
            if order.auto_confirm:
                

                for picking in order.picking_ids:
                    

                    if picking.state not in ("done", "cancel"):

                        # Reserve stock
                        picking.action_assign()

                        picking.button_validate()
                        
               

        return res
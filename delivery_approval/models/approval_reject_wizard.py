from odoo import models, fields


class DeliveryApprovalRejectWizard(models.TransientModel):
    _name = 'delivery.approval.reject.wizard'
    _description = 'Reject Delivery Wizard'

    picking_id = fields.Many2one('stock.picking', required=True)
    remarks = fields.Text(string='Reason', required=True)

    def action_confirm(self):
        self.ensure_one()
        self.picking_id.action_reject_delivery(self.remarks)
        return {'type': 'ir.actions.act_window_close'}
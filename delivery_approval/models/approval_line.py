from odoo import models, fields, _
from odoo.exceptions import UserError


class DeliveryApprovalLine(models.Model):
    _name = 'delivery.approval.line'
    _description = 'Delivery Approval Line'
    _order = 'sequence, id'

    picking_id = fields.Many2one(
        'stock.picking', string='Transfer', required=True,
        ondelete='cascade', index=True)
    level_id = fields.Many2one(
        'delivery.approval.level', string='Approval Level',
        required=True, ondelete='restrict')
    sequence = fields.Integer(
        related='level_id.sequence', store=True)
    approver_ids = fields.Many2many(
        related='level_id.approver_ids', string='Approvers')
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='pending', required=True)
    action_user_id = fields.Many2one(
        'res.users', string='Actioned By', readonly=True)
    action_date = fields.Datetime(string='Action Date', readonly=True)
    remarks = fields.Text(string='Remarks')

    def _check_can_action(self):
        """Raise an error if the current user cannot approve/reject."""
        self.ensure_one()
        if self.picking_id.state in ('done', 'cancel'):
            raise UserError(_("This transfer is already done or cancelled."))
        if self.state != 'pending':
            raise UserError(_("'%s' has already been actioned.")
                            % self.level_id.name)
        if self.env.user not in self.approver_ids:
            raise UserError(_("You are not an approver for '%s'.")
                            % self.level_id.name)
        previous = self.picking_id.approval_line_ids.filtered(
            lambda l: l.sequence < self.sequence and l.state != 'approved')
        if previous:
            raise UserError(_("'%s' must be approved first.")
                            % previous[0].level_id.name)

    def action_approve(self):
        for line in self:
            line._check_can_action()
            line.sudo().write({
                'state': 'approved',
                'action_user_id': self.env.user.id,
                'action_date': fields.Datetime.now(),
            })
            line.picking_id.message_post(
                body=_("%s approved by %s.")
                % (line.level_id.name, self.env.user.name))

    def action_reject(self, remarks):
        for line in self:
            line._check_can_action()
            line.sudo().write({
                'state': 'rejected',
                'action_user_id': self.env.user.id,
                'action_date': fields.Datetime.now(),
                'remarks': remarks,
            })
            line.picking_id.message_post(
                body=_("%s rejected by %s. Reason: %s")
                % (line.level_id.name, self.env.user.name, remarks))
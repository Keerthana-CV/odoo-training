from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    approval_line_ids = fields.One2many(
        'delivery.approval.line', 'picking_id', string='Approvals')
    approval_state = fields.Selection([
        ('not_required', 'Not Required'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Approval Status', compute='_compute_approval_state',
        store=True)
    can_approve = fields.Boolean(compute='_compute_can_approve')

    @api.depends('approval_line_ids.state')
    def _compute_approval_state(self):
        for picking in self:
            states = picking.approval_line_ids.mapped('state')
            if not states:
                picking.approval_state = 'not_required'
            elif 'rejected' in states:
                picking.approval_state = 'rejected'
            elif all(s == 'approved' for s in states):
                picking.approval_state = 'approved'
            else:
                picking.approval_state = 'pending'

    @api.depends('approval_state')
    def _compute_show_validate(self):
        # Odoo's normal rules first, then hide Validate while approvals
        # are still pending or were rejected
        super()._compute_show_validate()
        for picking in self:
            if picking.approval_state in ('pending', 'rejected'):
                picking.show_validate = False

    @api.depends('approval_line_ids.state', 'state')
    @api.depends_context('uid')
    def _compute_can_approve(self):
        for picking in self:
            line = picking._get_current_approval_line()
            picking.can_approve = bool(
                line
                and picking.state not in ('done', 'cancel')
                and self.env.user in line.approver_ids)

    def _get_current_approval_line(self):
        """Return the line waiting for action (first level not approved)."""
        self.ensure_one()
        for line in self.approval_line_ids.sorted('sequence'):
            if line.state != 'approved':
                return line if line.state == 'pending' \
                    else self.env['delivery.approval.line']
        return self.env['delivery.approval.line']

    def action_approve_delivery(self):
        for picking in self:
            line = picking._get_current_approval_line()
            if not line:
                raise UserError(_("There is nothing to approve."))
            line.action_approve()

    def action_open_reject_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Delivery'),
            'res_model': 'delivery.approval.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_picking_id': self.id},
        }

    def action_reject_delivery(self, remarks):
        for picking in self:
            line = picking._get_current_approval_line()
            if not line:
                raise UserError(_("There is nothing to reject."))
            line.action_reject(remarks)

    def action_reset_approval(self):
        if not self.env.user.has_group('stock.group_stock_manager'):
            raise UserError(_("Only Inventory Managers can reset approvals."))
        for picking in self:
            if picking.state in ('done', 'cancel'):
                raise UserError(_("This transfer is already done or cancelled."))
            if picking.approval_state != 'rejected':
                raise UserError(_("Only rejected approvals can be reset."))
            picking.approval_line_ids.sudo().write({
                'state': 'pending',
                'action_user_id': False,
                'action_date': False,
                'remarks': False,
            })
            picking.message_post(
                body=_("Approvals were reset to pending by %s.")
                % self.env.user.name)

    def button_validate(self):
        # Safety net: the button is hidden, but this also blocks automatic
        # or programmatic validation
        for picking in self:
            if picking.approval_state == 'rejected':
                raise UserError(_(
                    "Transfer %s cannot be validated because an approval "
                    "was rejected.") % picking.name)
            if picking.approval_state == 'pending':
                waiting = picking.approval_line_ids.filtered(
                    lambda l: l.state != 'approved')
                raise UserError(_(
                    "Transfer %s cannot be validated until all approvals "
                    "are completed.\nWaiting for: %s")
                    % (picking.name,
                       ", ".join(waiting.mapped('level_id.name'))))
        return super().button_validate()

    @api.model_create_multi
    def create(self, vals_list):
        pickings = super().create(vals_list)
        pickings._create_approval_lines()
        return pickings

    def _create_approval_lines(self):
        Level = self.env['delivery.approval.level'].sudo()
        for picking in self:
            if (picking.approval_line_ids
                    or picking.picking_type_code != 'outgoing'
                    or not picking.sale_id):
                continue
            levels = Level.search([
                ('company_id', 'in', [picking.company_id.id, False]),
            ])
            picking.sudo().write({
                'approval_line_ids': [
                    Command.create({'level_id': level.id})
                    for level in levels
                ],
            })
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class DeliveryApprovalLevel(models.Model):
    _name = 'delivery.approval.level'
    _description = 'Delivery Approval Level'
    _order = 'sequence, id'

    name = fields.Char(string='Level Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10, required=True)
    approver_ids = fields.Many2many(
        'res.users', string='Approvers', required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company)

    @api.constrains('sequence', 'company_id')
    def _check_unique_sequence(self):
        for rec in self:
            duplicate = self.search([
                ('id', '!=', rec.id),
                ('sequence', '=', rec.sequence),
                ('company_id', '=', rec.company_id.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(
                    _("Sequence %s is already used by '%s'.")
                    % (rec.sequence, duplicate.name))
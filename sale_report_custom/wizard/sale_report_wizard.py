from odoo import models, fields, api
from odoo.exceptions import UserError


class SaleReportWizard(models.TransientModel):
    _name = 'sale.report.wizard'
    _description = 'Sales Report Wizard'

    date_from = fields.Datetime(string='From Date', required=True)
    date_to = fields.Datetime(string='To Date', required=True)
    partner_ids = fields.Many2many('res.partner', string='Customers')
    product_id = fields.Many2one('product.product', string='Product')

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise UserError("From Date cannot be after To Date.")

    def _get_report_lines(self):
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('move_id.state', '=', 'posted'),
            ('move_id.create_date', '>=', self.date_from),
            ('move_id.create_date', '<=', self.date_to),
        ]
        if self.partner_ids:
            domain += [
                '|',
                ('move_id.partner_id', 'in', self.partner_ids.ids),
                ('move_id.commercial_partner_id', 'in', self.partner_ids.ids),
            ]
        if self.product_id:
            domain.append(('product_id', '=', self.product_id.id))

        lines = self.env['account.move.line'].search(domain, order='move_id, id')
        return lines.sorted(key=lambda l: (l.move_id.partner_id.name or '', l.move_id.id, l.id))

    def action_print_report(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/sale_report_custom/xlsx/{self.id}',
            'target': 'self',
        }

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleReturnLineWizard(models.TransientModel):
    _name = 'sale.return.line.wizard'
    _description = 'Select Sale Order Lines to Return'

    return_order_id = fields.Many2one('sale.order', string='Return Order', required=True)
    origin_sale_order_id = fields.Many2one('sale.order', string='Original Sale Order', required=True)
    line_ids = fields.One2many('sale.return.line.wizard.line', 'wizard_id', string='Lines')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        origin_id = res.get('origin_sale_order_id')
        if origin_id:
            origin = self.env['sale.order'].browse(origin_id)
            lines = []
            for line in origin.order_line:
                if line.display_type:
                    continue
                already_returned = self._get_already_returned_qty(line)
                max_returnable = line.product_uom_qty - already_returned
                if max_returnable <= 0:
                    continue
                lines.append((0, 0, {
                    'origin_line_id': line.id,
                    'product_id': line.product_id.id,
                    'ordered_qty': line.product_uom_qty,
                    'already_returned_qty': already_returned,
                    'max_returnable_qty': max_returnable,
                    'return_qty': max_returnable,
                    'selected': True,
                }))
            res['line_ids'] = lines
        return res

    def _get_already_returned_qty(self, origin_line):
        return_lines = self.env['sale.order.line'].search([
            ('origin_order_line_id', '=', origin_line.id),
            ('order_id.state', '!=', 'cancel'),
        ])
        return sum(return_lines.mapped('product_uom_qty'))

    def action_confirm_copy(self):
        self.ensure_one()
        _logger.info("=== WIZARD DEBUG: total lines = %s", len(self.line_ids))
        for l in self.line_ids:
            _logger.info(
                "=== LINE: id=%s selected=%s origin_line_id=%s return_qty=%s",
                l.id, l.selected, l.origin_line_id.id, l.return_qty
            )

        selected_lines = self.line_ids.filtered(lambda l: l.selected and l.origin_line_id)
        if not selected_lines:
            raise UserError("Please select at least one line to return.")

        for wiz_line in selected_lines:
            origin_line = wiz_line.origin_line_id
            already_returned = self._get_already_returned_qty(origin_line)
            max_returnable = origin_line.product_uom_qty - already_returned
            return_qty = wiz_line.return_qty

            if return_qty <= 0:
                raise UserError(f"Return quantity for {origin_line.product_id.name} must be greater than zero.")
            if return_qty > max_returnable:
                raise UserError(
                    f"Cannot return {return_qty} of {origin_line.product_id.name} — "
                    f"only {max_returnable} remaining to return."
                )

            self.env['sale.order.line'].create({
                'order_id': self.return_order_id.id,
                'product_id': origin_line.product_id.id,
                'product_uom_qty': return_qty,
                'product_uom': origin_line.product_uom.id,
                'price_unit': origin_line.price_unit,
                'origin_order_line_id': origin_line.id,
            })
        return {'type': 'ir.actions.act_window_close'}


class SaleReturnLineWizardLine(models.TransientModel):
    _name = 'sale.return.line.wizard.line'
    _description = 'Sale Return Wizard Line'

    wizard_id = fields.Many2one('sale.return.line.wizard', string='Wizard')
    origin_line_id = fields.Many2one('sale.order.line', string='Original Line')
    product_id = fields.Many2one('product.product', string='Product')
    ordered_qty = fields.Float(string='Ordered Qty')
    already_returned_qty = fields.Float(string='Already Returned')
    max_returnable_qty = fields.Float(string='Max Returnable')
    return_qty = fields.Float(string='Qty to Return')
    selected = fields.Boolean(string='Return This', default=True)
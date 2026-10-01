from odoo import models, fields, api
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_sales_return = fields.Boolean(string='Is Sales Return', default=False)
    origin_sale_order_id = fields.Many2one(
        'sale.order',
        string='Copy Sale Order',
        domain="[('is_sales_return', '=', False), ('state', '=', 'sale')]",
        help='Select the original confirmed sale order this return is against.'
    )

    return_picking_ids = fields.Many2many(
        'stock.picking',
        'sale_order_return_picking_rel',
        'order_id', 'picking_id',
        string='Return Deliveries',
        copy=False,
    )
    return_picking_count = fields.Integer(
        string='Return Delivery Count',
        compute='_compute_return_picking_count',
    )

    credit_note_ids = fields.Many2many(
        'account.move',
        'sale_order_credit_note_rel',
        'order_id', 'move_id',
        string='Credit Notes',
        copy=False,
    )
    credit_note_count = fields.Integer(
        string='Credit Note Count',
        compute='_compute_credit_note_count',
    )

    @api.depends('return_picking_ids')
    def _compute_return_picking_count(self):
        for order in self:
            order.return_picking_count = len(order.return_picking_ids)

    @api.depends('credit_note_ids')
    def _compute_credit_note_count(self):
        for order in self:
            order.credit_note_count = len(order.credit_note_ids)

    @api.onchange('origin_sale_order_id')
    def _onchange_origin_sale_order_id(self):
        if self.origin_sale_order_id:
            self.partner_id = self.origin_sale_order_id.partner_id

    def action_copy_sale_order_lines(self):
        self.ensure_one()
        if not self.origin_sale_order_id:
            raise UserError("Please select a Sale Order to copy first.")

        origin = self.origin_sale_order_id

        delivery_done = any(picking.state == 'done' for picking in origin.picking_ids)
        invoice_done = bool(origin.invoice_ids.filtered(lambda inv: inv.state == 'posted'))

        if not delivery_done and not invoice_done:
            raise UserError(
                "Cannot create a return: the original order has not been delivered "
                "or invoiced yet. At least one of these must be completed first."
            )

        return {
            'name': 'Select Lines to Return',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.return.line.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_return_order_id': self.id,
                'default_origin_sale_order_id': origin.id,
            },
        }

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            if order.is_sales_return and order.origin_sale_order_id:
                order._create_return_delivery()
                order._create_credit_note()
        return res

    def _create_return_delivery(self):
        self.ensure_one()
        origin = self.origin_sale_order_id

        done_pickings = origin.picking_ids.filtered(
            lambda p: p.state == 'done' and p.picking_type_id.code == 'outgoing'
        )
        if not done_pickings:
            return

        return_lines = self.order_line.filtered(
            lambda l: l.origin_order_line_id and l.origin_order_line_id.order_id == origin
        )
        qty_to_return = {}
        for line in return_lines:
            qty_to_return[line.product_id.id] = qty_to_return.get(line.product_id.id, 0.0) + line.product_uom_qty

        if not qty_to_return:
            return

        StockReturnPicking = self.env['stock.return.picking']

        for picking in done_pickings:
            picked_product_ids = set(picking.move_ids.mapped('product_id').ids)
            relevant = picked_product_ids & set(qty_to_return.keys())
            if not relevant:
                continue

            wizard = StockReturnPicking.with_context(
                active_id=picking.id, active_model='stock.picking'
            ).create({})

            for return_move in wizard.product_return_moves:
                if return_move.product_id.id in qty_to_return:
                    return_move.quantity = qty_to_return[return_move.product_id.id]
                else:
                    return_move.quantity = 0.0

            result = wizard.action_create_returns()

            new_picking_id = result.get('res_id')
            if not new_picking_id:
                continue

            new_picking = self.env['stock.picking'].browse(new_picking_id)
            new_picking.action_confirm()
            new_picking.action_assign()
            for move in new_picking.move_ids:
                move.quantity = move.product_uom_qty
            new_picking.button_validate()
            self.return_picking_ids = [(4, new_picking.id)]

    def _create_credit_note(self):
        self.ensure_one()
        origin = self.origin_sale_order_id

        posted_invoices = origin.invoice_ids.filtered(
            lambda inv: inv.state == 'posted' and inv.move_type == 'out_invoice'
        )
        if not posted_invoices:
            return

        return_lines = self.order_line.filtered(
            lambda l: l.origin_order_line_id and l.origin_order_line_id.order_id == origin
        )
        qty_to_credit = {}
        for line in return_lines:
            qty_to_credit[line.product_id.id] = qty_to_credit.get(line.product_id.id, 0.0) + line.product_uom_qty

        if not qty_to_credit:
            return

        for invoice in posted_invoices:
            credit_lines = []
            for inv_line in invoice.invoice_line_ids:
                product = inv_line.product_id
                remaining = qty_to_credit.get(product.id, 0.0)
                if product.id not in qty_to_credit or remaining <= 0:
                    continue

                qty = min(remaining, inv_line.quantity)
                if qty <= 0:
                    continue

                credit_lines.append((0, 0, {
                    'product_id': product.id,
                    'quantity': qty,
                    'price_unit': inv_line.price_unit,
                    'name': inv_line.name,
                    'tax_ids': [(6, 0, inv_line.tax_ids.ids)],
                    'account_id': inv_line.account_id.id,
                }))
                qty_to_credit[product.id] -= qty

            if not credit_lines:
                continue

            credit_note = self.env['account.move'].create({
                'move_type': 'out_refund',
                'partner_id': invoice.partner_id.id,
                'invoice_origin': self.name,
                'ref': f"Credit Note for {invoice.name} (Return {self.name})",
                'invoice_line_ids': credit_lines,
            })
            credit_note.action_post()
            self.credit_note_ids = [(4, credit_note.id)]

    def action_view_return_pickings(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('stock.action_picking_tree_all')
        action['domain'] = [('id', 'in', self.return_picking_ids.ids)]
        if len(self.return_picking_ids) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = self.return_picking_ids.id
        return action

    def action_view_credit_notes(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_out_refund_type')
        action['domain'] = [('id', 'in', self.credit_note_ids.ids)]
        if len(self.credit_note_ids) == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = self.credit_note_ids.id
        return action


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    origin_order_line_id = fields.Many2one(
        'sale.order.line',
        string='Original Order Line',
        help='If this line was created via a Sales Return, this points to the original line it was copied from.'
    )

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        lines = self.filtered(lambda l: not l.order_id.is_sales_return)
        return super(SaleOrderLine, lines)._action_launch_stock_rule(
            previous_product_uom_qty=previous_product_uom_qty
        )
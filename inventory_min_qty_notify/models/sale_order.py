from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            order._check_minimum_quantity()
        return res

    def _check_minimum_quantity(self):
        self.ensure_one()

        # 1. Total ordered quantity per product in this order
        ordered = {}
        for line in self.order_line:
            product = line.product_id
            if product and product.is_storable:
                qty = line.product_uom._compute_quantity(
                    line.product_uom_qty, product.uom_id)
                ordered[product] = ordered.get(product, 0.0) + qty

        # 2. Find the Discuss channel created at install time
        channel = self.env.ref(
            'inventory_min_qty_notify.channel_inventory_notification',
            raise_if_not_found=False,
        )
        if not channel:
            return
        channel = channel.sudo()
        bot_partner = self.env.ref('base.partner_root')

        product_config = self.env['inventory.min.qty'].sudo()
        category_config = self.env['inventory.min.qty.category'].sudo()
        company_ids = [self.company_id.id, False]

        # 3. Compare remaining stock with every limit that applies
        for product, qty in ordered.items():
            remaining = product.qty_available - qty
            limits = []

            # 3a. Product-wise limits
            product_configs = product_config.search([
                ('product_ids', 'in', product.id),
                ('company_id', 'in', company_ids),
            ])
            limits += product_configs.mapped('min_qty')

            # 3b. Category-wise limits (the product's category and its parents)
            category_ids = [
                int(cid) for cid in product.categ_id.parent_path.split('/') if cid
            ]
            category_configs = category_config.search([
                ('category_ids', 'in', category_ids),
                ('company_id', 'in', company_ids),
            ])
            limits += category_configs.mapped('min_qty')

            # 4. Post one message for each limit that is crossed
            for limit in limits:
                if remaining < limit:
                    self._post_min_qty_message(
                        channel, bot_partner, product, limit, remaining)

    def _post_min_qty_message(self, channel, bot_partner, product, limit, remaining):
        product_name = product.with_context(
            display_default_code=False).display_name
        message = (
            "Inventory Minimum Quantity Notification: "
            "%s has fallen below its minimum stock limit of %g units. "
            "Current on-hand quantity: %g units."
        ) % (product_name, limit, remaining)
        channel.message_post(
            body=message,
            author_id=bot_partner.id,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )
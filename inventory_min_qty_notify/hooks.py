from odoo import api, SUPERUSER_ID

CHANNEL_NAME = 'Inventory Notification'


def post_init_hook(env):
    """Runs once, right after the module is installed."""
    channel = env['discuss.channel'].search(
        [('name', '=', CHANNEL_NAME), ('channel_type', '=', 'channel')],
        limit=1,
    )
    if not channel:
        channel = env['discuss.channel'].create({
            'name': CHANNEL_NAME,
            'description': 'Automatic alerts when product stock falls below its minimum limit.',
            'channel_type': 'channel',
        })

    # Give the channel a fixed technical ID so we can find it easily later
    xmlid = env['ir.model.data'].search([
        ('module', '=', 'inventory_min_qty_notify'),
        ('name', '=', 'channel_inventory_notification'),
    ], limit=1)
    if not xmlid:
        env['ir.model.data'].create({
            'module': 'inventory_min_qty_notify',
            'name': 'channel_inventory_notification',
            'model': 'discuss.channel',
            'res_id': channel.id,
            'noupdate': True,
        })

    # Add all Inventory users as members, so the channel shows in their Discuss sidebar
    stock_users = env.ref('stock.group_stock_user').users
    partners = stock_users.mapped('partner_id')
    if partners:
        channel.add_members(partner_ids=partners.ids)
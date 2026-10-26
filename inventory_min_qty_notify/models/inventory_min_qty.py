from odoo import api, fields, models
from odoo.exceptions import ValidationError


class InventoryMinQty(models.Model):
    _name = 'inventory.min.qty'
    _description = 'Inventory Minimum Quantity'

    name = fields.Char(string='Name', required=True)
    product_ids = fields.Many2many(
        'product.product',
        'inventory_min_qty_product_rel',
        'min_qty_id',
        'product_id',
        string='Products',
        domain=[('is_storable', '=', True)],
        required=True,
    )
    min_qty = fields.Float(string='Minimum Quantity', required=True, default=1.0)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
    )

    @api.constrains('min_qty')
    def _check_min_qty(self):
        for rec in self:
            if rec.min_qty < 0:
                raise ValidationError("Minimum Quantity cannot be negative.")
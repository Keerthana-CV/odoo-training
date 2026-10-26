from odoo import api, fields, models
from odoo.exceptions import ValidationError


class InventoryMinQtyCategory(models.Model):
    _name = 'inventory.min.qty.category'
    _description = 'Inventory Minimum Quantity (Category Wise)'

    name = fields.Char(string='Name', required=True)
    category_ids = fields.Many2many(
        'product.category',
        'inventory_min_qty_category_rel',
        'min_qty_id',
        'category_id',
        string='Product Categories',
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
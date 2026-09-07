from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    communication_address = fields.Text(string="Communication Address")
    street = fields.Char()
    street2 = fields.Char()
    city = fields.Char()
    zip = fields.Char()
    country_id = fields.Many2one('res.country')
    state_id = fields.Many2one('res.country.state')
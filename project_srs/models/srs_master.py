from odoo import models, fields


class SrsMaster(models.Model):
    _name = 'project.srs.master'
    _description = 'SRS Master'

    name = fields.Char(string='SRS Name', required=True)
    code = fields.Char(string='SRS Code')
    description = fields.Text(string='Description')
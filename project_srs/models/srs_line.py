from odoo import models, fields


class ProjectSrsLine(models.Model):
    _name = 'project.srs.line'
    _description = 'Project SRS Line'

    project_id = fields.Many2one(
        'project.project',
        string='Project',
        required=True,
        ondelete='cascade'
    )

    srs_master_id = fields.Many2one(
        'project.srs.master',
        string='SRS',
        required=True
    )

    description = fields.Text(
        string='Description',
        related='srs_master_id.description',
        readonly=False
    )
from odoo import models, fields, api


class ProjectProject(models.Model):
    _inherit = 'project.project'

    srs_line_ids = fields.One2many(
        'project.srs.line',
        'project_id',
        string='SRS Lines'
    )

    srs_reference_project_id = fields.Many2one(
        'project.project',
        string='Reference Template',
        domain="[('id', '!=', id)]",
        help="Select another project to copy its SRS lines into this project."
    )

    @api.onchange('srs_reference_project_id')
    def _onchange_srs_reference_project_id(self):
        if self.srs_reference_project_id:
            # Keep any lines already added manually in this project
            keep_commands = [
                (4, line.id) for line in self.srs_line_ids if isinstance(line.id, int)
            ]
            # Copy lines from the selected reference project
            copy_commands = [
                (0, 0, {
                    'srs_master_id': line.srs_master_id.id,
                    'description': line.description,
                })
                for line in self.srs_reference_project_id.srs_line_ids
            ]
            self.srs_line_ids = keep_commands + copy_commands

    def action_print_srs(self):
        return self.env.ref('project_srs.action_report_project_srs').report_action(self)
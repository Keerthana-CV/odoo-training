from odoo import models, fields

print("COLLEGE STUDENT PYTHON FILE LOADED")


class CollegeStudent(models.Model):
    _name = "college.student"
    _description = "college student"

    def action_print_student(self):
        return self.env.ref(
            'college_erp.action_college_student_report'
        ).report_action(self)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed')
    ], string="Status", default='draft')

    def action_confirm(self):
        self.state = 'confirm'

    def action_draft(self):
        self.state = 'draft'

    hide_address = fields.Boolean(string="Hide Address")
    admission_number = fields.Char(string="Admission Number", required=True)
    admission_date = fields.Date(string="Admission Date", required=True)
    first_name = fields.Char(string="First Name", required=True)
    last_name = fields.Char(string="Last Name", required=True)
    father_name = fields.Char(string="Father's Name", required=True)
    mother_name = fields.Char(string="Mother's Name", required=True)
    communication_address = fields.Text(
        string="Communication Address",
        required=True
    )
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one(
        'res.country.state',
        'Fed. State',
        domain="[('country_id', '=?', country_id)]"
    )
    country_id = fields.Many2one('res.country')
    country_code = fields.Char(
        related='country_id.code',
        string='Country Code'
    )
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
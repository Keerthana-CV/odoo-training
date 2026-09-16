import io
import xlsxwriter
from odoo import http
from odoo import fields as odoo_fields
from odoo.http import request, content_disposition

class SaleReportController(http.Controller):

    @http.route('/sale_report_custom/xlsx/<int:wizard_id>', type='http', auth='user')
    def download_sale_report_xlsx(self, wizard_id):
        wizard = request.env['sale.report.wizard'].browse(wizard_id)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Sales Report')

        # ---- Formats (styles) ----
        title_fmt = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'})
        sub_fmt = workbook.add_format({'italic': True, 'align': 'center'})
        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#D9E1F2', 'border': 1, 'align': 'center'
        })
        cell_fmt = workbook.add_format({'border': 1})
        money_fmt = workbook.add_format({'border': 1, 'num_format': '$#,##0.00'})
        headers = [
            'Customer', 'Invoice Date', 'Invoice Status', 'Payment Status',
            'Product', 'Quantity', 'Amount (Untaxed)', 'Tax', 'Total'
        ]
        ncols = len(headers) - 1

        # ---- Title rows ----
        sheet.merge_range(0, 0, 0, ncols, 'SALES REPORT', title_fmt)
        sheet.merge_range(
            1, 0, 1, ncols,
            f"From: {odoo_fields.Datetime.context_timestamp(wizard, wizard.date_from).strftime('%d-%m-%Y %H:%M')}   "
            f"To: {odoo_fields.Datetime.context_timestamp(wizard, wizard.date_to).strftime('%d-%m-%Y %H:%M')}",
            sub_fmt
        )

        # ---- Header row ----
        row = 3
        for col, h in enumerate(headers):
            sheet.write(row, col, h, header_fmt)

        # ---- Data rows ----
        lines = wizard._get_report_lines()
        row += 1
        last_customer = None
        for line in lines:
            move = line.move_id
            tax_amt = line.price_total - line.price_subtotal
            customer_name = move.partner_id.name or ''
            display_name = customer_name if customer_name != last_customer else ''
            sheet.write(row, 0, display_name, cell_fmt)
            local_create = odoo_fields.Datetime.context_timestamp(move, move.create_date) if move.create_date else None
            sheet.write(row, 1, local_create.strftime('%Y-%m-%d %H:%M') if local_create else '', cell_fmt)
            sheet.write(row, 2, dict(move._fields['state'].selection).get(move.state, ''), cell_fmt)
            sheet.write(row, 3, dict(move._fields['payment_state'].selection).get(move.payment_state, ''), cell_fmt)
            sheet.write(row, 4, line.product_id.name or '', cell_fmt)
            sheet.write(row, 5, line.quantity, cell_fmt)
            sheet.write(row, 6, line.price_subtotal, money_fmt)
            sheet.write(row, 7, tax_amt, money_fmt)
            sheet.write(row, 8, line.price_total, money_fmt)
            last_customer = customer_name
            row += 1

        # ---- Column widths ----
        widths = [25, 14, 14, 14, 25, 10, 15, 12, 15]
        for col, width in enumerate(widths):
            sheet.set_column(col, col, width)

        workbook.close()
        output.seek(0)

        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition('sales_report.xlsx')),
            ]
        )
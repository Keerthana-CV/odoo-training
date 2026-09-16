{
    'name': 'Custom Sales Report',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'depends': ['sale', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sale_report_wizard_view.xml',
        'views/menu.xml',
        # 'report/sale_xlsx_report.xml',   # we'll add this back in a later step
    ],
    'installable': True,
}
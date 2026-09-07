{
    'name': 'SB Sale Automation',
    'version': '18.0.1.0',
    'depends': ['sale_stock'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'reports/sale_order_report.xml',
    ],
    'installable': True,
}
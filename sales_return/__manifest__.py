{
    'name': 'Sales Return',
    'version': '18.0.1.0.0',
    'summary': 'Create sales returns linked to original sale orders, with reverse delivery and credit note',
    'category': 'Sales',
    'depends': ['sale_management', 'sale_stock', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'wizard/sale_return_line_wizard_view.xml',
    ],
    'installable': True,
    'application': False,
}
{
    'name': 'Delivery Approval',
    'version': '18.0.1.0.0',
    'summary': 'Multi-level approval before validating sales deliveries',
    'depends': ['stock', 'sale_stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/approval_level_views.xml',
        'views/approval_reject_wizard_views.xml',
        'views/stock_picking_views.xml',
        
    ],
    'installable': True,
    'application': False,
}
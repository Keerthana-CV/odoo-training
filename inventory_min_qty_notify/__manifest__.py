{
    'name': 'Inventory Minimum Quantity Notification',
    'version': '18.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Notify in Discuss when product stock falls below a minimum limit',
    'depends': ['stock', 'sale_stock', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/inventory_min_qty_views.xml',
        'views/inventory_min_qty_category_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
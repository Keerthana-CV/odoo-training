{
    'name': 'College ERP',
    'version': '18.0.1.1',
    'summary': 'College Management System',
    'description': 'Module for managing college activities',
    'depends': ['base', 'sale'],
    'author': 'HP',
    'category': 'Education',
    'data': [
        'security/ir.model.access.csv',
        "views/college_student_views.xml",
        "views/sale_order_views.xml",
        "views/college_erp_menus.xml",
        'report/college_student_report.xml',
],
    'application': True,
}
{
    'name': 'Project SRS',
    'version': '18.0.1.0.0',
    'category': 'Project',
    'summary': 'SRS management for Projects',
    'description': """
        Project SRS Management
        =======================
        Manage SRS master data and project SRS requirements.
    """,
    'depends': ['project'],

    'data': [
        'security/ir.model.access.csv',
        'views/srs_master_views.xml',
        'views/project_views.xml',
        'report/srs_report.xml',
        ],
    'installable': True,
    'application': True,
}
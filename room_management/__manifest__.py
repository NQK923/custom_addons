{
    'name': 'Quản lý phòng khám',
    'version': '1.0',
    'category': 'Healthcare',
    'summary': 'Quản lý phòng khám',
    'description': """
        Module quản lý phòng khám và theo dõi bệnh nhân trong phòng
    """,
    'depends': ['base', 'patient_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

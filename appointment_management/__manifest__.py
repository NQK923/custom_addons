{
    'name': 'Appointment Management',
    'version': '1.0',
    'category': 'Healthcare',
    'summary': 'Quản lý lịch hẹn khám',
    'description': """
        Module quản lý lịch hẹn khám bệnh
    """,
    'depends': ['base', 'hr', 'patient_management', 'room_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

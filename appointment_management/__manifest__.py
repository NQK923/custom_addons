{
    'name': 'Đặt lịch khám bệnh',
    'version': '1.0',
    'category': 'Healthcare',
    'summary': 'Quản lý lịch hẹn khám',
    'description': """
        Module quản lý lịch hẹn khám bệnh
    """,
    'depends': ['base', 'hr', 'patient_management', 'room_management', 'staff_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        "views/clinic_patient_views.xml",
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}

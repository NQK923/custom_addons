{
    'name': 'Đặt lịch khám bệnh',
    'version': '1.0',
    'category': 'Healthcare',
    'summary': 'Quản lý lịch hẹn khám',
    'description': """
        Module quản lý lịch hẹn khám bệnh
    """,
    'depends': ['base', 'hr', 'patient_management', 'room_management', 'staff_management', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/appointment_templates.xml',
        'views/appointment_list_template.xml',
        'views/appointment_detail_template.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
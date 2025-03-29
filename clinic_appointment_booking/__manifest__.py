{
    'name': 'Đặt lịch hẹn khám',
    'version': '1.0',
    'summary': 'Module đặt lịch hẹn khám cho bệnh nhân',
    'description': """
        Module cho phép bệnh nhân đặt lịch hẹn khám và kiểm tra lịch hẹn đã đặt.
    """,
    'category': 'Healthcare',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'web', 'website', 'patient_management', 'room_management', 'staff_management', 'appointment_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/appointment_booking_views.xml',
        'views/website_templates.xml',
        'data/appointment_booking_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
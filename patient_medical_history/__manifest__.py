{
    'name': "Lịch sử khám của bệnh nhân",
    'summary': "Hiển thị lịch sử khám của bệnh nhân trên giao diện web",
    'description': "Module cho phép tìm kiếm bệnh nhân theo email, xác thực OTP và hiển thị lịch sử khám.",
    'author': "Your Name",
    'version': '1.0',
    'depends': ['base', 'website', 'mail', 'patient_management', 'insurance_management', 'Treatment_and_care_management'],  # Added 'mail' dependency
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'views/patient_history_templates.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
}

{
    'name': "Lịch sử khám của bệnh nhân",
    'summary': "Hiển thị lịch sử khám của bệnh nhân trên giao diện web",
    'description': "Module cho phép tìm kiếm bệnh nhân theo mã hoặc tên và hiển thị lịch sử khám.",
    'author': "Your Name",
    'version': '1.0',
    'depends': ['base', 'website'],  # Added 'website' dependency
    'data': [
        'security/ir.model.access.csv',
        'views/patient_history_templates.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
}
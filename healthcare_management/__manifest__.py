# -*- coding: utf-8 -*-

{
    'name': 'Quản Lý Chăm Sóc Khách Hàng Y Tế',
    'version': '1.0',
    'summary': 'Quản lý phản hồi của bệnh nhân và chăm sóc khách hàng',
    'description': """
        Module quản lý liên lạc và chăm sóc khách hàng trong lĩnh vực y tế:
        - Quản lý phản hồi từ bệnh nhân
        - Xử lý khiếu nại 
        - Theo dõi cải thiện dịch vụ chăm sóc sức khỏe
        - Nhắc nhở lịch hẹn tự động
    """,
    'category': 'Healthcare',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'mail', 'appointment_management', 'staff_management', 'website'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/security.xml',
        # Data
        'data/sequence.xml',
        'data/appointment_reminder_cron.xml',
        'data/appointment_reminder_email_template.xml',
        'views/website_templates/website_menu.xml',
        'views/website_templates/healthcare_dashboard_template.xml',
        'views/website_templates/patient_feedback_template.xml',
        'views/website_templates/complaint_template.xml',
        'views/website_templates/feedback_dashboard_template.xml',
        'views/website_templates/feedback_statistics_template.xml',
        'views/website_templates/complaint_dashboard_template.xml',
        'views/website_templates/complaint_statistics_template.xml',
        'views/website_templates/appointment_reminder_template.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}

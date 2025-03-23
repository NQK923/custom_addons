# -*- coding: utf-8 -*-

{
    'name': 'Quản lý Hồ sơ và Chứng nhận Y tế',
    'version': '1.0',
    'summary': 'Quản lý hồ sơ, chứng nhận và giấy phép hoạt động y tế',
    'description': """
        Module quản lý hồ sơ và chứng nhận y tế cho bệnh viện và phòng khám
        ==============================================================
        - Quản lý chứng nhận và giấy phép hoạt động
        - Theo dõi thời hạn hiệu lực và gia hạn
        - Lưu trữ hồ sơ kiểm tra và đánh giá
        - Cảnh báo thời hạn hết hạn
    """,
    'category': 'Healthcare',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'mail', 'staff_management'],
    'data': [
        'security/certification_security.xml',
        'security/ir.model.access.csv',
        'views/certification_views.xml',
        'views/inspection_views.xml',
        'views/menu_views.xml',
        'data/mail_template_data.xml',
        'data/reminder_cron.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
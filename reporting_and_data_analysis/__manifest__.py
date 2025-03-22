# -*- coding: utf-8 -*-
{
    'name': 'Báo Cáo Y Tế',
    'version': '1.0',
    'summary': 'Module báo cáo y tế cho bệnh viện và phòng khám',
    'description': """
        Module này cung cấp các chức năng báo cáo y tế cho bệnh viện và phòng khám, bao gồm:
        - Báo cáo tình hình bệnh nhân
        - Báo cáo dịch tễ học
        - Báo cáo chất lượng dịch vụ
        - Báo cáo chỉ số hiệu suất
    """,
    'category': 'Healthcare',
    'author': 'Your Name',
    'website': 'https://www.yourwebsite.com',
    'depends': ['base', 'mail', 'hospital_management'],  # Giả sử có module hospital_management
    'data': [
        'security/ir.model.access.csv',
        'views/medical_report_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
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
    'depends': ['base', 'mail','appointment_management','healthcare_management','staff_management', 'invoice_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/invoice_report_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
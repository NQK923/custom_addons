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
    'depends': ['base', 'mail', 'appointment_management', 'healthcare_management', 'staff_management',
                'invoice_management', 'website'],  # Added website dependency
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/website_templates/invoice_report_templates.xml',
        'views/website_templates/medical_report_templates.xml',
        'views/website_templates/dashboard_templates.xml',
        'views/website_templates/report_wizard_templates.xml',
        'views/website_menu.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}

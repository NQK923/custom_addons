# -*- coding: utf-8 -*-

{
    'name': 'Quản lý Tuân thủ Y tế',
    'version': '1.0',
    'summary': 'Quản lý tuân thủ các quy định y tế cho bệnh viện và phòng khám',
    'description': """
        Module quản lý tuân thủ y tế cho Odoo 18
        =======================================
        - Quản lý các quy định y tế quốc gia và quốc tế
        - Theo dõi trạng thái tuân thủ
        - Tạo báo cáo tuân thủ
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'category': 'Healthcare',
    'depends': ['base', 'mail', 'staff_management', 'website'],  # Thêm website dependency
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        # 'views/health_compliance_views.xml',
        # 'views/health_regulation_views.xml',
        # 'views/menu_views.xml',
        'views/website_menu.xml',
        'views/compliance_dashboard.xml',
        'views/compliance_form.xml',
        'views/regulation_list.xml',
        'views/regulation_form.xml',
        'views/authority_list.xml',
        'views/authority_form.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}

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
    """,
    'category': 'Healthcare',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'mail', 'contacts','hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/patient_feedback_views.xml',
        'views/complaint_views.xml',
        'views/feedback_dashboard_view.xml',
        'views/feedback_statistics_view.xml',
        'views/menu_views.xml',
        'data/sequence.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
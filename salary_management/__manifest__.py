# -*- coding: utf-8 -*-
{
    'name': "Quản lý lương thưởng",

    'summary': "Hiển thị và quản lý lương thưởng trên giao diện web",

    'description': """
Module cho phép quản lý lương thưởng của nhân viên thông qua giao diện web.
Các chức năng chính:
- Quản lý bảng lương theo tháng
- Xem phiếu lương cá nhân
- Quản lý phụ cấp, thưởng, khấu trừ
- Xác nhận và thanh toán lương
    """,

    'author': "Your Name",
    'website': "https://www.yourcompany.com",

    'category': 'Healthcare',
    'version': '1.0',
    'license': 'LGPL-3',

    'depends': ['base', 'staff_management', 'website'],

    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        # 'views/views.xml',
        'views/salary_templates.xml',
        'views/salary_sheet_templates.xml',
        'views/salary_detail_templates.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
}

# -*- coding: utf-8 -*-
{
    'name': "Quản lý nhân sự",

    'summary': "Quản lý thông tin nhân sự y tế trên giao diện web",

    'description': """
Module cho phép quản lý thông tin nhân sự y tế, chấm công và đánh giá hiệu suất thông qua giao diện web.
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    'category': 'Healthcare',
    'version': '0.1',
    'license': 'LGPL-3',

    'depends': ['base', 'website'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        # 'views/views.xml',
        'views/website_menu.xml',
        'views/tab_menu_template.xml',
        'views/staff_list_template.xml',
        'views/staff_detail_template.xml',
        'views/staff_form_template.xml',
        'views/staff_type_list_template.xml',
        'views/staff_type_form_template.xml',
        'views/department_list_template.xml',
        'views/department_form_template.xml',
        'views/attendance_template.xml',
        'views/performance_template.xml',
    ],
    'installable': True,
    'application': True,
}

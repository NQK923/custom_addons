# -*- coding: utf-8 -*-
{
     'name': "Quản lý bảo hiểm y tế",

    'summary': "Quản lý thông tin bảo hiểm y tế của bệnh nhân",


    'description': """
Module quản lý thông tin bảo hiểm y tế của bệnh nhân, hỗ trợ:
- Quản lý số thẻ bảo hiểm
- Kiểm tra hiệu lực
- Thông tin nơi đăng ký khám chữa bệnh
- Mức chi trả bảo hiểm
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Healthcare',
    'version': '0.1',
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'patient_management', 'website'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'installable': True,
    'application': True,

}
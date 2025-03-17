# -*- coding: utf-8 -*-
{
    'name': "Quản lý bệnh nhân",
    'summary': "Quản lý thông tin bệnh nhân",
    'description': """
    Long description of module's purpose
    """,
    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Tools',
    'version': '0.1',
    'license': 'LGPL-3',
    'depends': ['base', 'insurance_management'],  # Thêm insurance_management vào depends
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}